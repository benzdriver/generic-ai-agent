# src/app/knowledge/delete_old_points.py

"""
旧点删除器：负责删除过期或废弃的向量点
"""

from src.infrastructure.vector_store import BaseVectorStore, VectorStoreFactory, QdrantVectorStore

def delete_old_points(vector_store: BaseVectorStore) -> None:
    """删除已标记为废弃的向量点"""
    
    # 删除原始集合中的废弃点
    vector_store.delete(
        collection_name=QdrantVectorStore.DOCUMENT_COLLECTION,
        points_selector={
            "filter": {
                "must": [
                    {
                        "key": "status",
                        "match": {
                            "value": "obsolete"
                        }
                    }
                ]
            }
        }
    )
    
    # 删除合并集合中的废弃点
    vector_store.delete(
        collection_name=QdrantVectorStore.MERGED_COLLECTION,
        points_selector={
            "filter": {
                "must": [
                    {
                        "key": "status",
                        "match": {
                            "value": "obsolete"
                        }
                    }
                ]
            }
        }
    )

if __name__ == "__main__":
    vector_store = VectorStoreFactory.get_vector_store()
    delete_old_points(vector_store)
