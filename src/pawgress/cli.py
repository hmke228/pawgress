"""Collect text and display the complete Epic 1 report."""

import argparse
import sys
from collections.abc import Sequence

from pawgress.ai import AIGenerationError
from pawgress.pipeline import generate_report


def validate_report(report: object) -> None:
    """Validate the structure and content of a returned report."""
    if not isinstance(report, dict):
        raise ValueError("Report must be a dictionary.")

    observations = report.get("observations")
    if not isinstance(observations, str) or not observations.strip():
        raise ValueError("Observations must contain a non-empty string.")

    interpretation = report.get("interpretation")
    if not isinstance(interpretation, str) or not interpretation.strip():
        raise ValueError("Interpretation must contain a non-empty string.")

    if "comparison" not in report:
        raise ValueError("Report must contain a 'comparison' field.")

    comparison = report["comparison"]
    if comparison is not None:
        if not isinstance(comparison, str) or not comparison.strip():
            raise ValueError("Comparison must be a non-empty string or None.")


def display_report(
    observations: str,
    interpretation: str,
    comparison: str | None,
) -> None:
    """Display the report generated from AI and Comparison components."""
    print(f"Observations:\n\t{observations}")
    print(f"Interpretation:\n\t{interpretation}")
    if comparison is None:
        print("Comparison:\n\tNot available.")
    else:
        print(f"Comparison:\n\t{comparison}")


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

    try:
        report = generate_report(text)
        validate_report(report)
    except (ValueError, AIGenerationError) as error:
        print(f"Unable to display report: {error}", file=sys.stderr)
        return 1

    print("\nEpic 1 Report — Comparison uses mock history\n")
    display_report(
        observations=report["observations"],
        interpretation=report["interpretation"],
        comparison=report["comparison"],
    )
    print("\nEnd of Report\n")
    return 0
