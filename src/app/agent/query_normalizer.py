# src/app/agent/query_normalizer.py

"""
规范化路由器：负责将用户问题转换为标准形式
"""

import datetime
import uuid
from typing import Dict, Any
from src.infrastructure.vector_store.embedding_router import get_embedding
from src.infrastructure.vector_store.base import BaseVectorStore
from src.infrastructure.vector_store.qdrant import QdrantVectorStore
from src.infrastructure.llm.base import BaseLLM

def transform_query_to_canonical_form(
    user_query: str, 
    llm: BaseLLM,
    vector_store: BaseVectorStore,
    threshold: float = 0.9
) -> str:
    """将用户问题转换为标准形式"""
    
    # Step 1: embed original question
    embedding = get_embedding(user_query)

    # Step 2: search for similar canonical question
    hits = vector_store.search(
        collection_name=QdrantVectorStore.CANONICAL_COLLECTION,
        query_vector=embedding,
        limit=1
    )

    if hits and hits[0].score >= threshold:
        return hits[0].payload["canonical"]

    # Step 3: fallback to LLM to normalize
    prompt = f"请将以下用户问题改写为标准化移民术语表达，用于统一检索：\n\n用户问题：{user_query}"
    canonical = llm.generate(prompt)

    # Step 4: store canonical question for future reuse
    vector_store.upsert(
        collection_name=QdrantVectorStore.CANONICAL_COLLECTION,
        points=[{
            "id": str(uuid.uuid4()),
            "vector": embedding,
            "payload": {
                "raw": user_query,
                "canonical": canonical,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
        }]
    )
    
    return canonical.strip()
