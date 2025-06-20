#!/usr/bin/env python3
"""
Test CrawlJob model creation
"""

import sys
sys.path.insert(0, '.')

from core.models import CrawlJob, CrawlStatus, CrawlConfig
from datetime import datetime

# Test data similar to what's in Redis
job_data = {
    "job_id": "test-123",
    "urls": ["https://example.com"],
    "status": CrawlStatus.QUEUED,
    "created_at": datetime.utcnow(),
    "progress": 0,
    "urls_crawled": 0,
    "pages_discovered": 0,
    "errors": []
}

# Try without config
try:
    job = CrawlJob(**job_data)
    print("❌ Should have failed without config")
except Exception as e:
    print(f"✅ Expected error without config: {e}")

# Try with config
job_data["config"] = CrawlConfig()
try:
    job = CrawlJob(**job_data)
    print("✅ Success with config")
    print(f"Job ID: {job.job_id}")
    print(f"Collection: {job.collection_name}")
except Exception as e:
    print(f"❌ Unexpected error with config: {e}")