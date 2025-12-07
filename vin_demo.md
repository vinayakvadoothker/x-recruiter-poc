# Vin's Demo Plan: Grok Recruiting Platform Backend

## Your Role: Backend Infrastructure + Multi-Tenancy + Position Creation

**Focus**: Build multi-tenant backend infrastructure, Grok-powered position creation, pipeline tracking, and company dashboard APIs.

**Timeline**: 12-18 hours total (feature-by-feature, fully complete each)

---

## Development Approach: Feature-by-Feature (Fully Complete Each)

**Strategy**: Complete each feature fully (Database → API → Frontend) before moving to the next. This ensures:
- Each feature is testable end-to-end
- No partial implementations
- Clear progress milestones
- Easier debugging and iteration

---

## 📊 Quick Reference: Database Usage

### PostgreSQL (Relational Data)
**Use for**: CRUD operations, company_id filtering, foreign keys, relational queries
- ✅ Teams - Full data with company_id, member_ids, open_positions
- ✅ Interviewers - Full data with company_id, team_id foreign key
- ⏳ Positions - Full data with company_id, team_id, status, distribution flags
- ⏳ Conversations - Grok conversation state
- ⏳ Pipeline Stages - Candidate pipeline tracking

### Weaviate (Vector Database)
**Use for**: Embeddings, similarity search, matching operations
- ✅ Candidate embeddings - For candidate similarity search
- ✅ Team embeddings - For team-candidate matching
- ✅ Interviewer embeddings - For interviewer-candidate matching
- ⏳ Position embeddings - For position similarity checking

### Key Point: Dual Storage
- **Teams & Interviewers**: Stored in BOTH PostgreSQL (CRUD) and Weaviate (embeddings for matching)
- **Positions**: Will be stored in BOTH PostgreSQL (CRUD) and Weaviate (embeddings for similarity)
- **Candidates**: Currently only in Weaviate (will add PostgreSQL for pipeline tracking)

**See "Database Architecture" section below for full details.**

---

## Phase-by-Phase Schedule

### Phase 0: Foundation Setup (1.5 hours)

**Backend Tasks (1.5 hours)**:
1. **PostgreSQL Client** (1 hour):
   - Create `backend/database/postgres_client.py` (NEW)
   - Connection pooling (asyncpg or psycopg2)
   - Connection string from `DATABASE_URL` env var
   - Test connection

2. **Multi-Tenancy Foundation** (0.5 hour):
   - Create `CompanyContext` class
   - Add `company_id` filtering helper methods
   - Update Weaviate schema to include `company_id` in metadata

**Deliverable**: PostgreSQL client working, company context ready

**Frontend Tasks** (1.5 hours - happens in parallel):
- Next.js setup & shadcn integration
- Design system & dark theme (xAI/Grok inspired)
- Basic layout & routing structure

---

### Phase 1: Teams Management ✅ COMPLETE - 4 hours

**Step 1: Database (1 hour)** ✅
- Create `teams` table in PostgreSQL (see SQL in demo_spec.md)
- Add indexes
- Test table creation and queries
- **Note**: Teams are stored in PostgreSQL for relational queries. Embeddings are stored in Weaviate via KnowledgeGraph (for matching).

**Step 2: Backend API (1.5 hours)** ✅
- Create `backend/orchestration/company_context.py` (if not done)
- Add request/response models to `backend/api/models.py`
- Add endpoints to `backend/api/routes.py`:
  - `GET /api/teams` - List teams (filtered by company_id) - **Uses PostgreSQL**
  - `POST /api/teams` - Create team - **Saves to PostgreSQL**
  - `GET /api/teams/{team_id}` - Get team details - **Uses PostgreSQL**
  - `PUT /api/teams/{team_id}` - Update team - **Updates PostgreSQL**
  - `DELETE /api/teams/{team_id}` - Delete team - **Deletes from PostgreSQL**
  - `POST /api/teams/chat/stream` - AI-powered team creation chat
- **Note**: API routes use PostgreSQL directly. For matching operations, teams also need embeddings in Weaviate (via KnowledgeGraph).
- Test all endpoints with Postman/curl

