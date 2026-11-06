"""Epic 1 text pipeline with one illustrative historical report."""

import os
from dataclasses import asdict

from openai import OpenAI

from pawgress.ai import AIGenerationError, AIGenerator
from pawgress.behavioral_comparison import compare_reports
from pawgress.openai_generator import OpenAIGenerator
from pawgress.rag import build_rag_context


def run_pipeline(user_input: str, generator: AIGenerator) -> dict[str, str]:
    """Generate two AI fields, then append a deterministic comparison summary."""
    context = build_rag_context(user_input)
    response = generator.generate(user_input, context)
    comparison = compare_reports(
        response.observations,
        [
            {
                "report_id": "epic1-mock-history",
                "behavioral_observations": {
                    "current": "The dog barked and stayed calm."
                },
            }
        ],
    )
    return {**asdict(response), "comparison": comparison["comparison_summary"]}


def generate_report(user_input: str) -> dict[str, str]:
    """Run the pipeline with the existing OpenAI adapter and environment config."""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise AIGenerationError("Set OPENAI_API_KEY and OPENAI_MODEL before running.")
    with OpenAI(max_retries=0) as client:
        return run_pipeline(
            user_input, OpenAIGenerator(client, model=os.environ["OPENAI_MODEL"])
        )
