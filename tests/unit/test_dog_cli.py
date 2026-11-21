"""Tests for the dog report display."""

from pathlib import Path

import pytest

from pawgress.dog_cli import display_dog_report


@pytest.mark.parametrize(
    ("comparison", "reference_ids", "expected_comparison", "expected_references"),
    [
        (
            None,
            [],
            "No comparable history available.",
            "None",
        ),
        (
            "Similar observations were reported previously.",
            ["previous-1", "previous-2"],
            "Similar observations were reported previously.",
            "previous-1, previous-2",
        ),
    ],
    ids=["no-history", "with-history"],
)
def test_display_dog_report(
    comparison: str | None,
    reference_ids: list[str],
    expected_comparison: str,
    expected_references: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "report_id": "report-1",
        "created_at": "2026-11-20T12:00:00+00:00",
        "scene_context": "Another dog approaching.",
        "safety_assessment": "Safety cannot be established from still images.",
        "behavioral_observations": {
            "observations": "The dog is standing.\nIts tail is lowered.",
            "interpretation": "The dog's emotional state is uncertain.",
            "comparison": comparison,
        },
        "recommendations": "Allow space and observe.",
        "referenced_report_ids": reference_ids,
    }

    display_dog_report(report, Path("reports.db"))

    output = capsys.readouterr()
    assert output.out == (
        "\nPawgress Dog Report — report-1\n"
        "Created: 2026-11-20T12:00:00+00:00\n"
        "Scene: Another dog approaching.\n"
        "\n1. Safety Assessment\n"
        "Safety cannot be established from still images.\n"
        "\n2. Behavioral Observations\n"
        "\n  Observations:\n"
        "    The dog is standing.\n"
        "    Its tail is lowered.\n"
        "\n  Interpretation:\n"
        "    The dog's emotional state is uncertain.\n"
        "\n  Comparison:\n"
        f"    {expected_comparison}\n"
        "\n3. Recommendations\n"
        "Allow space and observe.\n"
        f"\nReferenced reports: {expected_references}\n"
        "Report saved to: reports.db\n"
    )
    assert output.err == ""
