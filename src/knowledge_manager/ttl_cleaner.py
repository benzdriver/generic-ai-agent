# src/knowledge_manager/ttl_cleaner.py

"""
TTL清理器：负责清理过期的知识点
"""

from datetime import datetime, timedelta
from vector_engine.qdrant_client import (
    get_client,
    DOCUMENT_COLLECTION,
)
from config.env_manager import init_config

# 初始化配置
config = init_config()
TTL_DAYS = config['knowledge']['ttl_days']

def clean_expired_points():
    """清理过期的向量点"""
    client = get_client()
    cutoff_date = datetime.utcnow() - timedelta(days=TTL_DAYS)
    
    # 删除过期的点
    client.delete(
        collection_name=DOCUMENT_COLLECTION,
        filter={
            "must": [
                {
                    "key": "created_at",
                    "range": {
                        "lt": cutoff_date.isoformat()
                    }
                }
            ]
        }
    )

if __name__ == "__main__":
    clean_expired_points()
