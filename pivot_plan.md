# Pivot Plan: Inbound Review Automation with Specialized Knowledge Graph

## Executive Summary

**New Focus**: Inbound review automation pipeline with specialized embeddings and vector-based knowledge graph.

**Core Innovation**: Graph-warm-started FG-TS algorithm (kept) + specialized multi-profile embedder + vector database for fast similarity search.

**Key Components**:
1. Specialized embedder for 4 profile types (candidates, teams, interviewers, positions)
2. Vector DB storage (replace Neo4j)
3. Knowledge graph abstraction
4. Automated phone screening (production-quality)
5. Team/interviewer matching with profile overview + interview prep
6. Lightweight outbound info gathering (Ishaan - 4 sources)

---

## Architecture Overview

### Current → New

**Storage**:
- Neo4j (graph database) → Vector DB (Pinecone/Weaviate/Qdrant) + lightweight metadata store

**Embeddings**:
- Hash-based placeholders → Specialized multi-modal embedder (sentence-transformers)

**Similarity**:
- kNN on graphs → Vector cosine similarity

**Pipeline**:
- Outbound sourcing → Inbound review automation (phone screen → matching → interview prep)

**Algorithm**:
- Graph-warm-started FG-TS (KEPT - core innovation)
- But uses embedding similarity instead of graph similarity for warm-start

---

## Knowledge Graph Schema

### Profile Types

#### 1. Candidate Profile
```python
{
    "id": str,                    # Unique candidate ID
    "github_handle": str,         # GitHub username
    "x_handle": Optional[str],    # X/Twitter username
    "linkedin_url": Optional[str], # LinkedIn URL
    "arxiv_ids": List[str],       # arXiv paper IDs
    
    # Core profile data
    "skills": List[str],          # Technical skills
    "experience": List[str],       # Work experience descriptions
    "experience_years": int,       # Years of experience
    "domains": List[str],          # Domain expertise (ML, systems, etc.)
    "education": List[str],        # Education background
    "projects": List[Dict],        # Project information
    "github_stats": Dict,          # GitHub activity stats
    "expertise_level": str,        # Junior/Mid/Senior/Staff
    
    # Extracted from sources
    "repos": List[Dict],          # GitHub repositories
    "papers": List[Dict],         # arXiv papers
    "posts": List[Dict],           # X posts (technical content)
    
    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    "source": str,                # "outbound" or "inbound"
    
    # Embedding (computed)
    "embedding": List[float],     # Multi-modal embedding vector
    "ability_cluster": Optional[str]  # Cluster ID (e.g., "CUDA Experts")
}
```

#### 2. Team Profile
```python
{
    "id": str,                    # Unique team ID
    "name": str,                  # Team name
    "department": str,            # Department/org
    
    # Team composition
    "members": List[Dict],        # Current team members
    "member_count": int,          # Number of members
    "member_ids": List[str],      # IDs of team members
    
    # Hiring needs
    "needs": List[str],           # What team needs (skills, roles)
    "open_positions": List[str],  # Open position IDs
    "hiring_priorities": List[str], # Priority areas
    
    # Expertise
    "expertise": List[str],       # Team's expertise areas
    "stack": List[str],           # Technical stack
    "domains": List[str],         # Domain focus
    
    # Culture
    "culture": str,               # Team culture description
    "work_style": str,            # Work style (remote, hybrid, etc.)
    
    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    
    # Embedding (computed)
    "embedding": List[float],     # Team embedding vector
    "cluster": Optional[str]      # Team cluster ID
}
```

#### 3. Interviewer Profile
```python
{
    "id": str,                    # Unique interviewer ID
    "name": str,                  # Interviewer name
    "email": str,                 # Email
    "team_id": str,               # Team they belong to
    
    # Expertise
    "expertise": List[str],       # Technical expertise areas
    "expertise_level": str,       # Depth of expertise
    "specializations": List[str],  # Specialized areas
    
    # Interview history
    "interview_history": List[Dict], # Past interviews
    "total_interviews": int,      # Total interviews conducted
    "successful_hires": int,      # Successful hires
    "success_rate": float,         # Success rate (0-1)
    
    # Interview style
    "interview_style": str,        # Technical deep-dive, behavioral, etc.
    "evaluation_focus": List[str], # What they focus on
    "question_style": str,        # Question style
    
    # Performance by cluster
    "cluster_success_rates": Dict[str, float], # Success rate by ability cluster
    
    # Availability
    "availability": Dict,         # Calendar availability
    "preferred_interview_types": List[str], # Types they prefer
    
    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    
    # Embedding (computed)
    "embedding": List[float]      # Interviewer embedding vector
}
```

#### 4. Position Profile
```python
{
    "id": str,                    # Unique position ID
    "title": str,                 # Job title
    "team_id": str,               # Team hiring for this role
    
    # Requirements
    "description": str,           # Full job description
    "requirements": List[str],    # Required skills/qualifications
    "must_haves": List[str],      # Must-have skills
    "nice_to_haves": List[str],   # Nice-to-have skills
    "experience_level": str,       # Required experience level
    
    # Role details
    "responsibilities": List[str], # Key responsibilities
    "tech_stack": List[str],      # Technologies used
    "domains": List[str],         # Domain focus
    
    # Team context
    "team_context": str,          # How role fits in team
    "reporting_to": str,          # Who they report to
    "collaboration": List[str],   # Who they work with
    
    # Status
    "status": str,                # "open", "filled", "on_hold"
    "priority": str,              # "high", "medium", "low"
    
    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    
    # Embedding (computed)
    "embedding": List[float]      # Position embedding vector
}
```

