# src/app/agent/response_router.py

"""
模块名称：response_router.py

功能：
- 处理用户查询并生成回答
- 利用多个知识库集合提供更准确的回答
- 支持对话历史和查询复用
"""

from typing import Dict, Any, List, Optional
from qdrant_client import models
from qdrant_client.http.models import ScoredPoint, Record
from src.infrastructure.vector_store.base import BaseVectorStore
from src.infrastructure.vector_store.qdrant import QdrantVectorStore
from src.infrastructure.vector_store.embedding_router import get_embedding
from src.app.agent.prompt_builder import build_prompt
from src.infrastructure.llm.base import BaseLLM
from src.app.ingestion.qa_logger import log_qa_to_knowledge_base
from src.app.agent.query_normalizer import transform_query_to_canonical_form
from src.infrastructure.config.domain_manager import get_domain_manager
from src.infrastructure.config.env_manager import get_config

# 获取系统配置
config = get_config()
domain_manager = get_domain_manager()

def get_conversation_context(user_id: str, vector_store: BaseVectorStore, limit: int = 5) -> List[Record]:
    """获取用户最近的对话历史"""
    results = vector_store.scroll(
        collection_name=QdrantVectorStore.CONVERSATION_COLLECTION,
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
    return results[0] if results else []

def find_similar_canonical_query(query: str, vector_store: BaseVectorStore, threshold: float = 0.8) -> Optional[ScoredPoint]:
    """查找相似的标准化查询"""
    results = vector_store.search(
        collection_name=QdrantVectorStore.CANONICAL_COLLECTION,
        query_vector=get_embedding(query),
        limit=1,
        score_threshold=threshold
    )
    return results[0] if results else None

def retrieve_relevant_documents(query: str, vector_store: BaseVectorStore, domain: Optional[str] = None, top_k: int = 3) -> List[ScoredPoint]:
    """从文档库中检索相关内容
    
    Args:
        query: 用户查询
        domain: 领域名称，用于确定使用哪个向量集合
        top_k: 返回的最大结果数
        
    Returns:
        list: 检索到的文档列表
    """
    collection_name = QdrantVectorStore.DOCUMENT_COLLECTION
    if domain:
        domain_collection = domain_manager.get_domain_collection(domain)
        if domain_collection:
            collection_name = domain_collection
    
    results = vector_store.search(
        collection_name=collection_name,
        query_vector=get_embedding(query),
        limit=top_k
    )
    return results

def is_complex_query(query: str, llm: BaseLLM) -> bool:
    """判断查询是否复杂，需要详细回答"""
    # 简单启发式规则
    if len(query) > 50:  # 长问题通常更复杂
        return True
    
    # 检查是否包含复杂关键词
    complex_keywords = [
        "步骤", "流程", "怎么办", "申请条件", "所需材料", "时间线", 
        "requirements", "process", "steps", "timeline", "documents needed",
        "详细", "具体", "complete", "detailed"
    ]
    
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in complex_keywords):
        return True
    
    return False

def get_user_context_summary(user_id: str, vector_store: BaseVectorStore) -> str:
    """获取用户上下文摘要"""
    context_records = get_conversation_context(user_id, vector_store, limit=3)
    
    if not context_records:
        return "新用户，无历史对话记录"
    
    # 构建简单的上下文摘要
    recent_topics = []
    for record in context_records:
        if 'question' in record.payload:
            question = record.payload['question'][:100]  # 截取前100字符
            recent_topics.append(f"- {question}")
    
    if recent_topics:
        return f"用户最近询问过：\n" + "\n".join(recent_topics[-2:])  # 只显示最近2个
    else:
        return "用户有历史对话，但无法解析"

