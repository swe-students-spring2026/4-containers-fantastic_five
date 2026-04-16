"""Tests for the CMAgent class."""

import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

fake_llmsetup = types.ModuleType("llmSetUp")


class FakeGetLLM:
    """Stub LLM provider used to avoid real API setup in tests."""

    def __init__(self, provider="openai", prompt=None):
        self.provider = provider
        self.prompt = prompt

    def get_llm(self):
        """Return a dummy object in place of a real LLM."""
        return object()


fake_llmsetup.GetLLM = FakeGetLLM
sys.modules["llmSetUp"] = fake_llmsetup

from CMagent import CMAgent


class FakeAnswer:
    """Simple container for fake model output."""

    def __init__(self, content):
        self.content = content


class FakeChain:
    """Stub async chain that returns a deterministic answer."""

    async def ainvoke(self, _payload):
        """Return a fake answer object."""
        return FakeAnswer("Test analysis result")


class FakePromptTemplate:
    """Stub prompt template that pipes into the fake chain."""

    def __or__(self, _other):
        """Return the fake chain when piped."""
        return FakeChain()


@pytest.mark.asyncio
@patch("CMagent.ChatPromptTemplate")
async def test_cmagent_run_sets_result(mock_prompt_template):
    """CMAgent.run should write the generated result onto the inputs object."""
    mock_prompt_template.from_messages.return_value = FakePromptTemplate()

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
@patch("CMagent.ChatPromptTemplate")
async def test_cmagent_call_invokes_run(mock_prompt_template):
    """Calling the agent directly should delegate to run()."""
    mock_prompt_template.from_messages.return_value = FakePromptTemplate()

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