### Relationships

```python
# Candidate relationships
{
    "candidate_id": str,
    "applied_to_positions": List[str],      # Position IDs
    "interviewed_by": List[str],            # Interviewer IDs
    "matched_to_teams": List[str],           # Team IDs
    "phone_screen_result": Optional[Dict],   # Phone screen outcome
    "assessment_result": Optional[Dict],     # Take-home assessment
    "technical_interview_result": Optional[Dict], # Technical interview
}

# Team relationships
{
    "team_id": str,
    "members": List[str],                    # Interviewer IDs
    "open_positions": List[str],             # Position IDs
    "interviewed_candidates": List[str],     # Candidate IDs
}

# Interviewer relationships
{
    "interviewer_id": str,
    "team_id": str,
    "interviewed_candidates": List[str],      # Candidate IDs
    "successful_matches": List[str],          # Candidate IDs (hired)
}
```

---

## Component 1: Specialized Embedder (Vin - 2-3 hours)

### Implementation

**File**: `backend/embeddings/recruiting_embedder.py`

```python
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any
import numpy as np

class RecruitingKnowledgeGraphEmbedder:
    """
    Highly specialized embedder for recruiting knowledge graph.
    
    Creates domain-specific embeddings for 4 profile types:
    1. Candidate profiles
    2. Team profiles
    3. Interviewer profiles
    4. Position profiles
    
    Uses sentence-transformers with specialized formatting per profile type.
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize embedder with base model.
        
        Args:
            model_name: Sentence-transformer model name
                       Options: 'all-mpnet-base-v2' (best quality),
                                'all-MiniLM-L6-v2' (faster)
        """
        self.model = SentenceTransformer(model_name)
    
    def embed_candidate(self, candidate_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate candidate-specific embedding.
        
        Focus: Technical abilities, experience depth, project impact.
        
        Args:
            candidate_data: Candidate profile dictionary
        
        Returns:
            Embedding vector (numpy array)
        """
        text = self._format_candidate_profile(candidate_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_team(self, team_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate team-specific embedding.
        
        Focus: Team needs, culture, expertise gaps.
        
        Args:
            team_data: Team profile dictionary
        
        Returns:
            Embedding vector (numpy array)
        """
        text = self._format_team_profile(team_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_interviewer(self, interviewer_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate interviewer-specific embedding.
        
        Focus: Interview expertise, success patterns, evaluation style.
        
        Args:
            interviewer_data: Interviewer profile dictionary
        
        Returns:
            Embedding vector (numpy array)
        """
        text = self._format_interviewer_profile(interviewer_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_position(self, position_data: Dict[str, Any]) -> np.ndarray:
        """
        Generate position-specific embedding.
        
        Focus: Requirements, must-haves, team context.
        
        Args:
            position_data: Position profile dictionary
        
        Returns:
            Embedding vector (numpy array)
        """
        text = self._format_position_profile(position_data)
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def _format_candidate_profile(self, data: Dict[str, Any]) -> str:
        """Specialized formatting for candidates."""
        skills = ', '.join(data.get('skills', []))
        experience = ', '.join(data.get('experience', []))
        education = ', '.join(data.get('education', []))
        projects = ', '.join([p.get('name', '') for p in data.get('projects', [])])
        
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
    
    def _format_team_profile(self, data: Dict[str, Any]) -> str:
        """Specialized formatting for teams."""
        return f"""
        TEAM PROFILE:
        Team Name: {data.get('name', 'Unknown')}
        Current Composition: {data.get('member_count', 0)} members
        Hiring Needs: {', '.join(data.get('needs', []))}
        Expertise Areas: {', '.join(data.get('expertise', []))}
        Technical Stack: {', '.join(data.get('stack', []))}
        Team Culture: {data.get('culture', 'Not specified')}
        Work Style: {data.get('work_style', 'Not specified')}
        Open Positions: {len(data.get('open_positions', []))} positions
        """
    
    def _format_interviewer_profile(self, data: Dict[str, Any]) -> str:
        """Specialized formatting for interviewers."""
        expertise = ', '.join(data.get('expertise', []))
        specializations = ', '.join(data.get('specializations', []))
        
        return f"""
        INTERVIEWER PROFILE:
        Name: {data.get('name', 'Unknown')}
        Expertise: {expertise}
        Specializations: {specializations}
        Interview Experience: {data.get('total_interviews', 0)} interviews
        Success Rate: {data.get('success_rate', 0.0):.1%}
        Successful Hires: {data.get('successful_hires', 0)}
        Interview Style: {data.get('interview_style', 'Not specified')}
        Evaluation Focus: {', '.join(data.get('evaluation_focus', []))}
        Question Style: {data.get('question_style', 'Not specified')}
        """
    
    def _format_position_profile(self, data: Dict[str, Any]) -> str:
        """Specialized formatting for positions."""
        requirements = ', '.join(data.get('requirements', []))
        must_haves = ', '.join(data.get('must_haves', []))
        nice_to_haves = ', '.join(data.get('nice_to_haves', []))
        tech_stack = ', '.join(data.get('tech_stack', []))
        
        return f"""
        POSITION PROFILE:
        Title: {data.get('title', 'Unknown')}
        Description: {data.get('description', '')[:200]}
        Requirements: {requirements}
        Must-Have Skills: {must_haves}
        Nice-to-Have Skills: {nice_to_haves}
        Experience Level: {data.get('experience_level', 'Not specified')}
        Technical Stack: {tech_stack}
        Domains: {', '.join(data.get('domains', []))}
        Team Context: {data.get('team_context', 'Not specified')}
        """
```

