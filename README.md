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

本系统采用分层架构，将核心业务逻辑与外部服务实现解耦，便于维护和扩展。

### 1. `src/app/`
核心应用层，包含所有业务逻辑。
- **`agent/`**: 智能问答核心逻辑，包括响应生成、Prompt构建和查询规范化。
- **`ingestion/`**: 知识接入与处理，负责解析文档、记录问答和自动打标签。
- **`knowledge/`**: 知识生命周期管理，包括知识的清理、合并和冲突检测。
  - `cluster_merger.py`: 定期用 KMeans 聚类相似问答并用 GPT 合并为精简条目。
  - `conflict_detector.py`: 检测和分析知识点之间的冲突。
  - `delete_old_points.py`: 清理合并后的原始问答片段。
  - `ttl_cleaner.py`: 自动删除过期知识。

### 2. `src/infrastructure/`
基础设施层，封装了所有与外部服务的交互。
- **`vector_store/`**: 向量数据库操作，封装了Qdrant客户端、文本嵌入、索引和检索。
- **`config/`**: 应用配置管理，负责加载环境变量和管理多领域配置。
- **`llm/`**: 大语言模型客户端，（未来）将封装与不同LLM提供商的API交互。

### 3. `src/main.py`
主程序入口，负责启动Telegram Bot并处理用户消息。

### 4. `scripts/`
独立的维护和管理脚本，例如初始化数据库集合、创建索引等。

### 5. `tests/`
包含应用的单元测试和集成测试。

### 6. `tags/`
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
