from unittest.mock import patch, MagicMock
import importlib


def test_retrieve_relevant_chunks(monkeypatch):
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
    with patch('src.vector_engine.qdrant_client.init_config', return_value=dummy_config):
        import src.vector_engine.retriever as retriever
        importlib.reload(retriever)
        hit = MagicMock(); hit.payload = {'text': 'data'}
        with patch('src.vector_engine.retriever.get_client') as mock_client, \
             patch('src.vector_engine.retriever.get_embedding', return_value=[0.1]):
            mock_client.return_value.search.return_value = [hit]
            results = retriever.retrieve_relevant_chunks('q', limit=1)
            assert results == [hit.payload]
