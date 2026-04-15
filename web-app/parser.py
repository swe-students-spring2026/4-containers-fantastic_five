"""Parse raw LLM agent output into structured analysis fields.

Uses position-based extraction to handle formatting variations robustly.
"""

from __future__ import annotations

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
    int_accumulator = ""
    i = index_score + len(key_score)
    while i < index_strength:
        c = result[i]
        if c in "0123456789":
            int_accumulator += c
        i += 1
    if len(int_accumulator) > 0:
        value_score = int(int_accumulator)

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
