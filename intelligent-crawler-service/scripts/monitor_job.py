#!/usr/bin/env python3
"""
Monitor crawl job progress and results
"""

import asyncio
import httpx
import sys
import json
from datetime import datetime
import time


class JobMonitor:
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
    
    async def monitor_job(self, job_id: str):
        """Monitor a specific job until completion"""
        print(f"📊 Monitoring job: {job_id}\n")
        
        completed = False
        last_progress = -1
        
        while not completed:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{self.api_url}/api/v1/crawl/{job_id}")
                    if response.status_code == 404:
                        print("❌ Job not found")
                        return
                    
                    data = response.json()
                    status = data.get('status', 'unknown')
                    progress = data.get('progress', 0)
                    urls_crawled = data.get('urls_crawled', 0)
                    urls_total = data.get('urls_total', 0)
                    pages_discovered = data.get('pages_discovered', 0)
                    errors = data.get('errors', [])
                    
                    # Only print if progress changed
                    if progress != last_progress:
                        print(f"\r⏳ Status: {status} | Progress: {progress:.1f}% | URLs: {urls_crawled}/{urls_total} | Pages found: {pages_discovered}", end='', flush=True)
                        last_progress = progress
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        completed = True
                        print(f"\n\n{'✅' if status == 'completed' else '❌'} Job {status}!")
                        
                        if status == 'completed':
                            print(f"\n📈 Final Results:")
                            print(f"   - URLs crawled: {urls_crawled}")
                            print(f"   - Total pages discovered: {pages_discovered}")
                            print(f"   - Average pages per URL: {pages_discovered/urls_crawled:.1f}")
                            
                            if errors:
                                print(f"\n⚠️  Errors encountered: {len(errors)}")
                                for error in errors[:5]:  # Show first 5 errors
                                    print(f"   - {error}")
                        
                        # Get detailed results
                        await self.get_job_results(job_id)
                    
                except Exception as e:
                    print(f"\n❌ Error monitoring job: {e}")
                    return
            
            if not completed:
                await asyncio.sleep(2)
    
    async def get_job_results(self, job_id: str):
        """Get detailed results for a completed job"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_url}/api/v1/crawl/{job_id}/results")
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n📄 Sample crawled pages:")
                    results = data.get('results', [])
                    for i, result in enumerate(results[:10]):  # Show first 10
                        print(f"   {i+1}. {result.get('url', 'N/A')}")
            except:
                pass  # Results endpoint might not be implemented yet
    
    async def list_recent_jobs(self):
        """List recent crawl jobs"""
        # For now, check Redis directly
        import redis
        r = redis.from_url("redis://localhost:6379", decode_responses=True)
        
        print("📋 Recent Crawl Jobs:\n")
        
        keys = r.keys("crawl_job:*")
        jobs = []
        
        for key in keys:
            job_data = r.hgetall(key)
            jobs.append({
                'job_id': job_data.get('job_id'),
                'status': job_data.get('status'),
                'created_at': job_data.get('created_at'),
                'urls_crawled': int(job_data.get('urls_crawled', 0)),
                'pages_discovered': int(job_data.get('pages_discovered', 0)),
                'progress': float(job_data.get('progress', 0))
            })
        
        # Sort by creation time
        jobs.sort(key=lambda x: x['created_at'], reverse=True)
        
        for job in jobs[:10]:  # Show last 10 jobs
            created = datetime.fromisoformat(job['created_at'])
            print(f"ID: {job['job_id']}")
            print(f"   Status: {job['status']} ({job['progress']:.1f}%)")
            print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   URLs crawled: {job['urls_crawled']}")
            print(f"   Pages found: {job['pages_discovered']}")
            print()
        
        r.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 monitor_job.py <command> [args]")
        print("\nCommands:")
        print("  list              - List recent crawl jobs")
        print("  monitor <job_id>  - Monitor a specific job")
        print("  status <job_id>   - Get current status of a job")
        sys.exit(1)
    
    monitor = JobMonitor()
    command = sys.argv[1]
    
    if command == "list":
        await monitor.list_recent_jobs()
    
    elif command == "monitor" and len(sys.argv) > 2:
        job_id = sys.argv[2]
        await monitor.monitor_job(job_id)
    
    elif command == "status" and len(sys.argv) > 2:
        job_id = sys.argv[2]
        # Just check once
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8080/api/v1/crawl/{job_id}")
            if response.status_code == 200:
                data = response.json()
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Job not found or error: {response.status_code}")
    
    else:
        print(f"❌ Unknown command or missing arguments: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())