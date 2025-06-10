# src/infrastructure/vector_store/factory.py

from .base import BaseVectorStore
from .qdrant import QdrantVectorStore

class VectorStoreFactory:
    """Factory for creating vector store clients."""

    @staticmethod
    def get_vector_store(provider: str = "qdrant") -> BaseVectorStore:
        """Get a vector store client based on the provider."""
        if provider == "qdrant":
            return QdrantVectorStore()
        # Add other providers here in the future
        # elif provider == "pinecone":
        #     return PineconeVectorStore()
        else:
            raise ValueError(f"Unsupported vector store provider: {provider}") 