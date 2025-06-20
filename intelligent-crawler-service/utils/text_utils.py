"""
Text processing utilities
"""

from typing import List
import re
from difflib import SequenceMatcher

def extract_key_sentences(text: str, num_sentences: int = 5) -> List[str]:
    """Extract key sentences from text"""
    # Simple sentence extraction
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Return first N sentences (simplified)
    return sentences[:num_sentences]

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    return SequenceMatcher(None, text1, text2).ratio()