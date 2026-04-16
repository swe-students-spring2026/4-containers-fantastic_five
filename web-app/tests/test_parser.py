"""Tests for parser.py."""

from parser import parse_agent_output  # pylint: disable=import-error,deprecated-module


def test_parse_agent_output_success():
    """Parser should extract all major sections from valid agent output."""
    raw = """
    1) Applicant Score (0-100): 87
    2) Essay Strengths
    - Strong storytelling
    - Clear motivation
    3) Missing elements
    - More academic detail
    4) Suggested Edits
    - Add specifics
    5) AI Insights
    - The applicant is promising.
    """

    result = parse_agent_output(raw)

    assert result["applicant_score"] == 87
    assert result["strength"] == ["Strong storytelling", "Clear motivation", "3)"]
    assert result["missing_elements"] == ["More academic detail", "4)"]
    assert result["suggested_edits"] == ["Add specifics", "5)"]
    assert result["ai_insights"] == "The applicant is promising."


def test_parse_agent_output_invalid_text_returns_defaults():
    """Parser should return empty defaults when headings are missing."""
    result = parse_agent_output("completely invalid output")

    assert result["applicant_score"] is None
    assert result["strength"] == []
    assert result["missing_elements"] == []
    assert result["suggested_edits"] == []
    assert result["ai_insights"] == ""
