"""Tests for Epic 2 workflow input collection."""

from pathlib import Path

import pytest

from pawgress.cli_input import (
    collect_image_paths,
    collect_situation,
    prompt_optional_text,
    prompt_required_text,
)


def test_retry_empty_required_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    inputs = iter(["", "   ", "  Valid Dog  "])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = prompt_required_text("Dog Name: ")

    assert result == "Valid Dog"
    output = capsys.readouterr()
    assert output.out == (
        "Please enter a non-empty value. This field is required.\n"
        "Please enter a non-empty value. This field is required.\n"
    )


@pytest.mark.parametrize(
    ("entered_text", "expected"),
    [
        ("", None),
        ("   ", None),
        ("  Usually calm around other dogs.  ", "Usually calm around other dogs."),
    ],
)
def test_optional_text(
    entered_text: str,
    expected: str | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: entered_text)

    assert prompt_optional_text("Background (optional): ") == expected
    assert capsys.readouterr().out == ""


def test_first_situation_requires_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(["", "  Another dog approached.  "])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert collect_situation(has_previous_reports=False) == "Another dog approached."


@pytest.mark.parametrize(
    ("entered_text", "expected"),
    [
        ("", None),
        ("   ", None),
        ("  Walking in the park.  ", "Walking in the park."),
    ],
)
def test_later_situation_is_optional(
    entered_text: str,
    expected: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: entered_text)

    assert collect_situation(has_previous_reports=True) == expected


def test_image_paths_preserve_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first photo.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"test fixture")
    second.write_bytes(b"test fixture")

    responses = iter([str(second), str(first), "done"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert collect_image_paths(minimum_count=2) == [
        str(second.resolve()),
        str(first.resolve()),
    ]


def test_image_paths_reject_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valid_file = tmp_path / "photo.jpg"
    valid_file.write_bytes(b"test fixture")

    responses = iter(
        [
            str(tmp_path / "missing.jpg"),
            str(valid_file),
            "done",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert collect_image_paths(minimum_count=1) == [str(valid_file.resolve())]
    assert "The provided path does not point to a file." in capsys.readouterr().out


def test_image_paths_reject_duplicates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valid_file = tmp_path / "photo.jpg"
    valid_file.write_bytes(b"test fixture")

    responses = iter([str(valid_file), str(valid_file), "done"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert collect_image_paths(minimum_count=1) == [str(valid_file.resolve())]
    assert "The provided file has already been added." in capsys.readouterr().out


def test_image_paths_require_minimum_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"test fixture")
    second.write_bytes(b"test fixture")

    responses = iter([str(first), "done", str(second), "done"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert collect_image_paths(minimum_count=2) == [
        str(first.resolve()),
        str(second.resolve()),
    ]
    assert "Please provide at least 2 image file(s)." in capsys.readouterr().out


def test_image_paths_reject_blank_and_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valid_file = tmp_path / "photo.jpg"
    valid_file.write_bytes(b"test fixture")

    responses = iter(["   ", str(tmp_path), str(valid_file), "done"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert collect_image_paths(minimum_count=1) == [str(valid_file.resolve())]

    output = capsys.readouterr()
    assert "Please enter a file path." in output.out
    assert "The provided path does not point to a file." in output.out


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, EOFError])
def test_image_collection_can_be_interrupted(
    exception_type: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupted_input(prompt: str) -> str:
        raise exception_type()

    monkeypatch.setattr("builtins.input", interrupted_input)

    with pytest.raises(exception_type):
        collect_image_paths(minimum_count=1)


def test_image_paths_retry_expansion_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valid_file = tmp_path / "photo.jpg"
    valid_file.write_bytes(b"test fixture")
    original_expanduser = Path.expanduser

    def fake_expanduser(path: Path) -> Path:
        if str(path) == "~missing/photo.jpg":
            raise RuntimeError("Home directory could not be resolved.")
        return original_expanduser(path)

    responses = iter(["~missing/photo.jpg", str(valid_file), "done"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(Path, "expanduser", fake_expanduser)

    assert collect_image_paths(minimum_count=1) == [str(valid_file.resolve())]
    assert (
        "The provided file could not be read. Please check the path and permissions."
    ) in capsys.readouterr().out
