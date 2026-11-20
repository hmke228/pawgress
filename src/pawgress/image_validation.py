"""Validate supported image contents before analysis."""

import warnings
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def validate_image(path: Path) -> None:
    """Pipeline requires a readable PNG, JPEG, or WebP with decodable image data."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(path) as image:
                if image.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError(
                        "Unsupported image format. Use PNG, JPEG, or WebP."
                    )
                image.verify()

            # Verification requires reopening before decoding pixel data.
            with Image.open(path) as image:
                image.load()

    except (Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise ValueError(
            "Image dimensions are too large and cannot be processed safely. "
            "Please resize the image and try again."
        ) from error
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ValueError(
            "The image could not be read or decoded. "
            "Please check permissions or export a new PNG, JPEG, or WebP copy."
        ) from error