**Step 3: Frontend (1.5 hours)** ✅
- Teams list page (`/teams`)
- Create team form with AI chat interface
- Edit team form with AI chat interface
- Delete team with confirmation dialog
- API integration
- Session storage for progress
- Test full flow: create → view → edit → delete

**✅ Feature Complete**: Teams management fully working end-to-end

---

### Phase 2: Interviewers Management ✅ COMPLETE - 3.5 hours

**Step 1: Database (0.5 hour)** ✅
- Create `interviewers` table in PostgreSQL (see SQL in demo_spec.md)
- Add foreign key to teams (`team_id`)
- Create indexes
- **Note**: Interviewers are stored in PostgreSQL for relational queries. Embeddings are stored in Weaviate via KnowledgeGraph (for matching).

**Step 2: Backend API (1.5 hours)** ✅
- Add request/response models
- Add endpoints:
  - `GET /api/interviewers` - List interviewers (filtered by company_id) ✅ - **Uses PostgreSQL**
  - `POST /api/interviewers` - Create interviewer ✅ - **Saves to PostgreSQL**
  - `GET /api/interviewers/{interviewer_id}` - Get interviewer details ✅ - **Uses PostgreSQL**
  - `PUT /api/interviewers/{interviewer_id}` - Update interviewer ✅ - **Updates PostgreSQL**
  - `DELETE /api/interviewers/{interviewer_id}` - Delete interviewer ✅ - **Deletes from PostgreSQL**
  - `POST /api/interviewers/chat/stream` - AI-powered interviewer creation chat ✅
- **Note**: API routes use PostgreSQL directly. For matching operations, interviewers also need embeddings in Weaviate (via KnowledgeGraph).
- Test all endpoints

**Step 3: Frontend (1.5 hours)** ✅
- Interviewers list page (`/interviewers`) ✅
- Create interviewer form with AI chat interface ✅
- Edit interviewer form ✅
- Delete interviewer with confirmation ✅
- Table truncation with tooltips for better UX ✅
- Auto-switch to form tab on chat completion ✅
- API integration ✅
- Test full flow ✅

**✅ Feature Complete**: Interviewers management fully working end-to-end

---

### Phase 2.5: Embeddings Visualization & Graph ✅ COMPLETE - 4 hours

**Backend Tasks (2 hours)** ✅
- `GET /api/teams/{team_id}/embedding` - Get team embedding vector ✅
- `GET /api/interviewers/{interviewer_id}/embedding` - Get interviewer embedding vector ✅
- `POST /api/teams/{team_id}/generate-embedding` - Generate team embedding ✅
- `POST /api/interviewers/{interviewer_id}/generate-embedding` - Generate interviewer embedding ✅
- `GET /api/embeddings/graph` - Get all embeddings with 3D positions (PCA reduction) ✅
- `GET /api/embeddings/{profile_type}/{profile_id}/similar` - Find similar embeddings (cross-type) ✅
- `GET /api/weaviate/schema/status` - Check Weaviate schema status ✅
- `POST /api/weaviate/schema/create` - Manually create Weaviate schema ✅
- `POST /api/embeddings/sync` - Sync embeddings for teams/interviewers ✅
- Fixed Weaviate connection (gRPC fallback to HTTP) ✅
- Fixed Weaviate cluster mode (disabled for single-node) ✅
- Fixed Weaviate schema creation and detection ✅
- Added `find_similar_embeddings_across_types()` method ✅

**Frontend Tasks (2 hours)** ✅
- Embedding dialogs for teams and interviewers ✅
  - View embedding vector (768 dimensions)
  - Vector statistics (min, max, mean, magnitude)
  - Metadata display
  - Proper dialog structure matching CreateTeamDialog ✅
- Teams page: View/Generate embedding buttons ✅
- Interviewers page: View/Generate embedding buttons ✅
- Graph page (`/graph`) with 3D visualization ✅
  - Interactive 3D force graph using react-force-graph-3d ✅
  - Node click to view details and similar profiles ✅
  - Search by name ✅
  - Profile type filters (collapsible) ✅
  - Auto-zoom to filtered nodes ✅
  - Refocus button ✅
  - Legend with profile type counts ✅
- Node details dialog ✅
  - Embedding tab: Full vector, statistics, metadata ✅
  - Similar profiles tab: Cross-type similarity search ✅
  - Filters: Profile type, similarity threshold, search, sort ✅
  - Collapsible filters section ✅
