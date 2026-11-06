"""Direct unit tests for the CLI involving module entry point, input validation, report validation, and report display."""

import runpy
import sys

import pytest

import pawgress.cli as cli
from pawgress.cli import display_report, main, validate_report


def test_default_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    output = capsys.readouterr()
    assert "usage: pawgress" in output.out
    assert output.err == ""


@pytest.mark.parametrize(("args", "code"), [(["--help"], 0), (["--bad"], 2)])
def test_exit_codes(args: list[str], code: int) -> None:
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == code


def test_module_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["pawgress"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("pawgress", run_name="__main__")
    assert error.value.code == 0


@pytest.mark.parametrize("text", ["Woof Woof Woof!", "   Woof Woof Woof!  "])
def test_valid_input(text: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([text]) == 0
    output = capsys.readouterr()
    assert output.out == (
        "\nDemo Output — Placeholder Data\n\n"
        "Observations:\n"
        "      - Observation Placeholder\n"
        "      - User-Provided Text: Woof Woof Woof!\n"
        "Interpretation:\n"
        "\tInterpretation Placeholder - no AI analysis was performed.\n"
        "Comparison:\n"
        "\tNot available.\n"
        "\nEnd of Demo Output\n\n"
    )
    assert output.err == ""


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_input(
    text: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def reject_demo_call(text: str) -> dict[str, object]:
        pytest.fail("cli_demo cannot be called for empty input.")

    monkeypatch.setattr(cli, "cli_demo", reject_demo_call)

    with pytest.raises(SystemExit) as error:
        main([text])

    assert error.value.code == 2
    output = capsys.readouterr()
    assert "No text provided." in output.err
    assert output.out == ""


def test_display_report_with_comparison(capsys: pytest.CaptureFixture[str]) -> None:
    display_report(
        observations=["Observation 1.", "Observation 2."],
        interpretation="This is a sample interpretation.",
        comparison="This is a sample comparison.",
    )
    output = capsys.readouterr()
    assert output.out == (
        "Observations:\n"
        "      - Observation 1.\n"
        "      - Observation 2.\n"
        "Interpretation:\n"
        "\tThis is a sample interpretation.\n"
        "Comparison:\n"
        "\tThis is a sample comparison.\n"
    )
    assert output.err == ""


def test_display_report_without_comparison(capsys: pytest.CaptureFixture[str]) -> None:
    display_report(
        observations=["Observation 1.", "Observation 2."],
        interpretation="This is a sample interpretation.",
        comparison=None,
    )
    output = capsys.readouterr()
    assert output.out == (
        "Observations:\n"
        "      - Observation 1.\n"
        "      - Observation 2.\n"
        "Interpretation:\n"
        "\tThis is a sample interpretation.\n"
        "Comparison:\n"
        "\tNot available.\n"
    )
    assert output.err == ""


@pytest.mark.parametrize("comparison", ["This is a valid comparison.", None])
def test_valid_report(comparison: str | None) -> None:
    report = {
        "observations": ["Observation 1", "Observation 2"],
        "interpretation": "This is a valid interpretation.",
        "comparison": comparison,
    }
    validate_report(report)


@pytest.mark.parametrize("report", [None, [], "invalid report", 0])
def test_invalid_report_type(report: object) -> None:
    with pytest.raises(ValueError, match="Report must be a dictionary"):
        validate_report(report)


def test_invalid_report_missing_observations() -> None:
    report = {
        "interpretation": "This is not a list of observations.",
        "comparison": "This is a valid comparison.",
    }
    with pytest.raises(
        ValueError, match="Report must contain a non-empty list of observations."
    ):
        validate_report(report)


@pytest.mark.parametrize("observations", [[], None, "Observation", 0])
def test_invalid_observations_type(observations: object) -> None:
    report = {
        "observations": observations,
        "interpretation": "This is a valid interpretation.",
        "comparison": None,
    }
    with pytest.raises(
        ValueError,
        match="Report must contain a non-empty list of observations",
    ):
        validate_report(report)


@pytest.mark.parametrize("observation", ["", "   ", None, 0])
def test_invalid_report_invalid_observation(observation: object) -> None:
    report = {
        "observations": ["Observation 1", observation],
        "interpretation": "This is a valid interpretation.",
        "comparison": None,
    }

    with pytest.raises(
        ValueError,
        match="Each observation must contain a non-empty string.",
    ):
        validate_report(report)


def test_invalid_report_missing_interpretation() -> None:
    report = {
        "observations": ["Observation 1", "Observation 2"],
        "comparison": "This is a valid comparison.",
    }
    with pytest.raises(
        ValueError, match="Interpretation must contain a non-empty string."
    ):
        validate_report(report)


@pytest.mark.parametrize("interpretation", ["", "   ", None, 0, []])
def test_invalid_report_invalid_interpretation(interpretation: object) -> None:
    report = {
        "observations": ["Observation 1", "Observation 2"],
        "interpretation": interpretation,
        "comparison": None,
    }
    with pytest.raises(
        ValueError,
        match="Interpretation must contain a non-empty string",
    ):
        validate_report(report)


def test_invalid_report_missing_comparison() -> None:
    report = {
        "observations": ["Observation 1", "Observation 2"],
        "interpretation": "This is a valid interpretation.",
    }
    with pytest.raises(ValueError, match="Report must contain a 'comparison' field."):
        validate_report(report)


@pytest.mark.parametrize("comparison", ["", "   ", [], {}, 0])
def test_invalid_report_invalid_comparison(comparison: object) -> None:
    report = {
        "observations": ["Observation 1", "Observation 2"],
        "interpretation": "This is a valid interpretation.",
        "comparison": comparison,
    }

    with pytest.raises(
        ValueError,
        match="Comparison must be a non-empty string or None",
    ):
        validate_report(report)


def test_main_rejects_invalid_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_demo(text: str) -> dict[str, object]:
        return {
            "observations": [],
            "interpretation": "This is a sample interpretation.",
            "comparison": None,
        }

    monkeypatch.setattr(cli, "cli_demo", fake_demo)

    assert main(["My dog saw another dog and remained calm."]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == (
        "Unable to display report: "
        "Report must contain a non-empty list of observations.\n"
    )
