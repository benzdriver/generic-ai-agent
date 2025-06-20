#!/usr/bin/env python3
"""
Check Redis for job data
"""

import asyncio
import redis.asyncio as redis
import sys

async def check_redis():
    # Connect to Redis
    r = redis.from_url("redis://localhost:6379", decode_responses=True)
    
    # Find all crawl job keys
    keys = await r.keys("crawl_job:*")
    print(f"Found {len(keys)} job keys in Redis")
    
    if len(keys) > 0:
        # Check the latest job
        job_key = keys[-1]
        print(f"\nChecking job: {job_key}")
        
        # Get all fields
        job_data = await r.hgetall(job_key)
        print("\nJob data in Redis:")
        for field, value in job_data.items():
            print(f"  {field}: {value}")
    
    await r.close()

if __name__ == "__main__":
    asyncio.run(check_redis())