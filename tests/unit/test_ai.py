"""Offline contract tests; no generator implementation or AI client."""

import json
from dataclasses import asdict
from typing import get_type_hints

import pytest

from pawgress.ai import AIGenerator, AIResponse


def test_response_serialization_preserves_separate_fields() -> None:
    fields = {"observations": "  A light blinks.  ", "interpretation": "May be ready."}
    response = AIResponse(**fields)
    assert json.loads(json.dumps(asdict(response))) == fields
    assert response.observations == fields["observations"]


@pytest.mark.parametrize("field_name", ["observations", "interpretation"])
@pytest.mark.parametrize("value", [None, 1, True, []])
def test_response_rejects_non_strings(field_name: str, value: object) -> None:
    fields = {"observations": "A light blinks.", "interpretation": "May be ready."}
    fields[field_name] = value
    with pytest.raises(TypeError, match=f"{field_name} must be a string"):
        AIResponse(**fields)


@pytest.mark.parametrize("field_name", ["observations", "interpretation"])
@pytest.mark.parametrize("value", ["", " \t\n"])
def test_response_rejects_blank_fields(field_name: str, value: str) -> None:
    fields = {"observations": "A light blinks.", "interpretation": "May be ready."}
    fields[field_name] = value
    with pytest.raises(ValueError, match=f"{field_name} must not be blank"):
        AIResponse(**fields)


@pytest.mark.parametrize("field_name", ["observations", "interpretation", "summary"])
def test_response_requires_exact_fields(field_name: str) -> None:
    fields = {"observations": "A light blinks.", "interpretation": "May be ready."}
    if field_name == "summary":
        fields[field_name] = "Extra field"
    else:
        del fields[field_name]
    with pytest.raises(TypeError):
        AIResponse(**fields)


def test_generator_contract() -> None:
    assert get_type_hints(AIGenerator.generate) == {
        "user_input": str,
        "rag_context": str,
        "return": AIResponse,
    }
    with pytest.raises(TypeError):
        AIGenerator()
