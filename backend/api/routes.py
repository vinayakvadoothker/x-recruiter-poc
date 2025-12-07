"""
API route handlers for Grok Recruiter endpoints.
"""

import logging
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional

from backend.api.models import (
    RoleRequest,
    OutreachRequest,
    FeedbackRequest,
    SourcingResponse,
    HealthResponse,
    Candidate,
    PhoneScreenRequest,
    PhoneScreenResponse,
    QueryRequest,
    ExceptionalTalentRequest,
    TeamCreateRequest,
    TeamUpdateRequest,
    TeamResponse,
    TeamChatRequest,
    TeamChatResponse,
    TeamChatMessage,
    InterviewerCreateRequest,
    InterviewerUpdateRequest,
    InterviewerResponse,
    InterviewerChatRequest,
    InterviewerChatMessage,
    MatchRequest,
    MatchResponse,
    PositionCreateRequest,
    PositionUpdateRequest,
    PositionResponse,
    PositionChatRequest,
    PositionChatMessage,
    PositionSimilarityResponse,
    PositionDistributionRequest,
    PostToXRequest
)
# TODO: Remove - pipeline.py deleted, will be replaced with new inbound pipeline
# from backend.orchestration.pipeline import RecruitingPipeline
from backend.orchestration.recruiter_agent import RecruiterAgent
from backend.simulator.x_dm_simulator import XDMSimulator
from backend.integrations.grok_api import GrokAPIClient
from backend.database.query_engine import QueryEngine
from backend.database.knowledge_graph import KnowledgeGraph
from backend.matching.exceptional_talent_finder import ExceptionalTalentFinder
from backend.matching.team_matcher import TeamPersonMatcher
from backend.database.postgres_client import PostgresClient
from backend.database.vector_db_client import VectorDBClient
from backend.database.weaviate_connection import create_weaviate_client
from backend.database.weaviate_schema import create_profile_schemas
from backend.orchestration.company_context import get_company_context
from backend.embeddings.recruiting_embedder import RecruitingKnowledgeGraphEmbedder

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize shared instances (lazy initialization to avoid errors if env vars not set)
_pipeline = None
_simulator = None
_grok_client = None
_recruiter_agent = None
_phone_screen_interviewer = None
_query_engine = None
_knowledge_graph = None
_exceptional_finder = None
_team_matcher = None
_postgres_client = None
_vector_db_client = None


# TODO: Remove - pipeline.py deleted, will be replaced with new inbound pipeline
# def get_pipeline() -> RecruitingPipeline:
#     """Get or create pipeline instance."""
#     global _pipeline
#     if _pipeline is None:
#         _pipeline = RecruitingPipeline()
#     return _pipeline


def get_simulator() -> XDMSimulator:
    """Get or create simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = XDMSimulator()
    return _simulator


def get_grok_client() -> GrokAPIClient:
    """Get or create Grok client instance."""
    global _grok_client
    if _grok_client is None:
        _grok_client = GrokAPIClient()
    return _grok_client


def get_recruiter_agent() -> RecruiterAgent:
    """Get or create recruiter agent instance."""
    global _recruiter_agent
    if _recruiter_agent is None:
        _recruiter_agent = RecruiterAgent(
            grok_client=get_grok_client(),
            pipeline=None,  # TODO: Replace with new inbound pipeline
            simulator=get_simulator()
)
    return _recruiter_agent


def get_phone_screen_interviewer():
    """Get or create phone screen interviewer instance."""
    global _phone_screen_interviewer
    if _phone_screen_interviewer is None:
        from backend.interviews.phone_screen_interviewer import PhoneScreenInterviewer
        _phone_screen_interviewer = PhoneScreenInterviewer()
    return _phone_screen_interviewer


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status of the API
    """
    return HealthResponse(status="ok")


@router.post("/sourcing", response_model=SourcingResponse)
async def trigger_sourcing(role: RoleRequest):
    """
    Trigger candidate sourcing for a role.
    
    Args:
        role: Role description and requirements
    
    Returns:
        List of sourced candidates with scores
    """
    try:
        # TODO: Replace with new inbound pipeline
        raise HTTPException(status_code=501, detail="Old pipeline removed - new inbound pipeline coming in pivot")
        # pipeline = get_pipeline()
        # result = await pipeline.process_role_request(
        #     role.description,
        #     role_title=role.title
        # )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        role_id = result.get('role_id')
        candidates_data = result.get('candidates', [])
        
        # Convert to Candidate models
        candidates = []
        for cand_data in candidates_data:
            candidate = Candidate(
                github_handle=cand_data.get('github_handle', ''),
                x_handle=cand_data.get('x_handle'),
                profile_data=cand_data.get('profile_data', {}),
                repos=cand_data.get('repos', []),
                skills=cand_data.get('skills', []),
                experience=cand_data.get('experience', []),
                education=cand_data.get('education', []),
                similarity_score=cand_data.get('similarity_score'),
                bandit_score=cand_data.get('bandit_score')
            )
            candidates.append(candidate)
        
        return SourcingResponse(
            role_id=role_id,
            candidates=candidates,
            total_found=len(candidates)
        )
        
    except Exception as e:
        logger.error(f"Error in sourcing endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sourcing candidates: {str(e)}")


@router.get("/candidates/{role_id}", response_model=List[Candidate])
async def get_candidates(role_id: str):
    """
    Get candidate list for a role.
    
    Args:
        role_id: Role identifier
    
    Returns:
        Ranked list of candidates with graph similarities and bandit scores
    """
    try:
        # TODO: Replace with new inbound pipeline
        raise HTTPException(status_code=501, detail="Old pipeline removed - new inbound pipeline coming in pivot")
        # pipeline = get_pipeline()
        # candidates_data = pipeline.get_candidates_for_role(role_id)
        
        if not candidates_data:
            raise HTTPException(status_code=404, detail=f"No candidates found for role {role_id}")
        
        # Convert to Candidate models
        candidates = []
        for cand_data in candidates_data:
            candidate = Candidate(
                github_handle=cand_data.get('github_handle', ''),
                x_handle=cand_data.get('x_handle'),
                profile_data=cand_data.get('profile_data', {}),
                repos=cand_data.get('repos', []),
                skills=cand_data.get('skills', []),
                experience=cand_data.get('experience', []),
                education=cand_data.get('education', []),
                similarity_score=cand_data.get('similarity_score'),
                bandit_score=cand_data.get('bandit_score')
            )
            candidates.append(candidate)
        
        # Sort by similarity score (descending)
        candidates.sort(key=lambda x: x.similarity_score or 0.0, reverse=True)
        
        return candidates
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving candidates: {str(e)}")


