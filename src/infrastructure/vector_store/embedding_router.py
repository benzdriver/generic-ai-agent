# src/infrastructure/vector_store/embedding_router.py

"""
向量嵌入路由器：负责文本到向量的转换
"""

import openai
from typing import Dict, Any, List
from ..config.env_manager import get_config

def get_embedding(text: str) -> List[float]:
    """获取文本的向量嵌入"""
    # 获取配置
    config = get_config()
    
    # 检查API key是否存在
    if not config.openai.api_key:
        raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable.")
    
    # 创建临时客户端
    client = openai.OpenAI(api_key=config.openai.api_key)
    
    response = client.embeddings.create(
        model=config.openai.embedding_model,
        input=text
    )
    return response.data[0].embedding