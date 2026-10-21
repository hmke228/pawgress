"""Minimal command-line entry point for Pawgress."""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Accept & validate command-line arguments and process the input text."""
    parser = argparse.ArgumentParser(
        prog="pawgress",
        description="Pawgress Demo - This CLI accepts simple text input.",
    )
    parser.add_argument(
        "text", nargs="?", help="Text to process must be enclosed in quotes."
    )
    args = parser.parse_args(argv)

    if args.text is None:
        parser.print_help()
        return 0

    text = args.text.strip()
    if not text:
        parser.error("No text provided.")

    print(f"Received text: {text}")
    return 0
