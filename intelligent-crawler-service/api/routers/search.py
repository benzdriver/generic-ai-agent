"""
Search API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from core.models import SearchQuery, SearchResult
from ..dependencies import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/search", response_model=List[SearchResult])
async def search(
    query: SearchQuery,
    vector_store = Depends(get_vector_store)
):
    """
    Search the knowledge base
    """
    try:
        # Perform vector search
        results = await vector_store.search(
            query_text=query.query,
            collection=query.collection,
            top_k=query.top_k,
            min_score=query.min_score,
            metadata_filters=query.metadata_filters
        )
        
        # Convert to response model
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                id=result['id'],
                score=result['score'],
                text=result['text'],
                metadata=result['metadata'],
                source_url=result['metadata'].get('source_url', ''),
                source_title=result['metadata'].get('source_title', ''),
                highlights=result.get('highlights', [])
            ))
        
        return search_results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/collections")
async def list_collections(vector_store = Depends(get_vector_store)):
    """
    List available collections
    """
    try:
        collections = await vector_store.list_collections()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))