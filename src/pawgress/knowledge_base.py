"""Load and validate canine behavior knowledge references."""

import json
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FIELDS = {
    "id",
    "topic",
    "text",
    "source_title",
    "source_url",
}


def validate_reference(entry: object) -> dict[str, str]:
    """Check that a knowledge entry contains valid source information."""
    if not isinstance(entry, dict):
        raise ValueError("Knowledge entry must be a dictionary.")

    for field in REQUIRED_FIELDS:
        value = entry.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Knowledge entry has an invalid {field}.")

    parsed_url = urlparse(entry["source_url"])

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise ValueError("Knowledge entry must have a valid source URL.")

    return entry


def load_knowledge_base(file_path: str | Path) -> list[dict[str, str]]:
    """Load and validate references from a JSON knowledge base."""
    path = Path(file_path)

    with path.open(encoding="utf-8") as file:
        entries = json.load(file)

    if not isinstance(entries, list):
        raise ValueError("Knowledge base must contain a list of entries.")

    validated_entries = []
    seen_ids = set()

    for entry in entries:
        reference = validate_reference(entry)
        reference_id = reference["id"]

        if reference_id in seen_ids:
            raise ValueError(f"Duplicate knowledge reference ID: {reference_id}")

        seen_ids.add(reference_id)
        validated_entries.append(reference)

    return validated_entries
