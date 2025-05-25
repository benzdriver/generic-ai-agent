#!/usr/bin/env python3
# tests/test_all_collections.py

"""
测试所有Qdrant集合：验证所有集合是否可以正常添加向量和搜索
"""

import sys
import os
from pathlib import Path
import unittest
import numpy as np
import uuid
import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 直接导入集合名称常量，避免初始化整个配置
CANONICAL_COLLECTION = "canonical_queries"
CONVERSATION_COLLECTION = "conversations"
DOCUMENT_COLLECTION = "documents"
MERGED_COLLECTION = "merged_knowledge"

class TestAllCollections(unittest.TestCase):
    """测试所有Qdrant集合的功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备Qdrant集合测试环境...")
        
        # 从环境变量获取URL和API密钥
        cls.url = os.environ.get('QDRANT_URL')
        cls.api_key = os.environ.get('QDRANT_API_KEY')
        
        if not cls.url or not cls.api_key:
            print("⚠️ 未设置QDRANT_URL或QDRANT_API_KEY环境变量，请确保已设置正确的API密钥")
            cls.client = None
            return
        
        try:
            # 创建客户端
            cls.client = QdrantClient(url=cls.url, api_key=cls.api_key)
            print(f"✅ 成功连接到Qdrant: {cls.url}")
            
            # 准备测试数据
            cls.now = datetime.datetime.utcnow().isoformat()
            
            # 文档集合测试数据
            cls.document_test_data = [
                (np.random.rand(1536).tolist(), {
                    "text": "加拿大移民政策概述",
                    "source": "IRCC官方文档",
                    "category": "政策",
                    "test_id": "doc_test_1"
                }),
                (np.random.rand(1536).tolist(), {
                    "text": "加拿大技术移民申请流程",
                    "source": "IRCC官方文档",
                    "category": "流程",
                    "test_id": "doc_test_2"
                })
            ]
            
            # 规范化查询集合测试数据
            cls.canonical_test_data = [
                (np.random.rand(1536).tolist(), {
                    "raw": "怎么申请加拿大移民?",
                    "canonical": "加拿大移民申请流程",
                    "created_at": cls.now,
                    "test_id": "canonical_test_1"
                }),
                (np.random.rand(1536).tolist(), {
                    "raw": "学生签证需要什么材料?",
                    "canonical": "加拿大学生签证申请材料清单",
                    "created_at": cls.now,
                    "test_id": "canonical_test_2"
                })
            ]
            
            # 对话历史集合测试数据
            cls.conversation_test_data = [
                (np.random.rand(1536).tolist(), {
                    "user_id": "test_user_1",
                    "question": "加拿大技术移民需要什么条件?",
                    "answer": "加拿大技术移民主要通过Express Entry系统...",
                    "timestamp": cls.now,
                    "test_id": "conv_test_1"
                }),
                (np.random.rand(1536).tolist(), {
                    "user_id": "test_user_2",
                    "question": "我需要多少分才能申请EE?",
                    "answer": "Express Entry评分系统基于多个因素...",
                    "timestamp": cls.now,
                    "test_id": "conv_test_2"
                })
            ]
            
            # 合并知识点集合测试数据
            cls.merged_test_data = [
                (np.random.rand(1536).tolist(), {
                    "text": "加拿大技术移民综合指南",
                    "merged_from": ["id1", "id2", "id3"],
                    "created_at": cls.now,
                    "type": "merged_cluster",
                    "test_id": "merged_test_1"
                }),
                (np.random.rand(1536).tolist(), {
                    "text": "加拿大学生签证申请全流程",
                    "merged_from": ["id4", "id5"],
                    "created_at": cls.now,
                    "type": "merged_cluster",
                    "test_id": "merged_test_2"
                })
            ]
            
        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            cls.client = None
    
    def _test_collection(self, collection_name, test_data):
        """测试特定集合的读写功能"""
        if not self.client:
            self.skipTest("Qdrant客户端未初始化")
        
        print(f"\n{'='*30}")
        print(f"🔍 测试集合: {collection_name}")
        print(f"{'='*30}")
        
        # 检查集合是否存在
        self.assertTrue(self.client.collection_exists(collection_name), 
                       f"集合 {collection_name} 不存在，请先运行 initialize_collections.py")
        
        # 添加测试向量
        print("\n添加测试向量...")
        points = []
        ids = []  # 保存ID以便后续使用
        
        for i, (vector, payload) in enumerate(test_data):
            # 使用UUID作为点ID
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"✅ 成功添加 {len(points)} 个测试向量")
        
        # 测试搜索
        print("\n测试向量搜索...")
        search_vector = np.random.rand(1536).tolist()  # 随机搜索向量
        results = self.client.search(
            collection_name=collection_name,
            query_vector=search_vector,
            limit=2
        )
        
        self.assertTrue(len(results) > 0, "搜索应返回结果")
        print(f"✅ 搜索成功，找到 {len(results)} 个结果:")
        for i, result in enumerate(results):
            print(f"  {i+1}. ID: {result.id}")
            print(f"     相似度: {result.score:.4f}")
            print(f"     Payload: {result.payload}")
        
        return True
    
    def test_document_collection(self):
        """测试文档集合"""
        self._test_collection(DOCUMENT_COLLECTION, self.document_test_data)
    
    def test_canonical_collection(self):
        """测试规范化查询集合"""
        self._test_collection(CANONICAL_COLLECTION, self.canonical_test_data)
    
    def test_conversation_collection(self):
        """测试对话历史集合"""
        self._test_collection(CONVERSATION_COLLECTION, self.conversation_test_data)
    
    def test_merged_collection(self):
        """测试合并知识点集合"""
        self._test_collection(MERGED_COLLECTION, self.merged_test_data)

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 测试所有Qdrant集合")
    print("=" * 70)
    unittest.main() 