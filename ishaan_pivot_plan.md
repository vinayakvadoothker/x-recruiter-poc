# Ishaan's Pivot Plan: Phone Screen Interface + Outbound Gathering

## Your Role: Application Layer + Outbound Data Gathering

**Focus**: Build phone screen conversation interface, outbound info gathering from 4 sources, and ensure data matches exact schema.

**Timeline**: 18-28 hours total

**Important**: Wait for Vin to complete knowledge graph schema before starting outbound work. Use mock data in the meantime.

---

## Hour-by-Hour Schedule

### Hours 1-8: WAITING
- **Blocked**: Waiting for Vin to complete Knowledge Graph (Phase 4)
- **Can do**: Review API documentation, prepare for outbound work, set up API clients (stubs)

### Hours 9-11: GitHub Gathering
- **Hour 9**: Start after Vin completes Knowledge Graph (Hour 9)
- **Hour 9-10**: Implement `gather_from_github()` in outbound_gatherer.py, extract all required fields
- **Hour 10-11**: Match exact schema, write tests, test schema compliance

### Hours 11-14: X API Gathering
- **Hour 11-12**: Implement X API client (modify x_api.py), implement `gather_from_x()`
- **Hour 12-13**: Extract links (GitHub, LinkedIn, arXiv), extract technical content
- **Hour 13-14**: Match exact schema, write tests

### Hours 14-16: arXiv Gathering
- **Hour 14-15**: Create `backend/integrations/arxiv_api.py`, implement arXiv API client
- **Hour 15-16**: Implement `gather_from_arxiv()`, extract author/research data, match schema, write tests

### Hours 16-19: LinkedIn Gathering
- **Hour 16-17**: Create `backend/integrations/linkedin_api.py`, implement LinkedIn client (or scraping)
- **Hour 17-18**: Implement `gather_from_linkedin()`, extract profile data
- **Hour 18-19**: Match exact schema, write tests

### Hours 17-21: Phone Screen Interface (Parallel with LinkedIn)
- **Hour 17**: Start after Vin completes Decision Engine (Hour 17)
- **Hour 17-18**: Create `backend/interviews/phone_screen_interviewer.py`, implement conversation flow
- **Hour 18-19**: Implement question generation, implement information extraction
- **Hour 19-20**: Integrate with Vin's decision engine, write tests
- **Hour 20-21**: Test conversation quality, finalize phone screen interface

### Hours 19-22: Unified Gatherer
- **Hour 19-20**: Complete `outbound_gatherer.py`, implement data merging
- **Hour 20-21**: Implement schema validation, integrate with knowledge graph
- **Hour 21-22**: Write tests, test end-to-end gathering

### Hours 22-24: API Updates
- **Hour 22-23**: Update `backend/api/routes.py`, add inbound endpoints
- **Hour 23-24**: Update `backend/api/models.py`, write tests, test all endpoints

### Hours 24-28: Profile Input Interfaces
- **Hour 24-25**: Create `backend/orchestration/profile_creator.py`, implement team creation
- **Hour 25-26**: Implement interviewer creation, implement position creation
- **Hour 26-27**: Add API endpoints, add validation, write tests
- **Hour 27-28**: Test all input interfaces, finalize profile input system

---

## Phase 1: Phone Screen Interviewer Interface (3-4 hours)

### Task: Build AI-powered phone screen conversation (like Anthropic Interviewer)

**File**: `backend/interviews/phone_screen_interviewer.py` (NEW)

**Implementation**:
- Conduct real-time conversation with candidate
- Generate interview questions based on candidate + position
- Extract information from conversation
- Integrate with Vin's decision engine

**Key Methods**:
- `conduct_phone_screen(candidate_id, position_id)` → full phone screen
- `_generate_interview_plan(candidate, position)` → generate questions
- `_conduct_conversation(interview_plan)` → run conversation
- `_extract_information(conversation, candidate, position)` → extract key info

**Integration**:
- Uses `KnowledgeGraph` (from Vin) to get profiles
- Uses `GrokAPIClient` for conversation and extraction
- Uses `PhoneScreenDecisionEngine` (from Vin) for decision
- Updates knowledge graph with results

**Interface**:
- Conversation flow (like Anthropic Interviewer)
- Real-time question/answer
- Information extraction
- Decision display

**Testing**:
- `tests/test_phone_screen_interviewer.py` (NEW)
- Test conversation flow
- Test question generation
- Test information extraction
- Test decision integration

**Deliverable**: Production-quality phone screen interface ✅

---

## Phase 2: Outbound Info Gathering - GitHub (2 hours)

### Task: Gather candidate info from GitHub

**File**: `backend/orchestration/outbound_gatherer.py` (NEW - partial)

**Method**: `gather_from_github(github_handle: str) -> Dict`

**What to Extract**:
- Profile data (bio, location, company)
- Repositories (top repos, languages, stars)
- Skills (from repos, languages, topics)
- Experience (from bio, company, repos)
- Projects (from repos)
- GitHub stats (commits, stars, contributions)

