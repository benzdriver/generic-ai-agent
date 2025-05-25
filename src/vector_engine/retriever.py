# src/vector_engine/retriever.py

"""
检索器：负责相似向量的检索，支持垂直领域定制
"""

from typing import List, Dict, Any, Optional
from vector_engine.embedding_router import get_embedding
from vector_engine.qdrant_client import get_client, DOCUMENT_COLLECTION

# 领域特定的集合映射
DOMAIN_COLLECTIONS = {
    "immigration": "immigration_docs",
    "legal": "legal_docs",
    "medical": "medical_docs",
    "education": "education_docs",
    # 默认使用通用文档集合
    "default": DOCUMENT_COLLECTION
}

def retrieve_relevant_chunks(query: str, limit: int = 5, domain: str = "default", filter_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """检索相关文本块
    
    Args:
        query: 用户查询
        limit: 返回结果数量限制
        domain: 垂直领域名称，用于选择合适的集合
        filter_tags: 可选的标签过滤条件
        
    Returns:
        List[Dict[str, Any]]: 检索到的相关文本块列表
    """
    client = get_client()
    query_vector = get_embedding(query)
    
    # 获取领域特定的集合名称
    collection_name = DOMAIN_COLLECTIONS.get(domain, DOCUMENT_COLLECTION)
    
    # 构建过滤条件
    filter_condition = None
    if filter_tags:
        filter_condition = {
            "must": [
                {
                    "key": "tags",
                    "match": {
                        "any": filter_tags
                    }
                }
            ]
        }
    
    # 执行检索
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        query_filter=filter_condition
    )
    
    return [hit.payload for hit in results]

def register_domain_collection(domain: str, collection_name: str) -> None:
    """注册新的领域集合映射
    
    Args:
        domain: 领域名称
        collection_name: Qdrant集合名称
    """
    DOMAIN_COLLECTIONS[domain] = collection_name
    print(f"✅ 已注册领域集合映射: {domain} -> {collection_name}")

