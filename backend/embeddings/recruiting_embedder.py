"""
recruiting_embedder.py - Specialized embedder for recruiting knowledge graph

This module implements a highly specialized embedder for the recruiting domain,
creating domain-specific embeddings for 4 profile types using sentence-transformers.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Entity extraction methodology (skills, experience, education)
    - Our adaptation: We use specialized formatting to extract key information
      from profiles before embedding, following the entity-focused approach from [1]

Our Novel Contribution:
Specialized multi-modal embedder: Creates domain-specific embeddings for 4 profile
types (candidates, teams, interviewers, positions) with specialized formatting
that focuses on the most relevant information for each profile type. This enables
better similarity matching than generic embeddings.

Key functions:
- RecruitingKnowledgeGraphEmbedder: Main embedder class
- embed_candidate(): Generate candidate-specific embedding
- embed_team(): Generate team-specific embedding
- embed_interviewer(): Generate interviewer-specific embedding
- embed_position(): Generate position-specific embedding

Dependencies:
- sentence-transformers: Pre-trained transformer models for embeddings
- numpy: Numerical array operations
- torch: Required by sentence-transformers

Implementation Rationale:

Why sentence-transformers over other embedding approaches:
1. **Local execution**: sentence-transformers runs locally, no API calls needed
   - Alternative: Grok/OpenAI embeddings API - Rejected because:
     * API rate limits and costs for high-volume embedding generation
     * Network latency for each embedding request
     * Dependency on external service availability
   - Trade-off: Larger model size (~400MB for MPNet) but faster for batch operations

2. **Specialized formatting per profile type**: Custom text formatting before embedding
   - Alternative: Direct embedding of raw JSON/dict - Rejected because:
     * Raw data includes irrelevant fields (IDs, timestamps, metadata)
     * Doesn't emphasize key matching factors (skills, needs, requirements)
     * Generic embeddings don't capture domain-specific relationships
   - Our approach: Format each profile type to emphasize relevant information
     * Candidates: Skills, experience depth, project impact
     * Teams: Hiring needs, expertise gaps, culture
     * Interviewers: Interview expertise, success patterns, evaluation style
     * Positions: Requirements, must-haves, team context

3. **Single model for all profile types**: Use one model (all-mpnet-base-v2) for all 4 types
   - Alternative: Separate models per profile type - Rejected because:
     * More complex deployment and maintenance
     * Model loading overhead (4x memory usage)
     * Cross-type similarity still works with single model
   - Trade-off: Slightly less specialized per type, but simpler and more maintainable

4. **Normalized embeddings**: Always normalize to unit vectors
   - Why: Enables cosine similarity (dot product) for fast similarity search
   - Alternative: Raw embeddings - Rejected because:
     * Magnitude differences can skew similarity scores
     * Cosine similarity is standard for semantic similarity
   - Trade-off: Slight computational overhead for normalization, but standard practice

5. **In-memory formatting functions**: Format profiles in Python before embedding
   - Alternative: Pre-process and store formatted text - Rejected because:
     * Profiles update frequently, would need re-formatting anyway
     * Formatting logic is simple and fast
     * Keeps data model clean (store raw data, format on-demand)
   - Trade-off: Small CPU overhead per embedding, but simpler data model

Design Decisions:
- **Model choice (all-mpnet-base-v2)**: 768 dimensions, high quality, good balance
  - Alternative: all-MiniLM-L6-v2 (384 dims, faster) - Rejected for quality
  - Alternative: Larger models (1024+ dims) - Rejected for speed/memory
- **Separate format methods per type**: Each profile type has unique _format_* method
  - Why: Different profile types have different key fields to emphasize
  - Alternative: Single generic formatter - Rejected for lack of specialization
- **String formatting over structured data**: Convert to text before embedding
  - Why: Transformers work best with natural language text
  - Alternative: Embed structured data directly - Rejected (transformers expect text)
"""

from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Optional
import numpy as np


