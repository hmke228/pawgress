"""CLI entry point for Epic 2 dog reports and the legacy text demonstration."""

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

from pawgress.ai import AIGenerationError
from pawgress.dog_cli import run_dog_cli
from pawgress.pipeline import generate_report
from pawgress.rag import REFERENCE_PATH, KnowledgeRetrievalError


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

    created_at = report.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("Report must contain a 'created_at' timestamp.")

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
        description="Pawgress: dog behavior reports with images and comparable history.",
    )
    parser.add_argument(
        "text", nargs="?", help="Text to process must be enclosed in quotes."
    )
    parser.add_argument(
        "--dog", action="store_true", help="Run the Epic 2 dog workflow."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path.home() / ".local/share/pawgress/pawgress.db",
        help="SQLite file for one dog's profile and report history (--dog).",
    )
    parser.add_argument(
        "--knowledge-base",
        type=Path,
        default=REFERENCE_PATH,
        help="Sourced canine reference JSON file (--dog).",
    )
    args = parser.parse_args(argv)

    if args.dog:
        if args.text is not None:
            parser.error("Use --dog alone; enter the situation at the prompt.")
        try:
            run_dog_cli(args.db, args.knowledge_base)
        except sqlite3.Error as error:
            print(
                f"Unable to access or save report data: {error}\n"
                "Check that the database location is writable. If the database is "
                "locked, close other Pawgress processes using it and try again. "
                "Keep the same --db path to retain your profile and history.",
                file=sys.stderr,
            )
            return 1
        except KnowledgeRetrievalError as error:
            print(
                f"Unable to retrieve canine references: {error}\n"
                "Check the --knowledge-base path and file permissions. "
                "Use a non-empty, validated reference JSON file; ask the "
                "team to repair invalid reference data before retrying.",
                file=sys.stderr,
            )
            return 1
        except AIGenerationError as error:
            print(
                f"Unable to generate dog report: {error}\n"
                "Check the reported cause before retrying: API configuration "
                "or access, quota/rate limits, connection, or an invalid response. "
                "If the problem persists, share the error and request ID with "
                "the team, but never your API key.",
                file=sys.stderr,
            )
            return 1
        except (ValueError, OSError) as error:
            print(f"Unable to generate dog report: {error}", file=sys.stderr)
            return 1
        except (EOFError, KeyboardInterrupt):
            print("Dog report cancelled.", file=sys.stderr)
            return 1
        return 0

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
