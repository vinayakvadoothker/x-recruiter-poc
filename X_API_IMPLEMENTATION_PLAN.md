# X API Implementation Plan

⚠️ **IMPORTANT**: The candidate schema requires a `name` field. X API returns the user's display name in the `name` field of the user profile. We must extract and include this field in the gathered candidate data.

## Step 1: Add Credentials to .env

Add these lines to your `.env` file:


**Note**: The Bearer Token is URL-encoded (the `%3D` is `=`). We'll decode it in code or use it as-is depending on X API requirements.

---

## Step 2: Implementation Plan

### What We Need to Build

#### 1. X API Client (`backend/integrations/x_api.py`)
**Current State**: Stub implementation
**What to Implement**:

1. **Authentication**:
   - Support OAuth 1.0a (Consumer Key + Secret + Access Token + Secret)
   - Support Bearer Token for OAuth 2.0 endpoints
   - Use `requests-oauthlib` or `tweepy` library for OAuth 1.0a

2. **Core Methods**:
   - `get_profile(username: str)` → Get user profile data (includes `name` field - REQUIRED)
   - `get_user_tweets(username: str, max_results: int = 100)` → Get user's recent tweets
   - `search_users(query: str)` → Search for users by keyword
   - `extract_links_from_tweets(tweets: List[Dict])` → Extract GitHub/LinkedIn/arXiv links

3. **Data Extraction**:
   - **Name**: Extract from `profile.get("name")` (⚠️ REQUIRED field)
   - Profile: bio, location, website, follower count, following count
   - Tweets: text, timestamp, engagement metrics
   - Links: Extract URLs from tweets and bio
   - Technical content: Identify technical posts (keywords, hashtags)


#### 2. Outbound Gatherer (`backend/orchestration/outbound_gatherer.py`)
**Current State**: Doesn't exist yet
**What to Implement**:

1. **Main Method**: `gather_from_x(x_handle: str) -> Dict`
   - Takes X username (without @)
   - Calls X API client to get profile and tweets
   - Extracts links (GitHub, LinkedIn, arXiv)
   - Extracts technical content
   - Formats data to match exact candidate schema

2. **Link Extraction**:
   - GitHub: Extract `github.com/username` → `github_handle`
   - LinkedIn: Extract `linkedin.com/in/...` → `linkedin_url`
   - arXiv: Extract `arxiv.org/abs/...` → `arxiv_ids`

3. **Technical Content Extraction**:
   - Parse tweets for technical keywords
   - Extract skills mentioned in tweets
   - Extract domains/technologies discussed
   - Extract experience mentions

4. **Schema Compliance**:
   - Match exact candidate schema from `ishaan_pivot_plan.md`
   - **Required fields**: `id`, `name` ⚠️, `x_handle`, `skills`, `experience`, `experience_years`, `domains`, `expertise_level`
   - Optional fields: `github_handle`, `linkedin_url`, `arxiv_ids`, `posts`, `projects`
   - **Note**: `name` is REQUIRED - extract from X profile `name` field, use username as fallback if missing

---

## Step 3: Technical Details

### X API v2 Endpoints We'll Use

1. **Get User by Username**:
   ```
   GET https://api.twitter.com/2/users/by/username/:username
   ```
   - Returns: profile data, public metrics

2. **Get User Tweets**:
   ```
   GET https://api.twitter.com/2/users/:id/tweets
   ```
   - Returns: recent tweets (up to 100 per request)
   - Need to paginate for more tweets

3. **Search Users** (optional, for future):
   ```
   GET https://api.twitter.com/2/users/search
   ```
   - Search by keyword

### Authentication Strategy

**Option 1: Use Bearer Token (Simpler)**
- Bearer Token works for most read-only endpoints
- No OAuth 1.0a complexity
- Just add `Authorization: Bearer {token}`` header

**Option 2: Use OAuth 1.0a (More Complete)**
- Required for some endpoints (DM, write operations)
- For read-only, Bearer Token is sufficient
- We'll start with Bearer Token, add OAuth 1.0a if needed

### Libraries Needed

**Option A: Use `requests` + manual OAuth**
- Simple, lightweight
- Manual OAuth 1.0a signing (complex)

**Option B: Use `tweepy` (Recommended)**
- Handles OAuth 1.0a automatically
- Easy to use
- Well-maintained
- Add to `requirements.txt`: `tweepy>=4.14.0`

**Option C: Use `requests-oauthlib`**
- More control than tweepy
- Still handles OAuth 1.0a
- Add to `requirements.txt`: `requests-oauthlib>=1.3.1`

**Recommendation**: Start with **Option B (tweepy)** for simplicity, fall back to manual if needed.

---

## Step 4: Data Extraction Logic

### From X Profile:
```python
{
    "id": f"x_{username}",
    "x_handle": username,
    "name": profile.get("name"),  # ⚠️ REQUIRED: Full name from X profile
    "bio": profile.get("description"),  # Extract skills/domains from here
    "location": profile.get("location"),
    "website": profile.get("url"),  # May contain GitHub/LinkedIn
    "followers_count": profile.get("public_metrics", {}).get("followers_count", 0),
    "following_count": profile.get("public_metrics", {}).get("following_count", 0),
}
```

**⚠️ IMPORTANT**: The `name` field is **REQUIRED** in the candidate schema. X API returns `name` in the user profile object, so we extract it directly from `profile.get("name")`. If the name is missing from X profile, we should use the username as fallback or log a warning.

### From Tweets:
```python
# Extract links
github_links = extract_github_links(tweets)  # → github_handle
linkedin_links = extract_linkedin_links(tweets)  # → linkedin_url
arxiv_links = extract_arxiv_links(tweets)  # → arxiv_ids

