"""
API route handlers for Grok Recruiter endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List

from backend.api.models import (
    RoleRequest,
    OutreachRequest,
    FeedbackRequest,
    SourcingResponse,
    HealthResponse,
    Candidate
)
from backend.orchestration.pipeline import RecruitingPipeline
from backend.orchestration.recruiter_agent import RecruiterAgent
from backend.simulator.x_dm_simulator import XDMSimulator
from backend.integrations.grok_api import GrokAPIClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize shared instances
pipeline = RecruitingPipeline()
simulator = XDMSimulator()
grok_client = GrokAPIClient()
recruiter_agent = RecruiterAgent(
    grok_client=grok_client,
    pipeline=pipeline,
    simulator=simulator
)


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
        # Process role request through pipeline
        result = await pipeline.process_role_request(
            role.description,
            role_title=role.title
        )
        
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
        candidates_data = pipeline.get_candidates_for_role(role_id)
        
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
        # Get candidate and role data
        candidates = pipeline.get_candidates_for_role(outreach.role_id)
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

