# src/infrastructure/vector_store/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """Abstract base class for vector store clients."""

    @abstractmethod
    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """Upsert points into the vector store."""
        pass

    @abstractmethod
    def search(self, collection_name: str, query_vector: List[float], limit: int, query_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Search for similar vectors in the vector store."""
        pass
        
    @abstractmethod
    def scroll(self, collection_name: str, scroll_filter: Optional[Dict[str, Any]] = None, limit: int = 10, with_payload: bool = True, with_vectors: bool = False) -> List[Any]:
        """Scroll through points in the vector store."""
        pass
        
    @abstractmethod
    def delete(self, collection_name: str, filter: Dict[str, Any]) -> None:
        """Delete points from the vector store."""
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, vectors_config: Any, metadata: Dict[str, Any]) -> None:
        """Create a new collection."""
        pass

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass

    @abstractmethod
    def get_collection(self, collection_name: str) -> Any:
        """Get information about a collection."""
        pass
        
    @abstractmethod
    def create_payload_index(self, collection_name: str, field_name: str, field_schema: Any) -> None:
        """Create a payload index."""
        pass
        
    @abstractmethod
    def update_points(self, collection_name: str, points_selector: Any, payload: Dict[str, Any]) -> None:
        """Update points in the vector store."""
        pass 