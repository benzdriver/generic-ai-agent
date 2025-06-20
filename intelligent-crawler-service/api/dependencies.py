"""
FastAPI dependencies
"""

from typing import Optional
import redis.asyncio as redis
import asyncpg
from functools import lru_cache

from core.config import get_settings

settings = get_settings()

# Redis connection
_redis_pool: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.redis_url,
            decode_responses=True
        )
    return _redis_pool

# Database connection
_db_pool: Optional[asyncpg.Pool] = None

async def get_db() -> asyncpg.Pool:
    """Get database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            settings.postgres_url,
            min_size=5,
            max_size=20
        )
    return _db_pool

# Task manager with Redis backend
class TaskManager:
    def __init__(self):
        self.redis = None
    
    async def _get_redis(self):
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def queue_crawl_job(self, job):
        """Queue a crawl job in Redis and Celery"""
        redis_client = await self._get_redis()
        
        # Store job info in Redis
        job_key = f"crawl_job:{job.job_id}"
        job_data = {
            "job_id": job.job_id,
            "urls": ",".join(job.urls),
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "progress": 0,
            "urls_crawled": 0,
            "pages_discovered": 0,
            "errors": "[]"
        }
        
        await redis_client.hset(job_key, mapping=job_data)
        await redis_client.expire(job_key, 86400)  # Expire after 24 hours
        
        # Queue to Celery using send_task to avoid import issues
        from celery import Celery
        celery_app = Celery('tasks', broker=settings.redis_url)
        
        for url in job.urls:
            celery_app.send_task(
                'crawler.crawl_website',
                args=[url, job.job_id, job.config.dict()],
                queue='crawler_tasks'
            )
    
    async def get_job_status(self, job_id):
        """Get job status from Redis"""
        redis_client = await self._get_redis()
        job_key = f"crawl_job:{job_id}"
        
        job_data = await redis_client.hgetall(job_key)
        if not job_data:
            return None
        
        # Convert Redis data to job object
        from core.models import CrawlJob, CrawlStatus, CrawlConfig
        from datetime import datetime
        
        job = CrawlJob(
            job_id=job_data.get("job_id", job_id),
            urls=job_data.get("urls", "").split(",") if job_data.get("urls") else [],
            config=CrawlConfig(),  # Default config for now
            status=CrawlStatus(job_data.get("status", "pending")),
            created_at=datetime.fromisoformat(job_data.get("created_at", datetime.utcnow().isoformat())),
            progress=float(job_data.get("progress", 0)),
            urls_crawled=int(job_data.get("urls_crawled", 0)),
            pages_discovered=int(job_data.get("pages_discovered", 0)),
            errors=[]
        )
        
        return job
    
    async def cancel_job(self, job_id):
        """Cancel a job"""
        redis_client = await self._get_redis()
        job_key = f"crawl_job:{job_id}"
        
        # Check if job exists
        exists = await redis_client.exists(job_key)
        if not exists:
            return False
        
        # Update status to cancelled
        await redis_client.hset(job_key, "status", "cancelled")
        return True
    
    async def get_job_results(self, job_id, offset, limit):
        """Get job results"""
        job = await self.get_job_status(job_id)
        if not job:
            return None
        
        return {
            "completed": job.status == CrawlStatus.COMPLETED,
            "status": job.status.value,
            "progress": job.progress,
            "total": job.pages_discovered,
            "data": []  # Simplified for now
        }
    
    async def initialize(self):
        self.redis = await get_redis()
    
    async def cleanup(self):
        if self.redis:
            await self.redis.close()

_task_manager: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    """Get task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

# Vector store (placeholder)
class VectorStore:
    async def search(self, **kwargs):
        return []
    
    async def list_collections(self):
        return ["default"]

_vector_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    """Get vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store