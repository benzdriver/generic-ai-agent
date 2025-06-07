# 🔗 Doji Memory 集成指南

本指南说明如何将 Generic AI Agent 与 Doji Memory 系统集成，实现企业级向量存储和检索。

## 🎯 集成概述

### 架构优势

```
┌─────────────────────┐    HTTP API    ┌─────────────────────┐
│   Generic AI Agent  │ ──────────────► │   Doji Memory       │
│   (智能问答前端)     │                │   (向量存储后端)     │
│                     │                │                     │
│ • Telegram Bot      │                │ • Weaviate 数据库   │
│ • 知识管理          │                │ • 批量优化          │
│ • TTL 清理          │                │ • 智能缓存          │
│ • 聚类合并          │                │ • REST API          │
└─────────────────────┘                └─────────────────────┘
```

**集成后的优势：**
- 🚀 **性能提升**: 利用 Doji Memory 的批量处理和缓存优化
- 🔧 **服务解耦**: 向量存储作为独立微服务部署
- 📈 **可扩展性**: 支持多个 AI Agent 共享同一个向量存储
- 🛡️ **企业级**: 生产就绪的向量存储解决方案

## 🚀 快速开始

### 1. 环境配置

创建 `.env` 文件：

```bash
# 向量后端配置
VECTOR_BACKEND=doji_memory
DOJI_MEMORY_URL=http://your-internal-server:8000

# OpenAI API 配置
OPENAI_API_KEY=your-openai-api-key

# Telegram Bot 配置
TELEGRAM_TOKEN=your-telegram-bot-token
```

### 2. 启动 Doji Memory 服务

在内部网络的另一台机器上：

```bash
# 克隆 Doji Memory
git clone https://github.com/benzdriver/doji_memory.git
cd doji_memory

# 配置环境变量
echo "OPENAI_API_KEY=your_openai_api_key" > .env

# 启动服务
cd api
docker-compose up -d

# 验证服务
curl http://localhost:8000/health
```

### 3. 测试集成

```bash
# 在 Generic AI Agent 目录中
python test_doji_integration.py
```

## 🔧 配置选项

### 向量后端切换

Generic AI Agent 支持在 Qdrant 和 Doji Memory 之间无缝切换：

```bash
# 使用 Qdrant（默认）
VECTOR_BACKEND=qdrant

# 使用 Doji Memory
VECTOR_BACKEND=doji_memory
DOJI_MEMORY_URL=http://192.168.1.100:8000
```

### 集合映射

系统自动将 Qdrant 集合映射到 Doji Memory 的项目/仓库结构：

| Qdrant 集合 | Doji Memory 项目 | Doji Memory 仓库 |
|-------------|------------------|------------------|
| `canonical_queries` | `generic-ai-agent` | `canonical` |
| `conversations` | `generic-ai-agent` | `conversations` |
| `documents` | `generic-ai-agent` | `documents` |
| `merged_knowledge` | `generic-ai-agent` | `merged` |

## 📚 API 使用示例

### 基本向量操作

```python
from vector_engine.hybrid_vector_router import get_hybrid_router, VectorBackend

# 初始化路由器
router = get_hybrid_router()

# 获取文本向量
vector = router.get_embedding("测试文本")

# 批量向量化（Doji Memory 优势）
vectors = router.get_batch_embeddings(["文本1", "文本2", "文本3"])

# 存储数据
points = [{
    "id": "uuid-here",
    "vector": vector,
    "payload": {"text": "内容", "tags": ["标签"]}
}]
router.upsert_points("collection_name", points)

# 搜索
results = router.search(
    collection_name="documents",
    query_text="查询文本",
    limit=5
)
```

### 检索器集成

```python
from vector_engine.retriever import retrieve_relevant_chunks

# 自动使用配置的后端
results = retrieve_relevant_chunks(
    query="加拿大移民申请",
    limit=5,
    domain="immigration"
)
```

## 🔄 后端切换

### 运行时切换

