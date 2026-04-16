import sys
import types
from types import SimpleNamespace
from unittest.mock import patch
import pytest

fake_llmsetup = types.ModuleType("llmSetUp")


class FakeGetLLM:
    def __init__(self, provider="openai", prompt=None):
        self.provider = provider
        self.prompt = prompt

    def get_llm(self):
        return object()


fake_llmsetup.GetLLM = FakeGetLLM
sys.modules["llmSetUp"] = fake_llmsetup

from CMagent import CMAgent


class FakeAnswer:
    def __init__(self, content):
        self.content = content


class FakeChain:
    async def ainvoke(self, payload):
        return FakeAnswer("Test analysis result")


class FakePromptTemplate:
    def __or__(self, other):
        return FakeChain()


@pytest.mark.asyncio
@patch("CMagent.ChatPromptTemplate")
async def test_cmagent_run_sets_result(mock_prompt_template):
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