def is_immigration_related(query: str) -> bool:
    """检测查询是否与移民相关（使用轻量级关键词匹配，不调用LLM API）"""
    query_lower = query.lower()
    
    # 明确的移民关键词
    immigration_keywords = [
        "移民", "签证", "express entry", "pnp", "工签", "学签", "永久居民", "pr", "citizenship",
        "immigration", "visa", "permit", "resident", "sponsor", "family class", "refugee",
        "cec", "fsw", "skilled worker", "provincial nominee", "lmia", "ielts", "celpip",
        "枫叶卡", "入籍", "团聚", "雅思", "语言考试", "加拿大移民", "申请移民", "移民条件",
        "移民政策", "移民法", "移民顾问", "申请pr", "移民项目", "移民时间", "移民费用",
        "canada", "canadian", "加拿大", "申请", "条件", "要求", "流程", "材料", "费用"
    ]
    
    # 非移民关键词（明确排除）
    non_immigration_keywords = [
        "汽车", "suv", "car", "vehicle", "automobile", "房地产", "买房", "房价", "投资", "股票", "基金",
        "医疗", "看病", "医院", "保险", "天气", "旅游", "美食", "购物", "电影", "电视", "音乐", 
        "体育", "游戏", "技术", "编程", "软件", "硬件", "娱乐", "新闻", "政治", "经济",
        "数学", "物理", "化学", "历史", "地理", "文学", "艺术", "科学", "教育", "学校",
        "工作", "求职", "简历", "面试", "薪水", "创业", "生意", "餐厅", "酒店", "飞机",
        "火车", "公交", "地铁", "手机", "电脑", "网站", "app", "社交", "约会", "结婚",
        "宠物", "动物", "植物", "花园", "装修", "家具", "服装", "化妆", "健身", "运动"
    ]
    
    # 检查是否包含移民关键词
    has_immigration_keywords = any(keyword in query_lower for keyword in immigration_keywords)
    
    # 检查是否包含非移民关键词
    has_non_immigration_keywords = any(keyword in query_lower for keyword in non_immigration_keywords)
    
    # 如果明确包含非移民关键词且不包含移民关键词，判定为非移民相关
    if has_non_immigration_keywords and not has_immigration_keywords:
        return False
    
    # 如果包含移民关键词，判定为移民相关
    if has_immigration_keywords:
        return True
    
    # 对于模糊的情况，使用简单的长度判断
    # 如果是很短的问候语或简单问题，判定为可能相关（保守策略）
    if len(query.strip()) < 15:
        return True
    
    # 默认情况下，假设与移民相关（保守策略，避免误判）
    return True

def generate_non_immigration_response() -> str:
    """生成非移民问题的标准回复"""
    return """
抱歉，我是Thinkforward AI移民咨询的专业AI助手小思，只能回答与加拿大移民相关的问题。

🎯 我可以帮您解答：
• 各类加拿大移民项目（Express Entry、PNP等）
• 签证申请流程和要求
• 移民政策解读和分析
• 申请条件评估和材料准备
• 移民时间线和费用咨询

💡 不妨问我这些问题：
"Express Entry需要什么条件？"
"我可以申请哪个省提名项目？"
"配偶担保移民需要多长时间？"

📞 如需其他服务或人工咨询：
📧 专业咨询: contact@thinkforward.ai
🌐 官方网站: www.thinkforward.ai
"""

def generate_response(
    user_query: str, 
    llm: BaseLLM,
    vector_store: BaseVectorStore,
    user_id: Optional[str] = None, 
    domain: Optional[str] = None
) -> str:
    """生成回答
    
    Args:
        user_query: 用户查询
        user_id: 用户ID（可选）
        domain: 领域名称（可选），默认使用系统配置的默认领域
        
    Returns:
        str: 生成的回答
    """
    if domain is None:
        domain = config.domains.default_domain
    
    # 首先检查是否为移民相关问题（仅对移民领域进行边界检测）
    # 使用轻量级关键词检测，不调用LLM API，节省成本
    if domain in ["immigration_consultant", "immigration"]:
        if not is_immigration_related(user_query):
            return generate_non_immigration_response()
    
    # 获取用户上下文
    user_context_summary = ""
    if user_id:
        user_context_summary = get_user_context_summary(user_id, vector_store)
    
    canonical_query = transform_query_to_canonical_form(user_query, llm=llm, vector_store=vector_store)
    
    similar_query = find_similar_canonical_query(canonical_query, vector_store)
    if similar_query and similar_query.score > 0.9:
        return similar_query.payload["answer"]
    
    relevant_docs = retrieve_relevant_documents(canonical_query, vector_store, domain=domain)
    doc_contents = [doc.payload["content"] for doc in relevant_docs]
    
    # 智能选择模板：根据问题复杂度
    template_domain = domain
    if domain == "immigration_consultant" or domain == "immigration":
        if is_complex_query(user_query, llm):
            template_domain = "immigration_detailed"
        else:
            template_domain = "immigration"
    
    prompt = build_prompt(user_query, doc_contents, domain=template_domain)
    
    # 如果有用户上下文，添加到prompt中
    if user_context_summary and user_context_summary != "新用户，无历史对话记录":
        prompt = f"【用户背景】\n{user_context_summary}\n\n{prompt}"
    
    domain_llm_config = domain_manager.get_domain_llm_config(domain)
    
    if domain_llm_config:
        provider = domain_llm_config.get('preferred_provider')
        model_params = domain_llm_config.get('model_params', {})
        # 为了获得更简洁的回答，调整参数
        model_params['temperature'] = model_params.get('temperature', 0.2)  # 降低创造性
        model_params['top_p'] = model_params.get('top_p', 0.8)  # 提高一致性
        response = llm.generate(prompt, provider=provider, **model_params)
    else:
        response = llm.generate(prompt, temperature=0.2, top_p=0.8)
    
    log_qa_to_knowledge_base(user_query, response, vector_store, user_id=user_id, llm=llm)
    
    return response
