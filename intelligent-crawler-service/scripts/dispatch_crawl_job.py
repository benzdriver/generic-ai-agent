#!/usr/bin/env python3
"""
Script to dispatch crawl jobs for testing
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import List, Dict, Any


class CrawlDispatcher:
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        
    async def dispatch_crawl(self, urls: List[str], config: Dict[str, Any] = None) -> Dict:
        """Dispatch a crawl job to the API"""
        if config is None:
            config = {
                "max_depth": 2,
                "max_pages": 50,
                "ai_evaluation": True,
                "min_quality_score": 0.5,
                "allowed_domains": [],
                "excluded_patterns": []
            }
        
        payload = {
            "urls": urls,
            "config": config
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/v1/crawl",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                print(f"❌ Failed to connect to API at {self.api_url}")
                print("Make sure the crawler service is running: make dev")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error dispatching crawl job: {e}")
                sys.exit(1)
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get the status of a crawl job"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/crawl/{job_id}"
            )
            response.raise_for_status()
            return response.json()
    
    async def test_dispatch(self):
        """Test dispatch with sample websites"""
        test_urls = [
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada.html"
        ]
        
        print("🚀 Dispatching test crawl job...")
        print(f"URLs to crawl: {json.dumps(test_urls, indent=2)}")
        
        result = await self.dispatch_crawl(test_urls)
        
        print(f"\n✅ Job dispatched successfully!")
        print(f"Job ID: {result['job_id']}")
        print(f"Status: {result['status']}")
        print(f"Created: {result['created_at']}")
        
        # Monitor job status
        print("\n📊 Monitoring job status...")
        job_id = result['job_id']
        
        for i in range(10):  # Check status for up to 50 seconds
            await asyncio.sleep(5)
            status = await self.get_job_status(job_id)
            print(f"Status check {i+1}: {status.get('status', 'unknown')}")
            
            if status.get('status') in ['completed', 'failed']:
                print(f"\n🏁 Job {status['status']}!")
                if status.get('results'):
                    print(f"Pages crawled: {len(status['results'])}")
                break
        
        return result


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dispatch_crawl_job.py <command> [args]")
        print("\nCommands:")
        print("  test_dispatch    - Run a test crawl job")
        print("  crawl <url>      - Crawl a specific URL")
        print("  status <job_id>  - Check status of a job")
        sys.exit(1)
    
    dispatcher = CrawlDispatcher()
    command = sys.argv[1]
    
    if command == "test_dispatch":
        await dispatcher.test_dispatch()
    
    elif command == "crawl" and len(sys.argv) > 2:
        url = sys.argv[2]
        result = await dispatcher.dispatch_crawl([url])
        print(f"✅ Job dispatched: {result['job_id']}")
    
    elif command == "status" and len(sys.argv) > 2:
        job_id = sys.argv[2]
        status = await dispatcher.get_job_status(job_id)
        print(json.dumps(status, indent=2))
    
    else:
        print(f"❌ Unknown command or missing arguments: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())