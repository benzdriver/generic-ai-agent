# src/app/knowledge/cluster_merger.py

"""
知识点合并器：负责合并相似的知识点
"""

import datetime
import uuid
from typing import Dict, Any, List, Tuple
from sklearn.cluster import KMeans
from qdrant_client import QdrantClient
from src.infrastructure.vector_store.embedding_router import get_embedding
from src.infrastructure.config.env_manager import get_config
from src.infrastructure.vector_store import BaseVectorStore, VectorStoreFactory
from src.infrastructure.llm import BaseLLM, LLMFactory

def _merge_knowledge_points(points: List[str], llm: BaseLLM) -> str:
    """合并多个知识点"""
    if not points:
        return ""
    
    if len(points) == 1:
        return points[0]
    
    prompt = f"""请将以下几个相关的知识点合并为一个完整的知识点：

知识点列表：
{'\n'.join(f'- {p}' for p in points)}

要求：
1. 保留所有重要信息
2. 去除重复内容
3. 使表述更加完整和准确
4. 保持逻辑连贯性
"""
    
    return llm.generate(prompt).strip()


def cluster_and_merge(n_clusters: int = 10) -> None:
    vector_store: BaseVectorStore = VectorStoreFactory.get_vector_store()
    llm: BaseLLM = LLMFactory.get_llm()

    points, _ = vector_store.scroll(
        collection_name=vector_store.DOCUMENT_COLLECTION,
        limit=1000,
        with_payload=True,
        with_vectors=True
    )
    
    if not points or len(points) < n_clusters:
        print("⚠️ 数据量不足，跳过聚类")
        return

    ids = [p.id for p in points]
    vectors = [p.vector for p in points]
    payloads = [p.payload for p in points]
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto").fit(vectors)

    for i in range(n_clusters):
        cluster_indices = [j for j, label in enumerate(kmeans.labels_) if label == i]
        
        if len(cluster_indices) < 2:
            continue

        cluster_texts = [payloads[j]["text"] for j in cluster_indices if "text" in payloads[j]]
        
        if len(cluster_texts) < 2:
            continue

        summary = _merge_knowledge_points(cluster_texts[:5], llm)

        new_payload = {
            "text": summary,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "merged_from": [ids[j] for j in cluster_indices[:5]],
            "type": "merged_cluster"
        }

        vector_store.upsert(
            collection_name=vector_store.MERGED_COLLECTION,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": get_embedding(summary),
                "payload": new_payload
            }]
        )
        print(f"✅ 合并 cluster-{i} 成功，条数：{len(cluster_texts[:5])}")


if __name__ == "__main__":
    cluster_and_merge(n_clusters=10)
