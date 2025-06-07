"""
混合向量路由器

支持在 Qdrant 和 Doji Memory 之间无缝切换，
提供统一的向量操作接口
"""

import os
from typing import List, Dict, Any, Optional
from enum import Enum
from src.config.env_manager import init_config

# 导入两种客户端
from .qdrant_client import get_client as get_qdrant_client, init_collections as init_qdrant_collections
from .doji_memory_client import get_doji_adapter

class VectorBackend(Enum):
    """向量后端类型"""
    QDRANT = "qdrant"
    DOJI_MEMORY = "doji_memory"

class HybridVectorRouter:
    """混合向量路由器"""
    
    def __init__(self, backend: VectorBackend = None, doji_url: str = None):
        """初始化混合向量路由器
        
        Args:
            backend: 后端类型，如果不指定则从环境变量读取
            doji_url: Doji Memory 服务URL
        """
        # 确定使用的后端
        if backend is None:
            backend_str = os.getenv('VECTOR_BACKEND', 'qdrant').lower()
            self.backend = VectorBackend.QDRANT if backend_str == 'qdrant' else VectorBackend.DOJI_MEMORY
        else:
            self.backend = backend
        
        # 初始化相应的客户端
        if self.backend == VectorBackend.QDRANT:
            self.client = get_qdrant_client()
            self._init_qdrant()
            print(f"🔄 使用 Qdrant 作为向量后端")
        else:
            self.adapter = get_doji_adapter(doji_url)
            print(f"🔄 使用 Doji Memory 作为向量后端: {doji_url or 'default'}")
    
    def _init_qdrant(self):
        """初始化 Qdrant 集合"""
        try:
            init_qdrant_collections()
        except Exception as e:
            print(f"⚠️ Qdrant 集合初始化失败: {str(e)}")
    
    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """插入或更新点数据
        
        Args:
            collection_name: 集合名称
            points: 点数据列表
        """
        if self.backend == VectorBackend.QDRANT:
            # Qdrant 操作
            from qdrant_client.http import models
            qdrant_points = []
            
            for point in points:
                qdrant_point = models.PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                qdrant_points.append(qdrant_point)
            
            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )
            print(f"✅ Qdrant: 成功存储 {len(points)} 条记录到 {collection_name}")
        else:
            # Doji Memory 操作
            self.adapter.upsert_points(collection_name, points)
    
    def search(self, collection_name: str, query_vector: List[float] = None, 
              query_text: str = None, limit: int = 5, 
              query_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索相似向量
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            query_text: 查询文本（Doji Memory 需要）
            limit: 结果数量限制
            query_filter: 查询过滤条件
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        if self.backend == VectorBackend.QDRANT:
            # Qdrant 搜索
            if query_vector is None:
                raise ValueError("Qdrant 后端需要查询向量")
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            
            # 转换为统一格式
            return [
                {
                    "payload": hit.payload,
                    "score": hit.score
                }
                for hit in results
            ]
        else:
            # Doji Memory 搜索
            return self.adapter.search(
                collection_name=collection_name,
                query_text=query_text,
                limit=limit,
                query_filter=query_filter
            )
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本向量
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 向量表示
        """
        if self.backend == VectorBackend.QDRANT:
            # 使用原有的 embedding_router
            from .embedding_router import get_embedding
            return get_embedding(text)
        else:
            # 使用 Doji Memory
            return self.adapter.get_embedding(text)
    
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        if self.backend == VectorBackend.QDRANT:
            # Qdrant 不支持批量，逐个处理
            from .embedding_router import get_embedding
            return [get_embedding(text) for text in texts]
        else:
            # 使用 Doji Memory 的批量处理
            return self.adapter.client.get_batch_embeddings(texts)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        if self.backend == VectorBackend.QDRANT:
            try:
                # 尝试获取集合信息
                from .qdrant_client import get_collection_info
                info = get_collection_info()
                return {
                    "backend": "qdrant",
                    "status": "healthy",
                    "collections": list(info.keys())
                }
            except Exception as e:
                return {
                    "backend": "qdrant",
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            try:
                # 检查 Doji Memory 服务
                is_healthy = self.adapter.client._health_check()
                return {
                    "backend": "doji_memory",
                    "status": "healthy" if is_healthy else "unhealthy",
                    "url": self.adapter.client.base_url
                }
            except Exception as e:
                return {
                    "backend": "doji_memory",
                    "status": "unhealthy",
                    "error": str(e)
                }


# 全局路由器实例
_hybrid_router = None

def get_hybrid_router(backend: VectorBackend = None, doji_url: str = None) -> HybridVectorRouter:
    """获取混合向量路由器实例
    
    Args:
        backend: 向量后端类型
        doji_url: Doji Memory URL
        
    Returns:
        HybridVectorRouter: 路由器实例
    """
    global _hybrid_router
    if _hybrid_router is None:
        _hybrid_router = HybridVectorRouter(backend, doji_url)
    return _hybrid_router

def switch_backend(backend: VectorBackend, doji_url: str = None) -> HybridVectorRouter:
    """切换向量后端
    
    Args:
        backend: 新的后端类型
        doji_url: Doji Memory URL（如果切换到 Doji Memory）
        
    Returns:
        HybridVectorRouter: 新的路由器实例
    """
    global _hybrid_router
    _hybrid_router = HybridVectorRouter(backend, doji_url)
    return _hybrid_router 