### Dependencies

Add to `requirements-vin.txt`:
```
sentence-transformers>=2.2.0
torch>=2.0.0  # Required by sentence-transformers
```

### Testing

**File**: `tests/test_recruiting_embedder.py`

- Test all 4 embed methods
- Test embedding dimensions
- Test normalization
- Test with minimal data
- Test with full data

---

## Component 2: Vector DB Storage (Vin - 2-3 hours)

### Choice: Weaviate (self-hosted) or Pinecone (cloud)

**Recommendation**: Weaviate (free, self-hosted, good for hackathon)

### Implementation

**File**: `backend/database/vector_db_client.py`

```python
import weaviate
from typing import List, Dict, Any, Optional
import numpy as np

class VectorDBClient:
    """
    Vector database client for storing embeddings and fast similarity search.
    
    Uses Weaviate for vector storage and retrieval.
    """
    
    def __init__(self, url: str = "http://localhost:8080"):
        """
        Initialize Weaviate client.
        
        Args:
            url: Weaviate server URL
        """
        self.client = weaviate.Client(url)
        self._create_schema()
    
    def _create_schema(self):
        """Create Weaviate schema for 4 profile types."""
        # Define schema for each profile type
        # Candidate, Team, Interviewer, Position
        pass
    
    def store_candidate(self, candidate_id: str, embedding: np.ndarray, metadata: Dict):
        """Store candidate embedding with metadata."""
        pass
    
    def store_team(self, team_id: str, embedding: np.ndarray, metadata: Dict):
        """Store team embedding with metadata."""
        pass
    
    def store_interviewer(self, interviewer_id: str, embedding: np.ndarray, metadata: Dict):
        """Store interviewer embedding with metadata."""
        pass
    
    def store_position(self, position_id: str, embedding: np.ndarray, metadata: Dict):
        """Store position embedding with metadata."""
        pass
    
    def search_similar_candidates(self, query_embedding: np.ndarray, top_k: int = 50) -> List[Dict]:
        """Search for similar candidates."""
        pass
    
    def search_similar_teams(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict]:
        """Search for similar teams."""
        pass
    
    def search_similar_interviewers(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Dict]:
        """Search for similar interviewers."""
        pass
    
    def search_similar_positions(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict]:
        """Search for similar positions."""
        pass
```

### Docker Setup

Add to `docker-compose.yml`:
```yaml
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=none
      - ENABLE_MODULES=text2vec-openai,text2vec-cohere,text2vec-huggingface
    volumes:
      - weaviate_data:/var/lib/weaviate
```

### Dependencies

Add to `requirements-vin.txt`:
```
weaviate-client>=3.24.0
```

---

## Component 3: Knowledge Graph Abstraction (Vin - 1-2 hours)

### Implementation

**File**: `backend/database/knowledge_graph.py`

```python
from typing import Dict, List, Any, Optional
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings.recruiting_embedder import RecruitingKnowledgeGraphEmbedder

class KnowledgeGraph:
    """
    Knowledge graph abstraction for recruiting domain.
    
    Handles 4 profile types: Candidates, Teams, Interviewers, Positions
    Uses vector DB for embeddings, lightweight store for metadata.
    """
    
    def __init__(self, vector_db: Optional[VectorDBClient] = None, 
                 embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None):
        self.vector_db = vector_db or VectorDBClient()
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.metadata_store = {}  # Lightweight in-memory (or PostgreSQL)
    
    # Candidate methods
    def add_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Add candidate to knowledge graph."""
        # Generate embedding
        embedding = self.embedder.embed_candidate(candidate_data)
        
        # Store in vector DB
        self.vector_db.store_candidate(
            candidate_data['id'],
            embedding,
            candidate_data
        )
        
        # Store metadata
        self.metadata_store[f"candidate:{candidate_data['id']}"] = candidate_data
        
        return candidate_data['id']
    
    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get candidate from knowledge graph."""
        return self.metadata_store.get(f"candidate:{candidate_id}")
    
    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates."""
        return [v for k, v in self.metadata_store.items() if k.startswith("candidate:")]
    
    # Team methods
    def add_team(self, team_data: Dict[str, Any]) -> str:
        """Add team to knowledge graph."""
        embedding = self.embedder.embed_team(team_data)
        self.vector_db.store_team(team_data['id'], embedding, team_data)
        self.metadata_store[f"team:{team_data['id']}"] = team_data
        return team_data['id']
    
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team from knowledge graph."""
        return self.metadata_store.get(f"team:{team_id}")
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all teams."""
        return [v for k, v in self.metadata_store.items() if k.startswith("team:")]
    
    def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all interviewers in a team."""
        team = self.get_team(team_id)
        if not team:
            return []
        member_ids = team.get('member_ids', [])
        return [self.get_interviewer(id) for id in member_ids if self.get_interviewer(id)]
    
    # Interviewer methods
    def add_interviewer(self, interviewer_data: Dict[str, Any]) -> str:
        """Add interviewer to knowledge graph."""
        embedding = self.embedder.embed_interviewer(interviewer_data)
        self.vector_db.store_interviewer(interviewer_data['id'], embedding, interviewer_data)
        self.metadata_store[f"interviewer:{interviewer_data['id']}"] = interviewer_data
        return interviewer_data['id']
    
    def get_interviewer(self, interviewer_id: str) -> Optional[Dict[str, Any]]:
        """Get interviewer from knowledge graph."""
        return self.metadata_store.get(f"interviewer:{interviewer_id}")
    
    def get_all_interviewers(self) -> List[Dict[str, Any]]:
        """Get all interviewers."""
        return [v for k, v in self.metadata_store.items() if k.startswith("interviewer:")]
    
    # Position methods
    def add_position(self, position_data: Dict[str, Any]) -> str:
        """Add position to knowledge graph."""
        embedding = self.embedder.embed_position(position_data)
        self.vector_db.store_position(position_data['id'], embedding, position_data)
        self.metadata_store[f"position:{position_data['id']}"] = position_data
        return position_data['id']
    
    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position from knowledge graph."""
        return self.metadata_store.get(f"position:{position_id}")
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        return [v for k, v in self.metadata_store.items() if k.startswith("position:")]
    
    # Update methods
    def update_candidate(self, candidate_id: str, new_data: Dict[str, Any]):
        """Update candidate in knowledge graph."""
        existing = self.get_candidate(candidate_id)
        if existing:
            updated = {**existing, **new_data, 'updated_at': datetime.now()}
            # Re-embed if key fields changed
            if self._needs_reembedding(existing, updated):
                embedding = self.embedder.embed_candidate(updated)
                self.vector_db.store_candidate(candidate_id, embedding, updated)
            self.metadata_store[f"candidate:{candidate_id}"] = updated
    
    def _needs_reembedding(self, old: Dict, new: Dict) -> bool:
        """Check if profile needs re-embedding."""
        key_fields = ['skills', 'experience', 'education', 'projects']
        return any(old.get(f) != new.get(f) for f in key_fields)
```

