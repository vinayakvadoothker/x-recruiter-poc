# Ishaan's Pivot Plan: Phone Screen Interface + Outbound Gathering

## Your Role: Application Layer + Outbound Data Gathering

**Focus**: Build phone screen conversation interface, outbound info gathering from 3 sources (X, GitHub, arXiv), and ensure data matches exact schema.

**Timeline**: 16-25 hours total (reduced from 18-28 due to LinkedIn removal)

**Status**: Phone Screen Interface ✅ COMPLETE | Outbound Gathering ✅ COMPLETE (3/3 sources done, individual gathering only) | Profile Input ❌ NOT NEEDED

---

## 📊 Progress Summary

### ✅ COMPLETED (11-13 hours)
- **Phase 1: Phone Screen Interface** - ✅ DONE (ENHANCED)
  - `backend/interviews/phone_screen_interviewer.py` - Created and working with Vapi
  - API endpoint `POST /api/v1/phone-screen` - Working
  - Live test successful (real phone calls working)
  - Integrated with decision engine and knowledge graph
  - **ENHANCED**: Hyper-personalized system prompts based on candidate background (arXiv papers, GitHub repos, X posts)
  - **ENHANCED**: Hard-hitting technical questions (deep-dive on research, architecture, trade-offs)
  - **ENHANCED**: Deep analysis extraction (not just skills - full technical assessment, red flags, insights)
  - **ENHANCED**: Comprehensive decision reasoning with examples and concerns

- **Phase 3: X API Gathering** - ✅ DONE
  - `backend/integrations/x_api.py` - Full X API client implemented
  - `backend/orchestration/outbound_gatherer.py` - Created with `gather_from_x()`
  - Grok-based extraction for accurate skills/domains/experience
  - 1520 datapoints gathered per candidate (exceeds 500 target)
  - `gather_and_save_from_x()` - Automatically saves cleaned profile to knowledge graph
  - All tests passing

- **Phase 3.5: X DM Follow-Up Service** - ✅ DONE
  - `backend/integrations/x_dm_service.py` - Full DM service implemented
  - OAuth 1.0a support for DM sending (requires app permissions)
  - DM templates for resume, arXiv ID, GitHub, LinkedIn URL, phone, email
  - Grok-based parsing of DM responses (works with natural language)
  - Resume extraction as plain text (not URLs)
  - Integration with `outbound_gatherer` to auto-request missing fields
  - Test scripts for simulated responses
  - **Note**: DM sending requires X API app permissions. Parsing works with any text.

- **Phase 4: arXiv Gathering** - ✅ DONE
  - `backend/integrations/arxiv_api.py` - Full arXiv API client implemented
  - Support for arXiv author identifier and ORCID lookup
  - Extracts actual research content (papers, abstracts, contributions)
  - Grok-based extraction of skills, domains, research contributions
  - Tested with Simeon Warner (warner_s_1, ORCID: 0000-0002-7970-7855)
  - **Matching Logic Updated**: arXiv research now heavily weighted (25% weight) in team/interviewer matching and phone screen decisions

### ✅ ALL COMPLETE

**Completed Phases:**
- ✅ Phase 1: Phone Screen Interface (ENHANCED)
- ✅ Phase 2: GitHub Gathering
- ✅ Phase 3: X API Gathering
- ✅ Phase 3.5: X DM Follow-Up Service
- ✅ Phase 4: arXiv Gathering

**Removed Phases (Not Needed for Hackathon):**
- ❌ Phase 6: Unified Gatherer - **REMOVED** (individual gathering is sufficient)
- ❌ Phase 8: Profile Input Interfaces - **REMOVED** (not needed for demo)

---

## ⚠️ Important Updates

1. ~~**Wait for Vin**: Don't start outbound until knowledge graph schema is finalized~~ ✅ **DONE** - Knowledge graph is complete, you can start outbound work now
2. **Phone Screen**: Now uses Vapi for real voice calls (better than original text-based plan!)
3. **Schema Updates**: 
   - Positions now require `company` field
   - Candidates now require `name` and `phone_number` fields

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
- **Hour 12-13**: Extract links (GitHub, arXiv), extract technical content
- **Hour 13-14**: Match exact schema, write tests

