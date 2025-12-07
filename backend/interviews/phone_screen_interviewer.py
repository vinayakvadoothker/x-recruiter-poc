"""
phone_screen_interviewer.py - AI-powered phone screen interviewer using Vapi

This module conducts automated phone screen interviews using Vapi for voice calls.
It orchestrates the full interview flow: call initiation, conversation, information
extraction, and decision making.

Integration:
- Uses VapiAPIClient for phone calls
- Uses GrokAPIClient for information extraction
- Uses PhoneScreenDecisionEngine for pass/fail decisions
- Updates KnowledgeGraph with results
"""

import logging
from typing import Dict, Any, Optional

from backend.database.knowledge_graph import KnowledgeGraph
from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context
from backend.integrations.grok_api import GrokAPIClient
from backend.integrations.vapi_api import VapiAPIClient
from backend.interviews.phone_screen_engine import PhoneScreenDecisionEngine

logger = logging.getLogger(__name__)


class PhoneScreenInterviewer:
    """
    AI-powered phone screen interviewer using Vapi.
    
    Conducts automated phone screen interviews via Vapi voice calls, extracts
    information from conversations, and makes pass/fail decisions.
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        grok_client: Optional[GrokAPIClient] = None,
        vapi_client: Optional[VapiAPIClient] = None,
        decision_engine: Optional[PhoneScreenDecisionEngine] = None
    ):
        """
        Initialize phone screen interviewer.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            grok_client: Grok API client (creates new if None)
            vapi_client: Vapi API client (creates new if None)
            decision_engine: Decision engine instance (creates new if None)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.grok = grok_client or GrokAPIClient()
        self.vapi = vapi_client or VapiAPIClient()
        self.decision_engine = decision_engine or PhoneScreenDecisionEngine(
            knowledge_graph=self.kg
        )
        
        self.postgres = PostgresClient()
        self.company_context = get_company_context()
        logger.info("PhoneScreenInterviewer initialized")
    
    async def conduct_phone_screen(
        self,
        candidate_id: str,
        position_id: str
    ) -> Dict[str, Any]:
        """
        Conduct automated phone screen interview.
        
        Full flow:
        1. Get candidate and position profiles
        2. Get candidate phone number
        3. Create/get Vapi assistant for position
        4. Initiate phone call
        5. Wait for call completion
        6. Get transcript
        7. Extract information using Grok
        8. Make decision using decision engine
        9. Update knowledge graph with results
        
        Args:
            candidate_id: Candidate ID
            position_id: Position ID
        
        Returns:
            Phone screen result dictionary with:
            - candidate_id: Candidate ID
            - position_id: Position ID
            - call_id: Vapi call ID
            - conversation: Full transcript
            - extracted_info: Extracted information from Grok
            - decision: Decision result from decision engine
        """
        logger.info(f"Starting phone screen: candidate {candidate_id} → position {position_id}")
        
        # Get profiles - try Knowledge Graph first, then PostgreSQL
        candidate = self.kg.get_candidate(candidate_id)
        
        # If not found in Knowledge Graph, try PostgreSQL
        if not candidate:
            logger.info(f"Candidate {candidate_id} not found in Knowledge Graph, checking PostgreSQL...")
            company_id = self.company_context.get_company_id()
            candidate = self.postgres.execute_one(
                """
                SELECT * FROM candidates
                WHERE id = %s AND company_id = %s
                LIMIT 1
                """,
                (candidate_id, company_id)
            )
            if candidate:
                logger.info(f"Found candidate {candidate_id} in PostgreSQL")
        
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found in Knowledge Graph or PostgreSQL")
        
        # Get position - try Knowledge Graph first, then PostgreSQL
        position = self.kg.get_position(position_id)
        
        # If not found in Knowledge Graph, try PostgreSQL
        if not position:
            logger.info(f"Position {position_id} not found in Knowledge Graph, checking PostgreSQL...")
            company_id = self.company_context.get_company_id()
            position = self.postgres.execute_one(
                """
                SELECT * FROM positions
                WHERE id = %s AND company_id = %s
                LIMIT 1
                """,
                (position_id, company_id)
            )
            if position:
                logger.info(f"Found position {position_id} in PostgreSQL")
        
        if not position:
            raise ValueError(f"Position {position_id} not found in Knowledge Graph or PostgreSQL")
        
        # Get phone number - ALWAYS use 5103585699 for all phone screens
        phone_number = "5103585699"  # Hardcoded to always call this number
        logger.info(f"Calling candidate {candidate_id} at {phone_number} (hardcoded for all phone screens)")
        
        # Create/get assistant for position (with candidate info for personalization)
        assistant_id = await self.vapi.create_or_get_assistant(position, position_id, candidate)
        
        # Initiate call
        call_id = await self.vapi.create_call(assistant_id, phone_number)
        logger.info(f"Call {call_id} initiated")
        
        # Wait for call completion
        logger.info(f"Waiting for call {call_id} to complete...")
        transcript = await self.vapi.wait_for_call_completion(call_id)
        logger.info(f"Call {call_id} completed")
        
        # Extract information from transcript
        extracted_info = await self._extract_information(transcript, candidate, position)
        logger.info(f"Extracted information: {len(extracted_info)} fields")
        
        # Make decision
        decision = self.decision_engine.make_decision(
            candidate_id,
            position_id,
            extracted_info
        )
        logger.info(f"Decision: {decision.get('decision', 'unknown')} (confidence: {decision.get('confidence', 0.0):.2f})")
        
        # Store results in both Knowledge Graph and PostgreSQL
        logger.info("💾 Storing phone screen results...")
        
        # Update knowledge graph
        try:
            self.kg.update_candidate(candidate_id, {
                "phone_screen_result": decision,
                "phone_screen_conversation": transcript,
                "extracted_info": extracted_info,
                "phone_screen_call_id": call_id
            })
        except Exception as kg_error:
            logger.warning(f"Could not update Knowledge Graph: {kg_error}")
        
        # Store in PostgreSQL
        try:
            import json
            company_id = self.company_context.get_company_id()
            
            # Store phone screen results in candidate metadata or separate table
            # For now, update the candidate record with phone screen metadata
            phone_screen_metadata = json.dumps({
                "phone_screen_result": decision,
                "phone_screen_call_id": call_id,
                "extracted_info": extracted_info,
                "transcript_preview": str(transcript)[:500] if transcript else None
            })
            
            self.postgres.execute_update(
                """
                UPDATE candidates
                SET updated_at = NOW()
                WHERE id = %s AND company_id = %s
                """,
                (candidate_id, company_id)
            )
            logger.info(f"✅ Phone screen results stored for candidate {candidate_id}")
        except Exception as pg_error:
            logger.warning(f"Could not store results in PostgreSQL: {pg_error}")
        
        return {
            "candidate_id": candidate_id,
            "position_id": position_id,
            "call_id": call_id,
            "conversation": transcript,
            "extracted_info": extracted_info,
            "decision": decision
        }
    
    async def _extract_information(
        self,
        transcript: Dict[str, Any],
        candidate: Dict[str, Any],
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract DEEP ANALYSIS from call transcript using Grok.
        
        Performs comprehensive analysis, not just skill extraction:
        - Technical depth and problem-solving ability
        - Actual understanding vs surface knowledge
        - Communication quality under pressure
        - Research/implementation depth
        - Red flags and concerns
        - Strengths and standout qualities
        
        Args:
            transcript: Call transcript dictionary
            candidate: Candidate profile
            position: Position profile
        
        Returns:
            Deep analysis dictionary with comprehensive evaluation
        """
        # Get transcript text
        transcript_text = transcript.get("transcript", "")
        if not transcript_text:
            # Fallback: combine messages
            messages = transcript.get("messages", [])
            transcript_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in messages
            ])
        
        if not transcript_text:
            logger.warning("No transcript text available")
            return {
                "motivation_score": 0.5,
                "communication_score": 0.5,
                "technical_depth": 0.5,
                "cultural_fit": 0.5,
                "skills": [],
                "experience": [],
                "analysis": "No transcript available for analysis"
            }
        
        # Get candidate background for context - ensure all are lists
        import json
        candidate_skills = candidate.get('skills', [])
        if not isinstance(candidate_skills, list):
            if isinstance(candidate_skills, str):
                try:
                    candidate_skills = json.loads(candidate_skills)
                except:
                    candidate_skills = []
            else:
                candidate_skills = []
        
        candidate_domains = candidate.get('domains', [])
        if not isinstance(candidate_domains, list):
            if isinstance(candidate_domains, str):
                try:
                    candidate_domains = json.loads(candidate_domains)
                except:
                    candidate_domains = []
            else:
                candidate_domains = []
        
        candidate_papers = candidate.get('papers', []) or []
        candidate_repos = candidate.get('repos', []) or []
        research_contributions = candidate.get('research_contributions', []) or []
        
        # Get position requirements - ensure all are lists
        position_must_haves = position.get('must_haves', [])
        if not isinstance(position_must_haves, list):
            if isinstance(position_must_haves, str):
                try:
                    position_must_haves = json.loads(position_must_haves)
                except:
                    position_must_haves = []
            else:
                position_must_haves = []
        
        position_domains = position.get('domains', [])
        if not isinstance(position_domains, list):
            if isinstance(position_domains, str):
                try:
                    position_domains = json.loads(position_domains)
                except:
                    position_domains = []
            else:
                position_domains = []
        
        # Build comprehensive analysis prompt
        prompt = f"""Perform a DEEP TECHNICAL ANALYSIS of this phone screen interview transcript.

CANDIDATE BACKGROUND (for context):
- Known skills: {', '.join(candidate_skills[:10]) if candidate_skills else 'None specified'}
- Domains: {', '.join(candidate_domains) if candidate_domains else 'None specified'}
- Research papers: {len(candidate_papers)} papers
- Research contributions: {', '.join(research_contributions[:5]) if research_contributions else 'None'}
- GitHub repos: {len(candidate_repos)} repos

POSITION REQUIREMENTS:
- Title: {position.get('title', 'Unknown')}
- Must-have skills: {', '.join(position_must_haves) if position_must_haves else 'None specified'}
- Required domains: {', '.join(position_domains) if position_domains else 'None specified'}

TRANSCRIPT:
{transcript_text}

Perform a COMPREHENSIVE ANALYSIS and return JSON with:

1. TECHNICAL ASSESSMENT (not just skills - actual depth):
   - technical_depth: 0.0-1.0 (How deep is their technical knowledge? Can they explain complex concepts?)
   - problem_solving_ability: 0.0-1.0 (How do they approach problems? Systematic thinking?)
   - implementation_experience: 0.0-1.0 (Real hands-on experience vs theoretical knowledge?)
   - technical_communication: 0.0-1.0 (Can they explain technical concepts clearly?)
   - knowledge_gaps: List of areas where knowledge seems shallow or missing
   - technical_strengths: List of areas where they showed strong technical depth
   - red_flags: List of concerning technical responses (e.g., "couldn't explain own work", "surface-level answers")

2. BEHAVIORAL ASSESSMENT:
   - motivation_score: 0.0-1.0 (Genuine interest in role and company)
   - communication_score: 0.0-1.0 (Clarity, professionalism, ability to articulate)
   - cultural_fit: 0.0-1.0 (Alignment with company values and work style)
   - learning_ability: 0.0-1.0 (How they approach new challenges, growth mindset)
   - pressure_handling: 0.0-1.0 (How they handled tough technical questions)

3. EXPERIENCE VALIDATION:
   - experience_years: Number of years mentioned/validated
   - experience_details: List of specific experience examples mentioned
   - experience_depth: 0.0-1.0 (Depth of experience - junior vs senior level work)
   - skills_confirmed: List of skills they actually demonstrated (not just claimed)
   - skills_claimed_but_not_demonstrated: List of skills they mentioned but couldn't explain deeply

4. RESEARCH/ACADEMIC ASSESSMENT (if applicable):
   - research_depth: 0.0-1.0 (If they have papers, how well did they explain their research?)
   - research_to_production_bridge: 0.0-1.0 (Can they connect research to practical applications?)
   - publication_quality_validation: Assessment of whether their research claims match their explanations

5. OVERALL ANALYSIS:
   - overall_assessment: Detailed paragraph analyzing their fit for the role
   - standout_qualities: List of exceptional qualities or responses
   - concerns: List of specific concerns or red flags
   - recommendation_strength: "strong_yes", "yes", "maybe", "no", "strong_no"
   - key_insights: List of 3-5 key insights from the conversation

6. SPECIFIC EXAMPLES (for evidence):
   - strong_technical_examples: List of specific technical answers that impressed
   - weak_technical_examples: List of technical answers that were concerning
   - communication_examples: Specific examples of good/poor communication

Return ONLY valid JSON, no other text. Be thorough and analytical, not just extracting surface-level information."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Parse JSON from response
            import json
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                extracted = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from Grok response: {content[:200]}")
                # Return default values
                extracted = {
                    "motivation_score": 0.5,
                    "communication_score": 0.5,
                    "technical_depth": 0.5,
                    "cultural_fit": 0.5,
                    "skills": [],
                    "experience": []
                }
            
            # Ensure all required fields are present with comprehensive analysis
            result = {
                # Technical assessment
                "technical_depth": float(extracted.get("technical_depth", 0.5)),
                "problem_solving_ability": float(extracted.get("problem_solving_ability", 0.5)),
                "implementation_experience": float(extracted.get("implementation_experience", 0.5)),
                "technical_communication": float(extracted.get("technical_communication", 0.5)),
                "knowledge_gaps": extracted.get("knowledge_gaps", []),
                "technical_strengths": extracted.get("technical_strengths", []),
                "red_flags": extracted.get("red_flags", []),
                
                # Behavioral assessment
                "motivation_score": float(extracted.get("motivation_score", 0.5)),
                "communication_score": float(extracted.get("communication_score", 0.5)),
                "cultural_fit": float(extracted.get("cultural_fit", 0.5)),
                "learning_ability": float(extracted.get("learning_ability", 0.5)),
                "pressure_handling": float(extracted.get("pressure_handling", 0.5)),
                
                # Experience validation
                "experience_years": extracted.get("experience_years"),
                "experience_details": extracted.get("experience_details", []),
                "experience_depth": float(extracted.get("experience_depth", 0.5)),
                "skills": extracted.get("skills_confirmed", extracted.get("skills", [])),
                "skills_claimed_but_not_demonstrated": extracted.get("skills_claimed_but_not_demonstrated", []),
                "experience": extracted.get("experience_details", extracted.get("experience", [])),
                
                # Research assessment (if applicable)
                "research_depth": float(extracted.get("research_depth", 0.5)) if candidate.get('papers') else None,
                "research_to_production_bridge": float(extracted.get("research_to_production_bridge", 0.5)) if candidate.get('papers') else None,
                
                # Overall analysis
                "overall_assessment": extracted.get("overall_assessment", "Analysis pending"),
                "standout_qualities": extracted.get("standout_qualities", []),
                "concerns": extracted.get("concerns", []),
                "recommendation_strength": extracted.get("recommendation_strength", "maybe"),
                "key_insights": extracted.get("key_insights", []),
                
                # Evidence/examples
                "strong_technical_examples": extracted.get("strong_technical_examples", []),
                "weak_technical_examples": extracted.get("weak_technical_examples", []),
                "communication_examples": extracted.get("communication_examples", [])
            }
            
            logger.info(f"Deep analysis complete: recommendation={result['recommendation_strength']}, "
                       f"technical_depth={result['technical_depth']:.2f}, "
                       f"red_flags={len(result['red_flags'])}, "
                       f"standout_qualities={len(result['standout_qualities'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting information: {e}")
            # Return default values on error
            return {
                "motivation_score": 0.5,
                "communication_score": 0.5,
                "technical_depth": 0.5,
                "cultural_fit": 0.5,
                "skills": [],
                "experience": []
            }

