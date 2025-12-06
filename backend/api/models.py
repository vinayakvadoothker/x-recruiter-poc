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

