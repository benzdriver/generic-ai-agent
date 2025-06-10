# src/app/ingestion/qa_logger.py
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
from src.infrastructure.vector_store.embedding_router import get_embedding
from src.infrastructure.vector_store.base import BaseVectorStore
from src.infrastructure.vector_store.qdrant import QdrantVectorStore
from src.app.agent.query_normalizer import transform_query_to_canonical_form
from src.app.ingestion.tagger import auto_tag
from src.infrastructure.llm.base import BaseLLM

def log_conversation(user_id: str, question: str, answer: str, vector_store: BaseVectorStore) -> None:
    """记录对话历史"""
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
    vector_store.upsert(
        collection_name=QdrantVectorStore.CONVERSATION_COLLECTION,
        points=[conversation_point]
    )
    print(f"✅ 对话已记录到历史")

def log_canonical_query(question: str, canonical_form: str, answer: str, vector_store: BaseVectorStore) -> None:
    """记录标准化查询"""
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
    vector_store.upsert(
        collection_name=QdrantVectorStore.CANONICAL_COLLECTION,
        points=[canonical_point]
    )
    print(f"✅ 标准化查询已记录")

def log_qa_to_knowledge_base(
    question: str, 
    answer: str, 
    vector_store: BaseVectorStore,
    llm: BaseLLM,
    user_id: Optional[str] = None, 
    domain: str = "canada_immigration"
) -> None:
    """
    将用户一轮问答记录到多个集合中。
    
    Args:
        question: 用户原始提问
        answer: 生成的回答内容
        vector_store: 向量存储客户端
        llm: 语言模型客户端
        user_id: 用户ID（可选）
        domain: 领域标记
    """
    # 1. 记录对话历史
    if user_id:
        log_conversation(user_id, question, answer, vector_store)
    
    # 2. 生成并记录标准化查询
    canonical_form = transform_query_to_canonical_form(question, llm=llm, vector_store=vector_store)
    log_canonical_query(question, canonical_form, answer, vector_store)
    
    # 3. 生成标签
    tags = auto_tag(canonical_form + "\n" + answer, domain=domain)
    
    print(f"📥 问答处理完成（标签：{tags}）")
