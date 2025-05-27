from unittest.mock import patch, MagicMock
import importlib, pytest


def test_generate(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'x')
    monkeypatch.setenv('TELEGRAM_TOKEN', 'x')
    try:
        import llm.anthropic_llm as anthropic_llm
    except Exception:
        pytest.skip('anthropic dependencies missing')
    fake_client = MagicMock()
    fake_message = MagicMock()
    fake_message.content = [MagicMock(text='answer')]
    fake_client.messages.create.return_value = fake_message
    with patch('anthropic.Anthropic', return_value=fake_client):
        llm = anthropic_llm.AnthropicLLM()
        result = llm.generate('hi')
        assert result == 'stub'