- Fixed React Three Fiber compatibility issues ✅
- Removed automatic embedding sync from graph page ✅

**✅ Feature Complete**: Full embeddings visualization and graph exploration system

---

### Phase 3: Position Creation ✅ COMPLETE - 7 hours

**Backend Tasks (4 hours)** ✅:
1. **Grok Conversation Management** (2 hours) ✅:
   - Create `conversations` table in PostgreSQL ✅
   - Create `positions` table in PostgreSQL (relational data) ✅
   - Create `position_distribution` table in PostgreSQL (distribution flags) ✅
   - Implement Grok conversation management (store in PostgreSQL) ✅
   - Implement position data extraction ✅

2. **Position APIs** (2 hours) ✅:
   - `POST /api/positions/chat/stream` - Streaming Grok position creation chat ✅
   - `GET /api/positions` - List positions - **Uses PostgreSQL** ✅
   - `GET /api/positions/{position_id}` - Get position details - **Uses PostgreSQL** ✅
   - `PUT /api/positions/{position_id}` - Update position - **Updates PostgreSQL** ✅
   - `DELETE /api/positions/{position_id}` - Delete position - **Deletes from PostgreSQL** ✅
   - `POST /api/positions/check-similarity` - Check for similar positions - **Uses Weaviate for similarity search** ✅
   - `GET /api/positions/{position_id}/embedding` - Get position embedding ✅
   - `POST /api/positions/{position_id}/generate-embedding` - Generate position embedding ✅
   - Position similarity checking - **Uses Weaviate embeddings** ✅
   - Distribution flags (store in PostgreSQL) ✅
   - **Dual Storage**: Save positions to PostgreSQL (relational) AND Weaviate (embeddings for similarity) ✅

**Deliverable**: Grok-powered position creation with APIs ✅

**Frontend Tasks** ✅:
- Grok chat interface (position creation) ✅
- Position list page with search ✅
- Edit position dialog with chat interface ✅
- Similar positions warning before creation ✅
- Auto-create on second click after similarity warning ✅
- Position embedding dialog ✅
- Graph page shows position embeddings ✅
- Node details dialog supports positions ✅

---

### Phase 4: Candidate Storage & CRUD (2 hours)

**Backend Tasks (2 hours)**:
1. **Candidate PostgreSQL Storage** (1 hour):
   - Create `candidates` table in PostgreSQL
   - Add `company_id` filtering
   - Migrate candidates from Weaviate-only to dual storage (PostgreSQL + Weaviate)
   - Store full candidate data in PostgreSQL (source of truth)
   - Keep embeddings in Weaviate (for matching)

2. **Candidate APIs** (1 hour):
   - `GET /api/candidates` - List candidates (filtered by company_id) - **Uses PostgreSQL**
   - `GET /api/candidates/{candidate_id}` - Get candidate details - **Uses PostgreSQL**
   - `POST /api/candidates` - Create candidate - **Saves to PostgreSQL AND Weaviate**
   - `PUT /api/candidates/{candidate_id}` - Update candidate - **Updates PostgreSQL AND Weaviate**
   - `DELETE /api/candidates/{candidate_id}` - Delete candidate - **Deletes from PostgreSQL AND Weaviate**
   - `GET /api/candidates?position_id={position_id}` - Filter by position
   - Update outbound gathering to save to PostgreSQL

**Deliverable**: Candidates stored in both PostgreSQL (CRUD) and Weaviate (embeddings)

**Frontend Tasks** (happens in parallel):
- Candidate list page
- Candidate details page
- Basic filtering and search

---

### Phase 5: Pipeline Tracking (2.5 hours)

**Backend Tasks (2.5 hours)**:
1. **Pipeline System** (1.5 hours):
   - Create `pipeline_stages` table in PostgreSQL
   - Create `PipelineTracker` class
   - Implement stage transitions (store in PostgreSQL)
   - Store pipeline history (in PostgreSQL)

2. **Pipeline APIs** (1 hour):
   - `GET /api/candidates?stage={stage}` - Filter by stage
   - `GET /api/candidates/{candidate_id}/pipeline` - Get pipeline status
   - `PUT /api/candidates/{candidate_id}/stage` - Update pipeline stage
   - Integrate with phone screen system
   - Integrate with matching system

