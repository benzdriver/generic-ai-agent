"""
Admin API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
import logging

from ..dependencies import get_db, get_task_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        # Placeholder stats
        return {
            "total_jobs": 0,
            "active_jobs": 0,
            "total_pages_crawled": 0,
            "total_collections": 1,
            "system_status": "operational"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collections/{collection_name}/reindex")
async def reindex_collection(collection_name: str):
    """Trigger reindexing of a collection"""
    return {
        "message": f"Reindexing triggered for collection: {collection_name}",
        "status": "queued"
    }

@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection"""
    if collection_name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default collection")
    
    return {
        "message": f"Collection {collection_name} deleted",
        "status": "success"
    }