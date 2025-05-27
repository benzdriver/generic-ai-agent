import importlib
from config import env_manager


def test_list_domains(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'x')
    monkeypatch.setenv('TELEGRAM_TOKEN', 'x')
    import config.domain_manager as dm
    importlib.reload(dm)
    env_manager.init_config(test_mode=True)
    domains = dm.domain_manager.list_domains()
    assert 'immigration_consultant' in domains
