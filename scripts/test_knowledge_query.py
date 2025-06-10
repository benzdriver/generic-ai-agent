#!/usr/bin/env python3
"""
测试知识库查询
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.vector_store.factory import VectorStoreFactory
from src.infrastructure.vector_store.embedding_router import get_embedding

def test_query(collection_name: str, query: str, limit: int = 3):
    """测试查询并显示结果"""
    print(f"\n{'='*60}")
    print(f"查询: {query}")
    print(f"集合: {collection_name}")
    print(f"{'='*60}\n")
    
    # 初始化向量存储
    vector_store = VectorStoreFactory.get_vector_store()
    
    # 生成查询向量
    query_vector = get_embedding(query)
    
    # 搜索
    results = vector_store.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )
    
    # 显示结果
    for i, result in enumerate(results, 1):
        print(f"结果 {i}:")
        print(f"  相关性分数: {result.score:.3f}")
        print(f"  URL: {result.payload.get('url', 'N/A')}")
        print(f"  标题: {result.payload.get('title', 'N/A')}")
        print(f"  内容预览: {result.payload['content'][:200]}...")
        print(f"  AI摘要: {result.payload.get('ai_summary', 'N/A')}")
        print()

def main():
    # 测试几个关键查询
    queries = [
        "What is the Start-up Visa program and how to apply?",
        "Express Entry requirements and process",
        "Provincial Nominee Program eligibility"
    ]
    
    # 测试test_crawl集合
    print("\n测试 test_crawl_docs 集合:")
    test_query("test_crawl_docs", "What is the Start-up Visa program?", limit=2)

if __name__ == "__main__":
    main() 