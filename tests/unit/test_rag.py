"""Unit tests for RAG knowledge retrieval."""

import pytest

from pawgress.rag import (
    build_rag_context,
    extract_keywords,
    format_context,
    retrieve_context,
)


def test_retrieve_matching_context():
    """A relevant query should return the matching entry."""
    results = retrieve_context("tucked tail")

    assert any(entry["id"] == "entry_1" for entry in results)


def test_retrieve_no_matching_context():
    """An unrelated query should return an empty list."""
    results = retrieve_context("airplane maintenance")

    assert results == []


def test_extract_keywords():
    """Check that punctuation and common words are removed."""
    keywords = extract_keywords("My dog has a tucked tail!")

    assert keywords == {"dog", "tucked", "tail"}


def test_retrieve_ranked_context():
    """Check that entries are ranked by matching keywords."""
    results = retrieve_context("play bow and stiff body posture")

    assert results[0]["id"] == "entry_3"
    assert results[1]["id"] == "entry_2"


def test_retrieve_empty_query():
    """Check that an empty query returns no results."""
    results = retrieve_context("")

    assert results == []


def test_format_matching_context():
    """Check that retrieved entries are formatted for AI generation."""
    results = retrieve_context("tucked tail")
    context = format_context(results)

    assert "[entry_1]" in context
    assert "A tucked tail can be a sign of fear or discomfort." in context


def test_format_empty_context():
    """Check that no matches produce an empty context string."""
    context = format_context([])

    assert context == ""


def test_build_rag_context_with_match():
    """Check that matching knowledge is ready for AI generation."""
    context = build_rag_context("tucked tail")

    assert "[entry_1]" in context
    assert "A tucked tail can be a sign of fear or discomfort." in context


def test_build_rag_context_no_match():
    """Check that unrelated input produces an empty context."""
    context = build_rag_context("airplane engine maintenance")

    assert context == ""


def test_retrieve_top_k():
    """Check that only the highest-ranked entry is returned."""
    results = retrieve_context("play bow and stiff body posture", top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == "entry_3"


def test_retrieve_min_score():
    """Check that entries below the minimum score are excluded."""
    results = retrieve_context("play bow and stiff body posture", min_score=3)

    assert len(results) == 1
    assert results[0]["id"] == "entry_3"


def test_retrieve_top_k_zero():
    """Check that requesting zero results returns an empty list."""
    results = retrieve_context("tucked tail", top_k=0)

    assert results == []


def test_retrieve_invalid_top_k():
    """Check that a negative result limit is rejected."""
    with pytest.raises(ValueError, match="top_k"):
        retrieve_context("tucked tail", top_k=-1)


def test_retrieve_invalid_min_score():
    """Check that an invalid minimum score is rejected."""
    with pytest.raises(ValueError, match="min_score"):
        retrieve_context("tucked tail", min_score=0)
