# Ishaan's Implementation Checklist

## Your Role: Integration & Orchestration (APIs + X DM Simulator)

**Goal**: Build API integrations, X DM simulator, end-to-end pipeline, and demo dashboard

**Timeline**: 3 days, 8 hours/day = 24 hours total

**Your Files** (You own these):
```
backend/
├── api/
│   ├── main.py
│   ├── routes.py
│   └── models.py
├── integrations/
│   ├── x_api.py
│   ├── github_api.py
│   ├── grok_api.py
│   └── api_utils.py
├── orchestration/
│   ├── recruiter_agent.py
│   ├── candidate_sourcer.py
│   └── pipeline.py
├── simulator/
│   ├── x_dm_simulator.py
│   ├── simulator_ui.py (Streamlit)
│   └── simulator_api.py
└── demo/
    ├── dashboard.py
    └── metrics.py
```

---

## Day 1: Foundation (8 hours)

### Hour 1-2: API Clients Setup

**Task**: Set up GitHub and Grok API clients

**Checklist**:
- [ ] Create `backend/integrations/github_api.py`
- [ ] Implement GitHub API authentication
- [ ] Implement `search_users(query, language, topics)` - Search for candidates
- [ ] Implement `get_user_profile(username)` - Get profile data
- [ ] Implement `get_user_repos(username)` - Get repositories
- [ ] Implement `get_repo_languages(repo)` - Get languages used
- [ ] Create `backend/integrations/grok_api.py`
- [ ] Implement Grok API authentication
- [ ] Implement `get_embeddings(text)` - Get text embeddings
- [ ] Implement `extract_entities_with_grok(text, entity_types)` - Entity extraction
- [ ] Create `backend/integrations/api_utils.py` for shared utilities
- [ ] Set up environment variables (.env file)
- [ ] Test API connections

**GitHub API Example**:
```python
# backend/integrations/github_api.py
import httpx
from typing import List, Dict

class GitHubAPIClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"token {token}"}
    
    async def search_users(self, query: str, language: str = None) -> List[Dict]:
        """Search GitHub users by query, language, etc."""
        # Your implementation
        pass
    
    async def get_user_profile(self, username: str) -> Dict:
        """Get user profile data"""
        pass
```

**Grok API Example**:
```python
# backend/integrations/grok_api.py
import httpx
from typing import List, Dict

class GrokAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
    
    async def extract_entities_with_grok(self, text: str, entity_types: List[str]) -> Dict:
        """
        Extract entities using Grok API
        
        Entity types: ['skills', 'experience', 'education', 'projects']
        """
        # Call Grok API with prompt to extract entities
        pass
    
    async def get_embeddings(self, text: str) -> List[float]:
        """Get text embeddings from Grok"""
        pass
```

---

### Hour 3-4: FastAPI Server

**Task**: Set up FastAPI backend server

**Checklist**:
- [ ] Create `backend/api/main.py`
- [ ] Initialize FastAPI app
- [ ] Set up CORS (if needed)
- [ ] Create `backend/api/models.py` with Pydantic models:
  - [ ] `Candidate` model
  - [ ] `Role` model
  - [ ] `GraphSimilarity` model
  - [ ] `BanditState` model
- [ ] Create `backend/api/routes.py` with endpoints:
  - [ ] `GET /health` - Health check
  - [ ] `POST /sourcing` - Trigger candidate sourcing
  - [ ] `GET /candidates` - Get candidate list
  - [ ] `POST /outreach` - Send outreach
  - [ ] `POST /feedback` - Update from feedback
- [ ] Test server starts: `uvicorn backend.api.main:app --reload`
- [ ] Test health endpoint

**FastAPI Structure**:
```python
# backend/api/main.py
from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(title="Grok Recruiter API")
app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok"}

# backend/api/routes.py
from fastapi import APIRouter
router = APIRouter()

@router.post("/sourcing")
async def trigger_sourcing(role_description: str):
    """Trigger candidate sourcing"""
    pass
```

---

### Hour 5-6: Candidate Sourcing

**Task**: Implement candidate sourcing from GitHub/X

**Checklist**:
- [ ] Create `backend/orchestration/candidate_sourcer.py`
- [ ] Implement `source_from_github(role_description)` - Search GitHub
- [ ] Implement `source_from_x(role_description)` - Search X profiles
- [ ] Implement `extract_candidate_data(profile)` - Parse profile data
- [ ] Implement `rank_candidates(candidates, role)` - Initial ranking
- [ ] Test with sample role description
- [ ] Return structured candidate data

