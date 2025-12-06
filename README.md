# Grok Recruiter

AI-powered candidate sourcing and recruitment system using Graph-Warm-Started Feel-Good Thompson Sampling.

## Overview

Grok Recruiter is an end-to-end recruitment system that:
- Sources candidates from GitHub and X
- Uses graph-based similarity matching
- Employs Feel-Good Thompson Sampling for candidate selection
- Learns from recruiter feedback to improve over time
- Provides X DM interface for recruiter interaction

## Architecture

```
┌─────────────────┐
│  X DM Interface │  (Simulator or Real X API)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Recruiter Agent │  (Grok-powered)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pipeline       │  (Orchestration)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│ Sourcer│ │ Graph   │
│        │ │ Similarity│
└────────┘ └──────────┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│  FG-TS Bandit   │
└─────────────────┘
```

## Setup

### Prerequisites

- Python 3.11+
- API keys:
  - Grok API key (for entity extraction)
  - GitHub token (for candidate sourcing)
  - Neo4j credentials (for graph storage - optional for MVP)

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd x-recruiter-poc
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `GROK_API_KEY` - Grok API key (CRITICAL)
- `GITHUB_TOKEN` - GitHub personal access token
- `NEO4J_URI` - Neo4j database URI (optional)
- `NEO4J_USER` - Neo4j username (optional)
- `NEO4J_PASSWORD` - Neo4j password (optional)

## Usage

### Start FastAPI Server

```bash
uvicorn backend.api.main:app --reload
```

API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Start Dashboard (Optional)

```bash
streamlit run backend/demo/dashboard.py
```

Dashboard will be available at `http://localhost:8501`

### Use X DM Simulator

```python
from backend.simulator.x_dm_simulator import XDMSimulator
from backend.orchestration.recruiter_agent import RecruiterAgent

simulator = XDMSimulator()
agent = RecruiterAgent(simulator=simulator)

# Send message
response = await agent.handle_message("I need an LLM inference engineer")
print(response)

# View chat history
simulator.display_chat()
```

## API Endpoints

### POST /api/v1/sourcing
Trigger candidate sourcing for a role.

**Request:**
```json
{
  "description": "Role description text",
  "title": "Job Title (optional)"
}
```

**Response:**
```json
{
  "role_id": "uuid",
  "candidates": [...],
  "total_found": 25
}
```

### GET /api/v1/candidates/{role_id}
Get candidate list for a role.

### POST /api/v1/outreach
Send outreach message to a candidate.

### POST /api/v1/feedback
Submit feedback on a candidate.

## Project Structure

```
backend/
├── api/              # FastAPI application
├── integrations/     # API clients (GitHub, Grok, X)
├── orchestration/   # Pipeline, agent, sourcer
├── simulator/       # X DM simulator
└── demo/            # Dashboard and metrics
```

## Integration with Vin's Code

The system uses mock implementations for Vin's graph and bandit code. When Vin's code is ready:

1. Replace imports in `backend/orchestration/pipeline.py`:
```python
# Remove try/except, use direct imports:
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
```

2. All mock functions are clearly marked with comments indicating where to switch.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions under 500 lines

## Demo

See `demo_script.md` for step-by-step demo flow.

## License

[Your License Here]

## Contributors

- Ishaan: Integration & Orchestration (APIs + X DM Simulator)
- Vin: Backend Core (Graph + ML Algorithm)

