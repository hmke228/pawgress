"""Provider-independent AI contract for the Epic 1 text prototype."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AIResponse:
    """Two required strings; serialize with dataclasses.asdict.

    observations: Input-grounded facts without unsupported behavioral inferences.
    interpretation: Input/context-informed interpretation expressing uncertainty.
    Validation checks structure, not factual accuracy or quality of interpretation.
    """

    observations: str
    interpretation: str

    def __post_init__(self) -> None:
        for field_name in ("observations", "interpretation"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if not value.strip():
                raise ValueError(f"{field_name} must not be blank")


class AIGenerator(Protocol):
    """Provider-independent contract for text generation."""

    def generate(self, user_input: str, rag_context: str) -> AIResponse: ...


class AIGenerationError(RuntimeError):
    """Generation failed or returned an unusable response."""
