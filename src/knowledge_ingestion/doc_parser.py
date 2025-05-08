# src/knowledge_ingestion/doc_parser.py

import os
import re
from bs4 import BeautifulSoup
import uuid
import datetime
from typing import Dict, Any
from vector_engine.embedding_router import get_embedding
from vector_engine.qdrant_client import DOCUMENT_COLLECTION, get_client


def parse_ircc_html(file_path: str) -> list:
    """
    将 IRCC 政策 HTML 页面解析为段落列表（每段可供嵌入）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    raw_text = soup.get_text(separator="\n")
    paragraphs = [p.strip() for p in raw_text.split("\n") if len(p.strip()) > 40]
    return paragraphs


def parse_ircc_text(file_path: str) -> list:
    """
    将 IRCC 政策纯文本解析为逻辑段落
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    # 分段：以两个换行为段落切分
    chunks = [chunk.strip() for chunk in re.split(r'\n{2,}', raw) if len(chunk.strip()) > 40]
    return chunks


def store_document(content: str, metadata: Dict[str, Any]):
    """存储文档到知识库
    
    Args:
        content: 文档内容
        metadata: 文档元数据，包含 source, doc_type 等信息
    """
    client = get_client()
    doc_point = {
        "id": str(uuid.uuid4()),
        "vector": get_embedding(content),
        "payload": {
            "content": content,
            "source": metadata.get("source", "unknown"),
            "doc_type": metadata.get("doc_type", "general"),
            "created_at": datetime.datetime.utcnow().isoformat(),
            **metadata
        }
    }
    
    client.upsert(
        collection_name=DOCUMENT_COLLECTION,
        points=[doc_point]
    )
    print(f"✅ 文档已存储到知识库：{metadata.get('source', 'unknown')}")


def parse_and_store_document(file_path: str, doc_type: str = "general"):
    """解析文档并存储
    
    Args:
        file_path: 文档路径
        doc_type: 文档类型
    """
    # TODO: 实现文档解析逻辑
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = {
        "source": file_path,
        "doc_type": doc_type,
    }
    
    store_document(content, metadata)
