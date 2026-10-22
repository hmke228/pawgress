"""Simple knowledge retrieval for the Pawgress MVP."""

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


def retrieve_context(query: str) -> list[dict[str, str]]:
    """Return knowledge entries containing words from the query."""
    query_words = set(query.lower().split())

    if not query_words:
        return []

    matches = []

    for entry in KNOWLEDGE_BASE:
        entry_words = set(entry["text"].lower().split())

        if query_words & entry_words:
            matches.append(entry)

    return matches
