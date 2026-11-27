"""Simple knowledge retrieval for the Pawgress MVP."""

import re
from pathlib import Path

from pawgress.knowledge_base import load_knowledge_base

REFERENCE_PATH = Path(__file__).with_name("data") / "canine_references.json"


class KnowledgeRetrievalError(ValueError):
    """Professional reference data could not be loaded or used."""


def retrieve_canine_knowledge(
    situation: str | None, reference_path: Path = REFERENCE_PATH
) -> list[dict[str, str]]:
    """Retrieve relevant sourced references without unrelated fallback."""
    try:
        references = load_knowledge_base(reference_path)
    except (OSError, ValueError) as error:
        raise KnowledgeRetrievalError(
            f"Unable to load canine references from '{reference_path}': {error}"
        ) from error

    if not references:
        raise KnowledgeRetrievalError(
            "Populate the canine knowledge base before generating reports."
        )

    if situation and situation.strip():
        matches = retrieve_context(situation, knowledge_base=references)
    else:
        matches = references

    return [
        {
            "source": f"{entry['source_title']} ({entry['source_url']})",
            "content": entry["text"],
        }
        for entry in matches
    ]


KNOWLEDGE_BASE = [
    {
        "id": "entry_1",
        "text": "A tucked tail can be a sign of fear or discomfort.",
    },
    {
        "id": "entry_2",
        "text": "A play bow can indicate playful behavior.",
    },
    {
        "id": "entry_3",
        "text": "Stiff body posture can indicate tension.",
    },
]


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "dog",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "its",
    "it's",
    "my",
    "of",
    "on",
    "or",
    "s",
    "someone",
    "the",
    "to",
    "was",
    "when",
    "with",
}


NORMALIZED_TERMS = {
    "barks": "bark",
    "barking": "bark",
    "barked": "bark",
    "growls": "growl",
    "growling": "growl",
    "growled": "growl",
}


def extract_keywords(text: str) -> set[str]:
    """Extract and normalize meaningful words for knowledge retrieval."""
    words = re.findall(r"\b\w+\b", text.lower())

    return {
        NORMALIZED_TERMS.get(word, word) for word in words if word not in STOP_WORDS
    }


def retrieve_context(
    query: str,
    top_k: int | None = None,
    min_score: int = 1,
    knowledge_base: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Retrieve references ranked by keyword overlap."""
    if top_k is not None and top_k < 0:
        raise ValueError("top_k must be non-negative")

    if min_score < 1:
        raise ValueError("min_score must be at least 1")

    query_words = extract_keywords(query)

    if not query_words or top_k == 0:
        return []

    matches = []

    for entry in knowledge_base if knowledge_base is not None else KNOWLEDGE_BASE:
        entry_words = extract_keywords(entry["text"])
        score = len(query_words & entry_words)

        # Only include entries that meet the minimum score.
        if score >= min_score:
            matches.append((score, entry))

    # Put the strongest matches first.
    matches.sort(key=lambda item: item[0], reverse=True)

    # Limit the number of references when requested.
    if top_k is not None:
        matches = matches[:top_k]

    return [entry for score, entry in matches]


def format_context(entries: list[dict[str, str]]) -> str:
    """Format retrieved knowledge entries with available source information."""
    if not entries:
        return ""

    lines = []

    for entry in entries:
        line = f"[{entry['id']}] {entry['text']}"

        if "source_title" in entry and "source_url" in entry:
            line += f"\nSource: {entry['source_title']} ({entry['source_url']})"

        lines.append(line)

    return "\n".join(lines)


def build_rag_context(
    user_input: str,
    knowledge_base: list[dict[str, str]] | None = None,
) -> str:
    """Retrieve and format knowledge for the AI component."""
    entries = retrieve_context(user_input, knowledge_base=knowledge_base)
    return format_context(entries)
