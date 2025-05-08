# src/knowledge_manager/delete_old_points.py

"""
旧点删除器：负责删除过期或废弃的向量点
"""

from qdrant_client import QdrantClient
from config.env_manager import init_config

# 初始化配置
config = init_config()
QDRANT_URL = config['qdrant']['url']
SOURCE_COLLECTION = config['qdrant']['collection']
MERGED_COLLECTION = config['qdrant']['merged_collection']

def get_client() -> QdrantClient:
    """获取Qdrant客户端"""
    return QdrantClient(url=QDRANT_URL)

def delete_old_points():
    """删除已标记为废弃的向量点"""
    client = get_client()
    
    # 删除原始集合中的废弃点
    client.delete(
        collection_name=SOURCE_COLLECTION,
        filter={
            "must": [
                {
                    "key": "status",
                    "match": {
                        "value": "obsolete"
                    }
                }
            ]
        }
    )
    
    # 删除合并集合中的废弃点
    client.delete(
        collection_name=MERGED_COLLECTION,
        filter={
            "must": [
                {
                    "key": "status",
                    "match": {
                        "value": "obsolete"
                    }
                }
            ]
        }
    )

if __name__ == "__main__":
    delete_old_points()
