"""Unit tests for canine knowledge base loading and validation."""

import json

import pytest

from pawgress.knowledge_base import load_knowledge_base, validate_reference


def test_validate_reference():
    """A complete reference should pass validation."""
    entry = {
        "id": "ref_001",
        "topic": "Canine body language",
        "text": "Example knowledge entry for testing.",
        "source_title": "Example Source",
        "source_url": "https://example.com/reference",
    }

    assert validate_reference(entry) == entry


def test_validate_reference_missing_source():
    """A reference without source attribution should be rejected."""
    entry = {
        "id": "ref_001",
        "topic": "Canine body language",
        "text": "Example knowledge entry for testing.",
        "source_title": "",
        "source_url": "",
    }

    with pytest.raises(ValueError):
        validate_reference(entry)


def test_load_knowledge_base(tmp_path):
    """A valid JSON knowledge base should load successfully."""
    entries = [
        {
            "id": "ref_001",
            "topic": "Canine body language",
            "text": "Example knowledge entry for testing.",
            "source_title": "Example Source",
            "source_url": "https://example.com/reference",
        }
    ]

    file_path = tmp_path / "references.json"
    file_path.write_text(json.dumps(entries), encoding="utf-8")

    assert load_knowledge_base(file_path) == entries


def test_validate_reference_not_dictionary():
    """Reject knowledge entries that are not dictionaries."""
    with pytest.raises(ValueError, match="dictionary"):
        validate_reference("This is not a dictionary")


def test_load_knowledge_base_invalid_structure(tmp_path):
    """Reject a JSON knowledge base that is not a list."""
    file_path = tmp_path / "references.json"
    file_path.write_text(
        json.dumps({"id": "ref_001"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="list of entries"):
        load_knowledge_base(file_path)


def test_load_knowledge_base_duplicate_ids(tmp_path):
    """Reject knowledge base entries with duplicate reference IDs."""
    entry = {
        "id": "ref_001",
        "topic": "Canine body language",
        "text": "Example knowledge entry for testing.",
        "source_title": "Example Source",
        "source_url": "https://example.com/reference",
    }

    entries = [
        entry,
        {**entry, "text": "Another entry with the same ID."},
    ]

    file_path = tmp_path / "references.json"
    file_path.write_text(json.dumps(entries), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate knowledge reference ID"):
        load_knowledge_base(file_path)


@pytest.mark.parametrize(
    "source_url",
    [
        "not a URL",
        "example.com/reference",
        "ftp://example.com/reference",
        "https://",
        "",
    ],
)
def test_validate_reference_invalid_url(source_url):
    """Reject references with invalid source URLs."""
    entry = {
        "id": "ref_001",
        "topic": "Canine body language",
        "text": "Example knowledge entry for testing.",
        "source_title": "Example Source",
        "source_url": source_url,
    }

    with pytest.raises(ValueError):
        validate_reference(entry)