---

## Component 4: Automated Phone Screening (Vin + Ishaan - 6-8 hours)

### Vin's Part: Decision Engine (3-4 hours)

**File**: `backend/interviews/phone_screen_engine.py`

```python
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.embeddings.recruiting_embedder import RecruitingKnowledgeGraphEmbedder
from backend.database.knowledge_graph import KnowledgeGraph

class PhoneScreenDecisionEngine:
    """
    Decision engine for phone screen pass/fail.
    
    Uses bandit algorithm (warm-started from embeddings) to make decisions.
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.embedder = RecruitingKnowledgeGraphEmbedder()
        self.bandit = GraphWarmStartedFGTS()
    
    def make_decision(self, candidate_id: str, position_id: str, 
                     extracted_info: Dict) -> Dict:
        """
        Make pass/fail decision based on phone screen.
        
        Args:
            candidate_id: Candidate ID
            position_id: Position ID
            extracted_info: Information extracted from phone screen
        
        Returns:
            Decision dictionary with pass/fail, confidence, reasoning
        """
        # Get candidate and position
        candidate = self.kg.get_candidate(candidate_id)
        position = self.kg.get_position(position_id)
        
        # Generate embeddings
        candidate_emb = self.embedder.embed_candidate(candidate)
        position_emb = self.embedder.embed_position(position)
        
        # Compute similarity
        similarity = cosine_similarity(candidate_emb, position_emb)
        
        # Use bandit to make decision (warm-started from similarity)
        # Initialize bandit with similarity as prior
        self.bandit.initialize_from_embeddings(
            [candidate],
            position_emb
        )
        
        # Make decision based on:
        # - Embedding similarity
        # - Extracted info quality
        # - Must-have requirements check
        decision = self._evaluate_candidate(
            candidate, position, extracted_info, similarity
        )
        
        return decision
    
    def _evaluate_candidate(self, candidate, position, extracted_info, similarity):
        """Evaluate candidate and make decision."""
        # Check must-haves
        must_haves = position.get('must_haves', [])
        candidate_skills = candidate.get('skills', [])
        
        missing_must_haves = [mh for mh in must_haves if mh not in candidate_skills]
        
        # Decision logic
        if missing_must_haves:
            return {
                "passed": False,
                "confidence": 0.9,
                "reasoning": f"Missing must-have skills: {missing_must_haves}",
                "similarity": similarity
            }
        
        # Use similarity + extracted info
        if similarity > 0.7 and extracted_info.get('motivation_score', 0) > 0.6:
            return {
                "passed": True,
                "confidence": similarity * 0.8,
                "reasoning": "High similarity and strong motivation",
                "similarity": similarity
            }
        
        # Borderline cases
        if similarity > 0.5:
            return {
                "passed": True,
                "confidence": similarity * 0.6,
                "reasoning": "Moderate similarity, proceed to next stage",
                "similarity": similarity
            }
        
        return {
            "passed": False,
            "confidence": 1 - similarity,
            "reasoning": "Low similarity to position requirements",
            "similarity": similarity
        }
```

### Ishaan's Part: Conversation Interface (3-4 hours)

**File**: `backend/interviews/phone_screen_interviewer.py`

