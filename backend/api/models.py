"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Candidate(BaseModel):
    """Candidate data structure."""
    
    github_handle: str = Field(..., description="GitHub username")
    x_handle: Optional[str] = Field(None, description="X (Twitter) username")
    profile_data: Dict[str, Any] = Field(default_factory=dict, description="Profile information")
    repos: List[Dict[str, Any]] = Field(default_factory=list, description="List of repositories")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experience: List[str] = Field(default_factory=list, description="Work experience")
    education: List[str] = Field(default_factory=list, description="Education background")
    similarity_score: Optional[float] = Field(None, description="Graph similarity score")
    bandit_score: Optional[float] = Field(None, description="Bandit algorithm score")


class Role(BaseModel):
    """Role description and requirements."""
    
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Role description")
    requirements: List[str] = Field(default_factory=list, description="Required skills/qualifications")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Creation timestamp")


class RoleRequest(BaseModel):
    """Request model for /sourcing endpoint."""
    
    description: str = Field(..., description="Role description text")
    title: Optional[str] = Field(None, description="Job title")
    requirements: Optional[List[str]] = Field(None, description="Required skills")


class OutreachRequest(BaseModel):
    """Request model for /outreach endpoint."""
    
    candidate_id: str = Field(..., description="Candidate identifier")
    role_id: str = Field(..., description="Role identifier")
    message: Optional[str] = Field(None, description="Custom message (optional, will be generated if not provided)")


class FeedbackRequest(BaseModel):
    """Request model for /feedback endpoint."""
    
    candidate_id: str = Field(..., description="Candidate identifier")
    role_id: str = Field(..., description="Role identifier")
    feedback_type: str = Field(..., description="Type of feedback: 'positive', 'negative', or 'neutral'")
    feedback_text: Optional[str] = Field(None, description="Additional feedback text")
    reward: Optional[float] = Field(None, description="Reward value for bandit update (0.0 to 1.0)")


class SourcingResponse(BaseModel):
    """Response model for /sourcing endpoint."""
    
    role_id: str = Field(..., description="Generated role identifier")
    candidates: List[Candidate] = Field(..., description="List of sourced candidates")
    total_found: int = Field(..., description="Total number of candidates found")


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")


class PhoneScreenRequest(BaseModel):
    """Request model for /phone-screen endpoint."""
    
    candidate_id: str = Field(..., description="Candidate identifier")
    position_id: str = Field(..., description="Position identifier")


class PhoneScreenResponse(BaseModel):
    """Response model for /phone-screen endpoint."""
    
    candidate_id: str = Field(..., description="Candidate identifier")
    position_id: str = Field(..., description="Position identifier")
    call_id: str = Field(..., description="Vapi call ID")
    decision: Dict[str, Any] = Field(..., description="Decision result from decision engine")
    extracted_info: Dict[str, Any] = Field(..., description="Extracted information from conversation")
    status: str = Field(..., description="Status: 'completed' or 'error'")


class QueryRequest(BaseModel):
    """Request model for /candidates/query endpoint."""
    
    cluster: Optional[str] = Field(None, description="Ability cluster name")
    required_skills: Optional[List[str]] = Field(None, description="Required skills (AND)")
    excluded_skills: Optional[List[str]] = Field(None, description="Excluded skills (NOT)")
    optional_skills: Optional[List[str]] = Field(None, description="Optional skills (OR)")
    min_arxiv_papers: Optional[int] = Field(None, description="Minimum arXiv papers")
    min_github_stars: Optional[int] = Field(None, description="Minimum GitHub stars")
    min_x_followers: Optional[int] = Field(None, description="Minimum X followers")
    min_experience_years: Optional[int] = Field(None, description="Minimum experience years")
    required_domains: Optional[List[str]] = Field(None, description="Required domains")
    similarity_query: Optional[str] = Field(None, description="Semantic similarity query text")
    top_k: int = Field(50, description="Maximum number of results")


