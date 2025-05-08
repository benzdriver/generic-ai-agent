"""
环境变量管理模块：集中管理所有配置项
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
def load_env() -> None:
    """加载环境变量，优先级：.env.local > .env"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    local_env_path = Path(__file__).parent.parent.parent / '.env.local'
    
    if local_env_path.exists():
        load_dotenv(local_env_path)
    elif env_path.exists():
        load_dotenv(env_path)

# OpenAI 配置
def get_openai_config() -> Dict[str, str]:
    """获取 OpenAI 相关配置"""
    return {
        'api_key': os.environ.get('OPENAI_API_KEY'),
        'model': os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
        'embedding_model': os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')
    }

# Anthropic 配置
def get_anthropic_config() -> Dict[str, str]:
    """获取 Anthropic 相关配置"""
    return {
        'api_key': os.environ.get('ANTHROPIC_API_KEY'),
        'model': os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')
    }

# Qdrant 配置
def get_qdrant_config() -> Dict[str, Any]:
    """获取 Qdrant 相关配置"""
    return {
        'url': os.environ.get('QDRANT_URL', 'http://localhost:6333'),
        'api_key': os.environ.get('QDRANT_API_KEY'),
        'collection': os.environ.get('QDRANT_COLLECTION', 'immigration_qa'),
        'merged_collection': os.environ.get('QDRANT_MERGED_COLLECTION', 'immigration_merged'),
        'is_cloud': os.environ.get('QDRANT_IS_CLOUD', 'false').lower() == 'true'
    }

# Telegram 配置
def get_telegram_config() -> Dict[str, str]:
    """获取 Telegram 相关配置"""
    return {
        'token': os.environ.get('TELEGRAM_TOKEN')
    }

# 知识管理配置
def get_knowledge_config() -> Dict[str, Any]:
    """获取知识管理相关配置"""
    return {
        'ttl_days': int(os.environ.get('TTL_DAYS', 180)),
        'tag_rule_dir': os.environ.get('TAG_RULE_DIR', 'tags')
    }

# 日志配置
def get_logging_config() -> Dict[str, str]:
    """获取日志相关配置"""
    return {
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
        'dir': os.environ.get('LOG_DIR', 'logs')
    }

# 验证必需的环境变量
def validate_required_env() -> None:
    """验证必需的环境变量是否已设置"""
    required_vars = [
        'OPENAI_API_KEY',
        'TELEGRAM_TOKEN'
    ]
    
    # 如果使用Qdrant Cloud，需要API Key
    if os.environ.get('QDRANT_IS_CLOUD', 'false').lower() == 'true':
        required_vars.append('QDRANT_API_KEY')
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# 初始化所有配置
def init_config() -> Dict[str, Any]:
    """初始化并返回所有配置"""
    load_env()
    validate_required_env()
    
    return {
        'openai': get_openai_config(),
        'anthropic': get_anthropic_config(),
        'qdrant': get_qdrant_config(),
        'telegram': get_telegram_config(),
        'knowledge': get_knowledge_config(),
        'logging': get_logging_config()
    } 