```python
from backend.integrations.grok_api import GrokAPIClient
from backend.database.knowledge_graph import KnowledgeGraph

class PhoneScreenInterviewer:
    """
    AI-powered phone screen interviewer (like Anthropic Interviewer).
    
    Conducts conversation, extracts information, makes decision.
    """
    
    def __init__(self, kg: KnowledgeGraph, grok_client: GrokAPIClient):
        self.kg = kg
        self.grok = grok_client
        self.decision_engine = PhoneScreenDecisionEngine(kg)
    
    async def conduct_phone_screen(self, candidate_id: str, position_id: str) -> Dict:
        """
        Conduct automated phone screen.
        
        Args:
            candidate_id: Candidate ID
            position_id: Position ID
        
        Returns:
            Phone screen result with decision
        """
        # Get profiles
        candidate = self.kg.get_candidate(candidate_id)
        position = self.kg.get_position(position_id)
        
        # Generate interview plan
        interview_plan = await self._generate_interview_plan(candidate, position)
        
        # Conduct conversation
        conversation = await self._conduct_conversation(interview_plan)
        
        # Extract information
        extracted_info = await self._extract_information(conversation, candidate, position)
        
        # Make decision
        decision = self.decision_engine.make_decision(
            candidate_id, position_id, extracted_info
        )
        
        # Update knowledge graph
        self.kg.update_candidate(candidate_id, {
            "phone_screen_result": decision,
            "phone_screen_conversation": conversation,
            "extracted_info": extracted_info
        })
        
        return {
            "candidate_id": candidate_id,
            "position_id": position_id,
            "conversation": conversation,
            "extracted_info": extracted_info,
            "decision": decision
        }
    
    async def _generate_interview_plan(self, candidate, position):
        """Generate interview questions based on candidate and position."""
        prompt = f"""
        Generate phone screen interview plan for:
        
        Candidate: {candidate.get('name', 'Unknown')}
        Skills: {', '.join(candidate.get('skills', []))}
        
        Position: {position.get('title', 'Unknown')}
        Requirements: {', '.join(position.get('requirements', []))}
        Must-haves: {', '.join(position.get('must_haves', []))}
        
        Generate 5-7 questions to:
        1. Verify technical skills
        2. Assess experience depth
        3. Understand motivation
        4. Check cultural fit
        5. Identify any gaps
        
        Return as JSON with questions and focus areas.
        """
        
        response = await self.grok._make_chat_request(prompt)
        return self._parse_interview_plan(response)
    
    async def _conduct_conversation(self, interview_plan):
        """Conduct conversation following interview plan."""
        # Use Grok to conduct conversation
        # Store conversation history
        conversation = []
        
        for question in interview_plan['questions']:
            # Ask question
            # Get response (simulated or real)
            # Store in conversation
            pass
        
        return conversation
    
    async def _extract_information(self, conversation, candidate, position):
        """Extract key information from conversation."""
        prompt = f"""
        Extract key information from phone screen conversation:
        
        Conversation: {conversation}
        Candidate Profile: {candidate}
        Position Requirements: {position}
        
        Extract:
        1. Skills verified (list)
        2. Experience depth (score 0-1)
        3. Motivation level (score 0-1)
        4. Cultural fit (score 0-1)
        5. Any concerns or gaps
        
        Return as JSON.
        """
        
        response = await self.grok._make_chat_request(prompt)
        return self._parse_extracted_info(response)
```

---

## Component 5: Team/Interviewer Matching (Vin - 4-6 hours)

### Implementation

**File**: `backend/matching/team_matcher.py`

