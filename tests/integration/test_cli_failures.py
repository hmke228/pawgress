"""Offline subprocess checks for CLI failure messages and exit statuses."""

import subprocess
import sys

import pytest

FAILURE_SCRIPT = """
import runpy
import sqlite3
import sys
from unittest.mock import patch

from pawgress.ai import AIGenerationError
from pawgress.rag import KnowledgeRetrievalError

errors = {
    "storage": sqlite3.OperationalError("database is locked"),
    "references": KnowledgeRetrievalError("Reference file is missing."),
    "generation": AIGenerationError("HTTP 429; quota exhausted"),
}

error = errors[sys.argv[1]]
sys.argv = ["pawgress", "--dog"]

with patch("pawgress.cli.run_dog_cli", side_effect=error):
    runpy.run_module("pawgress", run_name="__main__")
"""


@pytest.mark.parametrize(
    ("failure", "expected_message", "recovery_hint"),
    [
        (
            "storage",
            "database is locked",
            "Keep the same --db path",
        ),
        (
            "references",
            "Unable to retrieve canine references",
            "--knowledge-base",
        ),
        (
            "generation",
            "HTTP 429; quota exhausted",
            "Check the reported cause before retrying",
        ),
    ],
)
def test_cli_failure_message(
    failure: str,
    expected_message: str,
    recovery_hint: str,
) -> None:
    result = subprocess.run(
        [sys.executable, "-c", FAILURE_SCRIPT, failure],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert expected_message in result.stderr
    assert recovery_hint in result.stderr
    assert "Traceback" not in result.stderr
