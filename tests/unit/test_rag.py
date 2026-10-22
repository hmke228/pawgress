"""Unit tests for RAG knowledge retrieval."""

from pawgress.rag import retrieve_context


def test_retrieve_matching_context():
    """A relevant query should return the matching entry."""
    results = retrieve_context("tucked tail")

    assert any(entry["id"] == "entry_1" for entry in results)


def test_retrieve_no_matching_context():
    """An unrelated query should return an empty list."""
    results = retrieve_context("airplane maintenance")

    assert results == []