class ExceptionalTalentRequest(BaseModel):
    """Request model for /candidates/exceptional endpoint."""
    
    position_id: str = Field(..., description="Position ID (REQUIRED - finds exceptional talent FOR this position)")
    min_score: float = Field(0.90, description="Minimum combined score (0.0-1.0). Default 0.90 = EXTREMELY STRICT")
    min_arxiv_papers: int = Field(0, description="Optional: Minimum arXiv papers (filter)")
    min_github_stars: int = Field(0, description="Optional: Minimum GitHub stars (filter)")
    min_x_followers: int = Field(0, description="Optional: Minimum X followers (filter)")
    top_k: int = Field(20, description="Maximum number of results")


# Phase 1: Teams Management Models

class TeamCreateRequest(BaseModel):
    """Request model for creating a team."""
    
    name: str = Field(..., description="Team name")
    department: Optional[str] = Field(None, description="Department name")
    needs: Optional[List[str]] = Field(default_factory=list, description="Team needs/skills gaps")
    expertise: Optional[List[str]] = Field(default_factory=list, description="Team expertise areas")
    stack: Optional[List[str]] = Field(default_factory=list, description="Technologies used by team")
    domains: Optional[List[str]] = Field(default_factory=list, description="Domain expertise")
    culture: Optional[str] = Field(None, description="Team culture description")
    work_style: Optional[str] = Field(None, description="Work style description")
    hiring_priorities: Optional[List[str]] = Field(default_factory=list, description="Hiring priorities")


class TeamUpdateRequest(BaseModel):
    """Request model for updating a team."""
    
    name: Optional[str] = Field(None, description="Team name")
    department: Optional[str] = Field(None, description="Department name")
    needs: Optional[List[str]] = Field(None, description="Team needs/skills gaps")
    expertise: Optional[List[str]] = Field(None, description="Team expertise areas")
    stack: Optional[List[str]] = Field(None, description="Technologies used by team")
    domains: Optional[List[str]] = Field(None, description="Domain expertise")
    culture: Optional[str] = Field(None, description="Team culture description")
    work_style: Optional[str] = Field(None, description="Work style description")
    hiring_priorities: Optional[List[str]] = Field(None, description="Hiring priorities")


