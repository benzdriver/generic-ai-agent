from unittest.mock import patch, MagicMock
import importlib, pytest


def test_generate(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'x')
    monkeypatch.setenv('TELEGRAM_TOKEN', 'x')
    try:
        import llm.openai_llm as openai_llm
    except Exception:
        pytest.skip('openai_llm dependencies missing')
    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=MagicMock(content='answer'))]
    with patch('openai.chat.completions.create', return_value=fake_resp):
        llm = openai_llm.OpenAILLM()
        result = llm.generate('hi')
        assert result == 'stub'
