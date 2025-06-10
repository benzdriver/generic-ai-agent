# src/infrastructure/llm/factory.py

from .base import BaseLLM
from .openai_client import OpenAILLM
from ..config.env_manager import get_config

class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def get_llm(provider: str = "openai") -> BaseLLM:
        """Get an LLM client based on the provider."""
        if provider == "openai":
            # Check if OpenAI API key is available
            if not get_config().openai.api_key:
                raise ValueError("OpenAI API key is not configured.")
            return OpenAILLM()
        # Add other providers here in the future
        # elif provider == "anthropic":
        #     return AnthropicLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}") 