```python
from vector_engine.hybrid_vector_router import switch_backend, VectorBackend

# 切换到 Doji Memory
router = switch_backend(
    VectorBackend.DOJI_MEMORY, 
    doji_url="http://192.168.1.100:8000"
)

# 切换回 Qdrant
router = switch_backend(VectorBackend.QDRANT)
```

### 环境变量切换

```bash
# 方法1: 修改 .env 文件
VECTOR_BACKEND=doji_memory

# 方法2: 运行时设置
export VECTOR_BACKEND=doji_memory
python main.py
```

## 🧪 测试和验证

### 健康检查

```python
from vector_engine.hybrid_vector_router import get_hybrid_router

router = get_hybrid_router()
health = router.health_check()
print(health)
```

### 性能对比测试

```python
import time
from vector_engine.hybrid_vector_router import switch_backend, VectorBackend

# 测试 Qdrant
router_qdrant = switch_backend(VectorBackend.QDRANT)
start = time.time()
vectors_qdrant = [router_qdrant.get_embedding(f"文本{i}") for i in range(10)]
time_qdrant = time.time() - start

# 测试 Doji Memory
router_doji = switch_backend(VectorBackend.DOJI_MEMORY)
start = time.time()
vectors_doji = router_doji.get_batch_embeddings([f"文本{i}" for i in range(10)])
time_doji = time.time() - start

print(f"Qdrant: {time_qdrant:.2f}s")
print(f"Doji Memory: {time_doji:.2f}s")
print(f"性能提升: {(time_qdrant/time_doji):.1f}x")
```

## 🚀 部署建议

### 生产环境部署

1. **Doji Memory 服务器**:
   ```bash
   # 内部网络机器 (192.168.1.100)
   cd doji_memory/api
   docker-compose up -d
   ```

2. **Generic AI Agent**:
   ```bash
   # 应用服务器
   export VECTOR_BACKEND=doji_memory
   export DOJI_MEMORY_URL=http://192.168.1.100:8000
   python main.py
   ```

### 高可用配置

```bash
# 使用负载均衡器
DOJI_MEMORY_URL=http://doji-memory-lb:8000

# 或者配置多个实例
DOJI_MEMORY_URLS=http://192.168.1.100:8000,http://192.168.1.101:8000
```

## 🔍 故障排除

### 常见问题

1. **连接失败**:
   ```bash
   # 检查网络连通性
   curl http://192.168.1.100:8000/health
   
   # 检查防火墙设置
   telnet 192.168.1.100 8000
   ```

2. **API 密钥问题**:
   ```bash
   # 确保两个服务使用相同的 OpenAI API Key
   echo $OPENAI_API_KEY
   ```

3. **性能问题**:
   ```python
   # 启用缓存
   client.get_embedding("text", use_cache=True)
   
   # 使用批量处理
   client.get_batch_embeddings(texts)
   ```

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from vector_engine.doji_memory_client import DojiMemoryClient
client = DojiMemoryClient()
```

## 📈 性能优化

### 批量处理优化

```python
# ❌ 低效：逐个处理
for text in texts:
    vector = router.get_embedding(text)

# ✅ 高效：批量处理
vectors = router.get_batch_embeddings(texts)
```

### 缓存策略

```python
# 启用智能缓存
client = DojiMemoryClient()
vector = client.get_embedding("重复文本", use_cache=True)
```

### 连接池配置

```python
# 自定义超时和连接设置
client = DojiMemoryClient(
    base_url="http://192.168.1.100:8000",
    timeout=60
)
```

## 🎉 集成完成

恭喜！你已经成功将 Generic AI Agent 与 Doji Memory 集成。现在你可以：

- ✅ 享受企业级向量存储性能
- ✅ 利用批量处理和智能缓存
- ✅ 实现服务解耦和独立扩展
- ✅ 在两种后端之间无缝切换

如有问题，请查看测试脚本 `test_doji_integration.py` 或参考两个项目的文档。 