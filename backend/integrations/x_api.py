"""
X API client stub for future integration.

This is a placeholder for X (Twitter) API integration.
Not needed for hackathon MVP, but prepared for future use.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class XAPIClient:
    """
    Client for interacting with X (Twitter) API.
    
    Currently a stub - to be implemented when X API access is available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize X API client stub.
        
        Args:
            api_key: X API key (not used in stub)
        """
        logger.warning("XAPIClient is a stub - not yet implemented")
        self.api_key = api_key
    
    async def search_profiles(self, query: str) -> List[Dict]:
        """
        Search for X profiles by query.
        
        Args:
            query: Search query string
        
        Returns:
            Empty list (stub implementation)
        """
        logger.warning("X API search_profiles not yet implemented")
        return []
    
    async def get_profile(self, username: str) -> Dict:
        """
        Get profile information for an X user.
        
        Args:
            username: X username (without @)
        
        Returns:
            Empty dictionary (stub implementation)
        """
        logger.warning("X API get_profile not yet implemented")
        return {}
    
    async def send_dm(self, user_id: str, message: str) -> bool:
        """
        Send a direct message to an X user.
        
        Args:
            user_id: X user ID
            message: Message text
        
        Returns:
            False (stub implementation)
        """
        logger.warning("X API send_dm not yet implemented")
        return False