### Hours 14-16: arXiv Gathering
- **Hour 14-15**: Create `backend/integrations/arxiv_api.py`, implement arXiv API client
- **Hour 15-16**: Implement `gather_from_arxiv()`, extract author/research data, match schema, write tests

### Hours 16-19: Phone Screen Interface
- **Hour 17**: Start after Vin completes Decision Engine (Hour 17)
- **Hour 17-18**: Create `backend/interviews/phone_screen_interviewer.py`, implement conversation flow
- **Hour 18-19**: Implement question generation, implement information extraction
- **Hour 19-20**: Integrate with Vin's decision engine, write tests
- **Hour 20-21**: Test conversation quality, finalize phone screen interface

### Hours 16-19: Unified Gatherer - ❌ REMOVED
- **Hour 19-20**: Complete `outbound_gatherer.py`, implement data merging
- **Hour 20-21**: Implement schema validation, integrate with knowledge graph
- **Hour 21-22**: Write tests, test end-to-end gathering

### Hours 19-22: API Updates
- **Hour 19-20**: Update `backend/api/routes.py`, add inbound endpoints
- **Hour 20-21**: Update `backend/api/models.py`, write tests, test all endpoints

### Hours 22-26: Profile Input Interfaces - ❌ REMOVED
- **Hour 22-23**: Create `backend/orchestration/profile_creator.py`, implement team creation
- **Hour 23-24**: Implement interviewer creation, implement position creation
- **Hour 24-25**: Add API endpoints, add validation, write tests
- **Hour 25-26**: ❌ REMOVED - Not needed for hackathon

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

## Phase 3.5: X DM Follow-Up Service (3-4 hours) ✅ COMPLETE

### Task: Build X DM service to gather additional candidate information

**Purpose**: After initial gathering from public X data, send DMs to candidates requesting:
- Resume/CV (paste text or share link)
- arXiv author identifier (e.g., `https://arxiv.org/a/warner_s_1` or ORCID)
- GitHub username (if not found in posts)
- LinkedIn URL (if not found in posts)
- Phone number (for phone screen interviews)
- Email address (optional)

**File**: `backend/integrations/x_dm_service.py` (NEW)

**Implementation**:

1. **DM Sending**:
   - `send_dm(user_id: str, message: str)` → Send DM to candidate
   - Uses X API OAuth 1.0a (requires Access Token + Secret, not just Bearer Token)
   - X API endpoint: `POST /2/dm_conversations/:dm_conversation_id/messages`

2. **DM Templates**:
   ```python
   RESUME_REQUEST = """
   Hi {name}! We're building your candidate profile and would love to include your resume. 
   Could you paste your resume here or share a link? Thanks!
   """
   
   ARXIV_ID_REQUEST = """
   Hi {name}! Do you have an arXiv author identifier? 
   If so, please share it (e.g., https://arxiv.org/a/warner_s_1 or your ORCID: 0000-0002-7970-7855). 
   This helps us find all your research papers!
   """
   
   GITHUB_REQUEST = """
   Hi {name}! We'd like to add your GitHub profile to your candidate profile. 
   What's your GitHub username?
   """
   
   LINKEDIN_REQUEST = """
   Hi {name}! Could you share your LinkedIn profile URL? 
   This helps us build a complete picture of your experience.
   """
   
   PHONE_REQUEST = """
   Hi {name}! We'd like to schedule a phone screen interview. 
   Could you share your phone number? (format: +1234567890)
   """
   ```

3. **Response Monitoring**:
   - `check_dm_responses(user_id: str)` → Check for DM replies
   - `get_dm_conversation(conversation_id: str)` → Get full conversation
   - Poll X API for new messages

4. **Response Parsing** (using Grok):
   - `parse_dm_response(message: str, requested_field: str)` → Extract info from reply
   - Uses Grok to intelligently extract:
     - Resume text/URL from message
     - arXiv author ID (handles both formats: `warner_s_1` or ORCID)
     - GitHub handle
     - LinkedIn URL
     - Phone number (normalizes formats)
     - Email address

