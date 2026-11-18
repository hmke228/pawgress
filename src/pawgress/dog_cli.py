"""Interactive Epic 2 collection and display, using the existing CLI input helpers."""

import os
from pathlib import Path

from pawgress.ai import AIGenerationError
from pawgress.cli_input import (
    collect_image_paths,
    collect_situation,
    prompt_optional_text,
    prompt_required_text,
)
from pawgress.pipeline import generate_dog_report
from pawgress.storage import ReportStore


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
    observations = report["behavioral_observations"]
    print(f"\nPawgress Dog Report — {report['report_id']}")
    print(f"Created: {report['created_at']}\nScene: {report['scene_context']}")
    for heading, content in (
        ("Safety Assessment", report["safety_assessment"]),
        ("Behavioral Observations", observations["observations"]),
        ("Interpretation", observations["interpretation"]),
        (
            "Comparison",
            observations["comparison"] or "No comparable history available.",
        ),
        ("Recommendations", report["recommendations"]),
    ):
        print(f"\n{heading}:\n{content}")
    print(
        "\nReferenced reports: "
        + (", ".join(report["referenced_report_ids"]) or "None")
    )
    print(f"Report saved to: {store.path}")