```python
from backend.database.knowledge_graph import KnowledgeGraph
from backend.embeddings.recruiting_embedder import RecruitingKnowledgeGraphEmbedder
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from typing import Dict, List, Tuple
import numpy as np

class TeamPersonMatcher:
    """
    Match candidates to teams and specific interviewers.
    
    Uses vector similarity + bandit algorithm for optimal matching.
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.embedder = RecruitingKnowledgeGraphEmbedder()
    
    def match_to_team(self, candidate_id: str) -> Dict:
        """
        Find which team should interview this candidate.
        
        Args:
            candidate_id: Candidate ID
        
        Returns:
            Match result with team_id, score, reasoning
        """
        candidate = self.kg.get_candidate(candidate_id)
        candidate_emb = self.embedder.embed_candidate(candidate)
        
        # Get all teams
        teams = self.kg.get_all_teams()
        
        # Compute match scores
        matches = []
        for team in teams:
            team_emb = self.embedder.embed_team(team)
            similarity = cosine_similarity(candidate_emb, team_emb)
            
            # Additional factors
            needs_match = self._check_needs_match(candidate, team)
            expertise_match = self._check_expertise_match(candidate, team)
            
            score = similarity * 0.6 + needs_match * 0.3 + expertise_match * 0.1
            
            matches.append({
                "team_id": team['id'],
                "team": team,
                "score": score,
                "similarity": similarity,
                "needs_match": needs_match,
                "expertise_match": expertise_match
            })
        
        # Use bandit to select (warm-started from scores)
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(
            [m['team'] for m in matches],
            candidate_emb
        )
        
        # Select best match
        selected_idx = bandit.select_candidate()
        best_match = matches[selected_idx]
        
        return {
            "candidate_id": candidate_id,
            "team_id": best_match['team_id'],
            "team": best_match['team'],
            "match_score": best_match['score'],
            "similarity": best_match['similarity'],
            "reasoning": self._generate_reasoning(candidate, best_match['team'], best_match)
        }
    
    def match_to_person(self, candidate_id: str, team_id: str) -> Dict:
        """
        Find which person on team should interview candidate.
        
        Args:
            candidate_id: Candidate ID
            team_id: Team ID
        
        Returns:
            Match result with interviewer_id, score, reasoning
        """
        candidate = self.kg.get_candidate(candidate_id)
        team = self.kg.get_team(team_id)
        candidate_emb = self.embedder.embed_candidate(candidate)
        
        # Get team members (interviewers)
        interviewers = self.kg.get_team_members(team_id)
        
        if not interviewers:
            return {"error": "No interviewers found for team"}
        
        # Compute match scores
        matches = []
        for interviewer in interviewers:
            interviewer_emb = self.embedder.embed_interviewer(interviewer)
            similarity = cosine_similarity(candidate_emb, interviewer_emb)
            
            # Additional factors
            expertise_match = self._check_expertise_match(candidate, interviewer)
            success_rate = interviewer.get('success_rate', 0.5)
            cluster_success = interviewer.get('cluster_success_rates', {}).get(
                candidate.get('ability_cluster'), 0.5
            )
            
            score = (
                similarity * 0.4 +
                expertise_match * 0.3 +
                success_rate * 0.2 +
                cluster_success * 0.1
            )
            
            matches.append({
                "interviewer_id": interviewer['id'],
                "interviewer": interviewer,
                "score": score,
                "similarity": similarity,
                "expertise_match": expertise_match,
                "success_rate": success_rate
            })
        
        # Use bandit to select
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(
            [m['interviewer'] for m in matches],
            candidate_emb
        )
        
        selected_idx = bandit.select_candidate()
        best_match = matches[selected_idx]
        
        return {
            "candidate_id": candidate_id,
            "team_id": team_id,
            "interviewer_id": best_match['interviewer_id'],
            "interviewer": best_match['interviewer'],
            "match_score": best_match['score'],
            "similarity": best_match['similarity'],
            "reasoning": self._generate_person_reasoning(candidate, best_match['interviewer'], best_match)
        }
    
    def _check_needs_match(self, candidate, team) -> float:
        """Check how well candidate matches team needs."""
        team_needs = set(team.get('needs', []))
        candidate_skills = set(candidate.get('skills', []))
        
        if not team_needs:
            return 0.5  # Neutral if no needs specified
        
        overlap = len(team_needs.intersection(candidate_skills))
        return overlap / len(team_needs)
    
    def _check_expertise_match(self, candidate, team_or_interviewer) -> float:
        """Check expertise match."""
        candidate_domains = set(candidate.get('domains', []))
        other_domains = set(team_or_interviewer.get('expertise', []))
        
        if not other_domains:
            return 0.5
        
        overlap = len(candidate_domains.intersection(other_domains))
        return overlap / len(other_domains)
    
    def _generate_reasoning(self, candidate, team, match_data) -> str:
        """Generate human-readable reasoning for team match."""
        return f"""
        Candidate matches team '{team['name']}' because:
        - Similarity score: {match_data['similarity']:.2%}
        - Needs match: {match_data['needs_match']:.2%} of team needs met
        - Expertise match: {match_data['expertise_match']:.2%} domain overlap
        - Team is hiring for: {', '.join(team.get('needs', [])[:3])}
        """
    
    def _generate_person_reasoning(self, candidate, interviewer, match_data) -> str:
        """Generate human-readable reasoning for person match."""
        return f"""
        {interviewer['name']} should interview this candidate because:
        - Similarity score: {match_data['similarity']:.2%}
        - Expertise match: {match_data['expertise_match']:.2%}
        - Interview success rate: {match_data['success_rate']:.1%}
        - Specializes in: {', '.join(interviewer.get('expertise', [])[:3])}
        """
```

### Interview Prep Generator

**File**: `backend/matching/interview_prep_generator.py`

```python
from backend.database.knowledge_graph import KnowledgeGraph
from backend.integrations.grok_api import GrokAPIClient

class InterviewPrepGenerator:
    """
    Generate interview prep materials for interviewer.
    
    Creates profile overview, questions, and focus areas.
    """
    
    def __init__(self, kg: KnowledgeGraph, grok_client: GrokAPIClient):
        self.kg = kg
        self.grok = grok_client
    
    async def generate_prep(self, candidate_id: str, team_id: str, 
                           interviewer_id: str) -> Dict:
        """
        Generate interview prep materials.
        
        Args:
            candidate_id: Candidate ID
            team_id: Team ID
            interviewer_id: Interviewer ID
        
        Returns:
            Interview prep with profile overview, questions, focus areas
        """
        candidate = self.kg.get_candidate(candidate_id)
        team = self.kg.get_team(team_id)
        interviewer = self.kg.get_interviewer(interviewer_id)
        position = self.kg.get_position(candidate.get('applied_to_positions', [None])[0])
        
        # Generate profile overview
        profile_overview = await self._generate_profile_overview(
            candidate, position, team
        )
        
        # Generate questions
        questions = await self._generate_questions(
            candidate, position, interviewer
        )
        
        # Generate focus areas
        focus_areas = await self._generate_focus_areas(
            candidate, position, interviewer
        )
        
        return {
            "candidate_id": candidate_id,
            "interviewer_id": interviewer_id,
            "profile_overview": profile_overview,
            "questions": questions,
            "focus_areas": focus_areas,
            "candidate_summary": self._summarize_candidate(candidate),
            "position_summary": self._summarize_position(position),
            "team_context": self._summarize_team(team)
        }
    
    async def _generate_profile_overview(self, candidate, position, team):
        """Generate candidate profile overview for interviewer."""
        prompt = f"""
        Generate interview prep profile overview:
        
        Candidate: {candidate.get('name', 'Unknown')}
        Skills: {', '.join(candidate.get('skills', []))}
        Experience: {candidate.get('experience_years', 0)} years
        Education: {', '.join(candidate.get('education', []))}
        
        Position: {position.get('title', 'Unknown')}
        Requirements: {', '.join(position.get('requirements', []))}
        
        Team: {team.get('name', 'Unknown')}
        Team Needs: {', '.join(team.get('needs', []))}
        
        Create a concise profile overview (2-3 paragraphs) highlighting:
        1. Candidate's key strengths
        2. How they match position requirements
        3. Areas to probe during interview
        4. Team fit considerations
        """
        
        response = await self.grok._make_chat_request(prompt)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def _generate_questions(self, candidate, position, interviewer):
        """Generate interview questions."""
        prompt = f"""
        Generate technical interview questions for:
        
        Candidate Skills: {', '.join(candidate.get('skills', []))}
        Position Requirements: {', '.join(position.get('requirements', []))}
        Interviewer Expertise: {', '.join(interviewer.get('expertise', []))}
        
        Generate 5-7 questions that:
        1. Verify technical skills
        2. Assess depth of knowledge
        3. Probe areas of uncertainty
        4. Match interviewer's expertise
        
        Return as JSON array of questions with:
        - question: The question text
        - focus_area: What it's testing
        - difficulty: Easy/Medium/Hard
        """
        
        response = await self.grok._make_chat_request(prompt)
        return self._parse_questions(response)
    
    async def _generate_focus_areas(self, candidate, position, interviewer):
        """Generate focus areas for interviewer."""
        prompt = f"""
        Generate interview focus areas:
        
        Candidate: {candidate}
        Position: {position}
        Interviewer: {interviewer}
        
        Identify 3-5 areas to focus on during interview:
        1. Skills to verify deeply
        2. Experience to probe
        3. Gaps to explore
        4. Team fit assessment
        
        Return as JSON array.
        """
        
        response = await self.grok._make_chat_request(prompt)
        return self._parse_focus_areas(response)
```

