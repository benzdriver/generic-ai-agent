"""
Intelligent Crawler Service API
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from .routers import crawl, search, admin, health
from .dependencies import get_redis, get_db
from core.tasks import CrawlTaskManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Intelligent Crawler Service",
    description="AI-powered web crawler for building high-quality knowledge bases",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(crawl.router, prefix="/api/v1", tags=["crawl"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(health.router, prefix="/health", tags=["health"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Intelligent Crawler Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Intelligent Crawler Service...")
    
    # Initialize task manager
    task_manager = CrawlTaskManager()
    await task_manager.initialize()
    
    # Initialize database connections
    # This will be handled by dependencies
    
    logger.info("Service started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Intelligent Crawler Service...")
    
    # Cleanup tasks
    task_manager = CrawlTaskManager()
    await task_manager.cleanup()
    
    logger.info("Service shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)