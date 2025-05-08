# Placeholder for conflict_detector.py 

"""
冲突检测器：检测和分析知识点之间的冲突

功能：
1. 语义相似度检测
2. 时间版本比较
3. 内容矛盾分析（通过 LLM）
"""

import json
import datetime
from typing import List, Dict, Tuple
import numpy as np
from vector_engine.embedding_router import get_embedding
from vector_engine.qdrant_client import get_client, DOCUMENT_COLLECTION
from config.env_manager import init_config
from llm.factory import LLMFactory

# 初始化配置
config = init_config()
SIMILARITY_THRESHOLD = 0.92  # 语义相似度阈值

# 获取LLM实例
llm = LLMFactory.get_llm()

def analyze_conflict(text1: str, text2: str) -> Dict[str, any]:
    """分析两个知识点之间的冲突
    
    Args:
        text1: 第一个知识点
        text2: 第二个知识点
        
    Returns:
        Dict: 包含冲突分析结果的字典
    """
    prompt = f"""请分析以下两个知识点是否存在冲突，并给出详细分析：

知识点1：
{text1}

知识点2：
{text2}

请从以下几个方面分析：
1. 是否存在直接冲突
2. 是否存在潜在冲突
3. 冲突的具体内容
4. 可能的解决方案

请以JSON格式返回结果，包含以下字段：
- has_conflict: 是否存在冲突（true/false）
- conflict_type: 冲突类型（"direct"/"potential"/"none"）
- details: 具体冲突内容
- solution: 建议的解决方案
"""
    
    try:
        response = llm.generate(prompt)
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        return {
            "has_conflict": True,  # 保守起见，解析失败时认为可能存在冲突
            "conflict_type": "potential",
            "details": response,
            "solution": "需要人工审核（JSON解析失败）"
        }

def check_content_conflict(text1: str, text2: str) -> Tuple[bool, str]:
    """使用LLM检查两段文本是否存在冲突
    
    Args:
        text1: 第一段文本
        text2: 第二段文本
        
    Returns:
        Tuple[bool, str]: (是否存在冲突, 原因)
    """
    llm = LLMFactory.get_llm()
    
    # 构建提示词
    prompt = f"""请分析以下两段文本是否存在冲突或矛盾：

文本1：
{text1}

文本2：
{text2}

请仅返回 "有冲突" 或 "无冲突"，以及一句话说明原因。
"""
    
    # 判断是否需要分块处理
    if llm.should_use_chunks([text1, text2]):
        response = llm.generate_with_chunks([text1, text2], **{"prompt": prompt})
    else:
        response = llm.generate(prompt)
    
    # 解析响应
    has_conflict = "有冲突" in response
    reason = response.split("，", 1)[1] if "，" in response else ""
    
    return has_conflict, reason

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算余弦相似度"""
    v1_array = np.array(v1)
    v2_array = np.array(v2)
    return np.dot(v1_array, v2_array) / (np.linalg.norm(v1_array) * np.linalg.norm(v2_array))

def fetch_recent_documents(days: int = 30) -> List[Dict]:
    """获取最近N天的知识条目"""
    client = get_client()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    
    points = client.scroll(
        collection_name=DOCUMENT_COLLECTION,
        scroll_filter={
            "must": [
                {
                    "key": "created_at",
                    "range": {
                        "gte": cutoff.isoformat()
                    }
                }
            ]
        },
        limit=1000,
        with_payload=True,
        with_vectors=True
    )[0]
    
    return [
        {
            "id": point.id,
            "vector": point.vector,
            "text": point.payload.get("content", ""),  # 使用 content 字段
            "created_at": point.payload.get("created_at")
        }
        for point in points
    ]

def detect_conflicts(knowledge_points: List[Dict] = None) -> List[Tuple[Dict, Dict, Dict]]:
    """检测知识库中的冲突
    
    Args:
        knowledge_points: 可选的知识点列表，如果不提供则获取最近的文档
        
    Returns:
        List[Tuple]: 包含冲突文档对和分析结果的列表
    """
    if knowledge_points is None:
        knowledge_points = fetch_recent_documents()
    
    conflicts = []
    for i, doc1 in enumerate(knowledge_points):
        for doc2 in knowledge_points[i+1:]:
            # 1. 检查语义相似度
            similarity = cosine_similarity(doc1["vector"], doc2["vector"])
            
            if similarity > SIMILARITY_THRESHOLD:
                # 2. 使用 LLM 检查内容冲突
                has_conflict, reason = check_content_conflict(doc1["text"], doc2["text"])
                
                if has_conflict:
                    # 3. 详细分析冲突
                    analysis = analyze_conflict(doc1["text"], doc2["text"])
                    analysis["similarity"] = similarity
                    analysis["initial_reason"] = reason
                    
                    conflicts.append((doc1, doc2, analysis))
    
    return conflicts

def resolve_conflicts(conflicts: List[Tuple[Dict, Dict, Dict]]) -> None:
    """解决检测到的冲突
    
    策略：
    1. 对于直接冲突：保留最新版本，将旧版本标记为已弃用
    2. 对于潜在冲突：标记需要人工审核
    """
    client = get_client()
    
    for doc1, doc2, analysis in conflicts:
        time1 = datetime.datetime.fromisoformat(doc1["created_at"])
        time2 = datetime.datetime.fromisoformat(doc2["created_at"])
        
        if analysis["conflict_type"] == "direct":
            # 直接冲突：标记较旧的版本为弃用
            obsolete_doc = doc1 if time1 < time2 else doc2
            client.update_points(
                collection_name=DOCUMENT_COLLECTION,
                points_selector={"points": [obsolete_doc["id"]]},
                payload={
                    "status": "obsolete",
                    "obsolete_reason": analysis["details"],
                    "obsolete_at": datetime.datetime.utcnow().isoformat()
                }
            )
            print(f"✅ 已将文档 {obsolete_doc['id']} 标记为弃用")
        else:
            # 潜在冲突：标记两个文档都需要审核
            for doc in [doc1, doc2]:
                client.update_points(
                    collection_name=DOCUMENT_COLLECTION,
                    points_selector={"points": [doc["id"]]},
                    payload={
                        "status": "needs_review",
                        "review_reason": analysis["details"],
                        "flagged_at": datetime.datetime.utcnow().isoformat()
                    }
                )
            print(f"⚠️ 已将文档 {doc1['id']} 和 {doc2['id']} 标记为需要审核")

if __name__ == "__main__":
    print("🔍 开始检测知识库冲突...")
    conflicts = detect_conflicts()
    
    if conflicts:
        print(f"发现 {len(conflicts)} 对潜在冲突：")
        for doc1, doc2, analysis in conflicts:
            print(f"\n相似度：{analysis['similarity']:.2f}")
            print(f"冲突类型：{analysis['conflict_type']}")
            print(f"文档1：{doc1['text'][:100]}...")
            print(f"文档2：{doc2['text'][:100]}...")
            print(f"分析：{analysis['details']}")
            print(f"建议解决方案：{analysis['solution']}")
        
        resolve_conflicts(conflicts)
    else:
        print("✅ 未发现冲突") 