5. **Auto-Request Missing Fields**:
   - `request_missing_fields(candidate_id: str)` → Automatically request missing info
   - Checks candidate profile for gaps
   - Sends appropriate DM requests
   - Tracks what was requested

6. **Profile Updates**:
   - `update_profile_from_dm(candidate_id: str, dm_data: Dict)` → Update candidate profile
   - Merges DM-gathered data into existing profile
   - Updates knowledge graph

**Integration**:
- Uses `XAPIClient` (needs OAuth 1.0a for DM sending)
- Uses `GrokAPIClient` for parsing DM responses
- Uses `OutboundGatherer` to update profiles
- Uses `KnowledgeGraph` to save updated profiles

**Workflow**:
```
1. Initial gathering: gather_from_x() → finds public data
2. Identify gaps: Check what's missing (GitHub, arXiv ID, phone, resume)
3. Send DMs: Automatically send follow-up requests
4. Monitor responses: Poll for DM replies
5. Parse responses: Extract info using Grok
6. Update profile: Add new info to candidate profile
7. Re-embed: Knowledge graph automatically re-embeds updated profile
```

**X API Requirements**:
- Need OAuth 1.0a (Access Token + Secret) for DM sending
- Bearer Token is read-only, can't send DMs
- Endpoint: `POST /2/dm_conversations/:dm_conversation_id/messages`
- Need to create DM conversation first (or use existing)

**Testing**:
- Test DM sending (requires test X account)
- Test response parsing with Grok
- Test profile updates
- Test with real candidates (opt-in)

**Deliverable**: X DM service for gathering additional candidate information ✅

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

## Phase 5: LinkedIn - REMOVED

**Note**: LinkedIn data gathering has been removed. Only `linkedin_url` is collected as an identifier (no data gathering from LinkedIn).

---

## Phase 6: Unified Gatherer - ❌ REMOVED

**Decision**: Individual gathering from each source is sufficient for the hackathon. Each source (`gather_from_x()`, `gather_from_github()`, `gather_from_arxiv()`) works independently and can be called separately. No unified merging needed.

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

**CRITICAL**: All sources must populate the updated schema (see "UPDATED CANDIDATE SCHEMA" section above).

**Key Requirements**:
- Minimum 500 datapoints per candidate per source
- All required fields must be populated
- DM-gathered fields are optional but enhance profile completeness
- Schema supports comprehensive profiling across all sources

### Schema Validation

**File**: `backend/orchestration/schema_validator.py` (NEW - optional helper)

Validate that gathered data matches exact schema before storing.

---

## Testing Strategy

