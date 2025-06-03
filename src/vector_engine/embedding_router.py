# src/vector_engine/embedding_router.py

"""
向量嵌入路由器：负责文本到向量的转换
"""

import openai
from src.config.env_manager import init_config

# 初始化配置
config = init_config()
openai.api_key = config['openai']['api_key']
EMBEDDING_MODEL = config['openai']['embedding_model']

def get_embedding(text: str) -> list[float]:
    """获取文本的向量嵌入"""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding
