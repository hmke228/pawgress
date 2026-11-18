"""Epic 2 dog-report orchestration and the legacy Epic 1 text demonstration."""

import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from pawgress.ai import AIGenerationError, AIGenerator
from pawgress.behavioral_comparison import compare_reports, complete_dog_report
from pawgress.dog_report import DogReportInput
from pawgress.openai_generator import OpenAIGenerator
from pawgress.rag import REFERENCE_PATH, build_rag_context, retrieve_canine_knowledge
from pawgress.storage import ReportStore


def generate_dog_report(
    profile: dict,
    image_paths: list[str],
    situation: str | None,
    target_hint: str,
    store: ReportStore,
    reference_path: Path = REFERENCE_PATH,
) -> dict:
    """Connect sourced RAG, vision generation, history comparison and persistence."""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise AIGenerationError("Set OPENAI_API_KEY and OPENAI_MODEL before running.")
    request = DogReportInput(
        profile,
        image_paths,
        retrieve_canine_knowledge(situation, reference_path),
        situation,
        target_hint,
    )
    with OpenAI(max_retries=0) as client:
        model = os.environ["OPENAI_MODEL"]
        current = OpenAIGenerator(client, model).generate_dog_report(request)
        report = current.to_report_content() | {
            "report_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return complete_dog_report(report, store, client, model)


def run_pipeline(user_input: str, generator: AIGenerator) -> dict[str, str]:
    """Generate two AI fields, then compare against illustrative mock history."""
    context = build_rag_context(user_input)
    response = generator.generate(user_input, context)
    comparison = compare_reports(
        response.observations,
        [
            {
                "report_id": "epic1-mock-history",
                "created_at": "2026-01-01T00:00:00+00:00",
                "scene_context": None,
                "behavioral_observations": {
                    "current": "The dog barked and stayed calm."
                },
            }
        ],
    )
    report = {**asdict(response), "comparison": comparison["comparison_summary"]}
    report["created_at"] = datetime.now(timezone.utc).isoformat()
    return report


def generate_report(user_input: str) -> dict[str, str]:
    """Run the pipeline with the existing OpenAI adapter and environment config."""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise AIGenerationError("Set OPENAI_API_KEY and OPENAI_MODEL before running.")
    with OpenAI(max_retries=0) as client:
        return run_pipeline(
            user_input, OpenAIGenerator(client, model=os.environ["OPENAI_MODEL"])
        )