**Implementation**:
```python
# backend/orchestration/candidate_sourcer.py
from backend.integrations.github_api import GitHubAPIClient
from backend.integrations.grok_api import GrokAPIClient

class CandidateSourcer:
    def __init__(self):
        self.github = GitHubAPIClient(os.getenv("GITHUB_TOKEN"))
        self.grok = GrokAPIClient(os.getenv("GROK_API_KEY"))
    
    async def source_candidates(self, role_description: str) -> List[Dict]:
        """
        Source candidates from GitHub and X
        
        Returns list of candidate dictionaries with:
        - github_handle
        - x_handle
        - profile_data
        - repos
        - skills (extracted)
        """
        # Search GitHub
        # Search X
        # Extract data
        # Return candidates
        pass
```

---

### Hour 7-8: X DM Simulator (Basic)

**Task**: Build basic X DM simulator

**Checklist**:
- [ ] Create `backend/simulator/x_dm_simulator.py`
- [ ] Implement chat interface (CLI version first)
- [ ] Implement message sending
- [ ] Implement message receiving
- [ ] Store chat history
- [ ] Test basic conversation flow
- [ ] Create simple UI (Streamlit or HTML)

**CLI Version** (Start here - fastest):
```python
# backend/simulator/x_dm_simulator.py
class XDMSimulator:
    def __init__(self):
        self.chat_history = []
    
    def send_message(self, message: str):
        """Send message from recruiter"""
        self.chat_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now()
        })
    
    def receive_message(self, message: str):
        """Receive message from @x_recruiting"""
        self.chat_history.append({
            'role': 'assistant',
            'content': message,
            'timestamp': datetime.now()
        })
    
    def display_chat(self):
        """Display chat history"""
        for msg in self.chat_history:
            print(f"{msg['role']}: {msg['content']}")
```

**Streamlit Version** (Upgrade later):
```python
# backend/simulator/simulator_ui.py
import streamlit as st

st.title("X Recruiter - DM Simulator")
st.write("Simulating X DM interface for @x_recruiting")

# Display chat
for msg in chat_history:
    st.chat_message(msg['role']).write(msg['content'])

# Input
user_input = st.chat_input("Type your message...")
if user_input:
    response = recruiter_agent.handle_message(user_input)
    st.chat_message("assistant").write(response)
```

---

## Day 2: Integration (8 hours)

### Hour 1-2: Pipeline Integration

**Task**: Connect all components end-to-end

