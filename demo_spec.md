# Grok Recruiting Platform - Demo Specification

## Overview

**Grok Recruiting** is a multi-tenant recruiting platform that automates candidate discovery, phone screening, and matching using AI. For the demo, we hardcode **xAI** as the single tenant.

## Core Concept

Companies get a Grok Recruiting account with:
- Their own interface with full ACLs (hardcoded for demo)
- Their own X handle for outbound recruiting (hardcoded for demo)
- Ability to manage teams, interviewers, positions, and track candidates
- AI-powered position creation via Grok LLM
- Automated candidate pipeline tracking

---

## 1. Multi-Tenant Architecture

### Tenant Model (Hardcoded for Demo)

**Single Tenant: xAI**
- `company_id`: `"xai"`
- `company_name`: `"xAI"`
- `x_handle`: `"xai"` (hardcoded)
- `x_api_credentials`: Use existing X API credentials

### Data Isolation

All entities must include `company_id`:
- Teams: `company_id: "xai"`
- Positions: `company_id: "xai"`
- Candidates: `company_id: "xai"` (when gathered for xAI)
- Interviewers: `company_id: "xai"`

**CRITICAL**: All queries must filter by `company_id` to ensure data isolation.

---

## 2. Company Interface Features

### 2.1 Teams Management
- **Add Team**: Create new team profiles
- **View Teams**: List all teams with member count, open positions
- **Edit Team**: Update team needs, expertise, stack
- **Team Details**: View team members, open positions, hiring priorities

### 2.2 Interviewers Management
- **Add Interviewer**: Create interviewer profiles, assign to team
- **View Interviewers**: List all interviewers by team
- **Edit Interviewer**: Update expertise, interview style, specializations
- **Interviewer Details**: View success rates, cluster performance

### 2.3 Position Management

#### Position Creation Flow (Grok-Powered)

**Step 1: Grok Conversation**
- User clicks "Create New Position"
- Grok asks questions via conversational interface:
  - "What role are you looking to fill?"
  - "What are the must-have technical skills?"
  - "What's the experience level? (Junior/Mid/Senior/Staff)"
  - "What domains does this role cover?"
  - "What are the key responsibilities?"
  - "What's the priority? (high/medium/low)"

**Step 2: Similarity Check**
- After Grok extracts requirements, check for similar existing positions
- Use embedding similarity (existing `RecruitingKnowledgeGraphEmbedder`)
- If similarity > 0.85: Suggest using existing position
- If similarity < 0.85: Proceed with creation

**Step 3: Position Creation**
- Create position profile with extracted data
- Assign to team (from conversation or default)
- Set `company_id: "xai"`
- Set `status: "open"`

**Step 4: Distribution Options**
- **Post to X**: Store flag `post_to_x: true` (no functionality yet)
- **Make Available to Grok**: Store flag `available_to_grok: true` (no functionality yet)
- User can choose both, one, or neither

#### Position Tracking
- **View All Positions**: List with status (open, in-progress, on-hold, filled)
- **Position Details**: 
  - Full requirements, must-haves, nice-to-haves
  - Candidates in pipeline (by stage)
  - Team assigned
  - Created date, priority
- **Edit Position**: Update requirements, status, priority
- **Close Position**: Mark as filled or cancelled

### 2.4 Candidate Tracking

#### Pipeline Stages

Candidates progress through stages:
1. **Gathered** - Found via outbound gathering (X, GitHub, arXiv)
2. **Phone Screen Scheduled** - Phone screen call scheduled
3. **Phone Screen Completed** - Call completed, decision made
4. **Matched to Team** - Team matching completed
5. **Matched to Interviewer** - Interviewer matching completed
6. **Rejected** - Candidate rejected at any stage
7. **Accepted** - Candidate accepted (future: offer extended)

#### Candidate Dashboard
- **View All Candidates**: List with current stage, position(s) applied to
- **Filter by Stage**: Show candidates at specific pipeline stage
- **Filter by Position**: Show candidates for specific position
- **Candidate Details**:
  - Full profile (skills, experience, domains, expertise level)
  - Source data (X posts, GitHub repos, arXiv papers)
  - Phone screen results (if completed)
  - Match results (team, interviewer)
  - Pipeline history (stage transitions, timestamps)
  - Current positions in pipeline

