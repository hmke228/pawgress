"""Interactive Epic 2 collection and display, using the existing CLI input helpers."""

import os
from pathlib import Path
from textwrap import indent

from pawgress.ai import AIGenerationError
from pawgress.cli_input import (
    collect_image_paths,
    collect_situation,
    prompt_optional_text,
    prompt_required_text,
)
from pawgress.pipeline import generate_dog_report
from pawgress.storage import ReportStore


def display_dog_report(report: dict, database: Path) -> None:
    """Display all three report sections, with behavioral details grouped together."""
    behavior = report["behavioral_observations"]
    comparison = behavior["comparison"]
    if comparison is None:
        comparison = "No comparable history available."

    print(f"\nPawgress Dog Report — {report['report_id']}")
    print(f"Created: {report['created_at']}")
    print(f"Scene: {report['scene_context']}")

    print("\n1. Safety Assessment")
    print(report["safety_assessment"])

    print("\n2. Behavioral Observations")
    for heading, content in (
        ("Observations", behavior["observations"]),
        ("Interpretation", behavior["interpretation"]),
        ("Comparison", comparison),
    ):
        print(f"\n  {heading}:")
        print(indent(content, "    "))

    print("\n3. Recommendations")
    print(report["recommendations"])

    references = ", ".join(report["referenced_report_ids"]) or "None"
    print(f"\nReferenced reports: {references}")
    print(f"Report saved to: {database}")


def run_dog_cli(database: Path, reference_path: Path) -> None:
    """Reuse one dog's profile and print the completed, persisted report."""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise AIGenerationError("Set OPENAI_API_KEY and OPENAI_MODEL before running.")
    store = ReportStore(database)
    profile = store.load_profile()
    if profile is None:
        profile = {
            "name": prompt_required_text("Dog's name: "),
            "description": prompt_required_text(
                "Dog's appearance, basic details and behavioral background: "
            ),
        }
        store.save_profile(profile)
    print(f"Dog: {profile['name']}\nSaved profile: {profile['description']}")
    situation = collect_situation(has_previous_reports=bool(store.previous_reports()))
    image_paths = collect_image_paths(minimum_count=1)
    target_hint = (
        prompt_optional_text(
            "Which dog in the images is yours? (optional identifying details): "
        )
        or ""
    )
    print("Generating report and checking comparable history...", flush=True)
    report = generate_dog_report(
        profile, image_paths, situation, target_hint, store, reference_path
    )
    display_dog_report(report, store.path)