**Checklist**:
- [ ] Create `backend/orchestration/pipeline.py`
- [ ] Implement `process_role_request(role_description)`:
  - [ ] Source candidates (GitHub/X)
  - [ ] Extract entities (Grok API)
  - [ ] Build graphs (call Vin's `graph_builder.py`)
  - [ ] Compute similarities (call Vin's `graph_similarity.py`)
  - [ ] Initialize FG-TS (call Vin's `fgts_bandit.py`)
  - [ ] Select candidates (FG-TS)
  - [ ] Return candidate list
- [ ] Implement error handling
- [ ] Add logging
- [ ] Test end-to-end flow

**Pipeline Structure**:
```python
# backend/orchestration/pipeline.py
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS

class RecruitingPipeline:
    async def process_role_request(self, role_description: str):
        # 1. Source candidates
        candidates = await candidate_sourcer.source_candidates(role_description)
        
        # 2. Extract entities (Grok API)
        role_entities = await grok_api.extract_entities_with_grok(role_description)
        
        # 3. Build graphs (Vin's code)
        role_graph = build_candidate_role_graph(None, role_entities)
        candidate_graphs = [build_candidate_role_graph(c, role_entities) 
                           for c in candidates]
        
        # 4. Initialize FG-TS (Vin's code)
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_graph(candidates, role_graph)
        
        # 5. Select candidates
        selected = bandit.select_candidate()
        
        return candidates[selected]
```

---

### Hour 3-4: X DM Simulator + Agent

**Task**: Complete simulator and integrate with Grok agent

**Checklist**:
- [ ] Complete `x_dm_simulator.py` (full features)
- [ ] Create `backend/orchestration/recruiter_agent.py`
- [ ] Implement `handle_message(message)` - Process recruiter messages
- [ ] Implement role requirement extraction (ask clarifying questions)
- [ ] Implement candidate recommendation display
- [ ] Implement feedback collection
- [ ] Connect simulator to agent
- [ ] Test full conversation flow

**Recruiter Agent**:
```python
# backend/orchestration/recruiter_agent.py
from backend.integrations.grok_api import GrokAPIClient
from backend.orchestration.pipeline import RecruitingPipeline

class RecruiterAgent:
    def __init__(self, use_simulator=True):
        self.grok = GrokAPIClient(os.getenv("GROK_API_KEY"))
        self.pipeline = RecruitingPipeline()
        self.conversation_state = {}
    
    async def handle_message(self, message: str) -> str:
        """
        Handle recruiter message via X DM (simulated or real)
        
        Returns response from @x_recruiting
        """
        # Parse message
        # Extract intent (new role, feedback, question)
        # Call Grok API for response generation
        # Trigger pipeline if needed
        # Return response
        pass
    
    async def process_role_request(self, role_description: str):
        """Process new role request"""
        # Ask clarifying questions
        # Trigger sourcing pipeline
        # Return candidate recommendations
        pass
```

---

### Hour 5-6: API Endpoints

**Task**: Complete FastAPI endpoints

**Checklist**:
- [ ] Complete `POST /sourcing` endpoint
  - [ ] Accept role description
  - [ ] Trigger candidate sourcing
  - [ ] Return candidate list
- [ ] Complete `GET /candidates` endpoint
  - [ ] Return ranked candidate list
  - [ ] Include graph similarities
  - [ ] Include bandit scores
- [ ] Complete `POST /outreach` endpoint
  - [ ] Accept candidate selection
  - [ ] Generate outreach message (Grok)
  - [ ] Send via simulator
  - [ ] Track outreach
- [ ] Complete `POST /feedback` endpoint
  - [ ] Accept feedback (positive/negative)
  - [ ] Update bandit (call Vin's `bandit.update()`)
  - [ ] Store in Neo4j
- [ ] Test all endpoints

**API Routes**:
```python
# backend/api/routes.py
@router.post("/sourcing")
async def trigger_sourcing(role: RoleRequest):
    """Trigger candidate sourcing for a role"""
    candidates = await pipeline.process_role_request(role.description)
    return {"candidates": candidates}

@router.get("/candidates/{role_id}")
async def get_candidates(role_id: str):
    """Get candidate list for a role"""
    # Return candidates with scores
    pass

@router.post("/outreach")
async def send_outreach(outreach: OutreachRequest):
    """Send outreach to candidate"""
    # Generate message, send, track
    pass

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback on candidate"""
    # Update bandit, store feedback
    pass
```

---

### Hour 7-8: Basic Demo

**Task**: Create basic demo dashboard

**Checklist**:
- [ ] Create `backend/demo/dashboard.py`
- [ ] Display candidate list
- [ ] Display graph similarities
- [ ] Display bandit state (alpha/beta values)
- [ ] Show learning metrics (basic)
- [ ] Test dashboard loads

**Dashboard Structure**:
```python
# backend/demo/dashboard.py
import streamlit as st

st.title("Grok Recruiter Dashboard")

# Candidate list
st.header("Candidates")
for candidate in candidates:
    st.write(f"{candidate['name']} - Similarity: {candidate['similarity']}")

# Learning metrics
st.header("Learning Metrics")
st.write(f"Response Rate: {response_rate}%")
st.write(f"Total Interactions: {total_interactions}")
```

---

## Day 3: Polish & Demo (8 hours)

### Hour 1-2: Metrics Dashboard

**Task**: Complete learning curve visualization

**Checklist**:
- [ ] Create `backend/demo/metrics.py`
- [ ] Implement learning curve data collection
- [ ] Implement warm-start vs cold-start comparison
- [ ] Create visualization (plotly/matplotlib)
- [ ] Display response rates over time
- [ ] Display improvement metrics
- [ ] Test with real data

**Metrics Visualization**:
```python
# backend/demo/metrics.py
import plotly.graph_objects as go

def plot_learning_curves(warm_start_data, cold_start_data):
    """
    Plot learning curves comparing warm-start vs cold-start
    """
    fig = go.Figure()
    
    # Warm-start curve
    fig.add_trace(go.Scatter(
        x=warm_start_data['timestamps'],
        y=warm_start_data['response_rates'],
        name='Graph Warm-Started FG-TS'
    ))
    
    # Cold-start curve
    fig.add_trace(go.Scatter(
        x=cold_start_data['timestamps'],
        y=cold_start_data['response_rates'],
        name='Cold-Start FG-TS'
    ))
    
    fig.update_layout(
        title="Learning Curves: Warm-Start vs Cold-Start",
        xaxis_title="Interactions",
        yaxis_title="Response Rate"
    )
    
    return fig
```

---

### Hour 3-4: Demo Script

**Task**: Prepare demo flow

**Checklist**:
- [ ] Create demo script/flow document
- [ ] Test end-to-end demo:
  - [ ] Recruiter requests role
  - [ ] System sources candidates
  - [ ] Shows candidate list
  - [ ] Selects candidate (FG-TS)
  - [ ] Sends outreach
  - [ ] Gets feedback
  - [ ] Updates and shows learning
- [ ] Fix any bugs
- [ ] Prepare sample data (if needed)
- [ ] Record demo video (backup)

**Demo Flow**:
```
1. Open X DM simulator
2. Recruiter: "I need an LLM inference engineer"
3. System: "What skills are must-haves? Experience level?"
4. Recruiter: [Answers]
5. System: "Sourcing candidates..."
6. System: "Found 25 candidates. Top 5: [list]"
7. System: "Should I reach out to top 10?"
8. Recruiter: "Yes, but candidate #3 isn't qualified - missing CUDA"
9. System: "Got it, updating my criteria..."
10. System: [Shows improved candidates]
11. System: [Shows learning metrics - 3x faster learning]
```

---

### Hour 5-6: Presentation Prep

**Task**: Create presentation materials

**Checklist**:
- [ ] Create slides (Keynote/PowerPoint)
- [ ] Slide 1: Problem statement
- [ ] Slide 2: Our solution (graph-warm-started FG-TS)
- [ ] Slide 3: Architecture diagram
- [ ] Slide 4: Results (learning curves)
- [ ] Slide 5: Demo
- [ ] Prepare talking points
- [ ] Prepare Q&A answers
- [ ] Record demo video (backup)

**Key Talking Points**:
- "We use graph structure to warm-start Feel-Good Thompson Sampling"
- "This is a novel combination - first application of graph structure as prior for bandits"
- "Results show 3x faster learning compared to cold-start"
- "Built on three papers: [cite papers]"
- "End-to-end system: sourcing → matching → outreach → learning"

---

### Hour 7-8: Final Polish

**Task**: Code cleanup and final testing

**Checklist**:
- [ ] Code cleanup (remove debug prints, unused code)
- [ ] Improve error messages
- [ ] Add logging throughout
- [ ] Test end-to-end one more time
- [ ] Fix any last bugs
- [ ] Update README
- [ ] Prepare for demo

---

## Interface with Vin

### What You Provide (Vin calls these)

**Functions**:
```python
# backend/integrations/grok_api.py
def extract_entities_with_grok(text: str, entity_types: List[str]) -> Dict
    """Extract entities using Grok API - Vin needs this!"""

# backend/database/neo4j_client.py (if you set it up)
def store_graph(graph, graph_id) -> None
def get_candidate_graph(candidate_id) -> Graph
```

**Priority**: Get `extract_entities_with_grok()` done on Day 1 - Vin needs it Day 2!

---

### What You Need from Vin

**Functions** (Vin provides):
```python
# backend/graph/graph_builder.py
def build_candidate_role_graph(candidate_data, role_data) -> Graph

# backend/graph/graph_similarity.py
def compute_graph_similarity(role_graph, candidate_graph) -> float

# backend/algorithms/fgts_bandit.py
class GraphWarmStartedFGTS:
    def initialize(candidates, role_graph) -> None
    def select() -> int
    def update(arm_index, reward) -> None
```

**If Vin's code isn't ready**: Use mock functions, integrate later

---

## Success Criteria

**You're done when**:
- [ ] X DM simulator works (looks like X DMs)
- [ ] GitHub API integrated (sourcing works)
- [ ] Grok API integrated (entity extraction works)
- [ ] End-to-end pipeline works (sourcing → outreach → feedback)
- [ ] Demo dashboard works (shows learning curves)
- [ ] Metrics displayed (warm-start vs cold-start)
- [ ] Demo script ready
- [ ] Presentation ready

---

## Quick Reference

**APIs to integrate**:
- GitHub API: https://docs.github.com/en/rest
- Grok API: https://docs.x.ai/docs/tutorial
- X API: https://developer.twitter.com/en/docs (for future)

**Key endpoints you build**:
- `POST /sourcing` - Trigger sourcing
- `GET /candidates` - Get candidate list
- `POST /outreach` - Send outreach
- `POST /feedback` - Update from feedback

**Tech Stack**:
- `fastapi` - API server
- `httpx` - HTTP client
- `streamlit` - Simulator UI
- `plotly` - Visualizations
- `pydantic` - Data validation

---

## Critical Dependencies

**Day 1 Priority**: 
- Get `extract_entities_with_grok()` working - Vin needs it Day 2!

**Day 2 Priority**:
- Get pipeline working - needs Vin's graph/bandit code
- If Vin's code not ready, use mocks

**Day 3 Priority**:
- Get demo working - needs Vin's learning curve data
- If not ready, use simulated data

---

**Remember**: Focus on your domain. Don't touch Vin's files. Daily sync at end of day. Ship it! 🚀