---

## Component 6: Outbound Info Gathering (Ishaan - 8-10 hours)

### Schema for Outbound Data

Ishaan must populate knowledge graph with this exact schema:

**File**: `backend/orchestration/outbound_gatherer.py`

```python
class OutboundGatherer:
    """
    Lightweight outbound info gathering from 4 sources.
    
    Sources: GitHub, X API, arXiv, LinkedIn
    Populates knowledge graph with candidate profiles.
    """
    
    async def gather_from_github(self, github_handle: str) -> Dict:
        """
        Gather candidate info from GitHub.
        
        Returns candidate profile matching exact schema:
        {
            "id": f"github_{github_handle}",
            "github_handle": github_handle,
            "skills": [...],  # From repos, languages
            "experience": [...],  # From bio, repos
            "projects": [...],  # From repos
            "github_stats": {...},
            ...
        }
        """
        pass
    
    async def gather_from_x(self, x_handle: str) -> Dict:
        """
        Gather candidate info from X (Twitter).
        
        Extract:
        - GitHub links from posts
        - LinkedIn mentions
        - arXiv paper links
        - Project announcements
        - Technical content
        
        Returns candidate profile matching exact schema.
        """
        pass
    
    async def gather_from_arxiv(self, arxiv_id: str) -> Dict:
        """
        Gather candidate info from arXiv.
        
        Extract:
        - Author info
        - Research areas
        - Paper topics
        - Co-authors
        
        Returns candidate profile matching exact schema.
        """
        pass
    
    async def gather_from_linkedin(self, linkedin_url: str) -> Dict:
        """
        Gather candidate info from LinkedIn.
        
        Extract:
        - Skills
        - Experience
        - Education
        - Projects
        
        Returns candidate profile matching exact schema.
        """
        pass
```

### Exact Schema Mapping

**For Ishaan**: Use this exact structure when populating knowledge graph:

```python
# Candidate profile structure (MUST MATCH)
candidate_profile = {
    "id": "unique_id",  # Format: "github_{handle}" or "x_{handle}"
    "github_handle": str or None,
    "x_handle": str or None,
    "linkedin_url": str or None,
    "arxiv_ids": List[str],
    
    # Core data (REQUIRED)
    "skills": List[str],  # Extract from all sources
    "experience": List[str],  # Work experience descriptions
    "experience_years": int,  # Calculate from experience
    "domains": List[str],  # Infer from skills/experience
    "education": List[str],  # From LinkedIn, GitHub bio
    "projects": List[Dict],  # From GitHub repos, X posts
    "expertise_level": str,  # Infer: "Junior", "Mid", "Senior", "Staff"
    
    # Source-specific data
    "repos": List[Dict],  # GitHub repos
    "papers": List[Dict],  # arXiv papers
    "posts": List[Dict],  # X posts (technical only)
    "github_stats": Dict,  # Commits, stars, etc.
    
    # Metadata
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "source": "outbound"
}
```

---

## File Cleanup Plan (Vin)

### Files to Remove

1. **Neo4j files** (replaced by vector DB):
   - `backend/database/neo4j_client.py` ❌
   - `backend/database/neo4j_schema.py` ❌
   - `backend/database/neo4j_queries.py` ❌
   - `backend/database/neo4j_graph_storage.py` ❌
   - `backend/database/neo4j_bandit_state.py` ❌
   - `tests/test_neo4j_*.py` ❌

2. **Old pipeline** (replaced by inbound automation):
   - `backend/orchestration/pipeline.py` ❌ (old outbound pipeline)
   - `backend/orchestration/candidate_sourcer.py` ❌ (old sourcing, Ishaan will rebuild)

3. **Old graph similarity** (replaced by vector similarity):
   - `backend/graph/graph_similarity.py` ❌ (kNN on graphs, not needed)
   - But keep `graph_builder.py` for in-memory graph construction (papers use this)

4. **Demo files** (not needed for new focus):
   - `backend/demo/dashboard.py` ❌ (or repurpose)
   - `backend/demo/metrics.py` ❌ (or repurpose)

5. **Old simulator** (not needed):
   - `backend/simulator/x_dm_simulator.py` ❌ (or repurpose for phone screen)