class TeamResponse(BaseModel):
    """Response model for team data."""
    
    id: str = Field(..., description="Team ID")
    company_id: str = Field(..., description="Company ID")
    name: str = Field(..., description="Team name")
    department: Optional[str] = Field(None, description="Department name")
    needs: List[str] = Field(default_factory=list, description="Team needs/skills gaps")
    expertise: List[str] = Field(default_factory=list, description="Team expertise areas")
    stack: List[str] = Field(default_factory=list, description="Technologies used by team")
    domains: List[str] = Field(default_factory=list, description="Domain expertise")
    culture: Optional[str] = Field(None, description="Team culture description")
    work_style: Optional[str] = Field(None, description="Work style description")
    hiring_priorities: List[str] = Field(default_factory=list, description="Hiring priorities")
    member_count: int = Field(0, description="Number of team members")
    member_ids: List[str] = Field(default_factory=list, description="Team member IDs")
    open_positions: List[str] = Field(default_factory=list, description="Open position IDs")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TeamChatMessage(BaseModel):
    """Message in team creation chat."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class TeamChatRequest(BaseModel):
    """Request model for team creation chat."""
    
    messages: List[TeamChatMessage] = Field(..., description="Conversation history")
    session_id: Optional[str] = Field(None, description="Session ID for progress tracking")
    current_data: Optional[TeamCreateRequest] = Field(None, description="Current form data for context")


class TeamChatResponse(BaseModel):
    """Response model for team creation chat."""
    
    message: str = Field(..., description="Assistant's response message")
    is_complete: bool = Field(False, description="Whether all required fields are collected")
    team_data: Optional[TeamCreateRequest] = Field(None, description="Extracted team data if complete")
    session_id: str = Field(..., description="Session ID for progress tracking")


# Phase 2: Interviewers Management Models

class InterviewerCreateRequest(BaseModel):
    """Request model for creating an interviewer."""
    
    name: str = Field(..., description="Interviewer name (required)")
    phone_number: str = Field(..., description="Phone number (required)")
    email: str = Field(..., description="Email address (required)")
    team_id: Optional[str] = Field(None, description="Team ID (optional)")
    expertise: Optional[List[str]] = Field(default_factory=list, description="Technical expertise areas")
    expertise_level: Optional[str] = Field(None, description="Depth of expertise")
    specializations: Optional[List[str]] = Field(default_factory=list, description="Specialized areas")
    interview_style: Optional[str] = Field(None, description="Interview style description")
    evaluation_focus: Optional[List[str]] = Field(default_factory=list, description="What they focus on during interviews")
    question_style: Optional[str] = Field(None, description="Question style")
    preferred_interview_types: Optional[List[str]] = Field(default_factory=list, description="Preferred interview types")


class InterviewerUpdateRequest(BaseModel):
    """Request model for updating an interviewer."""
    
    name: Optional[str] = Field(None, description="Interviewer name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    team_id: Optional[str] = Field(None, description="Team ID (can be set to None to unassign)")
    expertise: Optional[List[str]] = Field(None, description="Technical expertise areas")
    expertise_level: Optional[str] = Field(None, description="Depth of expertise")
    specializations: Optional[List[str]] = Field(None, description="Specialized areas")
    interview_style: Optional[str] = Field(None, description="Interview style description")
    evaluation_focus: Optional[List[str]] = Field(None, description="What they focus on during interviews")
    question_style: Optional[str] = Field(None, description="Question style")
    preferred_interview_types: Optional[List[str]] = Field(None, description="Preferred interview types")


class InterviewerResponse(BaseModel):
    """Response model for interviewer data."""
    
    id: str = Field(..., description="Interviewer ID")
    company_id: str = Field(..., description="Company ID")
    team_id: Optional[str] = Field(None, description="Team ID (optional)")
    name: str = Field(..., description="Interviewer name")
    phone_number: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    expertise: List[str] = Field(default_factory=list, description="Technical expertise areas")
    expertise_level: Optional[str] = Field(None, description="Depth of expertise")
    specializations: List[str] = Field(default_factory=list, description="Specialized areas")
    interview_style: Optional[str] = Field(None, description="Interview style description")
    evaluation_focus: List[str] = Field(default_factory=list, description="What they focus on during interviews")
    question_style: Optional[str] = Field(None, description="Question style")
    preferred_interview_types: List[str] = Field(default_factory=list, description="Preferred interview types")
    total_interviews: int = Field(0, description="Total interviews conducted")
    successful_hires: int = Field(0, description="Successful hires")
    success_rate: float = Field(0.0, description="Success rate (0-1)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class InterviewerChatMessage(BaseModel):
    """Message in interviewer creation chat."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class InterviewerChatRequest(BaseModel):
    """Request model for interviewer creation chat."""
    
    messages: List[InterviewerChatMessage] = Field(..., description="Conversation history")
    session_id: Optional[str] = Field(None, description="Session ID for progress tracking")
    current_data: Optional[InterviewerCreateRequest] = Field(None, description="Current form data for context")


class MatchRequest(BaseModel):
    """Request model for /candidates/{candidate_id}/match endpoint."""
    position_id: Optional[str] = Field(None, description="Position ID (optional, for position-specific matching)")


class MatchResponse(BaseModel):
    """Response model for /candidates/{candidate_id}/match endpoint."""
    candidate_id: str = Field(..., description="Candidate identifier")
    team_match: Optional[Dict[str, Any]] = Field(None, description="Team match result")
    interviewer_match: Optional[Dict[str, Any]] = Field(None, description="Interviewer match result")
    position_id: Optional[str] = Field(None, description="Position ID if provided")


# Phase 3: Position Management Models