### Unit Tests
- Each source gatherer (GitHub, X, arXiv)
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
│   ├── x_api.py                        # ✅ DONE - X API client implemented
│   ├── x_dm_service.py                  # NEW - X DM service for follow-up requests
│   ├── arxiv_api.py                    # NEW - arXiv client
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
requests>=2.31.0  # For API calls
requests-oauthlib>=1.3.1  # For X API OAuth 1.0a (DM sending)
```

---

## Checklist

### Phase 1: Phone Screen Interface ✅ COMPLETE
- [x] Create `backend/interviews/phone_screen_interviewer.py` ✅ DONE (uses Vapi)
- [x] Implement conversation flow ✅ DONE (Vapi handles conversation)
- [x] Implement question generation ✅ DONE (via Vapi assistant system prompt)
- [x] Implement information extraction ✅ DONE (uses Grok to extract from transcript)
- [x] Integrate with Vin's decision engine ✅ DONE (PhoneScreenDecisionEngine integrated)
- [ ] Write tests (optional - simple test exists)
- [x] Test conversation quality ✅ DONE (live test working)

### Phase 2: GitHub Gathering ✅ COMPLETE
- [x] Implement `gather_from_github()` in outbound_gatherer.py ✅ DONE
- [x] Extract all required fields ✅ DONE
- [x] Match exact schema ✅ DONE
- [x] Write tests ✅ DONE
- [x] Test schema compliance ✅ DONE
- [x] Test with @vinayakvadoothker ✅ DONE

### Phase 3: X API Gathering
- [ ] Implement X API client (modify x_api.py)
- [ ] Implement `gather_from_x()` in outbound_gatherer.py
- [ ] Extract links (GitHub, arXiv)
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

### Phase 5: LinkedIn - REMOVED
- LinkedIn data gathering removed. Only `linkedin_url` collected as identifier.

### Phase 6: Unified Gatherer
- [ ] Complete `outbound_gatherer.py`
- [ ] Implement data merging
- [ ] Implement schema validation
- [ ] Integrate with knowledge graph
- [ ] Write tests
- [ ] Test end-to-end gathering

### Phase 7: API Updates (PARTIAL)
- [x] Update `backend/api/routes.py` ✅ DONE (phone screen endpoint added)
- [x] Add inbound endpoints ✅ DONE (POST /phone-screen endpoint)
- [x] Update `backend/api/models.py` ✅ DONE (PhoneScreenRequest/Response models)
- [ ] Write tests (optional)
- [x] Test all endpoints ✅ DONE (live test working)

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

- Phone Screen Interface: 3-4 hours ✅ DONE
- X API Gathering: 2-3 hours ✅ DONE
- GitHub Gathering: 2 hours ✅ DONE
- X DM Follow-Up Service: 3-4 hours - NOT STARTED (NEW)
- arXiv Gathering: 2 hours - NOT STARTED
- LinkedIn Gathering: REMOVED (only URL collection, no data gathering)
- Unified Gatherer: 2-3 hours - NOT STARTED
- API Updates: 1-2 hours ✅ DONE (partial)
- Profile Input Interfaces: 4-6 hours - NOT STARTED

**Total**: 11-13 hours (all phases complete)
**Completed**: 11-13 hours (all phases done, unified gatherer and profile input removed)
**Remaining**: 0 hours ✅

**Note**: See "Hour-by-Hour Schedule" section above for detailed breakdown. Hours 1-8 are waiting for Vin's Knowledge Graph.

---

## Success Criteria

✅ Phone screen interface conducts quality conversations  
✅ X API gathering collects 500+ datapoints per candidate  
✅ X API gathering uses Grok for accurate extraction  
✅ X DM service can request and parse follow-up information (plain text resume support)  
✅ All 3 sources (X, GitHub, arXiv) gather data matching exact schema (500+ datapoints each)  
✅ Individual gathering methods work correctly (`gather_from_x()`, `gather_from_github()`, `gather_from_arxiv()`)  
✅ Knowledge graph can be populated with gathered data  
✅ API endpoints work for inbound pipeline (phone screen)  

---

## Important Notes

1. ~~**Wait for Vin**: Don't start outbound until knowledge graph schema is finalized~~ ✅ **DONE** - Knowledge graph is complete
2. **Exact Schema**: Must match schema exactly - no deviations
3. **Data Quality**: Extract as much as possible, but handle missing data gracefully
4. **Merging**: When multiple sources have same data, prefer most reliable source
5. **Testing**: Test with real data from all sources
6. **Error Handling**: Handle API failures, missing data, invalid inputs
7. ~~**Profile Input**: Phase 8 enables real users to input their information~~ ❌ REMOVED - Not needed for hackathon

---

## ✅ COMPLETED WORK

### Phase 1: Phone Screen Interface - COMPLETE
- ✅ `backend/interviews/phone_screen_interviewer.py` - Created and working
- ✅ Integrated with Vapi for real phone calls
- ✅ Uses Grok for information extraction
- ✅ Integrated with PhoneScreenDecisionEngine
- ✅ API endpoint: `POST /api/v1/phone-screen` - Working
- ✅ Live test successful (call created and in progress)

**Note**: Phone screen now uses Vapi for actual voice calls instead of text-based conversation. This is better than the original plan!

---

## 🚧 REMAINING WORK FOR ISHAAN

### Phase 2-5: Outbound Info Gathering (11-14 hours) - PARTIAL
**Status**: X API complete (✅), X DM service complete (✅), other sources need implementation

#### Phase 2: GitHub Gathering (2 hours) ✅ COMPLETE
- [x] Create `backend/orchestration/outbound_gatherer.py` (if doesn't exist) ✅ DONE
- [x] Implement `gather_from_github()` method ✅ DONE
- [x] Extract all required fields matching exact schema ✅ DONE
- [x] Write tests ✅ DONE
- [x] Test schema compliance ✅ DONE
- [x] Test with @vinayakvadoothker ✅ DONE

#### Phase 3: X API Gathering (2-3 hours) ✅ COMPLETE
- [x] Implement X API client (modify `backend/integrations/x_api.py`) ✅ DONE
- [x] Implement `gather_from_x()` in outbound_gatherer.py ✅ DONE
- [x] Extract links (GitHub, arXiv) ✅ DONE
- [x] Extract technical content using Grok ✅ DONE
- [x] Match exact schema ✅ DONE
- [x] Write tests ✅ DONE
- [x] Gather 500+ datapoints per candidate ✅ DONE (1520 datapoints)
- [x] Save cleaned profile to knowledge graph ✅ DONE

### Phase 3.5: X DM Follow-Up Service (3-4 hours) - NOT STARTED
**Status**: New phase for gathering additional info via X DMs

**Purpose**: After initial gathering, send DMs to candidates asking for:
- Resume/CV (paste or link)
- arXiv author identifier (e.g., `https://arxiv.org/a/warner_s_1` or ORCID)
- GitHub username (if not found in posts)
- LinkedIn URL (if not found in posts)
- Phone number (for phone screen interviews)
- Any other missing profile information

