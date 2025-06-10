"""
智能边界检测器
使用知识库动态判断查询是否与移民相关，避免硬编码关键词维护问题
"""

from typing import List, Tuple
import logging
from src.infrastructure.vector_store.base import BaseVectorStore
from src.infrastructure.vector_store.embedding_router import get_embedding

logger = logging.getLogger(__name__)

class IntelligentBoundaryDetector:
    """智能边界检测器 - 基于知识库的动态判断"""
    
    def __init__(self, vector_store: BaseVectorStore):
        self.vector_store = vector_store
        
        # 基础配置
        self.immigration_threshold = 0.4  # 相似度阈值（基于测试分析调整）
        self.max_search_results = 5
        
        # 明确的排除词（非常确定与移民无关）
        self.explicit_exclude_keywords = [
            "天气", "weather", "今天几号", "现在几点", "你好", "hello", "谢谢", "thank you",
            "再见", "goodbye", "聊天", "chat", "讲个笑话", "tell me a joke",
            "唱歌", "sing", "跳舞", "dance", "游戏", "game", "电影推荐", "movie recommendation",
            "汽车推荐", "买车", "车型推荐", "汽车品牌", "二手车", "新车", "车辆", "汽车价格"
        ]
        
    def is_immigration_related(self, query: str, domain: str = "immigration_consultant") -> Tuple[bool, float, str]:
        """
        使用知识库判断查询是否与移民相关
        
        Args:
            query: 用户查询
            domain: 领域名称
            
        Returns:
            Tuple[bool, float, str]: (是否相关, 置信度分数, 判断理由)
        """
        query_lower = query.lower().strip()
        
        # 第一层：明确排除的通用词汇
        if any(exclude in query_lower for exclude in self.explicit_exclude_keywords):
            return False, 0.0, "明确的非移民通用查询"
        
        # 第二层：使用向量搜索在知识库中查找相关内容
        try:
            similarity_score, reason = self._search_knowledge_base(query, domain)
            
            # 判断是否相关
            is_related = similarity_score >= self.immigration_threshold
            
            logger.info(f"边界检测 - 查询: '{query[:50]}...', 相似度: {similarity_score:.3f}, 相关: {is_related}")
            
            return is_related, similarity_score, reason
            
        except Exception as e:
            logger.error(f"知识库查询失败: {e}")
            # 出错时采用保守策略，假设相关
            return True, 0.5, "知识库查询失败，保守判断为相关"
    
    def _search_knowledge_base(self, query: str, domain: str) -> Tuple[float, str]:
        """在知识库中搜索相关内容"""
        
        # 获取查询的向量表示
        query_vector = get_embedding(query)
        
        # 在主要集合中搜索（使用实际存在的集合名称）
        collection_names = [
            "immigration_docs",        # 移民文档
            "merged_knowledge",        # 合并的知识库
            "canonical_queries",       # 标准化查询
            "conversations",           # 历史对话
            "documents"                # 通用文档
        ]
        
        max_similarity = 0.0
        best_match_content = ""
        
        for collection_name in collection_names:
            try:
                # 在当前集合中搜索
                results = self.vector_store.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=self.max_search_results
                )
                
                if results:
                    # 获取最高相似度
                    top_score = results[0].score if results else 0.0
                    
                    if top_score > max_similarity:
                        max_similarity = top_score
                        best_match_content = results[0].payload.get("content", "")[:100]
                        
            except Exception as e:
                logger.warning(f"搜索集合 {collection_name} 失败: {e}")
                continue
        
        # 生成判断理由
        if max_similarity >= self.immigration_threshold:
            reason = f"在知识库中找到相关内容 (相似度: {max_similarity:.3f}): {best_match_content[:50]}..."
        else:
            reason = f"知识库中未找到相关内容 (最高相似度: {max_similarity:.3f})"
            
        return max_similarity, reason
    
    def test_keyword_in_knowledge_base(self, keyword: str) -> dict:
        """测试特定关键词在知识库中的相关性"""
        is_related, score, reason = self.is_immigration_related(keyword)
        
        return {
            "keyword": keyword,
            "is_immigration_related": is_related,
            "similarity_score": score,
            "reason": reason,
            "threshold": self.immigration_threshold
        }

# 辅助函数：测试多个关键词
def test_multiple_keywords(detector: IntelligentBoundaryDetector, keywords: List[str]) -> List[dict]:
    """批量测试关键词"""
    results = []
    for keyword in keywords:
        result = detector.test_keyword_in_knowledge_base(keyword)
        results.append(result)
    return results

# 使用示例和测试
def demo_intelligent_detection(vector_store: BaseVectorStore):
    """演示智能检测功能"""
    detector = IntelligentBoundaryDetector(vector_store)
    
    # 测试关键词列表
    test_keywords = [
        "suv",                    # 创业签证（应该相关）
        "express entry",          # 快速通道（应该相关）
        "汽车推荐",                # 汽车（应该不相关）
        "pnp",                    # 省提名（应该相关）
        "天气怎么样",              # 天气（应该不相关）
        "配偶担保",               # 移民项目（应该相关）
        "买房投资",               # 投资（可能不相关）
        "startup visa",           # 创业签证（应该相关）
        "lmia",                   # 劳动力市场影响评估（应该相关）
        "看电影"                  # 娱乐（应该不相关）
    ]
    
    print("🧪 智能边界检测测试结果：")
    print("=" * 80)
    
    results = test_multiple_keywords(detector, test_keywords)
    
    for result in results:
        status = "✅ 相关" if result["is_immigration_related"] else "❌ 不相关"
        print(f"{status} | {result['keyword']:<15} | 分数: {result['similarity_score']:.3f} | {result['reason'][:50]}...")
    
    return results

if __name__ == "__main__":
    # 如果直接运行此文件，执行演示
    from src.infrastructure.vector_store.factory import VectorStoreFactory
    
    vector_store = VectorStoreFactory.get_vector_store()
    demo_intelligent_detection(vector_store) 