#!/usr/bin/env python3
"""
Crawler Dashboard - View detailed crawler statistics and progress
"""

import redis
import json
from datetime import datetime
from collections import defaultdict
import sys


class CrawlerDashboard:
    def __init__(self):
        self.redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    
    def show_dashboard(self):
        """Display comprehensive crawler statistics"""
        print("="*80)
        print("🕷️  INTELLIGENT CRAWLER DASHBOARD")
        print("="*80)
        
        # Get all jobs
        job_keys = self.redis_client.keys("crawl_job:*")
        
        if not job_keys:
            print("\n❌ No crawl jobs found")
            return
        
        jobs = []
        for key in job_keys:
            job_data = self.redis_client.hgetall(key)
            jobs.append(job_data)
        
        # Sort by creation time
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Overall statistics
        total_jobs = len(jobs)
        completed_jobs = sum(1 for j in jobs if j.get('status') == 'completed')
        in_progress_jobs = sum(1 for j in jobs if j.get('status') == 'in_progress')
        queued_jobs = sum(1 for j in jobs if j.get('status') == 'queued')
        failed_jobs = sum(1 for j in jobs if j.get('status') == 'failed')
        
        total_pages = sum(int(j.get('pages_discovered', 0)) for j in jobs)
        total_urls = sum(int(j.get('urls_crawled', 0)) for j in jobs)
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"   Total Jobs: {total_jobs}")
        print(f"   ✅ Completed: {completed_jobs}")
        print(f"   🔄 In Progress: {in_progress_jobs}")
        print(f"   ⏳ Queued: {queued_jobs}")
        print(f"   ❌ Failed: {failed_jobs}")
        print(f"\n   📄 Total Pages Crawled: {total_pages:,}")
        print(f"   🔗 Total URLs Processed: {total_urls}")
        if total_urls > 0:
            print(f"   📈 Avg Pages per URL: {total_pages/total_urls:.1f}")
        
        # Recent jobs
        print(f"\n📋 RECENT JOBS (Last 5)")
        print("-"*80)
        
        for job in jobs[:5]:
            self._display_job(job)
        
        # Domain statistics
        print(f"\n🌐 CRAWLED DOMAINS")
        print("-"*80)
        domain_stats = defaultdict(int)
        
        for job in jobs:
            urls = job.get('urls', '').split(',')
            for url in urls:
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        domain_stats[domain] += 1
                    except:
                        pass
        
        for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {domain}: {count} crawls")
    
    def _display_job(self, job):
        """Display a single job's information"""
        job_id = job.get('job_id', 'Unknown')
        status = job.get('status', 'unknown')
        created = job.get('created_at', '')
        urls_crawled = int(job.get('urls_crawled', 0))
        pages_discovered = int(job.get('pages_discovered', 0))
        progress = float(job.get('progress', 0))
        
        # Status emoji
        status_emoji = {
            'completed': '✅',
            'in_progress': '🔄',
            'queued': '⏳',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(status, '❓')
        
        print(f"\n{status_emoji} Job ID: {job_id[:8]}...")
        print(f"   Status: {status} ({progress:.1f}%)")
        
        if created:
            created_dt = datetime.fromisoformat(created)
            print(f"   Created: {created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"   URLs Crawled: {urls_crawled}")
        print(f"   Pages Discovered: {pages_discovered:,}")
        
        # Show URLs for this job
        urls = job.get('urls', '').split(',')
        if urls and urls[0]:
            print(f"   Target URLs:")
            for url in urls[:3]:  # Show first 3
                print(f"      - {url[:80]}...")
    
    def show_active_workers(self):
        """Show active crawler workers"""
        print("\n👷 ACTIVE WORKERS")
        print("-"*80)
        
        # This would normally check Celery for active workers
        # For now, we'll check Docker
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=crawler-worker", "--format", "table {{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True
            )
            print(result.stdout)
        except:
            print("   Unable to check worker status")
    
    def close(self):
        """Close connections"""
        self.redis_client.close()


def main():
    dashboard = CrawlerDashboard()
    
    try:
        dashboard.show_dashboard()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--workers":
            dashboard.show_active_workers()
            
    finally:
        dashboard.close()


if __name__ == "__main__":
    main()