**File**: `backend/integrations/x_dm_service.py` (NEW)

**Implementation**:
- `send_follow_up_dm(user_id: str, message_template: str)` → Send DM to candidate
- `check_dm_responses(user_id: str)` → Check for DM replies
- `parse_dm_response(message: str)` → Extract info from candidate's reply
- `request_resume(user_id: str)` → Send resume request DM
- `request_arxiv_id(user_id: str)` → Send arXiv author ID request DM
- `request_github_handle(user_id: str)` → Send GitHub handle request DM
- `request_linkedin_url(user_id: str)` → Send LinkedIn URL request DM
- `request_phone_number(user_id: str)` → Send phone number request DM

**DM Templates**:
```python
RESUME_REQUEST = """
Hi {name}! We're building your candidate profile and would love to include your resume. 
Could you paste your resume here or share a link? Thanks!
"""

ARXIV_ID_REQUEST = """
Hi {name}! Do you have an arXiv author identifier? 
If so, please share it (e.g., https://arxiv.org/a/warner_s_1 or your ORCID). 
This helps us find all your research papers!
"""

GITHUB_REQUEST = """
Hi {name}! We'd like to add your GitHub profile to your candidate profile. 
What's your GitHub username?
"""

LINKEDIN_REQUEST = """
Hi {name}! Could you share your LinkedIn profile URL? 
This helps us build a complete picture of your experience.
"""

PHONE_REQUEST = """
Hi {name}! We'd like to schedule a phone screen interview. 
Could you share your phone number? (format: +1234567890)
"""
```

**Integration**:
- Uses X API OAuth 1.0a (requires Access Token + Secret for DM sending)
- Integrates with `outbound_gatherer.py` to update candidate profiles
- Updates knowledge graph with new information

**Workflow**:
1. Initial gathering: `gather_from_x()` finds what it can from public data
2. Identify gaps: Check what's missing (GitHub, arXiv ID, phone, etc.)
3. Send DMs: Automatically send follow-up requests for missing info
4. Monitor responses: Check for DM replies
5. Parse responses: Extract info from candidate replies (using Grok)
6. Update profile: Add new info to candidate profile in knowledge graph

**Testing**:
- Test DM sending (requires test account)
- Test response parsing
- Test profile updates
- Test with real candidates (opt-in)

**Deliverable**: X DM service for gathering additional candidate information ✅

