#!/usr/bin/env python3
"""
Functional tests for doji_memory integration
Tests end-to-end functionality with mocked doji_memory components
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestEndToEndFunctionality:
    """Test end-to-end functionality with doji_memory"""
    
    @patch('src.vector_engine.doji_memory_client.get_weaviate_client')
    @patch('src.vector_engine.doji_memory_client.create_project_memory_class')
    def test_init_collections(self, mock_create_class, mock_get_client):
        """Test collection initialization"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        from src.vector_engine.doji_memory_client import init_collections
        
        init_collections()
        
        mock_get_client.assert_called_once()
        mock_create_class.assert_called_once_with(mock_client)
    
    @patch('src.vector_engine.vector_indexer.write_memories_batch')
    def test_document_indexing_workflow(self, mock_write_batch):
        """Test complete document indexing workflow"""
        mock_write_batch.return_value = ["uuid1", "uuid2", "uuid3"]
        
        from src.vector_engine.vector_indexer import upsert_documents
        
        documents = [
            "Immigration policy document 1",
            "Immigration policy document 2", 
            "Immigration policy document 3"
        ]
        
        metadata = {
            "collection": "documents",
            "project": "immigration",
            "repo": "policy-docs",
            "tags": ["immigration", "policy"],
            "source": "government"
        }
        
        result = upsert_documents(documents, metadata)
        
        assert len(result) == 3
        mock_write_batch.assert_called_once()
        
        call_args = mock_write_batch.call_args[0][0]
        assert len(call_args) == 3
        
        for i, memory in enumerate(call_args):
            assert memory["content"] == documents[i]
            assert memory["project"] == "immigration"
            assert memory["repo"] == "policy-docs"
            assert memory["tags"] == ["immigration", "policy"]
            assert memory["source"] == "government"
    
    @patch('src.vector_engine.doji_retriever.get_similar_memories')
    def test_document_retrieval_workflow(self, mock_get_memories):
        """Test complete document retrieval workflow"""
        mock_memories = [
            {
                "content": "Immigration document about work permits",
                "project": "immigration",
                "repo": "policy-docs",
                "agent": "indexer",
                "tags": ["work-permit", "immigration"],
                "source": "government"
            },
            {
                "content": "Immigration document about student visas",
                "project": "immigration", 
                "repo": "policy-docs",
                "agent": "indexer",
                "tags": ["student-visa", "immigration"],
                "source": "government"
            }
        ]
        mock_get_memories.return_value = mock_memories
        
        from src.vector_engine.doji_retriever import retrieve_relevant_chunks
        
        results = retrieve_relevant_chunks(
            query="work permit requirements",
            limit=2,
            domain="immigration"
        )
        
        assert len(results) == 2
        assert "work permits" in results[0]["content"]
        assert "student visas" in results[1]["content"]
        
        mock_get_memories.assert_called_once_with(
            query="work permit requirements",
            project="documents",  # Mapped from domain via COLLECTION_TO_PROJECT
            limit=2
        )
    
    def test_collection_mapping(self):
        """Test collection name to project mapping"""
        from src.vector_engine.doji_memory_client import COLLECTION_TO_PROJECT
        
        expected_mappings = {
            "canonical_queries": "canonical",
            "conversations": "conversations",
            "documents": "documents",
            "merged_knowledge": "merged"
        }
        
        for collection, project in expected_mappings.items():
            assert COLLECTION_TO_PROJECT[collection] == project
    
    def test_domain_collection_mapping(self):
        """Test domain to collection mapping in retriever"""
        from src.vector_engine.doji_retriever import DOMAIN_COLLECTIONS
        
        assert "immigration" in DOMAIN_COLLECTIONS
        assert "legal" in DOMAIN_COLLECTIONS
        assert "medical" in DOMAIN_COLLECTIONS
        assert "education" in DOMAIN_COLLECTIONS
        assert "default" in DOMAIN_COLLECTIONS

class TestBackwardCompatibility:
    """Test backward compatibility with existing interfaces"""
    
    def test_vector_indexer_interface_compatibility(self):
        """Test that vector_indexer maintains the same interface"""
        from src.vector_engine.vector_indexer import upsert_documents, get_client
        
        import inspect
        
        upsert_sig = inspect.signature(upsert_documents)
        assert 'paragraphs' in upsert_sig.parameters
        assert 'metadata' in upsert_sig.parameters
        
        assert callable(get_client)
    
    def test_retriever_interface_compatibility(self):
        """Test that retriever maintains the same interface"""
        from src.vector_engine.doji_retriever import retrieve_relevant_chunks, register_domain_collection
        
        import inspect
        
        retrieve_sig = inspect.signature(retrieve_relevant_chunks)
        assert 'query' in retrieve_sig.parameters
        assert 'limit' in retrieve_sig.parameters
        assert 'domain' in retrieve_sig.parameters
        assert 'filter_tags' in retrieve_sig.parameters
        
        assert callable(register_domain_collection)

class TestErrorHandling:
    """Test error handling in doji_memory integration"""
    
    @patch('src.vector_engine.vector_indexer.write_memories_batch')
    def test_indexing_error_handling(self, mock_write_batch):
        """Test error handling in document indexing"""
        mock_write_batch.side_effect = Exception("Weaviate connection error")
        
        from src.vector_engine.vector_indexer import upsert_documents
        
        with pytest.raises(Exception) as exc_info:
            upsert_documents(["test document"], {"project": "test"})
        
        assert "Weaviate connection error" in str(exc_info.value)
    
    @patch('src.vector_engine.doji_retriever.get_similar_memories')
    def test_retrieval_error_handling(self, mock_get_memories):
        """Test error handling in document retrieval"""
        mock_get_memories.side_effect = Exception("Retrieval error")
        
        from src.vector_engine.doji_retriever import retrieve_relevant_chunks
        
        results = retrieve_relevant_chunks("test query")
        assert results == []

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