**Deliverable**: Pipeline tracking system with APIs

**Frontend Tasks** (happens in parallel):
- Candidate pipeline dashboard (Kanban board)
- Stage filtering
- Pipeline timeline view

---

### Phase 6: Candidate Pipeline Operations (1.5 hours)

**Backend Tasks (1.5 hours)**:
1. **Pipeline Integration APIs** (1 hour):
   - `POST /api/candidates/{candidate_id}/phone-screen` - Trigger phone screen
   - `POST /api/candidates/{candidate_id}/match` - Trigger matching
   - `GET /api/candidates/{candidate_id}/pipeline` - Get full pipeline history
   - Integrate phone screen with pipeline tracking
   - Integrate matching with pipeline tracking

2. **Outbound Integration** (0.5 hour):
   - Update outbound gathering to set `company_id: "xai"`
   - Auto-create pipeline entry when candidate is gathered

**Deliverable**: Full candidate pipeline operations with phone screen and matching

**Frontend Tasks** (happens in parallel):
- Enhanced candidate details with pipeline timeline
- Phone screen trigger button
- Match trigger button
- Pipeline status indicators

---

### Phase 7: Company Dashboard & Stats (1 hour)

**Backend Tasks (1 hour)**:
- `GET /api/company/info` - Get company info
- `GET /api/company/stats` - Get stats (positions, candidates, teams)
- `GET /api/positions/{position_id}/candidates` - Get candidates in pipeline
- `PUT /api/positions/{position_id}/distribution` - Update distribution flags

**Deliverable**: Company dashboard APIs

**Frontend Tasks** (happens in parallel):
- Dashboard overview
- Stats cards
- Recent activity

---

### Phase 8: Testing & Polish (2 hours)

**Backend Tasks (2 hours)**:
- End-to-end testing
- API testing
- Integration testing
- Documentation

**Frontend Tasks** (happens in parallel):
- Polish & animations
- Final UI tweaks

---

## Key Implementation Details

### 1. Company Context Manager

```python
# backend/orchestration/company_context.py
class CompanyContext:
    """Manages current company context (hardcoded to xai for demo)."""
    
    def __init__(self):
        self.current_company_id = "xai"  # Hardcoded for demo
    
    def get_company_id(self) -> str:
        return self.current_company_id
    
    def filter_by_company(self, query_params: Dict) -> Dict:
        """Add company_id filter to query."""
        query_params['company_id'] = self.current_company_id
        return query_params
```

### 2. Pipeline Stages

```python
from enum import Enum

class PipelineStage(str, Enum):
    GATHERED = "gathered"
    PHONE_SCREEN_SCHEDULED = "phone_screen_scheduled"
    PHONE_SCREEN_COMPLETED = "phone_screen_completed"
    MATCHED_TO_TEAM = "matched_to_team"
    MATCHED_TO_INTERVIEWER = "matched_to_interviewer"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
```

### 3. Grok Position Creation Prompt

```
You are helping create a new job position for xAI.

Ask the user questions to gather:
1. Job title
2. Must-have technical skills
3. Nice-to-have skills
4. Experience level (Junior/Mid/Senior/Staff)
5. Key responsibilities
6. Domains (LLM Inference, GPU Computing, etc.)
7. Priority (high/medium/low)
8. Team assignment (if known)

After gathering all information, summarize what you've learned and ask for confirmation before creating the position.

Format your response as JSON when you have all information:
{
    "title": "...",
    "must_haves": [...],
    "nice_to_haves": [...],
    "experience_level": "...",
    "responsibilities": [...],
    "domains": [...],
    "priority": "...",
    "team_id": "..." (optional)
}
```

### 4. Position Similarity Check

```python
def find_similar_positions(
    position_data: Dict,
    company_id: str,
    threshold: float = 0.85
) -> List[Dict]:
    """
    Find similar existing positions.
    
    Returns positions with similarity >= threshold.
    """
    # Generate embedding for new position
    position_emb = embedder.embed_position(position_data)
    
    # Get all existing positions for company
    existing_positions = kg.get_all_positions()
    existing_positions = [p for p in existing_positions if p.get('company_id') == company_id]
    
    # Calculate similarities
    similar = []
    for pos in existing_positions:
        existing_emb = embedder.embed_position(pos)
        similarity = cosine_similarity(position_emb, existing_emb)
        if similarity >= threshold:
            similar.append({
                'position': pos,
                'similarity': similarity
            })
    
    return sorted(similar, key=lambda x: x['similarity'], reverse=True)
```

