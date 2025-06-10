# src/infrastructure/llm/openai_client.py

from typing import Any, Dict
import openai
from .base import BaseLLM
from ..config.env_manager import get_config

class OpenAILLM(BaseLLM):
    """OpenAI LLM client."""

    def __init__(self):
        self.config = get_config().openai
        openai.api_key = self.config.api_key
        self.model = self.config.model

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the OpenAI LLM."""
        response = openai.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.choices[0].message.content.strip() 