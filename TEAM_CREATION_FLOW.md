# Complete Team Creation Flow: Frontend to Backend

## Overview
The team creation flow supports two methods: **AI-powered chat** (Grok) or **manual form entry**. Both methods ultimately create a team in PostgreSQL and generate embeddings in Weaviate.

---

## 🎯 Flow Diagram

```
User Action
    ↓
[CreateTeamDialog Opens]
    ↓
┌─────────────────┬─────────────────┐
│   Chat Tab      │   Form Tab      │
│  (AI-Powered)   │  (Manual Entry) │
└─────────────────┴─────────────────┘
         ↓                  ↓
    [Grok Chat]      [Form Fields]
         ↓                  ↓
    [Extract Data]   [User Input]
         ↓                  ↓
    [Auto-fill Form]  [Ready to Submit]
         ↓                  ↓
         └──────────┬───────────┘
                    ↓
         [User Clicks "Create Team"]
                    ↓
         [POST /api/teams]
                    ↓
    ┌───────────────────────────────┐
    │      Backend Processing       │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  1. Insert into PostgreSQL     │
    │     - Generate UUID            │
    │     - Add company_id           │
    │     - Set timestamps           │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  2. Store in Weaviate         │
    │     - Generate embedding      │
    │     - Store vector + metadata  │
    └───────────────────────────────┘
                    ↓
         [Return TeamResponse]
                    ↓
    [Frontend: Refresh Teams List]
```

---

## 📱 Frontend Flow

### 1. Dialog Initialization (`CreateTeamDialog.tsx`)

**When dialog opens:**
- Loads saved session from `sessionStorage` (if exists)
  - Chat messages
  - Session ID
  - Form data
  - Chat completion status
- Initializes state:
  - `activeTab`: 'chat' or 'form' (defaults to 'chat')
  - `messages`: Chat history
  - `formData`: Team data object
  - `sessionId`: For maintaining conversation context

**Session Storage Keys:**
- `team_creation_data`: Chat session state
- `team_creation_form`: Form field values

---

### 2. Chat Tab Flow (AI-Powered)

#### Step 2.1: User Types Message
- User enters text in input field
- Presses Enter or clicks Send button
- `handleSendMessage()` is called

#### Step 2.2: Build Request
```typescript
const requestBody = {
  messages: chatMessages.map(m => ({ role: m.role, content: m.content })),
  session_id: sessionId,  // If exists
  current_data: {         // Current form values (for context)
    name: formData.name,
    expertise: formData.expertise,
    // ... other fields
  }
}
```

#### Step 2.3: Stream to Backend
- **Endpoint**: `POST /api/teams/chat/stream`
- **Method**: Server-Sent Events (SSE) streaming
- **Request**: Sent via `fetch()` with streaming response

#### Step 2.4: Handle Streaming Response
```typescript
// Read stream chunk by chunk
const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  // Parse SSE format: "data: {json}\n\n"
  // Update UI with streaming text
  setStreamingMessage(fullMessage);
}
```

#### Step 2.5: Process Final Response
When stream completes:
- **If `is_complete: true`**:
  - Extract `team_data` from response
  - Auto-populate form fields
  - Switch to Form tab automatically
  - Show success message
- **If `is_complete: false`**:
  - Add assistant message to chat
  - Wait for next user input
  - Continue conversation

#### Step 2.6: Save Session
- All chat state saved to `sessionStorage`
- Persists across page refreshes
- Can "Start Over" to clear session

---

### 3. Form Tab Flow (Manual Entry)

#### Step 3.1: User Fills Form
- Direct input into form fields:
  - Team Name (required)
  - Department
  - Expertise (comma-separated)
  - Tech Stack (comma-separated)
  - Domains (comma-separated)
  - Needs/Skills Gaps (comma-separated)
  - Culture (textarea)
  - Work Style (textarea)
  - Hiring Priorities (comma-separated)

#### Step 3.2: Form Validation
- Checks: `formData.name.trim().length > 0`
- Shows error toast if name missing

#### Step 3.3: Parse Comma-Separated Lists
```typescript
const needs = needsInput.split(',').map(s => s.trim()).filter(Boolean);
const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
// ... etc
```

#### Step 3.4: Build Request
```typescript
const teamData: TeamCreateRequest = {
  name: formData.name,
  department: formData.department,
  needs: needs.length > 0 ? needs : undefined,
  expertise: expertise.length > 0 ? expertise : undefined,
  // ... other fields
}
```

---

### 4. Submit Team Creation

#### Step 4.1: Call API
```typescript
createTeamMutation.mutate(teamData);
```

**API Call**: `POST /api/teams`
- **Method**: `apiClient.createTeam(data)`
- **Body**: `TeamCreateRequest` JSON

#### Step 4.2: Handle Success
- Invalidate React Query cache: `queryClient.invalidateQueries({ queryKey: ['teams'] })`
- Show success toast
- Clear session storage
- Reset all state
- Close dialog
- Teams list automatically refreshes

