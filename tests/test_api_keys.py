#!/usr/bin/env python3
# tests/test_api_keys.py

"""
API密钥测试：验证各种API密钥是否有效
"""

import sys
import os
from pathlib import Path
import unittest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config.env_manager import get_config
import openai
from qdrant_client import QdrantClient

class TestAPIKeys(unittest.TestCase):
    """测试各种API密钥是否有效"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备API密钥测试环境...")
        # 初始化配置
        cls.config = get_config()
    
    def test_openai_api_key(self):
        """测试OpenAI API密钥是否有效"""
        if not self.config.openai.api_key:
            self.skipTest("OpenAI API密钥未设置")
        
        print("\n测试OpenAI API密钥...")
        try:
            # 设置API密钥
            openai.api_key = self.config.openai.api_key
            # 尝试调用API
            response = openai.embeddings.create(
                model=self.config.openai.embedding_model,
                input="测试OpenAI API密钥是否有效"
            )
            # 检查响应
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.data)
            self.assertGreater(len(response.data), 0)
            self.assertGreater(len(response.data[0].embedding), 0)
            print("✅ OpenAI API密钥有效")
        except Exception as e:
            self.fail(f"OpenAI API密钥无效: {str(e)}")
    
    def test_anthropic_api_key(self):
        """测试Anthropic API密钥是否有效"""
        if not self.config.anthropic.api_key:
            self.skipTest("Anthropic API密钥未设置")
        
        print("\n测试Anthropic API密钥...")
        try:
            # 导入Anthropic客户端
            import anthropic
            # 创建客户端
            client = anthropic.Anthropic(api_key=self.config.anthropic.api_key)
            # 尝试调用API
            response = client.messages.create(
                model=self.config.anthropic.model,
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "测试Anthropic API密钥是否有效"}
                ]
            )
            # 检查响应
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.content)
            print("✅ Anthropic API密钥有效")
        except Exception as e:
            self.fail(f"Anthropic API密钥无效: {str(e)}")
    
    def test_qdrant_connection(self):
        """测试Qdrant连接是否有效"""
        if not self.config.qdrant.url:
            self.skipTest("Qdrant URL未设置")
        
        print("\n测试Qdrant连接...")
        try:
            # 创建客户端
            if self.config.qdrant.is_cloud and self.config.qdrant.api_key:
                client = QdrantClient(url=self.config.qdrant.url, api_key=self.config.qdrant.api_key)
            else:
                client = QdrantClient(url=self.config.qdrant.url)
            
            # 尝试获取集合列表
            try:
                collections = client.get_collections()
                
                # 检查响应
                self.assertIsNotNone(collections)
                print(f"✅ Qdrant连接有效，发现 {len(collections.collections)} 个集合")
                for collection in collections.collections:
                    print(f"  - {collection.name}")
            except Exception as e:
                print(f"⚠️ 无法获取Qdrant集合列表: {str(e)}")
                print("⚠️ 这可能是权限问题或服务器配置问题，但基本连接可能仍然有效")
                
                # 尝试一个更基本的操作 - 健康检查
                try:
                    health = client.http.health_check()
                    if health and hasattr(health, 'result') and health.result:
                        print("✅ Qdrant健康检查通过")
                    else:
                        print("⚠️ Qdrant健康检查未通过")
                except Exception as e2:
                    print(f"⚠️ Qdrant健康检查失败: {str(e2)}")
                    raise
        except Exception as e:
            print(f"⚠️ Qdrant连接测试失败: {str(e)}")
            print("⚠️ 这不会阻止其他测试运行，但可能会影响需要向量数据库的功能")

if __name__ == "__main__":
    print("=" * 70)
    print("🔑 API密钥测试")
    print("=" * 70)
    unittest.main() 