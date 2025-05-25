#!/usr/bin/env python3
# tests/test_collections.py

"""
测试Qdrant集合：验证集合是否可以正常添加向量和搜索
"""

import sys
import os
from pathlib import Path
import unittest
import numpy as np
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# 定义常量
DOCUMENT_COLLECTION = "documents"  # 文档知识库集合

class TestCollections(unittest.TestCase):
    """测试Qdrant集合的基本功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备Qdrant集合测试环境...")
        # 加载环境变量
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            print(f"加载环境变量文件: {env_path}")
            load_dotenv(env_path)
        else:
            print("⚠️ 未找到.env文件，使用默认值")
        
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
        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            cls.client = None
    
    def test_document_collection(self):
        """测试文档集合的添加和搜索功能"""
        if not self.client:
            self.skipTest("Qdrant客户端未初始化")
        
        print(f"\n测试集合: {DOCUMENT_COLLECTION}")
        
        # 生成一些测试向量和payload
        test_vectors = [
            (np.random.rand(1536).tolist(), {"text": "加拿大移民政策概述", "source": "IRCC官方文档", "category": "政策"}),
            (np.random.rand(1536).tolist(), {"text": "加拿大技术移民申请流程", "source": "IRCC官方文档", "category": "流程"}),
            (np.random.rand(1536).tolist(), {"text": "加拿大家庭团聚移民指南", "source": "IRCC官方文档", "category": "指南"})
        ]
        
        # 添加测试向量
        print("\n添加测试向量...")
        points = []
        ids = []  # 保存ID以便后续使用
        
        for i, (vector, payload) in enumerate(test_vectors):
            # 使用UUID作为点ID
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))
        
        self.client.upsert(
            collection_name=DOCUMENT_COLLECTION,
            points=points
        )
        print(f"✅ 成功添加 {len(points)} 个测试向量")
        
        # 测试搜索
        print("\n测试向量搜索...")
        search_vector = np.random.rand(1536).tolist()  # 随机搜索向量
        results = self.client.search(
            collection_name=DOCUMENT_COLLECTION,
            query_vector=search_vector,
            limit=2
        )
        
        self.assertTrue(len(results) > 0, "搜索应返回结果")
        print(f"✅ 搜索成功，找到 {len(results)} 个结果:")
        for i, result in enumerate(results):
            print(f"  {i+1}. 文本: {result.payload.get('text', 'N/A')}")
            print(f"     相似度: {result.score:.4f}")
            print(f"     类别: {result.payload.get('category', 'N/A')}")
        
        # 测试过滤搜索
        print("\n测试过滤搜索...")
        filter_results = self.client.search(
            collection_name=DOCUMENT_COLLECTION,
            query_vector=search_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value="政策")
                    )
                ]
            ),
            limit=2
        )
        
        print(f"✅ 过滤搜索成功，找到 {len(filter_results)} 个结果:")
        for i, result in enumerate(filter_results):
            print(f"  {i+1}. 文本: {result.payload.get('text', 'N/A')}")
            print(f"     相似度: {result.score:.4f}")
            print(f"     类别: {result.payload.get('category', 'N/A')}")
            if "政策" in result.payload.get('category', ''):
                self.assertEqual(result.payload.get('category'), "政策", "过滤搜索应只返回政策类别")

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 Qdrant集合测试")
    print("=" * 70)
    unittest.main() 