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
            "Authorization": f"Bearer {self.token}",  # Use Bearer for fine-grained tokens
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
        per_page: int = 100,
        max_repos: int = 100
    ) -> List[Dict]:
        """
        Get repositories for a GitHub user (with pagination).
        
        Args:
            username: GitHub username
            sort: Sort order ("updated", "created", "stars", "forks")
            per_page: Number of repos per page (max 100)
            max_repos: Maximum number of repos to retrieve
        
        Returns:
            List of repository dictionaries
        """
        all_repos = []
        page = 1
        
        while len(all_repos) < max_repos:
        url = f"{self.base_url}/users/{username}/repos"
        params = {
            "sort": sort,
            "per_page": min(per_page, 100),
                "page": page,
                "type": "all"  # Get all repos (public, private if accessible)
        }
        
        try:
            repos = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            # Handle both list and paginated responses
            if isinstance(repos, list):
                    page_repos = repos
            else:
                    page_repos = repos.get("items", [])
                
                if not page_repos:
                    break
                
                all_repos.extend(page_repos)
                
                # If we got fewer than per_page, we're done
                if len(page_repos) < per_page:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error getting repos for {username} (page {page}): {e}")
                break
        
        logger.info(f"Retrieved {len(all_repos)} repos for {username}")
        return all_repos[:max_repos]
    
    async def get_repo_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Get README content for a repository.
        
        Tries multiple README filenames: README.md, README, README.txt, etc.
        
        Args:
            owner: Repository owner username
            repo: Repository name
        
        Returns:
            README content as string, or None if not found
        """
        readme_names = ["README.md", "README", "README.txt", "readme.md", "readme"]
        
        for readme_name in readme_names:
            try:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{readme_name}"
                response = await retry_with_backoff(
                    self._make_get_request,
                    url=url
                )
                
                # GitHub returns base64 encoded content
                if response.get("content"):
                    import base64
                    content = base64.b64decode(response["content"]).decode('utf-8', errors='ignore')
                    logger.info(f"Retrieved README for {owner}/{repo}")
                    return content
                    
            except Exception as e:
                # Try next README name
                continue
        
        logger.debug(f"No README found for {owner}/{repo}")
        return None
    
    async def get_repo_code_search(
        self,
        owner: str,
        repo: str,
        query: str,
        language: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for relevant code in a repository.
        
        Uses GitHub Code Search API to find relevant code snippets.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            query: Search query (e.g., "embedding", "vector similarity")
            language: Optional language filter (e.g., "python")
        
        Returns:
            List of code search results with file paths and snippets
        """
        search_query = f"{query} in:file repo:{owner}/{repo}"
        if language:
            search_query += f" language:{language}"
        
        url = f"{self.base_url}/search/code"
        params = {"q": search_query}
        
        # Use text-match format for code snippets
        headers = {
            **self.headers,
            "Accept": "application/vnd.github.text-match+json"
        }
        
        try:
            response = await retry_with_backoff(
                self._make_get_request_with_headers,
                url=url,
                params=params,
                headers=headers
            )
            
            items = response.get("items", [])
            logger.info(f"Found {len(items)} code matches for {query} in {owner}/{repo}")
            return items
            
        except Exception as e:
            logger.error(f"Error searching code in {owner}/{repo}: {e}")
            return []
    
    async def _make_get_request_with_headers(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """
        Make a GET request with custom headers.
        
        Args:
            url: Full URL to request
            params: Query parameters
            headers: Custom headers (merged with default headers)
        
        Returns:
            Response dictionary from API
        """
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)
        
        response = await self.client.get(url, headers=request_headers, params=params)
        handle_api_error(response, "GitHub API request failed")
        return response.json()
    
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

