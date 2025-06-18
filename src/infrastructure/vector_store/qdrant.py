# src/infrastructure/vector_store/qdrant.py
"""
Qdrant Vector Store implementation.
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from qdrant_client import QdrantClient, models
from .base import BaseVectorStore
from ..config.env_manager import QdrantConfig

PointId = Union[int, str, UUID]


class QdrantVectorStore(BaseVectorStore):
    """Qdrant implementation of the vector store."""

    CANONICAL_COLLECTION: str = "canonical_queries"
    CONVERSATION_COLLECTION: str = "conversations"
    DOCUMENT_COLLECTION: str = "documents"
    MERGED_COLLECTION: str = "merged_knowledge"

    def __init__(self, config: QdrantConfig):
        if config.is_cloud:
            self.client = QdrantClient(url=config.url, api_key=config.api_key)
        else:
            self.client = QdrantClient(url=config.url)

    def upsert(self, collection_name: str, points: List[models.PointStruct]) -> None:
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int,
        query_filter: Optional[models.Filter] = None,
        score_threshold: Optional[float] = None,
    ) -> List[models.ScoredPoint]:
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold,
        )

    def scroll(
        self,
        collection_name: str,
        scroll_filter: Optional[models.Filter] = None,
        limit: int = 10,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> Tuple[List[models.Record], Optional[PointId]]:
        return self.client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

    def delete(
        self, collection_name: str, points_selector: models.PointsSelector
    ) -> None:
        self.client.delete(
            collection_name=collection_name, points_selector=points_selector
        )

    def create_collection(
        self, collection_name: str, vectors_config: models.VectorParams, **kwargs
    ) -> None:
        self.client.create_collection(
            collection_name=collection_name, vectors_config=vectors_config, **kwargs
        )

    def collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)

    def get_collection(self, collection_name: str) -> models.CollectionInfo:
        return self.client.get_collection(collection_name)

    def create_payload_index(
        self,
        collection_name: str,
        field_name: str,
        field_schema: models.PayloadSchemaType,
    ) -> None:
        self.client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_schema,
        )

    def update_points(
        self,
        collection_name: str,
        points_selector: models.PointsSelector,
        payload: Dict[str, Any],
    ) -> None:
        self.client.set_payload(
            collection_name=collection_name,
            payload=payload,
            points=points_selector,
            wait=True,
        )

    def initialize_collections(self, vector_size: int = 1536) -> None:
        """Initializes all necessary collections in the vector store."""
        collections: List[Tuple[str, str]] = [
            (self.CANONICAL_COLLECTION, "Canonical queries collection"),
            (self.CONVERSATION_COLLECTION, "Conversation history collection"),
            (self.DOCUMENT_COLLECTION, "Document knowledge base collection"),
            (self.MERGED_COLLECTION, "Merged knowledge points collection"),
        ]

        for name, description in collections:
            if not self.collection_exists(name):
                self.client.recreate_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=vector_size, distance=models.Distance.COSINE
                    ),
                )
                print(f"✅ Created collection: {name}")
            else:
                print(f"ℹ️ Collection already exists: {name}")
