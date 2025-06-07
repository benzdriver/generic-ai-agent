# src/vector_engine/retriever.py

"""
检索器：负责相似向量的检索，支持垂直领域定制
支持 Qdrant 和 Doji Memory 后端切换
"""

from typing import List, Dict, Any, Optional
from .hybrid_vector_router import get_hybrid_router, VectorBackend
from .qdrant_client import DOCUMENT_COLLECTION

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
    router = get_hybrid_router()
    
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
    
    # 根据后端类型执行不同的检索逻辑
    if router.backend == VectorBackend.QDRANT:
        # Qdrant 需要向量
        query_vector = router.get_embedding(query)
        results = router.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_condition
        )
    else:
        # Doji Memory 可以直接用文本搜索
        results = router.search(
            collection_name=collection_name,
            query_text=query,
            limit=limit,
            query_filter=filter_condition
        )
    
    return [result["payload"] for result in results]

def register_domain_collection(domain: str, collection_name: str) -> None:
    """注册新的领域集合映射
    
    Args:
        domain: 领域名称
        collection_name: Qdrant集合名称
    """
    DOMAIN_COLLECTIONS[domain] = collection_name
    print(f"✅ 已注册领域集合映射: {domain} -> {collection_name}")

