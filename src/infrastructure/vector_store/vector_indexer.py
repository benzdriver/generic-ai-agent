# src/infrastructure/vector_store/vector_indexer.py

"""
向量索引器：负责文档的向量化和索引
"""

import uuid
from typing import List, Dict, Any
from .embedding_router import get_embedding
from .qdrant import QdrantVectorStore
from ..config.env_manager import get_config

def index_documents(
    documents: List[Dict[str, Any]], 
    collection_name: str,
    batch_size: int = 100
) -> None:
    """批量索引文档到向量存储
    
    Args:
        documents: 文档列表，每个文档应包含 'content' 字段
        collection_name: 目标集合名称
        batch_size: 批处理大小
    """
    
    vector_store = QdrantVectorStore()
    
    # 确保集合存在
    if not vector_store.collection_exists(collection_name):
        vector_store.initialize_collections()
    
    # 批量处理文档
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        points = []
        
        for doc in batch:
            doc_id = doc.get('id', str(uuid.uuid4()))
            content = doc.get('content', '')
            
            if not content:
                continue
                
            # 生成向量嵌入
            vector = get_embedding(content)
            
            # 创建点结构
            point = {
                "id": doc_id,
                "vector": vector,
                "payload": doc
            }
            points.append(point)
        
        # 批量插入
        if points:
            vector_store.upsert(collection_name=collection_name, points=points)
            print(f"✅ 已索引 {len(points)} 个文档到集合 {collection_name}")

def upsert_documents(
    documents: List[Dict[str, Any]], 
    collection_name: str = None
) -> None:
    """插入或更新文档
    
    Args:
        documents: 文档列表
        collection_name: 目标集合名称，如果为None则使用默认集合
    """
    if collection_name is None:
        config = get_config()
        collection_name = QdrantVectorStore.DOCUMENT_COLLECTION
    
    index_documents(documents, collection_name)

def delete_documents(document_ids: List[str], collection_name: str) -> None:
    """删除指定的文档
    
    Args:
        document_ids: 要删除的文档ID列表
        collection_name: 集合名称
    """
    from qdrant_client import models
    
    vector_store = QdrantVectorStore()
    
    # 构建删除条件
    points_selector = models.PointIdsList(points=document_ids)
    
    # 执行删除
    vector_store.delete(collection_name=collection_name, points_selector=points_selector)
    print(f"✅ 已从集合 {collection_name} 删除 {len(document_ids)} 个文档")
