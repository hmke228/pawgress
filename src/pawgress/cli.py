"""Command-line entry point for Pawgress: Demo accepts and validates user input text and displays a report with placeholder data"""

import argparse
import sys
from collections.abc import Sequence


def validate_report(report: object) -> None:
    """Validate the structure and content of a returned report."""
    if not isinstance(report, dict):
        raise ValueError("Report must be a dictionary.")

    observations = report.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("Report must contain a non-empty list of observations.")

    for observation in observations:
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError("Each observation must contain a non-empty string.")

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
    observations: Sequence[str],
    interpretation: str,
    comparison: str | None,
) -> None:
    """Display the report generated from AI and Comparison components."""
    print("Observations:")
    for obs in observations:
        print(f"      - {obs}")
    print(f"Interpretation:\n\t{interpretation}")
    if comparison is None:
        print("Comparison:\n\tNot available.")
    else:
        print(f"Comparison:\n\t{comparison}")


def cli_demo(text: str) -> dict[str, object]:
    """Return placeholder data until the shared pipeline is connected."""
    return {
        "observations": ["Observation Placeholder", f"User-Provided Text: {text}"],
        "interpretation": "Interpretation Placeholder - no AI analysis was performed.",
        "comparison": None,
    }


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
        report = cli_demo(text)
        validate_report(report)
    except ValueError as error:
        print(f"Unable to display report: {error}", file=sys.stderr)
        return 1

    print("\nDemo Output — Placeholder Data\n")
    display_report(
        observations=report["observations"],
        interpretation=report["interpretation"],
        comparison=report["comparison"],
    )
    print("\nEnd of Demo Output\n")
    return 0