class PositionCreateRequest(BaseModel):
    """Request model for creating a position."""
    
    title: Optional[str] = Field(None, description="Job title (required for creation, optional for chat context)")
    team_id: Optional[str] = Field(None, description="Team ID (optional)")
    description: Optional[str] = Field(None, description="Full job description")
    requirements: Optional[List[str]] = Field(default_factory=list, description="Required skills/qualifications")
    must_haves: Optional[List[str]] = Field(default_factory=list, description="Must-have skills")
    nice_to_haves: Optional[List[str]] = Field(default_factory=list, description="Nice-to-have skills")
    experience_level: Optional[str] = Field(None, description="Experience level: Junior, Mid, Senior, Staff")
    responsibilities: Optional[List[str]] = Field(default_factory=list, description="Key responsibilities")
    tech_stack: Optional[List[str]] = Field(default_factory=list, description="Technologies used")
    domains: Optional[List[str]] = Field(default_factory=list, description="Domain focus")
    team_context: Optional[str] = Field(None, description="How role fits in team")
    reporting_to: Optional[str] = Field(None, description="Who they report to")
    collaboration: Optional[List[str]] = Field(default_factory=list, description="Who they work with")
    priority: Optional[str] = Field("medium", description="Priority: high, medium, low")
    status: Optional[str] = Field("open", description="Status: open, in-progress, on-hold, filled, cancelled")


class PositionUpdateRequest(BaseModel):
    """Request model for updating a position."""
    
    title: Optional[str] = Field(None, description="Job title")
    team_id: Optional[str] = Field(None, description="Team ID")
    description: Optional[str] = Field(None, description="Full job description")
    requirements: Optional[List[str]] = Field(None, description="Required skills/qualifications")
    must_haves: Optional[List[str]] = Field(None, description="Must-have skills")
    nice_to_haves: Optional[List[str]] = Field(None, description="Nice-to-have skills")
    experience_level: Optional[str] = Field(None, description="Experience level")
    responsibilities: Optional[List[str]] = Field(None, description="Key responsibilities")
    tech_stack: Optional[List[str]] = Field(None, description="Technologies used")
    domains: Optional[List[str]] = Field(None, description="Domain focus")
    team_context: Optional[str] = Field(None, description="How role fits in team")
    reporting_to: Optional[str] = Field(None, description="Who they report to")
    collaboration: Optional[List[str]] = Field(None, description="Who they work with")
    priority: Optional[str] = Field(None, description="Priority")
    status: Optional[str] = Field(None, description="Status")


class PositionResponse(BaseModel):
    """Response model for position data."""
    
    id: str = Field(..., description="Position ID")
    company_id: str = Field(..., description="Company ID")
    title: str = Field(..., description="Job title")
    team_id: Optional[str] = Field(None, description="Team ID")
    description: Optional[str] = Field(None, description="Full job description")
    requirements: List[str] = Field(default_factory=list, description="Required skills/qualifications")
    must_haves: List[str] = Field(default_factory=list, description="Must-have skills")
    nice_to_haves: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    experience_level: Optional[str] = Field(None, description="Experience level")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    domains: List[str] = Field(default_factory=list, description="Domain focus")
    team_context: Optional[str] = Field(None, description="How role fits in team")
    reporting_to: Optional[str] = Field(None, description="Who they report to")
    collaboration: List[str] = Field(default_factory=list, description="Who they work with")
    priority: str = Field("medium", description="Priority")
    status: str = Field("open", description="Status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PositionChatMessage(BaseModel):
    """Message in position creation chat."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class PositionChatRequest(BaseModel):
    """Request model for position creation chat."""
    
    messages: List[PositionChatMessage] = Field(..., description="Conversation history")
    session_id: Optional[str] = Field(None, description="Session ID for progress tracking")
    current_data: Optional[PositionCreateRequest] = Field(None, description="Current form data for context")


class PositionSimilarityResponse(BaseModel):
    """Response model for position similarity check."""
    
    similar_positions: List[Dict[str, Any]] = Field(..., description="List of similar positions with similarity scores")
    threshold: float = Field(0.85, description="Similarity threshold used")
    has_duplicates: bool = Field(..., description="Whether any positions exceed threshold")


class PositionDistributionRequest(BaseModel):
    """Request model for position distribution settings."""
    
    post_to_x: bool = Field(False, description="Post position to X")
    available_to_grok: bool = Field(False, description="Make available to Grok")


class PostToXRequest(BaseModel):
    """Request model for posting to X."""
    
    post_text: str = Field(..., description="Post text (must end with 'interested')")

