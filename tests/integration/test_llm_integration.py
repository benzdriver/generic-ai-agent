#!/usr/bin/env python3
# tests/integration/test_llm_integration.py

"""
集成测试：测试LLM、向量数据库和领域配置的集成功能
"""

import sys
import os
import unittest
from pathlib import Path
import pytest

# set required environment variables for configuration
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("TELEGRAM_TOKEN", "test")
os.environ.setdefault("QDRANT_API_KEY", "test")
os.environ.setdefault("QDRANT_IS_CLOUD", "false")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
for p in (project_root, src_path):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

pytest.importorskip("langchain_community", reason="langchain_community not installed")

from src.config.env_manager import init_config
from src.config.domain_manager import domain_manager
from src.llm.factory import LLMFactory
from src.vector_engine.embedding_router import get_embedding
from src.agent_core.response_router import generate_response
from src.vector_engine.qdrant_client import init_collections, get_client
class TestLLMIntegration(unittest.TestCase):
    """测试LLM与其他组件的集成"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备测试环境...")
        # 初始化配置，使用真实API
        cls.config = init_config(test_mode=False)
        # 确保向量数据库集合存在
        init_collections()
        # 获取LLM实例
        cls.llm = LLMFactory.get_llm()
    
    def test_llm_basic_generation(self):
        """测试LLM基本生成功能"""
        prompt = "请用一句话回答：加拿大有多少个省？"
        response = self.llm.generate(prompt)
        print(f"\nLLM基本生成测试:\n问题: {prompt}\n回答: {response}")
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 10)  # 确保回答不是太短
    
    def test_embedding_generation(self):
        """测试嵌入向量生成"""
        text = "这是一个测试文本，用于生成嵌入向量"
        embedding = get_embedding(text)
        print(f"\n嵌入向量生成测试:\n文本长度: {len(text)}\n向量维度: {len(embedding)}")
        self.assertIsNotNone(embedding)
        self.assertGreater(len(embedding), 100)  # 确保向量维度合理
    
    def test_domain_config_loading(self):
        """测试领域配置加载"""
        domains = domain_manager.list_domains()
        print(f"\n领域配置加载测试:\n可用领域: {domains}")
        self.assertIsNotNone(domains)
        self.assertGreater(len(domains), 0)  # 确保至少有一个领域
        
        # 测试获取领域配置
        for domain in domains:
            config = domain_manager.get_domain_config(domain)
            self.assertIsNotNone(config)
            print(f"领域 '{domain}' 配置: {config.get('description', '无描述')}")
    
    def test_response_generation(self):
        """测试完整的回答生成流程"""
        # 测试默认领域
        query = "在加拿大，Express Entry最低分数线是多少？"
        response = generate_response(query)
        print(f"\n默认领域回答生成测试:\n问题: {query}\n回答: {response}")
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 20)  # 确保回答不是太短
        
        # 测试指定领域
        domains = domain_manager.list_domains()
        if domains:
            specific_domain = domains[0]
            query = "BC省PNP项目的申请条件是什么？"
            response = generate_response(query, domain=specific_domain)
            print(f"\n指定领域({specific_domain})回答生成测试:\n问题: {query}\n回答: {response}")
            self.assertIsNotNone(response)
            self.assertGreater(len(response), 20)  # 确保回答不是太短
    
    def test_llm_fallback(self):
        """测试LLM回退机制"""
        try:
            # 尝试使用一个不存在的提供商，应该会回退到可用的提供商
            fallback_llm = LLMFactory.get_llm("nonexistent_provider", fallback_providers=["openai"])
            response = fallback_llm.generate("这是一个测试")
            print(f"\nLLM回退机制测试:\n回答: {response}")
            self.assertIsNotNone(response)
        except Exception as e:
            self.fail(f"LLM回退机制测试失败: {str(e)}")

if __name__ == "__main__":
    unittest.main() 