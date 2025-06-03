#!/usr/bin/env python3
"""
Comprehensive tests for doji_memory integration
Tests the replacement of Qdrant with doji_memory across all components
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestDojiMemoryClient:
    """Test doji_memory_client adapter functionality"""
    
    def test_import_doji_memory_client(self):
        """Test that doji_memory_client can be imported"""
        try:
            from src.vector_engine.doji_memory_client import get_client, init_collections
            from src.vector_engine.doji_memory_client import CANONICAL_COLLECTION, DOCUMENT_COLLECTION
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import doji_memory_client: {e}")
    
    def test_collection_constants(self):
        """Test that collection constants are properly defined"""
        from src.vector_engine.doji_memory_client import (
            CANONICAL_COLLECTION, CONVERSATION_COLLECTION, 
            DOCUMENT_COLLECTION, MERGED_COLLECTION
        )
        
        assert CANONICAL_COLLECTION == "canonical_queries"
        assert CONVERSATION_COLLECTION == "conversations"
        assert DOCUMENT_COLLECTION == "documents"
        assert MERGED_COLLECTION == "merged_knowledge"
    
    @patch('src.vector_engine.doji_memory_client.get_weaviate_client')
    def test_get_client(self, mock_weaviate_client):
        """Test get_client function returns weaviate client"""
        mock_client = MagicMock()
        mock_weaviate_client.return_value = mock_client
        
        from src.vector_engine.doji_memory_client import get_client
        client = get_client()
        
        assert client == mock_client
        mock_weaviate_client.assert_called_once()

class TestDojiRetriever:
    """Test doji_retriever adapter functionality"""
    
    def test_import_doji_retriever(self):
        """Test that doji_retriever can be imported"""
        try:
            from src.vector_engine.doji_retriever import retrieve_relevant_chunks
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import doji_retriever: {e}")
    
    @patch('src.vector_engine.doji_retriever.get_similar_memories')
    def test_retrieve_relevant_chunks(self, mock_get_memories):
        """Test retrieve_relevant_chunks function"""
        mock_memories = [
            {
                "content": "Test content 1",
                "project": "documents",
                "repo": "main",
                "agent": "test",
                "tags": ["test"],
                "source": "test"
            }
        ]
        mock_get_memories.return_value = mock_memories
        
        from src.vector_engine.doji_retriever import retrieve_relevant_chunks
        
        results = retrieve_relevant_chunks("test query", limit=1)
        
        assert len(results) == 1
        assert results[0]["content"] == "Test content 1"
        mock_get_memories.assert_called_once()

class TestVectorIndexer:
    """Test vector_indexer with doji_memory backend"""
    
    def test_import_vector_indexer(self):
        """Test that vector_indexer can be imported"""
        try:
            from src.vector_engine.vector_indexer import upsert_documents, get_client
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import vector_indexer: {e}")
    
    @patch('src.vector_engine.vector_indexer.write_memories_batch')
    def test_upsert_documents(self, mock_write_batch):
        """Test upsert_documents function with doji_memory backend"""
        mock_write_batch.return_value = ["uuid1", "uuid2"]
        
        from src.vector_engine.vector_indexer import upsert_documents
        
        paragraphs = ["Test paragraph 1", "Test paragraph 2"]
        metadata = {"project": "test", "repo": "main"}
        
        result = upsert_documents(paragraphs, metadata)
        
        assert result == ["uuid1", "uuid2"]
        mock_write_batch.assert_called_once()
        
        call_args = mock_write_batch.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["content"] == "Test paragraph 1"
        assert call_args[0]["project"] == "test"

class TestConfigurationUpdates:
    """Test configuration updates for weaviate support"""
    
    def test_weaviate_config_function(self):
        """Test that weaviate configuration function exists"""
        try:
            from src.config.env_manager import get_weaviate_config
            config = get_weaviate_config()
            
            assert 'url' in config
            assert 'api_key' in config
            assert 'is_cloud' in config
        except ImportError as e:
            pytest.fail(f"Failed to import weaviate config: {e}")
    
    @patch.dict(os.environ, {
        'WEAVIATE_URL': 'http://test:8080',
        'WEAVIATE_API_KEY': 'test-key',
        'WEAVIATE_IS_CLOUD': 'true'
    })
    def test_weaviate_config_values(self):
        """Test weaviate configuration values from environment"""
        from src.config.env_manager import get_weaviate_config
        
        config = get_weaviate_config()
        
        assert config['url'] == 'http://test:8080'
        assert config['api_key'] == 'test-key'
        assert config['is_cloud'] == True

class TestImportUpdates:
    """Test that import statements have been updated correctly"""
    
    def test_no_direct_qdrant_imports(self):
        """Test that key files no longer import qdrant_client directly"""
        import ast
        import inspect
        
        test_files = [
            'src.vector_engine.vector_indexer',
            'src.vector_engine.doji_memory_client',
            'src.vector_engine.doji_retriever'
        ]
        
        for module_name in test_files:
            try:
                module = __import__(module_name, fromlist=[''])
                source = inspect.getsource(module)
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert 'qdrant_client' not in alias.name, f"Found qdrant_client import in {module_name}"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and 'qdrant_client' in node.module:
                            pytest.fail(f"Found qdrant_client import in {module_name}")
                            
            except ImportError:
                pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
