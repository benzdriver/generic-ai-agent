"""
Qdrant客户端管理模块：统一管理Qdrant连接和集合

集合说明：
1. CANONICAL_COLLECTION: 存储规范化后的用户查询，用于查询复用
2. CONVERSATION_COLLECTION: 存储对话历史，用于上下文管理
3. DOCUMENT_COLLECTION: 存储文档知识库，包含IRCC等官方文档
4. MERGED_COLLECTION: 存储经过合并的知识点，减少冗余
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config.env_manager import init_config
from typing import Optional, Dict, Any
import datetime

config = init_config(test_mode=False)
qdrant_config = config['qdrant']

def get_client() -> QdrantClient:
    """获取Qdrant客户端
    
    根据配置返回适当的客户端实例：
    - 如果是云版本，使用API Key认证
    - 如果是本地版本，直接连接URL
    """
    if qdrant_config['is_cloud']:
        print(f"连接到Qdrant云服务: {qdrant_config['url']}")
        print(f"API密钥前10个字符: {qdrant_config['api_key'][:10]}...")
        
        return QdrantClient(
            url=qdrant_config['url'],
            api_key=qdrant_config['api_key'],
            prefer_grpc=False,
            timeout=60.0,  # 增加超时时间
            check_compatibility=False,  # 跳过版本兼容性检查
            https=True  # 确保使用HTTPS连接
        )
    return QdrantClient(
        url=qdrant_config['url'], 
        prefer_grpc=False,
        timeout=60.0,
        check_compatibility=False
    )

CANONICAL_COLLECTION = "canonical_queries"  # 规范化查询集合
CONVERSATION_COLLECTION = "conversations"   # 对话历史集合
DOCUMENT_COLLECTION = "documents"  # 文档知识库集合
MERGED_COLLECTION = "merged_knowledge"  # 合并知识点集合

def init_collections(vector_size: int = 1536):
    """初始化所有必需的集合
    
    Args:
        vector_size: 向量维度，默认使用OpenAI embedding模型的1536维
    """
    client = get_client()
    
    collections = [
        (CANONICAL_COLLECTION, "规范化查询集合，存储用户查询的标准形式"),
        (CONVERSATION_COLLECTION, "对话历史集合，存储用户对话记录"),
        (DOCUMENT_COLLECTION, "文档知识库集合，存储官方文档内容"),
        (MERGED_COLLECTION, "合并知识点集合，存储去重后的知识")
    ]
    
    for name, description in collections:
        try:
            try:
                client.get_collection(name)
                print(f"ℹ️ 集合已存在：{name}")
                continue
            except Exception as e:
                print(f"集合 {name} 不存在，错误: {str(e)}")
            
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            
            try:
                try:
                    client.create_payload_index(
                        collection_name=name,
                        field_name="created_at",
                        field_schema="float"  # 使用字符串而不是枚举
                    )
                    print(f"✅ 为集合 {name} 创建 created_at 索引成功")
                except Exception as e:
                    print(f"⚠️ 为集合 {name} 创建 created_at 索引失败: {str(e)}")
                    if "403" in str(e):
                        print("   权限不足，无法创建索引，但集合仍可使用")
                
                try:
                    client.create_payload_index(
                        collection_name=name,
                        field_name="status",
                        field_schema="keyword"  # 使用字符串而不是枚举
                    )
                    print(f"✅ 为集合 {name} 创建 status 索引成功")
                except Exception as e:
                    print(f"⚠️ 为集合 {name} 创建 status 索引失败: {str(e)}")
                    if "403" in str(e):
                        print("   权限不足，无法创建索引，但集合仍可使用")
                
                print(f"✅ 创建集合：{name} 完成")
            except Exception as index_error:
                print(f"⚠️ 无法为集合 {name} 创建索引：{str(index_error)}")
                print("   集合已创建，但索引创建失败")
        except Exception as create_error:
            print(f"❌ 创建集合 {name} 失败：{str(create_error)}")

def get_collection_info(collection_name: Optional[str] = None) -> Dict[str, Any]:
    """获取集合信息
    
    Args:
        collection_name: 集合名称，如果为None则返回所有集合信息
    
    Returns:
        包含集合信息的字典
    """
    client = get_client()
    if collection_name:
        try:
            return client.get_collection(collection_name).dict()
        except Exception as e:
            return {"error": str(e)}
    
    collections = {}
    for name in [CANONICAL_COLLECTION, CONVERSATION_COLLECTION, 
                 DOCUMENT_COLLECTION, MERGED_COLLECTION]:
        try:
            info = client.get_collection(name).dict()
            collections[name] = info
        except Exception as e:
            collections[name] = {"error": str(e)}
    
    return collections                  