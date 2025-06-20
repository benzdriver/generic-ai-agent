"""
Crawler Worker Tasks
"""

from celery import Celery
import logging
import asyncio
from typing import Dict, Any

from .intelligent_crawler import IntelligentCrawler
from core.config import get_settings
from core.models import CrawlConfig

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery
app = Celery('crawler.tasks')
app.config_from_object('core.celery_config')

@app.task(name='crawler.crawl_website')
def crawl_website(url: str, job_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crawl a website with intelligent evaluation
    """
    try:
        logger.info(f"Starting crawl for {url} (job: {job_id})")
        
        # Convert config dict to CrawlConfig
        crawl_config = CrawlConfig(**config)
        
        # Create and run crawler
        crawler = IntelligentCrawler(crawl_config)
        
        # Run async crawl in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(crawler.crawl([url]))
            
            # Update job status in Redis
            import redis
            redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            
            job_key = f"crawl_job:{job_id}"
            
            # Get current stats
            current_stats = redis_client.hgetall(job_key)
            urls_crawled = int(current_stats.get("urls_crawled", 0)) + 1
            pages_discovered = int(current_stats.get("pages_discovered", 0)) + len(results)
            
            # Update stats
            updates = {
                "urls_crawled": urls_crawled,
                "pages_discovered": pages_discovered,
                "status": "in_progress"
            }
            
            # Calculate progress
            total_urls = len(current_stats.get("urls", "").split(","))
            progress = (urls_crawled / total_urls) * 100 if total_urls > 0 else 0
            updates["progress"] = progress
            
            # If all URLs crawled, mark as completed
            if urls_crawled >= total_urls:
                updates["status"] = "completed"
            
            redis_client.hset(job_key, mapping=updates)
            
            logger.info(f"Crawl completed for {url}: {len(results)} pages found")
            
            # Send results to AI evaluation and vectorization
            if results:
                for result in results:
                    # Dispatch to AI evaluation queue
                    app.send_task(
                        'ai.evaluate_content',
                        args=[result, job_id],
                        queue='ai_tasks'
                    )
                    
                    # If AI evaluation is not needed immediately, send directly to vectorizer
                    # This is a fallback if AI evaluation is optional
                    if crawl_config.skip_ai_evaluation:
                        app.send_task(
                            'vectorizer.process_crawled_content',
                            args=[result, job_id],
                            queue='vectorizer_tasks'
                        )
            
            return {
                'success': True,
                'url': url,
                'pages_crawled': len(results),
                'job_id': job_id,
                'pages_sent_for_processing': len(results)
            }
            
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error crawling {url}: {e}")
        return {
            'success': False,
            'url': url,
            'error': str(e),
            'job_id': job_id
        }

@app.task(name='crawler.batch_crawl')
def batch_crawl(urls: list, job_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crawl multiple websites
    """
    results = []
    for url in urls:
        result = crawl_website(url, job_id, config)
        results.append(result)
    
    return {
        'success': True,
        'job_id': job_id,
        'total_urls': len(urls),
        'results': results
    }