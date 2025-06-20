# 🚀 Intelligent Crawler Service 部署指南

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API Key 或 Anthropic API Key
- 至少 4GB 可用内存

## 🔧 快速部署

### 1. 准备环境

```bash
# 克隆或复制服务目录
cd intelligent-crawler-service

# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，添加你的 API Keys
# 必须设置：OPENAI_API_KEY 或 ANTHROPIC_API_KEY
nano .env
```

### 2. 构建和启动服务

```bash
# 构建 Docker 镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# API 文档
open http://localhost:8080/docs

# Flower (任务监控)
open http://localhost:5555
```

## 📡 使用示例

### 创建爬取任务

```bash
curl -X POST http://localhost:8080/api/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.canada.ca/en/immigration-refugees-citizenship.html"],
    "config": {
      "max_depth": 3,
      "ai_evaluation": true,
      "min_quality_score": 0.6,
      "extract_tables": true
    },
    "collection_name": "immigration_docs"
  }'
```

### 查询任务状态

```bash
# 替换 {job_id} 为实际的任务 ID
curl http://localhost:8080/api/v1/crawl/{job_id}
```

### 搜索知识库

```bash
curl -X POST http://localhost:8080/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Express Entry requirements",
    "collection": "immigration_docs",
    "top_k": 5
  }'
```

## 🔍 服务架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   API       │────▶│   Redis      │────▶│  Workers    │
│  (Port 8080)│     │ (Task Queue) │     │  (Celery)   │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                         │
       ▼                                         ▼
┌─────────────┐                          ┌─────────────┐
│  PostgreSQL │                          │   Qdrant    │
│  (Metadata) │                          │  (Vectors)  │
└─────────────┘                          └─────────────┘
```

## 📊 监控和管理

### 查看任务队列

```bash
# 访问 Flower Web UI
open http://localhost:5555

# 或使用 Redis CLI
docker-compose exec redis redis-cli
> LLEN celery
```

### 数据库管理

```bash
# 连接到 PostgreSQL
docker-compose exec postgres psql -U crawler -d crawler_db

# 查看爬取任务
SELECT * FROM crawl_jobs ORDER BY created_at DESC LIMIT 10;

# 查看已爬取页面
SELECT url, quality_score, crawled_at FROM crawled_pages 
WHERE quality_score > 0.7 
ORDER BY crawled_at DESC LIMIT 20;
```

### 向量数据库管理

```bash
# Qdrant Web UI
open http://localhost:6333/dashboard

# 查看集合
curl http://localhost:6333/collections
```

## 🔧 配置优化

### 性能调优

编辑 `docker-compose.yml`:

```yaml
services:
  crawler-worker:
    deploy:
      replicas: 5  # 增加爬虫工作器数量
    environment:
      - BROWSER_POOL_SIZE=10  # 增加浏览器池大小

  ai-worker:
    deploy:
      replicas: 3  # 增加 AI 工作器数量
```

### 资源限制

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          memory: 512M
```

## 🚨 故障排除

### 常见问题

1. **API 无法启动**
   ```bash
   # 检查端口占用
   lsof -i :8080
   
   # 查看详细日志
   docker-compose logs api
   ```

2. **爬虫任务失败**
   ```bash
   # 检查 worker 日志
   docker-compose logs crawler-worker
   
   # 重启 workers
   docker-compose restart crawler-worker
   ```

3. **内存不足**
   ```bash
   # 减少并发数
   # 编辑 .env
   MAX_CONCURRENT_CRAWLS=5
   BROWSER_POOL_SIZE=3
   ```

## 🔒 安全建议

1. **生产环境配置**
   - 使用强密码替换默认的数据库密码
   - 启用 API 认证
   - 配置 HTTPS

2. **备份策略**
   ```bash
   # 备份 PostgreSQL
   docker-compose exec postgres pg_dump -U crawler crawler_db > backup.sql
   
   # 备份 Qdrant
   docker-compose exec qdrant qdrant-backup /qdrant/storage /backup
   ```

## 📈 扩展部署

### Kubernetes 部署

查看 `k8s/` 目录中的 Kubernetes 配置文件（如果需要可以创建）。

### 云服务部署

- **AWS**: 使用 ECS 或 EKS
- **GCP**: 使用 Cloud Run 或 GKE
- **Azure**: 使用 Container Instances 或 AKS

## 📞 支持

如有问题，请查看：
- API 文档: http://localhost:8080/docs
- 项目 README: [README.md](README.md)
- 演示脚本: `python demo.py`

---

**提示**: 首次运行可能需要下载 Docker 镜像和安装依赖，请耐心等待。