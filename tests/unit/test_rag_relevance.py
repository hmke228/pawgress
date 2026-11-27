"""Test RAG retrieval relevance using offline evaluation cases."""

import json
from pathlib import Path

import pytest

from pawgress.rag import retrieve_canine_knowledge

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "rag_relevance_cases.json"
)

with FIXTURE_PATH.open(encoding="utf-8") as file:
    CASES = json.load(file)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_rag_relevance(case):
    """Check the number and source of retrieved references."""
    results = retrieve_canine_knowledge(case["query"])

    assert len(results) == case["expected_matches"]

    if case["expected_matches"] > 0:
        assert case["expected_source_url"] in results[0]["source"]
