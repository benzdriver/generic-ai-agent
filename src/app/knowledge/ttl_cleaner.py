# src/app/knowledge/ttl_cleaner.py

"""
TTL清理器：负责清理过期的知识点
"""

from datetime import datetime, timedelta
from src.infrastructure.vector_store import BaseVectorStore, VectorStoreFactory, QdrantVectorStore
from src.infrastructure.config.env_manager import get_config

def clean_expired_points(vector_store: BaseVectorStore) -> None:
    """清理过期的向量点"""
    config = get_config()
    ttl_days = config.knowledge.ttl_days
    cutoff_date = datetime.utcnow() - timedelta(days=ttl_days)
    
    # 删除过期的点
    vector_store.delete(
        collection_name=QdrantVectorStore.DOCUMENT_COLLECTION,
        points_selector={
            "filter": {
                "must": [
                    {
                        "key": "created_at",
                        "range": {
                            "lt": cutoff_date.isoformat()
                        }
                    }
                ]
            }
        }
    )

if __name__ == "__main__":
    vector_store = VectorStoreFactory.get_vector_store()
    clean_expired_points(vector_store)