---

## 3. Candidate Interface

### Candidate View
- **Profile Display**: All gathered information in clean interface
  - Basic info (name, skills, experience, domains)
  - X profile summary
  - GitHub summary
  - arXiv research summary
  - Phone screen results (if completed)
- **Pipeline Status**: 
  - List of positions candidate is in pipeline for
  - Current stage for each position
  - Match results (team, interviewer) if matched
- **Timeline**: History of stage transitions

---

## 4. Technical Architecture

### 4.1 Storage Layer

#### PostgreSQL (Non-Graph Data)
- **Purpose**: Store relational data (companies, pipeline tracking, conversations, etc.)
- **Setup**: Local Docker with persistent volume
- **Connection**: `postgresql://postgres:postgres@localhost:5432/recruiting_db`
- **Persistence**: Data stored in Docker volume `postgres_data`
- **Tables** (to be created):
  - `companies` - Company profiles
  - `conversations` - Grok position creation conversations
  - `pipeline_stages` - Candidate pipeline stage history
  - `position_distribution` - Position distribution flags
  - Other relational data

#### Weaviate (Vector Database)
- **Purpose**: Store embeddings and enable similarity search
- **Setup**: Local Docker with persistent volume
- **Connection**: `http://localhost:8080`
- **Persistence**: Data stored in Docker volume `weaviate_data`
- **Collections**: Candidate, Team, Interviewer, Position embeddings

**Both databases persist data across container restarts via Docker volumes.**

### 4.2 Data Model Changes

#### Add `company_id` to All Entities

**Teams**:
```python
{
    "id": "team_001",
    "company_id": "xai",  # NEW
    "name": "LLM Inference Team",
    # ... rest of fields
}
```

**Positions**:
```python
{
    "id": "position_001",
    "company_id": "xai",  # NEW
    "title": "Senior LLM Inference Engineer",
    "company": "xAI",  # Already exists
    # ... rest of fields
}
```

**Candidates**:
```python
{
    "id": "candidate_001",
    "company_id": "xai",  # NEW - which company gathered this candidate
    "name": "John Doe",
    # ... rest of fields
}
```

**Interviewers**:
```python
{
    "id": "interviewer_001",
    "company_id": "xai",  # NEW
    "team_id": "team_001",
    # ... rest of fields
}
```

#### Add Pipeline Tracking Fields

**Candidates**:
```python
{
    # ... existing fields
    "pipeline_stage": "matched_to_interviewer",  # NEW
    "pipeline_history": [  # NEW
        {
            "stage": "gathered",
            "timestamp": "2025-12-07T10:00:00Z",
            "position_id": "position_001"
        },
        {
            "stage": "phone_screen_completed",
            "timestamp": "2025-12-07T11:00:00Z",
            "position_id": "position_001",
            "decision": "pass"
        },
        # ... more stages
    ],
    "active_positions": ["position_001", "position_002"],  # NEW
    "match_results": {  # NEW
        "position_001": {
            "team_id": "team_001",
            "team_match_score": 0.92,
            "interviewer_id": "interviewer_001",
            "interviewer_match_score": 0.88
        }
    }
}
```

**Positions**:
```python
{
    # ... existing fields
    "post_to_x": False,  # NEW - flag for X posting
    "available_to_grok": True,  # NEW - flag for Grok availability
    "candidates_by_stage": {  # NEW - for tracking
        "gathered": ["candidate_001", "candidate_002"],
        "phone_screen_completed": ["candidate_003"],
        "matched_to_team": ["candidate_004"],
        "matched_to_interviewer": ["candidate_005"]
    }
}
```

### 4.2 API Endpoints

#### Company Management
- `GET /api/company/info` - Get company info (xAI for demo)
- `GET /api/company/stats` - Get company stats (positions, candidates, teams)

#### Teams
- `GET /api/teams` - List all teams (filtered by company_id)
- `POST /api/teams` - Create team
- `GET /api/teams/{team_id}` - Get team details
- `PUT /api/teams/{team_id}` - Update team
- `GET /api/teams/{team_id}/positions` - Get team's positions
- `GET /api/teams/{team_id}/members` - Get team members

#### Interviewers
- `GET /api/interviewers` - List all interviewers (filtered by company_id)
- `POST /api/interviewers` - Create interviewer
- `GET /api/interviewers/{interviewer_id}` - Get interviewer details
- `PUT /api/interviewers/{interviewer_id}` - Update interviewer

#### Positions (Grok-Powered Creation)
- `POST /api/positions/create-conversation` - Start Grok conversation for position creation
- `POST /api/positions/conversation/{conversation_id}/message` - Send message to Grok
- `POST /api/positions/conversation/{conversation_id}/finalize` - Finalize position creation
- `GET /api/positions` - List all positions (filtered by company_id)
- `GET /api/positions/{position_id}` - Get position details
- `PUT /api/positions/{position_id}` - Update position
- `PUT /api/positions/{position_id}/distribution` - Update distribution flags (post_to_x, available_to_grok)
- `GET /api/positions/{position_id}/candidates` - Get candidates in pipeline for position
- `GET /api/positions/{position_id}/similar` - Check for similar positions (for suggestion)

#### Candidates
- `GET /api/candidates` - List all candidates (filtered by company_id)
- `GET /api/candidates?stage={stage}` - Filter by pipeline stage
- `GET /api/candidates?position_id={position_id}` - Filter by position
- `GET /api/candidates/{candidate_id}` - Get candidate details
- `GET /api/candidates/{candidate_id}/pipeline` - Get candidate pipeline status
- `PUT /api/candidates/{candidate_id}/stage` - Update pipeline stage
- `POST /api/candidates/{candidate_id}/phone-screen` - Trigger phone screen
- `POST /api/candidates/{candidate_id}/match` - Trigger matching (team + interviewer)

#### Outbound Gathering
- `POST /api/outbound/gather` - Gather candidate from X/GitHub/arXiv
  - Automatically sets `company_id: "xai"`

### 4.3 Grok Position Creation Flow

#### Conversation State Management

**Conversation Object**:
```python
{
    "conversation_id": "conv_123",
    "company_id": "xai",
    "messages": [
        {"role": "assistant", "content": "What role are you looking to fill?"},
        {"role": "user", "content": "Senior LLM Inference Engineer"},
        # ... more messages
    ],
    "extracted_data": {
        "title": "Senior LLM Inference Engineer",
        "must_haves": ["CUDA", "C++", "PyTorch"],
        # ... partial extraction
    },
    "status": "in_progress" | "ready_to_create" | "created"
}
```

#### Grok Prompt for Position Creation

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
```

#### Similarity Check Logic

1. Generate embedding for new position requirements
2. Search existing positions (filtered by `company_id: "xai"`)
3. Calculate similarity scores
4. If max similarity > 0.85: Return similar position(s) for suggestion
5. If max similarity < 0.85: Proceed with creation

---

## 5. UI/UX Flows

### 5.1 Position Creation Flow

1. User clicks "Create New Position"
2. Grok conversation interface opens
3. User chats with Grok about the position
4. Grok asks clarifying questions
5. After sufficient info gathered:
   - System checks for similar positions
   - If similar found: Show suggestion modal
   - User can use existing or create new
6. If creating new:
   - Show extracted position data for review
   - User confirms or edits
   - Position created
7. Distribution options shown:
   - Toggle "Post to X"
   - Toggle "Make Available to Grok"
8. Position appears in positions list

### 5.2 Candidate Pipeline View

1. User navigates to "Candidates" dashboard
2. See list of all candidates with:
   - Name, skills, experience
   - Current pipeline stage
   - Position(s) they're in pipeline for
   - Match scores (if matched)
3. Filter by:
   - Stage (dropdown)
   - Position (dropdown)
   - Skills (search)
4. Click candidate → See full details:
   - Complete profile
   - Source data (X, GitHub, arXiv)
   - Phone screen transcript/results
   - Match results (team, interviewer)
   - Pipeline timeline

### 5.3 Position Tracking View

1. User navigates to "Positions" dashboard
2. See list of all positions with:
   - Title, team, status
   - Candidate count by stage
   - Priority, created date
3. Click position → See details:
   - Full requirements
   - Candidates in pipeline (grouped by stage)
   - Team assigned
   - Distribution flags

---

## 6. Demo Scope

### What's Included

✅ Multi-tenant architecture (hardcoded to xAI)
✅ Teams and interviewers management
✅ Grok-powered position creation
✅ Position similarity checking
✅ Position distribution flags (stored, not functional)
✅ Candidate pipeline tracking
✅ Candidate interface
✅ Team and interviewer matching (end point)

### What's NOT Included (Future)

❌ Actual X posting functionality
❌ Grok availability functionality
❌ Interview scheduling
❌ Offer management
❌ Application submission flow
❌ Multi-company support (beyond hardcoding)

---

## 7. Success Criteria

✅ Company can create teams and interviewers
✅ Company can create positions via Grok conversation
✅ System suggests similar positions when appropriate
✅ Company can track candidates through pipeline stages
✅ Company can see candidate details and match results
✅ Candidates can view their profile and pipeline status
✅ All data properly isolated by company_id
✅ Pipeline ends at team/interviewer matching

---

## 8. Frontend Architecture

### 8.1 Tech Stack

**Framework**: Next.js 14+ (App Router)
- TypeScript/TSX
- Server Components + Client Components
- API Routes for backend integration

**UI Library**: shadcn/ui
- Unstyled, accessible components
- Built on Radix Primitives
- Full TypeScript support
- Highly customizable

**Styling**:
- Tailwind CSS (via shadcn)
- Dark mode by default (xAI/Grok inspired)
- Custom color palette matching xAI aesthetic

**State Management**:
- React Server Components (default)
- React Query / TanStack Query (for client-side data fetching)
- Zustand (for global UI state if needed)

**Additional Libraries**:
- `lucide-react` - Icons (matches xAI style)
- `framer-motion` - Smooth animations
- `date-fns` - Date formatting
- `zod` - Schema validation (matches backend)

### 8.2 Design System (xAI/Grok Inspired)

**Color Palette**:
- **Background**: Deep dark (`#000000` or `#0a0a0a`)
- **Surface**: Slightly lighter dark (`#1a1a1a` or `#141414`)
- **Primary**: xAI brand colors (if available) or clean blue/green
- **Text**: High contrast white/light gray (`#ffffff`, `#e5e5e5`)
- **Accents**: Subtle highlights for interactive elements
- **Borders**: Very subtle gray (`#2a2a2a`)

**Typography**:
- Clean, modern sans-serif (Inter, System UI, or similar)
- Clear hierarchy (headings, body, captions)
- Generous spacing

**Components Style**:
- Minimalist, clean interfaces
- Subtle shadows/borders
- Smooth transitions
- Focus on content over decoration
- Chat-like interface for Grok conversations
- Card-based layouts for data display

**Key Design Principles**:
1. **Dark-first**: Built for dark mode (xAI aesthetic)
2. **Minimalist**: Clean, uncluttered interfaces
3. **Content-focused**: Data and functionality over decoration
4. **Smooth interactions**: Subtle animations, hover states
5. **Accessible**: High contrast, clear typography

### 8.3 Frontend Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout (dark theme)
│   ├── page.tsx            # Dashboard/home
│   ├── (company)/          # Company routes
│   │   ├── teams/          # Teams management
│   │   ├── interviewers/  # Interviewers management
│   │   ├── positions/     # Positions management
│   │   └── candidates/    # Candidate tracking
│   └── api/               # API routes (proxy to backend)
├── components/
│   ├── ui/                # shadcn components
│   ├── company/           # Company-specific components
│   ├── candidates/        # Candidate components
│   ├── positions/         # Position components
│   └── grok-chat/         # Grok conversation interface
├── lib/
│   ├── api.ts             # API client
│   ├── utils.ts           # Utilities
│   └── hooks/             # Custom React hooks
├── types/                 # TypeScript types
└── styles/               # Global styles
```

### 8.4 Key Pages/Components

**Dashboard**:
- Overview cards (positions, candidates, teams)
- Recent activity
- Quick actions

**Grok Position Creation**:
- Chat interface (like Grok chat)
- Message bubbles
- Streaming responses (if possible)
- Position preview card

**Candidate Pipeline**:
- Kanban-style board (by stage)
- Candidate cards
- Drag-and-drop (optional)
- Filter/search

**Position Management**:
- List view with filters
- Position cards
- Similar positions modal

**Candidate Details**:
- Tabbed interface
- Profile, source data, pipeline, matches
- Clean data display

### 8.5 npm Packages

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@radix-ui/react-*": "latest",  // shadcn dependencies
    "tailwindcss": "^3.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "lucide-react": "^0.300.0",
    "framer-motion": "^10.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zod": "^3.22.0",
    "date-fns": "^2.30.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0"
  }
}
```