class RecruitingKnowledgeGraphEmbedder:
    """
    Highly specialized embedder for recruiting knowledge graph.
    
    Creates domain-specific embeddings for 4 profile types:
    1. Candidate profiles - Focus: Technical abilities, experience depth, project impact
    2. Team profiles - Focus: Team needs, culture, expertise gaps
    3. Interviewer profiles - Focus: Interview expertise, success patterns, evaluation style
    4. Position profiles - Focus: Requirements, must-haves, team context
    
    Uses sentence-transformers with specialized formatting per profile type to
    ensure embeddings capture the most relevant information for matching.
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize embedder with base model.
        
        Args:
            model_name: Sentence-transformer model name
                       Options:
                       - 'all-mpnet-base-v2' (default): Best quality, 768 dimensions
                       - 'all-MiniLM-L6-v2': Faster, 384 dimensions
        
        Raises:
            ImportError: If sentence-transformers is not installed
        """
        try:
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers>=2.2.0"
            )
    
    def embed_candidate(self, candidate_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate candidate-specific embedding.
        
        Focus: Technical abilities, experience depth, project impact.
        This method formats candidate data to emphasize skills, experience,
        and project work that are most relevant for matching.
        
        Args:
            candidate_data: Candidate profile dictionary with keys:
                - skills: List[str] - Technical skills
                - experience: List[str] - Work experience descriptions
                - experience_years: int - Years of experience
                - domains: List[str] - Domain expertise
                - education: List[str] - Education background
                - projects: List[Dict] - Project information
                - expertise_level: str - Junior/Mid/Senior/Staff
                - github_stats: Dict - GitHub activity stats
        
        Returns:
            Embedding vector as numpy array (shape: (768,) for MPNet)
            Normalized to unit length for cosine similarity
        
        Example:
            >>> embedder = RecruitingKnowledgeGraphEmbedder()
            >>> candidate = {
            ...     'skills': ['CUDA', 'C++', 'PyTorch'],
            ...     'experience_years': 5,
            ...     'domains': ['LLM Inference']
            ... }
            >>> embedding = embedder.embed_candidate(candidate)
            >>> assert embedding.shape == (768,)
            >>> assert np.isclose(np.linalg.norm(embedding), 1.0)  # Normalized
        """
        text = self._format_candidate_profile(candidate_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def _format_candidate_profile(self, data: Dict[str, Any]) -> str:
        """
        Format candidate profile data into specialized text for embedding.
        
        This formatting emphasizes technical skills, experience depth, and
        project impact - the key factors for candidate matching.
        
        Args:
            data: Candidate profile dictionary
        
        Returns:
            Formatted text string optimized for embedding
        """
        skills = ', '.join(data.get('skills', []))
        experience = ', '.join(data.get('experience', []))
        education = ', '.join(data.get('education', []))
        projects = ', '.join([
            p.get('name', '') for p in data.get('projects', [])
        ])
        
        return f"""
        CANDIDATE PROFILE:
        Technical Skills: {skills}
        Experience: {data.get('experience_years', 0)} years in {', '.join(data.get('domains', []))}
        Experience Details: {experience}
        Education: {education}
        Key Projects: {projects}
        Expertise Level: {data.get('expertise_level', 'Unknown')}
        GitHub Activity: {data.get('github_stats', {}).get('total_commits', 0)} commits
        """
    
    def embed_team(self, team_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate team-specific embedding.
        
        Focus: Team needs, culture, expertise gaps.
        This method formats team data to emphasize hiring needs, expertise areas,
        and team culture - the key factors for team-candidate matching.
        
        Args:
            team_data: Team profile dictionary with keys:
                - name: str - Team name
                - department: str - Department/org
                - needs: List[str] - What team needs (skills, roles)
                - expertise: List[str] - Team's expertise areas
                - stack: List[str] - Technical stack
                - domains: List[str] - Domain focus
                - culture: str - Team culture description
                - work_style: str - Work style (remote, hybrid, etc.)
                - hiring_priorities: List[str] - Priority areas
                - member_count: int - Number of members
                - open_positions: List[str] - Open position IDs
        
        Returns:
            Embedding vector as numpy array (shape: (768,) for MPNet)
            Normalized to unit length for cosine similarity
        
        Example:
            >>> embedder = RecruitingKnowledgeGraphEmbedder()
            >>> team = {
            ...     'name': 'LLM Inference Team',
            ...     'needs': ['CUDA expertise', 'GPU optimization'],
            ...     'expertise': ['CUDA', 'GPU Computing']
            ... }
            >>> embedding = embedder.embed_team(team)
            >>> assert embedding.shape == (768,)
            >>> assert np.isclose(np.linalg.norm(embedding), 1.0)  # Normalized
        """
        text = self._format_team_profile(team_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_interviewer(self, interviewer_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate interviewer-specific embedding.
        
        Focus: Interview expertise, success patterns, evaluation style.
        This method formats interviewer data to emphasize expertise, interview
        experience, and evaluation approach - the key factors for interviewer matching.
        
        Args:
            interviewer_data: Interviewer profile dictionary with keys:
                - name: str - Interviewer name
                - expertise: List[str] - Technical expertise areas
                - expertise_level: str - Depth of expertise
                - specializations: List[str] - Specialized areas
                - total_interviews: int - Total interviews conducted
                - successful_hires: int - Successful hires
                - success_rate: float - Success rate (0-1)
                - interview_style: str - Technical deep-dive, behavioral, etc.
                - evaluation_focus: List[str] - What they focus on
                - question_style: str - Question style
                - preferred_interview_types: List[str] - Types they prefer
        
        Returns:
            Embedding vector as numpy array (shape: (768,) for MPNet)
            Normalized to unit length for cosine similarity
        
        Example:
            >>> embedder = RecruitingKnowledgeGraphEmbedder()
            >>> interviewer = {
            ...     'name': 'Alex Chen',
            ...     'expertise': ['CUDA', 'GPU Optimization'],
            ...     'total_interviews': 50,
            ...     'success_rate': 0.75
            ... }
            >>> embedding = embedder.embed_interviewer(interviewer)
            >>> assert embedding.shape == (768,)
            >>> assert np.isclose(np.linalg.norm(embedding), 1.0)  # Normalized
        """
        text = self._format_interviewer_profile(interviewer_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_position(self, position_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate position-specific embedding.
        
        Focus: Requirements, must-haves, team context.
        This method formats position data to emphasize requirements, must-have skills,
        and team context - the key factors for position-candidate matching.
        
        Args:
            position_data: Position profile dictionary with keys:
                - title: str - Job title
                - description: str - Full job description
                - requirements: List[str] - Required skills/qualifications
                - must_haves: List[str] - Must-have skills
                - nice_to_haves: List[str] - Nice-to-have skills
                - experience_level: str - Required experience level
                - tech_stack: List[str] - Technologies used
                - domains: List[str] - Domain focus
                - responsibilities: List[str] - Key responsibilities
                - team_context: str - How role fits in team
        
        Returns:
            Embedding vector as numpy array (shape: (768,) for MPNet)
            Normalized to unit length for cosine similarity
        
        Example:
            >>> embedder = RecruitingKnowledgeGraphEmbedder()
            >>> position = {
            ...     'title': 'Senior LLM Inference Engineer',
            ...     'must_haves': ['CUDA', 'C++', 'PyTorch'],
            ...     'requirements': ['5+ years CUDA']
            ... }
            >>> embedding = embedder.embed_position(position)
            >>> assert embedding.shape == (768,)
            >>> assert np.isclose(np.linalg.norm(embedding), 1.0)  # Normalized
        """
        text = self._format_position_profile(position_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def _format_team_profile(self, data: Dict[str, Any]) -> str:
        """
        Format team profile data into specialized text for embedding.
        
        This formatting emphasizes hiring needs, expertise areas, and team culture
        - the key factors for team-candidate matching.
        
        Args:
            data: Team profile dictionary
        
        Returns:
            Formatted text string optimized for embedding
        """
        needs = ', '.join(data.get('needs', []))
        expertise = ', '.join(data.get('expertise', []))
        stack = ', '.join(data.get('stack', []))
        domains = ', '.join(data.get('domains', []))
        priorities = ', '.join(data.get('hiring_priorities', []))
        
        return f"""
        TEAM PROFILE:
        Team Name: {data.get('name', 'Unknown')}
        Department: {data.get('department', 'Not specified')}
        Current Composition: {data.get('member_count', 0)} members
        Hiring Needs: {needs}
        Hiring Priorities: {priorities}
        Expertise Areas: {expertise}
        Technical Stack: {stack}
        Domain Focus: {domains}
        Team Culture: {data.get('culture', 'Not specified')}
        Work Style: {data.get('work_style', 'Not specified')}
        Open Positions: {len(data.get('open_positions', []))} positions
        """
    
    def _format_interviewer_profile(self, data: Dict[str, Any]) -> str:
        """
        Format interviewer profile data into specialized text for embedding.
        
        This formatting emphasizes interview expertise, success patterns, and
        evaluation style - the key factors for interviewer-candidate matching.
        
        Args:
            data: Interviewer profile dictionary
        
        Returns:
            Formatted text string optimized for embedding
        """
        expertise = ', '.join(data.get('expertise', []))
        specializations = ', '.join(data.get('specializations', []))
        evaluation_focus = ', '.join(data.get('evaluation_focus', []))
        preferred_types = ', '.join(data.get('preferred_interview_types', []))
        
        return f"""
        INTERVIEWER PROFILE:
        Name: {data.get('name', 'Unknown')}
        Expertise: {expertise}
        Expertise Level: {data.get('expertise_level', 'Not specified')}
        Specializations: {specializations}
        Interview Experience: {data.get('total_interviews', 0)} interviews conducted
        Successful Hires: {data.get('successful_hires', 0)}
        Success Rate: {data.get('success_rate', 0.0):.1%}
        Interview Style: {data.get('interview_style', 'Not specified')}
        Evaluation Focus: {evaluation_focus}
        Question Style: {data.get('question_style', 'Not specified')}
        Preferred Interview Types: {preferred_types}
        """
    
    def _format_position_profile(self, data: Dict[str, Any]) -> str:
        """
        Format position profile data into specialized text for embedding.
        
        This formatting emphasizes requirements, must-have skills, and team context
        - the key factors for position-candidate matching.
        
        Args:
            data: Position profile dictionary
        
        Returns:
            Formatted text string optimized for embedding
        """
        requirements = ', '.join(data.get('requirements', []))
        must_haves = ', '.join(data.get('must_haves', []))
        nice_to_haves = ', '.join(data.get('nice_to_haves', []))
        tech_stack = ', '.join(data.get('tech_stack', []))
        domains = ', '.join(data.get('domains', []))
        responsibilities = ', '.join(data.get('responsibilities', []))
        
        # Truncate description to first 200 chars for embedding
        description = data.get('description', '')
        if len(description) > 200:
            description = description[:200] + '...'
        
        return f"""
        POSITION PROFILE:
        Title: {data.get('title', 'Unknown')}
        Description: {description}
        Requirements: {requirements}
        Must-Have Skills: {must_haves}
        Nice-to-Have Skills: {nice_to_haves}
        Experience Level: {data.get('experience_level', 'Not specified')}
        Technical Stack: {tech_stack}
        Domain Focus: {domains}
        Key Responsibilities: {responsibilities}
        Team Context: {data.get('team_context', 'Not specified')}
        Priority: {data.get('priority', 'medium')}
        Status: {data.get('status', 'open')}
        """

