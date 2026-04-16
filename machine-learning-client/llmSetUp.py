"""Small helper for setting up the LLM client."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# basic LLM setup helper


class GetLLM:
    """Get an LLM instance for the app."""

    def __init__(self, provider="openai", prompt=None):
        self.provider = provider
        self.prompt = prompt

    def get_llm(self):
        """Pick the right llm provider."""
        llm = None
        if self.provider == "openai":
            llm = self.get_openai_instance()
        else:
            print("No llm model found")

        return llm

    # openai path for now
    def get_openai_instance(self):  # I use openai but you can feel free to use others
        """Get an instance of the OpenAI LLM."""
        return ChatOpenAI(
            model="gpt-5.4-mini",
            temperature=0.0,
            api_key=os.getenv(
                "OPENAI_API_KEY"
            ),  # remember to put your apikey in the .env
        )