#### Step 4.3: Handle Error
- Show error toast with message
- Keep dialog open
- User can retry

---

## 🔧 Backend Flow

### 1. Chat Streaming Endpoint (`POST /api/teams/chat/stream`)

#### Step 1.1: Receive Request
```python
request: TeamChatRequest = {
  messages: List[ChatMessage],  # Conversation history
  session_id: Optional[str],    # For conversation continuity
  current_data: Optional[TeamCreateRequest]  # Current form values
}
```

#### Step 1.2: Build System Prompt
- Includes instructions for gathering team information
- Adds `current_data` context if provided
- Instructs Grok to ask one question at a time
- Specifies JSON format for completion

#### Step 1.3: Call Grok API
```python
grok = get_grok_client()
url = f"{grok.base_url}/chat/completions"
payload = {
    "model": "grok-4-1-fast-reasoning",
    "messages": messages,  # System + conversation history
    "temperature": 0.7,
    "stream": True  # Enable streaming
}
```

#### Step 1.4: Stream Response
- Uses `httpx.AsyncClient` with streaming
- Parses Grok's SSE format: `"data: {json}\n\n"`
- Yields chunks to frontend as they arrive
- Extracts content from `choices[0].delta.content`

#### Step 1.5: Parse Final Response
- Attempts to extract JSON from final message
- Looks for `team_data` object
- Sets `is_complete: true` if JSON found
- Returns session_id for conversation continuity

#### Step 1.6: Return Streaming Response
```python
# SSE format
yield f"data: {json.dumps({
    'content': chunk,
    'session_id': session_id
})}\n\n"

# Final message
yield f"data: {json.dumps({
    'final': {
        'message': full_message,
        'session_id': session_id,
        'is_complete': True,
        'team_data': parsed_team_data
    }
})}\n\n"
```

---

### 2. Team Creation Endpoint (`POST /api/teams`)

#### Step 2.1: Receive Request
```python
team_data: TeamCreateRequest = {
    name: str,  # Required
    department: Optional[str],
    needs: Optional[List[str]],
    expertise: Optional[List[str]],
    stack: Optional[List[str]],
    domains: Optional[List[str]],
    culture: Optional[str],
    work_style: Optional[str],
    hiring_priorities: Optional[List[str]]
}
```

#### Step 2.2: Get Company Context
```python
company_context = get_company_context()
company_id = company_context.get_company_id()  # Returns "xai"
```

#### Step 2.3: Generate Team ID
```python
team_id = str(uuid.uuid4())
now = datetime.now()
```

#### Step 2.4: Insert into PostgreSQL
```python
postgres = get_postgres_client()

query = """
    INSERT INTO teams (
        id, company_id, name, department, needs, expertise, stack, 
        domains, culture, work_style, hiring_priorities, 
        member_count, member_ids, open_positions, created_at, updated_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) RETURNING *
"""

result = postgres.execute_one(query, (
    team_id,
    company_id,  # "xai"
    team_data.name,
    team_data.department,
    team_data.needs or [],
    team_data.expertise or [],
    team_data.stack or [],
    team_data.domains or [],
    team_data.culture,
    team_data.work_style,
    team_data.hiring_priorities or [],
    0,  # member_count (initial)
    [],  # member_ids (initial)
    [],  # open_positions (initial)
    now,
    now
))
```

**PostgreSQL Table Structure:**
- `id`: UUID (primary key)
- `company_id`: "xai" (for multi-tenancy)
- All team fields (name, department, needs, etc.)
- Arrays stored as PostgreSQL arrays
- Timestamps: `created_at`, `updated_at`

#### Step 2.5: Store in Weaviate (for Embeddings)
```python
try:
    kg = get_knowledge_graph()
    team_dict = {
        'id': result['id'],
        'company_id': result['company_id'],
        'name': result['name'],
        # ... all other fields
    }
    kg.add_team(team_dict)  # Generates embedding and stores in Weaviate
except Exception as e:
    logger.warning(f"Failed to store team in Weaviate (non-critical): {e}")
    # Non-critical: continue even if Weaviate storage fails
```

**What `kg.add_team()` does:**
1. Calls `embedder.embed_team(team_data)` → Generates 768-dim embedding
2. Calls `vector_db.store_team(team_id, embedding, team_data)` → Stores in Weaviate
3. Weaviate stores:
   - Vector: 768-dimensional embedding
   - Metadata: Full team data as JSON
   - UUID: Deterministic UUID based on `Team:{team_id}`

**Weaviate Storage:**
- Collection: `Team`
- Profile ID: `team_id`
- Embedding: 768-dim normalized vector
- Metadata: Full team object with `company_id`

#### Step 2.6: Return Response
```python
return TeamResponse(
    id=result['id'],
    company_id=result['company_id'],
    name=result['name'],
    # ... all fields
    created_at=result['created_at'],
    updated_at=result['updated_at']
)
```

---

## 🔄 Data Flow Summary

### Dual Storage Pattern

