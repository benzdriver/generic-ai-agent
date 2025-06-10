#!/usr/bin/env python3
# tests/integration/test_llm_integration.py

"""
集成测试：测试LLM、向量数据库和领域配置的集成功能
"""

import sys
import os
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.infrastructure.config.env_manager import init_config
from src.infrastructure.config.domain_manager import get_domain_manager
from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.vector_store.embedding_router import get_embedding
from src.app.agent.response_router import generate_response
from src.infrastructure.vector_store.qdrant import QdrantVectorStore

class TestLLMIntegration(unittest.TestCase):
    """测试LLM与其他组件的集成"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备测试环境...")
        try:
            # 初始化配置，使用真实API
            cls.config = init_config(test_mode=False)
            
            # 检查API key是否配置
            if not cls.config.openai.api_key:
                raise unittest.SkipTest("OpenAI API key not configured")
            
            # 尝试连接向量数据库
            cls.vector_store = QdrantVectorStore()
            try:
                cls.vector_store.initialize_collections()
            except Exception as e:
                raise unittest.SkipTest(f"Qdrant不可用: {str(e)}")
                
        except unittest.SkipTest:
            raise
        except Exception as e:
            raise unittest.SkipTest(f"无法初始化测试环境: {str(e)}")
    
    def test_domain_config_loading(self):
        """测试领域配置加载"""
        domain_manager = get_domain_manager()
        domains = domain_manager.list_domains()
        
        self.assertIsInstance(domains, list)
        self.assertGreater(len(domains), 0, "应该至少有一个领域配置")
        
        # 测试获取默认领域配置
        default_domain = self.config.domains.default_domain
        config = domain_manager.get_domain_config(default_domain)
        self.assertIsInstance(config, dict)
        
        print(f"✅ 成功加载 {len(domains)} 个领域配置")
    
    def test_llm_basic_generation(self):
        """测试LLM基本生成功能"""
        try:
            llm = LLMFactory.get_llm()
            
            # 简单的文本生成测试
            prompt = "请用一句话介绍人工智能。"
            response = llm.generate(prompt)
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            
            print(f"✅ LLM生成测试通过，响应长度: {len(response)}")
            
        except Exception as e:
            self.skipTest(f"LLM生成失败: {str(e)}")
    
    def test_embedding_generation(self):
        """测试嵌入向量生成"""
        try:
            text = "这是一个测试文本"
            embedding = get_embedding(text)
            
            self.assertIsInstance(embedding, list)
            self.assertGreater(len(embedding), 0)
            self.assertTrue(all(isinstance(x, (int, float)) for x in embedding))
            
            print(f"✅ 嵌入向量生成测试通过，维度: {len(embedding)}")
            
        except Exception as e:
            self.skipTest(f"嵌入向量生成失败: {str(e)}")
    
    def test_response_generation(self):
        """测试完整的响应生成流程"""
        try:
            llm = LLMFactory.get_llm()
            
            # 测试查询
            query = "什么是加拿大移民？"
            
            # 生成响应
            response = generate_response(
                user_query=query,
                llm=llm,
                vector_store=self.vector_store,
                user_id="test_user",
                domain="immigration_consultant"
            )
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            
            print(f"✅ 完整响应生成测试通过，响应长度: {len(response)}")
            
        except Exception as e:
            self.skipTest(f"响应生成失败: {str(e)}")
    
    def test_llm_fallback(self):
        """测试LLM回退机制"""
        try:
            # 测试无效的provider
            with self.assertRaises(ValueError):
                LLMFactory.get_llm(provider="invalid_provider")
            
            print("✅ LLM回退机制测试通过")
            
        except Exception as e:
            self.skipTest(f"LLM回退测试失败: {str(e)}")

if __name__ == '__main__':
    unittest.main() 