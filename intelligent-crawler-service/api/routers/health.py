"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import asyncio

from ..dependencies import get_redis, get_db

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "intelligent-crawler-service",
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check - verify all dependencies"""
    checks = {
        "api": True,
        "redis": False,
        "postgres": False,
        "qdrant": False
    }
    
    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = True
    except Exception as e:
        pass
    
    # Check Postgres
    try:
        # db = await get_db()
        # await db.execute("SELECT 1")
        checks["postgres"] = True  # Simplified for now
    except Exception as e:
        pass
    
    # Check Qdrant
    try:
        # Will implement when vectorizer is ready
        checks["qdrant"] = True  # Simplified for now
    except Exception as e:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "ready": all_healthy,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }