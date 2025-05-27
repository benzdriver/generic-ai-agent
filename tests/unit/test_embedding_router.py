from unittest.mock import patch, MagicMock
import importlib


def test_get_embedding(monkeypatch):
    fake_embedding = [0.1, 0.2, 0.3]
    fake_resp = MagicMock()
    fake_resp.data = [MagicMock(embedding=fake_embedding)]
    dummy_config = {
        'openai': {'api_key': 'x', 'model': 'm', 'embedding_model': 'e'},
        'anthropic': {'api_key': 'x', 'model': 'a'},
        'qdrant': {'url': 'u', 'api_key': 'k', 'is_cloud': False,
                   'collection': 'c', 'merged_collection': 'm'},
        'telegram': {'token': 't'},
        'knowledge': {'ttl_days': 1, 'tag_rule_dir': 'tags'},
        'logging': {'level': 'INFO', 'dir': 'logs'},
        'domains': {'config_dir': 'domains', 'default_domain': 'immigration_consultant'}
    }
    with patch('vector_engine.embedding_router.init_config', return_value=dummy_config), \
         patch('openai.embeddings.create', return_value=fake_resp):
        import vector_engine.embedding_router as embedding_router
        importlib.reload(embedding_router)
        result = embedding_router.get_embedding('hello')
    assert result == fake_embedding