---

## Database Architecture: When to Use PostgreSQL vs Weaviate

### Dual Storage Strategy

**Teams and Interviewers are stored in BOTH databases** for different purposes:

#### PostgreSQL (Relational Data - Source of Truth)
**Purpose**: Store relational data with ACID guarantees, foreign keys, and company_id filtering

**What's stored**:
- ✅ **Teams** - Full team data with company_id, foreign keys, relationships
- ✅ **Interviewers** - Full interviewer data with company_id, team_id foreign key
- ⏳ **Positions** - Position data with company_id, team_id, status, distribution flags
- ⏳ **Conversations** - Grok position creation conversation state
- ⏳ **Pipeline Stages** - Candidate pipeline stage history
- ⏳ **Position Distribution** - Distribution flags (post_to_x, available_to_grok)
- ⏳ **Companies** - Company profiles

**When to use PostgreSQL**:
- ✅ **CRUD operations** (Create, Read, Update, Delete) for teams/interviewers/positions
- ✅ **Company_id filtering** - Multi-tenant data isolation
- ✅ **Foreign key relationships** - team_id, interviewer_id, position_id
- ✅ **Relational queries** - JOIN operations, aggregations
- ✅ **ACID transactions** - Data consistency guarantees
- ✅ **API endpoints** - All REST API endpoints use PostgreSQL

**Example**: `GET /api/teams` queries PostgreSQL with `WHERE company_id = 'xai'`

#### Weaviate (Vector Database - Embeddings & Similarity)
**Purpose**: Store embeddings for similarity search and matching

**What's stored**:
- ✅ **Candidate embeddings** - For candidate similarity search
- ✅ **Team embeddings** - For team-candidate matching
- ✅ **Interviewer embeddings** - For interviewer-candidate matching
- ✅ **Position embeddings** - For position-candidate matching and similarity checking

**When to use Weaviate**:
- ✅ **Similarity search** - Find similar candidates/teams/interviewers/positions
- ✅ **Matching operations** - Team matching, interviewer matching
- ✅ **Position similarity checking** - Check for duplicate positions
- ✅ **Embedding storage** - Store 768-dim embeddings for all profile types
- ✅ **Vector operations** - Cosine similarity, nearest neighbor search

**Example**: `TeamMatcher.match_to_team()` uses Weaviate to find similar teams

### Current Implementation Status

**Teams & Interviewers**:
- ✅ **PostgreSQL**: Stored via API routes (`/api/teams`, `/api/interviewers`)
- ⚠️ **Weaviate**: Should also store embeddings (for matching), but currently only used via KnowledgeGraph
- **Note**: API routes use PostgreSQL directly, not KnowledgeGraph. For matching, teams/interviewers need embeddings in Weaviate.

**Candidates**:
- ✅ **Weaviate**: Stored via KnowledgeGraph (embeddings + metadata)
- ⚠️ **PostgreSQL**: Not yet stored (will be added for pipeline tracking)

**Positions**:
- ⏳ **PostgreSQL**: Will be stored (Phase 3)
- ⏳ **Weaviate**: Will store embeddings (Phase 3)

### Architecture Decision: Why Both?

1. **PostgreSQL for Relational Data**:
   - Teams have `member_ids` (array of interviewer IDs)
   - Interviewers have `team_id` (foreign key)
   - Positions have `team_id` (foreign key)
   - Need ACID transactions for data consistency
   - Need company_id filtering for multi-tenancy
   - Need complex queries (JOINs, aggregations)

2. **Weaviate for Similarity Search**:
   - Fast vector similarity search (cosine similarity)
   - Find similar teams for candidate matching
   - Find similar interviewers for candidate matching
   - Position similarity checking (avoid duplicates)
   - Optimized for embedding operations

