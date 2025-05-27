import sys
import types
from src.llm.base import BaseLLM
import importlib


class DummyLLM(BaseLLM):
    def generate(self, prompt: str, **kwargs) -> str:
        return 'ok'
    def generate_with_chunks(self, chunks, **kwargs) -> str:
        return 'chunk'
    def chat(self, messages, **kwargs) -> str:
        return 'chat'


def test_fallback_llm(monkeypatch):
    import llm.factory as factory
    importlib.reload(factory)
    monkeypatch.setitem(factory.LLMFactory._implementations, 'dummy', DummyLLM)
    llm = factory.FallbackLLM(primary_provider='dummy')
    assert llm.generate('hi') == 'ok'
    assert llm.generate_with_chunks(['a']) == 'chunk'
    assert llm.chat([]) == 'chat'
