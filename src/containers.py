from dependency_injector import containers, providers
from src.infrastructure.config.env_manager import get_config, Config
from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.vector_store.factory import VectorStoreFactory
from src.app.user.user_manager import UserManager, get_user_manager
from src.infrastructure.llm.base import BaseLLM
from src.infrastructure.vector_store.base import BaseVectorStore


class Container(containers.DeclarativeContainer):

    config: providers.Singleton[Config] = providers.Singleton(get_config)

    llm: providers.Singleton[BaseLLM] = providers.Singleton(
        LLMFactory.get_llm, config=config
    )

    vector_store: providers.Singleton[BaseVectorStore] = providers.Singleton(
        VectorStoreFactory.get_vector_store, config=config
    )

    user_manager: providers.Factory[UserManager] = providers.Factory(
        get_user_manager, vector_store=vector_store
    )
