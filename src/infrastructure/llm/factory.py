# src/infrastructure/llm/factory.py

from .base import BaseLLM
from .openai_client import OpenAILLM
from ..config.env_manager import Config


class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def get_llm(config: Config, provider: str = "openai") -> BaseLLM:
        """Get an LLM client based on the provider."""
        if provider == "openai":
            if not config.openai.api_key:
                raise ValueError("OpenAI API key is not configured.")
            return OpenAILLM(config.openai)
        # Add other providers here in the future
        # elif provider == "anthropic":
        #     return AnthropicLLM(config.anthropic)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