3. **Dual Storage Pattern**:
   - PostgreSQL = Source of truth for relational data
   - Weaviate = Embeddings for similarity/matching
   - Both are needed: PostgreSQL for CRUD, Weaviate for matching

### Future: Sync Between Databases

**When creating/updating teams/interviewers**:
1. Save to PostgreSQL (via API routes) ✅
2. Also save to Weaviate (via KnowledgeGraph) for embeddings ⚠️ **TODO**

**When creating/updating positions** (Phase 3):
1. Save to PostgreSQL (relational data)
2. Save to Weaviate (embeddings for similarity checking)

---

## Dependencies

- **PostgreSQL**: Local Docker (via docker-compose)
  - Connection: `postgresql://postgres:postgres@localhost:5432/recruiting_db`
  - Persistent volume: `postgres_data`
  - **Used for**: Teams, interviewers, positions, conversations, pipeline stages
- **Weaviate**: Local Docker (via docker-compose)
  - Connection: `http://localhost:8080`
  - Persistent volume: `weaviate_data`
  - **Used for**: Embeddings for all 4 profile types (candidates, teams, interviewers, positions)
- Existing knowledge graph (needs modification for company_id)
- Existing embedding system (for position similarity)
- Existing Grok API client (needs conversation methods)
- Existing matching algorithms (team, interviewer)
- Existing phone screen system (needs pipeline integration)
- PostgreSQL client library (psycopg2)

---

## Success Criteria

✅ All entities support `company_id` and filter correctly
✅ Grok position creation works end-to-end
✅ Position similarity checking suggests duplicates when appropriate
✅ Pipeline tracking records all stage transitions
✅ Candidate filtering by stage/position works
✅ All APIs return data filtered by company_id
✅ Pipeline ends at team/interviewer matching
✅ All tests pass

---

## File Structure After Demo

```
backend/
├── database/
│   ├── knowledge_graph.py (MODIFIED - company_id support)
│   ├── kg_crud.py (MODIFIED - company_id filtering)
│   └── weaviate_schema.py (MODIFIED - company_id in metadata)
├── orchestration/
│   ├── company_context.py (NEW)
│   ├── pipeline_tracker.py (NEW)
│   └── position_creator.py (NEW)
├── matching/
│   └── position_matcher.py (NEW)
├── integrations/
│   └── grok_api.py (MODIFIED - conversation methods)
├── interviews/
│   └── phone_screen_interviewer.py (MODIFIED - pipeline updates)
├── matching/
│   └── team_matcher.py (MODIFIED - pipeline updates)
├── api/
│   ├── routes.py (MODIFIED - company/position/candidate endpoints)
│   └── models.py (MODIFIED - new request/response models)
└── datasets/
    └── sample_positions.py (MODIFIED - distribution flags)

scripts/
└── migrate_to_multi_tenant.py (NEW)

tests/
├── test_multi_tenancy.py (NEW)
├── test_position_creation.py (NEW)
└── test_pipeline_tracking.py (NEW)
```

---

## Checklist

### PostgreSQL Setup & Multi-Tenancy Foundation
- [x] Create PostgreSQL client with connection pooling ✅
- [x] Create database tables (teams, interviewers) ✅
- [ ] Create database tables (companies, conversations, pipeline_stages, position_distribution)
- [x] Add `company_id` to knowledge graph CRUD methods ✅
- [x] Add `company_id` filtering to all queries ✅
- [x] Update Weaviate schema to include `company_id` ✅
- [x] Create `CompanyContext` class ✅
- [ ] Create migration script
- [ ] Migrate existing sample data

### Phase 1: Teams Management ✅ COMPLETE
- [x] Create `teams` table in PostgreSQL ✅
- [x] Add request/response models ✅
- [x] `GET /api/teams` - List teams ✅
- [x] `POST /api/teams` - Create team ✅
- [x] `GET /api/teams/{team_id}` - Get team details ✅
- [x] `PUT /api/teams/{team_id}` - Update team ✅
- [x] `DELETE /api/teams/{team_id}` - Delete team ✅
- [x] `POST /api/teams/chat/stream` - AI-powered team creation chat ✅
- [x] Frontend: Teams list page ✅
- [x] Frontend: Create/edit team forms with AI chat ✅
- [x] Frontend: Delete team with confirmation ✅

