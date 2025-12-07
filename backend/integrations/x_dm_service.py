"""
X DM Service for follow-up candidate information gathering.

This service sends DMs to candidates requesting additional information:
- Resume/CV
- arXiv author identifier
- GitHub handle
- LinkedIn URL
- Phone number
- Email address

Uses OAuth 1.0a for DM sending (requires Access Token + Secret).
"""

import os
import logging
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv
from requests_oauthlib import OAuth1
import requests

from backend.integrations.api_utils import retry_with_backoff, handle_api_error
from backend.integrations.grok_api import GrokAPIClient

load_dotenv()
logger = logging.getLogger(__name__)


class XDMService:
    """
    Service for sending and receiving X DMs to gather candidate information.
    
    Uses OAuth 1.0a authentication for DM sending (requires Access Token + Secret).
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

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None
    ):
        """
        Initialize X DM Service.
        
        Args:
            api_key: X API Consumer Key. If not provided, reads from X_API_KEY env var.
            api_secret: X API Consumer Secret. If not provided, reads from X_API_SECRET env var.
            access_token: X API Access Token. If not provided, reads from X_ACCESS_TOKEN env var.
            access_token_secret: X API Access Token Secret. If not provided, reads from X_ACCESS_TOKEN_SECRET env var.
        
        Raises:
            ValueError: If required credentials are not provided
        """
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError(
                "X API OAuth 1.0a credentials required for DM sending. "
                "Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET environment variables."
            )
        
        # Set up OAuth 1.0a authentication
        self.oauth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
            signature_method='HMAC-SHA1',
            signature_type='AUTH_HEADER'
        )
        
        self.base_url = "https://api.x.com/2"
        self.grok_client = GrokAPIClient()
        
        logger.info("XDMService initialized with OAuth 1.0a")
    
    async def create_dm_conversation(self, participant_id: str) -> Optional[str]:
        """
        Create a new DM conversation with a participant.
        
        Args:
            participant_id: X user ID of the participant
        
        Returns:
            Conversation ID if successful, None otherwise
        """
        url = f"{self.base_url}/dm_conversations"
        payload = {
            "participant_id": participant_id
        }
        
        try:
            # Use asyncio to run synchronous requests in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    auth=self.oauth,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            )
            
            if response.status_code == 201:
                data = response.json()
                conversation_id = data.get("data", {}).get("dm_conversation_id")
                logger.info(f"Created DM conversation {conversation_id} with participant {participant_id}")
                return conversation_id
            else:
                logger.error(f"Failed to create DM conversation: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating DM conversation: {e}")
            return None
    
    async def send_dm_by_participant_id(self, participant_id: str, message: str) -> Optional[Dict]:
        """
        Send a DM to a participant by their user ID.
        
        Uses X API endpoint: POST /2/dm_conversations/with/:participant_id/messages
        
        Args:
            participant_id: X user ID of the recipient
            message: Message text to send
        
        Returns:
            Message data if successful, None otherwise
        """
        url = f"{self.base_url}/dm_conversations/with/{participant_id}/messages"
        payload = {
            "text": message
        }
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    auth=self.oauth,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Sent DM to participant {participant_id}")
                return data.get("data", {})
            else:
                logger.error(f"Failed to send DM: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending DM: {e}")
            return None
    
    async def send_dm_by_conversation_id(self, conversation_id: str, message: str) -> Optional[Dict]:
        """
        Send a DM to a conversation by conversation ID.
        
        Uses X API endpoint: POST /2/dm_conversations/:dm_conversation_id/messages
        
        Args:
            conversation_id: DM conversation ID
            message: Message text to send
        
        Returns:
            Message data if successful, None otherwise
        """
        url = f"{self.base_url}/dm_conversations/{conversation_id}/messages"
        payload = {
            "text": message
        }
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    auth=self.oauth,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Sent DM to conversation {conversation_id}")
                return data.get("data", {})
            else:
                logger.error(f"Failed to send DM: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending DM: {e}")
            return None
    
    async def get_dm_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get DM conversation details including messages.
        
        Uses X API endpoint: GET /2/dm_conversations/:dm_conversation_id
        
        Args:
            conversation_id: DM conversation ID
        
        Returns:
            Conversation data with messages if successful, None otherwise
        """
        url = f"{self.base_url}/dm_conversations/{conversation_id}"
        params = {
            "dm_event.fields": "id,text,created_at,dm_conversation_id,participant_id,sender_id",
            "max_results": 50
        }
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    url,
                    auth=self.oauth,
                    params=params
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved DM conversation {conversation_id}")
                return data.get("data", {})
            else:
                logger.error(f"Failed to get DM conversation: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting DM conversation: {e}")
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
        await self.grok_client.close()