---

---

## 10. Data Migration

For demo, existing sample data needs:
1. Add `company_id: "xai"` to all teams, positions, interviewers
2. Add `company_id: "xai"` to candidates (when gathered)
3. Add pipeline tracking fields to candidates
4. Add distribution flags to positions

### Database Setup

**PostgreSQL**:
- Database created automatically via Docker Compose
- Run migrations to create tables (companies, conversations, pipeline_stages, etc.)
- Sample data can be loaded via scripts

**Weaviate**:
- Schema created automatically on first connection
- Existing embeddings remain in Docker volume
- Add `company_id` to metadata for all existing entities

---

## 11. Security & ACLs

For demo, hardcode:
- All endpoints require `company_id: "xai"` in context
- All queries filter by `company_id`
- No actual authentication (assume single user = xAI)

Future: Implement proper authentication and authorization.

---

## 12. Infrastructure Setup

### Docker Compose Services

**PostgreSQL**:
- Image: `postgres:16-alpine`
- Port: `5432`
- Volume: `postgres_data` (persistent)
- Database: `recruiting_db`
- User/Password: `postgres/postgres`

**Weaviate**:
- Image: `semitechnologies/weaviate:latest`
- Port: `8080`
- Volume: `weaviate_data` (persistent)
- No authentication (local development)

### Environment Variables

**Backend (.env)**:
```bash
# PostgreSQL (Local Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/recruiting_db

# Weaviate (Local Docker)
WEAVIATE_URL=http://localhost:8080

# API Keys (Grok, X, Vapi, GitHub)
GROK_API_KEY=...
X_API_KEY=...
# ... etc
```

**Frontend (.env.local)**:
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Starting Services

**Backend**:
```bash
docker-compose up -d  # Starts PostgreSQL and Weaviate
uvicorn backend.api.main:app --reload  # Starts FastAPI server
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev  # Starts Next.js dev server on :3000
```

---

## 12. Development Timeline (Feature-by-Feature, Fully Complete Each)

**Approach**: Complete each feature fully (Database → API → Frontend) before moving to the next. This allows for testing and iteration at each step.

### Phase 0: Foundation Setup - 3 hours
**Backend (Vin)**: 1.5 hours
- PostgreSQL client setup
- Connection pooling
- Basic connection testing

**Frontend**: 1.5 hours
- Next.js setup & shadcn integration
- Design system & dark theme (xAI/Grok inspired)
- Basic layout & routing structure

---

### Phase 1: Teams Management (FULLY COMPLETE) - 4 hours

**Step 1: Database (1 hour)**
- Create `teams` table in PostgreSQL
- Add `company_id` column
- Create indexes
- Test table creation

**Step 2: Backend API (1.5 hours)**
- `GET /api/teams` - List teams (filtered by company_id)
- `POST /api/teams` - Create team
- `GET /api/teams/{team_id}` - Get team details
- `PUT /api/teams/{team_id}` - Update team
- Add request/response models
- Test all endpoints

**Step 3: Frontend (1.5 hours)**
- Teams list page
- Create/edit team forms
- API integration
- Test full flow (create → view → edit)

**✅ Feature Complete**: Teams management fully working before moving on

---

### Phase 2: Interviewers Management (FULLY COMPLETE) - 3.5 hours

**Step 1: Database (0.5 hour)**
- Create `interviewers` table in PostgreSQL
- Add `company_id` column
- Foreign key to teams
- Create indexes

**Step 2: Backend API (1.5 hours)**
- `GET /api/interviewers` - List interviewers (filtered by company_id)
- `POST /api/interviewers` - Create interviewer
- `GET /api/interviewers/{interviewer_id}` - Get interviewer details
- `PUT /api/interviewers/{interviewer_id}` - Update interviewer
- Add request/response models
- Test all endpoints