### Phase 2: Interviewers Management ✅ COMPLETE
- [x] Create `interviewers` table in PostgreSQL ✅
- [x] Add foreign key to teams ✅
- [x] Add request/response models ✅
- [x] `GET /api/interviewers` - List interviewers ✅
- [x] `POST /api/interviewers` - Create interviewer ✅
- [x] `GET /api/interviewers/{interviewer_id}` - Get interviewer details ✅
- [x] `PUT /api/interviewers/{interviewer_id}` - Update interviewer ✅
- [x] `DELETE /api/interviewers/{interviewer_id}` - Delete interviewer ✅
- [x] `POST /api/interviewers/chat/stream` - AI-powered interviewer creation chat ✅
- [x] Frontend: Interviewers list page ✅
- [x] Frontend: Create/edit interviewer forms with AI chat ✅
- [x] Frontend: Table truncation with tooltips ✅
- [x] Frontend: Auto-switch to form tab on completion ✅

### Phase 2.5: Embeddings Visualization & Graph ✅ COMPLETE
- [x] `GET /api/teams/{team_id}/embedding` - Get team embedding ✅
- [x] `GET /api/interviewers/{interviewer_id}/embedding` - Get interviewer embedding ✅
- [x] `POST /api/teams/{team_id}/generate-embedding` - Generate team embedding ✅
- [x] `POST /api/interviewers/{interviewer_id}/generate-embedding` - Generate interviewer embedding ✅
- [x] `GET /api/embeddings/graph` - Get embeddings with 3D positions ✅
- [x] `GET /api/embeddings/{profile_type}/{profile_id}/similar` - Cross-type similarity search ✅
- [x] `GET /api/weaviate/schema/status` - Schema status endpoint ✅
- [x] `POST /api/weaviate/schema/create` - Manual schema creation ✅
- [x] `POST /api/embeddings/sync` - Sync embeddings endpoint ✅
- [x] Frontend: Team embedding dialog with full vector display ✅
- [x] Frontend: Interviewer embedding dialog with full vector display ✅
- [x] Frontend: View/Generate embedding buttons on teams page ✅
- [x] Frontend: View/Generate embedding buttons on interviewers page ✅
- [x] Frontend: Graph page with 3D visualization (`/graph`) ✅
- [x] Frontend: Node click to view details and similar profiles ✅
- [x] Frontend: Search and filters on graph page ✅
- [x] Frontend: Auto-zoom to filtered nodes ✅
- [x] Frontend: Cross-type similarity search in node dialog ✅
- [x] Frontend: Advanced filters (type, similarity, search, sort) ✅
- [x] Fixed Weaviate connection issues (gRPC fallback) ✅
- [x] Fixed Weaviate cluster mode (single-node setup) ✅
- [x] Fixed Weaviate schema creation and detection ✅
- [x] Fixed React Three Fiber compatibility (switched to react-force-graph-3d) ✅

### Phase 3: Position Creation ✅ COMPLETE - 7 hours
- [x] Create `positions` table in PostgreSQL ✅
- [x] Create `conversations` table in PostgreSQL ✅
- [x] Create `position_distribution` table ✅
- [x] Implement Grok conversation management (store in PostgreSQL) ✅
- [x] Implement position data extraction ✅
- [x] Implement similarity checking ✅
- [x] Add distribution flags (store in PostgreSQL) ✅
- [x] `POST /api/positions/chat/stream` - Streaming Grok position creation chat ✅
- [x] `GET /api/positions` - List positions ✅
- [x] `GET /api/positions/{position_id}` - Get position details ✅
- [x] `PUT /api/positions/{position_id}` - Update position ✅
- [x] `DELETE /api/positions/{position_id}` - Delete position ✅
- [x] `POST /api/positions/check-similarity` - Check for similar positions ✅
- [x] `GET /api/positions/{position_id}/embedding` - Get position embedding ✅
- [x] `POST /api/positions/{position_id}/generate-embedding` - Generate position embedding ✅
- [x] Frontend: Grok chat interface (position creation) ✅
- [x] Frontend: Position list page with search ✅
- [x] Frontend: Edit position dialog with chat interface ✅
- [x] Frontend: Similar positions warning before creation ✅
- [x] Frontend: Auto-create on second click after similarity warning ✅
- [x] Frontend: Position embedding dialog ✅
- [x] Frontend: Graph page shows position embeddings ✅
- [x] Frontend: Node details dialog supports positions ✅
- [x] Fixed delete position error (204 No Content handling) ✅
- [x] Fixed Weaviate connection errors ✅

