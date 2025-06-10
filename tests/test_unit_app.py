# tests/test_unit_app.py

import unittest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock, patch
from src.app.agent.prompt_builder import build_prompt
from src.app.agent.query_normalizer import transform_query_to_canonical_form
from src.app.agent.response_router import generate_response

class TestPromptBuilder(unittest.TestCase):
    
    def test_build_prompt_with_context(self):
        """Test that the prompt is built correctly with context."""
        query = "What is the capital of France?"
        context = ["France is a country in Europe.", "The capital of France is Paris."]
        prompt = build_prompt(query, context)
        self.assertIn(query, prompt)
        self.assertIn(context[0], prompt)
        self.assertIn(context[1], prompt)

    def test_build_prompt_without_context(self):
        """Test that the prompt is built correctly without context."""
        query = "What is the capital of France?"
        prompt = build_prompt(query, [])
        self.assertIn(query, prompt)
        self.assertNotIn("【相关资料】", prompt)

    def test_build_prompt_with_domain(self):
        """Test that the prompt is built correctly with a specific domain."""
        query = "What is the capital of France?"
        context = ["France is a country in Europe.", "The capital of France is Paris."]
        prompt = build_prompt(query, context, domain="legal")
        self.assertIn("法律", prompt)

class TestQueryNormalizer(unittest.TestCase):
    
    @patch('src.app.agent.query_normalizer.get_embedding')
    def test_transform_query_to_canonical_form_with_similar_query(self, mock_get_embedding):
        """Test that the canonical form is returned when a similar query is found."""
        mock_get_embedding.return_value = [0.1] * 1536  # Mock embedding vector
        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = [MagicMock(score=0.95, payload={"canonical": "canonical form"})]
        mock_llm = MagicMock()
        
        query = "some user query"
        canonical_form = transform_query_to_canonical_form(query, llm=mock_llm, vector_store=mock_vector_store)
        
        self.assertEqual(canonical_form, "canonical form")
        mock_vector_store.search.assert_called_once()
        mock_llm.generate.assert_not_called()

    @patch('src.app.agent.query_normalizer.get_embedding')
    def test_transform_query_to_canonical_form_with_no_similar_query(self, mock_get_embedding):
        """Test that the LLM is used to generate the canonical form when no similar query is found."""
        mock_get_embedding.return_value = [0.1] * 1536  # Mock embedding vector
        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = []
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "llm generated canonical form"
        
        query = "some user query"
        canonical_form = transform_query_to_canonical_form(query, llm=mock_llm, vector_store=mock_vector_store)
        
        self.assertEqual(canonical_form, "llm generated canonical form")
        mock_vector_store.search.assert_called_once()
        mock_llm.generate.assert_called_once()
        mock_vector_store.upsert.assert_called_once()

class TestResponseRouter(unittest.TestCase):
    
    @patch('src.app.agent.response_router.get_conversation_context')
    @patch('src.app.agent.response_router.transform_query_to_canonical_form')
    @patch('src.app.agent.response_router.find_similar_canonical_query')
    @patch('src.app.agent.response_router.retrieve_relevant_documents')
    @patch('src.app.agent.response_router.build_prompt')
    @patch('src.app.agent.response_router.log_qa_to_knowledge_base')
    def test_generate_response(
        self, 
        mock_log_qa, 
        mock_build_prompt, 
        mock_retrieve_docs, 
        mock_find_similar, 
        mock_transform_query, 
        mock_get_context
    ):
        """Test the main logic of the response generation."""
        mock_llm = MagicMock()
        mock_vector_store = MagicMock()
        
        # Scenario 1: Similar query found
        mock_find_similar.return_value = MagicMock(score=0.95, payload={"answer": "cached answer"})
        response = generate_response("query", llm=mock_llm, vector_store=mock_vector_store)
        self.assertEqual(response, "cached answer")
        
        # Reset mocks for scenario 2
        mock_get_context.reset_mock()
        mock_transform_query.reset_mock()
        mock_find_similar.reset_mock()
        mock_retrieve_docs.reset_mock()
        mock_build_prompt.reset_mock()
        mock_llm.reset_mock()
        mock_log_qa.reset_mock()
        
        # Scenario 2: No similar query, normal response generation
        mock_find_similar.return_value = None
        mock_transform_query.return_value = "canonical query"
        mock_retrieve_docs.return_value = [MagicMock(payload={"content": "doc content"})]
        mock_build_prompt.return_value = "prompt"
        mock_llm.generate.return_value = "llm response"
        
        response = generate_response("query", llm=mock_llm, vector_store=mock_vector_store)
        
        self.assertEqual(response, "llm response")
        # Note: get_conversation_context is only called when user_id is provided
        # Since we're not providing user_id, it shouldn't be called
        mock_transform_query.assert_called_with("query", llm=mock_llm, vector_store=mock_vector_store)
        mock_find_similar.assert_called_with("canonical query", mock_vector_store)
        mock_retrieve_docs.assert_called_with("canonical query", mock_vector_store, domain="immigration_consultant")
        mock_build_prompt.assert_called_with("query", ["doc content"], domain="immigration_consultant")
        mock_llm.generate.assert_called_with("prompt", provider='openai', temperature=0.3, top_p=0.9)
        mock_log_qa.assert_called_with("query", "llm response", mock_vector_store, user_id=None, llm=mock_llm)

if __name__ == '__main__':
    unittest.main() 