"""Smoke tests for both installed CLI entry points."""

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
