# src/knowledge_manager/ttl_cleaner.py

"""
TTL清理器：负责清理过期的知识点
"""

from datetime import datetime, timedelta
from src.vector_engine.qdrant_client import (
    get_client,
    DOCUMENT_COLLECTION,
    init_collections
)
from src.config.env_manager import init_config
from qdrant_client.http import models

# 初始化配置
config = init_config()
TTL_DAYS = config['knowledge']['ttl_days']

def clean_expired_points():
    """清理过期的向量点"""
    client = get_client()
    
    init_collections()
    
    cutoff_date = datetime.utcnow() - timedelta(days=TTL_DAYS)
    
    try:
        try:
            date_filter = models.FieldCondition(
                key="created_at",
                range=models.Range(
                    lt=cutoff_date.timestamp()  # 使用时间戳
                )
            )
            
            filter_condition = models.Filter(
                must=[date_filter]
            )
            
            # 删除过期的点
            result = client.delete(
                collection_name=DOCUMENT_COLLECTION,
                points_selector=models.FilterSelector(
                    filter=filter_condition
                )
            )
            print(f"已清理 {result.status} 个过期点")
            return result
        except Exception as filter_error:
            print(f"使用过滤器清理过期点失败: {str(filter_error)}")
            
            if "403" in str(filter_error):
                print("权限不足，无法使用过滤器删除点，跳过清理")
                return {"status": "skipped", "reason": "permission_denied"}
            
            return {"status": "error", "reason": str(filter_error)}
    except Exception as e:
        print(f"清理过期点时出错: {str(e)}")
        return {"status": "error", "reason": str(e)}

if __name__ == "__main__":
    clean_expired_points()