@router.post("/outreach")
async def send_outreach(outreach: OutreachRequest):
    """
    Send outreach message to a candidate.
    
    Args:
        outreach: Outreach request with candidate and role information
    
    Returns:
        Confirmation of outreach sent
    """
    try:
        # TODO: Replace with new inbound pipeline
        raise HTTPException(status_code=501, detail="Old pipeline removed - new inbound pipeline coming in pivot")
        # pipeline = get_pipeline()
        # grok_client = get_grok_client()
        # simulator = get_simulator()
        # candidates = pipeline.get_candidates_for_role(outreach.role_id)
        candidate = None
        for cand in candidates:
            if cand.get('github_handle') == outreach.candidate_id:
                candidate = cand
                break
        
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {outreach.candidate_id} not found")
        
        role_data = pipeline.get_role_data(outreach.role_id)
        if not role_data:
            raise HTTPException(status_code=404, detail=f"Role {outreach.role_id} not found")
        
        # Generate personalized message using Grok if not provided
        if outreach.message:
            message = outreach.message
        else:
            prompt = f"""Generate a personalized outreach message for a candidate:

Candidate: {candidate.get('github_handle')}
Role: {role_data.get('title', 'Position')}
Role Description: {role_data.get('description', '')[:200]}

Keep it concise (under 200 characters), friendly, and professional."""
            
            try:
                response = await grok_client._make_chat_request(prompt)
                message = response.get("choices", [{}])[0].get("message", {}).get("content", "Hi! I have an exciting opportunity that might interest you.")
            except Exception as e:
                logger.warning(f"Error generating message: {e}")
                message = f"Hi @{candidate.get('github_handle')}! I have an exciting opportunity that might interest you."
        
        # Send via simulator (store in chat history)
        simulator.send_message(f"Outreach to @{outreach.candidate_id}: {message}", sender="system")
        
        return {
            "status": "sent",
            "candidate_id": outreach.candidate_id,
            "message": message,
            "sent_via": "simulator"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending outreach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sending outreach: {str(e)}")


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback on a candidate.
    
    Args:
        feedback: Feedback data including type and reward
    
    Returns:
        Confirmation of feedback processed
    """
    try:
        recruiter_agent = get_recruiter_agent()
        simulator = get_simulator()
        # Process feedback through recruiter agent
        feedback_text = feedback.feedback_text or feedback.feedback_type
        confirmation = await recruiter_agent.collect_feedback(
            feedback_text,
            candidate_id=feedback.candidate_id,
            role_id=feedback.role_id
        )
        
        # Store feedback in simulator
        simulator.send_message(
            f"Feedback on {feedback.candidate_id}: {feedback.feedback_type}",
            sender="system"
        )
        
        return {
            "status": "processed",
            "candidate_id": feedback.candidate_id,
            "feedback_type": feedback.feedback_type,
            "message": confirmation
        }
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")


@router.post("/phone-screen", response_model=PhoneScreenResponse)
async def conduct_phone_screen(request: PhoneScreenRequest):
    """
    Conduct automated phone screen interview via Vapi.
    
    Args:
        request: Phone screen request with candidate_id and position_id
    
    Returns:
        Phone screen result with decision and extracted information
    """
    try:
        interviewer = get_phone_screen_interviewer()
        
        result = await interviewer.conduct_phone_screen(
            candidate_id=request.candidate_id,
            position_id=request.position_id
        )
        
        return PhoneScreenResponse(
            candidate_id=result["candidate_id"],
            position_id=result["position_id"],
            call_id=result["call_id"],
            decision=result["decision"],
            extracted_info=result["extracted_info"],
            status="completed"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in phone screen: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error conducting phone screen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error conducting phone screen: {str(e)}")


def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create knowledge graph instance."""
    global _knowledge_graph, _postgres_client
    if _knowledge_graph is None:
        import os
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        # Get PostgreSQL client for teams/interviewers/positions
        postgres = get_postgres_client()
        _knowledge_graph = KnowledgeGraph(url=weaviate_url, postgres_client=postgres)
    return _knowledge_graph


def get_query_engine() -> QueryEngine:
    """Get or create query engine instance."""
    global _query_engine
    if _query_engine is None:
        _query_engine = QueryEngine(knowledge_graph=get_knowledge_graph())
    return _query_engine


@router.post("/candidates/query", response_model=List[Dict])
async def query_candidates(request: QueryRequest):
    """
    Query candidates with complex filters and optional similarity search.
    
    Supports:
    - Ability cluster filtering
    - Skill-based queries (AND, OR, NOT)
    - Multi-criteria queries (arXiv papers, GitHub stars, X followers)
    - Hybrid search (metadata filters + vector similarity)
    
    Args:
        request: Query request with filters and optional similarity query
    
    Returns:
        List of candidate profiles matching the criteria
    """
    try:
        query_engine = get_query_engine()
        
        # Build filters dictionary
        filters = {}
        
        if request.cluster:
            filters['ability_cluster'] = request.cluster
        
        if request.required_skills or request.excluded_skills or request.optional_skills:
            filters['skills'] = {}
            if request.required_skills:
                filters['skills']['required'] = request.required_skills
            if request.excluded_skills:
                filters['skills']['excluded'] = request.excluded_skills
            if request.optional_skills:
                filters['skills']['optional'] = request.optional_skills
        
        if request.required_domains:
            filters['domains'] = {'required': request.required_domains}
        
        if request.min_arxiv_papers is not None:
            filters['arxiv_papers'] = {'min': request.min_arxiv_papers}
        
        if request.min_github_stars is not None:
            filters['github_stars'] = {'min': request.min_github_stars}
        
        if request.min_experience_years is not None:
            filters['experience_years'] = {'min': request.min_experience_years}
        
        # Execute query
        if filters:
            results = query_engine.query_candidates(
                filters=filters,
                similarity_query=request.similarity_query,
                top_k=request.top_k
            )
        elif request.cluster:
            # Simple cluster query
            results = query_engine.query_by_ability_cluster(
                cluster_name=request.cluster,
                top_k=request.top_k
            )
        elif request.required_skills or request.excluded_skills or request.optional_skills:
            # Simple skill query
            results = query_engine.query_by_skills(
                required_skills=request.required_skills or [],
                excluded_skills=request.excluded_skills,
                optional_skills=request.optional_skills,
                top_k=request.top_k
            )
        else:
            # Use exceptional talent query if criteria provided
            results = query_engine.query_exceptional_talent(
                min_arxiv_papers=request.min_arxiv_papers or 0,
                min_github_stars=request.min_github_stars or 0,
                min_x_followers=request.min_x_followers or 0,
                min_experience_years=request.min_experience_years or 0,
                required_domains=request.required_domains,
                top_k=request.top_k
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error querying candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error querying candidates: {str(e)}")


@router.post("/candidates/exceptional", response_model=List[Dict])
async def find_exceptional_talent(request: ExceptionalTalentRequest):
    """
    Find exceptional talent FOR A SPECIFIC POSITION (1 in 1,000,000 candidate).
    
    Combines exceptional talent signals with position fit to find candidates who are
    BOTH truly exceptional AND a perfect fit for the position.
    
    EXTREMELY STRICT: Only 0.0001% of candidates pass (1 in 1,000,000).
    Requires BOTH exceptional talent AND perfect position fit.
    
    Args:
        request: Exceptional talent query with position_id (REQUIRED) and minimum score threshold
    
    Returns:
        List of exceptional candidate profiles ranked by combined_score (exceptional * position_fit)
    """
    try:
        finder = get_exceptional_finder()
        
        # Use exceptional talent finder FOR SPECIFIC POSITION
        # This finds candidates who are BOTH exceptional AND perfect fit for the position
        results = finder.find_exceptional_talent(
            position_id=request.position_id,  # REQUIRED - position-specific
            min_score=request.min_score,
            top_k=request.top_k
        )
        
        # Optionally filter by additional criteria if provided
        if request.min_arxiv_papers > 0 or request.min_github_stars > 0 or request.min_x_followers > 0:
            filtered = []
            for result in results:
                evidence = result.get('evidence', {})
                if (evidence.get('arxiv_papers', 0) >= request.min_arxiv_papers and
                    evidence.get('github_stars', 0) >= request.min_github_stars and
                    evidence.get('x_followers', 0) >= request.min_x_followers):
                    filtered.append(result)
            results = filtered[:request.top_k]
        
        return results
        
    except Exception as e:
        logger.error(f"Error finding exceptional talent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding exceptional talent: {str(e)}")


def get_exceptional_finder() -> ExceptionalTalentFinder:
    """Get or create exceptional talent finder instance."""
    global _exceptional_finder, _knowledge_graph
    if _exceptional_finder is None:
        _exceptional_finder = ExceptionalTalentFinder(knowledge_graph=get_knowledge_graph())
    return _exceptional_finder


def get_team_matcher() -> TeamPersonMatcher:
    """Get or create team matcher instance."""
    global _team_matcher
    if _team_matcher is None:
        _team_matcher = TeamPersonMatcher(knowledge_graph=get_knowledge_graph())
    return _team_matcher


def get_vector_db_client() -> VectorDBClient:
    """Get or create vector DB client instance."""
    global _vector_db_client
    if _vector_db_client is None:
        import os
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        _vector_db_client = VectorDBClient(url=weaviate_url)
    return _vector_db_client


@router.post("/candidates/{candidate_id}/match", response_model=MatchResponse)
async def match_candidate(candidate_id: str, request: Optional[MatchRequest] = None):
    """
    Match candidate to team and interviewer.
    
    Uses TeamPersonMatcher to find the best team and interviewer for a candidate.
    If position_id is provided, matching will be position-specific.
    
    Args:
        candidate_id: Candidate ID
        request: Optional match request with position_id
    
    Returns:
        Match result with team and interviewer matches
    """
    try:
        matcher = get_team_matcher()
        
        # Match to team
        team_match_result = matcher.match_to_team(candidate_id)
        if "error" in team_match_result:
            raise HTTPException(status_code=404, detail=team_match_result["error"])
        
        team_id = team_match_result.get("team_id")
        team_match = {
            "team_id": team_match_result.get("team_id"),
            "team_name": team_match_result.get("team", {}).get("name"),
            "match_score": team_match_result.get("match_score"),
            "similarity": team_match_result.get("similarity"),
            "needs_match": team_match_result.get("needs_match"),
            "expertise_match": team_match_result.get("expertise_match"),
            "arxiv_boost": team_match_result.get("arxiv_boost"),
            "reasoning": team_match_result.get("reasoning")
        }
        
        # Match to interviewer (within the matched team)
        interviewer_match = None
        if team_id:
            interviewer_match_result = matcher.match_to_person(candidate_id, team_id)
            if "error" not in interviewer_match_result:
                interviewer_match = {
                    "interviewer_id": interviewer_match_result.get("interviewer_id"),
                    "interviewer_name": interviewer_match_result.get("interviewer", {}).get("name"),
                    "match_score": interviewer_match_result.get("match_score"),
                    "similarity": interviewer_match_result.get("similarity"),
                    "expertise_match": interviewer_match_result.get("expertise_match"),
                    "success_rate": interviewer_match_result.get("success_rate"),
                    "arxiv_boost": interviewer_match_result.get("arxiv_boost"),
                    "reasoning": interviewer_match_result.get("reasoning")
                }
        
        return MatchResponse(
            candidate_id=candidate_id,
            team_match=team_match,
            interviewer_match=interviewer_match,
            position_id=request.position_id if request else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error matching candidate: {str(e)}")


def _sync_embeddings_internal() -> Dict:
    """
    Internal function to sync embeddings.
    Can be called from other endpoints or the sync endpoint.
    """
    kg = get_knowledge_graph()
    postgres = get_postgres_client()
    company_context = get_company_context()
    company_id = company_context.get_company_id()
    
    results = {
        "teams": {"created": 0, "updated": 0, "total": 0},
        "interviewers": {"created": 0, "updated": 0, "total": 0},
        "positions": {"created": 0, "updated": 0, "total": 0}
    }
    
    # Get all existing embeddings from Weaviate
    vector_db = get_vector_db_client()
    existing_team_ids = set()
    existing_interviewer_ids = set()
    existing_position_ids = set()
    
    for profile_type, id_set in [
        ("Team", existing_team_ids),
        ("Interviewer", existing_interviewer_ids),
        ("Position", existing_position_ids)
    ]:
        embeddings = vector_db.get_all_embeddings(profile_type, limit=1000)
        for emb in embeddings:
            if emb.get("company_id") == company_id:
                id_set.add(emb.get("profile_id"))
    
    # Sync Teams
    teams = postgres.execute_query(
        "SELECT * FROM teams WHERE company_id = %s",
        (company_id,)
    )
    results["teams"]["total"] = len(teams)
    
    for team_row in teams:
        team = dict(team_row)
        team_id = team['id']
        
        # Check if embedding exists
        if team_id not in existing_team_ids:
            # Generate and store embedding
            try:
                kg.add_team(team)
                results["teams"]["created"] += 1
                logger.info(f"Created embedding for team: {team_id}")
            except Exception as e:
                logger.error(f"Failed to create embedding for team {team_id}: {e}")
        else:
            # Update embedding (in case data changed)
            try:
                kg.update_team(team_id, team)
                results["teams"]["updated"] += 1
                logger.debug(f"Updated embedding for team: {team_id}")
            except Exception as e:
                logger.error(f"Failed to update embedding for team {team_id}: {e}")
    
    # Sync Interviewers
    interviewers = postgres.execute_query(
        "SELECT * FROM interviewers WHERE company_id = %s",
        (company_id,)
    )
    results["interviewers"]["total"] = len(interviewers)
    
    for interviewer_row in interviewers:
        interviewer = dict(interviewer_row)
        interviewer_id = interviewer['id']
        
        # Check if embedding exists
        if interviewer_id not in existing_interviewer_ids:
            # Generate and store embedding
            try:
                kg.add_interviewer(interviewer)
                results["interviewers"]["created"] += 1
                logger.info(f"Created embedding for interviewer: {interviewer_id}")
            except Exception as e:
                logger.error(f"Failed to create embedding for interviewer {interviewer_id}: {e}")
        else:
            # Update embedding (in case data changed)
            try:
                kg.update_interviewer(interviewer_id, interviewer)
                results["interviewers"]["updated"] += 1
                logger.debug(f"Updated embedding for interviewer: {interviewer_id}")
            except Exception as e:
                logger.error(f"Failed to update embedding for interviewer {interviewer_id}: {e}")
    
    # Sync Positions (if positions table exists)
    try:
        # Check if positions table exists first
        table_exists = postgres.execute_query(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'positions'
            )
            """
        )
        if not table_exists or not table_exists[0].get('exists', False):
            logger.debug("Positions table does not exist, skipping position embeddings sync")
            results["positions"]["total"] = 0
        else:
            positions = postgres.execute_query(
                "SELECT * FROM positions WHERE company_id = %s",
                (company_id,)
            )
            results["positions"]["total"] = len(positions)
        
        for position_row in positions:
            position = dict(position_row)
            position_id = position['id']
            
            # Check if embedding exists
            if position_id not in existing_position_ids:
                # Generate and store embedding
                try:
                    kg.add_position(position)
                    results["positions"]["created"] += 1
                    logger.info(f"Created embedding for position: {position_id}")
                except Exception as e:
                    logger.error(f"Failed to create embedding for position {position_id}: {e}")
            else:
                # Update embedding (in case data changed)
                try:
                    kg.update_position(position_id, position)
                    results["positions"]["updated"] += 1
                    logger.debug(f"Updated embedding for position: {position_id}")
                except Exception as e:
                    logger.error(f"Failed to update embedding for position {position_id}: {e}")
    except Exception as e:
        # Positions table might not exist yet or other error
        logger.debug(f"Positions table not available: {e}")
        results["positions"]["total"] = 0
    
    total_created = (
        results["teams"]["created"] +
        results["interviewers"]["created"] +
        results["positions"]["created"]
    )
    total_updated = (
        results["teams"]["updated"] +
        results["interviewers"]["updated"] +
        results["positions"]["updated"]
    )
    
    return {
        "status": "success",
        "company_id": company_id,
        "results": results,
        "summary": {
            "total_created": total_created,
            "total_updated": total_updated,
            "total_processed": (
                results["teams"]["total"] +
                results["interviewers"]["total"] +
                results["positions"]["total"]
            )
        }
    }


@router.get("/weaviate/schema/status", response_model=Dict)
async def get_weaviate_schema_status():
    """
    Check the status of Weaviate schema collections.
    
    Returns:
        Dictionary with:
        - collections: List of existing collection names
        - required: List of required collection names
        - missing: List of missing required collections
        - status: "complete" if all required collections exist, "incomplete" otherwise
    """
    try:
        import os
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        client = create_weaviate_client(weaviate_url)
        
        # Get existing collections
        existing_collections = []
        try:
            all_collections = client.collections.list_all()
            for col in all_collections:
                if isinstance(col, str):
                    existing_collections.append(col)
                elif hasattr(col, 'name'):
                    existing_collections.append(col.name)
                elif hasattr(col, '__str__'):
                    existing_collections.append(str(col))
        except Exception as e:
            logger.warning(f"Error listing collections: {e}")
        
        required_collections = ["Candidate", "Team", "Interviewer", "Position"]
        missing_collections = [col for col in required_collections if col not in existing_collections]
        
        return {
            "collections": existing_collections,
            "required": required_collections,
            "missing": missing_collections,
            "status": "complete" if len(missing_collections) == 0 else "incomplete",
            "message": f"Found {len(existing_collections)} collections. Missing: {', '.join(missing_collections) if missing_collections else 'none'}"
        }
    except Exception as e:
        logger.error(f"Error checking Weaviate schema status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking Weaviate schema status: {str(e)}")


@router.post("/weaviate/schema/create", response_model=Dict)
async def create_weaviate_schema():
    """
    Manually create or verify Weaviate schema for all profile types.
    
    This endpoint:
    1. Creates missing collections (Candidate, Team, Interviewer, Position)
    2. Skips collections that already exist
    3. Returns detailed results about what was created/existed/errored
    
    Useful for:
    - Debugging schema issues
    - Recovering from schema corruption
    - Initial setup
    
    Returns:
        Dictionary with:
        - created: List of collection names that were created
        - existing: List of collection names that already existed
        - errors: List of error messages (if any)
    """
    try:
        import os
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        client = create_weaviate_client(weaviate_url)
        results = create_profile_schemas(client)
        
        return {
            "success": len(results['errors']) == 0,
            "created": results['created'],
            "existing": results['existing'],
            "errors": results['errors'],
            "message": f"Schema creation complete. Created: {len(results['created'])}, Existing: {len(results['existing'])}, Errors: {len(results['errors'])}"
        }
    except Exception as e:
        logger.error(f"Error creating Weaviate schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating Weaviate schema: {str(e)}")


@router.post("/embeddings/sync", response_model=Dict)
async def sync_embeddings():
    """
    Sync embeddings: Ensure all teams/interviewers/positions from PostgreSQL have embeddings in Weaviate.
    
    This endpoint:
    1. Gets all teams/interviewers/positions from PostgreSQL
    2. Checks which ones don't have embeddings in Weaviate
    3. Generates and stores missing embeddings
    
    Returns:
        Dictionary with sync results (created, updated, total)
    """
    try:
        return _sync_embeddings_internal()
    except Exception as e:
        logger.error(f"Error syncing embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error syncing embeddings: {str(e)}")


@router.get("/embeddings/graph", response_model=Dict)
async def get_embeddings_for_graph():
    """
    Get all embeddings for graph visualization with 3D dimensionality reduction.
    
    Returns embeddings for all profile types (candidates, teams, interviewers, positions)
    reduced to 3D coordinates using PCA.
    
    Note: This endpoint does NOT automatically sync embeddings. Use /api/embeddings/sync
    to manually sync embeddings if needed.
    
    Returns:
        Dictionary with embeddings data for each profile type, reduced to 3D
    """
    try:
        import numpy as np
        from sklearn.decomposition import PCA
        
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Get all embeddings for each profile type
        all_data = {
            "candidates": [],
            "teams": [],
            "interviewers": [],
            "positions": []
        }
        
        # Collect all embeddings across all profile types for combined PCA
        all_filtered_data = []
        all_embedding_vectors = []
        
        # Fetch embeddings from Weaviate (no automatic sync - use /api/embeddings/sync manually if needed)
        for profile_type in ["Candidate", "Team", "Interviewer", "Position"]:
            embeddings_data = vector_db.get_all_embeddings(profile_type, limit=1000)
            
            # Filter by company_id and extract embeddings
            filtered_data = []
            embedding_vectors = []
            
            for item in embeddings_data:
                if item.get("company_id") == company_id:
                    embedding = item.get("embedding")
                    if embedding and len(embedding) == 768:  # Validate embedding size
                        data_item = {
                            "profile_id": item.get("profile_id"),
                            "profile_type": profile_type.lower(),
                            "metadata": item.get("metadata", {})
                        }
                        filtered_data.append(data_item)
                        embedding_vectors.append(embedding)
            
                        # Also add to combined list for PCA
                        all_filtered_data.append(data_item)
                        all_embedding_vectors.append(embedding)
            
            # Store filtered data by type
            all_data[profile_type.lower() + "s"] = filtered_data
        
        # Apply PCA to all embeddings combined (for better dimensionality reduction)
        if len(all_embedding_vectors) > 0:
            embeddings_array = np.array(all_embedding_vectors)
                
            # Reduce to 3D using PCA (if we have enough points) or use first 3 dimensions
            if len(all_embedding_vectors) >= 3:
                # Use PCA for proper dimensionality reduction
                    pca = PCA(n_components=3)
                    reduced_3d = pca.fit_transform(embeddings_array)
                    explained_variance = {
                        "x": float(pca.explained_variance_ratio_[0]) if len(pca.explained_variance_ratio_) > 0 else 0,
                        "y": float(pca.explained_variance_ratio_[1]) if len(pca.explained_variance_ratio_) > 1 else 0,
                        "z": float(pca.explained_variance_ratio_[2]) if len(pca.explained_variance_ratio_) > 2 else 0
                    }
            else:
                # For fewer than 3 points, just use first 3 dimensions directly
                reduced_3d = embeddings_array[:, :3]
                explained_variance = {
                    "x": 1.0 / 3.0,  # Approximate - can't calculate variance with < 3 points
                    "y": 1.0 / 3.0,
                    "z": 1.0 / 3.0
                }
            
            # Add 3D coordinates to all data items
            for i, data_item in enumerate(all_filtered_data):
                        data_item["position"] = {
                            "x": float(reduced_3d[i][0]),
                            "y": float(reduced_3d[i][1]),
                            "z": float(reduced_3d[i][2])
                        }
                        data_item["explained_variance"] = explained_variance

            return {
                "embeddings": all_data,
                "total_points": sum(len(v) for v in all_data.values()),
            "company_id": company_id
        }
        
    except Exception as e:
        logger.error(f"Error getting embeddings for graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting embeddings: {str(e)}")


@router.get("/embeddings/{profile_type}/{profile_id}/similar", response_model=Dict)
def get_similar_embeddings(profile_type: str, profile_id: str, top_k: int = 10, cross_type: bool = True):
    """
    Get similar embeddings for any profile type, optionally across all profile types.
    
    Args:
        profile_type: Profile type (team, interviewer, candidate, position)
        profile_id: Profile ID
        top_k: Number of similar profiles to return per type (if cross_type=True) or total (if cross_type=False)
        cross_type: If True, search across all profile types. If False, only search within same type.
    
    Returns:
        Dictionary with similar profiles grouped by type (if cross_type=True) or flat list (if cross_type=False)
    """
    try:
        # Map profile type to Weaviate class name
        class_name_map = {
            "team": "Team",
            "interviewer": "Interviewer",
            "candidate": "Candidate",
            "position": "Position"
        }
        
        class_name = class_name_map.get(profile_type.lower())
        if not class_name:
            raise HTTPException(status_code=400, detail=f"Invalid profile type: {profile_type}")
        
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        if cross_type:
            # Search across all profile types
            all_results = vector_db.find_similar_embeddings_across_types(class_name, profile_id, top_k)
            
            # Filter by company_id and format results
            formatted_results = {
                "candidates": [],
                "teams": [],
                "interviewers": [],
                "positions": []
            }
            
            for result_type, results in all_results.items():
                for result in results:
                    if result.get("metadata", {}).get("company_id") == company_id:
                        formatted_results[result_type].append({
                            "profile_id": result.get("profile_id"),
                            "profile_type": result.get("profile_type", result_type.rstrip("s")),
                            "similarity": result.get("similarity", 0.0),
                            "distance": result.get("distance", 0.0),
                            "metadata": result.get("metadata", {})
                        })
            
            return {
                "profile_id": profile_id,
                "profile_type": profile_type.lower(),
                "cross_type": True,
                "similar_profiles": formatted_results
            }
        else:
            # Search only within same type
            similar_results = vector_db.find_similar_embeddings(class_name, profile_id, top_k)
            
            # Filter by company_id and format results
            filtered_results = []
            for result in similar_results:
                if result.get("metadata", {}).get("company_id") == company_id:
                    filtered_results.append({
                        "profile_id": result.get("profile_id"),
                        "profile_type": profile_type.lower(),
                        "similarity": result.get("similarity", 0.0),
                        "distance": result.get("distance", 0.0),
                        "metadata": result.get("metadata", {})
                    })
            
            return {
                "profile_id": profile_id,
                "profile_type": profile_type.lower(),
                "cross_type": False,
                "similar_profiles": filtered_results
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting similar embeddings: {str(e)}")


@router.get("/candidates/{candidate_id}/talent-score", response_model=Dict)
async def get_talent_score(candidate_id: str):
    """
    Get exceptional talent score and breakdown for a candidate.
    
    Returns:
    - exceptional_score: Overall score (0.0-1.0)
    - signal_breakdown: Detailed breakdown by signal type
    - ranking: Percentile rank among all candidates (if ranked)
    - evidence: Supporting evidence (papers, stars, followers, etc.)
    - why_exceptional: Explanation of exceptional qualities
    """
    try:
        finder = get_exceptional_finder()
        
        result = finder.get_talent_breakdown(candidate_id)
        
        if not result.get('candidate_id'):
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting talent score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting talent score: {str(e)}")


# Phase 1: Teams Management Endpoints

def get_postgres_client() -> PostgresClient:
    """Get or create PostgreSQL client instance."""
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = PostgresClient()
    return _postgres_client


@router.get("/teams", response_model=List[TeamResponse])
def list_teams():
    """
    List all teams for the current company.
    
    Returns:
        List of teams filtered by company_id
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        query = """
            SELECT * FROM teams 
            WHERE company_id = %s 
            ORDER BY created_at DESC
        """
        teams = postgres.execute_query(query, (company_id,))
        
        # Convert to TeamResponse format
        result = []
        for team in teams:
            result.append(TeamResponse(
                id=team['id'],
                company_id=team['company_id'],
                name=team['name'],
                department=team.get('department'),
                needs=team.get('needs', []),
                expertise=team.get('expertise', []),
                stack=team.get('stack', []),
                domains=team.get('domains', []),
                culture=team.get('culture'),
                work_style=team.get('work_style'),
                hiring_priorities=team.get('hiring_priorities', []),
                member_count=team.get('member_count', 0),
                member_ids=team.get('member_ids', []),
                open_positions=team.get('open_positions', []),
                created_at=team['created_at'],
                updated_at=team['updated_at']
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing teams: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing teams: {str(e)}")


@router.post("/teams", response_model=TeamResponse, status_code=201)
def create_team(team_data: TeamCreateRequest):
    """
    Create a new team.
    
    Args:
        team_data: Team creation data
    
    Returns:
        Created team
    """
    try:
        import uuid
        from datetime import datetime
        
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        team_id = str(uuid.uuid4())
        now = datetime.now()
        
        query = """
            INSERT INTO teams (
                id, company_id, name, department, needs, expertise, stack, 
                domains, culture, work_style, hiring_priorities, 
                member_count, member_ids, open_positions, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING *
        """
        
        result = postgres.execute_one(query, (
            team_id,
            company_id,
            team_data.name,
            team_data.department,
            team_data.needs or [],
            team_data.expertise or [],
            team_data.stack or [],
            team_data.domains or [],
            team_data.culture,
            team_data.work_style,
            team_data.hiring_priorities or [],
            0,  # member_count
            [],  # member_ids
            [],  # open_positions
            now,
            now
        ))
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create team")
        
        # Also store in Weaviate for embeddings (for matching operations)
        try:
            kg = get_knowledge_graph()
            team_dict = {
                'id': result['id'],
                'company_id': result['company_id'],
                'name': result['name'],
                'department': result.get('department'),
                'needs': result.get('needs', []),
                'expertise': result.get('expertise', []),
                'stack': result.get('stack', []),
                'domains': result.get('domains', []),
                'culture': result.get('culture'),
                'work_style': result.get('work_style'),
                'hiring_priorities': result.get('hiring_priorities', []),
                'member_count': result.get('member_count', 0),
                'member_ids': result.get('member_ids', []),
                'open_positions': result.get('open_positions', []),
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
            kg.add_team(team_dict)
            logger.info(f"Team {result['id']} also stored in Weaviate for embeddings")
        except Exception as e:
            logger.warning(f"Failed to store team in Weaviate (non-critical): {e}")
            # Non-critical: continue even if Weaviate storage fails
        
        return TeamResponse(
            id=result['id'],
            company_id=result['company_id'],
            name=result['name'],
            department=result.get('department'),
            needs=result.get('needs', []),
            expertise=result.get('expertise', []),
            stack=result.get('stack', []),
            domains=result.get('domains', []),
            culture=result.get('culture'),
            work_style=result.get('work_style'),
            hiring_priorities=result.get('hiring_priorities', []),
            member_count=result.get('member_count', 0),
            member_ids=result.get('member_ids', []),
            open_positions=result.get('open_positions', []),
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating team: {str(e)}")


@router.get("/teams/{team_id}/embedding", response_model=Dict)
def get_team_embedding(team_id: str):
    """
    Get team embedding vector.
    
    Args:
        team_id: Team ID
    
    Returns:
        Dictionary with embedding vector and metadata
    """
    try:
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Get embedding from Weaviate
        embedding_data = vector_db.get_embedding("Team", team_id)
        
        if not embedding_data:
            raise HTTPException(status_code=404, detail=f"Embedding not found for team {team_id}")
        
        # Verify company_id matches
        if embedding_data.get("company_id") != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "profile_id": team_id,
            "profile_type": "team",
            "embedding": embedding_data.get("embedding"),
            "embedding_dimension": len(embedding_data.get("embedding", [])),
            "metadata": embedding_data.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team embedding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting team embedding: {str(e)}")


@router.get("/teams/{team_id}/similar", response_model=Dict)
def get_similar_teams(team_id: str, top_k: int = 10):
    """
    Get similar teams based on embedding similarity.
    
    Args:
        team_id: Team ID
        top_k: Number of similar teams to return
    
    Returns:
        Dictionary with similar teams and their similarity scores
    """
    try:
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Find similar embeddings
        similar_results = vector_db.find_similar_embeddings("Team", team_id, top_k)
        
        # Filter by company_id and format results
        filtered_results = []
        for result in similar_results:
            if result.get("metadata", {}).get("company_id") == company_id:
                filtered_results.append({
                    "profile_id": result.get("profile_id"),
                    "profile_type": "team",
                    "similarity": result.get("similarity", 0.0),
                    "distance": result.get("distance", 0.0),
                    "metadata": result.get("metadata", {})
                })
        
        return {
            "profile_id": team_id,
            "profile_type": "team",
            "similar_profiles": filtered_results
        }
        
    except Exception as e:
        logger.error(f"Error getting similar teams: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting similar teams: {str(e)}")


@router.post("/teams/{team_id}/generate-embedding", response_model=Dict)
def generate_team_embedding(team_id: str):
    """
    Generate and store embedding for a team if it doesn't exist.
    
    Args:
        team_id: Team ID
    
    Returns:
        Success message with embedding status
    """
    try:
        kg = get_knowledge_graph()
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        vector_db = get_vector_db_client()
        
        # Check if embedding already exists
        existing_embedding = vector_db.get_embedding("Team", team_id)
        if existing_embedding:
            return {
                "success": True,
                "message": f"Embedding already exists for team {team_id}",
                "team_id": team_id
            }
        
        # Get team from PostgreSQL
        team = postgres.execute_one(
            "SELECT * FROM teams WHERE id = %s AND company_id = %s",
            (team_id, company_id)
        )
        
        if not team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        # Generate and store embedding
        team_dict = dict(team)
        kg.add_team(team_dict)
        
        logger.info(f"Generated embedding for team: {team_id}")
        return {
            "success": True,
            "message": f"Embedding generated successfully for team {team_id}",
            "team_id": team_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating team embedding for {team_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating team embedding: {str(e)}")


@router.get("/teams/{team_id}", response_model=TeamResponse)
def get_team(team_id: str):
    """
    Get team details by ID.
    
    Args:
        team_id: Team ID
    
    Returns:
        Team details
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        query = """
            SELECT * FROM teams 
            WHERE id = %s AND company_id = %s
        """
        team = postgres.execute_one(query, (team_id, company_id))
        
        if not team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        return TeamResponse(
            id=team['id'],
            company_id=team['company_id'],
            name=team['name'],
            department=team.get('department'),
            needs=team.get('needs', []),
            expertise=team.get('expertise', []),
            stack=team.get('stack', []),
            domains=team.get('domains', []),
            culture=team.get('culture'),
            work_style=team.get('work_style'),
            hiring_priorities=team.get('hiring_priorities', []),
            member_count=team.get('member_count', 0),
            member_ids=team.get('member_ids', []),
            open_positions=team.get('open_positions', []),
            created_at=team['created_at'],
            updated_at=team['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting team: {str(e)}")


@router.put("/teams/{team_id}", response_model=TeamResponse)
def update_team(team_id: str, team_data: TeamUpdateRequest):
    """
    Update team details.
    
    Args:
        team_id: Team ID
        team_data: Team update data
    
    Returns:
        Updated team
    """
    try:
        from datetime import datetime
        
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # First check if team exists
        existing = postgres.execute_one(
            "SELECT * FROM teams WHERE id = %s AND company_id = %s",
            (team_id, company_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        # Build update query dynamically based on provided fields
        updates = []
        params = []
        
        if team_data.name is not None:
            updates.append("name = %s")
            params.append(team_data.name)
        if team_data.department is not None:
            updates.append("department = %s")
            params.append(team_data.department)
        if team_data.needs is not None:
            updates.append("needs = %s")
            params.append(team_data.needs)
        if team_data.expertise is not None:
            updates.append("expertise = %s")
            params.append(team_data.expertise)
        if team_data.stack is not None:
            updates.append("stack = %s")
            params.append(team_data.stack)
        if team_data.domains is not None:
            updates.append("domains = %s")
            params.append(team_data.domains)
        if team_data.culture is not None:
            updates.append("culture = %s")
            params.append(team_data.culture)
        if team_data.work_style is not None:
            updates.append("work_style = %s")
            params.append(team_data.work_style)
        if team_data.hiring_priorities is not None:
            updates.append("hiring_priorities = %s")
            params.append(team_data.hiring_priorities)
        
        if not updates:
            # No updates provided, return existing team
            return TeamResponse(
                id=existing['id'],
                company_id=existing['company_id'],
                name=existing['name'],
                department=existing.get('department'),
                needs=existing.get('needs', []),
                expertise=existing.get('expertise', []),
                stack=existing.get('stack', []),
                domains=existing.get('domains', []),
                culture=existing.get('culture'),
                work_style=existing.get('work_style'),
                hiring_priorities=existing.get('hiring_priorities', []),
                member_count=existing.get('member_count', 0),
                member_ids=existing.get('member_ids', []),
                open_positions=existing.get('open_positions', []),
                created_at=existing['created_at'],
                updated_at=existing['updated_at']
            )
        
        # Add updated_at
        updates.append("updated_at = %s")
        params.append(datetime.now())
        
        # Add WHERE clause params
        params.extend([team_id, company_id])
        
        query = f"""
            UPDATE teams 
            SET {', '.join(updates)}
            WHERE id = %s AND company_id = %s
            RETURNING *
        """
        
        result = postgres.execute_one(query, tuple(params))
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update team")
        
        # Also update in Weaviate for embeddings (for matching operations)
        try:
            kg = get_knowledge_graph()
            team_dict = {
                'id': result['id'],
                'company_id': result['company_id'],
                'name': result['name'],
                'department': result.get('department'),
                'needs': result.get('needs', []),
                'expertise': result.get('expertise', []),
                'stack': result.get('stack', []),
                'domains': result.get('domains', []),
                'culture': result.get('culture'),
                'work_style': result.get('work_style'),
                'hiring_priorities': result.get('hiring_priorities', []),
                'member_count': result.get('member_count', 0),
                'member_ids': result.get('member_ids', []),
                'open_positions': result.get('open_positions', []),
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
            kg.update_team(team_id, team_dict)
            logger.info(f"Team {team_id} also updated in Weaviate")
        except Exception as e:
            logger.warning(f"Failed to update team in Weaviate (non-critical): {e}")
            # Non-critical: continue even if Weaviate update fails
        
        return TeamResponse(
            id=result['id'],
            company_id=result['company_id'],
            name=result['name'],
            department=result.get('department'),
            needs=result.get('needs', []),
            expertise=result.get('expertise', []),
            stack=result.get('stack', []),
            domains=result.get('domains', []),
            culture=result.get('culture'),
            work_style=result.get('work_style'),
            hiring_priorities=result.get('hiring_priorities', []),
            member_count=result.get('member_count', 0),
            member_ids=result.get('member_ids', []),
            open_positions=result.get('open_positions', []),
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating team: {str(e)}")


@router.delete("/teams/{team_id}")
def delete_team(team_id: str):
    """
    Delete a team.
    
    Args:
        team_id: Team ID
    
    Returns:
        Success message
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if team exists
        existing = postgres.execute_one(
            "SELECT * FROM teams WHERE id = %s AND company_id = %s",
            (team_id, company_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        # Unassign all interviewers from this team (set team_id to NULL)
        postgres.execute_update(
            "UPDATE interviewers SET team_id = NULL WHERE team_id = %s AND company_id = %s",
            (team_id, company_id)
        )
        
        # Delete team
        query = "DELETE FROM teams WHERE id = %s AND company_id = %s"
        rows_affected = postgres.execute_update(query, (team_id, company_id))
        
        if rows_affected == 0:
            raise HTTPException(status_code=500, detail="Failed to delete team")
        
        return {"message": "Team deleted successfully. All interviewers have been unassigned."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting team: {str(e)}")


@router.post("/teams/chat", response_model=TeamChatResponse)
async def team_creation_chat(request: TeamChatRequest):
    """
    Chat endpoint for AI-powered team creation.
    
    Uses Grok AI to ask questions and extract team information conversationally.
    
    Args:
        request: Chat request with conversation history
    
    Returns:
        Chat response with next question or complete team data
    """
    import uuid
    import json
    
    try:
        grok = get_grok_client()
        session_id = request.session_id or str(uuid.uuid4())
        
        # Build system prompt for team creation
        system_prompt = """You are a helpful AI assistant helping to create a new team profile. 
Your goal is to ask questions one at a time to gather the following information:
- name (required): Team name
- department (optional): Department name
- expertise (optional): List of expertise areas (e.g., "Backend Development, Distributed Systems")
- stack (optional): List of technologies (e.g., "Python, FastAPI, PostgreSQL")
- domains (optional): List of domain expertise (e.g., "LLM Inference, GPU Computing")
- needs (optional): List of skills gaps/needs (e.g., "CUDA, Model Optimization")
- culture (optional): Team culture description
- work_style (optional): Work style description
- hiring_priorities (optional): List of hiring priorities (e.g., "Senior Engineers, Research Experience")

Ask ONE question at a time. Start with: "What's the name of the team you'd like to create?"

After each user response, extract the information and ask the next question. 
Once you have the name (required), you can ask about other fields. 
When you have enough information (at minimum the name), respond with a JSON object containing the extracted data.

Format your final response as JSON when complete:
{{
    "message": "Great! I have all the information I need.",
    "is_complete": true,
    "team_data": {{
        "name": "...",
        "department": "...",
        "expertise": [...],
        "stack": [...],
        "domains": [...],
        "needs": [...],
        "culture": "...",
        "work_style": "...",
        "hiring_priorities": [...]
    }}
}}

Otherwise, just respond with a natural follow-up question."""
        
        # Build conversation messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # If this is the first message, add the initial question
        if len(request.messages) == 0:
            messages.append({
                "role": "assistant",
                "content": "What's the name of the team you'd like to create?"
            })
        
        # Call Grok API directly
        url = f"{grok.base_url}/chat/completions"
        payload = {
            "model": "grok-4-1-fast-reasoning",
            "messages": messages,
            "temperature": 0.7
        }
        
        response = await grok.client.post(url, headers=grok.headers, json=payload)
        
        if response.status_code >= 400:
            error_detail = f"Grok API chat request failed: {response.status_code}"
            try:
                error_body = response.json()
                if "message" in error_body:
                    error_detail += f" - {error_body['message']}"
            except Exception:
                error_detail += f" - {response.text[:200]}"
            logger.error(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)
        
        result = response.json()
        
        assistant_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Try to parse JSON response if complete
        is_complete = False
        team_data = None
        
        # Check if response contains JSON
        if "is_complete" in assistant_message or "team_data" in assistant_message:
            try:
                # Try to extract JSON from response
                json_start = assistant_message.find("{")
                json_end = assistant_message.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = assistant_message[json_start:json_end]
                    parsed = json.loads(json_str)
                    if parsed.get("is_complete"):
                        is_complete = True
                        team_data_dict = parsed.get("team_data", {})
                        if team_data_dict:
                            team_data = TeamCreateRequest(**team_data_dict)
                            # Return clean message without JSON
                            assistant_message = parsed.get("message", "Great! I have all the information I need.")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Could not parse JSON from Grok response: {e}")
                # Continue with regular message
        
        return TeamChatResponse(
            message=assistant_message,
            is_complete=is_complete,
            team_data=team_data,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in team creation chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in team creation chat: {str(e)}")


@router.post("/teams/chat/stream")
async def team_creation_chat_stream(request: TeamChatRequest):
    """
    Streaming chat endpoint for AI-powered team creation.
    
    Uses Server-Sent Events (SSE) to stream responses character by character.
    
    Args:
        request: Chat request with conversation history
    
    Returns:
        Streaming response with SSE format
    """
    import uuid
    import json
    import asyncio
    
    async def generate():
        try:
            grok = get_grok_client()
            session_id = request.session_id or str(uuid.uuid4())
            
            # Build system prompt for team creation
            current_data_context = ""
            if request.current_data:
                current_data = request.current_data
                current_data_context = "\n\nCURRENT FORM DATA (for context - user may want to update these):\n"
                if current_data.name:
                    current_data_context += f"- name: {current_data.name}\n"
                if current_data.department:
                    current_data_context += f"- department: {current_data.department}\n"
                if current_data.expertise:
                    current_data_context += f"- expertise: {', '.join(current_data.expertise)}\n"
                if current_data.stack:
                    current_data_context += f"- stack: {', '.join(current_data.stack)}\n"
                if current_data.domains:
                    current_data_context += f"- domains: {', '.join(current_data.domains)}\n"
                if current_data.needs:
                    current_data_context += f"- needs: {', '.join(current_data.needs)}\n"
                if current_data.culture:
                    current_data_context += f"- culture: {current_data.culture}\n"
                if current_data.work_style:
                    current_data_context += f"- work_style: {current_data.work_style}\n"
                if current_data.hiring_priorities:
                    current_data_context += f"- hiring_priorities: {', '.join(current_data.hiring_priorities)}\n"
                current_data_context += "\nUse this as context. If the user wants to update something, acknowledge what's currently there and help them refine it."
            
            system_prompt = f"""You are a helpful AI assistant helping to create a new team profile. 
Your goal is to ask questions one at a time to gather the following information:
- name (required): Team name
- department (optional): Department name
- expertise (optional): List of expertise areas (e.g., "Backend Development, Distributed Systems")
- stack (optional): List of technologies (e.g., "Python, FastAPI, PostgreSQL")
- domains (optional): List of domain expertise (e.g., "LLM Inference, GPU Computing")
- needs (optional): List of skills gaps/needs (e.g., "CUDA, Model Optimization")
- culture (optional): Team culture description
- work_style (optional): Work style description
- hiring_priorities (optional): List of hiring priorities (e.g., "Senior Engineers, Research Experience")
{current_data_context}

Ask ONE question at a time. Start with: "What's the name of the team you'd like to create?"

After each user response, extract the information and ask the next question. 
Once you have the name (required), you can ask about other fields. 
When you have enough information (at minimum the name), respond with a JSON object containing the extracted data.

Format your final response as JSON when complete:
{{
    "message": "Great! I have all the information I need.",
    "is_complete": true,
    "team_data": {{
        "name": "...",
        "department": "...",
        "expertise": [...],
        "stack": [...],
        "domains": [...],
        "needs": [...],
        "culture": "...",
        "work_style": "...",
        "hiring_priorities": [...]
    }}
}}

Otherwise, just respond with a natural follow-up question."""
            
            # Build conversation messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            for msg in request.messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # If this is the first message, add the initial question
            if len(request.messages) == 0:
                messages.append({
                    "role": "assistant",
                    "content": "What's the name of the team you'd like to create?"
                })
            
            # Call Grok API with streaming
            url = f"{grok.base_url}/chat/completions"
            payload = {
                "model": "grok-4-1-fast-reasoning",
                "messages": messages,
                "temperature": 0.7,
                "stream": True
            }
            
            # Use a longer timeout for streaming requests (5 minutes)
            streaming_client = httpx.AsyncClient(timeout=300.0)
            try:
                async with streaming_client.stream("POST", url, headers=grok.headers, json=payload) as response:
                    if response.status_code >= 400:
                        error_detail = f"Grok API chat request failed: {response.status_code}"
                        try:
                            error_body = await response.aread()
                            error_text = error_body.decode() if isinstance(error_body, bytes) else str(error_body)
                            error_detail += f" - {error_text[:200]}"
                        except Exception:
                            pass
                        logger.error(error_detail)
                        yield f"data: {json.dumps({'error': error_detail})}\n\n"
                        return
                    
                    # Stream the response following Grok's SSE format
                    full_message = ""
                    finish_reason = None
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        # Grok sends lines in format: "data: {json}" or "data: [DONE]"
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:].strip()  # Remove "data: " prefix
                        
                        # Check for end of stream
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract content from delta (Grok format: choices[0].delta.content)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    full_message += content
                                    # Forward the content chunk to frontend
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                                
                                # Check for finish_reason (indicates end of stream)
                                finish_reason = choices[0].get("finish_reason")
                                if finish_reason:
                                    # Stream is complete, parse final message
                                    break
                                
                        except json.JSONDecodeError as e:
                            logger.debug(f"Could not parse SSE line: {line[:100]}")
                            continue
                    
                    # After stream completes, parse the full message for completion status
                    is_complete = False
                    team_data = None
                    
                    if full_message and ("is_complete" in full_message or "team_data" in full_message):
                        try:
                            # Try to extract JSON from the response
                            json_start = full_message.find("{")
                            json_end = full_message.rfind("}") + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = full_message[json_start:json_end]
                                parsed = json.loads(json_str)
                                if parsed.get("is_complete"):
                                    is_complete = True
                                    team_data_dict = parsed.get("team_data", {})
                                    if team_data_dict:
                                        team_data = team_data_dict
                                        full_message = parsed.get("message", "Great! I have all the information I need.")
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Could not parse JSON from Grok response: {e}")
                    
                    # Send final data with complete message
                    yield f"data: {json.dumps({'final': {'message': full_message, 'is_complete': is_complete, 'team_data': team_data, 'session_id': session_id}})}\n\n"
                    
                    # End stream
                    yield "data: [DONE]\n\n"
            finally:
                await streaming_client.aclose()
            
        except Exception as e:
            logger.error(f"Error in streaming team creation chat: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================================
# Phase 2: Interviewers Management Endpoints
# ============================================================================

@router.get("/interviewers", response_model=List[InterviewerResponse])
def list_interviewers():
    """
    List all interviewers for the current company.
    
    Returns:
        List of interviewers
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        query = "SELECT * FROM interviewers WHERE company_id = %s ORDER BY created_at DESC"
        interviewers = postgres.execute_query(query, (company_id,))
        
        return [
            InterviewerResponse(
                id=iv['id'],
                company_id=iv['company_id'],
                team_id=iv.get('team_id'),
                name=iv['name'],
                phone_number=iv['phone_number'],
                email=iv['email'],
                expertise=iv.get('expertise', []),
                expertise_level=iv.get('expertise_level'),
                specializations=iv.get('specializations', []),
                interview_style=iv.get('interview_style'),
                evaluation_focus=iv.get('evaluation_focus', []),
                question_style=iv.get('question_style'),
                preferred_interview_types=iv.get('preferred_interview_types', []),
                total_interviews=iv.get('total_interviews', 0),
                successful_hires=iv.get('successful_hires', 0),
                success_rate=iv.get('success_rate', 0.0),
                created_at=iv['created_at'],
                updated_at=iv['updated_at']
            )
            for iv in interviewers
        ]
        
    except Exception as e:
        logger.error(f"Error listing interviewers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing interviewers: {str(e)}")


@router.post("/interviewers", response_model=InterviewerResponse)
def create_interviewer(interviewer_data: InterviewerCreateRequest):
    """
    Create a new interviewer.
    
    Args:
        interviewer_data: Interviewer creation data
    
    Returns:
        Created interviewer
    """
    try:
        from datetime import datetime
        import uuid
        
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Validate team_id if provided
        if interviewer_data.team_id:
            team = postgres.execute_one(
                "SELECT * FROM teams WHERE id = %s AND company_id = %s",
                (interviewer_data.team_id, company_id)
            )
            if not team:
                raise HTTPException(status_code=404, detail=f"Team {interviewer_data.team_id} not found")
        
        # Generate ID
        interviewer_id = str(uuid.uuid4())
        
        # Insert interviewer
        query = """
            INSERT INTO interviewers (
                id, company_id, team_id, name, phone_number, email,
                expertise, expertise_level, specializations, interview_style,
                evaluation_focus, question_style, preferred_interview_types,
                total_interviews, successful_hires, success_rate,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        params = (
            interviewer_id,
            company_id,
            interviewer_data.team_id,
            interviewer_data.name,
            interviewer_data.phone_number,
            interviewer_data.email,
            interviewer_data.expertise or [],
            interviewer_data.expertise_level,
            interviewer_data.specializations or [],
            interviewer_data.interview_style,
            interviewer_data.evaluation_focus or [],
            interviewer_data.question_style,
            interviewer_data.preferred_interview_types or [],
            0,  # total_interviews
            0,  # successful_hires
            0.0,  # success_rate
            datetime.now(),
            datetime.now()
        )
        
        postgres.execute_update(query, params)
        
        # Fetch created interviewer
        created = postgres.execute_one(
            "SELECT * FROM interviewers WHERE id = %s",
            (interviewer_id,)
        )
        
        # Also store in Weaviate for embeddings (for matching operations)
        try:
            kg = get_knowledge_graph()
            interviewer_dict = {
                'id': created['id'],
                'company_id': created['company_id'],
                'team_id': created.get('team_id'),
                'name': created['name'],
                'phone_number': created['phone_number'],
                'email': created['email'],
                'expertise': created.get('expertise', []),
                'expertise_level': created.get('expertise_level'),
                'specializations': created.get('specializations', []),
                'interview_style': created.get('interview_style'),
                'evaluation_focus': created.get('evaluation_focus', []),
                'question_style': created.get('question_style'),
                'preferred_interview_types': created.get('preferred_interview_types', []),
                'total_interviews': created.get('total_interviews', 0),
                'successful_hires': created.get('successful_hires', 0),
                'success_rate': created.get('success_rate', 0.0),
                'created_at': created['created_at'],
                'updated_at': created['updated_at']
            }
            kg.add_interviewer(interviewer_dict)
            logger.info(f"Interviewer {created['id']} also stored in Weaviate for embeddings")
        except Exception as e:
            logger.warning(f"Failed to store interviewer in Weaviate (non-critical): {e}")
            # Non-critical: continue even if Weaviate storage fails
        
        return InterviewerResponse(
            id=created['id'],
            company_id=created['company_id'],
            team_id=created.get('team_id'),
            name=created['name'],
            phone_number=created['phone_number'],
            email=created['email'],
            expertise=created.get('expertise', []),
            expertise_level=created.get('expertise_level'),
            specializations=created.get('specializations', []),
            interview_style=created.get('interview_style'),
            evaluation_focus=created.get('evaluation_focus', []),
            question_style=created.get('question_style'),
            preferred_interview_types=created.get('preferred_interview_types', []),
            total_interviews=created.get('total_interviews', 0),
            successful_hires=created.get('successful_hires', 0),
            success_rate=created.get('success_rate', 0.0),
            created_at=created['created_at'],
            updated_at=created['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating interviewer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating interviewer: {str(e)}")


@router.get("/interviewers/{interviewer_id}/embedding", response_model=Dict)
def get_interviewer_embedding(interviewer_id: str):
    """
    Get interviewer embedding vector.
    
    Args:
        interviewer_id: Interviewer ID
    
    Returns:
        Dictionary with embedding vector and metadata
    """
    try:
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Get embedding from Weaviate
        embedding_data = vector_db.get_embedding("Interviewer", interviewer_id)
        
        if not embedding_data:
            raise HTTPException(status_code=404, detail=f"Embedding not found for interviewer {interviewer_id}")
        
        # Verify company_id matches
        if embedding_data.get("company_id") != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "profile_id": interviewer_id,
            "profile_type": "interviewer",
            "embedding": embedding_data.get("embedding"),
            "embedding_dimension": len(embedding_data.get("embedding", [])),
            "metadata": embedding_data.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interviewer embedding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting interviewer embedding: {str(e)}")


@router.get("/interviewers/{interviewer_id}/similar", response_model=Dict)
def get_similar_interviewers(interviewer_id: str, top_k: int = 10):
    """
    Get similar interviewers based on embedding similarity.
    
    Args:
        interviewer_id: Interviewer ID
        top_k: Number of similar interviewers to return
    
    Returns:
        Dictionary with similar interviewers and their similarity scores
    """
    try:
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Find similar embeddings
        similar_results = vector_db.find_similar_embeddings("Interviewer", interviewer_id, top_k)
        
        # Filter by company_id and format results
        filtered_results = []
        for result in similar_results:
            if result.get("metadata", {}).get("company_id") == company_id:
                filtered_results.append({
                    "profile_id": result.get("profile_id"),
                    "profile_type": "interviewer",
                    "similarity": result.get("similarity", 0.0),
                    "distance": result.get("distance", 0.0),
                    "metadata": result.get("metadata", {})
                })
        
        return {
            "profile_id": interviewer_id,
            "profile_type": "interviewer",
            "similar_profiles": filtered_results
        }
        
    except Exception as e:
        logger.error(f"Error getting similar interviewers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting similar interviewers: {str(e)}")


@router.post("/interviewers/{interviewer_id}/generate-embedding", response_model=Dict)
def generate_interviewer_embedding(interviewer_id: str):
    """
    Generate and store embedding for an interviewer if it doesn't exist.
    
    Args:
        interviewer_id: Interviewer ID
    
    Returns:
        Success message with embedding status
    """
    try:
        kg = get_knowledge_graph()
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        vector_db = get_vector_db_client()
        
        # Check if embedding already exists
        existing_embedding = vector_db.get_embedding("Interviewer", interviewer_id)
        if existing_embedding:
            return {
                "success": True,
                "message": f"Embedding already exists for interviewer {interviewer_id}",
                "interviewer_id": interviewer_id
            }
        
        # Get interviewer from PostgreSQL
        interviewer = postgres.execute_one(
            "SELECT * FROM interviewers WHERE id = %s AND company_id = %s",
            (interviewer_id, company_id)
        )
        
        if not interviewer:
            raise HTTPException(status_code=404, detail=f"Interviewer {interviewer_id} not found")
        
        # Generate and store embedding
        interviewer_dict = dict(interviewer)
        kg.add_interviewer(interviewer_dict)
        
        logger.info(f"Generated embedding for interviewer: {interviewer_id}")
        return {
            "success": True,
            "message": f"Embedding generated successfully for interviewer {interviewer_id}",
            "interviewer_id": interviewer_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating interviewer embedding for {interviewer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating interviewer embedding: {str(e)}")


@router.get("/interviewers/{interviewer_id}", response_model=InterviewerResponse)
def get_interviewer(interviewer_id: str):
    """
    Get interviewer details.
    
    Args:
        interviewer_id: Interviewer ID
    
    Returns:
        Interviewer details
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        query = "SELECT * FROM interviewers WHERE id = %s AND company_id = %s"
        interviewer = postgres.execute_one(query, (interviewer_id, company_id))
        
        if not interviewer:
            raise HTTPException(status_code=404, detail=f"Interviewer {interviewer_id} not found")
        
        return InterviewerResponse(
            id=interviewer['id'],
            company_id=interviewer['company_id'],
            team_id=interviewer.get('team_id'),
            name=interviewer['name'],
            phone_number=interviewer['phone_number'],
            email=interviewer['email'],
            expertise=interviewer.get('expertise', []),
            expertise_level=interviewer.get('expertise_level'),
            specializations=interviewer.get('specializations', []),
            interview_style=interviewer.get('interview_style'),
            evaluation_focus=interviewer.get('evaluation_focus', []),
            question_style=interviewer.get('question_style'),
            preferred_interview_types=interviewer.get('preferred_interview_types', []),
            total_interviews=interviewer.get('total_interviews', 0),
            successful_hires=interviewer.get('successful_hires', 0),
            success_rate=interviewer.get('success_rate', 0.0),
            created_at=interviewer['created_at'],
            updated_at=interviewer['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interviewer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting interviewer: {str(e)}")


@router.put("/interviewers/{interviewer_id}", response_model=InterviewerResponse)
def update_interviewer(interviewer_id: str, interviewer_data: InterviewerUpdateRequest):
    """
    Update interviewer details.
    
    Args:
        interviewer_id: Interviewer ID
        interviewer_data: Interviewer update data
    
    Returns:
        Updated interviewer
    """
    try:
        from datetime import datetime
        
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if interviewer exists
        existing = postgres.execute_one(
            "SELECT * FROM interviewers WHERE id = %s AND company_id = %s",
            (interviewer_id, company_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Interviewer {interviewer_id} not found")
        
        # Validate team_id if provided
        if interviewer_data.team_id is not None:
            if interviewer_data.team_id:  # Not empty string
                team = postgres.execute_one(
                    "SELECT * FROM teams WHERE id = %s AND company_id = %s",
                    (interviewer_data.team_id, company_id)
                )
                if not team:
                    raise HTTPException(status_code=404, detail=f"Team {interviewer_data.team_id} not found")
        
        # Build update query dynamically
        updates = []
        params = []
        
        if interviewer_data.name is not None:
            updates.append("name = %s")
            params.append(interviewer_data.name)
        if interviewer_data.phone_number is not None:
            updates.append("phone_number = %s")
            params.append(interviewer_data.phone_number)
        if interviewer_data.email is not None:
            updates.append("email = %s")
            params.append(interviewer_data.email)
        if interviewer_data.team_id is not None:
            updates.append("team_id = %s")
            params.append(interviewer_data.team_id if interviewer_data.team_id else None)
        if interviewer_data.expertise is not None:
            updates.append("expertise = %s")
            params.append(interviewer_data.expertise)
        if interviewer_data.expertise_level is not None:
            updates.append("expertise_level = %s")
            params.append(interviewer_data.expertise_level)
        if interviewer_data.specializations is not None:
            updates.append("specializations = %s")
            params.append(interviewer_data.specializations)
        if interviewer_data.interview_style is not None:
            updates.append("interview_style = %s")
            params.append(interviewer_data.interview_style)
        if interviewer_data.evaluation_focus is not None:
            updates.append("evaluation_focus = %s")
            params.append(interviewer_data.evaluation_focus)
        if interviewer_data.question_style is not None:
            updates.append("question_style = %s")
            params.append(interviewer_data.question_style)
        if interviewer_data.preferred_interview_types is not None:
            updates.append("preferred_interview_types = %s")
            params.append(interviewer_data.preferred_interview_types)
        
        if not updates:
            # No updates provided, return existing interviewer
            return InterviewerResponse(
                id=existing['id'],
                company_id=existing['company_id'],
                team_id=existing.get('team_id'),
                name=existing['name'],
                phone_number=existing['phone_number'],
                email=existing['email'],
                expertise=existing.get('expertise', []),
                expertise_level=existing.get('expertise_level'),
                specializations=existing.get('specializations', []),
                interview_style=existing.get('interview_style'),
                evaluation_focus=existing.get('evaluation_focus', []),
                question_style=existing.get('question_style'),
                preferred_interview_types=existing.get('preferred_interview_types', []),
                total_interviews=existing.get('total_interviews', 0),
                successful_hires=existing.get('successful_hires', 0),
                success_rate=existing.get('success_rate', 0.0),
                created_at=existing['created_at'],
                updated_at=existing['updated_at']
            )
        
        # Add updated_at
        updates.append("updated_at = %s")
        params.append(datetime.now())
        
        # Add WHERE clause params
        params.extend([interviewer_id, company_id])
        
        query = f"UPDATE interviewers SET {', '.join(updates)} WHERE id = %s AND company_id = %s"
        postgres.execute_update(query, tuple(params))
        
        # Fetch updated interviewer
        updated = postgres.execute_one(
            "SELECT * FROM interviewers WHERE id = %s AND company_id = %s",
            (interviewer_id, company_id)
        )
        
        # Also update in Weaviate for embeddings (for matching operations)
        try:
            kg = get_knowledge_graph()
            interviewer_dict = {
                'id': updated['id'],
                'company_id': updated['company_id'],
                'team_id': updated.get('team_id'),
                'name': updated['name'],
                'phone_number': updated['phone_number'],
                'email': updated['email'],
                'expertise': updated.get('expertise', []),
                'expertise_level': updated.get('expertise_level'),
                'specializations': updated.get('specializations', []),
                'interview_style': updated.get('interview_style'),
                'evaluation_focus': updated.get('evaluation_focus', []),
                'question_style': updated.get('question_style'),
                'preferred_interview_types': updated.get('preferred_interview_types', []),
                'total_interviews': updated.get('total_interviews', 0),
                'successful_hires': updated.get('successful_hires', 0),
                'success_rate': updated.get('success_rate', 0.0),
                'created_at': updated['created_at'],
                'updated_at': updated['updated_at']
            }
            kg.update_interviewer(interviewer_id, interviewer_dict)
            logger.info(f"Interviewer {interviewer_id} also updated in Weaviate")
        except Exception as e:
            logger.warning(f"Failed to update interviewer in Weaviate (non-critical): {e}")
            # Non-critical: continue even if Weaviate update fails
        
        return InterviewerResponse(
            id=updated['id'],
            company_id=updated['company_id'],
            team_id=updated.get('team_id'),
            name=updated['name'],
            phone_number=updated['phone_number'],
            email=updated['email'],
            expertise=updated.get('expertise', []),
            expertise_level=updated.get('expertise_level'),
            specializations=updated.get('specializations', []),
            interview_style=updated.get('interview_style'),
            evaluation_focus=updated.get('evaluation_focus', []),
            question_style=updated.get('question_style'),
            preferred_interview_types=updated.get('preferred_interview_types', []),
            total_interviews=updated.get('total_interviews', 0),
            successful_hires=updated.get('successful_hires', 0),
            success_rate=updated.get('success_rate', 0.0),
            created_at=updated['created_at'],
            updated_at=updated['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interviewer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating interviewer: {str(e)}")


@router.delete("/interviewers/{interviewer_id}")
def delete_interviewer(interviewer_id: str):
    """
    Delete an interviewer.
    
    Args:
        interviewer_id: Interviewer ID
    
    Returns:
        Success message
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if interviewer exists
        existing = postgres.execute_one(
            "SELECT * FROM interviewers WHERE id = %s AND company_id = %s",
            (interviewer_id, company_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Interviewer {interviewer_id} not found")
        
        # Delete interviewer
        query = "DELETE FROM interviewers WHERE id = %s AND company_id = %s"
        rows_affected = postgres.execute_update(query, (interviewer_id, company_id))
        
        if rows_affected == 0:
            raise HTTPException(status_code=500, detail="Failed to delete interviewer")
        
        return {"message": "Interviewer deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting interviewer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting interviewer: {str(e)}")


@router.post("/interviewers/chat/stream")
async def interviewer_creation_chat_stream(request: InterviewerChatRequest):
    """
    Streaming chat endpoint for AI-powered interviewer creation.
    Uses Server-Sent Events (SSE) to stream responses character by character.
    Args:
        request: Chat request with conversation history and optional current_data
    Returns:
        Streaming response with SSE format
    """
    import uuid
    import json
    import asyncio

    async def generate():
        try:
            grok = get_grok_client()
            session_id = request.session_id or str(uuid.uuid4())

            # Fetch all teams for the company
            postgres = get_postgres_client()
            company_context = get_company_context()
            company_id = company_context.get_company_id()
            
            teams_query = """
                SELECT * FROM teams 
                WHERE company_id = %s 
                ORDER BY name ASC
            """
            teams = postgres.execute_query(teams_query, (company_id,))
            
            # Format teams information for the prompt
            teams_info = ""
            if teams:
                teams_info = "\n\nAVAILABLE TEAMS (use these to match team names to team_id):\n"
                for team in teams:
                    teams_info += f"- ID: {team['id']}\n"
                    teams_info += f"  Name: {team['name']}\n"
                    if team.get('department'):
                        teams_info += f"  Department: {team['department']}\n"
                    if team.get('expertise'):
                        teams_info += f"  Expertise: {', '.join(team.get('expertise', []))}\n"
                    if team.get('domains'):
                        teams_info += f"  Domains: {', '.join(team.get('domains', []))}\n"
                    if team.get('stack'):
                        teams_info += f"  Stack: {', '.join(team.get('stack', []))}\n"
                    if team.get('culture'):
                        teams_info += f"  Culture: {team['culture']}\n"
                    if team.get('work_style'):
                        teams_info += f"  Work Style: {team['work_style']}\n"
                    teams_info += "\n"
            else:
                teams_info = "\n\nAVAILABLE TEAMS: No teams available yet.\n"

            # Build system prompt for interviewer creation
            current_data_context = ""
            if request.current_data:
                current_data = request.current_data
                current_data_context = "\n\nCURRENT FORM DATA (for context - user may want to update these):\n"
                if current_data.name:
                    current_data_context += f"- name: {current_data.name}\n"
                if current_data.phone_number:
                    current_data_context += f"- phone_number: {current_data.phone_number}\n"
                if current_data.email:
                    current_data_context += f"- email: {current_data.email}\n"
                if current_data.team_id:
                    current_data_context += f"- team_id: {current_data.team_id}\n"
                if current_data.expertise:
                    current_data_context += f"- expertise: {', '.join(current_data.expertise)}\n"
                if current_data.specializations:
                    current_data_context += f"- specializations: {', '.join(current_data.specializations)}\n"
                if current_data.interview_style:
                    current_data_context += f"- interview_style: {current_data.interview_style}\n"
                if current_data.evaluation_focus:
                    current_data_context += f"- evaluation_focus: {', '.join(current_data.evaluation_focus)}\n"
                if current_data.question_style:
                    current_data_context += f"- question_style: {current_data.question_style}\n"
                if current_data.preferred_interview_types:
                    current_data_context += f"- preferred_interview_types: {', '.join(current_data.preferred_interview_types)}\n"
                current_data_context += "\nUse this as context. If the user wants to update something, acknowledge what's currently there and help them refine it."
            
            system_prompt = f"""You are a helpful AI assistant helping to create a new interviewer profile. 
Your goal is to ask questions one at a time to gather the following information:
- name (required): Interviewer name
- phone_number (required): Phone number
- email (required): Email address
- team_id (optional): Team ID - MUST match one of the available team IDs listed below. If the user mentions a team name, find the matching team ID from the available teams list.
- expertise (optional): List of technical expertise areas (e.g., "Python, Machine Learning, Distributed Systems")
- expertise_level (optional): Depth of expertise (e.g., "Senior", "Expert", "Staff")
- specializations (optional): List of specialized areas (e.g., "LLM Inference, GPU Computing")
- interview_style (optional): Interview style description (e.g., "Technical deep-dive", "Behavioral focus")
- evaluation_focus (optional): List of what they focus on (e.g., "Problem-solving, System design, Code quality")
- question_style (optional): Question style (e.g., "Open-ended", "Structured", "Case-based")
- preferred_interview_types (optional): List of preferred interview types (e.g., "Technical", "System Design", "Behavioral")
{teams_info}
{current_data_context}

Ask ONE question at a time. Start with: "What's the name of the interviewer?"

After each user response, extract the information and ask the next question. 
Once you have the name, phone_number, and email (all required), you can ask about other fields. 
When you have enough information (at minimum the name, phone_number, and email), respond with a JSON object containing the extracted data.

Format your final response as JSON when complete:
{{
    "message": "Great! I have all the information I need.",
    "is_complete": true,
    "interviewer_data": {{
        "name": "...",
        "phone_number": "...",
        "email": "...",
        "team_id": "...",
        "expertise": [...],
        "expertise_level": "...",
        "specializations": [...],
        "interview_style": "...",
        "evaluation_focus": [...],
        "question_style": "...",
        "preferred_interview_types": [...]
    }}
}}

Otherwise, just respond with a natural follow-up question."""

            # Build conversation messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Add conversation history
            for msg in request.messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # If this is the first message and no history, add the initial question
            if len(request.messages) == 0 and not request.current_data:
                messages.append({
                    "role": "assistant",
                    "content": "What's the name of the interviewer?"
                })

            # Call Grok API with streaming
            url = f"{grok.base_url}/chat/completions"
            payload = {
                "model": "grok-4-1-fast-reasoning",
                "messages": messages,
                "temperature": 0.7,
                "stream": True
            }

            # Use a longer timeout for streaming requests (5 minutes)
            streaming_client = httpx.AsyncClient(timeout=300.0)
            try:
                async with streaming_client.stream("POST", url, headers=grok.headers, json=payload) as response:
                    if response.status_code >= 400:
                        error_detail = f"Grok API chat request failed: {response.status_code}"
                        try:
                            error_body = await response.aread()
                            error_text = error_body.decode() if isinstance(error_body, bytes) else str(error_body)
                            error_detail += f" - {error_text[:200]}"
                        except Exception:
                            pass
                        logger.error(error_detail)
                        yield f"data: {json.dumps({'error': error_detail})}\n\n"
                        return

                    # Stream the response
                    full_message = ""
                    try:
                        async for line in response.aiter_lines():
                            if not line or not line.startswith("data: "):
                                continue

                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")

                                if content:
                                    full_message += content
                                    yield f"data: {json.dumps({'content': content})}\n\n"

                                # Check if this is the final chunk
                                finish_reason = data.get("choices", [{}])[0].get("finish_reason")
                                if finish_reason:
                                    # Don't parse here - wait until stream completes to ensure full_message is complete
                                    break

                            except json.JSONDecodeError:
                                continue

                        # After stream completes, parse the full message for completion status
                        is_complete = False
                        interviewer_data = None
                        
                        if full_message and ("is_complete" in full_message or "interviewer_data" in full_message):
                            try:
                                # Try to extract JSON from markdown code blocks if present
                                json_str = full_message
                                if "```json" in full_message:
                                    json_str = full_message.split("```json")[1].split("```")[0].strip()
                                elif "```" in full_message:
                                    json_str = full_message.split("```")[1].split("```")[0].strip()
                                else:
                                    # Extract JSON from the message
                                    json_start = full_message.find("{")
                                    json_end = full_message.rfind("}") + 1
                                    if json_start >= 0 and json_end > json_start:
                                        json_str = full_message[json_start:json_end]
                                
                                if json_str:
                                    parsed = json.loads(json_str)
                                    logger.info(f"Parsed JSON from Grok: is_complete={parsed.get('is_complete')}, has_interviewer_data={bool(parsed.get('interviewer_data'))}")
                                    if parsed.get("is_complete"):
                                        is_complete = True
                                        interviewer_data_dict = parsed.get("interviewer_data", {})
                                        if interviewer_data_dict:
                                            interviewer_data = interviewer_data_dict
                                            full_message = parsed.get("message", "Great! I have all the information I need.")
                                            logger.info(f"Extracted interviewer_data with {len(interviewer_data_dict)} fields")
                                        else:
                                            logger.warning("interviewer_data_dict is empty or None")
                                    else:
                                        logger.warning(f"is_complete is False in parsed JSON: {parsed}")
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                logger.warning(f"Could not parse JSON from Grok response: {e}, full_message snippet: {full_message[:200]}")

                        # Send final data after parsing
                        final_payload = {'final': {'message': full_message, 'is_complete': is_complete, 'interviewer_data': interviewer_data, 'session_id': session_id}}
                        logger.info(f"Sending final data: is_complete={is_complete}, has_interviewer_data={bool(interviewer_data)}, interviewer_data_keys={list(interviewer_data.keys()) if interviewer_data else None}")
                        yield f"data: {json.dumps(final_payload)}\n\n"
                        
                        yield "data: [DONE]\n\n"
                    except (httpx.ReadTimeout, httpx.TimeoutException) as e:
                        logger.warning(f"Streaming timeout occurred, but we may have partial response: {e}")
                        # Try to parse what we have so far
                        if full_message:
                            is_complete = False
                            interviewer_data = None
                            try:
                                if "is_complete" in full_message or "interviewer_data" in full_message:
                                    # Try to extract JSON from markdown code blocks if present
                                    json_str = full_message
                                    if "```json" in full_message:
                                        json_str = full_message.split("```json")[1].split("```")[0].strip()
                                    elif "```" in full_message:
                                        json_str = full_message.split("```")[1].split("```")[0].strip()
                                    else:
                                        # Extract JSON from the message
                                        json_start = full_message.find("{")
                                        json_end = full_message.rfind("}") + 1
                                        if json_start >= 0 and json_end > json_start:
                                            json_str = full_message[json_start:json_end]
                                    
                                    if json_str:
                                        parsed = json.loads(json_str)
                                        if parsed.get("is_complete"):
                                            is_complete = True
                                            interviewer_data_dict = parsed.get("interviewer_data", {})
                                            if interviewer_data_dict:
                                                interviewer_data = interviewer_data_dict
                                                full_message = parsed.get("message", full_message)
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                logger.warning(f"Timeout handler: Could not parse JSON: {e}")
                                pass
                            
                            # Send what we have
                            yield f"data: {json.dumps({'final': {'message': full_message, 'is_complete': is_complete, 'interviewer_data': interviewer_data, 'session_id': session_id}})}\n\n"
                        else:
                            # No content received, send error
                            yield f"data: {json.dumps({'error': 'Streaming timeout - no response received. Please try again.'})}\n\n"
                        yield "data: [DONE]\n\n"
            finally:
                await streaming_client.aclose()

        except Exception as e:
            logger.error(f"Error in streaming interviewer creation chat: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# Phase 3: Position Management Endpoints
# ============================================================================

@router.get("/positions", response_model=List[PositionResponse])
def list_positions():
    """
    List all positions for the current company.
    
    Returns:
        List of positions filtered by company_id
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        query = """
            SELECT * FROM positions 
            WHERE company_id = %s 
            ORDER BY created_at DESC
        """
        positions = postgres.execute_query(query, (company_id,))
        
        # Convert to PositionResponse format
        result = []
        for position in positions:
            result.append(PositionResponse(
                id=position['id'],
                company_id=position['company_id'],
                title=position['title'],
                team_id=position.get('team_id'),
                description=position.get('description'),
                requirements=position.get('requirements', []),
                must_haves=position.get('must_haves', []),
                nice_to_haves=position.get('nice_to_haves', []),
                experience_level=position.get('experience_level'),
                responsibilities=position.get('responsibilities', []),
                tech_stack=position.get('tech_stack', []),
                domains=position.get('domains', []),
                team_context=position.get('team_context'),
                reporting_to=position.get('reporting_to'),
                collaboration=position.get('collaboration', []),
                priority=position.get('priority', 'medium'),
                status=position.get('status', 'open'),
                created_at=position['created_at'],
                updated_at=position['updated_at']
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing positions: {str(e)}")


@router.get("/positions/{position_id}", response_model=PositionResponse)
def get_position(position_id: str):
    """
    Get a single position by ID.
    
    Args:
        position_id: Position ID
    
    Returns:
        Position data
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        query = """
            SELECT * FROM positions 
            WHERE id = %s AND company_id = %s
        """
        position = postgres.execute_one(query, (position_id, company_id))
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        return PositionResponse(
            id=position['id'],
            company_id=position['company_id'],
            title=position['title'],
            team_id=position.get('team_id'),
            description=position.get('description'),
            requirements=position.get('requirements', []),
            must_haves=position.get('must_haves', []),
            nice_to_haves=position.get('nice_to_haves', []),
            experience_level=position.get('experience_level'),
            responsibilities=position.get('responsibilities', []),
            tech_stack=position.get('tech_stack', []),
            domains=position.get('domains', []),
            team_context=position.get('team_context'),
            reporting_to=position.get('reporting_to'),
            collaboration=position.get('collaboration', []),
            priority=position.get('priority', 'medium'),
            status=position.get('status', 'open'),
            created_at=position['created_at'],
            updated_at=position['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting position: {str(e)}")


@router.post("/positions/check-similarity", response_model=PositionSimilarityResponse)
def check_position_similarity(position_data: PositionCreateRequest):
    """
    Check for similar existing positions before creating a new one.
    
    Uses embedding similarity to find positions with similarity >= threshold (default 0.85).
    
    Args:
        position_data: Position data to check
    
    Returns:
        List of similar positions with similarity scores
    """
    try:
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if we have any positions with embeddings first
        all_positions = vector_db.get_all_embeddings("Position", limit=1000)
        company_positions = [p for p in all_positions if p.get("company_id") == company_id]
        
        logger.info(f"Checking similarity for position '{position_data.title}'. Found {len(company_positions)} existing positions with embeddings.")
        
        if len(company_positions) == 0:
            # No existing positions with embeddings, so no duplicates possible
            logger.info("No existing positions with embeddings found. Skipping similarity check.")
            return PositionSimilarityResponse(
                similar_positions=[],
                threshold=0.85,
                has_duplicates=False
            )
        
        # Generate embedding for the new position
        embedder = RecruitingKnowledgeGraphEmbedder()
        position_dict = position_data.model_dump()
        position_dict['company_id'] = company_id
        new_embedding = embedder.embed_position(position_dict)
        
        # Search for similar positions
        similar_results = vector_db._search("Position", new_embedding, top_k=10)
        
        logger.info(f"Similarity search returned {len(similar_results)} results")
        
        # Filter by company_id and format results
        threshold = 0.85
        similar_positions = []
        for result in similar_results:
            if result.get("metadata", {}).get("company_id") == company_id:
                similarity = result.get("similarity", 0.0)
                logger.debug(f"Found position {result.get('profile_id')} with similarity {similarity:.3f}")
                if similarity >= threshold:
                    similar_positions.append({
                        "position_id": result.get("profile_id"),
                        "title": result.get("metadata", {}).get("title", "Unknown"),
                        "similarity": float(similarity),
                        "distance": float(result.get("distance", 0.0)),
                        "metadata": result.get("metadata", {})
                    })
        
        logger.info(f"Found {len(similar_positions)} similar positions above threshold {threshold}")
        
        return PositionSimilarityResponse(
            similar_positions=similar_positions,
            threshold=threshold,
            has_duplicates=len(similar_positions) > 0
        )
        
    except Exception as e:
        logger.error(f"Error checking position similarity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking position similarity: {str(e)}")


@router.post("/positions", response_model=PositionResponse, status_code=201)
def create_position(position_data: PositionCreateRequest):
    """
    Create a new position.
    
    Args:
        position_data: Position creation data
    
    Returns:
        Created position
    """
    try:
        import uuid
        from datetime import datetime
        
        # Validate required fields
        if not position_data.title or not position_data.title.strip():
            raise HTTPException(status_code=400, detail="Position title is required")
        
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Validate team_id if provided
        if position_data.team_id:
            team_query = "SELECT id FROM teams WHERE id = %s AND company_id = %s"
            team = postgres.execute_one(team_query, (position_data.team_id, company_id))
            if not team:
                raise HTTPException(status_code=400, detail=f"Team {position_data.team_id} not found")
        
        position_id = str(uuid.uuid4())
        now = datetime.now()
        
        query = """
            INSERT INTO positions (
                id, company_id, title, team_id, description, requirements, must_haves,
                nice_to_haves, experience_level, responsibilities, tech_stack, domains,
                team_context, reporting_to, collaboration, priority, status,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING *
        """
        
        result = postgres.execute_one(query, (
            position_id,
            company_id,
            position_data.title,
            position_data.team_id,
            position_data.description,
            position_data.requirements or [],
            position_data.must_haves or [],
            position_data.nice_to_haves or [],
            position_data.experience_level,
            position_data.responsibilities or [],
            position_data.tech_stack or [],
            position_data.domains or [],
            position_data.team_context,
            position_data.reporting_to,
            position_data.collaboration or [],
            position_data.priority or 'medium',
            position_data.status or 'open',
            now,
            now
        ))
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create position")
        
        # Update team's open_positions if team_id is provided
        if position_data.team_id:
            try:
                team_update_query = """
                    UPDATE teams 
                    SET open_positions = array_append(open_positions, %s),
                        updated_at = %s
                    WHERE id = %s AND company_id = %s
                """
                postgres.execute_query(team_update_query, (position_id, now, position_data.team_id, company_id))
            except Exception as e:
                logger.warning(f"Failed to update team's open_positions: {e}")
        
        # Also store in Weaviate for embeddings (for matching operations)
        try:
            kg = get_knowledge_graph()
            position_dict = {
                'id': result['id'],
                'company_id': result['company_id'],
                'title': result['title'],
                'team_id': result.get('team_id'),
                'description': result.get('description'),
                'requirements': result.get('requirements', []),
                'must_haves': result.get('must_haves', []),
                'nice_to_haves': result.get('nice_to_haves', []),
                'experience_level': result.get('experience_level'),
                'responsibilities': result.get('responsibilities', []),
                'tech_stack': result.get('tech_stack', []),
                'domains': result.get('domains', []),
                'team_context': result.get('team_context'),
                'reporting_to': result.get('reporting_to'),
                'collaboration': result.get('collaboration', []),
                'priority': result.get('priority', 'medium'),
                'status': result.get('status', 'open'),
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
            kg.add_position(position_dict)
            logger.info(f"Position {result['id']} also stored in Weaviate for embeddings")
        except Exception as e:
            logger.warning(f"Failed to store position in Weaviate (non-critical): {e}")
            # Non-critical: continue even if Weaviate storage fails
        
        return PositionResponse(
            id=result['id'],
            company_id=result['company_id'],
            title=result['title'],
            team_id=result.get('team_id'),
            description=result.get('description'),
            requirements=result.get('requirements', []),
            must_haves=result.get('must_haves', []),
            nice_to_haves=result.get('nice_to_haves', []),
            experience_level=result.get('experience_level'),
            responsibilities=result.get('responsibilities', []),
            tech_stack=result.get('tech_stack', []),
            domains=result.get('domains', []),
            team_context=result.get('team_context'),
            reporting_to=result.get('reporting_to'),
            collaboration=result.get('collaboration', []),
            priority=result.get('priority', 'medium'),
            status=result.get('status', 'open'),
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating position: {str(e)}")


@router.put("/positions/{position_id}", response_model=PositionResponse)
def update_position(position_id: str, position_data: PositionUpdateRequest):
    """
    Update an existing position.
    
    Args:
        position_id: Position ID
        position_data: Position update data
    
    Returns:
        Updated position
    """
    try:
        from datetime import datetime
        
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if position exists
        existing = postgres.execute_one(
            "SELECT * FROM positions WHERE id = %s AND company_id = %s",
            (position_id, company_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        # Validate team_id if provided
        if position_data.team_id:
            team_query = "SELECT id FROM teams WHERE id = %s AND company_id = %s"
            team = postgres.execute_one(team_query, (position_data.team_id, company_id))
            if not team:
                raise HTTPException(status_code=400, detail=f"Team {position_data.team_id} not found")
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if position_data.title is not None:
            update_fields.append("title = %s")
            update_values.append(position_data.title)
        if position_data.team_id is not None:
            update_fields.append("team_id = %s")
            update_values.append(position_data.team_id)
        if position_data.description is not None:
            update_fields.append("description = %s")
            update_values.append(position_data.description)
        if position_data.requirements is not None:
            update_fields.append("requirements = %s")
            update_values.append(position_data.requirements)
        if position_data.must_haves is not None:
            update_fields.append("must_haves = %s")
            update_values.append(position_data.must_haves)
        if position_data.nice_to_haves is not None:
            update_fields.append("nice_to_haves = %s")
            update_values.append(position_data.nice_to_haves)
        if position_data.experience_level is not None:
            update_fields.append("experience_level = %s")
            update_values.append(position_data.experience_level)
        if position_data.responsibilities is not None:
            update_fields.append("responsibilities = %s")
            update_values.append(position_data.responsibilities)
        if position_data.tech_stack is not None:
            update_fields.append("tech_stack = %s")
            update_values.append(position_data.tech_stack)
        if position_data.domains is not None:
            update_fields.append("domains = %s")
            update_values.append(position_data.domains)
        if position_data.team_context is not None:
            update_fields.append("team_context = %s")
            update_values.append(position_data.team_context)
        if position_data.reporting_to is not None:
            update_fields.append("reporting_to = %s")
            update_values.append(position_data.reporting_to)
        if position_data.collaboration is not None:
            update_fields.append("collaboration = %s")
            update_values.append(position_data.collaboration)
        if position_data.priority is not None:
            update_fields.append("priority = %s")
            update_values.append(position_data.priority)
        if position_data.status is not None:
            update_fields.append("status = %s")
            update_values.append(position_data.status)
        
        if not update_fields:
            # No fields to update, return existing
            return PositionResponse(
                id=existing['id'],
                company_id=existing['company_id'],
                title=existing['title'],
                team_id=existing.get('team_id'),
                description=existing.get('description'),
                requirements=existing.get('requirements', []),
                must_haves=existing.get('must_haves', []),
                nice_to_haves=existing.get('nice_to_haves', []),
                experience_level=existing.get('experience_level'),
                responsibilities=existing.get('responsibilities', []),
                tech_stack=existing.get('tech_stack', []),
                domains=existing.get('domains', []),
                team_context=existing.get('team_context'),
                reporting_to=existing.get('reporting_to'),
                collaboration=existing.get('collaboration', []),
                priority=existing.get('priority', 'medium'),
                status=existing.get('status', 'open'),
                created_at=existing['created_at'],
                updated_at=existing['updated_at']
            )
        
        update_fields.append("updated_at = %s")
        update_values.append(datetime.now())
        update_values.extend([position_id, company_id])
        
        query = f"""
            UPDATE positions 
            SET {', '.join(update_fields)}
            WHERE id = %s AND company_id = %s
            RETURNING *
        """
        
        result = postgres.execute_one(query, tuple(update_values))
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update position")
        
        # Update embedding in Weaviate if data changed
        try:
            kg = get_knowledge_graph()
            position_dict = dict(result)
            kg.update_position(position_id, position_dict)
            logger.info(f"Updated embedding for position {position_id}")
        except Exception as e:
            logger.warning(f"Failed to update position embedding in Weaviate: {e}")
        
        return PositionResponse(
            id=result['id'],
            company_id=result['company_id'],
            title=result['title'],
            team_id=result.get('team_id'),
            description=result.get('description'),
            requirements=result.get('requirements', []),
            must_haves=result.get('must_haves', []),
            nice_to_haves=result.get('nice_to_haves', []),
            experience_level=result.get('experience_level'),
            responsibilities=result.get('responsibilities', []),
            tech_stack=result.get('tech_stack', []),
            domains=result.get('domains', []),
            team_context=result.get('team_context'),
            reporting_to=result.get('reporting_to'),
            collaboration=result.get('collaboration', []),
            priority=result.get('priority', 'medium'),
            status=result.get('status', 'open'),
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating position: {str(e)}")


@router.delete("/positions/{position_id}", status_code=204)
def delete_position(position_id: str):
    """
    Delete a position.
    
    Args:
        position_id: Position ID
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if position exists
        existing = postgres.execute_one(
            "SELECT * FROM positions WHERE id = %s AND company_id = %s",
            (position_id, company_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        # Delete from PostgreSQL (cascade will handle position_distribution)
        query = "DELETE FROM positions WHERE id = %s AND company_id = %s"
        rows_affected = postgres.execute_update(query, (position_id, company_id))
        
        if rows_affected == 0:
            raise HTTPException(status_code=500, detail="Failed to delete position")
        
        # Also delete from Weaviate
        try:
            vector_db = get_vector_db_client()
            vector_db.delete_embedding("Position", position_id)
            logger.info(f"Deleted position {position_id} from Weaviate")
        except Exception as e:
            logger.warning(f"Failed to delete position from Weaviate: {e}")
        
        # Remove from team's open_positions if it was assigned
        if existing.get('team_id'):
            try:
                team_update_query = """
                    UPDATE teams 
                    SET open_positions = array_remove(open_positions, %s),
                        updated_at = NOW()
                    WHERE id = %s AND company_id = %s
                """
                postgres.execute_update(team_update_query, (position_id, existing['team_id'], company_id))
            except Exception as e:
                logger.warning(f"Failed to remove position from team's open_positions: {e}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting position: {str(e)}")


@router.post("/positions/{position_id}/generate-embedding", response_model=Dict)
def generate_position_embedding(position_id: str):
    """
    Generate and store embedding for a position that doesn't have one yet.
    
    Args:
        position_id: Position ID
    
    Returns:
        Success message
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Get position from PostgreSQL
        position = postgres.execute_one(
            "SELECT * FROM positions WHERE id = %s AND company_id = %s",
            (position_id, company_id)
        )
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        # Generate and store embedding
        kg = get_knowledge_graph()
        position_dict = dict(position)
        kg.add_position(position_dict)
        
        return {
            "message": f"Embedding generated for position {position_id}",
            "position_id": position_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating position embedding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating position embedding: {str(e)}")


@router.post("/positions/{position_id}/generate-x-post", response_model=Dict)
async def generate_x_post(position_id: str):
    """
    Generate an X (Twitter) post for a position using Grok AI.
    
    The generated post will always end with "interested" (case-insensitive).
    
    Args:
        position_id: Position ID
    
    Returns:
        Generated post text
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Get position from PostgreSQL
        position = postgres.execute_one(
            "SELECT * FROM positions WHERE id = %s AND company_id = %s",
            (position_id, company_id)
        )
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        # Generate post using Grok
        grok = get_grok_client()
        position_dict = dict(position)
        post_text = await grok.generate_x_post(position_dict)
        
        return {
            "post_text": post_text,
            "position_id": position_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating X post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating X post: {str(e)}")


@router.post("/positions/{position_id}/post-to-x", response_model=Dict)
async def post_to_x(position_id: str, request: PostToXRequest):
    """
    Post the generated text to X (Twitter).
    
    Args:
        position_id: Position ID
        request: Request body with post_text (must end with "interested")
    
    Returns:
        Post creation result with post ID
    """
    try:
        post_text = request.post_text
        
        # Validate that post ends with "interested" (case-insensitive)
        if not post_text.lower().strip().endswith("interested"):
            raise HTTPException(
                status_code=400, 
                detail="Post must end with 'interested' (case-insensitive)"
            )
        
        # Post to X using X API
        from backend.integrations.x_api import XAPIClient
        x_client = XAPIClient()
        result = await x_client.create_post(post_text)
        
        # Update distribution flag
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Upsert distribution record
        from datetime import datetime
        now = datetime.now()
        
        # Check if distribution record exists
        existing = postgres.execute_one(
            "SELECT id FROM position_distribution WHERE position_id = %s AND company_id = %s",
            (position_id, company_id)
        )
        
        if existing:
            # Update existing
            postgres.execute_update(
                """
                UPDATE position_distribution 
                SET post_to_x = TRUE, updated_at = %s
                WHERE position_id = %s AND company_id = %s
                """,
                (now, position_id, company_id)
            )
        else:
            # Create new
            import uuid
            postgres.execute_update(
                """
                INSERT INTO position_distribution (id, position_id, company_id, post_to_x, created_at, updated_at)
                VALUES (%s, %s, %s, TRUE, %s, %s)
                """,
                (str(uuid.uuid4()), position_id, company_id, now, now)
            )
        
        return {
            "success": True,
            "post_id": result.get("data", {}).get("id"),
            "post_text": post_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting to X: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error posting to X: {str(e)}")


@router.put("/positions/{position_id}/distribution", response_model=Dict)
def update_position_distribution(position_id: str, distribution: PositionDistributionRequest):
    """
    Update position distribution flags (post_to_x, available_to_grok).
    
    Args:
        position_id: Position ID
        distribution: Distribution settings
    
    Returns:
        Updated distribution settings
    """
    try:
        postgres = get_postgres_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Check if position exists
        position = postgres.execute_one(
            "SELECT id FROM positions WHERE id = %s AND company_id = %s",
            (position_id, company_id)
        )
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        # Upsert distribution record
        from datetime import datetime
        import uuid
        now = datetime.now()
        
        existing = postgres.execute_one(
            "SELECT id FROM position_distribution WHERE position_id = %s AND company_id = %s",
            (position_id, company_id)
        )
        
        if existing:
            # Update existing
            postgres.execute_update(
                """
                UPDATE position_distribution 
                SET post_to_x = %s, available_to_grok = %s, updated_at = %s
                WHERE position_id = %s AND company_id = %s
                """,
                (distribution.post_to_x, distribution.available_to_grok, now, position_id, company_id)
            )
        else:
            # Create new
            postgres.execute_update(
                """
                INSERT INTO position_distribution (id, position_id, company_id, post_to_x, available_to_grok, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), position_id, company_id, distribution.post_to_x, distribution.available_to_grok, now, now)
            )
        
        return {
            "position_id": position_id,
            "post_to_x": distribution.post_to_x,
            "available_to_grok": distribution.available_to_grok
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating position distribution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating position distribution: {str(e)}")


@router.get("/positions/{position_id}/embedding", response_model=Dict)
def get_position_embedding(position_id: str):
    """
    Get embedding vector for a position.
    
    Args:
        position_id: Position ID
    
    Returns:
        Embedding data with vector, dimension, and metadata
    """
    try:
        vector_db = get_vector_db_client()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        embedding_data = vector_db.get_embedding("Position", position_id)
        if not embedding_data:
            raise HTTPException(status_code=404, detail=f"Embedding not found for position {position_id}")
        
        # Verify company_id matches
        if embedding_data.get("company_id") != company_id:
            raise HTTPException(status_code=404, detail=f"Embedding not found for position {position_id}")
        
        embedding_vector = embedding_data.get("embedding", [])
        
        # Calculate statistics
        import numpy as np
        if embedding_vector:
            arr = np.array(embedding_vector)
            stats = {
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "mean": float(np.mean(arr)),
                "magnitude": float(np.linalg.norm(arr))
            }
        else:
            stats = {"min": 0.0, "max": 0.0, "mean": 0.0, "magnitude": 0.0}
        
        return {
            "profile_id": position_id,
            "profile_type": "position",
            "embedding": embedding_vector,
            "dimension": len(embedding_vector) if embedding_vector else 0,
            "statistics": stats,
            "metadata": embedding_data.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position embedding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting position embedding: {str(e)}")


@router.post("/positions/chat/stream")
async def position_creation_chat_stream(request: PositionChatRequest):
    """
    Streaming chat endpoint for AI-powered position creation.
    
    Uses Server-Sent Events (SSE) to stream responses character by character.
    
    Args:
        request: Chat request with conversation history
    
    Returns:
        Streaming response with SSE format
    """
    import uuid
    import json
    import asyncio
    
    async def generate():
        try:
            grok = get_grok_client()
            session_id = request.session_id or str(uuid.uuid4())
            
            # Build system prompt for position creation
            current_data_context = ""
            if request.current_data:
                current_data = request.current_data
                current_data_context = "\n\nCURRENT FORM DATA (for context - user may want to update these):\n"
                if current_data.title:
                    current_data_context += f"- title: {current_data.title}\n"
                if current_data.team_id:
                    current_data_context += f"- team_id: {current_data.team_id}\n"
                if current_data.description:
                    current_data_context += f"- description: {current_data.description}\n"
                if current_data.requirements:
                    current_data_context += f"- requirements: {', '.join(current_data.requirements)}\n"
                if current_data.must_haves:
                    current_data_context += f"- must_haves: {', '.join(current_data.must_haves)}\n"
                if current_data.nice_to_haves:
                    current_data_context += f"- nice_to_haves: {', '.join(current_data.nice_to_haves)}\n"
                if current_data.experience_level:
                    current_data_context += f"- experience_level: {current_data.experience_level}\n"
                if current_data.responsibilities:
                    current_data_context += f"- responsibilities: {', '.join(current_data.responsibilities)}\n"
                if current_data.tech_stack:
                    current_data_context += f"- tech_stack: {', '.join(current_data.tech_stack)}\n"
                if current_data.domains:
                    current_data_context += f"- domains: {', '.join(current_data.domains)}\n"
                if current_data.team_context:
                    current_data_context += f"- team_context: {current_data.team_context}\n"
                if current_data.reporting_to:
                    current_data_context += f"- reporting_to: {current_data.reporting_to}\n"
                if current_data.collaboration:
                    current_data_context += f"- collaboration: {', '.join(current_data.collaboration)}\n"
                if current_data.priority:
                    current_data_context += f"- priority: {current_data.priority}\n"
                current_data_context += "\nUse this as context. If the user wants to update something, acknowledge what's currently there and help them refine it."
            
            system_prompt = f"""You are a helpful AI assistant helping to create a new job position for xAI. 
Your goal is to ask questions one at a time to gather the following information:
- title (required): Job title
- team_id (optional): Team ID that is hiring for this position
- description (optional): Full job description
- requirements (optional): List of required skills/qualifications
- must_haves (optional): List of must-have skills (e.g., "CUDA, C++, PyTorch")
- nice_to_haves (optional): List of nice-to-have skills
- experience_level (optional): Experience level (Junior, Mid, Senior, Staff)
- responsibilities (optional): List of key responsibilities
- tech_stack (optional): List of technologies used (e.g., "Python, FastAPI, PostgreSQL")
- domains (optional): List of domain focus (e.g., "LLM Inference, GPU Computing")
- team_context (optional): How role fits in team
- reporting_to (optional): Who they report to
- collaboration (optional): List of who they work with
- priority (optional): Priority level (high, medium, low)
{current_data_context}

Ask ONE question at a time. Start with: "What role are you looking to fill?"

After each user response, extract the information and ask the next question. 
Once you have the title (required), you can ask about other fields. 
When you have enough information (at minimum the title), respond with a JSON object containing the extracted data.

Format your final response as JSON when complete:
{{
    "message": "Great! I have all the information I need.",
    "is_complete": true,
    "position_data": {{
        "title": "...",
        "team_id": "...",
        "description": "...",
        "requirements": [...],
        "must_haves": [...],
        "nice_to_haves": [...],
        "experience_level": "...",
        "responsibilities": [...],
        "tech_stack": [...],
        "domains": [...],
        "team_context": "...",
        "reporting_to": "...",
        "collaboration": [...],
        "priority": "..."
    }}
}}

Otherwise, just respond with a natural follow-up question."""
            
            # Build conversation messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            for msg in request.messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # If this is the first message, add the initial question
            if len(request.messages) == 0:
                messages.append({
                    "role": "assistant",
                    "content": "What role are you looking to fill?"
                })
            
            # Call Grok API with streaming
            url = f"{grok.base_url}/chat/completions"
            payload = {
                "model": "grok-4-1-fast-reasoning",
                "messages": messages,
                "temperature": 0.7,
                "stream": True
            }
            
            # Use a longer timeout for streaming requests (5 minutes)
            streaming_client = httpx.AsyncClient(timeout=300.0)
            try:
                async with streaming_client.stream("POST", url, headers=grok.headers, json=payload) as response:
                    if response.status_code >= 400:
                        error_detail = f"Grok API chat request failed: {response.status_code}"
                        try:
                            error_body = await response.aread()
                            error_text = error_body.decode() if isinstance(error_body, bytes) else str(error_body)
                            error_detail += f" - {error_text[:200]}"
                        except Exception:
                            pass
                        logger.error(error_detail)
                        yield f"data: {json.dumps({'error': error_detail})}\n\n"
                        return
                    
                    # Stream the response following Grok's SSE format
                    full_message = ""
                    finish_reason = None
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        # Grok sends lines in format: "data: {json}" or "data: [DONE]"
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:].strip()  # Remove "data: " prefix
                        
                        # Check for end of stream
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract content from delta (Grok format: choices[0].delta.content)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    full_message += content
                                    # Forward the content chunk to frontend
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                                
                                # Check for finish_reason (indicates end of stream)
                                finish_reason = choices[0].get("finish_reason")
                                if finish_reason:
                                    # Stream is complete, parse final message
                                    break
                                
                        except json.JSONDecodeError as e:
                            logger.debug(f"Could not parse SSE line: {line[:100]}")
                            continue
                    
                    # After stream completes, parse the full message for completion status
                    is_complete = False
                    position_data = None
                    
                    if full_message and ("is_complete" in full_message or "position_data" in full_message):
                        try:
                            # Try to extract JSON from the response
                            json_start = full_message.find("{")
                            json_end = full_message.rfind("}") + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = full_message[json_start:json_end]
                                parsed = json.loads(json_str)
                                if parsed.get("is_complete"):
                                    is_complete = True
                                    position_data_dict = parsed.get("position_data", {})
                                    if position_data_dict:
                                        position_data = position_data_dict
                                        full_message = parsed.get("message", "Great! I have all the information I need.")
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Could not parse JSON from Grok response: {e}")
                    
                    # Send final data with complete message
                    yield f"data: {json.dumps({'final': {'message': full_message, 'is_complete': is_complete, 'position_data': position_data, 'session_id': session_id}})}\n\n"
                    
                    # End stream
                    yield "data: [DONE]\n\n"
            finally:
                await streaming_client.aclose()
            
        except Exception as e:
            logger.error(f"Error in streaming position creation chat: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

