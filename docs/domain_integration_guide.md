# 垂直领域集成指南

本文档介绍如何将通用AI代理系统适配到不同的垂直领域，实现领域特定的智能服务。

## 1. 领域配置文件

每个垂直领域需要创建一个YAML配置文件，放置在`domains`目录下。配置文件包含以下内容：

```yaml
# 领域基本信息
name: "your_domain_name"  # 领域名称
description: "领域描述"    # 领域简要描述

# LLM相关配置
llm:
  preferred_provider: "openai"  # 首选LLM提供商
  model_params:                 # 模型参数
    temperature: 0.5           # 温度参数
    top_p: 0.9                 # 采样参数

# 提示词模板
prompt_template: |
  你是一名专业的{领域}助手，请根据以下相关资料回答用户的问题。

  【相关资料】
  {context}

  【用户提问】
  {query}

  请用专业且友好的语气作答。如果没有相关信息，请明确说明。

# 向量集合名称
vector_collection: "your_domain_collection"

# 领域标签
tags:
  - "标签1"
  - "标签2"
  - "标签3"

# 评估指标
evaluation_metrics:
  accuracy: 0.8    # 准确率权重
  relevance: 0.7   # 相关性权重
  completeness: 0.6 # 完整性权重
```

## 2. 使用领域特定LLM

在代码中使用领域特定LLM：

```python
from llm.factory import FallbackLLM

# 创建特定领域的LLM实例
legal_llm = FallbackLLM.for_domain("legal")

# 使用领域LLM生成回答
response = legal_llm.generate(prompt)
```

## 3. 使用领域特定提示词

```python
from agent_core.prompt_builder import build_prompt
from vector_engine.retriever import retrieve_relevant_chunks

# 检索领域相关知识
chunks = retrieve_relevant_chunks(query, domain="legal")

# 构建领域特定提示词
prompt = build_prompt(query, chunks, domain="legal")
```

## 4. 注册新的领域

通过代码动态注册新领域：

```python
from config.domain_manager import domain_manager

# 注册新领域
domain_config = {
    "name": "finance",
    "description": "金融咨询领域",
    "llm": {
        "preferred_provider": "openai",
        "model_params": {
            "temperature": 0.3
        }
    },
    "prompt_template": "你是一名金融顾问...",
    "vector_collection": "finance_docs",
    "tags": ["投资", "理财", "股票"],
    "evaluation_metrics": {
        "accuracy": 0.9
    }
}

domain_manager.register_domain("finance", domain_config)
```

## 5. 领域知识库管理

为每个领域创建独立的向量集合：

```python
from vector_engine.retriever import register_domain_collection

# 注册领域集合
register_domain_collection("finance", "finance_docs")
```

## 6. 领域评估指标

每个领域可以定义特定的评估指标，用于衡量AI回答的质量：

```python
from config.domain_manager import domain_manager

# 获取领域评估指标
metrics = domain_manager.get_domain_evaluation_metrics("legal")

# 使用指标评估回答
def evaluate_response(response, metrics):
    # 实现评估逻辑
    pass
```

## 7. 完整使用示例

```python
from llm.factory import FallbackLLM
from agent_core.prompt_builder import build_prompt
from vector_engine.retriever import retrieve_relevant_chunks
from config.domain_manager import domain_manager

def process_query(query, domain="default"):
    # 1. 获取领域配置
    domain_config = domain_manager.get_domain_config(domain)
    
    # 2. 检索领域相关知识
    chunks = retrieve_relevant_chunks(
        query, 
        domain=domain,
        filter_tags=domain_config.get("tags", [])
    )
    
    # 3. 构建领域特定提示词
    prompt = build_prompt(query, chunks, domain=domain)
    
    # 4. 使用领域特定LLM生成回答
    llm = FallbackLLM.for_domain(domain)
    response = llm.generate(prompt)
    
    return response

# 使用示例
response = process_query("什么是知识产权保护？", domain="legal")
print(response)
```

## 8. 领域扩展建议

在扩展新的垂直领域时，建议关注以下几点：

1. **领域知识库**：收集高质量的领域专业知识
2. **领域术语表**：整理领域特定术语和概念
3. **领域标签体系**：建立完善的标签分类系统
4. **领域评估标准**：定义符合领域特点的评估指标
5. **领域提示词优化**：针对领域特点优化提示词模板

通过以上配置和代码调整，可以快速将通用AI代理系统适配到不同的垂直领域，提供更专业、更精准的智能服务。