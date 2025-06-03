# src/knowledge_manager/delete_old_points.py

"""
旧点删除器：负责删除过期或废弃的向量点
"""

from src.vector_engine.doji_memory_client import (
    get_client, 
    DOCUMENT_COLLECTION,
    MERGED_COLLECTION,
    init_collections
)
from src.config.env_manager import init_config

# 初始化配置
config = init_config()

def delete_old_points():
    """删除已标记为废弃的向量点"""
    client = get_client()
    
    init_collections()
    
    try:
        status_filter = models.FieldCondition(
            key="status",
            match=models.MatchValue(
                value="obsolete"
            )
        )
        
        filter_condition = models.Filter(
            must=[status_filter]
        )
        
        results = {
            "document_collection": "skipped",
            "merged_collection": "skipped"
        }
        
        # 尝试删除原始集合中的废弃点
        try:
            doc_result = client.delete(
                collection_name=DOCUMENT_COLLECTION,
                points_selector=models.FilterSelector(
                    filter=filter_condition
                )
            )
            print(f"已从 {DOCUMENT_COLLECTION} 删除 {doc_result.status} 个废弃点")
            results["document_collection"] = doc_result.status
        except Exception as doc_error:
            print(f"从 {DOCUMENT_COLLECTION} 删除废弃点失败: {str(doc_error)}")
            if "403" in str(doc_error):
                print(f"权限不足，无法从 {DOCUMENT_COLLECTION} 删除点")
        
        # 尝试删除合并集合中的废弃点
        try:
            merged_result = client.delete(
                collection_name=MERGED_COLLECTION,
                points_selector=models.FilterSelector(
                    filter=filter_condition
                )
            )
            print(f"已从 {MERGED_COLLECTION} 删除 {merged_result.status} 个废弃点")
            results["merged_collection"] = merged_result.status
        except Exception as merged_error:
            print(f"从 {MERGED_COLLECTION} 删除废弃点失败: {str(merged_error)}")
            if "403" in str(merged_error):
                print(f"权限不足，无法从 {MERGED_COLLECTION} 删除点")
        
        return results
    except Exception as e:
        print(f"删除废弃点时出错: {str(e)}")
        return {
            "document_collection": "error",
            "merged_collection": "error",
            "reason": str(e)
        }

if __name__ == "__main__":
    delete_old_points()
