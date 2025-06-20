# src/app/api/vector_endpoints.py
"""
Vector service endpoints for crawler integration.
Provides API access to vector store operations for external services.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ...infrastructure.vector_store import QdrantVectorStore
from ...infrastructure.vector_store.embedding_router import get_embedding
from ...infrastructure.config.env_manager import get_config
from qdrant_client import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vectors", tags=["vectors"])

# Request/Response Models
class Document(BaseModel):
    """Document to be vectorized"""
    id: str = Field(..., description="Unique document ID")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class IndexRequest(BaseModel):
    """Request to index documents"""
    documents: List[Document] = Field(..., description="Documents to index")
    collection: str = Field(default="crawled_documents", description="Target collection")

class IndexResponse(BaseModel):
    """Response from indexing operation"""
    status: str = Field(..., description="Operation status")
    count: int = Field(..., description="Number of documents indexed")
    failed: List[str] = Field(default_factory=list, description="IDs of failed documents")

class SearchRequest(BaseModel):
    """Request to search vectors"""
    query: str = Field(..., description="Search query")
    collection: str = Field(default="crawled_documents", description="Collection to search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")

class SearchResult(BaseModel):
    """Single search result"""
    id: str
    score: float
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    """Response from search operation"""
    results: List[SearchResult]
    total: int
    query: str

class CollectionRequest(BaseModel):
    """Request to create a collection"""
    name: str = Field(..., description="Collection name")
    vector_size: int = Field(default=1536, description="Vector dimension size")
    description: str = Field(default="", description="Collection description")

class CollectionResponse(BaseModel):
    """Response from collection operation"""
    status: str
    name: str
    created: bool

# Authentication dependency
async def verify_api_key(authorization: str = Header(...)) -> str:
    """Verify API key from Authorization header"""
    config = get_config()
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    
    # In production, check against stored API keys
    # For now, using a simple check from config
    expected_key = getattr(config, 'crawler_api_key', None)
    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key

# Initialize services
vector_store = QdrantVectorStore()

@router.post("/index", response_model=IndexResponse)
async def index_documents(
    request: IndexRequest,
    api_key: str = Depends(verify_api_key)
) -> IndexResponse:
    """
    Index documents from crawler service.
    
    This endpoint receives documents from the crawler service,
    generates embeddings, and stores them in the vector database.
    """
    try:
        indexed_count = 0
        failed_ids = []
        
        # Process documents in batches
        batch_size = 10
        for i in range(0, len(request.documents), batch_size):
            batch = request.documents[i:i + batch_size]
            
            # Extract texts for embedding
            texts = [doc.content for doc in batch]
            
            try:
                # Generate embeddings for each text
                embeddings = []
                for text in texts:
                    try:
                        embedding = get_embedding(text)
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.error(f"Failed to generate embedding: {str(e)}")
                        embeddings.append(None)
                
                # Prepare points for Qdrant
                points = []
                for doc, embedding in zip(batch, embeddings):
                    if embedding is None:
                        failed_ids.append(doc.id)
                        continue
                    point = models.PointStruct(
                        id=doc.id,
                        vector=embedding,
                        payload={
                            "url": doc.url,
                            "title": doc.title,
                            "content": doc.content,
                            "crawled_at": doc.metadata.get("crawled_at", datetime.utcnow().isoformat()),
                            "content_type": doc.metadata.get("content_type", "text/html"),
                            "quality_score": doc.metadata.get("quality_score", 0.0),
                            **doc.metadata
                        }
                    )
                    points.append(point)
                
                # Upsert to vector store
                vector_store.upsert(request.collection, points)
                indexed_count += len(points)
                
            except Exception as e:
                logger.error(f"Failed to index batch: {str(e)}")
                failed_ids.extend([doc.id for doc in batch])
        
        return IndexResponse(
            status="completed" if not failed_ids else "partial",
            count=indexed_count,
            failed=failed_ids
        )
        
    except Exception as e:
        logger.error(f"Indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_vectors(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
) -> SearchResponse:
    """
    Search vectors for crawler service.
    
    Performs semantic search across the specified collection
    and returns relevant documents.
    """
    try:
        # Check if collection exists
        if not vector_store.collection_exists(request.collection):
            raise HTTPException(status_code=404, detail=f"Collection '{request.collection}' not found")
        
        # Generate query embedding
        query_vector = get_embedding(request.query)
        
        # Build Qdrant filter if provided
        query_filter = None
        if request.filters:
            conditions = []
            for key, value in request.filters.items():
                if isinstance(value, list):
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value)
                        )
                    )
                else:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            
            if conditions:
                query_filter = models.Filter(must=conditions)
        
        # Perform search
        results = vector_store.search(
            collection_name=request.collection,
            query_vector=query_vector,
            limit=request.limit,
            query_filter=query_filter,
            score_threshold=request.score_threshold
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                id=str(result.id),
                score=result.score,
                url=result.payload.get("url", ""),
                title=result.payload.get("title", ""),
                content=result.payload.get("content", ""),
                metadata={
                    k: v for k, v in result.payload.items()
                    if k not in ["url", "title", "content"]
                }
            ))
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/collections", response_model=CollectionResponse)
async def create_collection(
    request: CollectionRequest,
    api_key: str = Depends(verify_api_key)
) -> CollectionResponse:
    """
    Create new collection for crawler.
    
    Creates a new vector collection with the specified configuration.
    """
    try:
        # Check if collection already exists
        if vector_store.collection_exists(request.name):
            return CollectionResponse(
                status="exists",
                name=request.name,
                created=False
            )
        
        # Create collection
        vector_store.create_collection(
            collection_name=request.name,
            vectors_config=models.VectorParams(
                size=request.vector_size,
                distance=models.Distance.COSINE
            )
        )
        
        # Create common indexes
        vector_store.create_payload_index(
            request.name,
            "url",
            models.PayloadSchemaType.KEYWORD
        )
        
        vector_store.create_payload_index(
            request.name,
            "crawled_at",
            models.PayloadSchemaType.DATETIME
        )
        
        logger.info(f"Created collection: {request.name}")
        
        return CollectionResponse(
            status="created",
            name=request.name,
            created=True
        )
        
    except Exception as e:
        logger.error(f"Collection creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")

@router.get("/collections/{collection_name}")
async def get_collection_info(
    collection_name: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Get information about a specific collection."""
    try:
        if not vector_store.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
        info = vector_store.get_collection(collection_name)
        
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "config": {
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get collection info: {str(e)}")

@router.delete("/documents")
async def delete_documents(
    collection: str,
    document_ids: List[str],
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Delete specific documents from a collection."""
    try:
        if not vector_store.collection_exists(collection):
            raise HTTPException(status_code=404, detail=f"Collection '{collection}' not found")
        
        # Delete by IDs
        vector_store.delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=document_ids)
        )
        
        return {
            "status": "deleted",
            "count": len(document_ids),
            "collection": collection
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete documents: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Check if vector service is healthy."""
    try:
        # Try to list collections as a health check
        collections = vector_store.client.get_collections()
        return {
            "status": "healthy",
            "collections_count": len(collections.collections)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Vector service unhealthy")