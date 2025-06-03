"""
Doji Memory客户端管理模块：统一管理Weaviate连接和集合
基于doji_memory系统，提供与Qdrant客户端相同的接口

集合映射说明：
1. CANONICAL_COLLECTION -> project: "canonical"
2. CONVERSATION_COLLECTION -> project: "conversations"  
3. DOCUMENT_COLLECTION -> project: "documents"
4. MERGED_COLLECTION -> project: "merged"
"""

import sys
import os
sys.path.append('/home/ubuntu/repos/doji_memory')

from vector.config import get_weaviate_client
from vector.schema_init import create_project_memory_class
from src.config.env_manager import init_config
from typing import Optional, Dict, Any
import datetime

config = init_config(test_mode=False)

COLLECTION_TO_PROJECT = {
    "canonical_queries": "canonical",
    "conversations": "conversations", 
    "documents": "documents",
    "merged_knowledge": "merged"
}

CANONICAL_COLLECTION = "canonical_queries"
CONVERSATION_COLLECTION = "conversations"
DOCUMENT_COLLECTION = "documents"
MERGED_COLLECTION = "merged_knowledge"

def get_client():
    """获取Weaviate客户端
    
    返回配置好的Weaviate客户端实例，兼容Qdrant客户端接口
    """
    try:
        weaviate_url = config.get('weaviate', {}).get('url', 'http://localhost:8080')
        print(f"连接到Weaviate服务: {weaviate_url}")
        
        client = get_weaviate_client(url=weaviate_url)
        return client
    except Exception as e:
        print(f"❌ 连接Weaviate失败: {str(e)}")
        return get_weaviate_client()

def init_collections(vector_size: int = 1536):
    """初始化所有必需的集合
    
    Args:
        vector_size: 向量维度，默认使用OpenAI embedding模型的1536维
    """
    try:
        client = get_client()
        
        create_project_memory_class(client)
        
        print("✅ Doji Memory集合初始化完成")
        print(f"   - 使用ProjectMemory类存储所有数据")
        print(f"   - 向量维度: {vector_size}")
        print(f"   - 支持的项目: {list(COLLECTION_TO_PROJECT.values())}")
        
    except Exception as e:
        print(f"❌ 初始化Doji Memory集合失败: {str(e)}")
        raise

def get_collection_info(collection_name: Optional[str] = None) -> Dict[str, Any]:
    """获取集合信息
    
    Args:
        collection_name: 集合名称，如果为None则返回所有集合信息
    
    Returns:
        包含集合信息的字典
    """
    client = get_client()
    
    try:
        schema = client.schema.get()
        
        if collection_name:
            project = COLLECTION_TO_PROJECT.get(collection_name)
            if not project:
                return {"error": f"Unknown collection: {collection_name}"}
            
            return {
                "collection_name": collection_name,
                "project": project,
                "schema": "ProjectMemory",
                "vector_size": 1536,
                "status": "active"
            }
        
        collections = {}
        for collection, project in COLLECTION_TO_PROJECT.items():
            collections[collection] = {
                "collection_name": collection,
                "project": project,
                "schema": "ProjectMemory", 
                "vector_size": 1536,
                "status": "active"
            }
        
        return collections
        
    except Exception as e:
        if collection_name:
            return {"error": str(e)}
        
        collections = {}
        for collection in COLLECTION_TO_PROJECT.keys():
            collections[collection] = {"error": str(e)}
        
        return collections
