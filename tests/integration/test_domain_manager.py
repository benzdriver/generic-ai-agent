#!/usr/bin/env python3
# tests/integration/test_domain_manager.py

"""
领域管理器集成测试：测试领域配置加载和使用
"""

import sys
import os
import unittest
import uuid
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.config.env_manager import init_config
from src.config.domain_manager import domain_manager
from src.agent_core.prompt_builder import build_prompt, register_domain_prompt

class TestDomainManager(unittest.TestCase):
    """测试领域管理器功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备领域管理器测试环境...")
        # 初始化配置，使用真实API
        cls.config = init_config(test_mode=False)
        # 测试领域名称（用于临时测试）
        cls.test_domain = f"test_domain_{uuid.uuid4().hex[:8]}"
    
    def test_list_domains(self):
        """测试列出所有领域"""
        domains = domain_manager.list_domains()
        print(f"\n可用领域列表: {domains}")
        self.assertIsNotNone(domains)
        self.assertGreaterEqual(len(domains), 1, "应该至少有一个领域")
    
    def test_get_domain_config(self):
        """测试获取领域配置"""
        domains = domain_manager.list_domains()
        if domains:
            domain = domains[0]
            config = domain_manager.get_domain_config(domain)
            print(f"\n领域 '{domain}' 配置:")
            for key, value in config.items():
                if key != "prompt_template":  # 提示词模板可能很长，不打印
                    print(f"  {key}: {value}")
            
            self.assertIsNotNone(config)
            self.assertIn("name", config, "配置应该包含name字段")
            self.assertIn("prompt_template", config, "配置应该包含prompt_template字段")
    
    def test_register_domain(self):
        """测试注册新领域"""
        # 创建测试领域配置
        test_config = {
            "name": self.test_domain,
            "description": "测试领域配置",
            "llm": {
                "preferred_provider": "openai",
                "model_params": {
                    "temperature": 0.5,
                    "top_p": 0.9
                }
            },
            "prompt_template": """
你是一个测试助手，请回答以下问题：

【相关资料】
{context}

【用户提问】
{query}

请简洁地回答。
""",
            "vector_collection": f"{self.test_domain}_docs",
            "tags": ["测试", "集成测试"]
        }
        
        # 注册领域（不保存到文件）
        domain_manager.register_domain(self.test_domain, test_config, save=False)
        
        # 验证领域是否已注册
        domains = domain_manager.list_domains()
        self.assertIn(self.test_domain, domains, f"测试领域 {self.test_domain} 应该在领域列表中")
        
        # 获取并验证领域配置
        config = domain_manager.get_domain_config(self.test_domain)
        self.assertEqual(config["name"], self.test_domain)
        self.assertEqual(config["description"], "测试领域配置")
        
        print(f"\n成功注册测试领域: {self.test_domain}")
    
    def test_domain_prompt_template(self):
        """测试领域提示词模板"""
        # 确保测试领域已注册
        if self.test_domain not in domain_manager.list_domains():
            self.test_register_domain()
        
        # 获取提示词模板
        template = domain_manager.get_domain_prompt_template(self.test_domain)
        self.assertIsNotNone(template)
        self.assertIn("{context}", template)
        self.assertIn("{query}", template)
        
        # 构建提示词
        query = "这是一个测试问题"
        context = ["这是测试上下文1", "这是测试上下文2"]
        prompt = build_prompt(query, context, domain=self.test_domain)
        
        print(f"\n使用领域 '{self.test_domain}' 构建的提示词:\n{prompt[:200]}...")
        
        self.assertIn(query, prompt)
        self.assertIn("测试上下文1", prompt)
        self.assertIn("测试上下文2", prompt)
    
    def test_register_domain_prompt(self):
        """测试通过prompt_builder注册领域提示词"""
        # 创建新的提示词模板
        new_template = """
你是一个通过prompt_builder注册的测试助手，请回答以下问题：

【测试资料】
{context}

【测试问题】
{query}

请简洁地回答测试问题。
"""
        # 注册提示词模板
        register_domain_prompt(self.test_domain, new_template)
        
        # 验证提示词模板是否已更新
        template = domain_manager.get_domain_prompt_template(self.test_domain)
        self.assertEqual(template, new_template)
        
        print(f"\n成功通过prompt_builder更新领域 '{self.test_domain}' 的提示词模板")

if __name__ == "__main__":
    unittest.main() 