"""
GitHub API client for candidate sourcing.

Provides functionality to search for users, get profiles, and analyze repositories.
"""

import os
import logging
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv

from backend.integrations.api_utils import retry_with_backoff, handle_api_error

load_dotenv()
logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """
    Client for interacting with GitHub API.
    
    Provides user search, profile retrieval, and repository analysis.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client.
        
        Args:
            token: GitHub personal access token. If not provided, reads from GITHUB_TOKEN env var.
        
        Raises:
            ValueError: If token is not provided or found in environment
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN environment variable or pass token parameter."
            )
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_users(
        self,
        query: str,
        language: Optional[str] = None,
        topics: Optional[List[str]] = None,
        per_page: int = 30
    ) -> List[Dict]:
        """
        Search for GitHub users by query, language, and topics.
        
        Args:
            query: Search query string
            language: Programming language filter (e.g., "Python", "JavaScript")
            topics: List of repository topics to filter by
            per_page: Number of results per page (max 100)
        
        Returns:
            List of user dictionaries with profile information
        """
        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"
        if topics:
            for topic in topics:
                search_query += f" topic:{topic}"
        
        url = f"{self.base_url}/search/users"
        params = {
            "q": search_query,
            "per_page": min(per_page, 100),
            "page": 1
        }
        
        try:
            response = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            users = response.get("items", [])
            logger.info(f"Found {len(users)} users matching query: {query}")
            return users
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    async def get_user_profile(self, username: str) -> Dict:
        """
        Get detailed profile information for a GitHub user.
        
        Args:
            username: GitHub username
        
        Returns:
            Dictionary with user profile data
        
        Raises:
            ValueError: If user not found or API request fails
        """
        url = f"{self.base_url}/users/{username}"
        
        try:
            profile = await retry_with_backoff(
                self._make_get_request,
                url=url
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile for {username}: {e}")
            raise ValueError(f"Failed to get profile for {username}: {e}")
    
    async def get_user_repos(
        self,
        username: str,
        sort: str = "updated",
        per_page: int = 30
    ) -> List[Dict]:
        """
        Get repositories for a GitHub user.
        
        Args:
            username: GitHub username
            sort: Sort order ("updated", "created", "stars", "forks")
            per_page: Number of repos per page (max 100)
        
        Returns:
            List of repository dictionaries
        """
        url = f"{self.base_url}/users/{username}/repos"
        params = {
            "sort": sort,
            "per_page": min(per_page, 100),
            "page": 1
        }
        
        try:
            repos = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            # Handle both list and paginated responses
            if isinstance(repos, list):
                return repos
            else:
                return repos.get("items", [])
            
        except Exception as e:
            logger.error(f"Error getting repos for {username}: {e}")
            return []
    
    async def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Get language statistics for a repository.
        
        Args:
            owner: Repository owner username
            repo: Repository name
        
        Returns:
            Dictionary mapping language names to bytes of code
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        
        try:
            languages = await retry_with_backoff(
                self._make_get_request,
                url=url
            )
            
            return languages if isinstance(languages, dict) else {}
            
        except Exception as e:
            logger.error(f"Error getting languages for {owner}/{repo}: {e}")
            return {}
    
    async def _make_get_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to GitHub API.
        
        Args:
            url: Full URL to request
            params: Query parameters
        
        Returns:
            Response dictionary from API
        """
        response = await self.client.get(url, headers=self.headers, params=params)
        handle_api_error(response, "GitHub API request failed")
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

