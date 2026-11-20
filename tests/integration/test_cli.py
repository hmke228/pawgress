"""Smoke tests for both installed CLI entry points."""

import os
import sqlite3
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

import pawgress.cli as cli
from pawgress.ai import AIGenerationError
from pawgress.rag import KnowledgeRetrievalError


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


@pytest.mark.parametrize(
    "entry", ["pawgress", str(Path(sysconfig.get_path("scripts")) / "pawgress")]
)
@pytest.mark.parametrize("failed", [False, True])
def test_complete_pipeline(entry: str, failed: bool, tmp_path: Path) -> None:
    """Run each real entry point in a child process; replace only HTTP transport."""
    script = """
import json
import os
import runpy
import sys
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
    with (
        patch("pawgress.pipeline.OpenAI", return_value=client),
        patch(
            "pawgress.pipeline.compare_reports",
            return_value={
                "comparison_summary": (
                    "Consistent observations include barking. "
                    "Newly observed behaviors include jumping. "
                    "Previously observed behaviors not mentioned in the current report "
                    "include relaxed posture."
                ),
                "referenced_report_ids": ["epic1-mock-history"],
            },
        ),
        patch("sqlite3.connect", side_effect=AssertionError("Unexpected SQLite access")),
    ):
        if entry == "pawgress":
            runpy.run_module(entry, run_name="__main__")
        else:
            runpy.run_path(entry, run_name="__main__")
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
        assert "OpenAI request failed." in result.stderr
        assert "HTTP 500" in result.stderr
        assert "Offline failure" in result.stderr
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


def test_storage_failure_shows_recovery_steps(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_storage(*args, **kwargs) -> None:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(cli, "run_dog_cli", fail_storage)

    assert cli.main(["--dog"]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert "database is locked" in output.err
    assert "close other Pawgress processes" in output.err
    assert "Keep the same --db path" in output.err
    assert "Traceback" not in output.err


def test_reference_failure_shows_recovery_steps(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_retrieval(*args, **kwargs) -> None:
        raise KnowledgeRetrievalError("Reference file is missing.")

    monkeypatch.setattr(cli, "run_dog_cli", fail_retrieval)

    assert cli.main(["--dog"]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert "Unable to retrieve canine references" in output.err
    assert "Reference file is missing." in output.err
    assert "--knowledge-base" in output.err
    assert "file permissions" in output.err
    assert "Traceback" not in output.err


def test_generation_failure_shows_recovery_steps(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_generation(*args, **kwargs) -> None:
        raise AIGenerationError("HTTP 429; quota exhausted; request ID: req_test")

    monkeypatch.setattr(cli, "run_dog_cli", fail_generation)

    assert cli.main(["--dog"]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert "HTTP 429; quota exhausted; request ID: req_test" in output.err
    assert "Check the reported cause before retrying" in output.err
    assert "never your API key" in output.err
    assert "Traceback" not in output.err
