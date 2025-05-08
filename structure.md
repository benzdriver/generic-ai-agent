# 系统模块职责说明（MVP阶段）

本系统为一套通用向量知识问答平台，已实现以下模块功能：

---

## 📂 agent_core/

- **response_router.py**
    
    接收用户问题 → 标准化问法 → 检索知识 → 构造 prompt → 调用 GPT 回答 → 写入知识库。
    
- **llm_executor.py**
    
    统一封装 OpenAI GPT API 接口，支持模型选择与重试。
    
- **prompt_builder.py**
    
    将检索内容与用户问题拼接为提示模板，供 GPT 使用。
    
- **canonical_router.py**
    
    将不同表达的用户提问规范化为统一形式，并缓存到 Qdrant。
    

---

## 📂 vector_engine/

- **embedding_router.py**
    
    对文本生成向量，默认支持 OpenAI embedding。
    
- **vector_indexer.py**
    
    将知识片段写入 Qdrant 向量库，附带元数据。
    
- **retriever.py**
    
    用语义向量搜索知识库中最相关片段，并返回结果用于生成回答。
    

---

## 📂 knowledge_ingestion/

- **doc_parser.py**
    
    解析 IRCC HTML 或纯文本内容，按段落切分。
    
- **qa_logger.py**
    
    结构化记录用户问答片段，自动规范问法、打标签、检查重复后入库。
    
- **tagger.py**
    
    通过配置文件（tags/*.yaml）为文本内容自动打上主题标签。
    

---

## 📂 knowledge_manager/

- **ttl_cleaner.py**
    
    清理超过指定时效（如180天）的知识片段，防止污染知识库。
    
- **cluster_merger.py**
    
    对知识进行聚类，自动用 GPT 总结为更通用问答，提升召回质量。
    
- **delete_old_points.py**
    
    删除已被合并的原始知识点，保持知识库精炼。
    

---

## 📂 scripts/

- **load_and_index.py**
    
    从文档中加载政策段落并批量写入向量库。
    
- **weekly_cleanup.py**
    
    一键运行知识聚类 → 合并 → 清理的自动维护任务（支持 crontab）。
    
- **run_weekly_cleanup.sh**
    
    可执行 shell 脚本，用于服务器上定时调度任务。
    

---

## 📂 tags/

- **immigration.yaml**
    
    关键词 → 标签映射文件，用于自动分类问题，如 “lmia”、“suv”、“spouse”等。
    

---

## ✅ 运行入口

- **main.py**
    
    Telegram 接入点：接受用户提问，调用 agent_core 问答流程并自动回复。