#### Phase 3.5: X DM Follow-Up Service (3-4 hours) ✅ COMPLETE
- [x] Create `backend/integrations/x_dm_service.py` ✅ DONE
- [x] Implement DM sending (requires OAuth 1.0a with Access Token) ✅ DONE
- [x] Create DM templates (resume, arXiv ID, GitHub, LinkedIn URL, phone) ✅ DONE
- [x] Implement DM response monitoring ✅ DONE
- [x] Parse DM responses using Grok ✅ DONE
- [x] Extract resume text from DM (plain text, not URLs) ✅ DONE
- [x] Extract arXiv author identifier from DM (supports both formats) ✅ DONE
- [x] Extract GitHub handle, LinkedIn URL (identifier only), phone number from DM ✅ DONE
- [x] Integrate with outbound_gatherer to auto-request missing fields ✅ DONE
- [x] Update candidate profiles with DM-gathered data ✅ DONE
- [x] Write tests ✅ DONE
- [x] Test with simulated/natural responses ✅ DONE

**Note**: DM sending requires X API app permissions ("Read and write and Direct message"). Once permissions are configured, DMs can be sent. Parsing works with any natural language text (real DMs or simulated responses).

#### Phase 4: arXiv Gathering (2 hours) ✅ COMPLETE
- [x] Create `backend/integrations/arxiv_api.py` ✅ DONE
- [x] Implement arXiv API client ✅ DONE
- [x] Implement `gather_from_arxiv()` in outbound_gatherer.py ✅ DONE
- [x] Support arXiv author identifier lookup (e.g., `https://arxiv.org/a/warner_s_1`) ✅ DONE
- [x] Support ORCID identifier lookup (e.g., `https://arxiv.org/a/0000-0002-7970-7855`) ✅ DONE
- [x] Extract author/research data (actual content, not just metadata) ✅ DONE
- [x] Extract all papers by author identifier ✅ DONE
- [x] Extract research areas, contributions, methodologies ✅ DONE
- [x] Match exact schema ✅ DONE
- [x] Write tests ✅ DONE
- [x] Test with Simeon Warner (warner_s_1, ORCID: 0000-0002-7970-7855) ✅ DONE

**Additional**: Updated matching logic to heavily weight arXiv research (25% weight in team/interviewer matching and phone screen decisions). arXiv research is a strong signal of technical depth and proven contributions.

#### Phase 5: LinkedIn - REMOVED
- LinkedIn data gathering removed. Only `linkedin_url` is collected as an identifier (no data gathering).

### Phase 6: Unified Gatherer - ❌ REMOVED
- Individual gathering is sufficient for hackathon
- Each source works independently

### Phase 8: Profile Input Interfaces - ❌ REMOVED
- Not needed for hackathon demo
- Sample datasets are sufficient
  - ⚠️ **CRITICAL**: Positions MUST include `company: str` field (required for Vapi phone screen personalization)
- [ ] Add API endpoints: `POST /api/teams/create`, `POST /api/interviewers/create`, `POST /api/positions/create`
- [ ] Add request models to `backend/api/models.py`
  - ⚠️ **CRITICAL**: `PositionCreateRequest` MUST include `company: str` field
- [ ] Add validation for schema compliance
- [ ] Write tests
- [ ] Test all input interfaces

---

## 📝 UPDATES TO SCHEMA

⚠️ **CRITICAL**: Positions now require `company` field:
- **Why**: Required for Vapi phone screen personalization (assistant greets candidates with company name)
- **Action Required**:
  - Add `company: str` to position schema
  - Update `PositionCreateRequest` model to include `company` (REQUIRED field, not optional)
  - Update `profile_creator.py` to include company when creating positions
  - Update all position creation code to require company field

**IMPORTANT**: Candidates now require `name` and `phone_number` fields:
- `name: str` - Candidate's full name
- `phone_number: str` - Phone number for Vapi calls (format: "5103585699" or "+15103585699")

---

## 📊 UPDATED CANDIDATE SCHEMA (500+ Datapoints)

**CRITICAL**: Candidate schema now supports 500+ datapoints per candidate for comprehensive profiling.

### Complete Candidate Schema

