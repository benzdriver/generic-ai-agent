# Development Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for admin UI, if needed)
- OpenAI/Anthropic API keys

### Local Development Setup

1. **Clone and setup environment**
```bash
cd intelligent-crawler-service
cp .env.example .env
# Edit .env with your API keys
```

2. **Start core services**
```bash
# Start infrastructure services
docker-compose up -d redis postgres qdrant

# Start API in development mode
uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```

3. **Start workers locally**
```bash
# Terminal 1: Crawler worker
celery -A crawler.tasks worker --loglevel=info -Q crawler_tasks

# Terminal 2: AI worker
celery -A ai.tasks worker --loglevel=info -Q ai_tasks

# Terminal 3: Vectorizer worker
celery -A vectorizer.tasks worker --loglevel=info -Q vectorizer_tasks
```

## 🏗️ Architecture Patterns

### 1. Task-Based Architecture
All heavy operations are handled asynchronously through Celery tasks:

```python
# Good: Async task
@app.task(name='crawler.crawl_website')
def crawl_website(url: str, job_id: str, config: Dict):
    # Long-running operation
    pass

# Bad: Blocking API endpoint
@router.post("/crawl")
async def crawl(url: str):
    # Don't do heavy work in API endpoints!
    results = crawl_website_sync(url)  # ❌
```

### 2. Dependency Injection
Use FastAPI's dependency injection for shared resources:

```python
# dependencies.py
async def get_redis() -> redis.Redis:
    return await redis.from_url(settings.redis_url)

# In routers
@router.get("/status")
async def get_status(redis_client = Depends(get_redis)):
    return await redis_client.get("status")
```

### 3. Pydantic Models
All data structures use Pydantic for validation:

```python
class CrawlConfig(BaseModel):
    max_depth: int = Field(default=3, ge=0, le=10)
    max_pages: int = Field(default=100, ge=1, le=10000)
    
    @validator('max_depth')
    def validate_depth(cls, v):
        # Custom validation logic
        return v
```

## 🔧 Common Development Tasks

### Adding a New Crawler Strategy

1. Create strategy file:
```python
# crawler/strategies/news_crawler.py
from .base import BaseCrawlerStrategy

class NewsCrawlerStrategy(BaseCrawlerStrategy):
    def should_crawl(self, url: str) -> bool:
        # News-specific logic
        pass
    
    def extract_content(self, page) -> Dict:
        # News-specific extraction
        pass
```

2. Register in crawler:
```python
# crawler/intelligent_crawler.py
STRATEGIES = {
    'news': NewsCrawlerStrategy(),
    'default': DefaultStrategy()
}
```

### Adding a New AI Evaluator

1. Create evaluator:
```python
# ai/evaluators/technical_evaluator.py
class TechnicalContentEvaluator:
    async def evaluate(self, content: PageContent) -> ContentEvaluation:
        prompt = self._build_prompt(content)
        response = await self.llm.generate(prompt)
        return self._parse_evaluation(response)
```

2. Add to evaluation pipeline:
```python
# ai/evaluator.py
evaluators = [
    GeneralEvaluator(),
    TechnicalEvaluator(),  # New
    QualityEvaluator()
]
```

### Adding a New Search Filter

1. Define filter model:
```python
# api/models/search.py
class SearchFilters(BaseModel):
    content_type: Optional[List[str]]
    date_range: Optional[DateRange]
    quality_score_min: Optional[float]
    # New filter
    language: Optional[List[str]]
```

2. Implement in search:
```python
# api/routers/search.py
def build_qdrant_filter(filters: SearchFilters):
    conditions = []
    if filters.language:
        conditions.append({
            "key": "language",
            "match": {"any": filters.language}
        })
    return Filter(must=conditions)
```

## 🧪 Testing

### Unit Tests
```python
# tests/test_crawler.py
import pytest
from crawler.intelligent_crawler import IntelligentCrawler

@pytest.mark.asyncio
async def test_crawler_respects_depth():
    config = CrawlConfig(max_depth=2)
    crawler = IntelligentCrawler(config)
    results = await crawler.crawl(["https://example.com"])
    
    assert all(r.depth <= 2 for r in results)
```

