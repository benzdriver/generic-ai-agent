# src/agent_core/canonical_router.py

"""
规范化路由器：负责将用户问题转换为标准形式
"""

import datetime
import uuid
from vector_engine.embedding_router import get_embedding
from vector_engine.qdrant_client import get_client, CANONICAL_COLLECTION
from config.env_manager import init_config
from llm.factory import LLMFactory

# 初始化配置
config = init_config()

# 获取LLM实例
llm = LLMFactory.get_llm()

def transform_query_to_canonical_form(user_query: str, threshold: float = 0.9) -> str:
    """将用户问题转换为标准形式"""
    client = get_client()
    
    # Step 1: embed original question
    embedding = get_embedding(user_query)

    # Step 2: search for similar canonical question
    hits = client.search(
        collection_name=CANONICAL_COLLECTION,
        query_vector=embedding,
        limit=1
    )

    if hits and hits[0].score >= threshold:
        payload = hits[0].payload or {}
        return payload.get("canonical_form") or payload.get("canonical")

    # Step 3: fallback to LLM to normalize
    prompt = f"请将以下用户问题改写为标准化移民术语表达，用于统一检索：\n\n用户问题：{user_query}"
    canonical_form = llm.generate(prompt)

    # Step 4: store canonical question for future reuse
    client.upsert(
        collection_name=CANONICAL_COLLECTION,
        points=[{
            "id": str(uuid.uuid4()),
            "vector": embedding,
            "payload": {
                "original_question": user_query,
                "canonical_form": canonical_form,
                "answer": None,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
        }]
    )

    return canonical_form.strip()