```python
candidate_profile = {
    # ========== IDENTIFIERS (10+ datapoints) ==========
    "id": str,  # Format: "github_{handle}" or "x_{handle}" or "arxiv_{id}" or "linkedin_{id}"
    "name": str,  # ⚠️ REQUIRED: Full name
    "phone_number": str or None,  # ⚠️ REQUIRED for phone screens: "+1234567890" format
    "email": str or None,  # Email address (from DM or LinkedIn)
    
    # Platform Identifiers
    "github_handle": str or None,  # GitHub username (from links or DM)
    "github_user_id": str or None,  # GitHub numeric user ID
    "x_handle": str or None,  # X/Twitter username
    "x_user_id": str or None,  # X numeric user ID
    "linkedin_url": str or None,  # LinkedIn profile URL (identifier only, no data gathering)
    "arxiv_author_id": str or None,  # ⚠️ NEW: arXiv author identifier (e.g., "warner_s_1" or ORCID)
    "arxiv_ids": List[str],  # List of arXiv paper IDs
    "orcid_id": str or None,  # ORCID identifier (if linked to arXiv)
    
    # ========== CORE PROFILE DATA (50+ datapoints) ==========
    "skills": List[str],  # ⚠️ REQUIRED: Technical skills (extracted by Grok)
    "experience": List[str],  # Work experience descriptions
    "experience_years": int,  # ⚠️ REQUIRED: Years of experience
    "domains": List[str],  # ⚠️ REQUIRED: Domain expertise (LLM Inference, GPU Computing, etc.)
    "education": List[str],  # Education background
    "projects": List[Dict],  # Project information
    "expertise_level": str,  # ⚠️ REQUIRED: "Junior", "Mid", "Senior", "Staff"
    
    # Resume/Document Data (from DM)
    "resume_text": str or None,  # ⚠️ NEW: Resume text (pasted in DM)
    "resume_url": str or None,  # ⚠️ NEW: Resume URL (if shared via link)
    "resume_parsed": Dict or None,  # ⚠️ NEW: Parsed resume data (skills, experience, education extracted)
    
    # ========== SOURCE-SPECIFIC DATA (400+ datapoints) ==========
    
    # GitHub Data (if available)
    "repos": List[Dict],  # GitHub repositories with full metadata
    "github_stats": Dict,  # GitHub activity stats
    "github_contributions": List[Dict],  # Contribution history
    
    # arXiv Data (if available)
    "papers": List[Dict],  # arXiv papers with full metadata
    "arxiv_stats": Dict or None,  # ⚠️ NEW: Publication stats (total papers, citations, etc.)
    "research_areas": List[str],  # ⚠️ NEW: Research areas from papers
    
    # X/Twitter Data (if available)
    "posts": List[Dict],  # X posts (50 most recent with full metadata)
    "x_analytics_summary": Dict,  # Summary of X analytics (engagement, activity patterns)
    
    
    # ========== DM-GATHERED DATA (20+ datapoints) ==========
    "dm_responses": List[Dict] or None,  # ⚠️ NEW: DM conversation history
    "dm_requested_fields": List[str] or None,  # ⚠️ NEW: Fields we requested via DM
    "dm_provided_fields": List[str] or None,  # ⚠️ NEW: Fields candidate provided
    "dm_last_contact": str or None,  # ⚠️ NEW: Last DM timestamp
    "dm_response_rate": float or None,  # ⚠️ NEW: Response rate to DM requests
    
    # ========== ANALYTICS & METRICS (50+ datapoints) ==========
    "engagement_metrics": Dict or None,  # ⚠️ NEW: Cross-platform engagement
    "activity_patterns": Dict or None,  # ⚠️ NEW: Activity patterns (posting frequency, etc.)
    "content_quality_score": float or None,  # ⚠️ NEW: Content quality assessment
    "technical_depth_score": float or None,  # ⚠️ NEW: Technical depth assessment
    
    # ========== METADATA (10+ datapoints) ==========
    "created_at": datetime,
    "updated_at": datetime,
    "source": str,  # "outbound" or "inbound"
    "data_completeness": float,  # ⚠️ NEW: 0.0-1.0 completeness score
    "last_gathered_from": List[str],  # ⚠️ NEW: Sources last gathered from
    "gathering_timestamp": Dict or None,  # ⚠️ NEW: When each source was last gathered
}
```

### Schema Breakdown by Datapoint Count

