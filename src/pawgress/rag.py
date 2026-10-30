"""Simple knowledge retrieval for the Pawgress MVP."""

import re

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
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "with",
}


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful words for knowledge retrieval."""
    words = re.findall(r"\b\w+\b", text.lower())

    return {word for word in words if word not in STOP_WORDS}


def retrieve_context(
    query: str, top_k: int | None = None, min_score: int = 1
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

    for entry in KNOWLEDGE_BASE:
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
    """Format retrieved knowledge entries for AI generation."""
    if not entries:
        return ""

    lines = []

    for entry in entries:
        lines.append(f"[{entry['id']}] {entry['text']}")

    return "\n".join(lines)


def build_rag_context(user_input: str) -> str:
    """Retrieve and format knowledge for the AI component."""
    entries = retrieve_context(user_input)
    return format_context(entries)
