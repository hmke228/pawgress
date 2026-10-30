"""Unit tests for the standalone behavioral comparison prototype."""

import importlib.util
import sqlite3
from pathlib import Path

import pytest

ENGINE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "research"
    / "behavioral_comparison"
    / "behavoral_comparison_engine.py"
)
SPEC = importlib.util.spec_from_file_location(
    "behavoral_comparison_engine", ENGINE_PATH
)
assert SPEC is not None and SPEC.loader is not None
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


@pytest.fixture
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fixture to provide a temporary database path for testing."""
    path = tmp_path / "pawgress.db"
    monkeypatch.setattr(engine, "DB_NAME", path)
    return path


def test_initialize_database_creates_reports_table(database_path):
    """Test that the database is initialized and the 'reports' table is created."""
    engine.initialize_database()
    engine.initialize_database()

    with sqlite3.connect(database_path) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'reports'"
        ).fetchone()

    assert table == ("reports",)


def test_save_and_get_previous_reports_filters_orders_and_limits(database_path):
    ""
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

    reports = engine.get_previous_reports("Milo", "current")

    assert [report["report_id"] for report in reports] == [
        "latest",
        "third",
        "second",
    ]
    assert reports[0] == {
        "report_id": "latest",
        "created_at": "2026-01-04",
        "scene_context": "park",
        "behavioral_observations": {"current": "observations for latest"},
    }


@pytest.mark.parametrize(
    ("text", "pattern", "expected"),
    [
        ("barking was not observed", "barking", True),
        ("barking were not observed", "barking", True),
        ("no barking", "barking", True),
        ("without barking", "barking", True),
        ("the dog was barking", "barking", False),
        ("NO GROWLING", "growling", True),
    ],
)
def test_is_negated(text, pattern, expected):
    """Test the is_negated function with various text and pattern combinations."""
    assert engine.is_negated(text, pattern) is expected


def test_compare_reports_returns_baseline_without_history():
    """Test that compare_reports returns a baseline when no previous reports exist.
    This test ensures that when there are no previous reports, the comparison summary indicates
    that a baseline is being established.
    """
    result = engine.compare_reports("The dog barked.", [])

    assert result == {
        "comparison_summary": (
            "No previous reports were available for comparison. "
            "This report establishes a behavioral baseline."
        ),
        "referenced_report_ids": [],
    }
