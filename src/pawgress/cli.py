"""Minimal command-line entry point for Pawgress."""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Show CLI help; application commands will be added in future work."""
    parser = argparse.ArgumentParser(
        prog="pawgress",
        description="Pawgress CLI scaffold. Application features are not implemented yet.",
    )
    parser.parse_args(argv)
    parser.print_help()
    return 0
