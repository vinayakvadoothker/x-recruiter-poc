"""
Grok API client for entity extraction and embeddings.

CRITICAL: Vin needs extract_entities_with_grok() for Day 2 work.
"""

import os
import logging
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv

from backend.integrations.api_utils import retry_with_backoff, handle_api_error

load_dotenv()
logger = logging.getLogger(__name__)


class GrokAPIClient:
    """
    Client for interacting with Grok API.
    
    Provides entity extraction and embedding generation capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Grok API client.
        
        Args:
            api_key: Grok API key. If not provided, reads from GROK_API_KEY env var.
        
        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Grok API key required. Set GROK_API_KEY environment variable or pass api_key parameter."
            )
        
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def extract_entities_with_grok(
        self,
        text: str,
        entity_types: List[str] = None
    ) -> Dict:
        """
        Extract entities from text using Grok API.
        
        CRITICAL: Vin needs this function for Day 2 work!
        
        Args:
            text: Text to extract entities from
            entity_types: List of entity types to extract.
                         Default: ['skills', 'experience', 'education', 'projects']
        
        Returns:
            Dictionary with extracted entities:
            {
                'skills': [list of skills],
                'experience': [list of experience items],
                'education': [list of education items],
                'projects': [list of projects]
            }
        
        Raises:
            ValueError: If API request fails
        """
        if entity_types is None:
            entity_types = ['skills', 'experience', 'education', 'projects']
        
        # Construct prompt for entity extraction
        entity_types_str = ", ".join(entity_types)
        prompt = f"""Extract the following entities from the text below:
- {entity_types_str}

Text:
{text}

Return a JSON object with keys matching the entity types listed above. Each key should contain a list of extracted items.

Example format:
{{
  "skills": ["Python", "Machine Learning"],
  "experience": ["5 years as Software Engineer"],
  "education": ["BS in Computer Science"],
  "projects": ["Built recommendation system"]
}}"""
        
        try:
            response = await retry_with_backoff(
                self._make_chat_request,
                prompt=prompt
            )
            
            # Parse response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Try to parse JSON from response
            import json
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                entities = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from Grok response: {content}")
                # Fallback: return empty structure
                entities = {entity_type: [] for entity_type in entity_types}
            
            # Ensure all entity types are present
            result = {}
            for entity_type in entity_types:
                result[entity_type] = entities.get(entity_type, [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            # Return empty structure on error
            return {entity_type: [] for entity_type in entity_types}
    
    async def get_embeddings(self, text: str) -> List[float]:
        """
        Get text embeddings from Grok API.
        
        Args:
            text: Text to generate embeddings for
        
        Returns:
            List of float values representing the embedding vector
        
        Raises:
            ValueError: If API request fails
        """
        try:
            response = await retry_with_backoff(
                self._make_embeddings_request,
                text=text
            )
            
            # Extract embedding from response
            embedding = response.get("data", [{}])[0].get("embedding", [])
            return embedding
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise ValueError(f"Failed to get embeddings: {e}")
    
    async def _make_chat_request(self, prompt: str) -> Dict:
        """
        Make a chat completion request to Grok API.
        
        Args:
            prompt: Prompt text to send
        
        Returns:
            Response dictionary from API
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": "grok-beta",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }
        
        response = await self.client.post(url, headers=self.headers, json=payload)
        handle_api_error(response, "Grok API chat request failed")
        return response.json()
    
    async def _make_embeddings_request(self, text: str) -> Dict:
        """
        Make an embeddings request to Grok API.
        
        Args:
            text: Text to generate embeddings for
        
        Returns:
            Response dictionary from API
        """
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": "text-embedding-ada-002",  # Update if Grok has different model
            "input": text
        }
        
        response = await self.client.post(url, headers=self.headers, json=payload)
        handle_api_error(response, "Grok API embeddings request failed")
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

