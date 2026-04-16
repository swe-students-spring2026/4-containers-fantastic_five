"""Tests for the CMAgent class."""

# pylint: disable=too-few-public-methods

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from CMagent import CMAgent  # pylint: disable=wrong-import-position,import-error


class _FakeAnswer:
    """Simple container for fake model output."""

    def __init__(self, content):
        """Store fake content."""
        self.content = content


class _FakeChain:
    """Stub async chain that returns a deterministic answer."""

    async def ainvoke(self, _payload):
        """Return a fake answer object."""
        return _FakeAnswer("Test analysis result")


class _FakePromptTemplate:
    """Stub prompt template that pipes into the fake chain."""

    def __or__(self, _other):
        """Return the fake chain when piped."""
        return _FakeChain()


@pytest.mark.asyncio
@patch.object(CMAgent, "get_llm", return_value=object())
@patch("CMagent.ChatPromptTemplate")
async def test_cmagent_run_sets_result(mock_prompt_template, _mock_get_llm):
    """CMAgent.run should write the generated result onto the inputs object."""
    mock_prompt_template.from_messages.return_value = _FakePromptTemplate()

    inputs = SimpleNamespace(
        intended_university="NYU",
        user_essay="Essay text",
        user_interview_response="Interview text",
        essay_file_name="essay.pdf",
        notes="Some notes",
        sat_score=1450,
        gpa=4.0,
        essay_pdf_bytes=b"123",
        result=None,
    )

    agent = CMAgent(prompt="Analyze this", inputs=inputs)
    output = await agent.run(inputs)

    assert output.result == "Test analysis result"


@pytest.mark.asyncio
@patch.object(CMAgent, "get_llm", return_value=object())
@patch("CMagent.ChatPromptTemplate")
async def test_cmagent_call_invokes_run(mock_prompt_template, _mock_get_llm):
    """Calling the agent directly should delegate to run()."""
    mock_prompt_template.from_messages.return_value = _FakePromptTemplate()

    inputs = SimpleNamespace(
        intended_university="NYU",
        user_essay="Essay text",
        user_interview_response="Interview text",
        essay_file_name="essay.pdf",
        notes="Some notes",
        sat_score=1450,
        gpa=4.0,
        essay_pdf_bytes=b"123",
        result=None,
    )

    agent = CMAgent(prompt="Analyze this", inputs=inputs)
    output = await agent(inputs)

    assert output.result == "Test analysis result"

