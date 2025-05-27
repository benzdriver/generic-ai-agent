from unittest.mock import patch, MagicMock
import importlib


def test_generate_response():
    dummy_doc = MagicMock(payload={'content': 'info'}, score=0.9)
    dummy_client = MagicMock()
    dummy_client.scroll.return_value = ([MagicMock(payload={}, id='c')], None)
    dummy_client.search.return_value = [dummy_doc]
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
        import agent_core.response_router as rr
        importlib.reload(rr)
    with patch.object(rr, 'get_client', return_value=dummy_client), \
         patch.object(rr, 'get_embedding', return_value=[0.1]), \
         patch.object(rr, 'transform_query_to_canonical_form', return_value='q'), \
         patch.object(rr.LLMFactory, 'get_llm') as mock_llm, \
         patch.object(rr, 'log_qa_to_knowledge_base'):
        mock_llm.return_value.generate.return_value = 'answer'
        resp = rr.generate_response('q', user_id='u')
    assert resp == 'stub'
