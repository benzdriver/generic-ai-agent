# src/knowledge_manager/cluster_merger.py

"""
知识点合并器：负责合并相似的知识点
"""

import os
import requests
import datetime
import uuid
from sklearn.cluster import KMeans
from src.vector_engine.embedding_router import get_embedding
from src.config.env_manager import init_config
from src.vector_engine.doji_memory_client import get_client, DOCUMENT_COLLECTION, MERGED_COLLECTION
from llm.factory import LLMFactory

# 初始化配置
config = init_config()

# 获取LLM实例
llm = LLMFactory.get_llm()

def get_client():
    """获取doji_memory客户端（兼容接口）"""
    from src.vector_engine.doji_memory_client import get_client as get_doji_client
    return get_doji_client()

def fetch_qa_embeddings(limit=1000):
    """获取QA嵌入向量（使用doji_memory后端）"""
    print("⚠️ fetch_qa_embeddings需要重新实现以支持doji_memory")
    return []


def merge_knowledge_points(points: list) -> str:
    """合并多个知识点"""
    if not points:
        return ""
    
    if len(points) == 1:
        return points[0]
    
    # 构建合并提示词
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


def cluster_and_merge(n_clusters=10):
    data = fetch_qa_embeddings()
    if len(data) < n_clusters:
        print("⚠️ 数据量不足，跳过聚类")
        return

    ids, vectors, payloads = zip(*data)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto").fit(vectors)

    for i in range(n_clusters):
        cluster_ids = [ids[j] for j, label in enumerate(kmeans.labels_) if label == i]
        cluster_texts = [payloads[j]["text"] for j, label in enumerate(kmeans.labels_) if label == i and "text" in payloads[j]]

        if len(cluster_texts) < 2:
            continue  # skip small clusters

        summary = merge_knowledge_points(cluster_texts[:5])

        new_payload = {
            "text": summary,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "merged_from": cluster_ids[:5],
            "type": "merged_cluster"
        }

        from src.vector_engine.vector_indexer import upsert_documents
        
        metadata = {
            "collection": "merged_knowledge",
            "source": "cluster_merge",
            "tags": ["merged", "cluster"],
            "agent": "cluster_merger"
        }
        
        try:
            upsert_documents([summary], metadata)
        except Exception as e:
            print(f"❌ 存储合并知识点失败: {e}")
        print(f"✅ 合并 cluster-{i} 成功，条数：{len(cluster_texts[:5])}")


def merge_similar_points(threshold: float = 0.95):
    """合并相似的向量点"""
    client = get_client()
    
    # 获取所有向量
    points = client.scroll(
        collection_name=DOCUMENT_COLLECTION,
        limit=1000,
        with_payload=True,
        with_vectors=True
    )[0]
    
    if not points:
        return
    
    # 提取向量和元数据
    vectors = [point.vector for point in points]
    payloads = [point.payload for point in points]
    
    # 使用KMeans聚类
    n_clusters = max(1, len(vectors) // 10)  # 假设平均每10个点可能形成一个聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(vectors)
    
    # 合并相似点
    merged_points = []
    for i in range(n_clusters):
        cluster_indices = [j for j, label in enumerate(clusters) if label == i]
        if len(cluster_indices) > 1:
            # 合并该聚类的所有点
            merged_vector = sum([vectors[j] for j in cluster_indices]) / len(cluster_indices)
            merged_payload = {
                "texts": [payloads[j]["text"] for j in cluster_indices],
                "merged_at": datetime.datetime.utcnow().isoformat(),
                "source_ids": [str(points[j].id) for j in cluster_indices]
            }
            merged_points.append((merged_vector, merged_payload))
    
    # 存储合并后的点
    if merged_points:
        client.upsert(
            collection_name=MERGED_COLLECTION,
            points=[
                {"vector": vector, "payload": payload}
                for vector, payload in merged_points
            ]
        )


if __name__ == "__main__":
    cluster_and_merge(n_clusters=10)