**Step 3: Frontend (1.5 hours)**
- Interviewers list page
- Create/edit interviewer forms
- API integration
- Test full flow

**✅ Feature Complete**: Interviewers management fully working before moving on

---

### Phase 3: Position Creation (FULLY COMPLETE) - 7 hours

**Step 1: Database (1 hour)**
- Create `positions` table in PostgreSQL
- Create `conversations` table (for Grok chats)
- Create `position_distribution` table
- Add `company_id` to all
- Create indexes

**Step 2: Backend API (4 hours)**
- Grok conversation management (store in PostgreSQL)
- Position similarity checking
- `POST /api/positions/create-conversation` - Start Grok conversation
- `POST /api/positions/conversation/{conversation_id}/message` - Send message
- `POST /api/positions/conversation/{conversation_id}/finalize` - Finalize creation
- `GET /api/positions` - List positions
- `GET /api/positions/{position_id}` - Get position details
- `PUT /api/positions/{position_id}` - Update position
- `GET /api/positions/{position_id}/similar` - Check for similar positions
- `PUT /api/positions/{position_id}/distribution` - Update distribution flags
- Test all endpoints

**Step 3: Frontend (2 hours)**
- Grok chat interface (position creation)
- Position list page
- Position details page
- Similar positions modal
- Test full flow (Grok conversation → create position → view)

**✅ Feature Complete**: Position creation fully working before moving on

---

### Phase 4: Pipeline Tracking (FULLY COMPLETE) - 5 hours

**Step 1: Database (1 hour)**
- Create `pipeline_stages` table in PostgreSQL
- Add `company_id`, `candidate_id`, `position_id`
- Create indexes for fast queries
- Test table creation

**Step 2: Backend API (2.5 hours)**
- Pipeline tracking system
- `GET /api/candidates?stage={stage}` - Filter by stage
- `GET /api/candidates/{candidate_id}/pipeline` - Get pipeline status
- `PUT /api/candidates/{candidate_id}/stage` - Update pipeline stage
- Integrate with phone screen system (auto-update stage)
- Integrate with matching system (auto-update stage)
- Test all endpoints

**Step 3: Frontend (1.5 hours)**
- Candidate pipeline dashboard (Kanban board)
- Stage filtering
- Pipeline timeline view
- Test full flow (stage transitions)

**✅ Feature Complete**: Pipeline tracking fully working before moving on

---

### Phase 5: Candidate Management (FULLY COMPLETE) - 4 hours

**Step 1: Database (0.5 hour)**
- Update `candidates` table (if needed)
- Ensure `company_id` column exists
- Create indexes for filtering

**Step 2: Backend API (2 hours)**
- `GET /api/candidates` - List candidates (filtered by company_id)
- `GET /api/candidates?position_id={position_id}` - Filter by position
- `GET /api/candidates/{candidate_id}` - Get candidate details
- `POST /api/candidates/{candidate_id}/phone-screen` - Trigger phone screen
- `POST /api/candidates/{candidate_id}/match` - Trigger matching
- Update outbound gathering to set `company_id: "xai"`
- Test all endpoints

**Step 3: Frontend (1.5 hours)**
- Candidate list page
- Candidate details page
- Filter/search functionality
- Test full flow

**✅ Feature Complete**: Candidate management fully working before moving on

---

### Phase 6: Company Dashboard (FULLY COMPLETE) - 2 hours

**Step 1: Database (0.5 hour)**
- Create `companies` table (if not exists)
- Add stats aggregation queries

**Step 2: Backend API (0.5 hour)**
- `GET /api/company/info` - Get company info
- `GET /api/company/stats` - Get stats (positions, candidates, teams)
- `GET /api/positions/{position_id}/candidates` - Get candidates in pipeline

**Step 3: Frontend (1 hour)**
- Dashboard overview page
- Stats cards
- Recent activity feed
- Test full flow

**✅ Feature Complete**: Dashboard fully working

---

### Phase 7: Testing & Polish - 2 hours

**Backend (Vin)**: 1 hour
- End-to-end testing
- Integration testing
- Fix any issues

**Frontend**: 1 hour
- UI polish & animations
- Final tweaks
- Cross-browser testing

**Total Estimated**: 32 hours (feature-by-feature, fully complete each)