**Exact Schema** (MUST MATCH):
```python
{
    "id": f"github_{github_handle}",
    "github_handle": github_handle,
    "x_handle": None,  # Will be filled from X source
    "linkedin_url": None,  # Will be filled from LinkedIn source
    "arxiv_ids": [],  # Will be filled from arXiv source
    
    # Core data (REQUIRED)
    "skills": List[str],  # From repos, languages, topics
    "experience": List[str],  # From bio, company, repos
    "experience_years": int,  # Calculate from account age, repos
    "domains": List[str],  # Infer from repos, languages
    "education": List[str],  # From bio (if mentioned)
    "projects": List[Dict],  # From repos
    "expertise_level": str,  # Infer: "Junior", "Mid", "Senior", "Staff"
    
    # Source-specific
    "repos": List[Dict],  # GitHub repos with metadata
    "github_stats": {
        "total_commits": int,
        "total_stars": int,
        "total_repos": int,
        "languages": Dict[str, int],  # Language -> line count
        "topics": List[str]
    },
    
    # Metadata
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "source": "outbound"
}
```

**Integration**:
- Uses existing `GitHubAPIClient` (already implemented)
- Extracts data from GitHub API responses
- Formats to exact schema
- Returns candidate profile

**Testing**:
- Test with real GitHub handles
- Test with minimal profiles
- Test schema compliance
- Test data extraction accuracy

**Deliverable**: GitHub data gathering matching exact schema ✅

---

## Phase 3: Outbound Info Gathering - X API (2-3 hours)

### Task: Gather candidate info from X (Twitter)

**File**: `backend/integrations/x_api.py` (MODIFY - currently stub)

**Implementation**:
- Implement X API client (search, get profile, get posts)
- Extract from X posts:
  - GitHub links → extract GitHub handle
  - LinkedIn mentions → extract LinkedIn URL
  - arXiv paper links → extract arXiv IDs
  - Project announcements → extract project info
  - Technical content → extract skills/expertise

**Method**: `gather_from_x(x_handle: str) -> Dict`

**What to Extract**:
- Profile data (bio, location)
- GitHub links (from posts, bio)
- LinkedIn mentions (from posts, bio)
- arXiv links (from posts)
- Technical posts (skills, expertise)
- Project announcements

**Exact Schema** (MUST MATCH):
```python
{
    "id": f"x_{x_handle}",
    "github_handle": str or None,  # From extracted links
    "x_handle": x_handle,
    "linkedin_url": str or None,  # From extracted mentions
    "arxiv_ids": List[str],  # From extracted links
    
    # Core data
    "skills": List[str],  # From technical posts
    "experience": List[str],  # From bio, posts
    "experience_years": int,  # Infer from posts, bio
    "domains": List[str],  # From technical content
    "education": List[str],  # From bio (if mentioned)
    "projects": List[Dict],  # From project announcements
    "expertise_level": str,  # Infer from content
    
    # Source-specific
    "posts": List[Dict],  # Technical posts only
    "github_stats": {},  # Empty (will be filled from GitHub source)
    
    # Metadata
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "source": "outbound"
}
```

**X API Endpoints Needed**:
- Search users
- Get user profile
- Get user tweets/posts
- Search tweets (for technical content)

**Testing**:
- Test with real X handles
- Test link extraction
- Test schema compliance
- Test data merging (X + GitHub)

**Deliverable**: X API data gathering matching exact schema ✅

---

## Phase 4: Outbound Info Gathering - arXiv (2 hours)

### Task: Gather candidate info from arXiv

**File**: `backend/integrations/arxiv_api.py` (NEW)

**Implementation**:
- arXiv API client (public API, no auth needed)
- Extract from papers:
  - Author info
  - Research areas
  - Paper topics
  - Co-authors
  - Publication dates

**Method**: `gather_from_arxiv(arxiv_id: str) -> Dict`

**What to Extract**:
- Author information
- Research areas (from categories, keywords)
- Paper topics
- Skills (infer from research areas)
- Experience (from publication history)
- Domains (from research areas)

**Exact Schema** (MUST MATCH):
```python
{
    "id": f"arxiv_{arxiv_id}",
    "github_handle": None,  # Will be filled from other sources
    "x_handle": None,  # Will be filled from other sources
    "linkedin_url": None,  # Will be filled from other sources
    "arxiv_ids": [arxiv_id],
    
    # Core data
    "skills": List[str],  # Infer from research areas
    "experience": List[str],  # From publication history
    "experience_years": int,  # Calculate from first publication
    "domains": List[str],  # From research areas
    "education": List[str],  # Infer from affiliations
    "projects": List[Dict],  # From papers
    "expertise_level": str,  # Infer: "Junior", "Mid", "Senior", "Staff"
    
    # Source-specific
    "papers": List[Dict],  # Paper metadata
    "github_stats": {},  # Empty
    
    # Metadata
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "source": "outbound"
}
```

**arXiv API**:
- Endpoint: `http://export.arxiv.org/api/query`
- Public API (no auth)
- Search by author, ID, etc.

**Testing**:
- Test with real arXiv IDs
- Test author search
- Test schema compliance
- Test data extraction

**Deliverable**: arXiv data gathering matching exact schema ✅

---

## Phase 5: Outbound Info Gathering - LinkedIn (2-3 hours)

### Task: Gather candidate info from LinkedIn

**File**: `backend/integrations/linkedin_api.py` (NEW)

**Note**: LinkedIn API is restricted. Options:
1. Use LinkedIn scraping (if allowed)
2. Use LinkedIn profile URLs (manual entry)
3. Use LinkedIn data if available

**Method**: `gather_from_linkedin(linkedin_url: str) -> Dict`

**What to Extract** (if available):
- Skills
- Experience (jobs, years)
- Education
- Projects
- Certifications