# Extract technical content
skills = extract_skills_from_tweets(tweets)  # Keywords, technologies
domains = extract_domains_from_tweets(tweets)  # ML, systems, etc.
experience = extract_experience_mentions(tweets)  # "5 years", "worked at X"
```

### Name Extraction:
```python
# From X Profile (REQUIRED)
name = profile.get("name")  # X API returns display name
if not name:
    # Fallback: Use username (but log warning)
    name = username
    logger.warning(f"X profile {username} has no name field, using username as fallback")
```

### Skills Extraction Strategy:
1. **Keyword matching**: Look for common tech terms (Python, PyTorch, CUDA, etc.)
2. **Hashtag analysis**: #MachineLearning, #Python, #LLM, etc.
3. **Bio parsing**: Extract from profile bio
4. **Tweet content**: Scan recent tweets for technical mentions

### Experience Extraction:
1. **Time mentions**: "5 years", "since 2020", "for 3 years"
2. **Company mentions**: "worked at", "engineer at", "built at"
3. **Role mentions**: "senior engineer", "staff engineer", "researcher"

---

## Step 5: Schema Matching

### Exact Schema (from `ishaan_pivot_plan.md`):
```python
{
    "id": f"x_{username}",
    "name": profile.get("name"),  # ⚠️ REQUIRED: Full name from X profile
    "github_handle": extracted_from_links or None,
    "x_handle": username,
    "linkedin_url": extracted_from_links or None,
    "arxiv_ids": extracted_from_links or [],
    
    # Core Profile Data (REQUIRED)
    "skills": List[str],  # MUST be populated
    "experience": List[str],  # Work experience descriptions
    "experience_years": int,  # Calculate from available data
    "domains": List[str],  # Infer from skills/experience
    "education": List[str],  # From bio (if mentioned)
    "projects": List[Dict],  # From tweets/repos (if linked)
    "expertise_level": str,  # "Junior", "Mid", "Senior", "Staff"
    
    # Source-Specific Data
    "posts": List[Dict],  # X posts with metadata
    "github_stats": Dict or {},  # Empty if no GitHub link
    
    # Metadata (REQUIRED)
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "source": "outbound"
}
```

**⚠️ CRITICAL**: The `name` field is **REQUIRED** in the candidate schema (as per `ishaan_pivot_plan.md` line 763-765). X API returns the user's display name in the `name` field of the user profile object. We must extract and include this field.

---

## Step 6: Implementation Order

1. **Install dependencies**: Add `tweepy` to `requirements.txt`
2. **Update X API client**: Implement authentication and core methods
3. **Test X API client**: Test with real X username
4. **Create outbound_gatherer.py**: Create file and structure
5. **Implement `gather_from_x()`**: Main gathering logic
6. **Implement link extraction**: GitHub, LinkedIn, arXiv
7. **Implement content extraction**: Skills, domains, experience
8. **Schema validation**: Ensure output matches exact schema
9. **Write tests**: Unit tests for each component
10. **Integration test**: End-to-end test with real X handle

---

## Step 7: Error Handling

- **Rate Limits**: X API has rate limits (varies by endpoint)
  - Implement retry with backoff (use existing `retry_with_backoff` utility)
  - Track rate limit headers and respect them

- **Missing Data**: Not all X profiles have complete data
  - Handle missing fields gracefully
  - Use defaults where appropriate
  - Log warnings for missing critical data

- **Invalid Usernames**: Handle non-existent users
  - Return empty dict or raise ValueError
  - Log error clearly

- **API Errors**: Handle 401, 403, 404, 429, 500 errors
  - Use existing `handle_api_error` utility
  - Provide clear error messages

---

## Step 8: Testing Strategy

### Unit Tests:
- Test X API client methods individually
- Test link extraction logic
- Test content extraction logic
- Test schema formatting

### Integration Tests:
- Test `gather_from_x()` with real X handle
- Test with minimal profile (no bio, few tweets)
- Test with rich profile (lots of data)
- Test schema compliance

### Edge Cases:
- User with no tweets
- User with private account (should handle gracefully)
- User with no bio
- User with no links
- **User with no name field** (use username as fallback, log warning)
- Invalid username

---

## Summary

**What you need to do:**
1. ✅ Add X API credentials to `.env` (formatted above)
2. ✅ Update `.env.example` (already done)
3. ✅ Update `ENV_REQUIREMENTS.md` (already done)

**What I'll implement:**
1. Update `backend/integrations/x_api.py` with full X API client
2. Create `backend/orchestration/outbound_gatherer.py` with `gather_from_x()` method
3. **Extract `name` field from X profile** (⚠️ REQUIRED in candidate schema)
4. Implement link extraction (GitHub, LinkedIn, arXiv)
5. Implement technical content extraction
6. Ensure schema compliance (including `name` field)
7. Add tests

**Estimated Time**: 2-3 hours

**Dependencies to add**: `tweepy>=4.14.0` (or `requests-oauthlib>=1.3.1`)

Ready to start implementation!

