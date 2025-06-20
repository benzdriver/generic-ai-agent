"""
URL utilities
"""

from urllib.parse import urlparse, urljoin, urlunparse
from typing import Optional
import re

def normalize_url(url: str) -> Optional[str]:
    """Normalize URL"""
    try:
        parsed = urlparse(url)
        
        # Ensure scheme
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        
        # Remove fragment
        normalized = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, 
             parsed.params, parsed.query, '')
        )
        
        # Remove trailing slash
        if normalized.endswith('/'):
            normalized = normalized[:-1]
        
        return normalized
    except Exception:
        return None

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except Exception:
        return False

def should_crawl_url(url: str, base_domain: str, config) -> bool:
    """Determine if URL should be crawled"""
    
    parsed = urlparse(url)
    
    # Check domain
    if config.allowed_domains:
        if parsed.netloc not in config.allowed_domains:
            return False
    elif parsed.netloc != base_domain:
        # By default, stay on same domain
        return False
    
    # Check exclude patterns
    if config.exclude_patterns:
        for pattern in config.exclude_patterns:
            if re.search(pattern, url):
                return False
    
    # Check include patterns
    if config.include_patterns:
        for pattern in config.include_patterns:
            if re.search(pattern, url):
                return True
        return False  # If include patterns specified, must match one
    
    return True