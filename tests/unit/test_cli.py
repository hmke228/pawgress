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
def test_valid_input(
    text: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_report(user_input: str) -> dict[str, str]:
        assert user_input == "Woof Woof Woof!"
        return {
            "observations": "The dog barked.",
            "interpretation": "Its emotional state is uncertain.",
            "comparison": "Consistent observations include barking.",
            "created_at": "2026-01-01T00:00:00+00:00",
        }

    monkeypatch.setattr(cli, "generate_report", fake_report)
    assert main([text]) == 0
    output = capsys.readouterr()
    assert output.out == (
        "\nEpic 1 Report — Comparison uses mock history\n\n"
        "Observations:\n"
        "\tThe dog barked.\n"
        "Interpretation:\n"
        "\tIts emotional state is uncertain.\n"
        "Comparison:\n"
        "\tConsistent observations include barking.\n"
        "\nEnd of Report\n\n"
    )
    assert output.err == ""


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_input(
    text: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def reject_demo_call(text: str) -> dict[str, object]:
        pytest.fail("generate_report cannot be called for empty input.")

    monkeypatch.setattr(cli, "generate_report", reject_demo_call)

    with pytest.raises(SystemExit) as error:
        main([text])

    assert error.value.code == 2
    output = capsys.readouterr()
    assert "No text provided." in output.err
    assert output.out == ""


def test_display_report_with_comparison(capsys: pytest.CaptureFixture[str]) -> None:
    display_report(
        observations="This is a sample observation.",
        interpretation="This is a sample interpretation.",
        comparison="This is a sample comparison.",
    )
    output = capsys.readouterr()
    assert output.out == (
        "Observations:\n"
        "\tThis is a sample observation.\n"
        "Interpretation:\n"
        "\tThis is a sample interpretation.\n"
        "Comparison:\n"
        "\tThis is a sample comparison.\n"
    )
    assert output.err == ""


def test_display_report_without_comparison(capsys: pytest.CaptureFixture[str]) -> None:
    display_report(
        observations="This is a sample observation.",
        interpretation="This is a sample interpretation.",
        comparison=None,
    )
    output = capsys.readouterr()
    assert output.out == (
        "Observations:\n"
        "\tThis is a sample observation.\n"
        "Interpretation:\n"
        "\tThis is a sample interpretation.\n"
        "Comparison:\n"
        "\tNot available.\n"
    )
    assert output.err == ""


@pytest.mark.parametrize("comparison", ["This is a valid comparison.", None])
def test_valid_report(comparison: str | None) -> None:
    report = {
        "observations": "This is a valid observation.",
        "interpretation": "This is a valid interpretation.",
        "comparison": comparison,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    validate_report(report)


@pytest.mark.parametrize("created_at", ["", "   ", None, 0])
def test_invalid_report_created_at(created_at: object) -> None:
    report = {
        "observations": "This is a valid observation.",
        "interpretation": "This is a valid interpretation.",
        "comparison": None,
        "created_at": created_at,
    }
    with pytest.raises(
        ValueError, match="Report must contain a 'created_at' timestamp."
    ):
        validate_report(report)


def test_invalid_report_missing_created_at() -> None:
    report = {
        "observations": "This is a valid observation.",
        "interpretation": "This is a valid interpretation.",
        "comparison": None,
    }
    with pytest.raises(
        ValueError, match="Report must contain a 'created_at' timestamp."
    ):
        validate_report(report)


@pytest.mark.parametrize("report", [None, [], "invalid report", 0])
def test_invalid_report_type(report: object) -> None:
    with pytest.raises(ValueError, match="Report must be a dictionary"):
        validate_report(report)


def test_invalid_report_missing_observations() -> None:
    report = {
        "interpretation": "This is a valid interpretation.",
        "comparison": "This is a valid comparison.",
    }
    with pytest.raises(
        ValueError, match="Observations must contain a non-empty string."
    ):
        validate_report(report)


@pytest.mark.parametrize("observations", ["", "   ", None, ["Observation"], 0])
def test_invalid_observations(observations: object) -> None:
    report = {
        "observations": observations,
        "interpretation": "This is a valid interpretation.",
        "comparison": None,
    }
    with pytest.raises(
        ValueError,
        match="Observations must contain a non-empty string.",
    ):
        validate_report(report)


def test_invalid_report_missing_interpretation() -> None:
    report = {
        "observations": "This is a valid observation.",
        "comparison": "This is a valid comparison.",
    }
    with pytest.raises(
        ValueError, match="Interpretation must contain a non-empty string."
    ):
        validate_report(report)


@pytest.mark.parametrize("interpretation", ["", "   ", None, 0, []])
def test_invalid_report_invalid_interpretation(interpretation: object) -> None:
    report = {
        "observations": "This is a valid observation.",
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
        "observations": "This is a valid observation.",
        "interpretation": "This is a valid interpretation.",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    with pytest.raises(ValueError, match="Report must contain a 'comparison' field."):
        validate_report(report)


@pytest.mark.parametrize("comparison", ["", "   ", [], {}, 0])
def test_invalid_report_invalid_comparison(comparison: object) -> None:
    report = {
        "observations": "This is a valid observation.",
        "interpretation": "This is a valid interpretation.",
        "comparison": comparison,
        "created_at": "2026-01-01T00:00:00+00:00",
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
            "observations": "",
            "interpretation": "This is a sample interpretation.",
            "comparison": None,
        }

    monkeypatch.setattr(cli, "generate_report", fake_demo)

    assert main(["My dog saw another dog and remained calm."]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == (
        "Unable to display report: Observations must contain a non-empty string.\n"
    )
