#!/usr/bin/env python3
"""
Doji Memory 集成测试脚本

测试 Generic AI Agent 与 Doji Memory 的集成功能
"""

import os
import sys
import uuid
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_doji_memory_basic():
    """测试 Doji Memory 基本功能"""
    print("🧪 开始测试 Doji Memory 基本功能...")
    
    try:
        from vector_engine.doji_memory_client import DojiMemoryClient
        
        # 初始化客户端
        print("1. 初始化 Doji Memory 客户端...")
        client = DojiMemoryClient()
        
        # 测试向量化
        print("2. 测试文本向量化...")
        test_text = "这是一个测试文本，用于验证向量化功能。"
        vector = client.get_embedding(test_text)
        print(f"   向量维度: {len(vector)}")
        print(f"   向量前5个元素: {vector[:5]}")
        
        # 测试批量向量化
        print("3. 测试批量向量化...")
        test_texts = [
            "加拿大移民政策",
            "工作签证申请",
            "永久居民身份"
        ]
        vectors = client.get_batch_embeddings(test_texts)
        print(f"   批量处理了 {len(vectors)} 个文本")
        
        # 测试存储内存
        print("4. 测试存储内存...")
        memory_uuid = client.store_memory(
            content="这是一个测试记忆：加拿大技术移民需要通过快速入境系统申请。",
            project="generic-ai-agent",
            repo="test",
            agent="test-agent",
            tags=["immigration", "canada", "test"]
        )
        print(f"   存储成功，UUID: {memory_uuid}")
        
        # 测试搜索
        print("5. 测试内存搜索...")
        search_results = client.search_memory(
            query="加拿大移民申请",
            project="generic-ai-agent",
            limit=3
        )
        print(f"   搜索到 {len(search_results)} 条结果")
        for i, result in enumerate(search_results):
            print(f"   结果 {i+1}: 相似度 {result.get('score', 0):.3f}")
        
        print("✅ Doji Memory 基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ Doji Memory 基本功能测试失败: {str(e)}")
        return False

def test_hybrid_router():
    """测试混合路由器功能"""
    print("\n🧪 开始测试混合路由器功能...")
    
    try:
        from vector_engine.hybrid_vector_router import (
            get_hybrid_router, 
            switch_backend, 
            VectorBackend
        )
        
        # 设置环境变量使用 Doji Memory
        os.environ['VECTOR_BACKEND'] = 'doji_memory'
        
        print("1. 初始化混合路由器...")
        router = get_hybrid_router()
        print(f"   当前后端: {router.backend.value}")
        
        # 测试健康检查
        print("2. 测试健康检查...")
        health = router.health_check()
        print(f"   健康状态: {health}")
        
        # 测试向量化
        print("3. 测试路由器向量化...")
        test_text = "测试路由器的向量化功能"
        vector = router.get_embedding(test_text)
        print(f"   向量维度: {len(vector)}")
        
        # 测试批量向量化
        print("4. 测试批量向量化...")
        test_texts = ["文本1", "文本2", "文本3"]
        vectors = router.get_batch_embeddings(test_texts)
        print(f"   批量处理了 {len(vectors)} 个文本")
        
        # 测试数据存储
        print("5. 测试数据存储...")
        test_points = [
            {
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "text": test_text,
                    "agent": "test-router",
                    "tags": ["test", "router"],
                    "created_at": datetime.now().timestamp()
                }
            }
        ]
        
        router.upsert_points("test_collection", test_points)
        
        # 测试搜索
        print("6. 测试搜索功能...")
        search_results = router.search(
            collection_name="test_collection",
            query_text="测试路由器",
            limit=3
        )
        print(f"   搜索到 {len(search_results)} 条结果")
        
        print("✅ 混合路由器功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 混合路由器功能测试失败: {str(e)}")
        return False

def test_retriever_integration():
    """测试检索器集成"""
    print("\n🧪 开始测试检索器集成...")
    
    try:
        from vector_engine.retriever import retrieve_relevant_chunks
        
        # 设置使用 Doji Memory
        os.environ['VECTOR_BACKEND'] = 'doji_memory'
        
        print("1. 测试检索器查询...")
        # 首先存储一些测试数据
        from vector_engine.hybrid_vector_router import get_hybrid_router
        router = get_hybrid_router()
        
        # 存储测试文档
        test_docs = [
            {
                "id": str(uuid.uuid4()),
                "vector": router.get_embedding("加拿大技术移民申请流程"),
                "payload": {
                    "text": "加拿大技术移民通过快速入境系统申请，需要通过语言测试和学历认证。",
                    "tags": ["immigration", "canada", "skilled-worker"],
                    "created_at": datetime.now().timestamp()
                }
            },
            {
                "id": str(uuid.uuid4()),
                "vector": router.get_embedding("工作签证申请要求"),
                "payload": {
                    "text": "申请加拿大工作签证需要有加拿大雇主的工作邀请函。",
                    "tags": ["work-permit", "canada"],
                    "created_at": datetime.now().timestamp()
                }
            }
        ]
        
        router.upsert_points("documents", test_docs)
        print("   测试文档存储完成")
        
        # 测试检索
        print("2. 测试相关性检索...")
        results = retrieve_relevant_chunks(
            query="如何申请加拿大移民",
            limit=2,
            domain="default"
        )
        
        print(f"   检索到 {len(results)} 条相关文档")
        for i, result in enumerate(results):
            print(f"   文档 {i+1}: {result.get('text', '')[:50]}...")
        
        print("✅ 检索器集成测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 检索器集成测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 Doji Memory 集成测试")
    print("=" * 60)
    
    # 设置环境变量（如果没有设置的话）
    if not os.getenv('DOJI_MEMORY_URL'):
        print("⚠️ 未设置 DOJI_MEMORY_URL，将使用默认值: http://localhost:8000")
        os.environ['DOJI_MEMORY_URL'] = 'http://localhost:8000'
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ 未设置 OPENAI_API_KEY，请先设置后再运行测试")
        return False
    
    # 运行测试
    tests = [
        test_doji_memory_basic,
        test_hybrid_router,
        test_retriever_integration
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 测试完成: {passed}/{len(tests)} 个测试通过")
    
    if passed == len(tests):
        print("🎉 所有测试都通过了！Generic AI Agent 已成功集成 Doji Memory")
    else:
        print("⚠️ 部分测试失败，请检查配置和服务状态")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 