# src/agent_core/prompt_builder.py

from typing import Dict, List, Optional
from config.domain_manager import domain_manager

# 领域特定的提示词模板
DOMAIN_PROMPTS = {
    # 移民领域模板
    "immigration": """
你是一名资深的加拿大移民顾问助手，请根据以下相关资料回答用户的问题。

【相关资料】
{context}

【用户提问】
{query}

请用简洁、专业且友好的语气作答。如果没有相关信息，请明确说明。
""",
    
    # 法律领域模板
    "legal": """
你是一名专业的法律顾问助手，请根据以下相关法律资料回答用户的问题。

【相关法律资料】
{context}

【用户提问】
{query}

请用准确、专业的法律术语回答，引用相关法条。如果信息不足以提供法律建议，请明确说明并建议咨询专业律师。
""",
    
    # 医疗领域模板
    "medical": """
你是一名医疗信息助手，请根据以下医学资料回答用户的问题。

【相关医学资料】
{context}

【用户提问】
{query}

请用通俗易懂的语言解释专业医学概念，提供科学准确的信息。强调这只是参考信息，不构成医疗建议，重要健康问题应咨询医生。
""",
    
    # 教育领域模板
    "education": """
你是一名教育顾问助手，请根据以下教育资料回答用户的问题。

【相关教育资料】
{context}

【用户提问】
{query}

请用鼓励性、启发性的语言回答，提供教育相关的建议和资源。如果信息不足，请明确说明。
""",
    
    # 默认通用模板
    "default": """
你是一名智能助手，请根据以下相关资料回答用户的问题。

【相关资料】
{context}

【用户提问】
{query}

请用简洁、专业且友好的语气作答。如果没有相关信息，请明确说明。
"""
}

def build_prompt(user_query: str, context_chunks: list = None, domain: str = "immigration_consultant", context: list = None, relevant_docs: list = None) -> str:
    """构建提示词
    
    Args:
        user_query: 用户查询
        context_chunks: 检索到的相关文本块（新参数）
        domain: 垂直领域名称，用于选择合适的提示词模板
        context: 对话上下文（兼容旧参数）
        relevant_docs: 检索到的相关文档（兼容旧参数）
        
    Returns:
        str: 构建好的提示词
    """
    # 兼容旧的调用方式
    if context_chunks is None and relevant_docs is not None:
        context_chunks = relevant_docs
    
    # 如果没有提供任何上下文，使用空列表
    if context_chunks is None:
        context_chunks = []
    
    # 合并上下文
    context_text = "\n\n".join(context_chunks)
    
    # 首先尝试从DomainManager获取领域特定的提示词模板
    domain_template = domain_manager.get_domain_prompt_template(domain)
    
    # 如果DomainManager中没有找到，则尝试使用本地定义的模板
    if not domain_template:
        domain_template = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["default"])
    
    # 填充模板
    prompt = domain_template.format(context=context_text, query=user_query)
    return prompt

def register_domain_prompt(domain: str, prompt_template: str) -> None:
    """注册新的领域提示词模板
    
    Args:
        domain: 领域名称
        prompt_template: 提示词模板，需要包含{context}和{query}占位符
    """
    if "{context}" not in prompt_template or "{query}" not in prompt_template:
        raise ValueError("提示词模板必须包含{context}和{query}占位符")
    
    # 同时更新本地缓存和DomainManager
    DOMAIN_PROMPTS[domain] = prompt_template
    
    # 检查是否已存在领域配置
    existing_config = domain_manager.get_domain_config(domain)
    if existing_config:
        # 更新现有配置中的提示词模板
        existing_config["prompt_template"] = prompt_template
        domain_manager.register_domain(domain, existing_config)
    else:
        # 创建新的领域配置
        new_config = {
            "name": domain,
            "description": f"{domain}领域",
            "prompt_template": prompt_template,
            "vector_collection": f"{domain}_docs",
            "tags": []
        }
        domain_manager.register_domain(domain, new_config)
    
    print(f"✅ 已注册领域提示词模板: {domain}")
