import os
from config import env_manager

def test_init_config(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai')
    monkeypatch.setenv('TELEGRAM_TOKEN', 'token')
    config = env_manager.init_config(test_mode=True)
    assert config['openai']['api_key'] == 'test-openai'
    assert 'telegram' in config
