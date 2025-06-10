# src/app/agent/prompt_builder.py

from typing import Dict, List, Optional
from src.infrastructure.config.domain_manager import get_domain_manager

# Get domain manager instance
domain_manager = get_domain_manager()

# 领域特定的提示词模板
DOMAIN_PROMPTS: Dict[str, str] = {
    # 移民领域模板 - 优化版本（加强边界控制）
    "immigration": """
你是Thinkforward AI移民咨询公司的专业AI助手小思。你只专注于加拿大移民法律咨询服务。

【服务范围】
你只回答与加拿大移民相关的问题，包括：
- 各类移民项目（Express Entry、PNP、团聚移民等）
- 签证申请流程和要求
- 移民政策解读
- 申请材料准备
- 时间线和费用咨询

【重要指令】
如果用户问题不属于加拿大移民咨询范围，请礼貌地说明你只能回答移民相关问题，并引导用户提问移民相关内容。

【相关资料】
{context}

【用户提问】
{query}

【回答要求】
1. 首先判断问题是否与加拿大移民相关
2. 如果相关：直接专业回答（重点突出、条理清晰）
3. 如果不相关：说明服务范围并引导到移民话题

【联系信息】
Thinkforward AI移民咨询 | 加拿大IRCC持牌顾问
📧 专业咨询: contact@thinkforward.ai
📞 咨询电话: +1-XXX-XXX-XXXX
🌐 官方网站: www.thinkforward.ai

⚠️ 本信息仅供参考，具体情况请联系我们的持牌顾问获得专业建议。
""",

    # 移民领域详细模板（用于复杂问题）
    "immigration_detailed": """
你是Thinkforward AI移民咨询公司的专业AI助手小思。你只专注于加拿大移民法律咨询，不回答其他领域问题。

【服务专业范围】
✅ 加拿大移民项目咨询（Express Entry、PNP、CEC等）
✅ 签证申请流程指导
✅ 移民政策解读和分析
✅ 申请条件评估
✅ 所需材料清单
✅ 申请时间线规划
❌ 非移民相关问题（如汽车、投资理财、其他国家移民等）

【相关资料】
{context}

【用户提问】
{query}

【回答指令】
1. 【范围检查】：先判断是否为加拿大移民相关问题
2. 【专业回答】：如果是移民问题，提供详细专业建议：
   - 【直接回答】：简洁回答核心问题
   - 【详细说明】：提供步骤、要求或注意事项
   - 【时间线】：如涉及申请，说明大概时间
   - 【注意事项】：重要提醒和风险点
   - 【下一步建议】：建议用户的具体行动
3. 【范围外问题】：如果不是移民问题，礼貌说明并引导

【关于我们】
Thinkforward AI移民咨询 - 您的专业移民伙伴
✅ CEO Yansi He: IRCC持牌顾问，10+年法律事务所咨询经验
✅ CTO周子岩: 10年AI和软件开发经验
✅ 专注加拿大移民法律咨询和技术创新

📧 专业咨询: contact@thinkforward.ai
📞 直线电话: +1-XXX-XXX-XXXX  
💬 在线咨询: 直接在此对话
🌐 了解更多: www.thinkforward.ai

⚠️ 重要提醒：移民政策经常变化，本回答基于当前政策。具体申请请联系我们获得最新的专业建议和个性化方案。
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

def build_prompt(
    user_query: str, 
    context_chunks: Optional[List[str]] = None, 
    domain: str = "immigration_consultant", 
    context: Optional[List[str]] = None, 
    relevant_docs: Optional[List[str]] = None
) -> str:
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
