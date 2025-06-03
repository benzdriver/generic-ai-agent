# src/vector_engine/vector_indexer.py

"""
向量索引器：负责向量数据的存储和索引
基于doji_memory系统，提供与Qdrant相同的接口
"""

import sys
import os
sys.path.append('/home/ubuntu/repos/doji_memory')

import uuid
import requests
from typing import Optional, Dict, Any, List
from src.vector_engine.embedding_router import get_embedding
from src.config.env_manager import init_config
from vector.memory_writer import write_memory, write_memories_batch

# 初始化配置
config = init_config()

def get_client():
    """获取Weaviate客户端（兼容Qdrant接口）"""
    return "doji_memory_client"

def upsert_documents(paragraphs: list, metadata: Optional[Dict[str, Any]] = None):
    """上传文档到向量数据库
    
    Args:
        paragraphs: 文档段落列表
        metadata: 元数据字典，包含项目、仓库等信息
    """
    if not paragraphs:
        return
    
    default_metadata = {
        "project": "documents",
        "repo": "main",
        "agent": "indexer",
        "tags": ["document"],
        "source": "indexer"
    }
    
    if metadata:
        if "collection" in metadata:
            collection_to_project = {
                "canonical_queries": "canonical",
                "conversations": "conversations",
                "documents": "documents", 
                "merged_knowledge": "merged"
            }
            default_metadata["project"] = collection_to_project.get(
                metadata["collection"], metadata["collection"]
            )
        
        if "project" in metadata:
            default_metadata["project"] = metadata["project"]
        if "repo" in metadata:
            default_metadata["repo"] = metadata["repo"]
        if "agent" in metadata:
            default_metadata["agent"] = metadata["agent"]
        if "tags" in metadata:
            if isinstance(metadata["tags"], list):
                default_metadata["tags"] = metadata["tags"]
            else:
                default_metadata["tags"] = [str(metadata["tags"])]
        if "source" in metadata:
            default_metadata["source"] = metadata["source"]
    
    memories = []
    for paragraph in paragraphs:
        memory = {
            "content": paragraph,
            "project": default_metadata["project"],
            "repo": default_metadata["repo"],
            "agent": default_metadata["agent"],
            "tags": default_metadata["tags"],
            "source": default_metadata["source"]
        }
        memories.append(memory)
    
    try:
        uuids = write_memories_batch(memories)
        print(f"✅ 成功索引 {len(uuids)} 个文档段落到项目: {default_metadata['project']}")
        return uuids
    except Exception as e:
        print(f"❌ 文档索引失败: {str(e)}")
        raise
