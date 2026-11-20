"""Fixed Story 3.2 response doubles; these do not measure live model accuracy."""

import json
from pathlib import Path

import httpx
import pytest
from openai import OpenAI
from PIL import Image

from pawgress.cli import main
from pawgress.pipeline import generate_dog_report
from pawgress.storage import ReportStore

PROFILE = {"name": "Promise", "description": "Golden dog; owner reports playfulness."}
REPORT = {
    "scene_context": "Owner reports another dog approaching outdoors.",
    "observations": "Image 1 shows a lowered tail; owner reports barking.",
    "interpretation": "The supplied reference suggests considering multiple cues.",
    "safety_assessment": "A still image cannot establish safety.",
    "recommendations": "Allow space and observe without forcing an interaction.",
}
AMBIGUOUS = REPORT | {
    "scene_context": "Two dogs are visible; the target cannot be identified.",
    "observations": "The collar and tail are obscured; no situation was supplied.",
    "interpretation": "The target's behavior cannot be assessed from this image.",
    "recommendations": "Provide a clearer image and identify the target dog.",
}
CASES = [
    ("first", "Another dog approached; Promise barked.", False, False, REPORT),
    ("history", "Another dog approached; Promise barked.", True, True, REPORT),
    ("no_match", "Another dog approached; Promise barked.", True, False, REPORT),
    (
        "missing_situation",
        None,
        True,
        False,
        REPORT
        | {
            "scene_context": "Image 1 shows an outdoor setting; the activity is unknown.",
            "observations": "Image 1 shows a lowered tail; no situation was supplied.",
        },
    ),
    ("ambiguous", None, True, False, AMBIGUOUS),
]


@pytest.fixture
def quality_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    image = tmp_path / "dog.png"
    with Image.new("RGB", (8, 8), color="blue") as picture:
        picture.save(image, format="PNG")
    store = ReportStore(tmp_path / "reports.db")
    store.save_profile(PROFILE)
    replies, requests = [], []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        reply = replies.pop(0)
        part = {"type": "output_text", "text": reply, "annotations": []}
        message = {"type": "message", "role": "assistant", "content": [part]}
        return httpx.Response(200, json={"status": "completed", "output": [message]})

    def client(**kwargs: object) -> OpenAI:
        return OpenAI(
            api_key="offline-test",
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handle)),
        )

    monkeypatch.setattr("pawgress.pipeline.OpenAI", client)
    return store, image, replies, requests


def seed_history(store: ReportStore) -> dict:
    old = {
        "report_id": "old",
        "created_at": "2026-01-01T00:00:00+00:00",
        "scene_context": REPORT["scene_context"],
        "safety_assessment": REPORT["safety_assessment"],
        "recommendations": REPORT["recommendations"],
        "behavioral_observations": {
            "observations": REPORT["observations"],
            "interpretation": REPORT["interpretation"],
            "comparison": None,
        },
        "referenced_report_ids": [],
    }
    store.save_report(old)
    return old


@pytest.mark.parametrize(
    "case,situation,history,match,fields", CASES, ids=[case[0] for case in CASES]
)
def test_fixed_report_scenarios(
    quality_setup: tuple,
    case: str,
    situation: str | None,
    history: bool,
    match: bool,
    fields: dict,
) -> None:
    store, image, replies, requests = quality_setup
    old = seed_history(store) if history else None
    replies.append(json.dumps(fields))
    if history:
        replies.append(json.dumps({"relevant_report_ids": ["old"] if match else []}))
    if match:
        replies.append(
            json.dumps(
                {
                    "comparison": "Similar cues; photographic evidence remains limited.",
                    "referenced_report_ids": ["old"],
                }
            )
        )
    report = generate_dog_report(PROFILE, [str(image)], situation, "", store)
    supplied = json.loads(requests[0]["input"][0]["content"][0]["text"])
    assert supplied["situation"] == situation
    assert set(supplied) == {
        "dog_profile",
        "situation",
        "target_hint",
        "canine_knowledge",
    }
    assert supplied["dog_profile"] == PROFILE
    for key, value in fields.items():
        container = (
            report["behavioral_observations"]
            if key in ("observations", "interpretation")
            else report
        )
        assert container[key] == value
    assert report["referenced_report_ids"] == (["old"] if match else [])
    assert (report["behavioral_observations"]["comparison"] is not None) == match
    assert store.previous_reports() == ([report, old] if history else [report])
    assert not replies


@pytest.mark.parametrize("field", list(REPORT))
@pytest.mark.parametrize("fault", ["missing", "blank", "null", "number", "duplicate"])
def test_malformed_report_never_saves_or_displays(
    quality_setup: tuple,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    field: str,
    fault: str,
) -> None:
    store, image, replies, requests = quality_setup
    old = seed_history(store)
    fields = dict(REPORT)
    if fault == "missing":
        del fields[field]
    elif fault != "duplicate":
        fields[field] = {"blank": " \n\t", "null": None, "number": 42}[fault]
    raw = json.dumps(fields)
    if fault == "duplicate":
        raw = raw[:-1] + f', "{field}": "Conflicting replacement"' + "}"
    replies.append(raw)
    replies.append(json.dumps({"relevant_report_ids": []}))
    answers = iter(["", str(image), "done", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["--dog", "--db", str(store.path)]) == 1
    output = capsys.readouterr()
    assert "invalid AI response" in output.err
    assert "Conflicting replacement" not in output.err
    assert "Traceback" not in output.err
    assert "Pawgress Dog Report" not in output.out
    assert store.previous_reports() == [old]
    assert len(requests) == 1
