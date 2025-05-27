from unittest.mock import patch, MagicMock
import importlib


def test_transform_query_to_canonical_form():
    dummy_hit = MagicMock(score=0.95, payload={'canonical_form': 'canon'})
    dummy_client = MagicMock()
    dummy_client.search.return_value = [dummy_hit]
    dummy_client.upsert.return_value = None
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
    with patch('config.env_manager.init_config', return_value=dummy_config):
        import agent_core.canonical_router as cr
        importlib.reload(cr)
    with patch.object(cr, 'get_client', return_value=dummy_client), \
         patch.object(cr, 'get_embedding', return_value=[0.1]), \
         patch.object(cr.LLMFactory, 'get_llm') as mock_llm:
        mock_llm.return_value.generate.return_value = 'canon'
        result = cr.transform_query_to_canonical_form('q')
    assert result == 'canon'
