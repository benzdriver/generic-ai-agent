import openai
import os
from typing import List, Optional
import numpy as np
from tenacity import retry, stop_after_attempt, wait_random_exponential
from src.app.utils.logging import get_logger

logger = get_logger(__name__)

# --- Configuration ---
# Use environment variables for API keys for better security
# Fallback to a dummy key for local testing without real API access
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "DUMMY_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Models - using an enum or a config file would be even better
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 2048  # Max batch size for OpenAI API

# --- Core Functions ---

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Generates an embedding for a given text using OpenAI's API.

    Args:
        text: The text to embed.
        model: The model to use for embedding.

    Returns:
        A list of floats representing the embedding.
    
    Raises:
        ValueError: If the input text is empty.
        Exception: For API errors after retries.
    """
    if not text:
        logger.warning("get_embedding called with empty text.")
        return []
        
    text = text.replace("\\n", " ")
    try:
        response = client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except openai.APIError as e:
        logger.error(f"OpenAI API error in get_embedding: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_embedding: {e}")
        raise

@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(3))
def get_embedding_batch(
    texts: List[str], 
    model: str = EMBEDDING_MODEL, 
    batch_size: int = EMBEDDING_BATCH_SIZE
) -> List[List[float]]:
    """
    Generates embeddings for a list of texts in batches.

    Args:
        texts: A list of texts to embed.
        model: The model to use.
        batch_size: The number of texts to process in a single API call.

    Returns:
        A list of embeddings, where each embedding is a list of floats.
    """
    if not texts:
        logger.warning("get_embedding_batch called with an empty list of texts.")
        return []

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # Sanitize batch inputs
        batch = [str(t).replace("\\n", " ") if t is not None else "" for t in batch]
        
        try:
            response = client.embeddings.create(input=batch, model=model)
            # Sort embeddings by original index to maintain order
            embeddings = sorted(response.data, key=lambda e: e.index)
            all_embeddings.extend([e.embedding for e in embeddings])
        except openai.APIError as e:
            logger.error(f"OpenAI API error in get_embedding_batch (batch starting at index {i}): {e}")
            # Pad with empty embeddings for the failed batch to maintain list size
            all_embeddings.extend([[] for _ in batch])
        except Exception as e:
            logger.error(f"An unexpected error occurred in get_embedding_batch: {e}")
            all_embeddings.extend([[] for _ in batch])
            
    return all_embeddings

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Calculates the cosine similarity between two vectors.

    Args:
        v1: The first vector.
        v2: The second vector.

    Returns:
        The cosine similarity, a value between -1 and 1.
    """
    if not v1 or not v2:
        return 0.0
    v1_np = np.array(v1)
    v2_np = np.array(v2)
    dot_product = np.dot(v1_np, v2_np)
    norm_v1 = np.linalg.norm(v1_np)
    norm_v2 = np.linalg.norm(v2_np)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return dot_product / (norm_v1 * norm_v2)

# --- Example Usage ---

async def example():
    """Example of using the embedding functions."""
    # Example for single embedding
    text1 = "What is the Start-up Visa Program in Canada?"
    embedding1 = get_embedding(text1)
    logger.info(f"Embedding for text 1 (len: {len(embedding1)}): {embedding1[:5]}...")

    # Example for batch embeddings
    texts = [
        "How do I apply for a visitor visa?",
        "What are the requirements for Express Entry?",
        "Tell me about the Provincial Nominee Program.",
        "This is an unrelated sentence about cars."
    ]
    embeddings = get_embedding_batch(texts)
    logger.info(f"Generated {len(embeddings)} embeddings in a batch.")

    # Calculate similarity
    if embedding1 and embeddings[0]:
        similarity = cosine_similarity(embedding1, embeddings[0])
        logger.info(f"Similarity between text1 and batch text 1: {similarity:.4f}")
    
    if embedding1 and embeddings[3]:
        similarity_low = cosine_similarity(embedding1, embeddings[3])
        logger.info(f"Similarity between text1 and unrelated text: {similarity_low:.4f}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(example()) 