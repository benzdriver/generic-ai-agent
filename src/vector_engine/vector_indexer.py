# src/vector_engine/vector_indexer.py

"""
向量索引器：负责向量数据的存储和索引
"""

import os
import uuid
import requests
from vector_engine.embedding_router import get_embedding
from qdrant_client import QdrantClient
from config.env_manager import init_config

# 初始化配置
config = init_config()
qdrant_config = config['qdrant']

def get_client() -> QdrantClient:
    """获取Qdrant客户端"""
    if qdrant_config['is_cloud']:
        return QdrantClient(
            url=qdrant_config['url'],
            api_key=qdrant_config['api_key']
        )
    return QdrantClient(url=qdrant_config['url'])

def upsert_documents(paragraphs: list, metadata: dict = None):
    """上传文档到向量数据库"""
    client = get_client()
    points = []
    
    for paragraph in paragraphs:
        embedding = get_embedding(paragraph)
        point_id = str(uuid.uuid4())
        payload = {
            "text": paragraph,
        }
        if metadata:
            payload.update(metadata)

        points.append({
            "id": point_id,
            "vector": embedding,
            "payload": payload
        })

    client.upsert(
        collection_name=qdrant_config['collection'],
        points=points
    )
