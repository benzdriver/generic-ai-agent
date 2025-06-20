"""
Configuration management
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Service URLs
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql://crawler:password@localhost:5432/crawler_db"
    qdrant_url: str = "http://localhost:6333"
    
    # LLM Settings
    llm_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    
    # Crawler Settings
    max_concurrent_crawls: int = 10
    default_max_depth: int = 3
    default_min_quality_score: float = 0.6
    browser_pool_size: int = 5
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    """Get cached settings instance"""
    return Settings()