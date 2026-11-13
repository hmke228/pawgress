"""Unit tests for the standalone behavioral comparison prototype."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime as DateTime
from pathlib import Path
from types import SimpleNamespace

import pytest

from pawgress import behavioral_comparison as engine


@pytest.fixture
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide an isolated SQLite database for a test."""
    path = tmp_path / "pawgress.db"
    monkeypatch.setattr(engine, "DB_NAME", path)
    return path


def report(report_id: str, observations: str, scene_context: str = "park") -> dict:
    """Create a previous-report value in the shape returned by the database."""
    return {
        "report_id": report_id,
        "created_at": "2026-01-01",
        "scene_context": scene_context,
        "behavioral_observations": {"current": observations},
    }


def patch_openai(
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    captured_requests: list | None = None,
) -> None:
    """Replace the OpenAI client with a deterministic test response."""

    class FakeResponses:
        def create(self, **kwargs):
            if captured_requests is not None:
                captured_requests.append(kwargs)
            return SimpleNamespace(output_text=output)

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.responses = FakeResponses()

    monkeypatch.setattr(engine, "OpenAI", FakeClient)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")


def test_initialize_database_creates_reports_table(database_path: Path):
    """Database initialization is safe to call more than once."""
    engine.initialize_database()
    engine.initialize_database()

    with closing(sqlite3.connect(database_path)) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'reports'"
        ).fetchone()

    assert table == ("reports",)


def test_save_and_get_previous_reports_filters_orders_and_limits(
    database_path: Path,
):
    """Previous reports are filtered by dog, ordered newest-first, and limited."""
    engine.initialize_database()
    for report_id, dog_name, created_at in [
        ("oldest", "Milo", "2026-01-01"),
        ("second", "Milo", "2026-01-02"),
        ("third", "Milo", "2026-01-03"),
        ("latest", "Milo", "2026-01-04"),
        ("other-dog", "Luna", "2026-01-05"),
        ("current", "Milo", "2026-01-06"),
    ]:
        engine.save_report(
            report_id, dog_name, created_at, "park", f"observations for {report_id}"
        )

    reports = engine.get_previous_reports("Milo", "current", limit=3)

    assert [item["report_id"] for item in reports] == ["latest", "third", "second"]
    assert reports[0] == {
        "report_id": "latest",
        "created_at": "2026-01-04",
        "scene_context": "park",
        "behavioral_observations": {"current": "observations for latest"},
    }


def test_get_previous_reports_defaults_to_ten(database_path: Path):
    """The app retrieves up to ten recent reports for the model to select from."""
    engine.initialize_database()
    for index in range(12):
        engine.save_report(
            str(index),
            "Milo",
            f"2026-01-{index + 1:02}",
            "park",
            f"observation {index}",
        )

    reports = engine.get_previous_reports("Milo", "current")

    assert len(reports) == 10
    assert reports[0]["report_id"] == "11"


def test_format_observation_list_handles_empty_single_and_multiple_values():
    """Observation labels are rendered as a readable list."""
    assert engine.format_observation_list([]) == "none identified"
    assert engine.format_observation_list(["barking"]) == "barking"
    assert engine.format_observation_list(["barking.", "jumping!"]) == (
        "barking and jumping"
    )
    assert engine.format_observation_list(["barking", "jumping", "growling"]) == (
        "barking, jumping, and growling"
    )


def test_compare_reports_returns_baseline_without_history(
    monkeypatch: pytest.MonkeyPatch,
):
    """No history establishes a baseline without making an API request."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = engine.compare_reports("The dog barked.", [])

    assert result == {
        "comparison_summary": (
            "No previous reports were available for comparison. "
            "This report establishes a behavioral baseline."
        ),
        "referenced_report_ids": [],
    }


def test_compare_reports_uses_one_model_selected_report(
    monkeypatch: pytest.MonkeyPatch,
):
    """Only the model-selected similar-scene report is referenced."""
    categories = {
        "selected_report_id": "park-report",
        "consistent": ["barking"],
        "new": ["jumping"],
        "previously_observed_not_mentioned": ["relaxed posture"],
    }
    requests = []
    patch_openai(monkeypatch, json.dumps(categories), requests)

    result = engine.compare_reports(
        "The dog barked and jumped.",
        [
            report("park-report", "The dog barked and stayed relaxed.", "park"),
            report("home-report", "The dog played with a toy.", "home"),
        ],
        scene_context="park",
    )

    assert result == {
        "comparison_summary": (
            "Consistent observations include barking; newly observed behaviors "
            "include jumping. Previously observed behaviors not mentioned in the "
            "current report include relaxed posture."
        ),
        "referenced_report_ids": ["park-report"],
    }
    assert result["comparison_summary"].count(".") <= 2
    request_input = json.loads(requests[0]["input"])
    assert request_input["current_scene_context"] == "park"
    assert [
        item["report_id"] for item in request_input["candidate_previous_reports"]
    ] == [
        "park-report",
        "home-report",
    ]
    assert "only with that selected report" in requests[0]["instructions"]
    assert "diagnoses" in requests[0]["instructions"]


def test_compare_reports_returns_baseline_when_no_similar_scene_is_selected(
    monkeypatch: pytest.MonkeyPatch,
):
    """The model can decline to compare when no scene context is similar."""
    patch_openai(
        monkeypatch,
        json.dumps(
            {
                "selected_report_id": None,
                "consistent": [],
                "new": [],
                "previously_observed_not_mentioned": [],
            }
        ),
    )

    result = engine.compare_reports(
        "The dog barked.", [report("home-report", "The dog played.", "home")], "park"
    )

    assert result == {
        "comparison_summary": (
            "No previous report from a similar scene context was available for "
            "comparison. This report establishes a behavioral baseline."
        ),
        "referenced_report_ids": [],
    }


def test_compare_reports_requires_api_key_for_history(
    monkeypatch: pytest.MonkeyPatch,
):
    """A missing key is reported when an API comparison is needed."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        engine.compare_reports("current", [report("previous", "prior")])


