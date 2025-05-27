from unittest.mock import patch
import importlib


def test_auto_tag(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'x')
    monkeypatch.setenv('TELEGRAM_TOKEN', 'x')
    dummy_config = {'knowledge': {'tag_rule_dir': 'tags'}}
    with patch('config.env_manager.init_config', return_value=dummy_config):
        import knowledge_ingestion.tagger as tagger
        importlib.reload(tagger)
    with patch.object(tagger, 'load_keyword_tags', return_value={'label': ['keyword']}):
        tags = tagger.auto_tag('this Keyword text', domain='immigration')
        assert 'label' in tags
