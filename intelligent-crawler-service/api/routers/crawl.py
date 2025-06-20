"""
Crawl API endpoints
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from ..dependencies import get_redis, get_db, get_task_manager
from core.models import CrawlConfig, CrawlJob, CrawlStatus

logger = logging.getLogger(__name__)

router = APIRouter()

class CrawlRequest(BaseModel):
    """Crawl request model"""
    urls: List[HttpUrl] = Field(..., description="List of URLs to crawl")
    config: Optional[CrawlConfig] = Field(default=None, description="Crawl configuration")
    collection_name: str = Field(default="default", description="Vector collection name")
    callback_url: Optional[HttpUrl] = Field(default=None, description="Webhook for completion")

class CrawlResponse(BaseModel):
    """Crawl response model"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None

@router.post("/crawl", response_model=CrawlResponse)
async def create_crawl_job(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    task_manager = Depends(get_task_manager)
):
    """
    Create a new crawl job
    
    This endpoint initiates an intelligent crawl of the provided URLs.
    The crawl happens asynchronously and you can check the status using the job_id.
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job
        job = CrawlJob(
            job_id=job_id,
            urls=[str(url) for url in request.urls],
            config=request.config or CrawlConfig(),
            collection_name=request.collection_name,
            callback_url=str(request.callback_url) if request.callback_url else None,
            status=CrawlStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        
        # Queue the job
        await task_manager.queue_crawl_job(job)
        
        # Estimate completion time based on URL count and depth
        url_count = len(request.urls)
        max_depth = request.config.max_depth if request.config else 3
        estimated_minutes = url_count * max_depth * 2  # Rough estimate
        
        return CrawlResponse(
            job_id=job_id,
            status="queued",
            message=f"Crawl job created for {url_count} URLs",
            created_at=job.created_at,
            estimated_completion=datetime.utcnow().timestamp() + (estimated_minutes * 60)
        )
        
    except Exception as e:
        logger.error(f"Error creating crawl job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crawl/{job_id}")
async def get_crawl_status(
    job_id: str,
    task_manager = Depends(get_task_manager)
):
    """
    Get crawl job status
    
    Returns detailed status information about a crawl job.
    """
    try:
        job = await task_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "urls_crawled": job.urls_crawled,
            "urls_total": len(job.urls),
            "pages_discovered": job.pages_discovered,
            "errors": job.errors,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "results_preview": job.results_preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl/{job_id}/cancel")
async def cancel_crawl_job(
    job_id: str,
    task_manager = Depends(get_task_manager)
):
    """
    Cancel a crawl job
    
    Attempts to cancel a running or queued crawl job.
    """
    try:
        success = await task_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or already completed")
        
        return {"message": "Job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crawl/{job_id}/results")
async def get_crawl_results(
    job_id: str,
    offset: int = 0,
    limit: int = 100,
    task_manager = Depends(get_task_manager)
):
    """
    Get crawl results
    
    Returns the crawled and processed content for a completed job.
    """
    try:
        results = await task_manager.get_job_results(job_id, offset, limit)
        
        if results is None:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if not results["completed"]:
            return {
                "message": "Job still in progress",
                "status": results["status"],
                "progress": results["progress"]
            }
        
        return {
            "job_id": job_id,
            "total_results": results["total"],
            "offset": offset,
            "limit": limit,
            "results": results["data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl/batch")
async def create_batch_crawl(
    requests: List[CrawlRequest],
    background_tasks: BackgroundTasks,
    task_manager = Depends(get_task_manager)
):
    """
    Create multiple crawl jobs
    
    Batch endpoint for creating multiple crawl jobs at once.
    """
    try:
        jobs = []
        
        for request in requests:
            job_id = str(uuid.uuid4())
            
            job = CrawlJob(
                job_id=job_id,
                urls=[str(url) for url in request.urls],
                config=request.config or CrawlConfig(),
                collection_name=request.collection_name,
                callback_url=str(request.callback_url) if request.callback_url else None,
                status=CrawlStatus.QUEUED,
                created_at=datetime.utcnow()
            )
            
            await task_manager.queue_crawl_job(job)
            jobs.append({"job_id": job_id, "urls": len(request.urls)})
        
        return {
            "message": f"Created {len(jobs)} crawl jobs",
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"Error creating batch jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))