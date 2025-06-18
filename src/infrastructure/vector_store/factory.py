# src/infrastructure/vector_store/factory.py

from .base import BaseVectorStore
from .qdrant import QdrantVectorStore
from ..config.env_manager import Config


class VectorStoreFactory:
    """Factory for creating vector store clients."""

    @staticmethod
    def get_vector_store(
        config: Config, provider: str = "qdrant"
    ) -> BaseVectorStore:
        """Get a vector store client based on the provider."""
        if provider == "qdrant":
            return QdrantVectorStore(config.qdrant)
        # Add other providers here in the future
        # elif provider == "pinecone":
        #     return PineconeVectorStore(config.pinecone)
        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")
