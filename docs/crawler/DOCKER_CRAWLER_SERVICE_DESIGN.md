# 🐳 智能爬虫向量化服务设计

## 📋 概述

设计一个独立的Docker服务，提供"URL列表 → 智能爬取 → 向量数据库"的完整pipeline。

## 🔍 现有开源方案分析

### 1. **Firecrawl** ⭐⭐⭐⭐⭐
- **GitHub**: https://github.com/mendableai/firecrawl
- **特点**: 
  - 专为LLM设计的爬虫
  - 自动处理JS渲染
  - 输出Markdown格式
  - 提供API和SDK
- **缺点**: 不包含向量化和知识库管理

### 2. **Crawlee** ⭐⭐⭐⭐
- **GitHub**: https://github.com/apify/crawlee
- **特点**:
  - 支持Playwright/Puppeteer
  - 自动重试和错误处理
  - 分布式爬取
- **缺点**: 需要自己实现向量化

### 3. **LlamaIndex Web Reader** ⭐⭐⭐
- **GitHub**: https://github.com/run-llama/llama_index
- **特点**:
  - 集成向量存储
  - 支持多种数据源
  - LLM友好
- **缺点**: 爬虫功能较简单

### 4. **Embedbase** ⭐⭐⭐
- **GitHub**: https://github.com/different-ai/embedbase
- **特点**:
  - 专注于向量化存储
  - 支持多种嵌入模型
  - REST API
- **缺点**: 爬虫功能有限

### 5. **Danswer** ⭐⭐⭐⭐
- **GitHub**: https://github.com/danswer-ai/danswer
- **特点**:
  - 企业级知识库
  - 支持多数据源
  - 包含问答系统
- **缺点**: 较重，不够灵活

## 🏗️ 推荐架构：组合方案

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 1. 智能爬虫服务（基于Firecrawl改造）
  smart-crawler:
    build: ./smart-crawler
    environment:
      - CRAWLER_MODE=intelligent
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "3001:3001"
    depends_on:
      - redis
      - postgres

  # 2. 向量化服务
  vectorizer:
    build: ./vectorizer
    environment:
      - EMBEDDING_MODEL=text-embedding-3-small
      - BATCH_SIZE=100
    depends_on:
      - qdrant

  # 3. 向量数据库
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

  # 4. 任务队列
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # 5. 元数据存储
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=crawler_db
      - POSTGRES_USER=crawler
      - POSTGRES_PASSWORD=secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # 6. API网关
  api-gateway:
    build: ./api-gateway
    ports:
      - "8080:8080"
    depends_on:
      - smart-crawler
      - vectorizer

volumes:
  qdrant_storage:
  postgres_data:
```

## 🔧 服务设计

### 1. **核心API设计**

```python
# api_gateway/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict

app = FastAPI(title="Intelligent Crawler Service")

class CrawlRequest(BaseModel):
    urls: List[str]
    config: Optional[Dict] = {
        "max_depth": 3,
        "smart_extraction": True,
        "extract_tables": True,
        "handle_pdfs": True,
        "language": "en"
    }
    vector_config: Optional[Dict] = {
        "collection_name": "default",
        "embedding_model": "text-embedding-3-small",
        "chunk_size": 1000,
        "chunk_overlap": 200
    }

class CrawlJob(BaseModel):
    job_id: str
    status: str
    progress: float
    results_preview: Optional[List[Dict]]

@app.post("/crawl", response_model=CrawlJob)
async def create_crawl_job(request: CrawlRequest, background_tasks: BackgroundTasks):
    """创建爬取任务"""
    job_id = generate_job_id()
    
    # 异步执行爬取
    background_tasks.add_task(
        crawl_and_vectorize,
        job_id=job_id,
        urls=request.urls,
        config=request.config,
        vector_config=request.vector_config
    )
    
    return CrawlJob(
        job_id=job_id,
        status="queued",
        progress=0.0
    )

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """获取任务状态"""
    return get_job_details(job_id)

@app.post("/search")
async def search_knowledge(query: str, collection: str = "default"):
    """搜索知识库"""
    results = await vector_search(query, collection)
    return results

@app.post("/update/{collection}")
async def incremental_update(collection: str):
    """触发增量更新"""
    return await trigger_incremental_update(collection)
```

### 2. **智能爬虫服务**

```python
# smart_crawler/crawler.py
class IntelligentCrawlerService:
    """基于Firecrawl改造的智能爬虫"""
    
    def __init__(self):
        self.llm = self._init_llm()
        self.browser_pool = BrowserPool(size=10)
        
    async def crawl_urls(self, urls: List[str], config: Dict) -> List[Dict]:
        """智能爬取URL列表"""
        
        results = []
        
        for url in urls:
            # 1. 智能判断页面价值
            if config.get('smart_extraction'):
                page_value = await self._assess_page_value(url)
                if page_value < config.get('min_value', 0.5):
                    continue
            
            # 2. 爬取内容
            content = await self._crawl_page(url, config)
            
            # 3. 智能提取
            if config.get('extract_tables'):
                content['tables'] = await self._extract_tables(content['html'])
                
            if config.get('handle_pdfs') and content.get('pdf_links'):
                content['pdfs'] = await self._process_pdfs(content['pdf_links'])
            
            # 4. 生成结构化输出
            structured = await self._structure_content(content)
            
            results.append({
                'url': url,
                'title': content['title'],
                'markdown': content['markdown'],
                'structured_data': structured,
                'metadata': {
                    'crawled_at': datetime.now(),
                    'page_value': page_value,
                    'extraction_config': config
                }
            })
            
        return results
    
    async def _assess_page_value(self, url: str) -> float:
        """AI评估页面价值"""
        # 快速预览页面
        preview = await self._quick_preview(url)
        
        assessment = await self.llm.assess(f"""
        Evaluate this page's value for knowledge extraction:
        URL: {url}
        Title: {preview['title']}
        Preview: {preview['text'][:500]}
        
        Return a score 0-1.
        """)
        
        return assessment['score']
