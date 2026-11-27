"""Exercise Epic 2 with real SQLite, RAG and SDK parsing; only HTTP is replaced."""

import json
import sqlite3
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from openai import OpenAI
from PIL import Image

from pawgress.ai import AIGenerationError
from pawgress.behavioral_comparison import complete_dog_report
from pawgress.cli import main
from pawgress.pipeline import generate_dog_report
from pawgress.rag import REFERENCE_PATH, retrieve_canine_knowledge
from pawgress.storage import ReportStore

Transport = tuple[list[object], list[dict], Callable[..., OpenAI]]

PROFILE = {"name": "Promise", "description": "Golden dog, red collar; usually playful."}
FIELDS = {
    "observations": "Owner reports barking; image shows a lowered tail.",
    "interpretation": "Emotion is uncertain; consider other cues and context.",
    "scene_context": "Owner reports another dog approaching outdoors.",
    "safety_assessment": "A still image cannot establish safety.",
    "recommendations": "Allow space and observe the whole body.",
}


def historical(report_id: str, day: int) -> dict:
    return {
        "report_id": report_id,
        "created_at": f"2026-01-{day:02}T00:00:00+00:00",
        "scene_context": FIELDS["scene_context"],
        "safety_assessment": FIELDS["safety_assessment"],
        "recommendations": FIELDS["recommendations"],
        "behavioral_observations": {
            "observations": FIELDS["observations"],
            "interpretation": FIELDS["interpretation"],
            "comparison": None,
        },
        "referenced_report_ids": [],
    }


@pytest.fixture
def store(tmp_path: Path) -> ReportStore:
    result = ReportStore(tmp_path / "data" / "test.db")
    result.save_profile(PROFILE)
    return result


@pytest.fixture
def images(tmp_path: Path) -> list[str]:
    paths = [tmp_path / "one.png", tmp_path / "two.jpg"]

    with Image.new("RGB", (8, 8), color="blue") as picture:
        picture.save(paths[0], format="PNG")
        picture.save(paths[1], format="JPEG")

    return [str(path) for path in paths]


@pytest.fixture
def transport(monkeypatch: pytest.MonkeyPatch) -> Transport:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    replies, requests = [], []

    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        assert body["model"] == "test-model"
        assert body["store"] is False
        assert body["text"]["format"]["strict"] is True
        reply = replies.pop(0)
        if isinstance(reply, httpx.Response):
            return reply
        part = {"type": "output_text", "text": json.dumps(reply), "annotations": []}
        message = {"type": "message", "role": "assistant", "content": [part]}
        return httpx.Response(200, json={"status": "completed", "output": [message]})

    def client(**kwargs) -> OpenAI:
        return OpenAI(
            api_key="offline-test",
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handle)),
        )

    monkeypatch.setattr("pawgress.pipeline.OpenAI", client)
    return replies, requests, client


@pytest.mark.parametrize(
    "situation", [None, "tucked tail", "unmatched query vocabulary"]
)
def test_first_report_preserves_content_and_sources(
    store: ReportStore, images: list[str], transport: Transport, situation: str | None
) -> None:
    replies, requests, _ = transport
    replies.append(FIELDS)
    result = generate_dog_report(PROFILE, images, situation, "red collar", store)
    assert len(requests) == 1
    content = requests[0]["input"][0]["content"]
    supplied = json.loads(content[0]["text"])
    assert supplied["dog_profile"] == PROFILE
    assert supplied["situation"] == situation
    assert supplied["target_hint"] == "red collar"

    if situation == "unmatched query vocabulary":
        assert supplied["canine_knowledge"] == []
    else:
        assert "https://" in supplied["canine_knowledge"][0]["source"]

    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert content[2]["image_url"].startswith("data:image/jpeg;base64,")
    assert result["behavioral_observations"] == {
        "observations": FIELDS["observations"],
        "interpretation": FIELDS["interpretation"],
        "comparison": None,
    }
    assert result["referenced_report_ids"] == []
    assert result["created_at"].endswith("+00:00")
    for key in ("scene_context", "safety_assessment", "recommendations"):
        assert result[key] == FIELDS[key]
    assert ReportStore(store.path).previous_reports() == [result]
    assert ReportStore(store.path).load_profile() == PROFILE


