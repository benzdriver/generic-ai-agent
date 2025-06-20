# Vector Database Integration Strategy

## 🎯 Integration Approach

Based on the existing vector store implementation in the main project, we have three options:

### Option 1: Shared Vector Store Service (Recommended) ✅
Use the main project's vector store implementation as a **shared service** that both systems can access.

**Advantages:**
- No code duplication
- Centralized vector database management
- Single source of truth for embeddings
- Easier maintenance and updates

**Implementation:**
1. Keep vector store in main project
2. Crawler service sends vectorization requests to main project
3. Main project handles all vector operations

### Option 2: Extract to Shared Library
Extract vector store code into a separate package that both projects can use.

**Advantages:**
- Code reuse without service dependencies
- Each service can scale independently
- Version control for the shared library

**Implementation:**
1. Create `generic-ai-vector-store` package
2. Both projects install it as dependency
3. Each service has its own vector store instance

### Option 3: Duplicate Implementation (Not Recommended) ❌
Copy the vector store implementation to crawler service.

**Disadvantages:**
- Code duplication
- Maintenance overhead
- Potential divergence of implementations

## 📋 Recommended Implementation Plan

### Phase 1: API-Based Integration

1. **Create Vector Service Endpoints in Main Project**

```python
# In main project: src/app/api/vector_endpoints.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from infrastructure.vector_store import QdrantVectorStore

router = APIRouter(prefix="/api/v1/vectors")

@router.post("/index")
async def index_documents(request: IndexRequest):
    """Index documents from crawler service"""
    vector_store = QdrantVectorStore()
    # Process and store vectors
    return {"status": "indexed", "count": len(request.documents)}

@router.post("/search")
async def search_vectors(request: SearchRequest):
    """Search vectors for crawler service"""
    vector_store = QdrantVectorStore()
    results = vector_store.search(...)
    return {"results": results}

@router.post("/collections")
async def create_collection(request: CollectionRequest):
    """Create new collection for crawler"""
    vector_store = QdrantVectorStore()
    vector_store.create_collection(...)
    return {"status": "created"}
```

2. **Update Crawler Service to Use Main Project's Vector API**

```python
# In crawler service: vectorizer/vector_client.py
import httpx
from typing import List, Dict, Any
from core.config import settings

class VectorServiceClient:
    """Client for main project's vector service"""
    
    def __init__(self):
        self.base_url = settings.main_project_api_url
        self.api_key = settings.main_project_api_key
    
    async def index_documents(self, documents: List[Dict[str, Any]]):
        """Send documents to main project for vectorization"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/vectors/index",
                json={"documents": documents},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
    
    async def search(self, query: str, collection: str = "documents"):
        """Search through main project's vector store"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/vectors/search",
                json={"query": query, "collection": collection}
            )
            return response.json()
```

3. **Update Crawler's Vectorizer Tasks**

```python
# In crawler service: vectorizer/tasks.py
from celery import Celery
from .vector_client import VectorServiceClient
from typing import List, Dict, Any

app = Celery('vectorizer')

@app.task(name='vectorizer.process_crawled_content')
async def process_crawled_content(content: Dict[str, Any]):
    """Process and vectorize crawled content"""
    
    # Prepare document for vectorization
    document = {
        "id": content["id"],
        "url": content["url"],
        "title": content["title"],
        "content": content["text"],
        "metadata": {
            "crawled_at": content["crawled_at"],
            "content_type": content["content_type"],
            "quality_score": content["quality_score"]
        }
    }
    
    # Send to main project for vectorization
    client = VectorServiceClient()
    result = await client.index_documents([document])
    
    return result
```

### Phase 2: Collection Management

1. **Define Collection Strategy**

```yaml
# config/collections.yaml
collections:
  # Main project collections (existing)
  canonical_queries:
    description: "Canonical Q&A pairs"
    vector_size: 1536
    
  conversations:
    description: "User conversation history"
    vector_size: 1536
    
  # Crawler-specific collections (new)
  crawled_documents:
    description: "Web pages crawled by crawler service"
    vector_size: 1536
    indexes:
      - field: "url"
        type: "keyword"
      - field: "domain"
        type: "keyword"
      - field: "crawled_at"
        type: "datetime"
      
  page_summaries:
    description: "AI-generated page summaries"
    vector_size: 1536
    indexes:
      - field: "original_url"
        type: "keyword"
```

2. **Implement Collection Initialization**

