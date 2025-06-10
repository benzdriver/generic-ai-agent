# src/infrastructure/llm/base.py
from abc import ABC, abstractmethod
from typing import List, Any

class BaseLLM(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM."""
        pass

    def should_use_chunks(self, texts: List[str]) -> bool:
        """Determine if text should be chunked for processing."""
        # Default implementation, can be overridden
        return sum(len(text) for text in texts) > 4000

    def generate_with_chunks(self, texts: List[str], **kwargs: Any) -> str:
        """Generate a response from the LLM with chunked text."""
        # Default implementation, can be overridden
        prompt = kwargs.pop("prompt", "")
        full_text = "\n".join(texts)
        return self.generate(prompt.format(context=full_text), **kwargs) 