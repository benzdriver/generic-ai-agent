# src/infrastructure/config/pydantic_config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, Any, Optional

class OpenAISettings(BaseSettings):
    api_key: Optional[str] = Field(None, alias='OPENAI_API_KEY')
    model: str = Field("gpt-4o-mini", alias='OPENAI_MODEL')
    embedding_model: str = Field("text-embedding-3-small", alias='EMBEDDING_MODEL')

    class Config:
        populate_by_name = True

class AnthropicSettings(BaseSettings):
    api_key: Optional[str] = Field(None, alias='ANTHROPIC_API_KEY')
    model: str = Field("claude-3-5-sonnet-latest", alias='ANTHROPIC_MODEL')

    class Config:
        populate_by_name = True

class QdrantSettings(BaseSettings):
    url: str = Field("http://localhost:6333", alias='QDRANT_URL')
    api_key: str = Field("", alias='QDRANT_API_KEY')
    collection: str = Field("immigration_qa", alias='QDRANT_COLLECTION')
    merged_collection: str = Field("immigration_merged", alias='QDRANT_MERGED_COLLECTION')
    is_cloud: bool = Field(False, alias='QDRANT_IS_CLOUD')

    class Config:
        populate_by_name = True

class TelegramSettings(BaseSettings):
    token: Optional[str] = Field(None, alias='TELEGRAM_TOKEN')

    class Config:
        populate_by_name = True

class KnowledgeSettings(BaseSettings):
    ttl_days: int = Field(180, alias='TTL_DAYS')
    tag_rule_dir: str = Field("tags", alias='TAG_RULE_DIR')

    class Config:
        populate_by_name = True

class DomainsSettings(BaseSettings):
    config_dir: str = "domains"
    default_domain: str = "immigration_consultant"

class LoggingSettings(BaseSettings):
    level: str = Field("INFO", alias='LOG_LEVEL')
    dir: str = Field("logs", alias='LOG_DIR')

    class Config:
        populate_by_name = True

class AppSettings(BaseSettings):
    openai: OpenAISettings = OpenAISettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    qdrant: QdrantSettings = QdrantSettings()
    telegram: TelegramSettings = TelegramSettings()
    knowledge: KnowledgeSettings = KnowledgeSettings()
    logging: LoggingSettings = LoggingSettings()
    domains: DomainsSettings = DomainsSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = '__'
        extra = 'ignore' 