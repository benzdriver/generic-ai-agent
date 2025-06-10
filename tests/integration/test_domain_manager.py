#!/usr/bin/env python3
# tests/integration/test_domain_manager.py

"""
领域管理器集成测试：测试领域配置和提示构建器
"""

import sys
import os
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.infrastructure.config.domain_manager import get_domain_manager
from src.infrastructure.config.env_manager import init_config
from src.app.agent.prompt_builder import build_prompt, register_domain_prompt

class TestDomainManager(unittest.TestCase):
    """测试领域管理器功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备领域管理器测试环境...")
        try:
            # 初始化配置，使用真实API
            cls.config = init_config(test_mode=False)
            cls.domain_manager = get_domain_manager()
        except Exception as e:
            cls.skipTest(f"无法初始化配置: {str(e)}")
    
    def test_get_domain_config(self):
        """测试获取领域配置"""
        # 测试获取已存在的领域配置
        config = self.domain_manager.get_domain_config("immigration_consultant")
        self.assertIsInstance(config, dict)
        
        # 测试获取不存在的领域配置
        config = self.domain_manager.get_domain_config("nonexistent")
        self.assertEqual(config, {})
    
    def test_list_domains(self):
        """测试列出所有领域"""
        domains = self.domain_manager.list_domains()
        self.assertIsInstance(domains, list)
        self.assertGreater(len(domains), 0)
    
    def test_register_domain(self):
        """测试注册新领域"""
        test_domain = "test_domain"
        test_config = {
            "name": test_domain,
            "description": "测试领域",
            "prompt_template": "测试提示词模板 {context} {query}",
            "vector_collection": "test_docs",
            "tags": ["测试"]
        }
        
        # 注册领域（不保存到文件）
        self.domain_manager.register_domain(test_domain, test_config, save=False)
        
        # 验证注册成功
        retrieved_config = self.domain_manager.get_domain_config(test_domain)
        self.assertEqual(retrieved_config["name"], test_domain)
        self.assertEqual(retrieved_config["description"], "测试领域")
    
    def test_domain_prompt_template(self):
        """测试领域提示词模板"""
        # 测试获取已存在领域的提示词模板
        template = self.domain_manager.get_domain_prompt_template("immigration_consultant")
        if template:
            self.assertIsInstance(template, str)
            self.assertIn("{context}", template)
            self.assertIn("{query}", template)
    
    def test_register_domain_prompt(self):
        """测试注册领域提示词"""
        test_domain = "test_prompt_domain"
        test_template = "测试提示词：{context} 问题：{query}"
        
        # 注册提示词
        register_domain_prompt(test_domain, test_template)
        
        # 验证注册成功
        retrieved_template = self.domain_manager.get_domain_prompt_template(test_domain)
        self.assertEqual(retrieved_template, test_template)

if __name__ == '__main__':
    unittest.main() 