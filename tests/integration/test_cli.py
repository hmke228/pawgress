"""Smoke tests for both installed CLI entry points."""

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest


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
    with patch("pawgress.pipeline.OpenAI", return_value=client), patch(
        "sqlite3.connect", side_effect=AssertionError("Unexpected SQLite access")
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
