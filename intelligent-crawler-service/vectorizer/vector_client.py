# vectorizer/vector_client.py
"""
Client for main project's vector service.
Handles communication with the vector API endpoints.
"""
import httpx
from typing import List, Dict, Any, Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorServiceClient:
    """Client for main project's vector service"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'main_project_api_url', 'http://localhost:8000')
        self.api_key = getattr(settings, 'main_project_api_key', 'crawler-api-key')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    async def index_documents(self, documents: List[Dict[str, Any]], collection: str = "crawled_documents") -> Dict[str, Any]:
        """Send documents to main project for vectorization"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/vectors/index",
                    json={
                        "documents": documents,
                        "collection": collection
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during document indexing: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise
    
    async def search(self, query: str, collection: str = "crawled_documents", 
                    limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search through main project's vector store"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request_data = {
                    "query": query,
                    "collection": collection,
                    "limit": limit
                }
                if filters:
                    request_data["filters"] = filters
                
                response = await client.post(
                    f"{self.base_url}/api/v1/vectors/search",
                    json=request_data,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during search: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise
    
    async def create_collection(self, name: str, vector_size: int = 1536, 
                               description: str = "") -> Dict[str, Any]:
        """Create a new collection in the vector store"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/vectors/collections",
                    json={
                        "name": name,
                        "vector_size": vector_size,
                        "description": description
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating collection: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/vectors/collections/{collection_name}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting collection info: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            raise
    
    async def delete_documents(self, collection: str, document_ids: List[str]) -> Dict[str, Any]:
        """Delete specific documents from a collection"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/vectors/documents",
                    params={"collection": collection},
                    json=document_ids,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error deleting documents: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the vector service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/api/v1/vectors/health")
                return response.status_code == 200
        except:
            return False