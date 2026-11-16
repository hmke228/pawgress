"""Smoke tests for both installed CLI entry points."""

import os
import runpy
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

import pawgress.cli as cli
from pawgress.ai import AIGenerationError


def test_main_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([]) == 0
    output = capsys.readouterr()
    assert "usage: pawgress" in output.out
    assert output.err == ""


def test_module_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["pawgress"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("pawgress", run_name="__main__")
    assert error.value.code == 0


@pytest.mark.parametrize("text", ["", "   "])
def test_main_rejects_empty_text(text: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main([text])
    assert error.value.code == 2
    assert "No text provided." in capsys.readouterr().err


def test_main_displays_valid_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_report(text: str) -> dict[str, str | None]:
        assert text == "My dog barked."
        return {
            "observations": "The dog barked.",
            "interpretation": "The dog may be excited.",
            "comparison": "Consistent with earlier reports.",
        }

    monkeypatch.setattr(cli, "generate_report", fake_report)
    assert cli.main([" My dog barked. "]) == 0
    output = capsys.readouterr()
    assert "Observations:\n\tThe dog barked.\n" in output.out
    assert "Comparison:\n\tConsistent with earlier reports.\n" in output.out
    assert output.err == ""


@pytest.mark.parametrize(
    ("report", "message"),
    [
        (None, "Report must be a dictionary."),
        (
            {"observations": "", "interpretation": "Valid", "comparison": None},
            "Observations must contain a non-empty string.",
        ),
        (
            {"observations": "Valid", "interpretation": " ", "comparison": None},
            "Interpretation must contain a non-empty string.",
        ),
        (
            {"observations": "Valid", "interpretation": "Valid"},
            "Report must contain a 'comparison' field.",
        ),
        (
            {"observations": "Valid", "interpretation": "Valid", "comparison": ""},
            "Comparison must be a non-empty string or None.",
        ),
    ],
)
def test_main_reports_invalid_report(
    report: object,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "generate_report", lambda text: report)
    assert cli.main(["My dog barked."]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert f"Unable to display report: {message}" in output.err


def test_main_reports_generation_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_generation(text: str) -> dict[str, str]:
        raise AIGenerationError("Offline failure")

    monkeypatch.setattr(cli, "generate_report", fail_generation)
    assert cli.main(["My dog barked."]) == 1
    assert capsys.readouterr().err == ("Unable to display report: Offline failure\n")


def test_validate_report_accepts_no_comparison() -> None:
    cli.validate_report(
        {
            "observations": "The dog barked.",
            "interpretation": "The dog may be excited.",
            "comparison": None,
        }
    )


def test_display_report_without_comparison(capsys: pytest.CaptureFixture[str]) -> None:
    cli.display_report("Observed barking.", "Uncertain.", None)
    assert capsys.readouterr().out.endswith("Comparison:\n\tNot available.\n")


@pytest.mark.parametrize(
    "command",
    [
        [sys.executable, "-m", "pawgress"],
        [str(Path(sysconfig.get_path("scripts")) / "pawgress")],
    ],
    ids=["module", "console-script"],
)
@pytest.mark.parametrize(
    ("arguments", "expected_code"),
    [([], 0), (["--help"], 0), (["--unknown-option"], 2)],
    ids=["no-arguments", "help", "invalid-option"],
)
def test_cli(
    command: list[str],
    arguments: list[str],
    expected_code: int,
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [*command, *arguments],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == expected_code
    if expected_code == 0:
        assert "usage: pawgress" in result.stdout
        assert "--help" in result.stdout
        assert result.stderr == ""
    else:
        assert "unrecognized arguments" in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        [sys.executable, "-m", "pawgress"],
        [str(Path(sysconfig.get_path("scripts")) / "pawgress")],
    ],
    ids=["module", "console-script"],
)
@pytest.mark.parametrize(
    ("input_text", "expected_code"),
    [
        ("My dog saw another dog and remained calm.", 1),
        ("", 2),
        ("   ", 2),
    ],
    ids=["valid-text", "empty-text", "whitespace"],
)
def test_cli_text_input(
    command: list[str],
    input_text: str,
    expected_code: int,
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [*command, input_text],
        cwd=tmp_path,
        env={
            key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == expected_code

    if expected_code == 1:
        assert "Set OPENAI_API_KEY and OPENAI_MODEL" in result.stderr
        assert result.stdout == ""
    else:
        assert "No text provided." in result.stderr
        assert result.stdout == ""


@pytest.mark.parametrize("entry", ["module", "console-script"])
@pytest.mark.parametrize("failed", [False, True])
def test_complete_pipeline(entry: str, failed: bool, tmp_path: Path) -> None:
    """Run each real entry point in a child process; replace only HTTP transport."""
    script = """
import json
import os
import runpy
import sys
from importlib.metadata import entry_points
from unittest.mock import patch
import httpx
from openai import OpenAI

entry, failed = sys.argv[1:]
sys.argv = [entry, "My dog has a tucked tail."]
os.environ["OPENAI_API_KEY"] = "offline-test"
os.environ["OPENAI_MODEL"] = "test-model"
fields = {"observations": "  The dog barked and jumped.  ", "interpretation": "Uncertain."}
def handle(request):
    body = json.loads(request.content)
    assert json.loads(body["input"]) == {
        "user_input": sys.argv[1],
        "rag_context": "[entry_1] A tucked tail can be a sign of fear or discomfort.",
    }
    if failed == "True":
        return httpx.Response(500, json={"error": {"message": "Offline failure"}})
    return httpx.Response(200, json={"status": "completed", "output": [{
        "type": "message", "role": "assistant", "content": [{
            "type": "output_text", "text": json.dumps(fields), "annotations": []
        }]
    }]})
with OpenAI(max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handle))) as client:
    with patch("pawgress.pipeline.OpenAI", return_value=client), patch(
        "sqlite3.connect", side_effect=AssertionError("Unexpected SQLite access")
    ):
        if entry == "module":
            runpy.run_module("pawgress", run_name="__main__")
        else:
            cli = next(
                point for point in entry_points(group="console_scripts")
                if point.name == "pawgress"
            )
            raise SystemExit(cli.load()())
"""
    result = subprocess.run(
        [sys.executable, "-c", script, entry, str(failed)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == int(failed), result.stderr
    if failed:
        assert "Unable to display report: OpenAI request failed:" in result.stderr
        assert result.stdout == ""
    else:
        assert "Observations:\n\t  The dog barked and jumped.  \n" in result.stdout
        assert "Interpretation:\n\tUncertain.\n" in result.stdout
        assert (
            "Comparison:\n\tConsistent observations include barking." in result.stdout
        )
        assert "Newly observed behaviors include jumping." in result.stdout
        assert "include relaxed posture." in result.stdout
        assert result.stderr == ""
