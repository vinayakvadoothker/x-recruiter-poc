"""
dm_screening_service.py - DM screening service for candidate pipeline

This service handles the DM screening phase of the pipeline:
1. Analyzes candidate profile gaps
2. Generates smart DM (only asks for missing info + screening questions)
3. Sends DM via X API
4. Parses DM responses
5. Calculates screening score
6. Updates pipeline stages
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from backend.integrations.x_dm_service import XDMService
from backend.integrations.grok_api import GrokAPIClient
from backend.orchestration.pipeline_tracker import PipelineTracker
from backend.orchestration.outbound_gatherer import OutboundGatherer
from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context
from backend.embeddings import RecruitingKnowledgeGraphEmbedder
from backend.database.vector_db_client import VectorDBClient

logger = logging.getLogger(__name__)


class DMScreeningService:
    """
    DM screening service for candidate pipeline Phase 1.
    
    Handles smart DM generation, sending, response parsing, and screening scoring.
    """
    
    def __init__(
        self,
        dm_service: Optional[XDMService] = None,
        grok_client: Optional[GrokAPIClient] = None,
        pipeline_tracker: Optional[PipelineTracker] = None,
        gatherer: Optional[OutboundGatherer] = None,
        postgres: Optional[PostgresClient] = None,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None,
        vector_db: Optional[VectorDBClient] = None
    ):
        """
        Initialize DM screening service.
        
        Args:
            dm_service: X DM service instance
            grok_client: Grok API client instance
            pipeline_tracker: Pipeline tracker instance
            gatherer: Outbound gatherer instance
            postgres: PostgreSQL client instance
            embedder: Embedder instance for generating embeddings
            vector_db: Vector DB client for storing embeddings
        """
        # Initialize DM service - try to create if not provided
        if dm_service is None:
            try:
                self.dm_service = XDMService()
                logger.debug("Auto-initialized XDMService in DMScreeningService")
            except Exception as e:
                logger.warning(f"Failed to auto-initialize XDMService: {e}")
                self.dm_service = None
        else:
            self.dm_service = dm_service
        
        self.grok = grok_client or GrokAPIClient()
        self.pipeline = pipeline_tracker or PipelineTracker(postgres)
        self.gatherer = gatherer or OutboundGatherer()
        self.postgres = postgres or PostgresClient()
        self.company_context = get_company_context()
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.vector_db = vector_db or VectorDBClient()
    
    async def analyze_profile_gaps(self, candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze candidate profile to determine what information is missing.
        
        Uses Grok to intelligently determine gaps based on required fields.
        
        Args:
            candidate_profile: Existing candidate profile
        
        Returns:
            Dict with missing_fields list and existing_fields list
        """
        required_fields = [
            "name", "phone_number", "skills", "experience_years", 
            "domains", "expertise_level"
        ]
        
        valuable_fields = [
            "resume_text", "github_handle", "arxiv_author_id", 
            "linkedin_url", "email"
        ]
        
        missing_required = []
        missing_valuable = []
        existing_fields = []
        
        # Check required fields
        for field in required_fields:
            value = candidate_profile.get(field)
            if not value or (isinstance(value, list) and len(value) == 0):
                missing_required.append(field)
            else:
                existing_fields.append(field)
        
        # Check valuable fields
        for field in valuable_fields:
            value = candidate_profile.get(field)
            if not value:
                missing_valuable.append(field)
            else:
                existing_fields.append(field)
        
        return {
            "missing_required": missing_required,
            "missing_valuable": missing_valuable,
            "existing_fields": existing_fields
        }
    
    async def generate_smart_dm(
        self,
        candidate_profile: Dict[str, Any],
        position_title: str,
        gaps: Dict[str, Any]
    ) -> str:
        """
        Generate a smart DM that only asks for missing information.
        
        Uses Grok to generate a personalized, conversational DM.
        
        Args:
            candidate_profile: Existing candidate profile
            position_title: Position title they're interested in
            gaps: Gap analysis result
        
        Returns:
            Generated DM message text
        """
        name = candidate_profile.get("name", "there")
        existing_info = []
        
        # Build context about what we already know
        if candidate_profile.get("github_handle"):
            existing_info.append(f"GitHub: {candidate_profile['github_handle']}")
        if candidate_profile.get("skills"):
            skills = candidate_profile["skills"][:3] if isinstance(candidate_profile["skills"], list) else []
            if skills:
                existing_info.append(f"Skills: {', '.join(skills)}")
        
        missing_required = gaps["missing_required"]
        missing_valuable = gaps["missing_valuable"]
        
        prompt = f"""Generate a friendly, professional DM message for a candidate who commented "interested" on our position post.

Candidate Name: {name}
Position: {position_title}

What we already know about them:
{', '.join(existing_info) if existing_info else "Basic profile from X"}

What we need to collect:
Required fields: {', '.join(missing_required) if missing_required else "None - all required fields present"}
Valuable fields: {', '.join(missing_valuable) if missing_valuable else "None"}

Screening questions to include:
1. "What's your strongest technical skill, and can you give me a specific example of how you've used it in a real project?"
2. "How many years of experience do you have with [relevant domain]? What's the most complex problem you've solved in this area?"
3. "What domain are you most interested in? (e.g., LLM Inference, GPU Computing, etc.)"

Instructions:
- Only ask for information we DON'T already have (don't repeat what we know)
- Be friendly and conversational
- Include the screening questions naturally
- Ask for resume (paste text directly), phone number, GitHub (if missing), arXiv ID (if missing)
- Keep it concise but warm

Generate the DM message:"""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            
            # Extract just the message content from Grok API response
            # Response format: {"choices": [{"message": {"content": "..."}}], "id": "...", "object": "...", ...}
            if isinstance(response, dict):
                # Extract content from the standard Grok API response format
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # If content is empty, try alternative formats
                if not content:
                    content = response.get('content', response.get('text', response.get('message', '')))
                
                # Clean up: remove markdown code blocks if present
                if "```" in content:
                    # Extract text from code blocks
                    if "```" in content:
                        parts = content.split("```")
                        # Take the last part before closing ```
                        content = parts[-1].split("```")[0].strip() if len(parts) > 1 else content
                
                # Remove any JSON structure if accidentally included
                if content.startswith("{") and content.endswith("}"):
                    try:
                        import json
                        parsed = json.loads(content)
                        # If it's a JSON object, try to extract text fields
                        content = parsed.get('content', parsed.get('text', parsed.get('message', str(parsed))))
                    except:
                        pass
                
                # Ensure it's a string and clean whitespace
                if not isinstance(content, str):
                    content = str(content)
                
                return content.strip()
            else:
                # If response is not a dict, convert to string and clean
                return str(response).strip()
        except Exception as e:
            logger.error(f"Error generating smart DM: {e}")
            # Fallback to template
            return self._generate_fallback_dm(name, missing_required, missing_valuable)
    
    def _generate_fallback_dm(
        self,
        name: str,
        missing_required: List[str],
        missing_valuable: List[str]
    ) -> str:
        """Generate fallback DM if Grok fails."""
        message = f"Hi {name}! Thanks for your interest in our positions.\n\n"
        
        if missing_required or missing_valuable:
            message += "To build your profile, could you help us with:\n\n"
            
            if "phone_number" in missing_required:
                message += "• Phone number (format: +1234567890) - for scheduling a phone screen\n"
            if "resume_text" in missing_valuable:
                message += "• Resume (paste text directly)\n"
            if "github_handle" in missing_valuable:
                message += "• GitHub username\n"
            if "arxiv_author_id" in missing_valuable:
                message += "• arXiv author identifier (if you have one)\n"
            
            message += "\nQuick screening questions:\n"
            message += "• What's your strongest technical skill, and can you give me a specific example?\n"
            message += "• How many years of experience do you have?\n"
            message += "• What domain are you most interested in?\n"
        
        message += "\nLooking forward to learning more!"
        return message
    
    async def process_interested_candidate(
        self,
        x_handle: str,
        x_user_id: str,
        position_id: str,
        position_title: str,
        x_post_id: str,
        comment_text: str
    ) -> Dict[str, Any]:
        """
        Process a candidate who commented "interested" on an X post.
        
        This is the main entry point for DM screening:
        1. Check/create candidate profile
        2. Analyze gaps
        3. Enter pipeline (dm_screening stage)
        4. Generate and send smart DM
        5. Track in pipeline
        
        Args:
            x_handle: X username
            x_user_id: X user ID
            position_id: Position ID they're interested in
            position_title: Position title
            x_post_id: X post ID they commented on
            comment_text: Their comment text
        
        Returns:
            Dict with candidate_id, pipeline_stage_id, dm_sent status
        """
        try:
            # Step 1: Check if candidate profile exists
            candidate = await self._get_or_create_candidate(x_handle, x_user_id)
            candidate_id = candidate["id"]
            
            # Step 2: Analyze profile gaps
            gaps = await self.analyze_profile_gaps(candidate)
            
            # Step 3: Enter pipeline (dm_screening stage)
            stage_metadata = {
                "x_post_id": x_post_id,
                "x_handle": x_handle,
                "x_user_id": x_user_id,
                "comment_text": comment_text,
                "position_title": position_title,
                "missing_fields": gaps["missing_required"] + gaps["missing_valuable"],
                "existing_fields": gaps["existing_fields"]
            }
            
            pipeline_stage_id = self.pipeline.enter_stage(
                candidate_id=candidate_id,
                position_id=position_id,
                stage="dm_screening",
                metadata=stage_metadata
            )
            
            # Step 4: Generate smart DM
            dm_message = await self.generate_smart_dm(candidate, position_title, gaps)
            
            # Step 5: Create or get DM conversation and send DM
            dm_result = None
            x_conversation_id = None
            
            if not self.dm_service:
                logger.warning(f"DM service not initialized. Cannot send DM to {x_handle}.")
            elif not x_user_id:
                logger.warning(f"Missing x_user_id for {x_handle}. Cannot send DM.")
            else:
                try:
                    # First, check if we have an existing conversation for this candidate (any position)
                    # Since X API reuses the same conversation ID for the same participant,
                    # we should reuse it across positions
                    existing_conv = self.postgres.execute_one(
                        """
                        SELECT x_conversation_id FROM dm_conversations
                        WHERE candidate_id = %s AND company_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (candidate_id, self.company_context.get_company_id())
                    )
                    
                    if existing_conv:
                        x_conversation_id = existing_conv.get('x_conversation_id')
                        logger.debug(f"Reusing existing conversation {x_conversation_id} for candidate {candidate_id}")
                        # Send message to existing conversation
                        dm_result = await self.dm_service.send_dm_by_conversation_id(
                            conversation_id=x_conversation_id,
                            message=dm_message
                        )
                    else:
                        # Create new conversation or send by participant ID (creates conversation automatically)
                        dm_result = await self.dm_service.send_dm_by_participant_id(
                            participant_id=x_user_id,
                            message=dm_message
                        )
                        
                        # Extract conversation ID from response
                        # X API may return it in different places
                        if dm_result:
                            x_conversation_id = dm_result.get('dm_conversation_id')
                            # Also check dm_event if present
                            if not x_conversation_id:
                                dm_event = dm_result.get('dm_event', {})
                                x_conversation_id = dm_event.get('dm_conversation_id')
                    
                    # Store conversation in database (will handle duplicates gracefully)
                    if x_conversation_id:
                        self._store_dm_conversation(
                            candidate_id=candidate_id,
                            position_id=position_id,
                            x_conversation_id=x_conversation_id,
                            x_participant_id=x_user_id,
                            x_participant_handle=x_handle
                        )
                    
                    logger.info(f"DM sent to {x_handle} for position {position_id} (conversation: {x_conversation_id})")
                except Exception as e:
                    logger.error(f"Failed to send DM to {x_handle}: {e}", exc_info=True)
            
            # Step 6: Update pipeline metadata with DM info
            stage_metadata["dm_message"] = dm_message
            stage_metadata["dm_sent_at"] = datetime.now().isoformat() if dm_result else None
            stage_metadata["dm_requested_fields"] = gaps["missing_required"] + gaps["missing_valuable"]
            stage_metadata["x_conversation_id"] = x_conversation_id
            
            # Update the stage metadata (convert dict to JSON for JSONB field)
            import json
            self.postgres.execute_update(
                """
                UPDATE pipeline_stages
                SET metadata = %s::jsonb, updated_at = NOW()
                WHERE id = %s
                """,
                (json.dumps(stage_metadata), pipeline_stage_id)
            )
            
            return {
                "candidate_id": candidate_id,
                "pipeline_stage_id": pipeline_stage_id,
                "dm_sent": dm_result is not None,
                "x_conversation_id": x_conversation_id,
                "stage": "dm_screening"
            }
            
        except Exception as e:
            logger.error(f"Error processing interested candidate: {e}")
            raise
    
    async def _get_or_create_candidate(
        self,
        x_handle: str,
        x_user_id: str
    ) -> Dict[str, Any]:
        """Get existing candidate or create new one from X data."""
        company_id = self.company_context.get_company_id()
        
        # Try to find existing candidate by x_handle or x_user_id
        candidate = self.postgres.execute_one(
            """
            SELECT * FROM candidates
            WHERE (x_handle = %s OR x_user_id = %s)
              AND company_id = %s
            LIMIT 1
            """,
            (x_handle, x_user_id, company_id)
        )
        
        if candidate:
            return candidate
        
        # If not found, gather from X and create profile
        logger.info(f"Gathering candidate profile from X: {x_handle}")
        profile = await self.gatherer.gather_and_save_from_x(x_handle)
        
        # Save to PostgreSQL
        candidate_id = profile.get("id", f"x_{x_handle}")
        self._save_candidate_to_postgres(profile, candidate_id)
        
        # Get the saved candidate
        candidate = self.postgres.execute_one(
            """
            SELECT * FROM candidates
            WHERE id = %s AND company_id = %s
            LIMIT 1
            """,
            (candidate_id, company_id)
        )
        
        # Generate and store embedding for the new candidate
        if candidate:
            await self._update_candidate_embedding(candidate_id, company_id)
        
        return candidate or profile
    
    def _save_candidate_to_postgres(self, profile: Dict[str, Any], candidate_id: str):
        """Save candidate profile to PostgreSQL."""
        company_id = self.company_context.get_company_id()
        
        # Convert lists/dicts to JSONB-compatible format (JSON strings)
        skills = json.dumps(profile.get("skills", []))
        domains = json.dumps(profile.get("domains", []))
        experience = json.dumps(profile.get("experience", []))
        education = json.dumps(profile.get("education", []))
        projects = json.dumps(profile.get("projects", []))
        resume_parsed = json.dumps(profile.get("resume_parsed")) if profile.get("resume_parsed") else None
        last_gathered_from = json.dumps(profile.get("last_gathered_from", []))
        gathering_timestamp = json.dumps(profile.get("gathering_timestamp")) if profile.get("gathering_timestamp") else None
        
        self.postgres.execute_update(
            """
            INSERT INTO candidates (
                id, company_id, name, phone_number, email,
                github_handle, github_user_id, x_handle, x_user_id,
                linkedin_url, arxiv_author_id, orcid_id,
                skills, domains, experience_years, expertise_level,
                experience, education, projects,
                resume_text, resume_url, resume_parsed,
                source, data_completeness, last_gathered_from, gathering_timestamp
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s::jsonb, %s::jsonb, %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                %s, %s, %s::jsonb,
                %s, %s, %s::jsonb, %s::jsonb
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                phone_number = COALESCE(EXCLUDED.phone_number, candidates.phone_number),
                email = COALESCE(EXCLUDED.email, candidates.email),
                github_handle = COALESCE(EXCLUDED.github_handle, candidates.github_handle),
                x_handle = COALESCE(EXCLUDED.x_handle, candidates.x_handle),
                x_user_id = COALESCE(EXCLUDED.x_user_id, candidates.x_user_id),
                skills = EXCLUDED.skills,
                domains = EXCLUDED.domains,
                experience_years = COALESCE(EXCLUDED.experience_years, candidates.experience_years),
                updated_at = NOW()
            """,
            (
                candidate_id, company_id,
                profile.get("name", "Unknown"),
                profile.get("phone_number"),
                profile.get("email"),
                profile.get("github_handle"),
                profile.get("github_user_id"),
                profile.get("x_handle"),
                profile.get("x_user_id"),
                profile.get("linkedin_url"),
                profile.get("arxiv_author_id"),
                profile.get("orcid_id"),
                skills, domains,
                profile.get("experience_years"),
                profile.get("expertise_level"),
                experience, education, projects,
                profile.get("resume_text"),
                profile.get("resume_url"),
                resume_parsed,
                profile.get("source", "inbound"),
                profile.get("data_completeness", 0.0),
                last_gathered_from,
                gathering_timestamp
            )
        )
    
    def _store_dm_conversation(
        self,
        candidate_id: str,
        position_id: str,
        x_conversation_id: str,
        x_participant_id: str,
        x_participant_handle: str
    ):
        """Store DM conversation in database for tracking."""
        company_id = self.company_context.get_company_id()
        
        # Check if conversation already exists (same conversation ID might be used for multiple positions)
        existing = self.postgres.execute_one(
            """
            SELECT id, candidate_id, position_id 
            FROM dm_conversations 
            WHERE x_conversation_id = %s AND company_id = %s
            """,
            (x_conversation_id, company_id)
        )
        
        if existing:
            # Conversation already exists - check if this candidate-position pair needs to be added
            existing_candidate = existing.get('candidate_id')
            existing_position = existing.get('position_id')
            
            if existing_candidate == candidate_id and existing_position == position_id:
                # Same candidate-position pair, just update
                self.postgres.execute_update(
                    """
                    UPDATE dm_conversations
                    SET x_participant_id = %s,
                        x_participant_handle = %s,
                        status = 'active',
                        updated_at = NOW()
                    WHERE x_conversation_id = %s 
                      AND candidate_id = %s 
                      AND position_id = %s
                      AND company_id = %s
                    """,
                    (x_participant_id, x_participant_handle, x_conversation_id, 
                     candidate_id, position_id, company_id)
                )
            else:
                # Different candidate or position - this is expected (same conversation, different position)
                # Just log it, don't create duplicate
                logger.debug(
                    f"Conversation {x_conversation_id} already exists for "
                    f"candidate {existing_candidate}, position {existing_position}. "
                    f"Skipping duplicate insert for candidate {candidate_id}, position {position_id}."
                )
        else:
            # New conversation - insert it
            try:
                self.postgres.execute_update(
                    """
                    INSERT INTO dm_conversations 
                        (company_id, candidate_id, position_id, x_conversation_id, 
                         x_participant_id, x_participant_handle, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())
                    ON CONFLICT (candidate_id, position_id) 
                    DO UPDATE SET 
                        x_conversation_id = EXCLUDED.x_conversation_id,
                        x_participant_id = EXCLUDED.x_participant_id,
                        x_participant_handle = EXCLUDED.x_participant_handle,
                        status = 'active',
                        updated_at = NOW()
                    """,
                    (company_id, candidate_id, position_id, x_conversation_id, 
                     x_participant_id, x_participant_handle)
                )
            except Exception as e:
                # Handle case where x_conversation_id unique constraint is violated
                # (conversation exists but for different candidate/position)
                if "x_conversation_id_key" in str(e) or "unique constraint" in str(e).lower():
                    logger.debug(
                        f"Conversation {x_conversation_id} already exists in database. "
                        f"Skipping insert for candidate {candidate_id}, position {position_id}."
                    )
                else:
                    raise
    
    async def process_dm_response(
        self,
        candidate_id: str,
        position_id: str,
        dm_message_text: str
    ) -> Dict[str, Any]:
        """
        Process a DM response from a candidate.
        
        Parses the response, extracts information, calculates screening score,
        and updates pipeline stages.
        
        Args:
            candidate_id: Candidate identifier
            position_id: Position ID
            dm_message_text: The DM message text from candidate
        
        Returns:
            Dict with extracted_fields, screening_score, new_stage
        """
        try:
            logger.info(
                f"🔄 PROCESSING DM RESPONSE: Starting for candidate {candidate_id}, "
                f"position {position_id}, message length: {len(dm_message_text)}"
            )
            
            # Get current pipeline stage
            current_stage = self.pipeline.get_current_stage(candidate_id, position_id)
            logger.info(
                f"🔄 PROCESSING DM RESPONSE: Current stage: {current_stage.get('stage') if current_stage else 'None'}"
            )
            
            if not current_stage:
                logger.warning(
                    f"⚠️ PROCESSING DM RESPONSE: No pipeline stage found for candidate {candidate_id}, "
                    f"position {position_id}. Creating dm_screening stage..."
                )
                # Create dm_screening stage if it doesn't exist
                self.pipeline.transition_stage(
                    candidate_id=candidate_id,
                    position_id=position_id,
                    new_stage="dm_screening",
                    metadata={"dm_requested_fields": []}
                )
                current_stage = self.pipeline.get_current_stage(candidate_id, position_id)
            
            if current_stage["stage"] != "dm_screening":
                logger.warning(
                    f"⚠️ PROCESSING DM RESPONSE: Candidate {candidate_id} is in stage '{current_stage['stage']}', "
                    f"not 'dm_screening'. Transitioning to dm_screening..."
                )
                # Transition to dm_screening stage
                self.pipeline.transition_stage(
                    candidate_id=candidate_id,
                    position_id=position_id,
                    new_stage="dm_screening",
                    metadata=current_stage.get("metadata", {})
                )
                current_stage = self.pipeline.get_current_stage(candidate_id, position_id)
            
            stage_metadata = current_stage.get("metadata", {})
            requested_fields = stage_metadata.get("dm_requested_fields", [])
            
            logger.info(
                f"🔄 PROCESSING DM RESPONSE: Requested fields: {requested_fields}, "
                f"Extracting all data in a single Grok call..."
            )
            
            # Extract everything in a single Grok call for efficiency
            extracted_fields, screening_responses, screening_score = await self._extract_all_from_dm(
                dm_message_text,
                requested_fields
            )
            
            logger.info(
                f"✅ EXTRACTION COMPLETE: Extracted {len(extracted_fields)} fields, "
                f"{len(screening_responses)} screening responses, score: {screening_score:.2f}"
            )
            
            # Update candidate profile with extracted fields (triggers async gathering)
            await self._update_candidate_profile(candidate_id, extracted_fields, screening_responses, screening_score)
            
            # Update pipeline stage
            stage_metadata["dm_response_received_at"] = datetime.now().isoformat()
            stage_metadata["extracted_fields"] = extracted_fields
            stage_metadata["screening_responses"] = screening_responses
            stage_metadata["screening_score"] = screening_score
            
            # Transition to next stage based on score
            if screening_score >= 0.5:
                new_stage = "dm_screening_passed"
            else:
                new_stage = "dm_screening_failed"
            
            self.pipeline.transition_stage(
                candidate_id=candidate_id,
                position_id=position_id,
                new_stage=new_stage,
                metadata=stage_metadata
            )
            
            return {
                "extracted_fields": extracted_fields,
                "screening_responses": screening_responses,
                "screening_score": screening_score,
                "new_stage": new_stage
            }
            
        except Exception as e:
            logger.error(f"Error processing DM response: {e}")
            raise
    
    async def _extract_all_from_dm(
        self,
        dm_text: str,
        requested_fields: List[str]
    ) -> tuple:
        """
        Extract all information from DM in a single Grok API call.
        
        Returns:
            (extracted_fields, screening_responses, screening_score)
        """
        # Build field extraction instructions
        field_instructions = []
        if "resume_text" in requested_fields:
            field_instructions.append("- resume_text: Full resume text if provided")
        if "github_handle" in requested_fields:
            field_instructions.append("- github_handle: GitHub username (e.g., @username or github.com/username)")
        if "arxiv_id" in requested_fields or "arxiv_author_id" in requested_fields:
            field_instructions.append("- arxiv_author_id: arXiv author ID if mentioned")
        if "phone_number" in requested_fields:
            field_instructions.append("- phone_number: Phone number if provided")
        if "email" in requested_fields:
            field_instructions.append("- email: Email address if provided")
        if "linkedin_url" in requested_fields:
            field_instructions.append("- linkedin_url: LinkedIn profile URL if provided")
        
        fields_section = "\n".join(field_instructions) if field_instructions else "No specific fields requested."
        
        prompt = f"""Analyze this candidate's DM response and extract ALL information in a single response.

DM Message: {dm_text}

Extract the following:

1. REQUESTED FIELDS (only if present in the message):
{fields_section}

2. SCREENING RESPONSES:
- strongest_skill: Their strongest technical skill and a specific example
- experience_years: Years of experience mentioned (as a number)
- complex_problem: Most complex problem they've solved
- domain_interest: Domain they're most interested in (e.g., LLM Inference, GPU Computing)

3. SCREENING SCORE (0.0-1.0):
Evaluate based on:
- Technical depth: Can they explain their work clearly?
- Experience validation: Do their claims seem realistic?
- Communication: Can they articulate clearly?
- Specificity: Do they provide concrete examples?

Score Guidelines:
- 0.0-0.3: Poor (vague answers, no examples, unclear communication)
- 0.3-0.5: Below threshold (some info but lacks depth)
- 0.5-0.7: Good (clear examples, good communication)
- 0.7-1.0: Excellent (strong technical depth, specific examples)

Be strict - filter out ~90% of candidates (most should score < 0.5).

Return ONLY a JSON object with this exact structure:
{{
    "extracted_fields": {{
        "resume_text": "...",
        "github_handle": "...",
        "phone_number": "...",
        "email": "...",
        "linkedin_url": "...",
        "arxiv_author_id": "..."
    }},
    "screening_responses": {{
        "strongest_skill": "...",
        "experience_years": 5,
        "complex_problem": "...",
        "domain_interest": "..."
    }},
    "screening_score": {{
        "score": 0.75,
        "reasoning": "Brief explanation"
    }}
}}

Only include fields that are actually present in the message. Set missing fields to null.
"""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            import json
            
            # Parse response
            if isinstance(response, str):
                # Try to extract JSON from markdown code blocks if present
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                result = json.loads(response)
            else:
                result = response
            
            # Extract components
            extracted_fields = result.get("extracted_fields", {})
            # Remove null values
            extracted_fields = {k: v for k, v in extracted_fields.items() if v is not None}
            
            screening_responses = result.get("screening_responses", {})
            # Remove null values
            screening_responses = {k: v for k, v in screening_responses.items() if v is not None}
            
            score_data = result.get("screening_score", {})
            screening_score = float(score_data.get("score", 0.0)) if isinstance(score_data, dict) else float(score_data) if isinstance(score_data, (int, float)) else 0.0
            
            return extracted_fields, screening_responses, screening_score
            
        except Exception as e:
            logger.error(f"Error extracting all from DM: {e}", exc_info=True)
            # Fallback: return empty dicts and basic score
            return {}, {}, 0.3
    
    async def _extract_screening_responses(self, dm_text: str) -> Dict[str, Any]:
        """Extract screening question responses from DM text."""
        prompt = f"""Extract screening question responses from this candidate's DM message.

DM Message: {dm_text}

Extract the following information:
1. strongest_skill: Their strongest technical skill and a specific example
2. experience_years: Years of experience mentioned
3. complex_problem: Most complex problem they've solved
4. domain_interest: Domain they're most interested in (e.g., LLM Inference, GPU Computing)

Return JSON with these fields. If a field is not mentioned, set it to null.
Example: {{"strongest_skill": "CUDA programming - built GPU acceleration for LLM inference", "experience_years": 5, "complex_problem": "Optimized inference latency by 50%", "domain_interest": "LLM Inference"}}
"""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            import json
            return json.loads(response) if isinstance(response, str) else response
        except Exception as e:
            logger.warning(f"Error extracting screening responses: {e}")
            return {}
    
    async def _calculate_screening_score(
        self,
        dm_text: str,
        screening_responses: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> float:
        """
        Calculate screening score (0.0-1.0) based on DM response quality.
        
        Uses Grok to analyze the response and assign a score.
        Score >= 0.5 means pass, < 0.5 means fail (filters ~90%).
        """
        prompt = f"""Analyze this candidate's DM response and assign a screening score (0.0-1.0).

DM Message: {dm_text}

Screening Responses: {screening_responses}

Extracted Fields: {extracted_fields}

Evaluate based on:
1. Technical depth: Can they explain their work clearly?
2. Experience validation: Do their claims seem realistic?
3. Communication: Can they articulate clearly?
4. Specificity: Do they provide concrete examples?

Score Guidelines:
- 0.0-0.3: Poor (vague answers, no examples, unclear communication)
- 0.3-0.5: Below threshold (some info but lacks depth)
- 0.5-0.7: Good (clear examples, good communication)
- 0.7-1.0: Excellent (strong technical depth, specific examples)

Return ONLY a JSON object with:
{{
    "score": 0.75,
    "reasoning": "Brief explanation of the score"
}}

Be strict - filter out ~90% of candidates (most should score < 0.5).
"""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            import json
            result = json.loads(response) if isinstance(response, str) else response
            return float(result.get("score", 0.0))
        except Exception as e:
            logger.warning(f"Error calculating screening score: {e}")
            # Fallback: basic heuristic
            has_example = "example" in dm_text.lower() or "built" in dm_text.lower() or "worked" in dm_text.lower()
            has_experience = screening_responses.get("experience_years") is not None
            has_skill = screening_responses.get("strongest_skill") is not None
            return 0.6 if (has_example and has_experience and has_skill) else 0.3
    
    async def _update_candidate_profile(
        self,
        candidate_id: str,
        extracted_fields: Dict[str, Any],
        screening_responses: Dict[str, Any],
        screening_score: float
    ):
        """
        Update candidate profile with extracted fields and screening data.
        
        Also triggers async gathering from GitHub, arXiv, and X if new identifiers are found.
        """
        company_id = self.company_context.get_company_id()
        
        # Get current candidate profile to check what we already have
        current_candidate = self.postgres.execute_one(
            """
            SELECT * FROM candidates
            WHERE id = %s AND company_id = %s
            """,
            (candidate_id, company_id)
        )
        
        # Build update query dynamically based on extracted fields
        updates = []
        params = []
        
        if "resume_text" in extracted_fields:
            updates.append("resume_text = %s")
            params.append(extracted_fields["resume_text"])
        
        if "phone_number" in extracted_fields:
            updates.append("phone_number = %s")
            params.append(extracted_fields["phone_number"])
        
        # Track new identifiers for async gathering
        new_github_handle = None
        new_arxiv_id = None
        x_handle = None
        
        if "github_handle" in extracted_fields:
            github_handle = extracted_fields["github_handle"]
            # Check if this is a new GitHub handle we don't have data for
            if not current_candidate or not current_candidate.get("github_handle"):
                new_github_handle = github_handle
            updates.append("github_handle = %s")
            params.append(github_handle)
        
        if "arxiv_id" in extracted_fields or "arxiv_author_id" in extracted_fields:
            arxiv_id = extracted_fields.get("arxiv_id") or extracted_fields.get("arxiv_author_id")
            # Check if this is a new arXiv ID we don't have data for
            if not current_candidate or not current_candidate.get("arxiv_author_id"):
                new_arxiv_id = arxiv_id
            updates.append("arxiv_author_id = %s")
            params.append(arxiv_id)
        
        if "linkedin_url" in extracted_fields:
            updates.append("linkedin_url = %s")
            params.append(extracted_fields["linkedin_url"])
        
        if "email" in extracted_fields:
            updates.append("email = %s")
            params.append(extracted_fields["email"])
        
        # Update screening data
        updates.append("screening_score = %s")
        params.append(screening_score)
        
        # Convert screening_responses to JSON string for JSONB field
        import json
        updates.append("screening_responses = %s::jsonb")
        params.append(json.dumps(screening_responses) if screening_responses else None)
        
        updates.append("updated_at = NOW()")
        
        if updates:
            params.append(candidate_id)
            params.append(company_id)
            
            query = f"""
                UPDATE candidates
                SET {', '.join(updates)}
                WHERE id = %s AND company_id = %s
            """
            
            self.postgres.execute_update(query, tuple(params))
            
            # Update embedding immediately with extracted fields (before async gathering)
            # This ensures embedding reflects DM response data right away
            asyncio.create_task(self._update_candidate_embedding(candidate_id, company_id))
        
        # Trigger async gathering from new sources
        if new_github_handle or new_arxiv_id or (current_candidate and current_candidate.get("x_handle")):
            # Run gathering asynchronously (fire and forget)
            asyncio.create_task(self._gather_from_sources_async(
                candidate_id=candidate_id,
                github_handle=new_github_handle,
                arxiv_id=new_arxiv_id,
                x_handle=current_candidate.get("x_handle") if current_candidate else None
            ))
    
    async def _gather_from_sources_async(
        self,
        candidate_id: str,
        github_handle: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        x_handle: Optional[str] = None
    ):
        """
        Asynchronously gather data from GitHub, arXiv, and X sources.
        
        This runs in the background (fire and forget) and merges gathered data 
        into the candidate profile. All gathering happens in parallel for speed.
        """
        """
        Asynchronously gather data from GitHub, arXiv, and X sources.
        
        This runs in the background and merges gathered data into the candidate profile.
        """
        try:
            logger.info(
                f"Starting async gathering for candidate {candidate_id}: "
                f"github={github_handle}, arxiv={arxiv_id}, x={x_handle}"
            )
            
            # Gather from all sources in parallel (async)
            gather_tasks = []
            
            if github_handle:
                gather_tasks.append(('github', self.gatherer.gather_from_github(github_handle)))
            
            if arxiv_id:
                gather_tasks.append(('arxiv', self.gatherer.gather_from_arxiv(arxiv_author_id=arxiv_id)))
            
            if x_handle:
                gather_tasks.append(('x', self.gatherer.gather_from_x(x_handle)))
            
            # Execute all gathering tasks in parallel
            gathered_data = {}
            if gather_tasks:
                logger.info(f"Gathering from {len(gather_tasks)} source(s) in parallel...")
                results = await asyncio.gather(*[task[1] for task in gather_tasks], return_exceptions=True)
                
                for (source_name, _), result in zip(gather_tasks, results):
                    if isinstance(result, Exception):
                        logger.warning(f"Error gathering from {source_name}: {result}")
                        continue
                    
                    if not result:
                        continue
                    
                    if source_name == 'github':
                        gathered_data.update(result)
                        logger.info(f"✅ Gathered GitHub data: {len(result.get('repos', []))} repos")
                    elif source_name == 'arxiv':
                        # Merge arXiv data
                        if 'papers' in result:
                            gathered_data.setdefault('papers', []).extend(result['papers'])
                        if 'research_areas' in result:
                            gathered_data.setdefault('research_areas', []).extend(result['research_areas'])
                        if 'skills' in result:
                            gathered_data.setdefault('skills', []).extend(result['skills'])
                        if 'arxiv_stats' in result:
                            gathered_data['arxiv_stats'] = result['arxiv_stats']
                        logger.info(f"✅ Gathered arXiv data: {len(result.get('papers', []))} papers")
                    elif source_name == 'x':
                        # Merge X data
                        if 'skills' in result:
                            gathered_data.setdefault('skills', []).extend(result['skills'])
                        if 'domains' in result:
                            gathered_data.setdefault('domains', []).extend(result['domains'])
                        if 'experience' in result:
                            gathered_data.setdefault('experience', []).extend(result['experience'])
                        logger.info(f"✅ Gathered/refreshed X data")
            
            # Merge gathered data into candidate profile
            if gathered_data:
                await self._merge_gathered_data(
                    candidate_id, 
                    gathered_data,
                    github_handle=github_handle,
                    arxiv_id=arxiv_id,
                    x_handle=x_handle
                )
                logger.info(f"✅ Completed async gathering for candidate {candidate_id}")
            
        except Exception as e:
            logger.error(f"Error in async gathering for candidate {candidate_id}: {e}", exc_info=True)
    
    async def _merge_gathered_data(
        self, 
        candidate_id: str, 
        gathered_data: Dict[str, Any],
        github_handle: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        x_handle: Optional[str] = None
    ):
        """
        Merge gathered data from multiple sources into candidate profile.
        
        Combines data from GitHub, arXiv, and X into a unified profile.
        """
        company_id = self.company_context.get_company_id()
        
        # Get current candidate
        current = self.postgres.execute_one(
            """
            SELECT * FROM candidates
            WHERE id = %s AND company_id = %s
            """,
            (candidate_id, company_id)
        )
        
        if not current:
            logger.warning(f"Candidate {candidate_id} not found for merging")
            return
        
        # Merge skills (deduplicate)
        current_skills = set(current.get('skills', []) or [])
        new_skills = set(gathered_data.get('skills', []))
        merged_skills = list(current_skills.union(new_skills))
        
        # Merge domains (deduplicate)
        current_domains = set(current.get('domains', []) or [])
        new_domains = set(gathered_data.get('domains', []))
        merged_domains = list(current_domains.union(new_domains))
        
        # Merge experience
        current_experience = current.get('experience', []) or []
        new_experience = gathered_data.get('experience', []) or []
        merged_experience = list(set(current_experience + new_experience))
        
        # Merge repos (if from GitHub)
        current_repos = current.get('repos', []) or []
        new_repos = gathered_data.get('repos', []) or []
        # Deduplicate by repo ID
        repo_ids = {repo.get('id') for repo in current_repos if repo.get('id')}
        merged_repos = current_repos + [r for r in new_repos if r.get('id') not in repo_ids]
        
        # Merge papers (if from arXiv)
        current_papers = current.get('papers', []) or []
        new_papers = gathered_data.get('papers', []) or []
        # Deduplicate by paper ID
        paper_ids = {p.get('id') for p in current_papers if p.get('id')}
        merged_papers = current_papers + [p for p in new_papers if p.get('id') not in paper_ids]
        
        # Update candidate with merged data
        updates = []
        params = []
        
        # Convert all JSONB fields to JSON strings
        import json
        
        if merged_skills:
            updates.append("skills = %s::jsonb")
            params.append(json.dumps(merged_skills))
        
        if merged_domains:
            updates.append("domains = %s::jsonb")
            params.append(json.dumps(merged_domains))
        
        if merged_experience:
            updates.append("experience = %s::jsonb")
            params.append(json.dumps(merged_experience))
        
        # Update repos (store in repos field)
        if merged_repos:
            updates.append("repos = %s::jsonb")
            params.append(json.dumps(merged_repos))
        
        # Update papers (store in papers field)
        if merged_papers:
            updates.append("papers = %s::jsonb")
            params.append(json.dumps(merged_papers))
        
        # Update GitHub stats if available
        if 'github_stats' in gathered_data:
            updates.append("github_stats = %s::jsonb")
            params.append(json.dumps(gathered_data['github_stats']))
        
        # Update arXiv stats if available
        if 'arxiv_stats' in gathered_data:
            updates.append("arxiv_stats = %s::jsonb")
            params.append(json.dumps(gathered_data['arxiv_stats']))
        
        # Update last_gathered_from and gathering_timestamp
        # Note: github_handle, arxiv_id, x_handle are passed to _merge_gathered_data
        # but we need to track what was actually gathered
        current_sources = set(current.get('last_gathered_from', []) or [])
        current_timestamps = current.get('gathering_timestamp', {}) or {}
        
        # Determine which sources were gathered based on what data we have
        new_sources = []
        if 'repos' in gathered_data or 'github_stats' in gathered_data:
            new_sources.append('github')
            current_timestamps['github'] = datetime.now().isoformat()
        if 'papers' in gathered_data or 'arxiv_stats' in gathered_data:
            new_sources.append('arxiv')
            current_timestamps['arxiv'] = datetime.now().isoformat()
        if 'skills' in gathered_data or 'domains' in gathered_data:
            # Check if this is from X (we already have X data if x_handle exists)
            if current.get('x_handle'):
                new_sources.append('x')
                current_timestamps['x'] = datetime.now().isoformat()
        
        updated_sources = list(current_sources.union(set(new_sources)))
        if updated_sources:
            updates.append("last_gathered_from = %s::jsonb")
            params.append(json.dumps(updated_sources))
            updates.append("gathering_timestamp = %s::jsonb")
            params.append(json.dumps(current_timestamps))
        
        updates.append("updated_at = NOW()")
        
        if updates:
            params.extend([candidate_id, company_id])
            
            query = f"""
                UPDATE candidates
                SET {', '.join(updates)}
                WHERE id = %s AND company_id = %s
            """
            
            self.postgres.execute_update(query, tuple(params))
            
            logger.info(
                f"Merged data for {candidate_id}: "
                f"{len(merged_skills)} skills, {len(merged_domains)} domains, "
                f"{len(merged_repos)} repos, {len(merged_papers)} papers"
            )
            
            # Update embedding in Weaviate with merged data
            await self._update_candidate_embedding(candidate_id, company_id)
    
    async def _update_candidate_embedding(self, candidate_id: str, company_id: str):
        """
        Update candidate embedding in Weaviate after data merge.
        
        Fetches the complete candidate profile from PostgreSQL and regenerates
        the embedding with all gathered data (repos, papers, etc.).
        """
        try:
            # Get complete candidate profile from PostgreSQL
            candidate = self.postgres.execute_one(
                """
                SELECT * FROM candidates
                WHERE id = %s AND company_id = %s
                """,
                (candidate_id, company_id)
            )
            
            if not candidate:
                logger.warning(f"Candidate {candidate_id} not found for embedding update")
                return
            
            # Convert PostgreSQL row to dict format expected by embedder
            # Handle JSONB fields that come as lists/dicts
            candidate_dict = dict(candidate)
            
            # Ensure JSONB fields are properly formatted
            # PostgreSQL returns JSONB as Python dict/list, but handle string case
            import json
            for jsonb_field in ['skills', 'domains', 'experience', 'education', 'projects', 
                              'repos', 'papers', 'last_gathered_from', 'github_stats', 
                              'arxiv_stats', 'resume_parsed', 'screening_responses']:
                value = candidate_dict.get(jsonb_field)
                if value is None:
                    continue
                if isinstance(value, str):
                    try:
                        candidate_dict[jsonb_field] = json.loads(value)
                    except:
                        # If not valid JSON, keep as string or set to empty
                        candidate_dict[jsonb_field] = [] if jsonb_field in ['skills', 'domains', 'experience', 'education', 'projects', 'repos', 'papers'] else {}
                # If already dict/list, keep as is
            
            # Generate new embedding with all gathered data
            embedding = self.embedder.embed_candidate(candidate_dict)
            
            # Update in Weaviate
            self.vector_db.store_candidate(candidate_id, embedding, candidate_dict)
            
            logger.info(f"✅ Updated embedding for candidate {candidate_id} with all gathered data")
            
        except Exception as e:
            logger.error(f"Error updating candidate embedding: {e}", exc_info=True)

