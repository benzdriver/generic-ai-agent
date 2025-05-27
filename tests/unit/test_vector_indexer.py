from unittest.mock import patch
import importlib


def test_upsert_documents():
    dummy_config = {
        'qdrant': {
            'url': 'u', 'api_key': 'k', 'collection': 'c',
            'merged_collection': 'm', 'is_cloud': False
        },
        'openai': {'api_key': 'x', 'model': 'm', 'embedding_model': 'e'},
        'anthropic': {'api_key': 'x', 'model': 'a'},
        'telegram': {'token': 't'},
        'knowledge': {'ttl_days': 1, 'tag_rule_dir': 'tags'},
        'logging': {'level': 'INFO', 'dir': 'logs'},
        'domains': {'config_dir': 'domains', 'default_domain': 'immigration_consultant'}
    }
    with patch('vector_engine.vector_indexer.init_config', return_value=dummy_config):
        import vector_engine.vector_indexer as vi
        importlib.reload(vi)
    called = {}
    class DummyClient:
        def upsert(self, collection_name, points):
            called['collection'] = collection_name
            called['points'] = points
    with patch('vector_engine.vector_indexer.get_client', return_value=DummyClient()), \
         patch('vector_engine.vector_indexer.get_embedding', return_value=[0.1,0.2]):
        vi.upsert_documents(['text'], metadata={'a':1})
    assert called['collection'] == vi.qdrant_config['collection']
    assert len(called['points']) == 1
