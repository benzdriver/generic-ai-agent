#!/usr/bin/env python3
"""
View crawled content and summaries
"""

import asyncio
import httpx
import sys
import json
from datetime import datetime


class ContentViewer:
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
    
    async def search_content(self, query: str, collection: str = "default"):
        """Search crawled content"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/v1/search",
                    json={
                        "query": query,
                        "collection": collection,
                        "top_k": 10,
                        "min_score": 0.5
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"❌ Error searching: {e}")
                return None
    
    async def get_job_results(self, job_id: str, limit: int = 10):
        """Get results from a specific crawl job"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/api/v1/crawl/{job_id}/results",
                    params={"limit": limit}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
            except Exception as e:
                print(f"❌ Error getting results: {e}")
                return None
    
    async def list_collections(self):
        """List available collections"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_url}/api/v1/search/collections")
                if response.status_code == 200:
                    return response.json()
                return None
            except:
                return None
    
    def display_search_results(self, results):
        """Display search results in a readable format"""
        if not results or 'results' not in results:
            print("❌ No results found")
            return
        
        print(f"\n🔍 Found {results.get('total', 0)} results")
        print("="*80)
        
        for i, result in enumerate(results['results'], 1):
            print(f"\n📄 Result {i}:")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
            print(f"   Score: {result.get('score', 0):.2f}")
            
            # Show snippet
            snippet = result.get('snippet', result.get('text', ''))
            if snippet:
                # Clean and truncate snippet
                snippet = ' '.join(snippet.split())[:200] + "..."
                print(f"   Snippet: {snippet}")
            
            # Show metadata if available
            metadata = result.get('metadata', {})
            if metadata:
                if 'content_type' in metadata:
                    print(f"   Type: {metadata['content_type']}")
                if 'quality_score' in metadata:
                    print(f"   Quality: {metadata['quality_score']:.2f}")
    
    async def view_recent_crawled_content(self):
        """View recently crawled content from Redis"""
        import redis
        r = redis.from_url("redis://localhost:6379", decode_responses=True)
        
        print("📚 RECENTLY CRAWLED CONTENT")
        print("="*80)
        
        # Get recent completed jobs
        job_keys = r.keys("crawl_job:*")
        completed_jobs = []
        
        for key in job_keys:
            job_data = r.hgetall(key)
            if job_data.get('status') == 'completed' and int(job_data.get('pages_discovered', 0)) > 0:
                completed_jobs.append(job_data)
        
        # Sort by creation time
        completed_jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        for job in completed_jobs[:3]:  # Show last 3 completed jobs
            print(f"\n🗂️  Job: {job['job_id'][:8]}...")
            print(f"   Completed: {job.get('created_at', 'Unknown')}")
            print(f"   Pages found: {job.get('pages_discovered', 0)}")
            
            urls = job.get('urls', '').split(',')
            if urls and urls[0]:
                print(f"   Crawled URLs:")
                for url in urls:
                    print(f"      - {url}")
            
            # Try to get some results from this job
            results = await self.get_job_results(job['job_id'], limit=3)
            if results and 'results' in results:
                print(f"\n   📋 Sample pages from this crawl:")
                for page in results['results'][:3]:
                    print(f"      • {page.get('url', 'N/A')}")
        
        r.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 view_crawled_content.py <command> [args]")
        print("\nCommands:")
        print("  search <query>    - Search crawled content")
        print("  recent            - View recent crawled content")
        print("  job <job_id>      - View content from specific job")
        print("  collections       - List available collections")
        sys.exit(1)
    
    viewer = ContentViewer()
    command = sys.argv[1]
    
    if command == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        print(f"🔎 Searching for: '{query}'")
        results = await viewer.search_content(query)
        viewer.display_search_results(results)
    
    elif command == "recent":
        await viewer.view_recent_crawled_content()
    
    elif command == "job" and len(sys.argv) > 2:
        job_id = sys.argv[2]
        results = await viewer.get_job_results(job_id)
        if results:
            print(f"\n📦 Content from job {job_id}:")
            print(f"Total results: {results.get('total_results', 0)}")
            if 'results' in results:
                for i, page in enumerate(results['results'][:10], 1):
                    print(f"\n{i}. {page.get('url', 'N/A')}")
        else:
            print("❌ No results found for this job")
    
    elif command == "collections":
        collections = await viewer.list_collections()
        if collections:
            print("\n📚 Available Collections:")
            for coll in collections.get('collections', []):
                print(f"   • {coll}")
        else:
            print("❌ Could not retrieve collections")
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())