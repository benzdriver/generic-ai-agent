# src/vector_engine/retriever.py

"""
检索器：负责相似向量的检索
"""

from vector_engine.embedding_router import get_embedding
from vector_engine.qdrant_client import get_client, COLLECTION_NAME

def retrieve_relevant_chunks(query: str, limit: int = 5) -> list:
    """检索相关文本块"""
    client = get_client()
    query_vector = get_embedding(query)
    
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit
    )
    
    return [hit.payload for hit in results]

