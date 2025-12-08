"""
chat_service.py - Chat interface for knowledge graph queries

This module provides a conversational interface to the knowledge graph,
allowing users to query candidates, teams, positions, and interviewers
using natural language. Uses Grok AI for query parsing and response formatting.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from backend.database.knowledge_graph import KnowledgeGraph
from backend.database.query_engine import QueryEngine
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder
from backend.integrations.grok_api import GrokAPIClient
from backend.orchestration.pipeline_tracker import PipelineTracker

logger = logging.getLogger(__name__)


class GraphChatService:
    """
    Chat service for knowledge graph queries.
    
    Handles:
    - Natural language query parsing
    - Graph query execution
    - Response formatting
    - Conversation context management
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        query_engine: Optional[QueryEngine] = None,
        grok_client: Optional[GrokAPIClient] = None,
        pipeline_tracker: Optional[PipelineTracker] = None
    ):
        self.kg = knowledge_graph or KnowledgeGraph()
        self.query_engine = query_engine or QueryEngine(self.kg)
        self.grok = grok_client or GrokAPIClient()
        self.pipeline = pipeline_tracker or PipelineTracker()
        
        # In-memory conversation context (session-based)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        
        logger.info("GraphChatService initialized")
    
    async def _parse_query(self, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Parse natural language query into structured graph operation.
        
        Args:
            query: User's natural language query
            history: Conversation history for context
        
        Returns:
            Parsed query structure with operation type and parameters
        """
        history_context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in history[-5:]  # Last 5 messages for context
        ])
        
        prompt = f"""You are a knowledge graph query parser. Parse this user query into a structured operation.

KNOWLEDGE GRAPH STRUCTURE:
- Profile types: candidates, teams, interviewers, positions
- Operations: search, filter, match, get, pipeline_status, similar

CONVERSATION HISTORY:
{history_context}

USER QUERY: {query}

Parse the query and return JSON with:
{{
    "operation": "search" | "filter" | "match" | "get" | "pipeline_status" | "similar",
    "profile_type": "candidates" | "teams" | "interviewers" | "positions" | "all",
    "filters": {{
        "skills": ["skill1", "skill2"],
        "min_arxiv_papers": 0,
        "min_github_stars": 0,
        "domains": ["domain1"],
        "experience_years": 0
    }},
    "similarity_target": {{
        "type": "candidate" | "team" | "position",
        "id": "profile_id"
    }},
    "query_text": "text to embed for similarity search",
    "top_k": 10,
    "context_references": ["candidate_id", "position_id"]  // IDs mentioned in conversation
}}

Examples:
- "Find ML engineers with 5+ papers" → {{"operation": "filter", "profile_type": "candidates", "filters": {{"min_arxiv_papers": 5, "skills": ["ML", "machine learning"]}}}}
- "Show me teams that need Python" → {{"operation": "search", "profile_type": "teams", "query_text": "Python developers", "top_k": 10}}
- "Match this candidate to positions" → {{"operation": "match", "profile_type": "positions", "similarity_target": {{"type": "candidate", "id": "from_context"}}}}
- "What's the pipeline for @username?" → {{"operation": "pipeline_status", "profile_type": "candidates", "filters": {{"x_handle": "username"}}}}

Return ONLY valid JSON, no other text."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Extract JSON from response (might have markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            logger.info(f"Parsed query: {parsed}")
            return parsed
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            # Fallback: simple search
            return {
                "operation": "search",
                "profile_type": "candidates",
                "query_text": query,
                "top_k": 10
            }
    
    def _execute_query(self, parsed_query: Dict[str, Any], session_id: str) -> List[Dict[str, Any]]:
        """
        Execute parsed query against knowledge graph.
        
        Args:
            parsed_query: Parsed query structure
            session_id: Session ID for context
        
        Returns:
            List of results with profile data
        """
        operation = parsed_query.get("operation", "search")
        profile_type = parsed_query.get("profile_type", "candidates")
        top_k = parsed_query.get("top_k", 10)
        
        results = []
        
        try:
            if operation == "search":
                # Similarity search
                query_text = parsed_query.get("query_text", "")
                if query_text:
                    # Generate embedding for query
                    embedder = RecruitingKnowledgeGraphEmbedder()
                    query_embedding = embedder.embed_text(query_text)
                    
                    # Map profile type to Weaviate class
                    class_map = {
                        "candidates": "Candidate",
                        "teams": "Team",
                        "interviewers": "Interviewer",
                        "positions": "Position"
                    }
                    class_name = class_map.get(profile_type, "Candidate")
                    
                    # Search
                    vector_db = VectorDBClient()
                    search_results = vector_db._search(class_name, query_embedding, top_k)
                    
                    # Enrich with full profile data
                    for result in search_results:
                        profile_id = result.get("profile_id")
                        profile = None
                        try:
                            if profile_type == "candidates":
                                profile = self.kg.get_candidate(profile_id)
                            elif profile_type == "teams":
                                profile = self.kg.get_team(profile_id)
                            elif profile_type == "interviewers":
                                profile = self.kg.get_interviewer(profile_id)
                            elif profile_type == "positions":
                                profile = self.kg.get_position(profile_id)
                        except Exception as e:
                            logger.warning(f"Error fetching profile {profile_id}: {e}")
                            profile = None
                        
                        if profile:
                            results.append({
                                "type": profile_type.rstrip("s"),
                                "id": profile_id,
                                "name": profile.get("name") or profile.get("title") or profile_id,
                                "similarity": result.get("similarity", 0.0),
                                "details": profile
                            })
            
            elif operation == "filter":
                # Filter-based query
                filters = parsed_query.get("filters", {})
                
                if profile_type == "candidates":
                    # Use query engine for complex filters
                    if filters.get("min_arxiv_papers") or filters.get("min_github_stars"):
                        candidates = self.query_engine.query_exceptional_talent(
                            min_arxiv_papers=filters.get("min_arxiv_papers", 0),
                            min_github_stars=filters.get("min_github_stars", 0),
                            top_k=top_k
                        )
                    elif filters.get("skills"):
                        candidates = self.query_engine.query_by_skills(
                            required_skills=filters.get("skills", []),
                            top_k=top_k
                        )
                    else:
                        candidates = self.kg.get_all_candidates()[:top_k]
                    
                    for candidate in candidates:
                        results.append({
                            "type": "candidate",
                            "id": candidate.get("id") or candidate.get("x_handle", ""),
                            "name": candidate.get("name") or candidate.get("x_handle", ""),
                            "details": candidate
                        })
            
            elif operation == "match":
                # Cross-type matching
                similarity_target = parsed_query.get("similarity_target", {})
                target_type = similarity_target.get("type", "candidate")
                target_id = similarity_target.get("id")
                
                if target_id and target_id != "from_context":
                    # Get target profile
                    if target_type == "candidate":
                        target = self.kg.get_candidate(target_id)
                    elif target_type == "position":
                        target = self.kg.get_position(target_id)
                    elif target_type == "team":
                        target = self.kg.get_team(target_id)
                    else:
                        target = None
                    
                    if target:
                        # Find similar profiles
                        embedder = RecruitingKnowledgeGraphEmbedder()
                        if target_type == "candidate":
                            target_embedding = embedder.embed_candidate(target)
                        elif target_type == "position":
                            target_embedding = embedder.embed_position(target)
                        elif target_type == "team":
                            target_embedding = embedder.embed_team(target)
                        else:
                            target_embedding = None
                        
                        if target_embedding:
                            class_map = {
                                "candidates": "Candidate",
                                "teams": "Team",
                                "positions": "Position"
                            }
                            class_name = class_map.get(profile_type, "Candidate")
                            
                            vector_db = VectorDBClient()
                            matches = vector_db._search(class_name, target_embedding, top_k)
                            
                            for match in matches:
                                profile_id = match.get("profile_id")
                                profile = None
                                try:
                                    if profile_type == "candidates":
                                        profile = self.kg.get_candidate(profile_id)
                                    elif profile_type == "teams":
                                        profile = self.kg.get_team(profile_id)
                                    elif profile_type == "positions":
                                        profile = self.kg.get_position(profile_id)
                                except Exception as e:
                                    logger.warning(f"Error fetching profile {profile_id}: {e}")
                                    profile = None
                                
                                if profile:
                                    results.append({
                                        "type": profile_type.rstrip("s"),
                                        "id": profile_id,
                                        "name": profile.get("name") or profile.get("title") or profile_id,
                                        "similarity": match.get("similarity", 0.0),
                                        "details": profile
                                    })
            
            elif operation == "pipeline_status":
                # Get pipeline status
                filters = parsed_query.get("filters", {})
                x_handle = filters.get("x_handle", "").lstrip("@")
                
                if x_handle:
                    # Find candidate by handle
                    from backend.database.postgres_client import PostgresClient
                    from backend.orchestration.company_context import get_company_context
                    postgres = PostgresClient()
                    company_id = get_company_context().get_company_id()
                    
                    candidate = postgres.execute_one(
                        "SELECT * FROM candidates WHERE x_handle = %s AND company_id = %s",
                        (x_handle, company_id)
                    )
                    
                    if candidate:
                        candidate_id = candidate.get("id")
                        # Get all positions for this candidate
                        positions = self.pipeline.get_positions_for_candidate(candidate_id)
                        
                        for pos in positions:
                            results.append({
                                "type": "pipeline",
                                "id": pos.get("position_id", ""),
                                "name": pos.get("position_title", ""),
                                "stage": pos.get("stage", ""),
                                "details": pos
                            })
            
            elif operation == "get":
                # Get specific profile
                filters = parsed_query.get("filters", {})
                profile_id = filters.get("id") or filters.get("x_handle", "").lstrip("@")
                
                if profile_id:
                    profile = None
                    try:
                        if profile_type == "candidates":
                            profile = self.kg.get_candidate(profile_id)
                        elif profile_type == "teams":
                            profile = self.kg.get_team(profile_id)
                        elif profile_type == "positions":
                            profile = self.kg.get_position(profile_id)
                    except Exception as e:
                        logger.warning(f"Error fetching profile {profile_id}: {e}")
                        profile = None
                    
                    if profile:
                        results.append({
                            "type": profile_type.rstrip("s"),
                            "id": profile_id,
                            "name": profile.get("name") or profile.get("title") or profile_id,
                            "details": profile
                        })
        
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
        
        return results[:top_k]
    
    async def _format_response(
        self,
        query: str,
        results: List[Dict[str, Any]],
        parsed_query: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """
        Format query results into natural language response.
        
        Args:
            query: Original user query
            results: Query results
            parsed_query: Parsed query structure
            history: Conversation history
        
        Returns:
            Formatted natural language response
        """
        if not results:
            # Even with no results, provide a helpful answer
            prompt = f"""You are a helpful knowledge graph assistant. The user asked a question but no matching results were found in the knowledge graph.

USER QUERY: {query}

QUERY TYPE: {parsed_query.get('operation', 'search')}
PROFILE TYPE: {parsed_query.get('profile_type', 'candidates')}

Provide a helpful, conversational response that:
1. Acknowledges what the user asked
2. Explains that no matching results were found in the knowledge graph
3. Suggests alternative ways to phrase the query or what might help
4. Offers to help with related queries

Be friendly and helpful, not just "no results found". Keep it concise (2-3 sentences)."""
            
            try:
                response = await self.grok._make_chat_request(prompt)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content
            except Exception as e:
                logger.error(f"Error formatting response: {e}")
                return "I couldn't find any results matching your query in the knowledge graph. Try rephrasing or being more specific. I can help you search for candidates, teams, positions, or interviewers."
        
        # Build results summary
        results_summary = []
        for result in results[:5]:  # Top 5 for summary
            result_str = f"- {result.get('name', result.get('id', 'Unknown'))}"
            if result.get('similarity'):
                result_str += f" ({result['similarity']*100:.1f}% match)"
            if result.get('stage'):
                result_str += f" - Stage: {result['stage']}"
            results_summary.append(result_str)
        
        prompt = f"""You are a helpful knowledge graph assistant. Format these query results into a natural, conversational response.

USER QUERY: {query}

QUERY TYPE: {parsed_query.get('operation', 'search')}
PROFILE TYPE: {parsed_query.get('profile_type', 'candidates')}

RESULTS FOUND: {len(results)}
TOP RESULTS:
{chr(10).join(results_summary)}

Format a helpful response that:
1. Acknowledges what the user asked
2. Summarizes what was found
3. Highlights key details from top results
4. Suggests follow-up questions if relevant

Keep it conversational and concise (2-3 sentences + bullet points for top results)."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            # Fallback response
            return f"Found {len(results)} results. Top matches: {', '.join([r.get('name', r.get('id', 'Unknown')) for r in results[:3]])}"
    
    async def chat(
        self,
        query: str,
        session_id: str,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process chat query and return response.
        
        Args:
            query: User's natural language query
            session_id: Session ID for context
            history: Conversation history
        
        Returns:
            Response with formatted text and results
        """
        history = history or []
        
        # Update conversation context
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({"role": "user", "content": query})
        
        try:
            # Parse query
            parsed_query = await self._parse_query(query, history)
            
            # Execute query
            results = self._execute_query(parsed_query, session_id)
            
            # Format response
            response_text = await self._format_response(query, results, parsed_query, history)
            
            # Update conversation context
            self.conversations[session_id].append({"role": "assistant", "content": response_text})
            
            return {
                "response": response_text,
                "results": results,
                "query_type": parsed_query.get("operation", "search")
            }
        
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "response": f"Sorry, I encountered an error processing your query: {str(e)}. Please try rephrasing.",
                "results": [],
                "query_type": "error"
            }

