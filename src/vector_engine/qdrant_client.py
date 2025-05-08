"""
Qdrant客户端管理模块：统一管理Qdrant连接和集合

集合说明：
1. CANONICAL_COLLECTION: 存储规范化后的用户查询，用于查询复用
2. CONVERSATION_COLLECTION: 存储对话历史，用于上下文管理
3. DOCUMENT_COLLECTION: 存储文档知识库，包含IRCC等官方文档
4. MERGED_COLLECTION: 存储经过合并的知识点，减少冗余
"""

from qdrant_client import QdrantClient, models
from config.env_manager import init_config
from typing import Optional
import datetime

# 初始化配置
config = init_config()
qdrant_config = config['qdrant']

def get_client() -> QdrantClient:
    """获取Qdrant客户端
    
    根据配置返回适当的客户端实例：
    - 如果是云版本，使用API Key认证
    - 如果是本地版本，直接连接URL
    """
    if qdrant_config['is_cloud']:
        return QdrantClient(
            url=qdrant_config['url'],
            api_key=qdrant_config['api_key']
        )
    return QdrantClient(url=qdrant_config['url'])

# 定义集合名称
CANONICAL_COLLECTION = "canonical_queries"  # 规范化查询集合
CONVERSATION_COLLECTION = "conversations"   # 对话历史集合
DOCUMENT_COLLECTION = "documents"          # 文档知识库集合
MERGED_COLLECTION = "merged_knowledge"     # 合并知识点集合

def init_collections(vector_size: int = 1536):
    """初始化所有必需的集合
    
    Args:
        vector_size: 向量维度，默认使用OpenAI ada-002的1536维
    """
    client = get_client()
    
    collections = [
        (CANONICAL_COLLECTION, "规范化查询集合，存储用户查询的标准形式"),
        (CONVERSATION_COLLECTION, "对话历史集合，存储用户对话记录"),
        (DOCUMENT_COLLECTION, "文档知识库集合，存储官方文档内容"),
        (MERGED_COLLECTION, "合并知识点集合，存储去重后的知识")
    ]
    
    for name, description in collections:
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                ),
                metadata={
                    "description": description,
                    "created_at": datetime.datetime.utcnow().isoformat()
                }
            )
            print(f"✅ 创建集合：{name}")
        else:
            print(f"ℹ️ 集合已存在：{name}")

def get_collection_info(collection_name: Optional[str] = None) -> dict:
    """获取集合信息
    
    Args:
        collection_name: 集合名称，如果为None则返回所有集合信息
    
    Returns:
        包含集合信息的字典
    """
    client = get_client()
    if collection_name:
        return client.get_collection(collection_name)
    
    collections = {}
    for name in [CANONICAL_COLLECTION, CONVERSATION_COLLECTION, 
                 DOCUMENT_COLLECTION, MERGED_COLLECTION]:
        try:
            info = client.get_collection(name)
            collections[name] = info
        except Exception as e:
            collections[name] = {"error": str(e)}
    
    return collections 