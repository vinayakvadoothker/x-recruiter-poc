"""
X API client for candidate data gathering.

This module provides integration with X (Twitter) API v2 for gathering
candidate profile information, tweets, and extracting links.
"""

import os
import logging
import urllib.parse
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv

from backend.integrations.api_utils import retry_with_backoff, handle_api_error

load_dotenv()
logger = logging.getLogger(__name__)


class XAPIClient:
    """
    Client for interacting with X (Twitter) API v2.
    
    Uses Bearer Token authentication for read-only endpoints.
    Provides methods to get user profiles, tweets, and extract links.
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize X API client.
        
        Args:
            bearer_token: X API Bearer Token. If not provided, reads from X_BEARER_TOKEN env var.
        
        Raises:
            ValueError: If bearer token is not provided or found in environment
        """
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError(
                "X API Bearer Token required. Set X_BEARER_TOKEN environment variable or pass bearer_token parameter."
            )
        
        # Decode URL-encoded bearer token if needed
        if "%" in self.bearer_token:
            self.bearer_token = urllib.parse.unquote(self.bearer_token)
        
        self.base_url = "https://api.x.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("XAPIClient initialized")
    
    async def get_profile(self, username: str) -> Dict:
        """
        Get profile information for an X user by username.
        
        Uses X API v2 endpoint: GET /2/users/by/username/:username
        
        Args:
            username: X username (without @)
        
        Returns:
            User profile dictionary with:
            - id: User ID
            - name: Display name (REQUIRED for candidate schema)
            - username: X username
            - description: Bio/description
            - location: Location
            - url: Website URL
            - public_metrics: Followers, following, tweet counts
            - created_at: Account creation date
        
        Raises:
            ValueError: If user not found or API error
        """
        # Remove @ if present
        username = username.lstrip("@")
        
        url = f"{self.base_url}/users/by/username/{username}"
        params = {
            "user.fields": "id,name,username,description,location,url,public_metrics,created_at,profile_image_url"
        }
        
        try:
            response = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            if "data" not in response:
                logger.warning(f"X API returned no data for username: {username}")
                return {}
            
            profile = response["data"]
            logger.info(f"Retrieved X profile for {username}: {profile.get('name', 'Unknown')}")
            return profile
            
        except Exception as e:
            logger.error(f"Error getting X profile for {username}: {e}")
            raise ValueError(f"Failed to get X profile for {username}: {e}")
    
    async def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 500,
        exclude_replies: bool = True,
        exclude_retweets: bool = True
    ) -> List[Dict]:
        """
        Get user's recent tweets.
        
        Uses X API v2 endpoint: GET /2/users/:id/tweets
        
        Args:
            user_id: X user ID (not username)
            max_results: Maximum number of tweets to retrieve (default: 500, max: 500 per request, can paginate for more)
            exclude_replies: Exclude reply tweets (default: True)
            exclude_retweets: Exclude retweets (default: True)
        
        Returns:
            List of tweet dictionaries with:
            - id: Tweet ID
            - text: Tweet content
            - created_at: Tweet timestamp
            - public_metrics: Engagement metrics
            - entities: URLs, mentions, hashtags
        """
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": min(max_results, 100),  # API limit is 100 per request, but we paginate
            "tweet.fields": "id,text,created_at,public_metrics,entities,lang,possibly_sensitive,referenced_tweets,context_annotations,author_id,conversation_id,in_reply_to_user_id",
            "exclude": []
        }
        
        if exclude_replies:
            params["exclude"].append("replies")
        if exclude_retweets:
            params["exclude"].append("retweets")
        
        if params["exclude"]:
            params["exclude"] = ",".join(params["exclude"])
        else:
            del params["exclude"]
        
        all_tweets = []
        next_token = None
        
        try:
            while len(all_tweets) < max_results:
                if next_token:
                    params["pagination_token"] = next_token
                
                response = await retry_with_backoff(
                    self._make_get_request,
                    url=url,
                    params=params
                )
                
                if "data" in response:
                    tweets = response["data"]
                    all_tweets.extend(tweets)
                    logger.debug(f"Retrieved {len(tweets)} tweets (total: {len(all_tweets)})")
                
                # Check for pagination
                if "meta" in response and "next_token" in response["meta"]:
                    next_token = response["meta"]["next_token"]
                else:
                    break
                
                # Stop if we have enough tweets
                if len(all_tweets) >= max_results:
                    break
            
            logger.info(f"Retrieved {len(all_tweets)} tweets for user {user_id}")
            return all_tweets[:max_results]
            
        except Exception as e:
            logger.error(f"Error getting tweets for user {user_id}: {e}")
            return []
    
    async def search_users(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for X users by query.
        
        Uses X API v2 endpoint: GET /2/users/search
        
        Args:
            query: Search query string
            max_results: Maximum number of users to return (default: 10, max: 100)
        
        Returns:
            List of user profile dictionaries
        """
        url = f"{self.base_url}/users/search"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "user.fields": "id,name,username,description,location,url,public_metrics"
        }
        
        try:
            response = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            if "data" in response:
                return response["data"]
            return []
            
        except Exception as e:
            logger.error(f"Error searching X users with query '{query}': {e}")
        return []
    
    def extract_links_from_tweets(self, tweets: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract links from tweets (GitHub, LinkedIn, arXiv).
        
        Args:
            tweets: List of tweet dictionaries
        
        Returns:
            Dictionary with:
            - github_handles: List of GitHub usernames
            - linkedin_urls: List of LinkedIn URLs
            - arxiv_ids: List of arXiv paper IDs
        """
        github_handles = []
        linkedin_urls = []
        arxiv_ids = []
        
        for tweet in tweets:
            text = tweet.get("text", "")
            entities = tweet.get("entities", {})
            urls = entities.get("urls", [])
            
            # Extract from tweet text and URLs
            for url_obj in urls:
                expanded_url = url_obj.get("expanded_url", "") or url_obj.get("url", "")
                
                # GitHub links
                if "github.com" in expanded_url:
                    # Extract username from github.com/username or github.com/username/repo
                    parts = expanded_url.split("github.com/")
                    if len(parts) > 1:
                        path = parts[1].split("/")[0].split("?")[0]
                        if path and path not in github_handles:
                            github_handles.append(path)
                
                # LinkedIn links
                if "linkedin.com" in expanded_url:
                    if expanded_url not in linkedin_urls:
                        linkedin_urls.append(expanded_url)
                
                # arXiv links
                if "arxiv.org" in expanded_url:
                    # Extract arXiv ID (format: arxiv.org/abs/YYYY.NNNNN)
                    if "/abs/" in expanded_url:
                        arxiv_id = expanded_url.split("/abs/")[-1].split("?")[0]
                        if arxiv_id and arxiv_id not in arxiv_ids:
                            arxiv_ids.append(arxiv_id)
            
            # Also check tweet text for mentions
            if "github.com" in text.lower():
                import re
                github_pattern = r"github\.com/([\w-]+)"
                matches = re.findall(github_pattern, text, re.IGNORECASE)
                github_handles.extend(matches)
        
        # Remove duplicates
        github_handles = list(set(github_handles))
        linkedin_urls = list(set(linkedin_urls))
        arxiv_ids = list(set(arxiv_ids))
        
        logger.info(f"Extracted links: {len(github_handles)} GitHub, {len(linkedin_urls)} LinkedIn, {len(arxiv_ids)} arXiv")
        
        return {
            "github_handles": github_handles,
            "linkedin_urls": linkedin_urls,
            "arxiv_ids": arxiv_ids
        }
    
    async def _make_get_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to X API.
        
        Args:
            url: Full URL to request
            params: Query parameters
        
        Returns:
            Response dictionary from API
        """
        response = await self.client.get(url, headers=self.headers, params=params)
        handle_api_error(response, "X API request failed")
        return response.json()
    
    async def create_post(self, text: str) -> Dict:
        """
        Create a post on X (Twitter).
        
        Uses X API v2 endpoint: POST /2/tweets
        Requires OAuth 1.0a authentication (not Bearer Token).
        
        Args:
            text: Post text content (max 280 characters)
        
        Returns:
            Dictionary with created post data including post ID
        
        Raises:
            ValueError: If post creation fails
        """
        # For posting, we need OAuth 1.0a (like DM service)
        # This requires different credentials than Bearer Token
        from requests_oauthlib import OAuth1
        import requests
        
        api_key = os.getenv("X_API_KEY")
        api_secret = os.getenv("X_API_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        
        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError(
                "X API OAuth 1.0a credentials required for posting. "
                "Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET environment variables."
            )
        
        oauth = OAuth1(
            api_key,
            client_secret=api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
            signature_method='HMAC-SHA1',
            signature_type='AUTH_HEADER'
        )
        
        url = f"{self.base_url}/tweets"
        payload = {
            "text": text
        }
        
        try:
            response = requests.post(url, auth=oauth, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Created X post: {result.get('data', {}).get('id', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Error creating X post: {e}")
            raise ValueError(f"Failed to create X post: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

