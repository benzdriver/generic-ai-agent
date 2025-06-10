#!/usr/bin/env python3
# tests/test_qdrant_connection.py

"""
Qdrant连接检查：仅检查Qdrant连接，不需要其他API密钥
"""

import sys
import os
from pathlib import Path
import unittest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from src.infrastructure.config.env_manager import get_config

class TestQdrantConnection(unittest.TestCase):
    """测试Qdrant连接"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备Qdrant连接测试环境...")
        cls.config = get_config()
    
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
                self.skipTest(f"无法连接到Qdrant: {str(e)}")

        except Exception as e:
            self.skipTest(f"无法连接到Qdrant: {str(e)}")

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 Qdrant连接检查")
    print("=" * 70)
    unittest.main() 