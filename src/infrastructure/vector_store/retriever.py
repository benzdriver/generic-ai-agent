# src/infrastructure/vector_store/retriever.py

"""
内容检索器：负责向量相似度检索和知识片段召回
"""

from typing import Dict, Any, List, Optional
from .embedding_router import get_embedding
from .qdrant import QdrantVectorStore

def retrieve_documents(
    query: str, 
    collection_name: str, 
    top_k: int = 5,
    score_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """检索相关文档"""
    
    vector_store = QdrantVectorStore()
    
    # 获取查询向量
    query_vector = get_embedding(query)
    
    # 执行相似度搜索
    results = vector_store.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold
    )
    
    return [
        {
            "content": hit.payload.get("content", ""),
            "score": hit.score,
            "metadata": hit.payload
        }
        for hit in results
    ]

def retrieve_with_filters(
    query: str,
    collection_name: str,
    filters: Dict[str, Any],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """带过滤条件的检索"""
    
    vector_store = QdrantVectorStore()
    query_vector = get_embedding(query)
    
    # 构建过滤条件
    from qdrant_client import models
    
    filter_conditions = []
    for key, value in filters.items():
        filter_conditions.append(
            models.FieldCondition(
                key=key,
                match=models.MatchValue(value=value)
            )
        )
    
    query_filter = models.Filter(must=filter_conditions) if filter_conditions else None
    
    results = vector_store.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter
    )
    
    return [
        {
            "content": hit.payload.get("content", ""),
            "score": hit.score,
            "metadata": hit.payload
        }
        for hit in results
    ]

