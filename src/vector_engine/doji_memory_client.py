"""
Doji Memory 客户端适配器

这个模块提供了与 Doji Memory REST API 的集成，
同时保持与现有 Qdrant 客户端兼容的接口
"""

import os
import uuid
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from src.config.env_manager import init_config

# 初始化配置
config = init_config(test_mode=False)

class DojiMemoryClient:
    """Doji Memory API 客户端"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """初始化 Doji Memory 客户端
        
        Args:
            base_url: Doji Memory API 基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or os.getenv('DOJI_MEMORY_URL', 'http://localhost:8000')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GenericAIAgent/1.0'
        })
        
        # 健康检查
        self._health_check()
    
    def _health_check(self) -> bool:
        """检查 Doji Memory 服务是否可用"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            if response.status_code == 200:
                print(f"✅ Doji Memory 服务连接成功: {self.base_url}")
                return True
            else:
                print(f"⚠️ Doji Memory 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到 Doji Memory 服务: {str(e)}")
            return False
    
    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """获取文本的向量表示
        
        Args:
            text: 输入文本
            use_cache: 是否使用缓存
            
        Returns:
            List[float]: 向量表示
        """
        try:
            response = self.session.post(
                f"{self.base_url}/embedding",
                json={
                    "text": text,
                    "use_cache": use_cache
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["vector"]
        except Exception as e:
            print(f"❌ 获取向量失败: {str(e)}")
            raise
    
    def get_batch_embeddings(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """批量获取文本的向量表示
        
        Args:
            texts: 文本列表
            use_cache: 是否使用缓存
            
        Returns:
            List[List[float]]: 向量列表
        """
        try:
            response = self.session.post(
                f"{self.base_url}/embedding/batch",
                json={
                    "texts": texts,
                    "use_cache": use_cache
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["vectors"]
        except Exception as e:
            print(f"❌ 批量获取向量失败: {str(e)}")
            raise
    
    def store_memory(self, content: str, project: str = "generic-ai-agent", 
                    repo: str = "main", agent: str = "system", 
                    tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """存储内存到 Doji Memory
        
        Args:
            content: 内容文本
            project: 项目名称
            repo: 仓库名称
            agent: 代理标识
            tags: 标签列表
            metadata: 额外元数据
            
        Returns:
            str: 存储的UUID
        """
        try:
            payload = {
                "content": content,
                "project": project,
                "repo": repo,
                "agent": agent,
                "tags": tags or [],
            }
            
            if metadata:
                payload.update(metadata)
            
            response = self.session.post(
                f"{self.base_url}/memory",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["uuid"]
        except Exception as e:
            print(f"❌ 存储内存失败: {str(e)}")
            raise
    
    def search_memory(self, query: str, project: str = "generic-ai-agent", 
                     limit: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """搜索相关内存
        
        Args:
            query: 查询文本
            project: 项目名称
            limit: 结果数量限制
            threshold: 相似度阈值
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            response = self.session.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "project": project,
                    "limit": limit,
                    "threshold": threshold
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["results"]
        except Exception as e:
            print(f"❌ 搜索内存失败: {str(e)}")
            raise
    
    def batch_store_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """批量存储内存
        
        Args:
            memories: 内存列表，每个包含 content, project, repo, agent, tags 等字段
            
        Returns:
            List[str]: 存储的UUID列表
        """
        try:
            response = self.session.post(
                f"{self.base_url}/memory/batch",
                json={"memories": memories},
                timeout=self.timeout * 2  # 批量操作需要更长时间
            )
            response.raise_for_status()
            return response.json()["uuids"]
        except Exception as e:
            print(f"❌ 批量存储内存失败: {str(e)}")
            raise


class DojiMemoryAdapter:
    """Doji Memory 适配器，提供与 Qdrant 兼容的接口"""
    
    def __init__(self, doji_url: str = None):
        """初始化适配器
        
        Args:
            doji_url: Doji Memory 服务URL
        """
        self.client = DojiMemoryClient(doji_url)
        self.project = "generic-ai-agent"
        
        # 集合映射 - 将 Qdrant 集合名称映射到 Doji Memory 的项目/仓库
        self.collection_mapping = {
            "canonical_queries": {"project": "generic-ai-agent", "repo": "canonical"},
            "conversations": {"project": "generic-ai-agent", "repo": "conversations"},
            "documents": {"project": "generic-ai-agent", "repo": "documents"},
            "merged_knowledge": {"project": "generic-ai-agent", "repo": "merged"}
        }
    
    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """插入或更新点数据（兼容 Qdrant 接口）
        
        Args:
            collection_name: 集合名称
            points: 点数据列表
        """
        mapping = self.collection_mapping.get(collection_name, {
            "project": self.project,
            "repo": collection_name
        })
        
        memories = []
        for point in points:
            payload = point.get("payload", {})
            memory = {
                "content": payload.get("text", ""),
                "project": mapping["project"],
                "repo": mapping["repo"],
                "agent": payload.get("agent", "system"),
                "tags": payload.get("tags", []),
                "metadata": {
                    "point_id": point.get("id"),
                    "created_at": payload.get("created_at", datetime.now().timestamp()),
                    **payload
                }
            }
            memories.append(memory)
        
        try:
            uuids = self.client.batch_store_memories(memories)
            print(f"✅ 成功存储 {len(uuids)} 条记录到 {collection_name}")
        except Exception as e:
            print(f"❌ 存储到 {collection_name} 失败: {str(e)}")
            raise
    
    def search(self, collection_name: str, query_vector: List[float] = None, 
              query_text: str = None, limit: int = 5, 
              query_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索相似向量（兼容 Qdrant 接口）
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量（暂时不支持）
            query_text: 查询文本
            limit: 结果数量限制
            query_filter: 查询过滤条件
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        if not query_text:
            raise ValueError("Doji Memory 适配器目前需要查询文本")
        
        mapping = self.collection_mapping.get(collection_name, {
            "project": self.project,
            "repo": collection_name
        })
        
        try:
            results = self.client.search_memory(
                query=query_text,
                project=mapping["project"],
                limit=limit
            )
            
            # 转换为 Qdrant 兼容格式
            compatible_results = []
            for result in results:
                compatible_result = {
                    "payload": {
                        "text": result.get("content", ""),
                        "score": result.get("score", 0.0),
                        **result.get("metadata", {})
                    },
                    "score": result.get("score", 0.0)
                }
                compatible_results.append(compatible_result)
            
            return compatible_results
        except Exception as e:
            print(f"❌ 搜索 {collection_name} 失败: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本向量（兼容接口）
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 向量表示
        """
        return self.client.get_embedding(text)


# 全局适配器示例
_doji_adapter = None

def get_doji_adapter(doji_url: str = None) -> DojiMemoryAdapter:
    """获取 Doji Memory 适配器实例"""
    global _doji_adapter
    if _doji_adapter is None:
        _doji_adapter = DojiMemoryAdapter(doji_url)
    return _doji_adapter 