**PostgreSQL (Source of Truth):**
- Stores relational data
- Used for CRUD operations
- Supports queries, joins, aggregations
- Company_id filtering
- Foreign key relationships

**Weaviate (Embeddings):**
- Stores 768-dim embeddings
- Used for similarity search
- Used for matching operations
- Enables team-candidate matching
- Enables cross-type similarity search

### Embedding Generation

**When team is created:**
1. Team data saved to PostgreSQL ✅
2. `kg.add_team()` called
3. `embedder.embed_team(team_data)` generates embedding
4. Embedding stored in Weaviate with metadata
5. Team now available for:
   - Similarity search
   - Candidate matching
   - Graph visualization

**Embedding Model:**
- Model: MPNet (768 dimensions)
- Normalized vectors
- Generated from: name, department, expertise, stack, domains, needs, culture, work_style, hiring_priorities

---

## 🎨 User Experience Flow

### Chat Method:
1. User opens dialog → Chat tab active
2. Grok asks: "What's the name of the team you'd like to create?"
3. User responds → Grok asks next question
4. Conversation continues until all info gathered
5. Grok returns JSON with `team_data`
6. Form auto-populates
7. Dialog switches to Form tab
8. User reviews and clicks "Create Team"
9. Team created → Dialog closes → Teams list refreshes

### Form Method:
1. User opens dialog → Switches to Form tab
2. User manually fills all fields
3. User clicks "Create Team"
4. Team created → Dialog closes → Teams list refreshes

### Hybrid Method:
1. User starts in Chat tab
2. Gets some info from Grok
3. Switches to Form tab
4. Manually edits/completes fields
5. Submits form
6. Team created

---

## 🔍 Key Implementation Details

### Session Persistence
- **Chat state**: Saved to `sessionStorage` after each message
- **Form state**: Saved to `sessionStorage` on every change
- **Survives**: Page refreshes, tab switches
- **Cleared**: On successful team creation or "Start Over"

### Error Handling
- **Chat errors**: Show toast, keep dialog open, allow retry
- **Weaviate errors**: Logged as warning, non-critical (PostgreSQL is source of truth)
- **PostgreSQL errors**: Return 500, show error toast

### Embedding Generation
- **Automatic**: Happens on team creation
- **Synchronous**: Blocking operation (but non-critical if fails)
- **Model**: MPNet (768-dim)
- **Normalized**: Vectors are L2-normalized

### Company Context
- **Hardcoded**: `company_id = "xai"` for demo
- **Filtering**: All queries filtered by company_id
- **Isolation**: Multi-tenant ready (just need auth)

---

## 📊 Database Operations

### PostgreSQL Insert
```sql
INSERT INTO teams (
    id, company_id, name, department, needs, expertise, stack, 
    domains, culture, work_style, hiring_priorities, 
    member_count, member_ids, open_positions, created_at, updated_at
) VALUES (
    'uuid', 'xai', 'Team Name', 'Engineering', 
    ARRAY['need1', 'need2'], ARRAY['exp1'], ARRAY['tech1'], 
    ARRAY['domain1'], 'culture text', 'work style', ARRAY['priority1'],
    0, ARRAY[]::uuid[], ARRAY[]::uuid[], NOW(), NOW()
) RETURNING *;
```

### Weaviate Storage
```python
# Generated UUID: uuid5("Team:{team_id}")
# Vector: [0.123, -0.456, ...] (768 dimensions)
# Metadata: {
#   "profile_id": "team_id",
#   "company_id": "xai",
#   "name": "Team Name",
#   ... all other fields
# }
```

---

## ✅ Success Criteria

After team creation:
- ✅ Team exists in PostgreSQL with `company_id = "xai"`
- ✅ Team has embedding in Weaviate (if storage succeeded)
- ✅ Team appears in teams list page
- ✅ Team can be viewed, edited, deleted
- ✅ Team embedding can be viewed in dialog
- ✅ Team appears in graph visualization (if embedding exists)
- ✅ Team can be used for candidate matching

---

## 🐛 Error Scenarios

### Chat Streaming Fails
- **Frontend**: Shows error toast, keeps dialog open
- **User**: Can retry or switch to form tab

### PostgreSQL Insert Fails
- **Backend**: Returns 500 error
- **Frontend**: Shows error toast, keeps dialog open
- **User**: Can retry with same data

### Weaviate Storage Fails
- **Backend**: Logs warning, continues (non-critical)
- **Team**: Still created in PostgreSQL
- **Impact**: Team won't have embedding (can generate later)
- **User**: Can manually generate embedding via button

---

## 🔄 State Management

### Frontend State
- **React Query**: Manages teams list cache
- **Local State**: Dialog state, form data, chat messages
- **Session Storage**: Persists across refreshes

### Backend State
- **No state**: Stateless API
- **Session ID**: Used for Grok conversation continuity
- **Database**: PostgreSQL and Weaviate are state stores

---

This completes the full team creation flow from user interaction to database storage! 🎉

