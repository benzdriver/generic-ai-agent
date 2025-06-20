"""
Change Detection for Incremental Updates
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional
import aiohttp

from core.models import UpdateCheck

logger = logging.getLogger(__name__)

class ChangeDetector:
    """
    Detects changes in web content
    """
    
    def __init__(self):
        self.session = None
        
    async def check_url(self, url: str) -> UpdateCheck:
        """
        Check if URL content has changed
        """
        try:
            # Get current content hash
            current_hash = await self._get_content_hash(url)
            
            # Get stored hash (in production from database)
            stored_hash = await self._get_stored_hash(url)
            
            # Compare
            has_changed = current_hash != stored_hash if stored_hash else True
            
            # Determine change type
            change_type = None
            if has_changed:
                if stored_hash is None:
                    change_type = 'new'
                else:
                    change_type = 'content'
            
            return UpdateCheck(
                url=url,
                has_changed=has_changed,
                change_type=change_type,
                old_hash=stored_hash,
                new_hash=current_hash,
                checked_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error checking {url}: {e}")
            return UpdateCheck(
                url=url,
                has_changed=False,
                change_type='error',
                checked_at=datetime.utcnow()
            )
    
    async def _get_content_hash(self, url: str) -> str:
        """Get hash of current content"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(url) as response:
            content = await response.text()
            
            # Simple content hash
            return hashlib.sha256(content.encode()).hexdigest()
    
    async def _get_stored_hash(self, url: str) -> Optional[str]:
        """Get stored hash from database"""
        # Simplified - in production would query database
        return None
    
    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()