@pytest.mark.parametrize("count", [0, 1, 2, 3, 5])
def test_filter_before_limit_without_filling_unrelated_history(
    store: ReportStore, transport: Transport, count: int
) -> None:
    replies, requests, client = transport
    originals = [historical(f"match-{i}", i + 1) for i in range(count)]
    # More than ten unrelated newer records must not hide the older relevant ones.
    originals += [historical(f"unrelated-{i}", i + 10) for i in range(12)]
    for report in originals:
        store.save_report(report)
    current = historical("current", 28)
    before = deepcopy(current)
    replies.append({"relevant_report_ids": [f"match-{i}" for i in range(count)]})
    expected = [f"match-{i}" for i in reversed(range(count))][:3]
    if expected:
        replies.append(
            {
                "comparison": "Similar cues; settings and stills limit inference.",
                "referenced_report_ids": list(reversed(expected)),
            }
        )
    with client() as sdk:
        result = complete_dog_report(current, store, sdk, "test-model")
    assert current == before
    assert result["referenced_report_ids"] == expected
    if expected:
        payload = json.loads(requests[1]["input"])
        assert "2-3 sentences and 40-70 words" in requests[1]["instructions"]
        assert [r["report_id"] for r in payload["selected_history"]] == expected
        schema = requests[1]["text"]["format"]["schema"]["properties"][
            "referenced_report_ids"
        ]
        assert schema["items"]["enum"] == expected
        assert schema["maxItems"] == len(expected)
        assert result["behavioral_observations"]["comparison"] is not None
    else:
        assert len(requests) == 1
        assert result["behavioral_observations"]["comparison"] is None
    payload = json.loads(requests[0]["input"])
    assert len(payload["candidates"]) == count + 12
    schema = requests[0]["text"]["format"]["schema"]["properties"][
        "relevant_report_ids"
    ]
    assert schema["items"]["enum"] == [r["report_id"] for r in payload["candidates"]]
    assert "current" not in schema["items"]["enum"]
    assert schema["maxItems"] == count + 12
    assert all("interpretation" not in r for r in payload["candidates"])
    assert store.previous_reports("current") == sorted(
        originals, key=lambda r: (r["created_at"], r["report_id"]), reverse=True
    )


@pytest.mark.parametrize("bad_ids", [["invented"], ["new"], [42], [{}], None, "old"])
def test_invalid_selection_never_saves_report(
    store: ReportStore, transport: Transport, bad_ids: object
) -> None:
    replies, _, client = transport
    old = historical("old", 1)
    store.save_report(old)
    replies.append({"relevant_report_ids": bad_ids})
    with client() as sdk, pytest.raises(AIGenerationError, match="history filtering"):
        complete_dog_report(historical("new", 2), store, sdk, "test-model")
    assert store.previous_reports() == [old]


@pytest.mark.parametrize(
    "reply",
    [
        {"comparison": " ", "referenced_report_ids": ["old"]},
        {"comparison": 42, "referenced_report_ids": ["old"]},
        {"comparison": "A summary", "referenced_report_ids": []},
        {"comparison": "A summary", "referenced_report_ids": ["unselected"]},
    ],
)
def test_invalid_comparison_never_saves_report(
    store: ReportStore, transport: Transport, reply: dict
) -> None:
    replies, _, client = transport
    store.save_report(historical("old", 1))
    store.save_report(historical("unselected", 2))
    replies.extend([{"relevant_report_ids": ["old"]}, reply])
    with client() as sdk, pytest.raises(AIGenerationError, match="history comparison"):
        complete_dog_report(historical("new", 3), store, sdk, "test-model")
    assert len(store.previous_reports()) == 2


def test_duplicate_valid_ids_are_referenced_once(
    store: ReportStore, transport: Transport
) -> None:
    replies, _, client = transport
    old = historical("11111111-2222-4333-8444-555555555555", 1)
    store.save_report(old)
    repeated = [old["report_id"], old["report_id"]]
    replies.extend(
        [
            {"relevant_report_ids": repeated},
            {
                "comparison": "Similar reported cues; still images limit comparison.",
                "referenced_report_ids": repeated,
            },
        ]
    )
    with client() as sdk:
        result = complete_dog_report(historical("new", 2), store, sdk, "test-model")
    assert result["referenced_report_ids"] == [old["report_id"]]
    assert store.previous_reports() == [result, old]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(401, json={"error": {"message": "Unauthorized"}}),
        httpx.Response(429, json={"error": {"message": "Rate limited"}}),
        httpx.Response(200, json={"status": "incomplete", "output": []}),
        httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "refusal", "refusal": "Cannot comply"}],
                    }
                ],
            },
        ),
        httpx.Response(200, json={"status": "completed", "output": []}),
        [],
        {"unexpected": []},
    ],
)
def test_history_api_errors_preserve_history(
    store: ReportStore, transport: Transport, response: object
) -> None:
    replies, _, client = transport
    store.save_report(historical("old", 1))
    replies.append(response)
    with client() as sdk, pytest.raises(AIGenerationError):
        complete_dog_report(historical("new", 2), store, sdk, "test-model")
    assert len(store.previous_reports()) == 1


