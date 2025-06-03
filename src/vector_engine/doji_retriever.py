"""
Doji Memory检索器：负责相似向量的检索，支持垂直领域定制
基于doji_memory系统，提供与Qdrant检索器相同的接口
"""

import sys
import os
sys.path.append('/home/ubuntu/repos/doji_memory')

from typing import List, Dict, Any, Optional
from src.vector_engine.embedding_router import get_embedding
from src.vector_engine.doji_memory_client import DOCUMENT_COLLECTION, COLLECTION_TO_PROJECT
from vector.retriever_factory import get_similar_memories

DOMAIN_COLLECTIONS = {
    "immigration": "immigration_docs",
    "legal": "legal_docs", 
    "medical": "medical_docs",
    "education": "education_docs",
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
    collection_name = DOMAIN_COLLECTIONS.get(domain, DOCUMENT_COLLECTION)
    
    project = COLLECTION_TO_PROJECT.get(collection_name, "documents")
    
    try:
        memories = get_similar_memories(
            query=query,
            project=project,
            limit=limit
        )
        
        results = []
        for memory in memories:
            payload = {
                "content": memory.get("content", ""),
                "project": memory.get("project", ""),
                "repo": memory.get("repo", ""),
                "agent": memory.get("agent", ""),
                "tags": memory.get("tags", []),
                "source": memory.get("source", ""),
                "timestamp": memory.get("timestamp", "")
            }
            
            if filter_tags:
                memory_tags = memory.get("tags", [])
                if not any(tag in memory_tags for tag in filter_tags):
                    continue
            
            results.append(payload)
        
        return results[:limit]  # 确保不超过限制
        
    except Exception as e:
        print(f"❌ Doji Memory检索失败: {str(e)}")
        return []

def register_domain_collection(domain: str, collection_name: str) -> None:
    """注册新的领域集合映射
    
    Args:
        domain: 领域名称
        collection_name: 集合名称（将映射到doji_memory项目）
    """
    DOMAIN_COLLECTIONS[domain] = collection_name
    print(f"✅ 已注册领域集合映射: {domain} -> {collection_name}")
    
    if collection_name not in COLLECTION_TO_PROJECT:
        project_name = collection_name.replace("_", "-")
        COLLECTION_TO_PROJECT[collection_name] = project_name
        print(f"✅ 已添加新项目映射: {collection_name} -> {project_name}")
