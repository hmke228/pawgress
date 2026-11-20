"""Offline tests for image-content validation."""

from pathlib import Path

import pytest
from PIL import Image

from pawgress.image_validation import validate_image


@pytest.mark.parametrize("image_format", ["PNG", "JPEG", "WEBP"])
def test_accepts_supported_image(
    tmp_path: Path,
    image_format: str,
) -> None:
    # Ensure validation uses contents, not filenames.
    path = tmp_path / "photo.bin"
    with Image.new("RGB", (8, 8), color="blue") as image:
        image.save(path, format=image_format)

    validate_image(path)


def test_rejects_unsupported_format(tmp_path: Path) -> None:
    # A JPEG extension must not disguise GIF contents.
    path = tmp_path / "photo.jpg"
    with Image.new("RGB", (8, 8), color="blue") as image:
        image.save(path, format="GIF")

    with pytest.raises(ValueError, match="Unsupported image format"):
        validate_image(path)


@pytest.mark.parametrize(
    "contents",
    [
        b"",
        b"This is not an image.",
        b"\x89PNG\r\n\x1a\n",
    ],
    ids=["empty-file", "text-file", "incomplete-png"],
)
def test_rejects_invalid_image(
    tmp_path: Path,
    contents: bytes,
) -> None:
    path = tmp_path / "photo.png"
    path.write_bytes(contents)

    with pytest.raises(ValueError, match="could not be read or decoded"):
        validate_image(path)


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="could not be read or decoded"):
        validate_image(tmp_path / "missing.png")
