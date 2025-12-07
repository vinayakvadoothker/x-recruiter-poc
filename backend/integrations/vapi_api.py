"""
Vapi API client for phone screen interviews.

This module provides integration with Vapi for conducting automated phone screen
interviews. Handles assistant creation, call management, and transcript retrieval.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
import httpx
from dotenv import load_dotenv

from backend.integrations.api_utils import retry_with_backoff, handle_api_error

load_dotenv()
logger = logging.getLogger(__name__)


class VapiAPIClient:
    """
    Client for interacting with Vapi API.
    
    Provides phone call management, assistant creation, and transcript retrieval
    for automated phone screen interviews.
    """
    
    def __init__(self, private_key: Optional[str] = None, phone_number_id: Optional[str] = None):
        """
        Initialize Vapi API client.
        
        Args:
            private_key: Vapi private API key. If not provided, reads from VAPI_PRIVATE_KEY env var.
            phone_number_id: Vapi phone number ID. If not provided, reads from VAPI_PHONE_NUMBER_ID env var.
        
        Raises:
            ValueError: If API key or phone number ID is not provided or found in environment
        """
        self.private_key = private_key or os.getenv("VAPI_PRIVATE_KEY")
        self.phone_number_id = phone_number_id or os.getenv("VAPI_PHONE_NUMBER_ID")
        
        if not self.private_key:
            raise ValueError(
                "Vapi private API key required. Set VAPI_PRIVATE_KEY environment variable or pass private_key parameter."
            )
        
        if not self.phone_number_id:
            raise ValueError(
                "Vapi phone number ID required. Set VAPI_PHONE_NUMBER_ID environment variable or pass phone_number_id parameter."
            )
        
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Cache for assistant IDs (keyed by position_id)
        self._assistant_cache: Dict[str, str] = {}
    
    async def create_or_get_assistant(
        self,
        position: Dict[str, Any],
        position_id: Optional[str] = None,
        candidate: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create or get assistant for a position.
        
        Creates an assistant programmatically with a position-specific system prompt.
        Caches assistant ID to avoid recreating for the same position.
        When candidate info is provided, creates a personalized assistant (not cached).
        
        Args:
            position: Position profile dictionary
            position_id: Optional position ID for caching (uses position['id'] if not provided)
            candidate: Optional candidate profile for personalization (if provided, assistant is not cached)
        
        Returns:
            Assistant ID string
        """
        # If candidate info is provided, don't cache (each candidate gets personalized assistant)
        if candidate:
            cache_key = None  # Don't use cache for personalized assistants
        else:
            cache_key = position_id or position.get('id', 'default')
            # Check cache first for non-personalized assistants
            if cache_key in self._assistant_cache:
                logger.info(f"Using cached assistant for position {cache_key}")
                return self._assistant_cache[cache_key]
        
        # Generate system prompt based on position
        system_prompt = self._generate_system_prompt(position, candidate)
        
        # Generate personalized first message
        candidate_name = candidate.get('name', 'there') if candidate else 'there'
        company = position.get('company', 'our company')
        position_title = position.get('title', 'position')
        
        # Hyper-personalized first message based on candidate background
        if candidate:
            papers = candidate.get('papers', [])
            repos = candidate.get('repos', [])
            research_contributions = candidate.get('research_contributions', [])
            
            if papers:
                first_message = f"Hi {candidate_name}, this is {company} calling about your phone screen for the {position_title} role. I've reviewed your research work - {len(papers)} papers is impressive. Are you available for a deep technical discussion now?"
            elif repos:
                github_handle = candidate.get('github_handle', 'your GitHub')
                first_message = f"Hi {candidate_name}, this is {company} calling about your phone screen for the {position_title} role. I've looked at your GitHub work - some interesting projects there. Are you available for a technical discussion now?"
            elif research_contributions:
                first_message = f"Hi {candidate_name}, this is {company} calling about your phone screen for the {position_title} role. I've reviewed your background - your work in {', '.join(research_contributions[:2])} caught my attention. Are you available for a technical discussion now?"
            else:
                domains = candidate.get('domains', [])
                if domains:
                    first_message = f"Hi {candidate_name}, this is {company} calling about your phone screen for the {position_title} role. I see you have expertise in {', '.join(domains[:2])}. Are you available for a deep technical discussion now?"
                else:
                    first_message = f"Hi {candidate_name}, this is {company} calling for your phone screen interview for the {position_title} role. This will be a technical deep-dive. Are you available to talk now?"
        else:
            first_message = f"Hi {candidate_name}, this is {company} calling for your phone screen interview for the {position_title} role. This will be a technical deep-dive. Are you available to talk now?"
        
        # Create assistant
        # Shorten name to max 40 characters (Vapi requirement)
        position_title = position.get('title', 'Position')
        assistant_name = f"Interviewer - {position_title}"[:40]
        
        assistant_data = {
            "name": assistant_name,
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.3,  # Lower temperature for more focused, technical responses
                "maxTokens": 800,  # Increased for longer, more detailed technical questions
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Default professional voice
            },
            "firstMessage": first_message,
            "endCallFunctionEnabled": True,
            "recordingEnabled": True
        }
        
        try:
            response = await retry_with_backoff(
                self._create_assistant,
                assistant_data=assistant_data
            )
            
            assistant_id = response.get("id")
            if not assistant_id:
                raise ValueError("Failed to create assistant: no ID returned")
            
            # Cache the assistant ID only if not personalized (no candidate info)
            if cache_key:
                self._assistant_cache[cache_key] = assistant_id
                logger.info(f"Created and cached assistant {assistant_id} for position {cache_key}")
            else:
                candidate_name = candidate.get('name', 'candidate') if candidate else 'candidate'
                logger.info(f"Created personalized assistant {assistant_id} for {candidate_name} (not cached)")
            
            return assistant_id
            
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            raise ValueError(f"Failed to create assistant: {e}")
    
    def _generate_system_prompt(self, position: Dict[str, Any], candidate: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate hyper-personalized, highly technical system prompt for assistant.
        
        Creates a deeply personalized interview script with hard-hitting technical questions
        based on candidate's specific background (arXiv papers, GitHub repos, X posts, etc.).
        
        Args:
            position: Position profile dictionary
            candidate: Optional candidate profile for personalization
        
        Returns:
            System prompt string
        """
        title = position.get('title', 'position')
        company = position.get('company', 'the company')
        # Ensure all fields are lists/strings, not None (PostgreSQL may return None or JSON strings)
        import json
        must_haves = position.get('must_haves') or []
        if not isinstance(must_haves, list):
            if isinstance(must_haves, str):
                try:
                    must_haves = json.loads(must_haves)
                except:
                    must_haves = []
            else:
                must_haves = []
        experience_level = position.get('experience_level') or ''
        domains = position.get('domains') or []
        if not isinstance(domains, list):
            if isinstance(domains, str):
                try:
                    domains = json.loads(domains)
                except:
                    domains = []
            else:
                domains = []
        skills = position.get('required_skills') or []
        if not isinstance(skills, list):
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = []
            else:
                skills = []
        
        # Get comprehensive candidate info for hyper-personalization
        candidate_name = candidate.get('name', 'the candidate') if candidate else 'the candidate'
        # Ensure candidate_skills is always a list (PostgreSQL may return None or JSON string)
        candidate_skills = candidate.get('skills', []) if candidate else []
        if not isinstance(candidate_skills, list):
            if isinstance(candidate_skills, str):
                import json
                try:
                    candidate_skills = json.loads(candidate_skills)
                except:
                    candidate_skills = []
            else:
                candidate_skills = []
        candidate_experience = candidate.get('experience_years', 0) if candidate else 0
        candidate_domains = candidate.get('domains', []) if candidate else []
        if not isinstance(candidate_domains, list):
            if isinstance(candidate_domains, str):
                import json
                try:
                    candidate_domains = json.loads(candidate_domains)
                except:
                    candidate_domains = []
            else:
                candidate_domains = []
        
        # Get arXiv research for deep technical questions
        papers = candidate.get('papers', []) if candidate else []
        research_contributions = candidate.get('research_contributions', []) if candidate else []
        arxiv_author_id = candidate.get('arxiv_author_id') if candidate else None
        
        # Get GitHub repos for technical depth
        repos = candidate.get('repos', []) if candidate else []
        github_handle = candidate.get('github_handle') if candidate else None
        
        # Get X posts for recent work
        posts = candidate.get('posts', []) if candidate else []
        
        # Build hyper-personalized prompt
        prompt = f"""You are conducting a DEEP TECHNICAL phone screen interview for {company} for a {title} role.

CANDIDATE PROFILE - USE THIS FOR HYPER-PERSONALIZED QUESTIONS:
- Name: {candidate_name}
"""
        
        if candidate_skills:
            prompt += f"- Known skills: {', '.join(candidate_skills[:10])}\n"
        
        if candidate_experience:
            prompt += f"- Years of experience: {candidate_experience}\n"
        
        if candidate_domains:
            prompt += f"- Domain expertise: {', '.join(candidate_domains)}\n"
        
        # Add arXiv research details for technical questions
        if papers:
            prompt += f"\nARXIV RESEARCH BACKGROUND (CRITICAL - ASK DEEP TECHNICAL QUESTIONS):\n"
            prompt += f"- Total papers: {len(papers)}\n"
            if papers:
                recent_papers = papers[:3]
                for i, paper in enumerate(recent_papers, 1):
                    title = paper.get('title', 'N/A')
                    abstract = paper.get('abstract', '')[:200]
                    categories = [c.get('term', '') for c in paper.get('categories', [])]
                    prompt += f"  Paper {i}: {title}\n"
                    prompt += f"    Abstract: {abstract}...\n"
                    prompt += f"    Categories: {', '.join(categories)}\n"
            
            if research_contributions:
                prompt += f"- Research contributions: {', '.join(research_contributions[:5])}\n"
        
        # Add GitHub repos for technical depth
        if repos:
            prompt += f"\nGITHUB ACTIVITY (ASK ABOUT SPECIFIC PROJECTS):\n"
            top_repos = sorted(repos, key=lambda r: r.get('stars', 0), reverse=True)[:3]
            for i, repo in enumerate(top_repos, 1):
                repo_name = repo.get('name', 'N/A')
                description = repo.get('description', '')
                language = repo.get('language', '')
                stars = repo.get('stars', 0)
                prompt += f"  Repo {i}: {repo_name} ({language}, {stars} stars)\n"
                if description:
                    prompt += f"    Description: {description[:150]}\n"
        
        # Add recent X posts for current work
        if posts:
            prompt += f"\nRECENT WORK (from X/Twitter):\n"
            recent_posts = posts[:3]
            for i, post in enumerate(recent_posts, 1):
                text = post.get('text', '')[:200]
                prompt += f"  Post {i}: {text}...\n"
        
        prompt += f"""
POSITION REQUIREMENTS:
"""
        
        if must_haves:
            prompt += f"- CRITICAL must-have skills: {', '.join(must_haves)}\n"
        
        if experience_level:
            prompt += f"- Required experience level: {experience_level}\n"
        
        if domains:
            prompt += f"- Domain expertise needed: {', '.join(domains)}\n"
        
        if skills:
            prompt += f"- Required skills: {', '.join(skills)}\n"
        
        prompt += f"""
INTERVIEW STRATEGY - HYPER-TECHNICAL AND PERSONALIZED:

1. OPENING (Personalized):
   - Address candidate by name: {candidate_name}
   - Reference their specific background: """
        
        if papers:
            prompt += f"mention their arXiv research ({len(papers)} papers)"
        elif repos:
            prompt += f"mention their GitHub work ({github_handle})"
        elif candidate_domains:
            prompt += f"mention their expertise in {', '.join(candidate_domains[:2])}"
        else:
            prompt += "their technical background"
        
        prompt += f"""
   - Set expectation: "This will be a deep technical discussion"

2. TECHNICAL DEPTH QUESTIONS (Ask HARD-HITTING questions based on their background):
"""
        
        # Generate specific technical questions based on candidate background
        if papers:
            prompt += f"""
   ARXIV RESEARCH QUESTIONS (CRITICAL if existing - Test their actual research depth if there is one that matches the position requirements):
   - "I see you published on [specific paper topic]. Walk me through the technical approach you took."
   - "In your paper on [topic], you mentioned [specific technical detail]. Can you explain the trade-offs you considered?"
   - "What were the biggest technical challenges in [specific research area]?"
   - "How does your research in [domain] relate to production systems?"
   - "What's the most technically complex problem you've solved in your research?"
"""
        
        if repos:
            prompt += f"""
   GITHUB PROJECT QUESTIONS (Test implementation depth):
   - "I see you built [repo name]. What was the most challenging technical decision you made?"
   - "Walk me through the architecture of [repo]. Why did you choose [specific tech]?"
   - "What technical debt or limitations exist in [repo]? How would you address them?"
   - "If you were to rebuild [repo] today, what would you do differently technically?"
"""
        
        if candidate_domains:
            prompt += f"""
   DOMAIN-SPECIFIC TECHNICAL QUESTIONS:
   - "In {candidate_domains[0]}, what's the most technically challenging problem you've worked on?"
   - "How do you handle [specific technical challenge in domain] at scale?"
   - "What are the current technical limitations in {candidate_domains[0]}? How would you push past them?"
   - "Describe a time you had to make a difficult technical trade-off in {candidate_domains[0]}."
"""
        
        prompt += f"""
   GENERAL HARD-HITTING TECHNICAL QUESTIONS:
   - "What's the most technically complex system you've designed/built? Walk me through the architecture."
   - "Describe a time you had to debug a production issue under pressure. What was your approach?"
   - "What technical decision have you made that you later regretted? What did you learn?"
   - "How do you stay current with technical advances in {', '.join(domains or candidate_domains or ['your field'])}?"
   - "What's a technical problem you're currently working on? What makes it challenging?"
   - "If you had to explain [complex technical concept from their background] to a junior engineer, how would you do it?"

3. POSITION-SPECIFIC TECHNICAL QUESTIONS:
   - "For this {title} role, what technical challenges do you anticipate?"
   - "How would your experience with {', '.join((candidate_skills[:3] if candidate_skills else ['your background']))} apply to {', '.join((must_haves[:3] if must_haves else ['our requirements']))}?"
   - "What technical problems at {company} are you most excited to solve?"

4. DEPTH PROBING (Follow up on EVERY technical answer):
   - Ask "Why?" and "How?" repeatedly
   - Challenge their assumptions: "What if [edge case]?"
   - Test understanding: "Can you explain [technical detail] in more depth?"
   - Look for gaps: "What about [related technical area]?"

5. ASSESSMENT CRITERIA (Evaluate):
   - Technical depth: Can they explain complex concepts clearly?
   - Problem-solving: Do they show systematic thinking?
   - Real experience: Can they discuss actual implementations, not just theory?
   - Learning ability: How do they approach new technical challenges?
   - Communication: Can they explain technical concepts clearly?

INTERVIEW STYLE:
- Be professional but direct
- Don't accept surface-level answers - dig deeper
- Ask follow-up questions that test actual understanding
- Reference their specific work (papers, repos, posts) to show you've done your research
- Keep it technical - this is a deep technical screen, not a casual chat
- Duration: 15-20 minutes of intense technical discussion

IMPORTANT: This is a HARD-HITTING technical interview. Push for depth. Test their actual knowledge, not just what they claim to know. Use their specific background to ask personalized, challenging questions.
"""
        
        return prompt
    
    async def create_call(
        self,
        assistant_id: str,
        candidate_phone: str
    ) -> str:
        """
        Initiate outbound call to candidate.
        
        Args:
            assistant_id: Assistant ID to use for the call
            candidate_phone: Candidate phone number (format: "5103585699" or "+15103585699")
        
        Returns:
            Call ID string
        """
        # Ensure phone number has +1 prefix for US numbers
        if not candidate_phone.startswith('+'):
            if candidate_phone.startswith('1'):
                candidate_phone = '+' + candidate_phone
            else:
                candidate_phone = '+1' + candidate_phone
        
        call_data = {
            "assistantId": assistant_id,
            "phoneNumberId": self.phone_number_id,
            "customer": {
                "number": candidate_phone
            }
        }
        
        try:
            response = await retry_with_backoff(
                self._make_call_request,
                call_data=call_data
            )
            
            call_id = response.get("id")
            if not call_id:
                raise ValueError("Failed to create call: no ID returned")
            
            logger.info(f"Created call {call_id} to {candidate_phone}")
            return call_id
            
        except Exception as e:
            logger.error(f"Error creating call: {e}")
            raise ValueError(f"Failed to create call: {e}")
    
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Get call status.
        
        Args:
            call_id: Call ID
        
        Returns:
            Call status dictionary with status, duration, etc.
        """
        try:
            response = await retry_with_backoff(
                self._get_call_request,
                call_id=call_id
            )
            return response
        except Exception as e:
            logger.error(f"Error getting call status: {e}")
            raise ValueError(f"Failed to get call status: {e}")
    
    async def get_transcript(self, call_id: str) -> Dict[str, Any]:
        """
        Get call transcript.
        
        Args:
            call_id: Call ID
        
        Returns:
            Transcript dictionary with messages, summary, etc.
        """
        try:
            response = await retry_with_backoff(
                self._get_call_request,
                call_id=call_id
            )
            
            # Extract transcript data
            transcript = {
                "call_id": call_id,
                "status": response.get("status"),
                "messages": response.get("messages", []),
                "summary": response.get("summary"),
                "transcript": response.get("transcript"),
                "duration": response.get("duration"),
                "ended_at": response.get("endedAt")
            }
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error getting transcript: {e}")
            raise ValueError(f"Failed to get transcript: {e}")
    
    async def wait_for_call_completion(
        self,
        call_id: str,
        timeout: int = 600,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Poll until call completes, then return transcript.
        
        Args:
            call_id: Call ID
            timeout: Maximum time to wait in seconds (default: 600 = 10 minutes)
            poll_interval: Seconds between status checks (default: 5)
        
        Returns:
            Transcript dictionary
        
        Raises:
            TimeoutError: If call doesn't complete within timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status_data = await self.get_call_status(call_id)
            status = status_data.get("status", "unknown")
            
            logger.debug(f"Call {call_id} status: {status}")
            
            if status in ["ended", "ended-by-system", "ended-by-customer"]:
                logger.info(f"Call {call_id} completed with status: {status}")
                return await self.get_transcript(call_id)
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Call {call_id} did not complete within {timeout} seconds")
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
    
    async def _create_assistant(self, assistant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create assistant via API."""
        url = f"{self.base_url}/assistant"
        response = await self.client.post(url, headers=self.headers, json=assistant_data)
        handle_api_error(response, "Vapi API create assistant failed")
        return response.json()
    
    async def _make_call_request(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create call via API."""
        url = f"{self.base_url}/call"
        response = await self.client.post(url, headers=self.headers, json=call_data)
        handle_api_error(response, "Vapi API create call failed")
        return response.json()
    
    async def _get_call_request(self, call_id: str) -> Dict[str, Any]:
        """Get call details via API."""
        url = f"{self.base_url}/call/{call_id}"
        response = await self.client.get(url, headers=self.headers)
        handle_api_error(response, "Vapi API get call failed")
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

