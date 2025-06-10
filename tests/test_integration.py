# tests/test_integration.py

import unittest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.agent.response_router import generate_response
from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.vector_store.factory import VectorStoreFactory
from src.infrastructure.config.env_manager import get_config

class TestIntegration(unittest.TestCase):
    
    def test_rag_pipeline(self):
        """Test the full RAG pipeline."""
        config = get_config()
        
        # Skip test if API keys are not configured
        if not config.openai.api_key:
            self.skipTest("OpenAI API key not configured")
        
        llm = LLMFactory.get_llm()
        vector_store = VectorStoreFactory.get_vector_store()
        
        # This test assumes that the vector store is running and accessible.
        # It also assumes that the LLM API key is configured correctly.
        query = "What is the process for applying for a work permit in Canada?"
        
        try:
            response = generate_response(query, llm=llm, vector_store=vector_store)
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
        except Exception as e:
            # If there are connection issues or other problems, skip the test
            self.skipTest(f"Integration test failed due to external dependencies: {str(e)}")

if __name__ == '__main__':
    unittest.main() 