**Exact Schema** (MUST MATCH):
```python
{
    "id": f"linkedin_{profile_id}",
    "github_handle": None,  # Will be filled from other sources
    "x_handle": None,  # Will be filled from other sources
    "linkedin_url": linkedin_url,
    "arxiv_ids": [],  # Will be filled from other sources
    
    # Core data
    "skills": List[str],  # From LinkedIn skills
    "experience": List[str],  # From work experience
    "experience_years": int,  # Calculate from experience
    "domains": List[str],  # Infer from experience
    "education": List[str],  # From education section
    "projects": List[Dict],  # From projects section
    "expertise_level": str,  # Infer from experience
    
    # Source-specific
    "github_stats": {},  # Empty
    
    # Metadata
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "source": "outbound"
}
```

**Implementation Options**:
- If LinkedIn API available: Use official API
- If scraping allowed: Use web scraping
- If manual: Accept profile URLs, extract what's possible

**Testing**:
- Test with real LinkedIn URLs (if possible)
- Test schema compliance
- Test data extraction

**Deliverable**: LinkedIn data gathering matching exact schema ✅

---

## Phase 6: Outbound Gatherer Integration (2-3 hours)

### Task: Integrate all 4 sources into unified gatherer

**File**: `backend/orchestration/outbound_gatherer.py` (COMPLETE)

**Implementation**:
- Main class: `OutboundGatherer`
- Methods for each source:
  - `gather_from_github(github_handle)`
  - `gather_from_x(x_handle)`
  - `gather_from_arxiv(arxiv_id)`
  - `gather_from_linkedin(linkedin_url)`
- Unified method: `gather_candidate(sources: Dict)` → merge all sources
- Schema validation: Ensure data matches exact schema
- Knowledge graph population: Add to Vin's knowledge graph

