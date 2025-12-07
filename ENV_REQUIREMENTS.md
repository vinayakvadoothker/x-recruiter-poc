# Environment Variables Requirements

**Managed by:** Vin (Vin's human assistant handles .env setup)

This document lists ALL environment variables required for the production-grade system.

---

## Required Variables

### 1. Weaviate Vector Database (REQUIRED)

**Purpose:** Store embeddings and enable fast similarity search

```bash
WEAVIATE_URL=http://localhost:8080
```

**Where it's used:**
- `backend/database/vector_db_client.py` - Vector DB client (Phase 3)
- `backend/database/knowledge_graph.py` - Knowledge graph abstraction (Phase 4)

**How to get:**
- Weaviate runs in Docker Compose (automatically started)
- Default URL is `http://localhost:8080` (Docker Compose)
- No authentication needed for local development

**Required for:**
- ✅ Embedding storage and retrieval
- ✅ Fast similarity search
- ✅ Knowledge graph storage

---

### 2. Grok API (REQUIRED)

**Purpose:** 
- Entity extraction from role descriptions and candidate profiles
- **CRITICAL: Natural language feedback parsing for self-improving agent (Phase 10)**

```bash
GROK_API_KEY=xai-SlvY0Bos1oOzap6Ed3tEygd3ZiL3V8fSihP5uPW7oMpO16smJivCI6fk3AVsiGCrmmbNIYPVJZfVjMgs
```

**Where it's used:**
- `backend/integrations/grok_api.py` - Grok API client
- `backend/orchestration/feedback_loop.py` - **LLM-based feedback parsing (NO KEYWORDS)**
- `backend/orchestration/recruiter_agent.py` - Recruiter agent integration
- Entity extraction (if used)

**How to get:**
- Sign up at: https://console.x.ai/
- Get API key from xAI Cloud Console
- API endpoint: `https://api.x.ai/v1`
- Model: `grok-4-latest`

**CRITICAL:** This is used for production-grade natural language understanding. 
NO keyword matching - all feedback parsing uses Grok API for accurate sentiment analysis.

**Required for:**
- ✅ Entity extraction (skills, experience, education)
- ✅ Pipeline processing
- ✅ Candidate sourcing

**Error if missing:**
- `ValueError: Grok API key required. Set GROK_API_KEY environment variable`

---

### 3. GitHub API (OPTIONAL but recommended)

**Purpose:** Candidate sourcing from GitHub repositories

```bash
GITHUB_TOKEN=your_github_token_here
```

**Where it's used:**
- `backend/integrations/github_api.py` - GitHub API client
- `backend/orchestration/candidate_sourcer.py` - Candidate sourcing

**How to get:**
- Go to: https://github.com/settings/tokens
- Generate a personal access token with `public_repo` scope

**Required for:**
- ⚠️ Candidate sourcing from GitHub (optional - can use mock data)

**Error if missing:**
- `ValueError: GitHub token required. Set GITHUB_TOKEN environment variable`
- Pipeline will fail if trying to source from GitHub without this

---

### 4. X API (OPTIONAL - Future use)

**Purpose:** X (Twitter) API for candidate sourcing and outreach

```bash
X_API_KEY=your_x_api_key_here
```

**Where it's used:**
- `backend/integrations/x_api.py` - X API client
- `backend/orchestration/candidate_sourcer.py` - X candidate sourcing

**How to get:**
- Apply for X API access at: https://developer.twitter.com/

**Required for:**
- ❌ Not needed for hackathon (using simulator instead)
- Future production use only

---

### 5. Logging (OPTIONAL)

**Purpose:** Control logging level

```bash
LOG_LEVEL=INFO
```

**Where it's used:**
- `backend/__init__.py` - Logging configuration

**Valid values:**
- `DEBUG` - Verbose logging
- `INFO` - Standard logging (default)
- `WARNING` - Warnings and errors only
- `ERROR` - Errors only

**Default:** `INFO`

---

## Complete .env Template

```bash
# ============================================================================
# PRODUCTION ENVIRONMENT VARIABLES
# Managed by Vin's human assistant
# ============================================================================

# Weaviate Vector Database (REQUIRED)
WEAVIATE_URL=http://localhost:8080

# Grok API (REQUIRED)
GROK_API_KEY=your_grok_api_key_here

# GitHub API (OPTIONAL but recommended)
GITHUB_TOKEN=your_github_token_here

# X API (OPTIONAL - Future use)
# X_API_KEY=your_x_api_key_here

# Logging (OPTIONAL)
LOG_LEVEL=INFO
```

---

## Setup Instructions for Vin's Human Assistant

1. **Create `.env` file** in project root (copy from `.env.example`)
2. **Weaviate setup:**
   - Weaviate runs automatically in Docker Compose
   - No configuration needed (default URL: http://localhost:8080)
3. **Get Grok API key:**
   - Sign up at https://docs.x.ai/docs/tutorial
   - Copy API key to `GROK_API_KEY`
4. **Get GitHub token (optional):**
   - Go to https://github.com/settings/tokens
   - Generate token with `public_repo` scope
   - Copy to `GITHUB_TOKEN`
5. **Verify `.env` is in `.gitignore`** (should already be there)

---

## Validation

To verify all required variables are set:

```bash
# Check if .env exists
test -f .env && echo "✅ .env file exists" || echo "❌ .env file missing"

# Check required variables (without exposing values)
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['WEAVIATE_URL', 'GROK_API_KEY']
missing = [v for v in required if not os.getenv(v)]
if missing:
    print(f'❌ Missing: {missing}')
else:
    print('✅ All required variables set')
"
```

---

## Notes

- **Never commit `.env` file** - It's in `.gitignore`
- **Use `.env.example`** as template (no real values)
- **Vin's human assistant** handles all .env setup
- **Ishaan's code** should NOT hardcode any API keys or credentials

