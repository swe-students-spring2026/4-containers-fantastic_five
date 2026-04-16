"""Parse raw LLM agent output into structured analysis fields.

Uses position-based extraction to handle formatting variations robustly.
"""

from __future__ import annotations

import re
from typing import TypedDict


class AgentOutput(TypedDict):
    """Structured output from parsed agent response."""

    applicant_score: int | None
    strength: list[str]
    missing_elements: list[str]
    suggested_edits: list[str]
    ai_insights: str


def parse_agent_output(result: str) -> AgentOutput:
    """
    Parse CMAgent raw text output into structured fields.

    Uses position-based extraction (robust to formatting variations).
    Looks for section markers and extracts text between them.

    Expected format:
    1) Applicant Score (0-100): <score>
    2) Essay Strengths (<bullet list>)
    3) Missing elements (<bullet list>)
    4) Suggested Edits (<bullet list>)
    5) AI Insights (<paragraph>)

    Returns:
        AgentOutput with parsed fields, or defaults if parsing fails
    """
    result = result.strip()

    key_score = "Applicant Score"
    key_strength = "Essay Strengths"
    key_missing = "Missing elements"
    key_edits = "Suggested Edits"
    key_insights = "AI Insights"

    result_lower = result.lower()
    index_score = result_lower.find(key_score.lower())
    index_strength = result_lower.find(key_strength.lower())
    index_missing = result_lower.find(key_missing.lower())
    index_edits = result_lower.find(key_edits.lower())
    index_insights = result_lower.find(key_insights.lower())

    if (
        index_score == -1
        or index_strength == -1
        or index_missing == -1
        or index_edits == -1
        or index_insights == -1
    ):
        return {
            "applicant_score": None,
            "strength": [],
            "missing_elements": [],
            "suggested_edits": [],
            "ai_insights": "",
        }

    value_score = None
    score_section = result[index_score:index_strength]

    # Prefer explicit score formats near the heading, e.g.:
    # "Applicant Score (0-100): 72" or "Applicant Score: 88/100"
    heading_score_match = re.search(
        r"(?i)applicant\s*score(?:\s*\([^)]*\))?\s*[:\-]?\s*([0-9]{1,3})(?:\s*/\s*100)?",
        score_section,
    )

    if heading_score_match:
        value_score = int(heading_score_match.group(1))
    else:
        # Fallback: first plausible standalone integer in the score section.
        for number_str in re.findall(r"\b\d{1,3}\b", score_section):
            candidate = int(number_str)
            value_score = candidate
            break

    if value_score is not None:
        value_score = max(0, min(100, value_score))

    i = index_strength + len(key_strength)
    value_strength = ""
    while i < index_missing:
        value_strength += result[i]
        i += 1

    i = index_missing + len(key_missing)
    value_missing = ""
    while i < index_edits:
        value_missing += result[i]
        i += 1

    i = index_edits + len(key_edits)
    value_edits = ""
    while i < index_insights:
        value_edits += result[i]
        i += 1

    i = index_insights + len(key_insights)
    value_insights = ""
    while i < len(result):
        value_insights += result[i]
        i += 1

    def cleanup(s: str) -> list[str]:
        """Clean bullet list: remove markers, strip whitespace, split lines."""
        lines = s.split("\n")
        cleaned = []

        if len(lines) > 0 and lines[0].replace("*", "").strip() == "":
            lines = lines[1:]

        for line in lines:
            line = line.strip()
            if line.startswith("-"):
                line = line[1:]
            line = line.strip()
            if line:
                cleaned.append(line)

        return cleaned

    strength_list = cleanup(value_strength)
    missing_list = cleanup(value_missing)
    edits_list = cleanup(value_edits)

    insights_list = cleanup(value_insights)
    insights_str = " ".join(insights_list).strip()

    return {
        "applicant_score": value_score,
        "strength": strength_list,
        "missing_elements": missing_list,
        "suggested_edits": edits_list,
        "ai_insights": insights_str,
    }
