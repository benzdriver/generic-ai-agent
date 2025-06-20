#!/usr/bin/env python3
# scripts/initialize_collections.py

"""
初始化Qdrant集合：创建项目所需的所有向量集合
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http import models
import datetime
import uuid

# 定义集合名称
CANONICAL_COLLECTION = "canonical_queries"  # 规范化查询集合
CONVERSATION_COLLECTION = "conversations"   # 对话历史集合
DOCUMENT_COLLECTION = "documents"          # 文档知识库集合
MERGED_COLLECTION = "merged_knowledge"     # 合并知识点集合
CRAWLED_DOCUMENTS_COLLECTION = "crawled_documents"  # 爬虫抓取的文档集合
PAGE_SUMMARIES_COLLECTION = "page_summaries"  # 页面摘要集合

def store_collection_metadata(client, collection_name, description):
    """使用特殊向量点存储集合元数据
    
    使用Qdrant的payload系统存储元数据，创建一个特殊的向量点
    """
    try:
        # 创建一个有效的UUID作为点ID
        metadata_id = str(uuid.uuid4())
        metadata_payload = {
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "is_metadata": True,
            "collection_info": True  # 标记这是集合信息
        }
        
        # 创建一个全0的向量（作为元数据占位符）
        zero_vector = [0.0] * 1536
        
        # 插入元数据点
        client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(
                id=metadata_id,
                vector=zero_vector,
                payload=metadata_payload
            )]
        )
        print(f"  ✓ 已存储集合元数据（使用payload）")
        return True
    except Exception as e:
        print(f"  ⚠️ 存储元数据失败: {str(e)}")
        return False

def main():
    """初始化所有必需的集合"""
    print("=" * 70)
    print("🔍 初始化Qdrant集合")
    print("=" * 70)
    
    # 加载环境变量
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        print(f"加载环境变量文件: {env_path}")
        load_dotenv(env_path)
    else:
        print("⚠️ 未找到.env文件，使用默认值")
    
    # 从环境变量获取URL和API密钥
    url = os.environ.get('QDRANT_URL')
    api_key = os.environ.get('QDRANT_API_KEY')
    
    if not api_key:
        print("⚠️ 未设置QDRANT_API_KEY环境变量，请确保已设置正确的API密钥")
        return
    
    try:
        # 创建客户端
        client = QdrantClient(url=url, api_key=api_key)
        print(f"✅ 成功连接到Qdrant: {url}")
        
        # 初始化所有集合
        collections = [
            (CANONICAL_COLLECTION, "规范化查询集合，存储用户查询的标准形式"),
            (CONVERSATION_COLLECTION, "对话历史集合，存储用户对话记录"),
            (DOCUMENT_COLLECTION, "文档知识库集合，存储官方文档内容"),
            (MERGED_COLLECTION, "合并知识点集合，存储去重后的知识"),
            (CRAWLED_DOCUMENTS_COLLECTION, "爬虫服务抓取的网页文档"),
            (PAGE_SUMMARIES_COLLECTION, "AI生成的网页摘要")
        ]
        
        print("\n开始创建集合...")
        for name, description in collections:
            if not client.collection_exists(name):
                print(f"创建集合: {name}...")
                # 创建集合（不使用metadata参数）
                client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI嵌入维度
                        distance=models.Distance.COSINE
                    )
                )
                print(f"✅ 成功创建集合: {name}")
                
                # 然后使用payload系统存储元数据
                print(f"  正在存储集合元数据...")
                store_collection_metadata(client, name, description)
            else:
                print(f"ℹ️ 集合已存在: {name}")
        
        # 列出所有集合
        collections = client.get_collections()
        print(f"\n当前所有集合 ({len(collections.collections)}):")
        for collection in collections.collections:
            print(f"  - {collection.name}")
            
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
    
    print("\n初始化完成")

if __name__ == "__main__":
    main() 