**Key Features**:
- Merge data from multiple sources
- Handle conflicts (prefer most recent/reliable source)
- Fill gaps (if GitHub has skills but X doesn't, use GitHub)
- Validate schema compliance
- Add to knowledge graph

**Integration**:
- Uses `KnowledgeGraph` (from Vin) to store profiles
- Uses all 4 API clients
- Validates schema before storing

**Testing**:
- Test gathering from single source
- Test gathering from multiple sources
- Test data merging
- Test schema validation
- Test knowledge graph population

**Deliverable**: Unified outbound gatherer populating knowledge graph ✅

---

## Phase 7: API Endpoints Update (1-2 hours)

### Task: Update API endpoints for inbound pipeline

**File**: `backend/api/routes.py` (MODIFY)

**New Endpoints**:
- `POST /inbound/phone_screen` - Start phone screen
- `GET /inbound/phone_screen/{candidate_id}` - Get phone screen results
- `POST /inbound/match` - Match candidate to team/person
- `GET /inbound/interview_prep/{candidate_id}` - Get interview prep
- `POST /outbound/gather` - Gather candidate info (for Ishaan's work)

**Update Models**:
- `backend/api/models.py` (MODIFY)
- Add models for phone screen, matching, interview prep

**Testing**:
- Test all new endpoints
- Test request/response models
- Test error handling

**Deliverable**: API endpoints for inbound pipeline ✅

---

## Exact Schema Reference

### For All Outbound Sources

**CRITICAL**: All sources must populate this exact structure:

```python
candidate_profile = {
    # IDs (REQUIRED)
    "id": str,  # Format: "github_{handle}" or "x_{handle}" or "arxiv_{id}" or "linkedin_{id}"
    "github_handle": str or None,
    "x_handle": str or None,
    "linkedin_url": str or None,
    "arxiv_ids": List[str],
    
    # Core Profile Data (REQUIRED)
    "skills": List[str],  # MUST be populated from at least one source
    "experience": List[str],  # Work experience descriptions
    "experience_years": int,  # Calculate from available data
    "domains": List[str],  # Infer from skills/experience
    "education": List[str],  # From bio, LinkedIn, etc.
    "projects": List[Dict],  # Project information
    "expertise_level": str,  # "Junior", "Mid", "Senior", "Staff"
    
    # Source-Specific Data
    "repos": List[Dict] or [],  # GitHub repos (if from GitHub)
    "papers": List[Dict] or [],  # arXiv papers (if from arXiv)
    "posts": List[Dict] or [],  # X posts (if from X)
    "github_stats": Dict or {},  # GitHub stats (if from GitHub)
    
    # Metadata (REQUIRED)
    "created_at": datetime,
    "updated_at": datetime,
    "source": "outbound"
}
```

### Schema Validation

**File**: `backend/orchestration/schema_validator.py` (NEW - optional helper)

Validate that gathered data matches exact schema before storing.

---

## Testing Strategy

### Unit Tests
- Each source gatherer (GitHub, X, arXiv, LinkedIn)
- Schema validation
- Data merging
- Knowledge graph population

### Integration Tests
- End-to-end: Gather from all sources → Merge → Store
- Knowledge graph integration
- API endpoint integration

### Edge Cases
- Missing data in sources
- Conflicting data between sources
- Invalid handles/URLs
- Empty profiles

---

## File Structure

```
backend/
├── interviews/
│   └── phone_screen_interviewer.py     # NEW - Conversation interface
├── orchestration/
│   ├── outbound_gatherer.py            # NEW - Unified gatherer
│   ├── schema_validator.py             # NEW - Schema validation (optional)
│   └── profile_creator.py              # NEW - Profile creation from user input
├── integrations/
│   ├── x_api.py                        # MODIFY - Implement (currently stub)
│   ├── arxiv_api.py                    # NEW - arXiv client
│   ├── linkedin_api.py                 # NEW - LinkedIn client
│   ├── github_api.py                   # KEEP - Already implemented
│   └── grok_api.py                     # KEEP
└── api/
    ├── routes.py                       # MODIFY - Add inbound endpoints
    └── models.py                       # MODIFY - Add new models
```

---

## Dependencies

**Add to `requirements.txt`**:
```
arxiv-api>=0.3.0  # For arXiv API
beautifulsoup4>=4.12.0  # For web scraping (if needed for LinkedIn)
requests>=2.31.0  # For API calls
```

---

## Checklist

### Phase 1: Phone Screen Interface
- [ ] Create `backend/interviews/phone_screen_interviewer.py`
- [ ] Implement conversation flow
- [ ] Implement question generation
- [ ] Implement information extraction
- [ ] Integrate with Vin's decision engine
- [ ] Write tests
- [ ] Test conversation quality

### Phase 2: GitHub Gathering
- [ ] Implement `gather_from_github()` in outbound_gatherer.py
- [ ] Extract all required fields
- [ ] Match exact schema
- [ ] Write tests
- [ ] Test schema compliance

### Phase 3: X API Gathering
- [ ] Implement X API client (modify x_api.py)
- [ ] Implement `gather_from_x()` in outbound_gatherer.py
- [ ] Extract links (GitHub, LinkedIn, arXiv)
- [ ] Extract technical content
- [ ] Match exact schema
- [ ] Write tests

### Phase 4: arXiv Gathering
- [ ] Create `backend/integrations/arxiv_api.py`
- [ ] Implement arXiv API client
- [ ] Implement `gather_from_arxiv()` in outbound_gatherer.py
- [ ] Extract author/research data
- [ ] Match exact schema
- [ ] Write tests

### Phase 5: LinkedIn Gathering
- [ ] Create `backend/integrations/linkedin_api.py`
- [ ] Implement LinkedIn client (or scraping)
- [ ] Implement `gather_from_linkedin()` in outbound_gatherer.py
- [ ] Extract profile data
- [ ] Match exact schema
- [ ] Write tests

### Phase 6: Unified Gatherer
- [ ] Complete `outbound_gatherer.py`
- [ ] Implement data merging
- [ ] Implement schema validation
- [ ] Integrate with knowledge graph
- [ ] Write tests
- [ ] Test end-to-end gathering

### Phase 7: API Updates
- [ ] Update `backend/api/routes.py`
- [ ] Add inbound endpoints
- [ ] Update `backend/api/models.py`
- [ ] Write tests
- [ ] Test all endpoints

### Phase 8: Profile Input Interfaces
- [ ] Create team profile input interface
- [ ] Create interviewer profile input interface
- [ ] Create position profile input interface
- [ ] Add API endpoints for profile creation
- [ ] Add validation for schema compliance
- [ ] Write tests
- [ ] Test all input interfaces

---

## Time Estimates

- Phone Screen Interface: 3-4 hours (Hours 17-21)
- GitHub Gathering: 2 hours (Hours 9-11)
- X API Gathering: 2-3 hours (Hours 11-14)
- arXiv Gathering: 2 hours (Hours 14-16)
- LinkedIn Gathering: 2-3 hours (Hours 16-19)
- Unified Gatherer: 2-3 hours (Hours 19-22)
- API Updates: 1-2 hours (Hours 22-24)
- Profile Input Interfaces: 4-6 hours (Hours 24-28)

**Total**: 18-28 hours

**Note**: See "Hour-by-Hour Schedule" section above for detailed breakdown. Hours 1-8 are waiting for Vin's Knowledge Graph.

---

## Success Criteria

✅ Phone screen interface conducts quality conversations  
✅ All 4 sources gather data matching exact schema  
✅ Data merging works correctly  
✅ Knowledge graph populated with correct data  
✅ API endpoints work for inbound pipeline  
✅ Teams can input their profile information  
✅ Interviewers can input their profile information  
✅ Positions can be created with full requirements  

---

## Important Notes

1. **Wait for Vin**: Don't start outbound until knowledge graph schema is finalized
2. **Exact Schema**: Must match schema exactly - no deviations
3. **Data Quality**: Extract as much as possible, but handle missing data gracefully
4. **Merging**: When multiple sources have same data, prefer most reliable source
5. **Testing**: Test with real data from all sources
6. **Error Handling**: Handle API failures, missing data, invalid inputs
7. **Profile Input**: Phase 8 enables real users to input their information (teams, interviewers, positions), not just sample datasets

---

## Phase 8: Profile Input Interfaces (4-6 hours)

### Task: Build interfaces for teams, interviewers, and positions to input their information

**Purpose**: Enable real users (teams, interviewers, recruiters) to input their information into the system, not just use sample datasets. This makes the system production-ready with real user data.

**Files**: 
- `backend/api/routes.py` (UPDATE - add profile creation endpoints)
- `backend/api/models.py` (UPDATE - add input models)
- `backend/orchestration/profile_creator.py` (NEW - profile creation logic)

### Implementation

#### 1. Team Profile Input Interface

**Endpoint**: `POST /api/teams/create`

**Request Model**:
```python
class TeamCreateRequest(BaseModel):
    name: str
    department: str
    needs: List[str]
    expertise: List[str]
    stack: List[str]
    domains: List[str]
    culture: str
    work_style: str
    hiring_priorities: List[str]
```

**Response**: Team profile with generated ID

**Validation**:
- All required fields present
- Schema compliance
- Valid data types

#### 2. Interviewer Profile Input Interface

**Endpoint**: `POST /api/interviewers/create`

**Request Model**:
```python
class InterviewerCreateRequest(BaseModel):
    name: str
    email: str
    team_id: str
    expertise: List[str]
    expertise_level: str
    specializations: List[str]
    interview_style: str
    evaluation_focus: List[str]
    question_style: str
    preferred_interview_types: List[str]
```

**Response**: Interviewer profile with generated ID

**Validation**:
- Team ID exists
- Email format valid
- Schema compliance

#### 3. Position Profile Input Interface

**Endpoint**: `POST /api/positions/create`

**Request Model**:
```python
class PositionCreateRequest(BaseModel):
    title: str
    team_id: str
    description: str
    requirements: List[str]
    must_haves: List[str]
    nice_to_haves: List[str]
    experience_level: str
    responsibilities: List[str]
    tech_stack: List[str]
    domains: List[str]
    team_context: str
    reporting_to: str
    collaboration: List[str]
    priority: str
```

**Response**: Position profile with generated ID

**Validation**:
- Team ID exists
- Must-haves not empty
- Schema compliance

### Profile Creator Service

**File**: `backend/orchestration/profile_creator.py`

```python
from backend.database.knowledge_graph import KnowledgeGraph
from typing import Dict, Any
from datetime import datetime

class ProfileCreator:
    """
    Service for creating profiles from user input.
    
    Validates input, generates IDs, and stores in knowledge graph.
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def create_team(self, team_data: Dict[str, Any]) -> str:
        """
        Create team profile from user input.
        
        Args:
            team_data: Team information from API request
        
        Returns:
            Team ID
        """
        # Generate ID
        team_id = f"team_{len(self.kg.get_all_teams()) + 1}"
        
        # Build full profile
        team_profile = {
            "id": team_id,
            "name": team_data["name"],
            "department": team_data["department"],
            "needs": team_data["needs"],
            "expertise": team_data["expertise"],
            "stack": team_data["stack"],
            "domains": team_data["domains"],
            "culture": team_data["culture"],
            "work_style": team_data["work_style"],
            "hiring_priorities": team_data.get("hiring_priorities", []),
            "member_count": 0,
            "member_ids": [],
            "open_positions": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Validate schema
        self._validate_team_profile(team_profile)
        
        # Store in knowledge graph
        return self.kg.add_team(team_profile)
    
    def create_interviewer(self, interviewer_data: Dict[str, Any]) -> str:
        """
        Create interviewer profile from user input.
        
        Args:
            interviewer_data: Interviewer information from API request
        
        Returns:
            Interviewer ID
        """
        # Validate team exists
        team = self.kg.get_team(interviewer_data["team_id"])
        if not team:
            raise ValueError(f"Team {interviewer_data['team_id']} not found")
        
        # Generate ID
        interviewer_id = f"interviewer_{len(self.kg.get_all_interviewers()) + 1}"
        
        # Build full profile
        interviewer_profile = {
            "id": interviewer_id,
            "name": interviewer_data["name"],
            "email": interviewer_data["email"],
            "team_id": interviewer_data["team_id"],
            "expertise": interviewer_data["expertise"],
            "expertise_level": interviewer_data["expertise_level"],
            "specializations": interviewer_data["specializations"],
            "interview_style": interviewer_data["interview_style"],
            "evaluation_focus": interviewer_data["evaluation_focus"],
            "question_style": interviewer_data["question_style"],
            "preferred_interview_types": interviewer_data["preferred_interview_types"],
            "total_interviews": 0,
            "successful_hires": 0,
            "success_rate": 0.0,
            "interview_history": [],
            "cluster_success_rates": {},
            "availability": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Validate schema
        self._validate_interviewer_profile(interviewer_profile)
        
        # Store in knowledge graph
        interviewer_id = self.kg.add_interviewer(interviewer_profile)
        
        # Update team's member list
        team["member_ids"].append(interviewer_id)
        team["member_count"] = len(team["member_ids"])
        self.kg.update_team(interviewer_data["team_id"], team)
        
        return interviewer_id
    
    def create_position(self, position_data: Dict[str, Any]) -> str:
        """
        Create position profile from user input.
        
        Args:
            position_data: Position information from API request
        
        Returns:
            Position ID
        """
        # Validate team exists
        team = self.kg.get_team(position_data["team_id"])
        if not team:
            raise ValueError(f"Team {position_data['team_id']} not found")
        
        # Generate ID
        position_id = f"position_{len(self.kg.get_all_positions()) + 1}"
        
        # Build full profile
        position_profile = {
            "id": position_id,
            "title": position_data["title"],
            "team_id": position_data["team_id"],
            "description": position_data["description"],
            "requirements": position_data["requirements"],
            "must_haves": position_data["must_haves"],
            "nice_to_haves": position_data.get("nice_to_haves", []),
            "experience_level": position_data["experience_level"],
            "responsibilities": position_data["responsibilities"],
            "tech_stack": position_data["tech_stack"],
            "domains": position_data["domains"],
            "team_context": position_data["team_context"],
            "reporting_to": position_data.get("reporting_to", ""),
            "collaboration": position_data.get("collaboration", []),
            "status": "open",
            "priority": position_data.get("priority", "medium"),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Validate schema
        self._validate_position_profile(position_profile)
        
        # Store in knowledge graph
        position_id = self.kg.add_position(position_profile)
        
        # Update team's open positions
        team["open_positions"].append(position_id)
        self.kg.update_team(position_data["team_id"], team)
        
        return position_id
    
    def _validate_team_profile(self, profile: Dict[str, Any]):
        """Validate team profile matches schema."""
        required_fields = ["id", "name", "department", "needs", "expertise", "stack", "domains"]
        for field in required_fields:
            if field not in profile:
                raise ValueError(f"Missing required field: {field}")
    
    def _validate_interviewer_profile(self, profile: Dict[str, Any]):
        """Validate interviewer profile matches schema."""
        required_fields = ["id", "name", "email", "team_id", "expertise", "expertise_level"]
        for field in required_fields:
            if field not in profile:
                raise ValueError(f"Missing required field: {field}")
    
    def _validate_position_profile(self, profile: Dict[str, Any]):
        """Validate position profile matches schema."""
        required_fields = ["id", "title", "team_id", "description", "requirements", "must_haves"]
        for field in required_fields:
            if field not in profile:
                raise ValueError(f"Missing required field: {field}")
```

### API Routes

**File**: `backend/api/routes.py` (UPDATE)

```python
from backend.orchestration.profile_creator import ProfileCreator
from backend.api.models import TeamCreateRequest, InterviewerCreateRequest, PositionCreateRequest

@router.post("/api/teams/create")
async def create_team(request: TeamCreateRequest):
    """
    Create a new team profile.
    
    Teams can input their information: name, department, needs, expertise, etc.
    """
    creator = ProfileCreator(kg)
    team_id = creator.create_team(request.dict())
    return {"team_id": team_id, "status": "created"}

@router.post("/api/interviewers/create")
async def create_interviewer(request: InterviewerCreateRequest):
    """
    Create a new interviewer profile.
    
    Interviewers can input their information: name, expertise, interview style, etc.
    """
    creator = ProfileCreator(kg)
    interviewer_id = creator.create_interviewer(request.dict())
    return {"interviewer_id": interviewer_id, "status": "created"}

@router.post("/api/positions/create")
async def create_position(request: PositionCreateRequest):
    """
    Create a new position profile.
    
    Recruiters/teams can input position requirements: title, requirements, must-haves, etc.
    """
    creator = ProfileCreator(kg)
    position_id = creator.create_position(request.dict())
    return {"position_id": position_id, "status": "created"}
```

### Testing

**File**: `tests/test_profile_creator.py` (NEW)

- Test team creation
- Test interviewer creation
- Test position creation
- Test validation (missing fields, invalid team_id, etc.)
- Test relationship updates (team member_ids, open_positions)
- Test schema compliance

### Usage Example

```python
# Team creates their profile
POST /api/teams/create
{
    "name": "LLM Inference Optimization",
    "department": "AI Infrastructure",
    "needs": ["CUDA expertise", "GPU optimization"],
    "expertise": ["CUDA", "GPU Computing"],
    "stack": ["CUDA", "C++", "PyTorch"],
    "domains": ["LLM Inference"],
    "culture": "Fast-paced, research-oriented",
    "work_style": "Hybrid",
    "hiring_priorities": ["Senior CUDA engineers"]
}

# Interviewer creates their profile
POST /api/interviewers/create
{
    "name": "Alex Chen",
    "email": "alex.chen@company.com",
    "team_id": "team_001",
    "expertise": ["CUDA", "GPU Optimization"],
    "expertise_level": "Senior",
    "specializations": ["CUDA kernel optimization"],
    "interview_style": "Technical deep-dive",
    "evaluation_focus": ["Technical depth", "Problem-solving"],
    "question_style": "Open-ended, scenario-based",
    "preferred_interview_types": ["Technical", "System Design"]
}

# Recruiter creates position
POST /api/positions/create
{
    "title": "Senior LLM Inference Optimization Engineer",
    "team_id": "team_001",
    "description": "We're looking for a senior engineer...",
    "requirements": ["5+ years CUDA", "Strong PyTorch"],
    "must_haves": ["CUDA", "C++", "LLM inference experience"],
    "nice_to_haves": ["TensorRT", "Triton"],
    "experience_level": "Senior",
    "responsibilities": ["Optimize LLM inference", "Build CUDA kernels"],
    "tech_stack": ["CUDA", "C++", "PyTorch"],
    "domains": ["LLM Inference"],
    "team_context": "Part of LLM Inference team",
    "priority": "high"
}
```

**Deliverable**: Complete profile input interfaces for teams, interviewers, and positions ✅

---

## Schema Compliance Checklist

For each source, ensure:
- [ ] All required fields populated
- [ ] Data types match schema
- [ ] IDs follow format (github_{handle}, x_{handle}, etc.)
- [ ] Metadata fields present (created_at, updated_at, source)
- [ ] Source-specific fields populated correctly
- [ ] No extra fields (only schema fields)

---

## Integration Points

**With Vin's Code**:
- `KnowledgeGraph.add_candidate()` - Store gathered profiles
- `KnowledgeGraph.get_candidate()` - Retrieve profiles
- `PhoneScreenDecisionEngine` - Use for phone screen decisions

**With Existing Code**:
- `GitHubAPIClient` - Already implemented, use as-is
- `GrokAPIClient` - Use for extraction if needed
- `XAPIClient` - Modify from stub to full implementation

---

## Questions to Ask Vin

1. Is knowledge graph schema finalized?
2. What's the exact format for candidate IDs?
3. How should I handle data conflicts when merging sources?
4. Should I validate schema before storing?
5. What's the preferred data source priority (GitHub > X > LinkedIn > arXiv)?

---

## Phase 8: Profile Input Interfaces (4-6 hours)

### Task: Build interfaces for teams, interviewers, and positions to input their information

**Purpose**: Enable real users (teams, interviewers, recruiters) to input their information into the system, not just use sample datasets. This makes the system production-ready with real user data.

**Files**: 
- `backend/api/routes.py` (UPDATE - add profile creation endpoints)
- `backend/api/models.py` (UPDATE - add input models)
- `backend/orchestration/profile_creator.py` (NEW - profile creation logic)

### Implementation

#### 1. Team Profile Input Interface

**Endpoint**: `POST /api/teams/create`

**Request Model**:
```python
class TeamCreateRequest(BaseModel):
    name: str
    department: str
    needs: List[str]
    expertise: List[str]
    stack: List[str]
    domains: List[str]
    culture: str
    work_style: str
    hiring_priorities: List[str]
```

**Response**: Team profile with generated ID

**Validation**:
- All required fields present
- Schema compliance
- Valid data types

#### 2. Interviewer Profile Input Interface

**Endpoint**: `POST /api/interviewers/create`

**Request Model**:
```python
class InterviewerCreateRequest(BaseModel):
    name: str
    email: str
    team_id: str
    expertise: List[str]
    expertise_level: str
    specializations: List[str]
    interview_style: str
    evaluation_focus: List[str]
    question_style: str
    preferred_interview_types: List[str]
```

**Response**: Interviewer profile with generated ID

**Validation**:
- Team ID exists
- Email format valid
- Schema compliance

#### 3. Position Profile Input Interface

**Endpoint**: `POST /api/positions/create`

**Request Model**:
```python
class PositionCreateRequest(BaseModel):
    title: str
    team_id: str
    description: str
    requirements: List[str]
    must_haves: List[str]
    nice_to_haves: List[str]
    experience_level: str
    responsibilities: List[str]
    tech_stack: List[str]
    domains: List[str]
    team_context: str
    reporting_to: str
    collaboration: List[str]
    priority: str
```

**Response**: Position profile with generated ID

**Validation**:
- Team ID exists
- Must-haves not empty
- Schema compliance

### Profile Creator Service

**File**: `backend/orchestration/profile_creator.py`

```python
from backend.database.knowledge_graph import KnowledgeGraph
from typing import Dict, Any
from datetime import datetime

class ProfileCreator:
    """
    Service for creating profiles from user input.
    
    Validates input, generates IDs, and stores in knowledge graph.
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def create_team(self, team_data: Dict[str, Any]) -> str:
        """
        Create team profile from user input.
        
        Args:
            team_data: Team information from API request
        
        Returns:
            Team ID
        """
        # Generate ID
        team_id = f"team_{len(self.kg.get_all_teams()) + 1}"
        
        # Build full profile
        team_profile = {
            "id": team_id,
            "name": team_data["name"],
            "department": team_data["department"],
            "needs": team_data["needs"],
            "expertise": team_data["expertise"],
            "stack": team_data["stack"],
            "domains": team_data["domains"],
            "culture": team_data["culture"],
            "work_style": team_data["work_style"],
            "hiring_priorities": team_data.get("hiring_priorities", []),
            "member_count": 0,
            "member_ids": [],
            "open_positions": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Validate schema
        self._validate_team_profile(team_profile)
        
        # Store in knowledge graph
        return self.kg.add_team(team_profile)
    
    def create_interviewer(self, interviewer_data: Dict[str, Any]) -> str:
        """
        Create interviewer profile from user input.
        
        Args:
            interviewer_data: Interviewer information from API request
        
        Returns:
            Interviewer ID
        """
        # Validate team exists
        team = self.kg.get_team(interviewer_data["team_id"])
        if not team:
            raise ValueError(f"Team {interviewer_data['team_id']} not found")
        
        # Generate ID
        interviewer_id = f"interviewer_{len(self.kg.get_all_interviewers()) + 1}"
        
        # Build full profile
        interviewer_profile = {
            "id": interviewer_id,
            "name": interviewer_data["name"],
            "email": interviewer_data["email"],
            "team_id": interviewer_data["team_id"],
            "expertise": interviewer_data["expertise"],
            "expertise_level": interviewer_data["expertise_level"],
            "specializations": interviewer_data["specializations"],
            "interview_style": interviewer_data["interview_style"],
            "evaluation_focus": interviewer_data["evaluation_focus"],
            "question_style": interviewer_data["question_style"],
            "preferred_interview_types": interviewer_data["preferred_interview_types"],
            "total_interviews": 0,
            "successful_hires": 0,
            "success_rate": 0.0,
            "interview_history": [],
            "cluster_success_rates": {},
            "availability": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Validate schema
        self._validate_interviewer_profile(interviewer_profile)
        
        # Store in knowledge graph
        interviewer_id = self.kg.add_interviewer(interviewer_profile)
        
        # Update team's member list
        team["member_ids"].append(interviewer_id)
        team["member_count"] = len(team["member_ids"])
        self.kg.update_team(interviewer_data["team_id"], team)
        
        return interviewer_id
    
    def create_position(self, position_data: Dict[str, Any]) -> str:
        """
        Create position profile from user input.
        
        Args:
            position_data: Position information from API request
        
        Returns:
            Position ID
        """
        # Validate team exists
        team = self.kg.get_team(position_data["team_id"])
        if not team:
            raise ValueError(f"Team {position_data['team_id']} not found")
        
        # Generate ID
        position_id = f"position_{len(self.kg.get_all_positions()) + 1}"
        
        # Build full profile
        position_profile = {
            "id": position_id,
            "title": position_data["title"],
            "team_id": position_data["team_id"],
            "description": position_data["description"],
            "requirements": position_data["requirements"],
            "must_haves": position_data["must_haves"],
            "nice_to_haves": position_data.get("nice_to_haves", []),
            "experience_level": position_data["experience_level"],
            "responsibilities": position_data["responsibilities"],
            "tech_stack": position_data["tech_stack"],
            "domains": position_data["domains"],
            "team_context": position_data["team_context"],
            "reporting_to": position_data.get("reporting_to", ""),
            "collaboration": position_data.get("collaboration", []),
            "status": "open",
            "priority": position_data.get("priority", "medium"),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Validate schema
        self._validate_position_profile(position_profile)
        
        # Store in knowledge graph
        position_id = self.kg.add_position(position_profile)
        
        # Update team's open positions
        team["open_positions"].append(position_id)
        self.kg.update_team(position_data["team_id"], team)
        
        return position_id
    
    def _validate_team_profile(self, profile: Dict[str, Any]):
        """Validate team profile matches schema."""
        required_fields = ["id", "name", "department", "needs", "expertise", "stack", "domains"]
        for field in required_fields:
            if field not in profile:
                raise ValueError(f"Missing required field: {field}")
    
    def _validate_interviewer_profile(self, profile: Dict[str, Any]):
        """Validate interviewer profile matches schema."""
        required_fields = ["id", "name", "email", "team_id", "expertise", "expertise_level"]
        for field in required_fields:
            if field not in profile:
                raise ValueError(f"Missing required field: {field}")
    
    def _validate_position_profile(self, profile: Dict[str, Any]):
        """Validate position profile matches schema."""
        required_fields = ["id", "title", "team_id", "description", "requirements", "must_haves"]
        for field in required_fields:
            if field not in profile:
                raise ValueError(f"Missing required field: {field}")
```

### API Routes

**File**: `backend/api/routes.py` (UPDATE)

```python
from backend.orchestration.profile_creator import ProfileCreator
from backend.api.models import TeamCreateRequest, InterviewerCreateRequest, PositionCreateRequest

@router.post("/api/teams/create")
async def create_team(request: TeamCreateRequest):
    """
    Create a new team profile.
    
    Teams can input their information: name, department, needs, expertise, etc.
    """
    creator = ProfileCreator(kg)
    team_id = creator.create_team(request.dict())
    return {"team_id": team_id, "status": "created"}

@router.post("/api/interviewers/create")
async def create_interviewer(request: InterviewerCreateRequest):
    """
    Create a new interviewer profile.
    
    Interviewers can input their information: name, expertise, interview style, etc.
    """
    creator = ProfileCreator(kg)
    interviewer_id = creator.create_interviewer(request.dict())
    return {"interviewer_id": interviewer_id, "status": "created"}

@router.post("/api/positions/create")
async def create_position(request: PositionCreateRequest):
    """
    Create a new position profile.
    
    Recruiters/teams can input position requirements: title, requirements, must-haves, etc.
    """
    creator = ProfileCreator(kg)
    position_id = creator.create_position(request.dict())
    return {"position_id": position_id, "status": "created"}
```

### Testing

**File**: `tests/test_profile_creator.py` (NEW)

- Test team creation
- Test interviewer creation
- Test position creation
- Test validation (missing fields, invalid team_id, etc.)
- Test relationship updates (team member_ids, open_positions)
- Test schema compliance

### Usage Example

```python
# Team creates their profile
POST /api/teams/create
{
    "name": "LLM Inference Optimization",
    "department": "AI Infrastructure",
    "needs": ["CUDA expertise", "GPU optimization"],
    "expertise": ["CUDA", "GPU Computing"],
    "stack": ["CUDA", "C++", "PyTorch"],
    "domains": ["LLM Inference"],
    "culture": "Fast-paced, research-oriented",
    "work_style": "Hybrid",
    "hiring_priorities": ["Senior CUDA engineers"]
}

# Interviewer creates their profile
POST /api/interviewers/create
{
    "name": "Alex Chen",
    "email": "alex.chen@company.com",
    "team_id": "team_001",
    "expertise": ["CUDA", "GPU Optimization"],
    "expertise_level": "Senior",
    "specializations": ["CUDA kernel optimization"],
    "interview_style": "Technical deep-dive",
    "evaluation_focus": ["Technical depth", "Problem-solving"],
    "question_style": "Open-ended, scenario-based",
    "preferred_interview_types": ["Technical", "System Design"]
}

# Recruiter creates position
POST /api/positions/create
{
    "title": "Senior LLM Inference Optimization Engineer",
    "team_id": "team_001",
    "description": "We're looking for a senior engineer...",
    "requirements": ["5+ years CUDA", "Strong PyTorch"],
    "must_haves": ["CUDA", "C++", "LLM inference experience"],
    "nice_to_haves": ["TensorRT", "Triton"],
    "experience_level": "Senior",
    "responsibilities": ["Optimize LLM inference", "Build CUDA kernels"],
    "tech_stack": ["CUDA", "C++", "PyTorch"],
    "domains": ["LLM Inference"],
    "team_context": "Part of LLM Inference team",
    "priority": "high"
}
```

**Deliverable**: Complete profile input interfaces for teams, interviewers, and positions ✅

