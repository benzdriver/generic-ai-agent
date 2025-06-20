"""
FastAPI application for vector service API.
Provides vector store operations for the crawler service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.vector_endpoints import router as vector_router
from infrastructure.config.env_manager import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Generic AI Agent Vector API",
    description="Vector store service for crawler integration",
    version="1.0.0"
)

# Configure CORS
config = get_config()
allowed_origins = getattr(config, 'allowed_origins', ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vector_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Generic AI Agent Vector API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )