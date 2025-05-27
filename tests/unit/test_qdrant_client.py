from unittest.mock import patch
import importlib


def test_init_collections():
    dummy_config = {
        'qdrant': {
            'url': 'http://test',
            'api_key': 'key',
            'collection': 'c',
            'merged_collection': 'm',
            'is_cloud': False
        },
        'openai': {'api_key': 'x', 'model': 'm', 'embedding_model': 'e'},
        'anthropic': {'api_key': 'x', 'model': 'a'},
        'telegram': {'token': 't'},
        'knowledge': {'ttl_days': 1, 'tag_rule_dir': 'tags'},
        'logging': {'level': 'INFO', 'dir': 'logs'},
        'domains': {'config_dir': 'domains', 'default_domain': 'immigration_consultant'}
    }
    with patch('vector_engine.qdrant_client.init_config', return_value=dummy_config):
        import vector_engine.qdrant_client as qc
        importlib.reload(qc)
        created = []
        class DummyClient:
            def collection_exists(self, n):
                return False
            def create_collection(self, collection_name, vectors_config, metadata=None):
                created.append(collection_name)
        with patch('vector_engine.qdrant_client.QdrantClient', return_value=DummyClient()):
            qc.init_collections(vector_size=3)
        assert set(created) == {qc.CANONICAL_COLLECTION, qc.CONVERSATION_COLLECTION, qc.DOCUMENT_COLLECTION, qc.MERGED_COLLECTION}