```python
# In main project: scripts/initialize_crawler_collections.py
from infrastructure.vector_store import QdrantVectorStore
from qdrant_client import models

def initialize_crawler_collections():
    vector_store = QdrantVectorStore()
    
    # Crawled documents collection
    if not vector_store.collection_exists("crawled_documents"):
        vector_store.create_collection(
            "crawled_documents",
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE
            )
        )
        
        # Create indexes
        vector_store.create_payload_index(
            "crawled_documents",
            "url",
            models.PayloadSchemaType.KEYWORD
        )
        
        vector_store.create_payload_index(
            "crawled_documents",
            "domain",
            models.PayloadSchemaType.KEYWORD
        )
```

### Phase 3: Search Integration

1. **Unified Search Across Collections**

```python
# In main project: src/app/search/unified_search.py
class UnifiedSearcher:
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embedder = EmbeddingRouter()
    
    async def search(self, query: str, include_collections: List[str] = None):
        """Search across multiple collections"""
        
        # Generate query embedding
        query_vector = await self.embedder.embed(query)
        
        # Default collections
        if not include_collections:
            include_collections = [
                "canonical_queries",
                "crawled_documents",
                "documents"
            ]
        
        results = {}
        for collection in include_collections:
            if self.vector_store.collection_exists(collection):
                collection_results = self.vector_store.search(
                    collection,
                    query_vector,
                    limit=10
                )
                results[collection] = collection_results
        
        # Merge and rank results
        return self._merge_results(results)
```

## 🔄 Data Flow Architecture

```
Crawler Service                    Main Project
     │                                  │
     ├─[Crawl Pages]                   │
     │                                  │
     ├─[Extract Content]               │
     │                                  │
     ├─[Send to Vector API]───────────>├─[Receive Documents]
     │                                  │
     │                                  ├─[Generate Embeddings]
     │                                  │
     │                                  ├─[Store in Qdrant]
     │                                  │
     ├─[Request Search]────────────────>├─[Vector Search]
     │                                  │
     ├<────────[Search Results]─────────┤
     │                                  │
```

## 🚀 Implementation Steps

1. **Week 1: API Development** ✅
   - [x] Create vector service endpoints in main project
   - [x] Add authentication for crawler service
   - [ ] Implement rate limiting
   - [x] Add API documentation

2. **Week 2: Crawler Integration** ✅
   - [x] Create VectorServiceClient in crawler
   - [x] Update vectorizer tasks
   - [x] Test end-to-end flow
   - [x] Handle error cases

3. **Week 3: Collection Management** ✅
   - [x] Define crawler-specific collections
   - [x] Create initialization scripts
   - [x] Implement collection lifecycle management
   - [ ] Add monitoring

4. **Week 4: Search Enhancement**
   - [ ] Implement unified search
   - [ ] Add search filters for crawled content
   - [ ] Create search analytics
   - [ ] Performance optimization

## 🔐 Security Considerations

1. **API Authentication**
   ```python
   # Use API keys or JWT tokens
   headers = {
       "Authorization": f"Bearer {api_key}",
       "X-Service": "crawler"
   }
   ```

2. **Rate Limiting**
   ```python
   # Implement rate limits per service
   @limiter.limit("1000/hour", key_func=get_service_id)
   ```

3. **Data Isolation**
   - Use collection-level permissions
   - Separate API keys per service
   - Audit logging for all operations

## 📊 Benefits of This Approach

1. **No Code Duplication**: Reuse existing, tested vector store implementation
2. **Centralized Management**: Single point for vector database operations
3. **Scalability**: Can scale vector service independently
4. **Consistency**: Same embedding model and configurations
5. **Maintenance**: Updates in one place benefit all services

## 🔧 Configuration

Add to crawler's `.env`:
```env
# Main Project API
MAIN_PROJECT_API_URL=http://main-project:8000
MAIN_PROJECT_API_KEY=your-secure-api-key

# Vector Service Settings
VECTOR_BATCH_SIZE=100
VECTOR_TIMEOUT=30
```

Add to main project's `.env`:
```env
# Crawler Service Access
CRAWLER_API_KEY=crawler-secure-key
CRAWLER_RATE_LIMIT=1000/hour
```

## 📈 Monitoring

1. **Metrics to Track**
   - Vectorization throughput
   - Search latency
   - API request rates
   - Error rates

2. **Dashboards**
   - Grafana dashboard for vector operations
   - Alerts for service degradation
   - Collection size monitoring

---

This integration approach maximizes code reuse while maintaining clean service boundaries. The crawler service focuses on crawling and content extraction, while the main project handles all vector database operations.

*Last Updated: 2025-06-19*