### Phase 4: Candidate Storage & CRUD
- [ ] Create `candidates` table in PostgreSQL
- [ ] Migrate candidates to dual storage (PostgreSQL + Weaviate)
- [ ] `GET /api/candidates` - List candidates
- [ ] `GET /api/candidates/{candidate_id}` - Get candidate details
- [ ] `POST /api/candidates` - Create candidate
- [ ] `PUT /api/candidates/{candidate_id}` - Update candidate
- [ ] `DELETE /api/candidates/{candidate_id}` - Delete candidate
- [ ] Update outbound gathering to save to PostgreSQL
- [ ] Frontend: Candidate list page
- [ ] Frontend: Candidate details page

### Phase 5: Pipeline Tracking
- [ ] Create `pipeline_stages` table in PostgreSQL
- [ ] Create `PipelineTracker` class
- [ ] Implement stage transitions
- [ ] Store pipeline history
- [ ] Add pipeline methods to knowledge graph
- [ ] Integrate with phone screen system
- [ ] Integrate with matching system

### APIs
- [ ] Company info/stats endpoints
- [x] Teams management endpoints ✅
- [x] Interviewers management endpoints ✅
- [x] Position management endpoints (with Grok) ✅
- [ ] Candidate CRUD endpoints (Phase 4)
- [ ] Candidate pipeline endpoints (Phase 5)
- [ ] Candidate operations endpoints (Phase 6)
- [ ] Update outbound gathering endpoint

### Testing
- [x] Test teams endpoints ✅
- [x] Test interviewers endpoints ✅
- [x] Test position endpoints ✅
- [x] Test Grok position creation ✅
- [x] Test position similarity checking ✅
- [ ] Test company_id isolation
- [ ] Test pipeline tracking
- [ ] Test all API endpoints
- [ ] End-to-end flow testing

## Notes

- **PostgreSQL**: Local Docker with persistent volume (same as Weaviate)
  - Connection string: `postgresql://postgres:postgres@localhost:5432/recruiting_db`
  - Data persists in Docker volume `postgres_data`
- **Weaviate**: Local Docker with persistent volume
  - Connection: `http://localhost:8080`
  - Data persists in Docker volume `weaviate_data`
  - **Cluster mode disabled** for single-node setup ✅
  - **gRPC fallback to HTTP** for robust connections ✅
- Hardcode `company_id: "xai"` everywhere for demo
- No actual authentication needed (assume single user)
- Distribution flags are stored but not functional
- Pipeline ends at team/interviewer matching
- All existing functionality must continue to work with company_id filtering
- Both databases start via `docker-compose up -d`

---

## 🎯 Next Steps

### Immediate Next Step: Phase 4 - Candidate Storage & CRUD

**What to build next:**
1. **Candidates table** in PostgreSQL
2. **Dual storage migration** (move candidates from Weaviate-only to PostgreSQL + Weaviate)
3. **Candidate CRUD APIs** (list, get, create, update, delete)
4. **Frontend candidate list and details pages**

**Why this is next:**
- Foundation is complete: Teams ✅, Interviewers ✅, Positions ✅, Embeddings ✅
- Candidates currently only in Weaviate - need PostgreSQL for pipeline tracking
- Enables Phase 5 (Pipeline Tracking) and Phase 6 (Pipeline Operations)
- Natural progression: positions → candidates → pipeline

**Estimated time**: 2 hours (1 hour backend + 1 hour frontend)

**Key deliverables:**
- Candidates table with company_id filtering
- Full CRUD APIs for candidates
- Dual storage pattern (PostgreSQL for data, Weaviate for embeddings)
- Frontend candidate management UI

**After Phase 4, then:**
- **Phase 5**: Pipeline Tracking (2.5 hours) - Track candidate progress through stages
- **Phase 6**: Candidate Pipeline Operations (1.5 hours) - Phone screen and matching integration
- **Phase 7**: Company Dashboard (1 hour) - Stats and overview

