#!/usr/bin/env python3
# tests/integration/test_vector_db.py

"""
向量数据库集成测试：测试Qdrant集合创建和文档索引
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
from src.vector_engine.qdrant_client import (
    get_client, 
    init_collections, 
    get_collection_info,
    DOCUMENT_COLLECTION,
    CANONICAL_COLLECTION
)
from src.vector_engine.embedding_router import get_embedding
from qdrant_client import models

class TestVectorDB(unittest.TestCase):
    """测试向量数据库功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备向量数据库测试环境...")
        # 初始化配置，使用真实API
        cls.config = init_config(test_mode=False)
        # 获取客户端
        try:
            cls.client = get_client()
            # 测试连接
            cls.client.http.health_check()
            cls.qdrant_available = True
        except Exception as e:
            print(f"⚠️ Qdrant连接失败: {str(e)}")
            print("⚠️ 将跳过需要Qdrant连接的测试")
            cls.qdrant_available = False
            cls.client = None
        
        # 测试集合名称（用于临时测试）
        cls.test_collection = f"test_collection_{uuid.uuid4().hex[:8]}"
        
        # 如果Qdrant可用，确保向量数据库集合存在
        if cls.qdrant_available:
            try:
                init_collections()
            except Exception as e:
                print(f"⚠️ 初始化集合失败: {str(e)}")
                cls.qdrant_available = False
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 删除测试集合
        try:
            if cls.client.collection_exists(cls.test_collection):
                cls.client.delete_collection(cls.test_collection)
                print(f"\n已删除测试集合: {cls.test_collection}")
        except Exception as e:
            print(f"清理测试集合时出错: {str(e)}")
    
    def test_collection_exists(self):
        """测试集合是否存在"""
        if not self.qdrant_available:
            self.skipTest("Qdrant不可用，跳过测试")
            
        collections = [DOCUMENT_COLLECTION, CANONICAL_COLLECTION]
        for collection in collections:
            exists = self.client.collection_exists(collection)
            print(f"\n集合存在性测试: {collection} {'存在' if exists else '不存在'}")
            self.assertTrue(exists, f"集合 {collection} 应该存在")
    
    def test_create_and_query_collection(self):
        """测试创建集合和查询"""
        if not self.qdrant_available:
            self.skipTest("Qdrant不可用，跳过测试")
            
        # 创建测试集合
        self.client.create_collection(
            collection_name=self.test_collection,
            vectors_config=models.VectorParams(
                size=1536,  # OpenAI嵌入维度
                distance=models.Distance.COSINE
            )
        )
        
        # 确认集合已创建
        exists = self.client.collection_exists(self.test_collection)
        self.assertTrue(exists, f"测试集合 {self.test_collection} 应该存在")
        
        # 添加测试文档
        test_docs = [
            {"text": "加拿大是北美洲的一个国家", "category": "地理"},
            {"text": "多伦多是加拿大最大的城市", "category": "城市"},
            {"text": "温哥华位于加拿大西海岸", "category": "城市"}
        ]
        
        # 获取嵌入并插入
        points = []
        for i, doc in enumerate(test_docs):
            embedding = get_embedding(doc["text"])
            points.append(models.PointStruct(
                id=i,
                vector=embedding,
                payload=doc
            ))
        
        # 批量插入
        self.client.upsert(
            collection_name=self.test_collection,
            points=points
        )
        
        # 查询测试
        query_text = "加拿大的城市"
        query_vector = get_embedding(query_text)
        results = self.client.search(
            collection_name=self.test_collection,
            query_vector=query_vector,
            limit=2
        )
        
        print(f"\n向量查询测试:\n查询: '{query_text}'\n结果数量: {len(results)}")
        for hit in results:
            print(f"匹配文本: '{hit.payload['text']}', 相似度: {hit.score:.4f}")
        
        self.assertGreaterEqual(len(results), 1, "查询应该返回至少一个结果")
        
        # 过滤查询测试
        filter_results = self.client.search(
            collection_name=self.test_collection,
            query_vector=query_vector,
            limit=2,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value="城市")
                    )
                ]
            )
        )
        
        print(f"\n过滤查询测试:\n查询: '{query_text}' (仅城市类别)\n结果数量: {len(filter_results)}")
        for hit in filter_results:
            print(f"匹配文本: '{hit.payload['text']}', 类别: {hit.payload['category']}, 相似度: {hit.score:.4f}")
        
        self.assertGreaterEqual(len(filter_results), 1, "过滤查询应该返回至少一个结果")
        for hit in filter_results:
            self.assertEqual(hit.payload["category"], "城市", "过滤结果应该只包含城市类别")

if __name__ == "__main__":
    unittest.main() 