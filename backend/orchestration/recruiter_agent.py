"""
Recruiter agent powered by Grok API.

Handles recruiter messages, processes role requests, and manages candidate interactions.
"""

import logging
import re
from typing import Dict, Optional, List, Any

from backend.integrations.grok_api import GrokAPIClient
from backend.orchestration.feedback_loop import FeedbackLoop
from backend.simulator.x_dm_simulator import XDMSimulator
from backend.database.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class RecruiterAgent:
    """
    AI recruiter agent that handles conversations and coordinates the recruitment pipeline.
    
    Uses Grok API for natural language understanding and response generation.
    Works with X DM simulator (or real X API when available).
    """
    
    def __init__(
        self,
        grok_client: Optional[GrokAPIClient] = None,
        pipeline: Optional[Any] = None,  # For inbound pipeline (Ishaan's work)
        simulator: Optional[XDMSimulator] = None,
        feedback_loop: Optional[FeedbackLoop] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None
    ):
        """
        Initialize recruiter agent.
        
        Args:
            grok_client: Grok API client instance
            pipeline: Recruitment pipeline instance (for inbound - Ishaan's work)
            simulator: X DM simulator instance
            feedback_loop: Feedback loop instance (creates new if None)
            knowledge_graph: Knowledge graph instance (for feedback loop)
        """
        self.grok = grok_client or GrokAPIClient()
        self.pipeline = pipeline  # For inbound pipeline (Ishaan's work)
        self.simulator = simulator or XDMSimulator()
        self.kg = knowledge_graph or KnowledgeGraph()
        # Initialize feedback loop with Grok client for LLM-based parsing
        self.feedback_loop = feedback_loop or FeedbackLoop(
            knowledge_graph=self.kg,
            grok_client=self.grok
        )
        self.conversation_state: Dict[str, any] = {}
        logger.info("RecruiterAgent initialized")
    
    async def handle_message(self, message: str) -> str:
        """
        Handle a recruiter message and generate response.
        
        Args:
            message: Message from recruiter
        
        Returns:
            Response message from @x_recruiting
        """
        # Store message in simulator
        self.simulator.send_message(message, sender="user")
        
        # Parse message intent
        intent = await self._parse_intent(message)
        
        logger.info(f"Parsed intent: {intent}")
        
        # Handle based on intent
        if intent == "new_role":
            response = await self._handle_new_role(message)
        elif intent == "feedback":
            response = await self._handle_feedback(message)
        elif intent == "question":
            response = await self._handle_question(message)
        elif intent == "get_candidates":
            response = await self._handle_get_candidates(message)
        else:
            response = await self._handle_general(message)
        
        # Store response in simulator
        self.simulator.receive_message(response)
        
        return response
    
    async def process_role_request(
        self,
        role_description: str,
        role_title: Optional[str] = None
    ) -> Dict:
        """
        Process a new role request.
        
        Args:
            role_description: Role description text
            role_title: Optional job title
        
        Returns:
            Pipeline result dictionary with candidates
        """
        try:
            # Ask clarifying questions if needed
            if not self._has_sufficient_info(role_description):
                return {
                    'needs_clarification': True,
                    'message': await self._ask_clarifying_questions(role_description)
                }
            
            # Inbound pipeline (Ishaan's work) - for now return error if not available
            if not self.pipeline:
                return {'error': 'Inbound pipeline not available - Ishaan\'s work in progress'}
            result = await self.pipeline.process_role_request(
                role_description,
                role_title=role_title
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing role request: {e}", exc_info=True)
            return {
                'error': str(e),
                'message': "I encountered an error processing your role request. Please try again."
            }
    
    async def collect_feedback(
        self,
        feedback_text: str,
        candidate_id: Optional[str] = None,
        role_id: Optional[str] = None
    ) -> str:
        """
        Collect and process feedback on a candidate.
        
        This method connects recruiter feedback to the feedback loop, enabling
        the self-improving agent to learn from feedback.
        
        Args:
            feedback_text: Feedback text from recruiter
            candidate_id: Candidate identifier
            role_id: Role/position identifier
        
        Returns:
            Confirmation message with learning metrics
        """
        try:
            # Process feedback through feedback loop
            if candidate_id and role_id:
                result = await self.feedback_loop.process_feedback(
                    candidate_id=candidate_id,
                    position_id=role_id,
                    feedback_text=feedback_text
                )
                
                if result.get('success'):
                    # Return message with learning metrics
                    return result.get('message', "Thank you for the feedback!")
                else:
                    # Feedback processed but couldn't update bandit (e.g., candidate not in list)
                    error = result.get('error', 'Unknown error')
                    logger.warning(f"Feedback processed but bandit not updated: {error}")
                    return f"Thank you for the feedback! I've recorded it. ({error})"
            else:
                # Missing candidate_id or role_id - just acknowledge
                logger.warning("Feedback received but missing candidate_id or role_id")
                return "Thank you for the feedback! I'll use this to improve future recommendations."
            
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}", exc_info=True)
            return "I encountered an error processing your feedback. Please try again."
    
    async def _parse_intent(self, message: str) -> str:
        """
        Parse message intent using Grok API.
        
        Args:
            message: Recruiter message
        
        Returns:
            Intent string: "new_role", "feedback", "question", "get_candidates", or "general"
        """
        prompt = f"""Analyze this recruiter message and determine the intent:

Message: "{message}"

Possible intents:
- "new_role": Recruiter wants to post a new job/role
- "feedback": Recruiter is providing feedback on a candidate
- "question": Recruiter is asking a question
- "get_candidates": Recruiter wants to see candidate list
- "general": General conversation

Respond with ONLY the intent name, nothing else."""

        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "general").strip().lower()
            
            # Extract intent from response
            if "new_role" in content or "new job" in content.lower():
                return "new_role"
            elif "feedback" in content:
                return "feedback"
            elif "question" in content or "?" in message:
                return "question"
            elif "candidates" in content or "list" in content:
                return "get_candidates"
            else:
                return "general"
                
        except Exception as e:
            logger.warning(f"Error parsing intent: {e}, defaulting to general")
            # Simple keyword-based fallback
            message_lower = message.lower()
            if any(word in message_lower for word in ["need", "looking for", "hire", "role", "position"]):
                return "new_role"
            elif any(word in message_lower for word in ["feedback", "not qualified", "good", "bad"]):
                return "feedback"
            elif "?" in message:
                return "question"
            else:
                return "general"
    
    async def _handle_new_role(self, message: str) -> str:
        """Handle new role request."""
        # Extract role description from message
        role_description = message
        
        # Process role request
        result = await self.process_role_request(role_description)
        
        if result.get('needs_clarification'):
            return result.get('message', "I need more information about this role.")
        
        if result.get('error'):
            return result.get('message', "I encountered an error. Please try again.")
        
        # Format candidate recommendations
        selected = result.get('selected_candidates', [])
        if not selected:
            return "I couldn't find any suitable candidates for this role. Try adjusting your requirements."
        
        response = f"I found {len(selected)} top candidates for this role:\n\n"
        for i, candidate in enumerate(selected[:5], 1):
            handle = candidate.get('github_handle', 'Unknown')
            similarity = candidate.get('similarity_score', 0.0)
            response += f"{i}. @{handle} (Match: {similarity:.1%})\n"
        
        response += f"\nShould I reach out to these candidates?"
        
        return response
    
    async def _handle_feedback(self, message: str) -> str:
        """Handle feedback message."""
        return await self.collect_feedback(message)
    
    async def _handle_question(self, message: str) -> str:
        """Handle general question."""
        prompt = f"""You are @x_recruiting, an AI recruiter assistant. Answer this question helpfully and concisely:

Question: {message}

Keep your response under 200 characters and friendly."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "I'm here to help with your recruiting needs!")
            return content
        except Exception as e:
            logger.error(f"Error handling question: {e}")
            return "I'm here to help with your recruiting needs! What can I do for you?"
    
    async def _handle_get_candidates(self, message: str) -> str:
        """Handle request to get candidate list."""
        # Get latest role from conversation state
        role_id = self.conversation_state.get('current_role_id')
        if not role_id:
            return "I don't have an active role. Please start by describing a role you need to fill."
        
        # Inbound pipeline (Ishaan's work) - for now return error if not available
        if not self.pipeline:
            return "Inbound pipeline not available - Ishaan's work in progress"
        candidates = self.pipeline.get_candidates_for_role(role_id)
        if not candidates:
            return "No candidates found for this role."
        
        response = f"Here are the candidates for this role:\n\n"
        for i, candidate in enumerate(candidates[:10], 1):
            handle = candidate.get('github_handle', 'Unknown')
            similarity = candidate.get('similarity_score', 0.0)
            response += f"{i}. @{handle} (Match: {similarity:.1%})\n"
        
        return response
    
    async def _handle_general(self, message: str) -> str:
        """Handle general conversation."""
        return await self._handle_question(message)
    
    def _has_sufficient_info(self, role_description: str) -> bool:
        """Check if role description has sufficient information."""
        # Simple heuristic: check if description is long enough
        return len(role_description.split()) >= 10
    
    async def _ask_clarifying_questions(self, role_description: str) -> str:
        """Generate clarifying questions using Grok."""
        prompt = f"""You are @x_recruiting. The recruiter provided this role description:

"{role_description}"

Ask 1-2 clarifying questions to get more details. Keep it concise and friendly."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "Can you provide more details about this role?")
            return content
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return "Can you provide more details about the required skills and experience level?"
    
    async def _parse_feedback(self, feedback_text: str) -> tuple[str, float]:
        """
        Parse feedback text to extract type and reward.
        
        Args:
            feedback_text: Feedback message
        
        Returns:
            Tuple of (feedback_type, reward)
        """
        feedback_lower = feedback_text.lower()
        
        # Determine feedback type
        if any(word in feedback_lower for word in ["good", "qualified", "yes", "interested", "positive"]):
            feedback_type = "positive"
            reward = 1.0
        elif any(word in feedback_lower for word in ["bad", "not qualified", "no", "not interested", "negative"]):
            feedback_type = "negative"
            reward = 0.0
        else:
            feedback_type = "neutral"
            reward = 0.5
        
        return feedback_type, reward