### Integration Tests
```python
# tests/integration/test_crawl_pipeline.py
@pytest.mark.integration
async def test_full_crawl_pipeline():
    # Start test job
    response = await client.post("/api/v1/crawl", json={
        "urls": ["https://test.example.com"]
    })
    job_id = response.json()["job_id"]
    
    # Wait for completion
    await wait_for_job_completion(job_id)
    
    # Verify results
    results = await get_job_results(job_id)
    assert len(results) > 0
```

### Testing with Docker
```bash
# Run all tests in Docker
make test

# Run specific test
docker-compose run --rm test-runner pytest tests/test_api.py -v
```

## 🐛 Debugging

### 1. Enable Debug Logging
```python
# In .env
LOG_LEVEL=DEBUG

# In code
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### 2. Inspect Celery Tasks
```bash
# Monitor task execution
celery -A crawler.tasks events

# Inspect task queue
celery -A crawler.tasks inspect active

# Flower UI
open http://localhost:5555
```

### 3. Debug Database Issues
```sql
-- Check job status
SELECT job_id, status, created_at, pages_discovered 
FROM crawl_jobs 
ORDER BY created_at DESC 
LIMIT 10;

-- Check crawled pages
SELECT url, content_type, ai_scores
FROM crawled_pages
WHERE job_id = 'your-job-id';
```

### 4. Debug Vector Search
```python
# scripts/debug_vectors.py
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Check collections
collections = client.get_collections()
print(f"Collections: {collections}")

# Search vectors
results = client.search(
    collection_name="default",
    query_vector=[0.1] * 1536,  # Example vector
    limit=5
)
```

## 📁 Code Organization

### File Naming Conventions
```
crawler/
├── __init__.py              # Package initialization
├── intelligent_crawler.py   # Main implementation
├── strategies/             # Strategy pattern implementations
│   ├── __init__.py
│   ├── base.py            # Abstract base class
│   └── default.py         # Default implementation
└── tasks.py               # Celery task definitions
```

### Import Organization
```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from core.config import settings
from core.models import CrawlJob
from .utils import normalize_url
```

## 🔒 Security Best Practices

### 1. API Key Management
```python
# Never hardcode keys
API_KEY = "sk-123..."  # ❌

# Use environment variables
API_KEY = os.getenv("OPENAI_API_KEY")  # ✅

# Or use settings
from core.config import settings
API_KEY = settings.openai_api_key  # ✅
```

### 2. Input Validation
```python
# Always validate URLs
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
```

### 3. Rate Limiting
```python
# Implement rate limiting for API endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/crawl")
@limiter.limit("10/minute")
async def create_crawl_job(request: Request):
    pass
```

## 🚀 Performance Optimization

### 1. Batch Processing
```python
# Good: Batch operations
async def vectorize_batch(texts: List[str]):
    embeddings = await openai.embeddings.create(
        input=texts,  # Batch of texts
        model="text-embedding-3-small"
    )

# Bad: Individual operations
for text in texts:
    embedding = await openai.embeddings.create(input=text)  # ❌
```

### 2. Connection Pooling
```python
# PostgreSQL connection pool
async def get_db_pool():
    return await asyncpg.create_pool(
        settings.postgres_url,
        min_size=5,
        max_size=20
    )

# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50
)
```

### 3. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_computation(url: str) -> float:
    # Cached computation
    return calculate_url_score(url)
```

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Playwright Documentation](https://playwright.dev/python/)

### Tools
- **httpie** - API testing: `http POST localhost:8080/api/v1/crawl urls:='["https://example.com"]'`
- **pgcli** - PostgreSQL CLI with autocomplete
- **redis-cli** - Redis debugging
- **docker stats** - Monitor container resources

### Monitoring
- Flower: http://localhost:5555
- Qdrant UI: http://localhost:6333/dashboard
- API Docs: http://localhost:8080/docs

---

*Last Updated: 2025-06-19*
*Version: 1.0.0*