def test_storage_is_immutable_and_isolated(store: ReportStore, tmp_path: Path) -> None:
    old = historical("old", 1)
    store.save_report(old)
    with pytest.raises(sqlite3.IntegrityError):
        store.save_report(old | {"recommendations": "replacement"})
    with pytest.raises(sqlite3.IntegrityError):
        store.save_profile({"name": "Other dog"})
    assert store.previous_reports() == [old]
    assert store.load_profile() == PROFILE
    other = ReportStore(tmp_path / "other.db")
    assert other.previous_reports() == []
    assert other.load_profile() is None


@pytest.mark.parametrize("stage", ["report generation", "filtering", "comparison"])
def test_api_error_identifies_stage_without_retry_or_partial_save(
    store: ReportStore, images: list[str], transport: Transport, stage: str
) -> None:
    replies, requests, _ = transport
    old = historical("old", 1)
    store.save_report(old)
    if stage != "report generation":
        replies.append(FIELDS)
    if stage == "comparison":
        replies.append({"relevant_report_ids": ["old"]})
    replies.append(
        httpx.Response(
            429,
            headers={"x-request-id": "req_offline"},
            json={
                "error": {"message": "Quota exhausted", "code": "insufficient_quota"}
            },
        )
    )
    expected_calls = len(replies)
    with pytest.raises(AIGenerationError) as failure:
        generate_dog_report(PROFILE, images, "Another dog approached.", "", store)
    message = str(failure.value)
    assert stage in message.lower()
    for expected in (
        "HTTP 429",
        "Quota exhausted",
        "insufficient_quota",
        "req_offline",
    ):
        assert expected in message
    assert len(requests) == expected_calls
    assert store.previous_reports() == [old]


@pytest.mark.parametrize("missing", ["OPENAI_API_KEY", "OPENAI_MODEL"])
def test_missing_configuration(
    store: ReportStore,
    images: list[str],
    transport: Transport,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    monkeypatch.delenv(missing)
    with pytest.raises(AIGenerationError, match="Set OPENAI_API_KEY"):
        generate_dog_report(PROFILE, images, "situation", "", store)
    assert main(["--dog", "--db", str(store.path)]) == 1
    assert store.previous_reports() == []


def test_empty_knowledge_and_invalid_image_make_no_request(
    store: ReportStore, images: list[str], transport: Transport, tmp_path: Path
) -> None:
    replies, requests, _ = transport
    empty = tmp_path / "empty.json"
    empty.write_text("[]")
    with pytest.raises(ValueError, match="Populate"):
        generate_dog_report(PROFILE, images, "situation", "", store, empty)
    with pytest.raises(ValueError, match="Cannot read"):
        generate_dog_report(PROFILE, ["missing.png"], "situation", "", store)
    assert replies == requests == []
    assert store.previous_reports() == []


def test_cli_first_and_later_report(
    tmp_path: Path,
    images: list[str],
    transport: Transport,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    replies, requests, _ = transport
    database = tmp_path / "cli.db"
    answers = iter(
        [
            PROFILE["name"],
            PROFILE["description"],
            "Another dog approached.",
            *images,
            "done",
            "red collar",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    replies.append(FIELDS)
    args = ["--dog", "--db", str(database)]
    assert main(args) == 0
    first = ReportStore(database).previous_reports()[0]
    output = capsys.readouterr().out
    for text in (
        "Safety Assessment",
        "Behavioral Observations",
        "Recommendations",
        "No comparable history",
        first["report_id"],
    ):
        assert text in output
    # No profile prompts on subsequent invocation; situation may be blank.
    answers = iter(["", images[0], "done", ""])
    replies.extend(
        [
            FIELDS,
            {"relevant_report_ids": [first["report_id"]]},
            {
                "comparison": "Comparable, but evidence is limited.",
                "referenced_report_ids": [first["report_id"]],
            },
        ]
    )
    assert main(args) == 0
    second = ReportStore(database).previous_reports()[0]
    assert second["report_id"] != first["report_id"]
    assert second["referenced_report_ids"] == [first["report_id"]]
    assert first in ReportStore(database).previous_reports()
    assert "Comparable, but evidence is limited." in capsys.readouterr().out
    assert (
        json.loads(requests[1]["input"][0]["content"][0]["text"])["situation"] is None
    )


@pytest.mark.parametrize(
    "error",
    [
        ValueError("bad image"),
        OSError("unreadable"),
        sqlite3.OperationalError("locked"),
        AIGenerationError("API failed"),
        EOFError(),
        KeyboardInterrupt(),
    ],
)
def test_cli_dog_errors_are_clean(
    error: BaseException, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("pawgress.cli.run_dog_cli", side_effect=error):
        assert main(["--dog"]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_cli_rejects_mixed_modes() -> None:
    with pytest.raises(SystemExit) as error:
        main(["--dog", "text"])
    assert error.value.code == 2


def test_packaged_reference_exists() -> None:
    assert REFERENCE_PATH.is_file()
    assert retrieve_canine_knowledge(None)
