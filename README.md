# 🧠 Smart Assistant (Immigration QA System)

A modular, self-evolving, embedding-based intelligent assistant for answering immigration-related questions. Built with OpenAI, Qdrant, and Telegram interface, and designed to support future multi-domain, multi-channel deployment.

---

## ✅ MVP 功能概览

- 🔍 语义问句统一（Canonical Question Normalization）
- 📥 知识结构化记录与向量入库
- 🧠 向量检索 + GPT 回答生成
- 🧹 自动知识清理（TTL）+ 聚类合并去冗余
- 🤖 Telegram 输入通道（未来支持 YouTube/XHS）

---

## 🧱 项目结构模块说明

### 1. `main.py`
入口程序，运行 Telegram bot，监听用户输入，调用问答引擎生成回复。

### 2. `agent_core/`
智能问答核心逻辑：
- `response_router.py`：主控制器，调用向量检索、构造 prompt、生成回答。
- `prompt_builder.py`：将用户问题与知识库片段整合为 GPT 使用的提示。
- `llm_executor.py`：调用 OpenAI GPT 模型接口。
- `canonical_router.py`：将用户问题转换为语义统一的标准问法。

### 3. `vector_engine/`
向量操作模块：
- `embedding_router.py`：生成 OpenAI embedding 向量。
- `vector_indexer.py`：将文本和 metadata 写入 Qdrant。
- `retriever.py`：从 Qdrant 中检索相似知识片段，默认先语义规范化。

### 4. `knowledge_ingestion/`
知识接入与处理：
- `doc_parser.py`：从 IRCC HTML 或文本文档中提取段落内容。
- `qa_logger.py`：记录结构化问答（带 canonical 问法 + 自动标签），并存入知识库。
- `tagger.py`：基于 YAML 标签规则，对问答自动打上关键词标签。

### 5. `knowledge_manager/`
知识生命周期管理：
- `ttl_cleaner.py`：自动删除过期知识（默认 180 天）。
- `cluster_merger.py`：定期用 KMeans 聚类相似问答并用 GPT 合并为精简条目。
- `delete_old_points.py`：清理合并后的原始问答片段。

### 6. `scripts/`
脚本集：
- `load_and_index.py`：将 IRCC 政策文档导入知识库。
- `weekly_cleanup.py`：批量执行合并 + 清理流程。
- `run_weekly_cleanup.sh`：Shell 启动器，便于 crontab 部署。

### 7. `tags/`
YAML 标签配置文件夹，每个领域一个文件（如 `immigration.yaml`）用于 `tagger.py` 自动标注。

---

## 🛠️ 环境变量（.env）

```env
OPENAI_API_KEY=your-openai-key
TELEGRAM_TOKEN=your-telegram-token
OPENAI_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=immigration_qa
QDRANT_MERGED_COLLECTION=immigration_merged
TTL_DAYS=180
TAG_RULE_DIR=tags
```

---

## 🧪 启动方式

```bash
# 启动 Telegram 问答 bot
python main.py

# 导入 IRCC 政策文档
python scripts/load_and_index.py data/ircc_news.html html

# 每周知识整理（可加 crontab）
bash run_weekly_cleanup.sh
```

---

## 🚀 可选扩展

| 模块 | 说明 |
|------|------|
| 多渠道输入 | 支持 Slack、XHS、YouTube 等平台评论问答 |
| 多领域支持 | 每个领域配置独立标签和 Qdrant collection |
| 用户反馈强化 | 用户点赞的内容优先保留或合并为 FAQ |
| 可视化后台 | 回答历史、知识浏览、标注 UI 等（用 Streamlit 搭建） |

---

本项目模块清晰、结构稳定，适合你的 Cursor Agent 理解全流程与未来接入点。