def test_compare_reports_rejects_unknown_selected_report(
    monkeypatch: pytest.MonkeyPatch,
):
    """The model cannot make the app reference a report it was not given."""
    patch_openai(
        monkeypatch,
        json.dumps(
            {
                "selected_report_id": "unknown",
                "consistent": [],
                "new": [],
                "previously_observed_not_mentioned": [],
            }
        ),
    )

    with pytest.raises(RuntimeError, match="invalid comparison response"):
        engine.compare_reports("current", [report("previous", "prior")])


def test_compare_reports_rejects_invalid_json_response(
    monkeypatch: pytest.MonkeyPatch,
):
    """Malformed model output fails explicitly."""
    patch_openai(monkeypatch, "not json")

    with pytest.raises(RuntimeError, match="invalid comparison response"):
        engine.compare_reports("current", [report("previous", "prior")])


def test_process_report_saves_reports_and_compares_with_history(
    database_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Reports persist, and the next report compares to one selected prior report."""
    engine.initialize_database()
    report_ids = iter(["report-1", "report-2"])
    created_at = DateTime(2026, 1, 1)
    monkeypatch.setattr(engine, "uuid4", lambda: next(report_ids))
    monkeypatch.setattr(engine, "datetime", SimpleNamespace(now=lambda: created_at))
    patch_openai(
        monkeypatch,
        json.dumps(
            {
                "selected_report_id": "report-1",
                "consistent": ["barking"],
                "new": ["jumping"],
                "previously_observed_not_mentioned": [],
            }
        ),
    )

    first_result = engine.process_report("Milo", "park", "The dog barked.")
    second_result = engine.process_report("Milo", "park", "The dog barked and jumped.")

    assert first_result == {
        "report_id": "report-1",
        "comparison_summary": (
            "No previous reports were available for comparison. "
            "This report establishes a behavioral baseline."
        ),
        "referenced_report_ids": [],
    }
    assert second_result == {
        "report_id": "report-2",
        "comparison_summary": (
            "Consistent observations include barking; newly observed behaviors "
            "include jumping. Previously observed behaviors not mentioned in the "
            "current report include none identified."
        ),
        "referenced_report_ids": ["report-1"],
    }

    with closing(sqlite3.connect(database_path)) as connection:
        saved_reports = connection.execute(
            """
            SELECT report_id, dog_name, created_at, scene_context, observations
            FROM reports
            ORDER BY report_id
            """
        ).fetchall()

    assert saved_reports == [
        ("report-1", "Milo", created_at.isoformat(), "park", "The dog barked."),
        (
            "report-2",
            "Milo",
            created_at.isoformat(),
            "park",
            "The dog barked and jumped.",
        ),
    ]


def test_main_uses_command_line_arguments_without_prompting(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    """The CLI forwards provided arguments without prompting for input."""
    saved_reports = []

    def fake_process_report(dog_name, scene_context, observations):
        saved_reports.append((dog_name, scene_context, observations))
        return {"report_id": "report-1"}

    monkeypatch.setattr(engine, "initialize_database", lambda: None)
    monkeypatch.setattr(engine, "process_report", fake_process_report)
    monkeypatch.setattr(engine, "pprint", lambda _result: None)
    monkeypatch.setattr(
        "builtins.input",
        lambda *_args: pytest.fail("The CLI should not request input."),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--dog-name",
            "Milo",
            "--scene-context",
            "park",
            "--observations",
            "The dog barked.",
        ],
    )

    engine.main()

    assert saved_reports == [("Milo", "park", "The dog barked.")]
    assert "Dog: Milo" in capsys.readouterr().out