```

### 3. **向量化服务**

```python
# vectorizer/service.py
class VectorizerService:
    """文档向量化服务"""
    
    def __init__(self):
        self.embedder = EmbeddingModel()
        self.chunker = TextChunker()
        self.vector_store = QdrantClient()
        
    async def vectorize_documents(self, documents: List[Dict], config: Dict):
        """向量化文档"""
        
        collection = config['collection_name']
        
        # 确保集合存在
        await self._ensure_collection(collection)
        
        all_chunks = []
        
        for doc in documents:
            # 1. 智能分块
            chunks = self.chunker.chunk(
                text=doc['markdown'],
                chunk_size=config['chunk_size'],
                overlap=config['chunk_overlap'],
                preserve_structure=True  # 保持段落/章节结构
            )
            
            # 2. 为每个块添加元数据
            for chunk in chunks:
                chunk['metadata'] = {
                    'source_url': doc['url'],
                    'title': doc['title'],
                    'chunk_index': chunk['index'],
                    'total_chunks': len(chunks),
                    **doc.get('structured_data', {})
                }
                all_chunks.append(chunk)
        
        # 3. 批量向量化
        embeddings = await self._batch_embed(
            [chunk['text'] for chunk in all_chunks]
        )
        
        # 4. 存储到向量数据库
        await self._store_vectors(collection, all_chunks, embeddings)
        
        return {
            'collection': collection,
            'documents_processed': len(documents),
            'chunks_created': len(all_chunks)
        }
```

### 4. **增量更新服务**

```python
# updater/service.py
class IncrementalUpdateService:
    """增量更新服务"""
    
    def __init__(self):
        self.change_detector = ChangeDetector()
        self.scheduler = UpdateScheduler()
        
    async def setup_monitoring(self, collection: str):
        """设置监控"""
        
        # 获取集合中的所有URL
        urls = await self._get_collection_urls(collection)
        
        # 创建监控任务
        for url in urls:
            await self.scheduler.schedule_monitoring(
                url=url,
                frequency=self._determine_frequency(url),
                callback=self._handle_change
            )
    
    async def _handle_change(self, url: str, change_type: str):
        """处理检测到的变化"""
        
        if change_type == 'content_update':
            # 重新爬取和向量化
            await self._update_document(url)
            
        elif change_type == 'page_removed':
            # 从向量库删除
            await self._remove_document(url)
```

## 🚀 使用示例

### 1. **基础使用**

```python
import requests

# 创建爬取任务
response = requests.post('http://localhost:8080/crawl', json={
    'urls': [
        'https://example.com/docs',
        'https://example.com/guides'
    ],
    'config': {
        'max_depth': 2,
        'smart_extraction': True
    },
    'vector_config': {
        'collection_name': 'my_knowledge_base'
    }
})

job = response.json()
print(f"Job created: {job['job_id']}")

# 检查状态
status = requests.get(f'http://localhost:8080/job/{job["job_id"]}').json()
print(f"Progress: {status['progress']}%")

# 搜索知识库
results = requests.post('http://localhost:8080/search', json={
    'query': 'How to get started?',
    'collection': 'my_knowledge_base'
}).json()
```

### 2. **SDK使用**

```python
from intelligent_crawler import CrawlerClient

client = CrawlerClient('http://localhost:8080')

# 爬取并向量化
job = client.crawl(
    urls=['https://docs.example.com'],
    max_depth=3,
    collection='docs'
)

# 等待完成
job.wait_until_complete()

# 搜索
results = client.search('installation guide', collection='docs')
```

## 🔧 配置选项

```yaml
# config.yaml
crawler:
  concurrent_requests: 10
  timeout: 30
  user_agent: "IntelligentCrawler/1.0"
  respect_robots: true
  
extraction:
  use_ai: true
  extract_tables: true
  extract_images: false
  handle_pdfs: true
  pdf_max_size: 10MB
  
vectorization:
  model: "text-embedding-3-small"
  chunk_size: 1000
  chunk_overlap: 200
  batch_size: 100
  
storage:
  vector_db: "qdrant"
  metadata_db: "postgres"
  cache: "redis"
  
monitoring:
  enable_incremental: true
  check_frequency: "1h"
  change_threshold: 0.05
```

## 🎯 优势

1. **模块化设计**: 每个组件独立，易于扩展
2. **智能化**: AI驱动的内容评估和提取
3. **可扩展**: 支持水平扩展
4. **多租户**: 支持多个知识库集合
5. **增量更新**: 自动保持内容最新
6. **标准API**: RESTful接口，易于集成

## 🔨 快速启动

```bash
# 克隆仓库
git clone https://github.com/yourorg/intelligent-crawler-service

# 配置环境变量
cp .env.example .env
# 编辑 .env 添加 API keys

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 测试API
curl http://localhost:8080/health
```

这个设计结合了现有开源项目的优点，并添加了智能化功能，可以作为通用的爬虫向量化服务用于多个项目。