# src/agent_core/response_router.py

"""
模块名称：response_router.py

功能：
- 处理用户查询并生成回答
- 利用多个知识库集合提供更准确的回答
- 支持对话历史和查询复用
"""

from qdrant_client import models
from vector_engine.qdrant_client import (
    CANONICAL_COLLECTION,
    CONVERSATION_COLLECTION,
    DOCUMENT_COLLECTION,
    get_client
)
from vector_engine.embedding_router import get_embedding
from agent_core.prompt_builder import build_prompt
from llm.factory import LLMFactory
from knowledge_ingestion.qa_logger import log_qa_to_knowledge_base
from agent_core.canonical_router import transform_query_to_canonical_form
from config.domain_manager import domain_manager
from config.env_manager import init_config

# 获取系统配置
config = init_config()
default_domain = config['domains']['default_domain']

# 获取LLM实例
llm = LLMFactory.get_llm()

def get_conversation_context(user_id: str, limit: int = 5):
    """获取用户最近的对话历史"""
    client = get_client()
    results = client.scroll(
        collection_name=CONVERSATION_COLLECTION,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    return results[0]  # 返回对话记录列表

def find_similar_canonical_query(query: str, threshold: float = 0.8):
    """查找相似的标准化查询"""
    client = get_client()
    results = client.search(
        collection_name=CANONICAL_COLLECTION,
        query_vector=get_embedding(query),
        limit=1,
        score_threshold=threshold
    )
    return results[0] if results else None

def retrieve_relevant_documents(query: str, domain: str = None, top_k: int = 3):
    """从文档库中检索相关内容
    
    Args:
        query: 用户查询
        domain: 领域名称，用于确定使用哪个向量集合
        top_k: 返回的最大结果数
        
    Returns:
        list: 检索到的文档列表
    """
    client = get_client()
    
    # 确定使用哪个集合
    collection_name = DOCUMENT_COLLECTION
    if domain:
        # 获取领域特定的向量集合名称
        domain_collection = domain_manager.get_domain_collection(domain)
        if domain_collection:
            collection_name = domain_collection
    
    # 执行向量搜索
    results = client.search(
        collection_name=collection_name,
        query_vector=get_embedding(query),
        limit=top_k
    )
    return results

def generate_response(user_query: str, user_id: str = None, domain: str = None) -> str:
    """生成回答
    
    Args:
        user_query: 用户查询
        user_id: 用户ID（可选）
        domain: 领域名称（可选），默认使用系统配置的默认领域
        
    Returns:
        str: 生成的回答
    """
    # 使用指定领域或默认领域
    if domain is None:
        domain = default_domain
    
    # 1. 获取对话上下文
    context = get_conversation_context(user_id) if user_id else []
    
    # 2. 规范化用户查询
    canonical_query = transform_query_to_canonical_form(user_query)
    
    # 3. 使用规范化查询搜索相似问题
    similar_query = find_similar_canonical_query(canonical_query)
    if similar_query and similar_query.score > 0.9:
        return similar_query.payload["answer"]
    
    # 4. 使用规范化查询检索相关文档
    relevant_docs = retrieve_relevant_documents(canonical_query, domain=domain)
    doc_contents = [doc.payload["content"] for doc in relevant_docs]
    
    # 5. 构建 prompt，使用指定领域
    prompt = build_prompt(
        user_query,
        doc_contents,
        domain=domain
    )
    
    # 6. 获取领域特定的LLM配置
    domain_llm_config = domain_manager.get_domain_llm_config(domain)
    
    # 7. 生成回答
    if domain_llm_config:
        # 使用领域特定的LLM配置
        provider = domain_llm_config.get('preferred_provider')
        model_params = domain_llm_config.get('model_params', {})
        response = llm.generate(prompt, provider=provider, **model_params)
    else:
        # 使用默认LLM配置
        response = llm.generate(prompt)
    
    # 8. 记录到知识库
    log_qa_to_knowledge_base(user_query, response, user_id)
    
    return response