### Files to Keep and How They Contribute

1. **Algorithm files** (core innovation - KEEP):
   - `backend/algorithms/fgts_bandit.py` ✅
     - **Contribution**: Core graph-warm-started FG-TS algorithm
     - **Change**: Modify `initialize_from_graph()` → `initialize_from_embeddings()`
     - **Why keep**: This is the innovation, just change similarity source
   
   - `backend/algorithms/bandit_utils.py` ✅
     - **Contribution**: Helper functions (confidence intervals, etc.)
     - **Why keep**: Still useful for bandit operations
   
   - `backend/algorithms/learning_tracker.py` ✅
     - **Contribution**: Track learning metrics
     - **Why keep**: Still useful for tracking bandit performance
   
   - `backend/algorithms/learning_data_export.py` ✅
     - **Contribution**: Export learning data
     - **Why keep**: Still useful for metrics

2. **Graph builder** (papers use this - KEEP):
   - `backend/graph/graph_builder.py` ✅
     - **Contribution**: Builds in-memory graphs (like papers do)
     - **Why keep**: Papers use NetworkX graphs for computation
     - **Note**: We don't store graphs, but use them for computation
     - **Change**: Keep as-is, use for in-memory similarity if needed

3. **Integrations** (KEEP):
   - `backend/integrations/grok_api.py` ✅
     - **Contribution**: Entity extraction, chat completions
     - **Why keep**: Still needed for phone screen, interview prep
   
   - `backend/integrations/github_api.py` ✅
     - **Contribution**: GitHub API client
     - **Why keep**: Ishaan will use for outbound
   
   - `backend/integrations/x_api.py` ✅
     - **Contribution**: X API client (currently stub)
     - **Why keep**: Ishaan will implement for outbound
   
   - `backend/integrations/api_utils.py` ✅
     - **Contribution**: Shared utilities (retry, error handling)
     - **Why keep**: Still useful

4. **API** (KEEP but modify):
   - `backend/api/main.py` ✅
     - **Contribution**: FastAPI app
     - **Change**: Update routes for inbound endpoints
   
   - `backend/api/models.py` ✅
     - **Contribution**: Pydantic models
     - **Change**: Add models for phone screen, matching, etc.
   
   - `backend/api/routes.py` ✅
     - **Contribution**: API endpoints
     - **Change**: Add inbound endpoints, remove old sourcing endpoint

5. **Agent** (KEEP but repurpose):
   - `backend/orchestration/recruiter_agent.py` ✅
     - **Contribution**: Agent framework
     - **Change**: Repurpose for phone screen conversation

### New Files to Create

**Vin**:
- `backend/embeddings/recruiting_embedder.py` (NEW)
- `backend/database/vector_db_client.py` (NEW)
- `backend/database/knowledge_graph.py` (NEW)
- `backend/matching/team_matcher.py` (NEW)
- `backend/matching/interview_prep_generator.py` (NEW)
- `backend/interviews/phone_screen_engine.py` (NEW)

**Ishaan**:
- `backend/interviews/phone_screen_interviewer.py` (NEW)
- `backend/orchestration/outbound_gatherer.py` (NEW)
- `backend/integrations/arxiv_api.py` (NEW)
- `backend/integrations/linkedin_api.py` (NEW)

---

## Timeline

### Phase 1: Foundation (Vin - 6-8 hours)
- Specialized embedder (2-3 hours)
- Vector DB storage (2-3 hours)
- Knowledge graph (1-2 hours)
- Cleanup (1 hour)

### Phase 2: Phone Screen (Vin + Ishaan - 6-8 hours)
- Decision engine (Vin - 3-4 hours)
- Conversation interface (Ishaan - 3-4 hours)

### Phase 3: Matching (Vin - 4-6 hours)
- Team/person matcher (3-4 hours)
- Interview prep generator (1-2 hours)

### Phase 4: Outbound (Ishaan - 8-10 hours)
- 4 source integrations (GitHub, X, arXiv, LinkedIn)
- Schema-compliant data population

### Phase 5: Talent Clustering (Vin - 3 hours) - CRITICAL
- K-means clustering on candidate embeddings
- Group candidates by ability clusters
- Update interviewer cluster_success_rates
- **Why Critical**: Judge 1 explicitly requested "group talent abilities"

### Phase 6: Feedback Loop Integration (Vin - 3 hours) - CRITICAL
- Connect recruiter feedback → bandit updates
- Integrate learning_tracker with feedback
- Remove TODOs from recruiter_agent
- **Why Critical**: Core hackathon requirement "self-improving agent"

### Phase 7: Online Learning Demo (Vin - 2 hours) - CRITICAL
- Demonstrate warm-start vs cold-start learning
- Generate learning curves
- Show 3x faster learning improvement
- **Why Critical**: Judges need to SEE the system learning

**Total**: 32-40 hours (updated with critical phases)

---

## Success Criteria

1. ✅ Specialized embedder generates embeddings for all 4 profile types
2. ✅ Vector DB stores and retrieves embeddings efficiently
3. ✅ Knowledge graph manages all 4 profile types
4. ✅ Phone screen conducts quality conversations and makes decisions
5. ✅ Team/person matching works with profile overview + prep
6. ✅ Outbound populates knowledge graph with correct schema

---

## Next Steps

1. Vin: Start with embedder + vector DB + knowledge graph
2. Vin: Clean up old files
3. Vin: Build phone screen decision engine
4. Vin: Build matching system
5. Ishaan: Wait for schema, then build outbound
6. Ishaan: Build phone screen interface
7. Integration: Connect all components

