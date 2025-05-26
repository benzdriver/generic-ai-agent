# src/knowledge_ingestion/qa_logger.py
"""
模块名称：qa_logger.py

功能：
- 将每轮问答结构化存储为知识片段，并写入 Qdrant 向量数据库
- 记录对话历史到 CONVERSATION_COLLECTION
- 记录标准化查询到 CANONICAL_COLLECTION
- 自动进行语义问法规范化和关键词打标签
"""
import uuid
import datetime
from typing import Optional
from vector_engine.embedding_router import get_embedding
from vector_engine.qdrant_client import (
    CANONICAL_COLLECTION,
    CONVERSATION_COLLECTION,
    get_client
)
from agent_core.canonical_router import transform_query_to_canonical_form
from knowledge_ingestion.tagger import auto_tag

def log_conversation(user_id: str, question: str, answer: str):
    """记录对话历史"""
    client = get_client()
    conversation_point = {
        "id": str(uuid.uuid4()),
        "vector": get_embedding(question + answer),
        "payload": {
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
    }
    client.upsert(
        collection_name=CONVERSATION_COLLECTION,
        points=[conversation_point]
    )
    print(f"✅ 对话已记录到历史")

def log_canonical_query(question: str, canonical_form: str, answer: Optional[str] = None):
    """记录标准化查询"""
    client = get_client()
    canonical_point = {
        "id": str(uuid.uuid4()),
        "vector": get_embedding(canonical_form),
        "payload": {
            "original_question": question,
            "canonical_form": canonical_form,
            "answer": answer,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
    }
    client.upsert(
        collection_name=CANONICAL_COLLECTION,
        points=[canonical_point]
    )
    print(f"✅ 标准化查询已记录")

def log_qa_to_knowledge_base(question: str, answer: str, user_id: str = None, domain: str = "canada_immigration"):
    """
    将用户一轮问答记录到多个集合中。
    
    Args:
        question: 用户原始提问
        answer: 生成的回答内容
        user_id: 用户ID（可选）
        domain: 领域标记
    """
    # 1. 记录对话历史
    if user_id:
        log_conversation(user_id, question, answer)
    
    # 2. 生成并记录标准化查询
    canonical_form = transform_query_to_canonical_form(question)
    log_canonical_query(question, canonical_form, answer)
    
    # 3. 生成标签
    tags = auto_tag(canonical_form + "\n" + answer, domain=domain)
    
    print(f"📥 问答处理完成（标签：{tags}）")
