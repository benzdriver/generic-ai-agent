import importlib


def test_build_prompt(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'x')
    monkeypatch.setenv('TELEGRAM_TOKEN', 'x')
    import src.agent_core.prompt_builder as prompt_builder
    importlib.reload(prompt_builder)
    prompt = prompt_builder.build_prompt(
        '什么是移民?',
        ['段落1', '段落2'],
        domain='immigration_consultant'
    )
    assert '段落1' in prompt and '什么是移民?' in prompt
