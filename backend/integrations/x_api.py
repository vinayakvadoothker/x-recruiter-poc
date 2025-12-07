"""
X API client for candidate data gathering.

This module provides integration with X (Twitter) API v2 for gathering
candidate profile information, tweets, and extracting links.
"""

import os
import logging
import urllib.parse
import json
import asyncio
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv
from pathlib import Path

from backend.integrations.api_utils import retry_with_backoff, handle_api_error

load_dotenv()
logger = logging.getLogger(__name__)

# Token file to persist refresh tokens (separate from .env)
TOKEN_FILE = Path(".x_refresh_token.json")


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
                          For OAuth 2.0 User Context operations, uses X_OAUTH2_ACCESS_TOKEN.
        
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
        
        # Store OAuth 2.0 credentials for token refresh
        self.oauth2_client_id = os.getenv("X_CLIENT_ID")
        self.oauth2_client_secret = os.getenv("X_CLIENT_SECRET")
        # Load refresh token from token file first, fallback to .env
        self.oauth2_refresh_token = self._load_refresh_token()
        
        self.base_url = "https://api.x.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("XAPIClient initialized")
    
    def _load_refresh_token(self) -> Optional[str]:
        """
        Load refresh token from token file first, then fallback to .env.
        
        Returns:
            Refresh token if found, None otherwise
        """
        # Try token file first (most up-to-date)
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                    refresh_token = token_data.get("refresh_token")
                    if refresh_token:
                        logger.debug(f"Loaded refresh token from {TOKEN_FILE}")
                        return refresh_token
            except Exception as e:
                logger.warning(f"Failed to load refresh token from {TOKEN_FILE}: {e}")
        
        # Fallback to .env
        refresh_token = os.getenv("X_OAUTH2_REFRESH_TOKEN")
        if refresh_token:
            logger.debug("Loaded refresh token from .env")
        return refresh_token
    
    def _save_refresh_token(self, refresh_token: str) -> None:
        """
        Save refresh token to token file for persistence across restarts.
        
        Args:
            refresh_token: The refresh token to save
        """
        try:
            from datetime import datetime
            token_data = {
                "refresh_token": refresh_token,
                "updated_at": datetime.now().isoformat()
            }
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f, indent=2)
            logger.debug(f"Saved refresh token to {TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save refresh token to {TOKEN_FILE}: {e}")
    
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
    
    async def _get_oauth2_access_token(self, force_refresh: bool = True) -> str:
        """
        Get OAuth 2.0 User Context access token, ALWAYS refreshing on every request.
        
        This method ALWAYS refreshes the token before each request to ensure we have
        a fresh, valid token. X API may rotate refresh tokens, so we always use the
        latest refresh token from memory.
        
        Args:
            force_refresh: If True, always refresh token (default: True)
        
        Returns:
            OAuth 2.0 User Context access token
        
        Raises:
            ValueError: If token cannot be obtained
        """
        # Check what credentials we have
        has_client_id = bool(self.oauth2_client_id)
        has_client_secret = bool(self.oauth2_client_secret)
        # Always get the latest refresh token (from token file or memory)
        current_refresh_token = self._load_refresh_token() or self.oauth2_refresh_token
        has_refresh_token = bool(current_refresh_token)
        
        # ALWAYS refresh on every request if we have refresh token and client credentials
        # This ensures we always have a fresh, valid token and handle token rotation
        if has_refresh_token and has_client_id and has_client_secret:
            # Temporarily update refresh token if it changed
            if current_refresh_token != self.oauth2_refresh_token:
                self.oauth2_refresh_token = current_refresh_token
            
            new_token = await self._refresh_oauth2_token()
            if new_token:
                # Update the token in environment for this process
                os.environ["X_OAUTH2_ACCESS_TOKEN"] = new_token
                logger.debug("Automatically refreshed OAuth 2.0 access token on request")
                return new_token
            else:
                # Refresh returned None - refresh token is likely invalid
                logger.error("Token refresh returned None - refresh token may be invalid")
                # Try using existing access token as fallback (if set)
                oauth2_access_token = os.getenv("X_OAUTH2_ACCESS_TOKEN")
                if oauth2_access_token:
                    logger.warning("Using existing access token as fallback (refresh failed)")
                    return oauth2_access_token
                # If no fallback, raise error
                raise ValueError(
                    "Failed to refresh OAuth 2.0 token - refresh token appears to be invalid or expired. "
                    "Run 'python scripts/auto_refresh_x_tokens.py' to attempt automatic refresh, "
                    "or 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                )
        
        # This shouldn't be reached if refresh works, but keep as safety fallback
        # (Access token is optional in .env since we generate it on each request)
        oauth2_access_token = os.getenv("X_OAUTH2_ACCESS_TOKEN")
        if oauth2_access_token:
            logger.debug("Using existing access token from .env (refresh may have been skipped)")
            return oauth2_access_token
        
        # Provide detailed error message about what's missing
        missing = []
        if not has_client_id:
            missing.append("X_CLIENT_ID")
        if not has_client_secret:
            missing.append("X_CLIENT_SECRET")
        if not has_refresh_token:
            missing.append("X_OAUTH2_REFRESH_TOKEN")
        
        error_msg = "X API OAuth 2.0 User Context access token required.\n"
        if missing:
            error_msg += f"Missing environment variables: {', '.join(missing)}\n"
        error_msg += "To get initial tokens, run: python scripts/get_x_oauth2_token.py\n"
        error_msg += "This will use your X_CLIENT_ID and X_CLIENT_SECRET to obtain X_OAUTH2_REFRESH_TOKEN."
        
        raise ValueError(error_msg)
    
    async def _refresh_oauth2_token(self) -> Optional[str]:
        """
        Refresh OAuth 2.0 access token using refresh token.
        
        Returns:
            New access token if refresh successful, None otherwise
        """
        if not all([self.oauth2_client_id, self.oauth2_client_secret, self.oauth2_refresh_token]):
            return None
        
        try:
            import base64
            import httpx
            
            # X API uses Basic Auth with client_id:client_secret
            credentials = f"{self.oauth2_client_id}:{self.oauth2_client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            url = "https://api.x.com/2/oauth2/token"
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "refresh_token": self.oauth2_refresh_token,
                "grant_type": "refresh_token"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data, timeout=30)
                
                # Log error details for debugging
                if response.status_code != 200:
                    try:
                        error_body = response.text
                        logger.error(f"Token refresh failed with status {response.status_code}: {error_body}")
                    except:
                        pass
                
                response.raise_for_status()
                result = response.json()
                
                new_access_token = result.get("access_token")
                new_refresh_token = result.get("refresh_token")
                
                if new_access_token:
                    logger.info("Successfully refreshed OAuth 2.0 access token")
                    # Update refresh token if a new one was provided (X API may rotate it)
                    if new_refresh_token and new_refresh_token != self.oauth2_refresh_token:
                        self.oauth2_refresh_token = new_refresh_token
                        os.environ["X_OAUTH2_REFRESH_TOKEN"] = new_refresh_token
                        # Save to token file for persistence across restarts
                        self._save_refresh_token(new_refresh_token)
                        logger.debug("Updated refresh token (X API rotated token)")
                    return new_access_token
                else:
                    logger.warning("Token refresh response did not contain access_token")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error refreshing OAuth 2.0 token: {e.response.status_code}")
            if e.response is not None:
                try:
                    error_body = e.response.text
                    logger.error(f"Error response body: {error_body}")
                    
                    # Check for specific error types
                    if e.response.status_code == 400:
                        try:
                            error_json = e.response.json()
                            error_desc = error_json.get("error_description", "")
                            if "invalid" in error_desc.lower() or "invalid_request" in error_json.get("error", ""):
                                logger.error(
                                    "Refresh token appears to be invalid or expired. "
                                    "Run 'python scripts/auto_refresh_x_tokens.py' to attempt automatic refresh, "
                                    "or 'python scripts/get_x_oauth2_token.py' to get new tokens."
                                )
                                # Return None so caller knows refresh failed
                                return None
                        except:
                            pass
                except:
                    pass
            # Return None on HTTP errors
            return None
        except Exception as e:
            logger.error(f"Error refreshing OAuth 2.0 token: {e}")
            # Return None on any other errors
            return None
    
    async def create_post(self, text: str) -> Dict:
        """
        Create a post on X (Twitter).
        
        Uses X API v2 endpoint: POST /2/tweets
        Requires OAuth 2.0 User Context authentication (Bearer token from PKCE flow).
        Automatically refreshes token if needed using X_CLIENT_ID, X_CLIENT_SECRET, and X_OAUTH2_REFRESH_TOKEN.
        
        Args:
            text: Post text content (max 280 characters)
        
        Returns:
            Dictionary with created post data including post ID
        
        Raises:
            ValueError: If post creation fails
        """
        # Get OAuth 2.0 User Context access token (always refresh before each request)
        oauth2_access_token = await self._get_oauth2_access_token(force_refresh=True)
        
        url = f"{self.base_url}/tweets"
        headers = {
            "Authorization": f"Bearer {oauth2_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload, timeout=30)
            
            # If we get 401, try refreshing token and retry once
            if response.status_code == 401:
                logger.info("Got 401, attempting to refresh OAuth 2.0 token and retry...")
                try:
                    # Force refresh when we get 401
                    refreshed_token = await self._get_oauth2_access_token(force_refresh=True)
                    if refreshed_token and refreshed_token != oauth2_access_token:
                        os.environ["X_OAUTH2_ACCESS_TOKEN"] = refreshed_token
                        headers["Authorization"] = f"Bearer {refreshed_token}"
                        response = await self.client.post(url, headers=headers, json=payload, timeout=30)
                        response.raise_for_status()
                    else:
                        # Refresh failed or returned same token, raise original 401
                        logger.error(
                            "Unable to refresh OAuth 2.0 token. "
                            "The refresh token may be invalid or expired. "
                            "Run 'python scripts/auto_refresh_x_tokens.py' to attempt automatic refresh, "
                            "or 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                        )
                        response.raise_for_status()
                except httpx.HTTPStatusError as refresh_error:
                    # If refresh also fails, provide helpful error
                    logger.error(f"Token refresh failed after 401: {refresh_error}")
                    # Log response details for debugging
                    try:
                        error_body = response.text
                        logger.error(f"401 Response body: {error_body}")
                    except:
                        pass
                    raise ValueError(
                        "Failed to create X post: Authentication failed. "
                        "The OAuth 2.0 access token is invalid and refresh failed. "
                        "Run 'python scripts/auto_refresh_x_tokens.py' to attempt automatic refresh, "
                        "or 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                    ) from refresh_error
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed after 401: {refresh_error}")
                    # Log response details for debugging
                    try:
                        error_body = response.text
                        logger.error(f"401 Response body: {error_body}")
                    except:
                        pass
                    raise ValueError(
                        "Failed to create X post: Authentication failed. "
                        "Run 'python scripts/auto_refresh_x_tokens.py' to attempt automatic refresh, "
                        "or 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                    ) from refresh_error
            else:
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created X post: {result.get('data', {}).get('id', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Error creating X post: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise ValueError(f"Failed to create X post: {e}")
    
    async def get_post_replies(self, post_id: str, max_results: int = 100) -> List[Dict]:
        """
        Get replies to a specific X post.
        
        Uses X API v2 endpoint: GET /2/tweets/search/recent with conversation_id filter
        Requires OAuth 2.0 User Context authentication (Bearer token from PKCE flow).
        
        Args:
            post_id: X post/tweet ID
            max_results: Maximum number of replies to retrieve (default: 100)
        
        Returns:
            List of reply dictionaries with:
            - id: Reply tweet ID
            - text: Reply text
            - author_id: User ID who replied
            - author_username: Username who replied
            - created_at: Reply timestamp
            - public_metrics: Engagement metrics
        """
        # Use OAuth 2.0 User Context token (from PKCE flow) for getting replies
        # Don't force refresh on every call to avoid excessive token refreshes during bulk operations
        # Token will be refreshed automatically if expired (401) or if missing
        try:
            token = await self._get_oauth2_access_token(force_refresh=False)
        except ValueError:
            logger.warning("X_OAUTH2_ACCESS_TOKEN not set, falling back to X_BEARER_TOKEN for replies")
            token = self.bearer_token
        
        try:
            # First, get the original tweet to get conversation_id
            tweet_url = f"{self.base_url}/tweets/{post_id}"
            tweet_params = {
                "tweet.fields": "id,text,author_id,conversation_id,created_at"
            }
            
            # Use OAuth 2.0 User Context token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            tweet_response = await self.client.get(tweet_url, headers=headers, params=tweet_params)
            
            # Handle rate limiting (429) before calling handle_api_error
            if tweet_response.status_code == 429:
                # Log all response headers and body for debugging
                logger.error("=" * 60)
                logger.error("X API Rate Limit (429) - Response Details (GET tweet):")
                logger.error("=" * 60)
                logger.error(f"Status Code: {tweet_response.status_code}")
                logger.error(f"Response Headers:")
                for header_name, header_value in tweet_response.headers.items():
                    logger.error(f"  {header_name}: {header_value}")
                try:
                    error_body = tweet_response.text
                    logger.error(f"Response Body: {error_body}")
                except:
                    logger.error("Response Body: (could not read)")
                logger.error("=" * 60)
                raise ValueError("X API rate limit (429): Too Many Requests. Please wait before trying again.")
            
            handle_api_error(tweet_response, "X API request failed")
            tweet_data = tweet_response.json()
            
            if "data" not in tweet_data:
                logger.warning(f"Could not find tweet {post_id}")
                return []
            
            conversation_id = tweet_data["data"].get("conversation_id", post_id)
            
            # Search for replies using conversation_id
            # Use the search endpoint to find all tweets in the conversation
            search_url = f"{self.base_url}/tweets/search/recent"
            search_params = {
                "query": f"conversation_id:{conversation_id}",
                "max_results": min(max_results, 100),
                "tweet.fields": "id,text,author_id,created_at,public_metrics,in_reply_to_user_id,referenced_tweets",
                "expansions": "author_id",
                "user.fields": "id,name,username"
            }
            
            search_response = await self.client.get(search_url, headers=headers, params=search_params)
            
            # Handle rate limiting (429) with retry
            if search_response.status_code == 429:
                # Log all response headers and body for debugging
                logger.error("=" * 60)
                logger.error("X API Rate Limit (429) - Response Details:")
                logger.error("=" * 60)
                logger.error(f"Status Code: {search_response.status_code}")
                logger.error(f"Response Headers:")
                for header_name, header_value in search_response.headers.items():
                    logger.error(f"  {header_name}: {header_value}")
                try:
                    error_body = search_response.text
                    logger.error(f"Response Body: {error_body}")
                except:
                    logger.error("Response Body: (could not read)")
                logger.error("=" * 60)
                
                # Check for Retry-After header
                retry_after = search_response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_time = int(retry_after)
                        logger.warning(f"Rate limited (429). Waiting {wait_time} seconds as specified by Retry-After header")
                        await asyncio.sleep(wait_time)
                        # Retry the request
                        search_response = await self.client.get(search_url, headers=headers, params=search_params)
                    except ValueError:
                        # Invalid Retry-After, use default
                        logger.warning("Rate limited (429). Waiting 15 seconds before retry...")
                        await asyncio.sleep(15)
                        search_response = await self.client.get(search_url, headers=headers, params=search_params)
                else:
                    # No Retry-After header, use default backoff
                    logger.warning("Rate limited (429). No Retry-After header found. Waiting 15 seconds before retry...")
                    await asyncio.sleep(15)
                    search_response = await self.client.get(search_url, headers=headers, params=search_params)
                
                # If still 429 after retry, raise error with all details
                if search_response.status_code == 429:
                    logger.error("Still rate limited (429) after retry. All response details:")
                    for header_name, header_value in search_response.headers.items():
                        logger.error(f"  {header_name}: {header_value}")
                    raise ValueError("X API rate limit (429): Too Many Requests. Please wait before trying again.")
            
            # If we get 401, try refreshing token and retry once
            if search_response.status_code == 401 and token != self.bearer_token:
                logger.info("Got 401 on replies search, attempting to refresh OAuth 2.0 token and retry...")
                try:
                    refreshed_token = await self._refresh_oauth2_token()
                    if refreshed_token:
                        os.environ["X_OAUTH2_ACCESS_TOKEN"] = refreshed_token
                        headers["Authorization"] = f"Bearer {refreshed_token}"
                        search_response = await self.client.get(search_url, headers=headers, params=search_params)
                    else:
                        handle_api_error(search_response, "X API search request failed")
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed: {refresh_error}")
                    handle_api_error(search_response, "X API search request failed")
            else:
                handle_api_error(search_response, "X API search request failed")
            
            search_data = search_response.json()
            
            replies = []
            if "data" in search_data:
                # Filter to only replies (not the original tweet)
                for tweet in search_data["data"]:
                    # Check if this is a reply (has referenced_tweets with type "replied_to")
                    ref_tweets = tweet.get("referenced_tweets", [])
                    is_reply = any(ref.get("type") == "replied_to" for ref in ref_tweets)
                    
                    if is_reply and tweet.get("id") != post_id:
                        # Get author info from includes
                        author_id = tweet.get("author_id")
                        author_info = {}
                        if "includes" in search_data and "users" in search_data["includes"]:
                            author_info = next(
                                (u for u in search_data["includes"]["users"] if u.get("id") == author_id),
                                {}
                            )
                        
                        replies.append({
                            "id": tweet.get("id"),
                            "text": tweet.get("text", ""),
                            "author_id": author_id,
                            "author_username": author_info.get("username", ""),
                            "author_name": author_info.get("name", ""),
                            "created_at": tweet.get("created_at"),
                            "public_metrics": tweet.get("public_metrics", {})
                        })
            
            logger.info(f"Retrieved {len(replies)} replies for post {post_id}")
            return replies
            
        except Exception as e:
            logger.error(f"Error getting replies for post {post_id}: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

