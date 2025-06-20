"""
Vectorizer Worker Tasks
"""

from celery import Celery
import logging
from typing import Dict, Any, List
import asyncio
from datetime import datetime
import redis
import json

from core.config import get_settings
from .vector_client import VectorServiceClient

logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery('vectorizer_tasks')
app.config_from_object('core.celery_config')

# Get settings
settings = get_settings()

# Initialize Redis client
redis_client = redis.from_url(settings.redis_url)

def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.task(name='vectorizer.process_crawled_content')
def process_crawled_content(content: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Process and vectorize crawled content
    """
    try:
        # Initialize vector client
        client = VectorServiceClient()
        
        # Prepare document for vectorization
        document = {
            "id": content.get("id", f"{job_id}_{content['url']}"),
            "url": content["url"],
            "title": content.get("title", ""),
            "content": content.get("text", ""),
            "metadata": {
                "crawled_at": content.get("crawled_at", datetime.utcnow().isoformat()),
                "content_type": content.get("content_type", "text/html"),
                "quality_score": content.get("ai_scores", {}).get("overall_score", 0.0),
                "job_id": job_id,
                "domain": content.get("domain", ""),
                "depth": content.get("depth", 0)
            }
        }
        
        # Send to main project for vectorization
        result = run_async(client.index_documents([document]))
        
        # Update job status
        update_job_vectorization_status(job_id, result)
        
        logger.info(f"Vectorized content for {content['url']}")
        
        return {
            'success': result.get('status') != 'failed',
            'document_id': document['id'],
            'url': content['url'],
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Error vectorizing content: {e}")
        return {
            'success': False,
            'error': str(e),
            'url': content.get('url', 'unknown')
        }

@app.task(name='vectorizer.batch_process_content')
def batch_process_content(contents: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Process multiple crawled contents
    """
    try:
        # Initialize vector client
        client = VectorServiceClient()
        
        # Prepare documents
        documents = []
        for content in contents:
            document = {
                "id": content.get("id", f"{job_id}_{content['url']}"),
                "url": content["url"],
                "title": content.get("title", ""),
                "content": content.get("text", ""),
                "metadata": {
                    "crawled_at": content.get("crawled_at", datetime.utcnow().isoformat()),
                    "content_type": content.get("content_type", "text/html"),
                    "quality_score": content.get("ai_scores", {}).get("overall_score", 0.0),
                    "job_id": job_id,
                    "domain": content.get("domain", ""),
                    "depth": content.get("depth", 0)
                }
            }
            documents.append(document)
        
        # Process in batches
        batch_size = 50
        total_success = 0
        failed_urls = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            try:
                result = run_async(client.index_documents(batch))
                total_success += result.get('count', 0)
                failed_urls.extend(result.get('failed', []))
            except Exception as e:
                logger.error(f"Batch vectorization failed: {e}")
                failed_urls.extend([doc['id'] for doc in batch])
        
        # Update job status
        update_job_vectorization_status(job_id, {
            'total_processed': len(documents),
            'success_count': total_success,
            'failed_count': len(failed_urls)
        })
        
        return {
            'success': True,
            'total_processed': len(documents),
            'success_count': total_success,
            'failed_urls': failed_urls
        }
        
    except Exception as e:
        logger.error(f"Error in batch vectorization: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.task(name='vectorizer.create_collection')
def create_collection(collection_name: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new vector collection
    """
    try:
        client = VectorServiceClient()
        
        result = run_async(client.create_collection(
            name=collection_name,
            vector_size=1536,
            description=description
        ))
        
        logger.info(f"Collection creation result: {result}")
        
        return {
            'success': True,
            'collection': collection_name,
            'created': result.get('created', False),
            'status': result.get('status', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.task(name='vectorizer.search_content')
def search_content(query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Search vectorized content
    """
    try:
        client = VectorServiceClient()
        
        result = run_async(client.search(
            query=query,
            collection="crawled_documents",
            limit=20,
            filters=filters
        ))
        
        return {
            'success': True,
            'query': query,
            'results': result.get('results', []),
            'total': result.get('total', 0)
        }
        
    except Exception as e:
        logger.error(f"Error searching content: {e}")
        return {
            'success': False,
            'error': str(e),
            'query': query
        }

@app.task(name='vectorizer.delete_job_vectors')
def delete_job_vectors(job_id: str) -> Dict[str, Any]:
    """
    Delete all vectors associated with a job
    """
    try:
        client = VectorServiceClient()
        
        # First search for all documents with this job_id
        search_result = run_async(client.search(
            query="*",  # We'll filter by metadata
            filters={"job_id": job_id},
            limit=1000  # Adjust as needed
        ))
        
        document_ids = [r['id'] for r in search_result.get('results', [])]
        
        if document_ids:
            # Delete the documents
            delete_result = run_async(client.delete_documents(
                collection="crawled_documents",
                document_ids=document_ids
            ))
            
            logger.info(f"Deleted {len(document_ids)} vectors for job {job_id}")
            
            return {
                'success': True,
                'deleted_count': len(document_ids),
                'job_id': job_id
            }
        else:
            return {
                'success': True,
                'deleted_count': 0,
                'job_id': job_id,
                'message': 'No vectors found for this job'
            }
        
    except Exception as e:
        logger.error(f"Error deleting job vectors: {e}")
        return {
            'success': False,
            'error': str(e),
            'job_id': job_id
        }

def update_job_vectorization_status(job_id: str, status_data: Dict[str, Any]):
    """Update job vectorization status in Redis"""
    try:
        key = f"job:{job_id}:vectorization"
        redis_client.setex(
            key,
            86400,  # 24 hours TTL
            json.dumps({
                'updated_at': datetime.utcnow().isoformat(),
                **status_data
            })
        )
    except Exception as e:
        logger.error(f"Failed to update vectorization status: {e}")

# Startup task to ensure collection exists
@app.task(name='vectorizer.ensure_collection')
def ensure_collection() -> Dict[str, Any]:
    """
    Ensure the crawled_documents collection exists
    """
    try:
        client = VectorServiceClient()
        
        # Check if collection exists
        try:
            info = run_async(client.get_collection_info("crawled_documents"))
            return {
                'success': True,
                'collection_exists': True,
                'info': info
            }
        except:
            # Collection doesn't exist, create it
            result = create_collection(
                "crawled_documents",
                "Web pages crawled by crawler service"
            )
            return result
            
    except Exception as e:
        logger.error(f"Error ensuring collection: {e}")
        return {
            'success': False,
            'error': str(e)
        }