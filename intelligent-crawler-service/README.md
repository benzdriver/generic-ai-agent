# 🤖 Intelligent Crawler Service

一个完全自主的AI驱动爬虫系统，专为构建高质量知识库设计。

## ✨ 核心特性

- **AI驱动的页面价值评估**: 自动判断页面是否值得爬取
- **智能内容提取**: 识别并提取表格、PDF、动态内容
- **自动质量控制**: 多层验证确保数据准确性
- **增量更新**: 智能检测变化，只更新必要内容
- **向量化存储**: 自动转换为向量并存储到数据库
- **完全自动化**: 无需人工干预的端到端流程

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/yourorg/intelligent-crawler-service
cd intelligent-crawler-service

# 2. 配置环境
cp .env.example .env
# 编辑 .env 文件，添加必要的 API keys

# 3. 启动服务
docker-compose up -d

# 4. 测试API
curl http://localhost:8080/health
```

## 📖 使用示例

### 基础爬取

```python
import requests

# 创建爬取任务
response = requests.post('http://localhost:8080/api/v1/crawl', json={
    'urls': ['https://www.canada.ca/immigration'],
    'config': {
        'max_depth': 3,
        'ai_evaluation': True,
        'min_quality_score': 0.6
    }
})

job_id = response.json()['job_id']
```

### 搜索知识库

```python
# 搜索
results = requests.post('http://localhost:8080/api/v1/search', json={
    'query': 'Express Entry requirements',
    'collection': 'immigration_docs'
})
```

## 🏗️ 架构

```
intelligent-crawler-service/
├── api/                 # FastAPI 应用
├── crawler/            # 智能爬虫核心
├── ai/                 # AI评估和分析
├── vectorizer/         # 向量化服务
├── updater/           # 增量更新服务
├── storage/           # 存储适配器
├── docker/            # Docker配置
└── tests/             # 测试套件
```

## 📝 License

MIT License