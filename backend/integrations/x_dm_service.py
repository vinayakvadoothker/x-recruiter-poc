"""
X DM Service for follow-up candidate information gathering.

This service sends DMs to candidates requesting additional information:
- Resume/CV
- arXiv author identifier
- GitHub handle
- LinkedIn URL
- Phone number
- Email address

Uses OAuth 2.0 User Context (Bearer token) for DM sending.
"""

import os
import logging
import json
import urllib.parse
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv
from pathlib import Path

from backend.integrations.api_utils import retry_with_backoff, handle_api_error
from backend.integrations.grok_api import GrokAPIClient

load_dotenv()
logger = logging.getLogger(__name__)

# Token file to persist refresh tokens (separate from .env)
TOKEN_FILE = Path(".x_refresh_token.json")


class XDMService:
    """
    Service for sending and receiving X DMs to gather candidate information.
    
    Uses OAuth 2.0 User Context (Bearer token) for DM sending.
    Uses Grok API for parsing DM responses.
    """
    
    # DM Templates
    RESUME_REQUEST = """Hi {name}! We're building your candidate profile and would love to include your resume. 
Could you paste your resume text here? (Just copy and paste the text directly) Thanks!"""

    ARXIV_ID_REQUEST = """Hi {name}! Do you have an arXiv author identifier? 
If so, please share it (e.g., https://arxiv.org/a/warner_s_1 or your ORCID: 0000-0002-7970-7855). 
This helps us find all your research papers!"""

    GITHUB_REQUEST = """Hi {name}! We'd like to add your GitHub profile to your candidate profile. 
What's your GitHub username?"""

    LINKEDIN_REQUEST = """Hi {name}! Could you share your LinkedIn profile URL? 
This helps us build a complete picture of your experience."""

    PHONE_REQUEST = """Hi {name}! We'd like to schedule a phone screen interview. 
Could you share your phone number? (format: +1234567890)"""

    EMAIL_REQUEST = """Hi {name}! Could you share your email address? 
This helps us contact you about opportunities."""

    def __init__(self):
        """
        Initialize X DM Service.
        
        Uses OAuth 2.0 User Context authentication (same as XAPIClient).
        Requires X_CLIENT_ID, X_CLIENT_SECRET, and X_OAUTH2_REFRESH_TOKEN.
        """
        # Store OAuth 2.0 credentials for token refresh
        self.oauth2_client_id = os.getenv("X_CLIENT_ID")
        self.oauth2_client_secret = os.getenv("X_CLIENT_SECRET")
        # Load refresh token from token file first, fallback to .env
        self.oauth2_refresh_token = self._load_refresh_token()
        
        if not all([self.oauth2_client_id, self.oauth2_client_secret, self.oauth2_refresh_token]):
            raise ValueError(
                "X API OAuth 2.0 User Context credentials required for DM sending. "
                "Set X_CLIENT_ID, X_CLIENT_SECRET, and X_OAUTH2_REFRESH_TOKEN environment variables. "
                "To get initial tokens, run: python scripts/get_x_oauth2_token.py"
        )
        
        self.base_url = "https://api.x.com/2"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.grok_client = GrokAPIClient()
        
        logger.info("XDMService initialized with OAuth 2.0 User Context")
    
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
    
    async def _get_oauth2_access_token(self, force_refresh: bool = True) -> str:
        """
        Get OAuth 2.0 User Context access token, refreshing if needed.
        
        Args:
            force_refresh: If True, always refresh token (default: True)
        
        Returns:
            OAuth 2.0 User Context access token
        
        Raises:
            ValueError: If token cannot be obtained
        """
        # Always get the latest refresh token (from token file or memory)
        current_refresh_token = self._load_refresh_token() or self.oauth2_refresh_token
        
        # Always refresh on every request if we have refresh token and client credentials
        if current_refresh_token and self.oauth2_client_id and self.oauth2_client_secret:
            # Temporarily update refresh token if it changed
            if current_refresh_token != self.oauth2_refresh_token:
                self.oauth2_refresh_token = current_refresh_token
            
            new_token = await self._refresh_oauth2_token()
            if new_token:
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
                    "Run 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                )
        
        # Fallback to .env access token
        oauth2_access_token = os.getenv("X_OAUTH2_ACCESS_TOKEN")
        if oauth2_access_token:
            logger.debug("Using existing access token from .env (refresh may have been skipped)")
            return oauth2_access_token
        
        # Provide detailed error message
        missing = []
        if not self.oauth2_client_id:
            missing.append("X_CLIENT_ID")
        if not self.oauth2_client_secret:
            missing.append("X_CLIENT_SECRET")
        if not current_refresh_token:
            missing.append("X_OAUTH2_REFRESH_TOKEN")
        
        error_msg = "X API OAuth 2.0 User Context access token required for DM sending.\n"
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
                
                if response.status_code == 200:
                    token_data = response.json()
                    new_access_token = token_data.get("access_token")
                    new_refresh_token = token_data.get("refresh_token")
                    
                    # Save new refresh token if provided (X API may rotate it)
                    if new_refresh_token and new_refresh_token != self.oauth2_refresh_token:
                        self.oauth2_refresh_token = new_refresh_token
                        self._save_refresh_token(new_refresh_token)
                        logger.info("Saved new refresh token from X API")
                    
                    return new_access_token
                else:
                    logger.error(f"Failed to refresh OAuth 2.0 token: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error refreshing OAuth 2.0 token: {e}")
            return None
    
    async def create_dm_conversation(self, participant_id: str, message: str) -> Optional[str]:
        """
        Create a new DM conversation with a participant.
        
        Uses X API endpoint: POST /2/dm_conversations/with/{participant_id}/messages
        This endpoint automatically creates a conversation if one doesn't exist.
        
        Args:
            participant_id: X user ID of the participant
            message: Initial message text
        
        Returns:
            Conversation ID if successful, None otherwise
        """
        # Validate participant_id
        if not participant_id:
            logger.error("Participant ID is required but was not provided.")
            return None
        
        # Use send_dm_by_participant_id which uses the correct endpoint
        result = await self.send_dm_by_participant_id(participant_id, message)
        if result:
            conversation_id = result.get("dm_conversation_id")
            if conversation_id:
                logger.info(f"Created DM conversation {conversation_id} with participant {participant_id}")
            return conversation_id
        return None
    
    async def _get_authenticated_user_id(self, access_token: str) -> Optional[str]:
        """
        Get the authenticated user's ID using OAuth 2.0 token.
        
        Args:
            access_token: OAuth 2.0 access token
        
        Returns:
            User ID of the authenticated user, or None if failed
        """
        try:
            url = f"{self.base_url}/users/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            response = await self.client.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("data", {}).get("id")
                if user_id:
                    logger.debug(f"Authenticated user ID: {user_id}")
                return user_id
            else:
                logger.warning(f"Failed to get authenticated user ID: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.warning(f"Error getting authenticated user ID: {e}")
            return None
    
    async def send_dm_by_participant_id(self, participant_id: str, message: str) -> Optional[Dict]:
        """
        Send a DM to a participant by their user ID.
        
        Creates a new DM conversation if one doesn't exist.
        Uses X API endpoint: POST /2/dm_conversations/with/{participant_id}/messages
        
        Args:
            participant_id: X user ID of the recipient
            message: Message text to send
        
        Returns:
            Message data with dm_conversation_id and dm_event_id if successful, None otherwise
        """
        # Get OAuth 2.0 access token
        oauth2_access_token = await self._get_oauth2_access_token(force_refresh=True)
        
        # Validate participant_id
        if not participant_id:
            logger.error("Participant ID is required but was not provided.")
            return None
        
        # Use the endpoint for sending DM by participant ID
        # This endpoint automatically creates a conversation if one doesn't exist
        url = f"{self.base_url}/dm_conversations/with/{participant_id}/messages"
        headers = {
            "Authorization": f"Bearer {oauth2_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": message
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload, timeout=30)
            
            # If we get 401, try refreshing token and retry once
            if response.status_code == 401:
                logger.info("Got 401, attempting to refresh OAuth 2.0 token and retry...")
                try:
                    refreshed_token = await self._get_oauth2_access_token(force_refresh=True)
                    if refreshed_token and refreshed_token != oauth2_access_token:
                        headers["Authorization"] = f"Bearer {refreshed_token}"
                        response = await self.client.post(url, headers=headers, json=payload, timeout=30)
                        response.raise_for_status()
                    else:
                        response.raise_for_status()
                except httpx.HTTPStatusError as refresh_error:
                    logger.error(f"Token refresh failed after 401: {refresh_error}")
                    raise ValueError(
                        "Failed to send DM: Authentication failed. "
                        "The OAuth 2.0 access token is invalid and refresh failed. "
                        "Run 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                    ) from refresh_error
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Sent DM to participant {participant_id}")
                result = data.get("data", {})
                # X API returns dm_conversation_id and dm_event_id in the response
                # Store both for future reference
                if result.get("dm_conversation_id"):
                    logger.debug(f"Created DM conversation {result['dm_conversation_id']}")
                return result
            elif response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_detail = error_data.get("detail", response.text)
                logger.error(
                    f"Failed to send DM (403 Forbidden): {error_detail}. "
                    f"Recipient: {participant_id}. "
                    f"This may indicate: (1) Invalid user ID, (2) Recipient has DMs disabled, "
                    f"(3) Users don't follow each other (if required), or (4) Other privacy restrictions."
                )
                # Don't raise - return None so caller can handle gracefully
                return None
            else:
                logger.error(f"Failed to send DM: {response.status_code} - {response.text}")
                response.raise_for_status()
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending DM: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error sending DM: {e}", exc_info=True)
            return None
    
    async def send_dm_by_conversation_id(self, conversation_id: str, message: str) -> Optional[Dict]:
        """
        Send a DM to an existing conversation by conversation ID.
        
        Uses X API endpoint: POST /2/dm_conversations/:dm_conversation_id/messages
        
        Args:
            conversation_id: DM conversation ID (from previous create_dm_conversation or send_dm_by_participant_id)
            message: Message text to send
        
        Returns:
            Message data with dm_conversation_id and dm_event_id if successful, None otherwise
        """
        # Get OAuth 2.0 access token
        oauth2_access_token = await self._get_oauth2_access_token(force_refresh=True)
        
        url = f"{self.base_url}/dm_conversations/{conversation_id}/messages"
        headers = {
            "Authorization": f"Bearer {oauth2_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": message
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload, timeout=30)
            
            # If we get 401, try refreshing token and retry once
            if response.status_code == 401:
                logger.info("Got 401, attempting to refresh OAuth 2.0 token and retry...")
                try:
                    refreshed_token = await self._get_oauth2_access_token(force_refresh=True)
                    if refreshed_token and refreshed_token != oauth2_access_token:
                        headers["Authorization"] = f"Bearer {refreshed_token}"
                        response = await self.client.post(url, headers=headers, json=payload, timeout=30)
                        response.raise_for_status()
                    else:
                        response.raise_for_status()
                except httpx.HTTPStatusError as refresh_error:
                    logger.error(f"Token refresh failed after 401: {refresh_error}")
                    raise ValueError(
                        "Failed to send DM: Authentication failed. "
                        "The OAuth 2.0 access token is invalid and refresh failed. "
                        "Run 'python scripts/get_x_oauth2_token.py' to get new tokens via OAuth flow."
                    ) from refresh_error
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Sent DM to conversation {conversation_id}")
                return data.get("data", {})
            else:
                logger.error(f"Failed to send DM: {response.status_code} - {response.text}")
                response.raise_for_status()
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending DM: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error sending DM: {e}", exc_info=True)
            return None
    
    async def get_dm_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get DM conversation details including messages.
        
        Uses X API endpoint: GET /2/dm_conversations/:dm_conversation_id/dm_events
        
        Args:
            conversation_id: DM conversation ID
        
        Returns:
            Conversation data with messages if successful, None otherwise
        """
        # Get OAuth 2.0 access token
        oauth2_access_token = await self._get_oauth2_access_token(force_refresh=True)
        
        # Use the correct endpoint for retrieving DM events
        url = f"{self.base_url}/dm_conversations/{conversation_id}/dm_events"
        headers = {
            "Authorization": f"Bearer {oauth2_access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dm_event.fields": "id,text,created_at,dm_conversation_id,participant_ids,sender_id",
            "max_results": 50
        }
        
        try:
            response = await self.client.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved DM events for conversation {conversation_id}")
                # X API returns data in format: {"data": {"dm_events": [...]}}
                return data.get("data", {})
            elif response.status_code == 404:
                logger.warning(f"DM conversation {conversation_id} not found (404). It may have been deleted or the ID is incorrect.")
                return None
            else:
                logger.error(f"Failed to get DM conversation: {response.status_code} - {response.text}")
                # Don't raise for 404, just return None
                if response.status_code != 404:
                    response.raise_for_status()
                return None
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"DM conversation {conversation_id} not found (404)")
            else:
                logger.error(f"HTTP error getting DM conversation: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting DM conversation: {e}", exc_info=True)
            return None
    
    async def request_resume(self, participant_id: str, name: str) -> Optional[Dict]:
        """Send a DM requesting resume."""
        message = self.RESUME_REQUEST.format(name=name)
        return await self.send_dm_by_participant_id(participant_id, message)
    
    async def request_arxiv_id(self, participant_id: str, name: str) -> Optional[Dict]:
        """Send a DM requesting arXiv author identifier."""
        message = self.ARXIV_ID_REQUEST.format(name=name)
        return await self.send_dm_by_participant_id(participant_id, message)
    
    async def request_github_handle(self, participant_id: str, name: str) -> Optional[Dict]:
        """Send a DM requesting GitHub handle."""
        message = self.GITHUB_REQUEST.format(name=name)
        return await self.send_dm_by_participant_id(participant_id, message)
    
    async def request_linkedin_url(self, participant_id: str, name: str) -> Optional[Dict]:
        """Send a DM requesting LinkedIn URL."""
        message = self.LINKEDIN_REQUEST.format(name=name)
        return await self.send_dm_by_participant_id(participant_id, message)
    
    async def request_phone_number(self, participant_id: str, name: str) -> Optional[Dict]:
        """Send a DM requesting phone number."""
        message = self.PHONE_REQUEST.format(name=name)
        return await self.send_dm_by_participant_id(participant_id, message)
    
    async def request_email(self, participant_id: str, name: str) -> Optional[Dict]:
        """Send a DM requesting email address."""
        message = self.EMAIL_REQUEST.format(name=name)
        return await self.send_dm_by_participant_id(participant_id, message)
    
    async def parse_dm_response(self, message_text: str, requested_field: str) -> Optional[Dict]:
        """
        Parse a DM response to extract requested information using Grok.
        
        Args:
            message_text: The DM message text from the candidate
            requested_field: What was requested ("resume", "arxiv_id", "github_handle", etc.)
        
        Returns:
            Extracted data dictionary, or None if parsing fails
        """
        prompt = f"""Extract the requested information from this candidate's DM response.

Requested field: {requested_field}
Candidate's message: {message_text}

Extract the information and return it in JSON format. For each field type:
- "resume": Extract the full resume text content (plain text, not URLs). The candidate pasted their resume text directly.
- "arxiv_id": Extract arXiv author identifier (format: "warner_s_1" or ORCID "0000-0002-7970-7855")
- "github_handle": Extract GitHub username (without @)
- "linkedin_url": Extract LinkedIn profile URL
- "phone_number": Extract phone number (normalize to +1234567890 format)
- "email": Extract email address

Return JSON with the extracted field(s). If not found, return null for that field.
Example: {{"github_handle": "username"}} or {{"arxiv_id": "warner_s_1"}} or {{"resume": "Full resume text here..."}}
"""
        
        try:
            # Use Grok chat completion for better parsing
            result = await self.grok_client.extract_entities_with_grok(
                prompt,
                entity_types=[requested_field]  # Only extract the requested field
            )
            
            # Parse the JSON response from Grok
            if isinstance(result, dict):
                # If resume, ensure we have the full text
                if requested_field == "resume" and "resume" in result:
                    # The resume should be the full text content
                    return {"resume_text": result.get("resume") or result.get("resume_text")}
                return result
            elif isinstance(result, str):
                import json
                try:
                    parsed = json.loads(result)
                    # Handle resume field
                    if requested_field == "resume" and "resume" in parsed:
                        return {"resume_text": parsed.get("resume")}
                    return parsed
                except:
                    # If it's a resume and not JSON, return the text directly
                    if requested_field == "resume":
                        return {"resume_text": result}
                    return {"raw_text": result}
            else:
                # If resume and result is None, try to extract from message_text
                if requested_field == "resume":
                    # For resume, if Grok fails, return the message text itself
                    return {"resume_text": message_text}
                return None
                
        except Exception as e:
            logger.error(f"Error parsing DM response with Grok: {e}")
            # Fallback: for resume, return the message text
            if requested_field == "resume":
                return {"resume_text": message_text}
            return None
    
    async def check_dm_responses(self, participant_id: str) -> List[Dict]:
        """
        Check for DM responses from a participant.
        
        Note: This is a simplified version. In production, you'd want to:
        - Store conversation IDs
        - Poll for new messages
        - Track which messages have been processed
        
        Args:
            participant_id: X user ID of the participant
        
        Returns:
            List of DM messages from the participant
        """
        # First, try to get or create conversation
        # For now, we'll use the participant-based endpoint
        # In production, you'd store conversation IDs
        
        # This is a placeholder - X API doesn't have a direct "get all DMs from user" endpoint
        # You'd need to maintain conversation state or use webhooks
        logger.warning("check_dm_responses: Full implementation requires conversation state tracking")
        return []
    
    async def request_missing_fields(
        self,
        participant_id: str,
        name: str,
        candidate_profile: Dict
    ) -> Dict[str, Optional[Dict]]:
        """
        Automatically request missing fields from a candidate profile.
        
        Args:
            participant_id: X user ID of the candidate
            name: Candidate's name
            candidate_profile: Current candidate profile
        
        Returns:
            Dictionary mapping field names to DM send results
        """
        results = {}
        
        # Check what's missing and request it
        if not candidate_profile.get("resume_text") and not candidate_profile.get("resume_url"):
            logger.info(f"Requesting resume from {name}")
            results["resume"] = await self.request_resume(participant_id, name)
        
        if not candidate_profile.get("arxiv_author_id"):
            logger.info(f"Requesting arXiv ID from {name}")
            results["arxiv_id"] = await self.request_arxiv_id(participant_id, name)
        
        if not candidate_profile.get("github_handle"):
            logger.info(f"Requesting GitHub handle from {name}")
            results["github_handle"] = await self.request_github_handle(participant_id, name)
        
        if not candidate_profile.get("linkedin_url"):
            logger.info(f"Requesting LinkedIn URL from {name}")
            results["linkedin_url"] = await self.request_linkedin_url(participant_id, name)
        
        if not candidate_profile.get("phone_number"):
            logger.info(f"Requesting phone number from {name}")
            results["phone_number"] = await self.request_phone_number(participant_id, name)
        
        if not candidate_profile.get("email"):
            logger.info(f"Requesting email from {name}")
            results["email"] = await self.request_email(participant_id, name)
        
        return results
    
    async def close(self):
        """Close any open connections."""
        await self.client.aclose()
        await self.grok_client.close()

