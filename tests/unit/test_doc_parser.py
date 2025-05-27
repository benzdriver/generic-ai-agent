import importlib


def test_parse_html_content(monkeypatch):
    from unittest.mock import patch
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
    with patch('knowledge_ingestion.doc_parser.get_embedding', return_value=[0.1]), \
         patch('knowledge_ingestion.doc_parser.get_client'):
        import knowledge_ingestion.doc_parser as doc_parser
        importlib.reload(doc_parser)
        html = '<html><body><p>short</p><p>' + 'a'*50 + '</p></body></html>'
        blocks = doc_parser.parse_html_content(html)
        assert len(blocks) == 1
        assert 'a'*20 in blocks[0]


def test_parse_ircc_text(tmp_path, monkeypatch):
    from unittest.mock import patch
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
    with patch('knowledge_ingestion.doc_parser.get_embedding', return_value=[0.1]), \
         patch('knowledge_ingestion.doc_parser.get_client'):
        import knowledge_ingestion.doc_parser as doc_parser
        importlib.reload(doc_parser)
        text = 'para1\n\n' + 'b'*50 + '\n\nend'
        f = tmp_path / 'f.txt'
        f.write_text(text, encoding='utf-8')
        chunks = doc_parser.parse_ircc_text(str(f))
        assert len(chunks) == 1
        assert 'b'*20 in chunks[0]
