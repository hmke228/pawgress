"""Direct unit tests for the CLI and module entry point."""

import runpy
import sys

import pytest

from pawgress.cli import main


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