- **Identifiers**: ~15 datapoints (IDs, handles, URLs)
- **Core Profile**: ~50 datapoints (skills, experience, domains, education, projects)
- **Resume Data**: ~30 datapoints (text, parsed fields, extracted info)
- **GitHub Data**: ~100 datapoints (repos, stats, contributions)
- **arXiv Data**: ~80 datapoints (papers, stats, research areas)
- **X Data**: ~150 datapoints (posts, analytics, engagement)
- **DM Data**: ~25 datapoints (conversations, responses, timestamps)
- **Analytics**: ~50 datapoints (metrics, scores, patterns)
- **Metadata**: ~10 datapoints (timestamps, source, completeness)

**Total**: ~570 datapoints per candidate (exceeds 500 target)

### New Fields from DM Follow-Ups

Fields that can be gathered via X DM:
- `arxiv_author_id`: arXiv author identifier (e.g., `warner_s_1` or ORCID)
- `resume_text`: Resume content (pasted in DM)
- `resume_url`: Resume URL (if shared via link)
- `resume_parsed`: Extracted resume data (skills, experience, education)
- `phone_number`: Phone number (if not in public profile)
- `email`: Email address (if shared)
- `dm_responses`: Full DM conversation history
- `dm_requested_fields`: What we asked for
- `dm_provided_fields`: What candidate provided

---

## Phase 8: Profile Input Interfaces (4-6 hours)

### Task: Build interfaces for teams, interviewers, and positions to input their information

**Purpose**: Enable real users (teams, interviewers, recruiters) to input their information into the system, not just use sample datasets. This makes the system production-ready with real user data.

⚠️ **CRITICAL REQUIREMENT**: Positions MUST include `company: str` field. This is required for Vapi phone screen personalization (the assistant greets candidates with company name).

**Files**: 
- `backend/api/routes.py` (UPDATE - add profile creation endpoints)
- `backend/api/models.py` (UPDATE - add input models)
  - ⚠️ **MUST include `company: str` in `PositionCreateRequest`**
- `backend/orchestration/profile_creator.py` (NEW - profile creation logic)
  - ⚠️ **MUST include `company` field when creating positions**

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

⚠️ **CRITICAL**: The `company` field is REQUIRED for positions. It is used by Vapi phone screen to personalize the assistant's greeting with the company name.

**Endpoint**: `POST /api/positions/create`

**Request Model**:
```python
class PositionCreateRequest(BaseModel):
    title: str
    company: str  # ⚠️ REQUIRED: Company name (used in Vapi phone screen personalization)
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
            "company": position_data["company"],  # NEW: Company field required
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
        required_fields = ["id", "title", "company", "team_id", "description", "requirements", "must_haves"]  # NEW: company required
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
    "company": "TechCorp",  # NEW: Company name required
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
5. What's the preferred data source priority (GitHub > X > arXiv)?

---

## Phase 8: Profile Input Interfaces (4-6 hours)

### Task: Build interfaces for teams, interviewers, and positions to input their information

**Purpose**: Enable real users (teams, interviewers, recruiters) to input their information into the system, not just use sample datasets. This makes the system production-ready with real user data.

⚠️ **CRITICAL REQUIREMENT**: Positions MUST include `company: str` field. This is required for Vapi phone screen personalization (the assistant greets candidates with company name).

**Files**: 
- `backend/api/routes.py` (UPDATE - add profile creation endpoints)
- `backend/api/models.py` (UPDATE - add input models)
  - ⚠️ **MUST include `company: str` in `PositionCreateRequest`**
- `backend/orchestration/profile_creator.py` (NEW - profile creation logic)
  - ⚠️ **MUST include `company` field when creating positions**

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

⚠️ **CRITICAL**: The `company` field is REQUIRED for positions. It is used by Vapi phone screen to personalize the assistant's greeting with the company name.

**Endpoint**: `POST /api/positions/create`

**Request Model**:
```python
class PositionCreateRequest(BaseModel):
    title: str
    company: str  # ⚠️ REQUIRED: Company name (used in Vapi phone screen personalization)
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
            "company": position_data["company"],  # NEW: Company field required
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
        required_fields = ["id", "title", "company", "team_id", "description", "requirements", "must_haves"]  # NEW: company required
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
    "company": "TechCorp",  # NEW: Company name required
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

