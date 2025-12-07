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

### 3. GitHub API (REQUIRED for outbound gathering)

**Purpose:** Candidate sourcing and data gathering from GitHub repositories


**Where it's used:**
- `backend/integrations/github_api.py` - GitHub API client
- `backend/orchestration/outbound_gatherer.py` - GitHub data gathering

**How to get:**
- Go to: https://github.com/settings/tokens?type=beta (Fine-grained tokens)
- Or: https://github.com/settings/tokens (Classic tokens)
- Generate a personal access token with:
  - **Fine-grained**: Repository permissions → Contents: Read-only, Metadata: Read-only
  - **Classic**: `public_repo` scope

**Required for:**
- ✅ GitHub data gathering (Phase 2)
- ✅ Reading public repositories
- ✅ Analyzing README files
- ✅ Extracting relevant code

**Error if missing:**
- `ValueError: GitHub token required. Set GITHUB_TOKEN environment variable`
- GitHub gathering will be skipped if token not available

---

### 4. X API (REQUIRED for outbound gathering)

**Purpose:** X (Twitter) API for candidate sourcing and gathering profile data

```bash
X_API_KEY=your_consumer_key_here
X_API_SECRET=your_consumer_key_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
X_BEARER_TOKEN=your_bearer_token_here
```

**Where it's used:**
- `backend/integrations/x_api.py` - X API client
- `backend/orchestration/outbound_gatherer.py` - X candidate data gathering

**How to get:**
- Apply for X API access at: https://developer.twitter.com/
- Create an app in X Developer Portal
- Get Consumer Key (API Key) and Consumer Key Secret (API Secret)
- Generate Access Token and Access Token Secret
- Generate Bearer Token for OAuth 2.0 endpoints

**Required for:**
- ✅ Outbound candidate gathering from X (Phase 3)
- ✅ Extracting GitHub/LinkedIn/arXiv links from X posts
- ✅ Extracting technical content from X posts

**Error if missing:**
- `ValueError: X API credentials required. Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, and X_BEARER_TOKEN environment variables`

---

### 5. Vapi API (REQUIRED for phone screen interviews)

**Purpose:** Automated phone screen interviews via voice calls

```bash
VAPI_PRIVATE_KEY=your_vapi_private_key_here
VAPI_PUBLIC_KEY=your_vapi_public_key_here
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id_here
```

**Where it's used:**
- `backend/integrations/vapi_api.py` - Vapi API client
- `backend/interviews/phone_screen_interviewer.py` - Phone screen interviewer
- `backend/api/routes.py` - Phone screen API endpoint

**How to get:**
- Sign up at: https://vapi.ai/
- Get API keys from Vapi dashboard
- Get phone number ID from Vapi dashboard (phone numbers section)
- API endpoint: `https://api.vapi.ai`

**Required for:**
- ✅ Automated phone screen interviews
- ✅ Voice call management
- ✅ Call transcript retrieval

**Error if missing:**
- `ValueError: Vapi private API key required. Set VAPI_PRIVATE_KEY environment variable`
- `ValueError: Vapi phone number ID required. Set VAPI_PHONE_NUMBER_ID environment variable`

---

### 6. Logging (OPTIONAL)

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

# X API (REQUIRED for outbound gathering)
X_API_KEY=your_consumer_key_here
X_API_SECRET=your_consumer_key_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
X_BEARER_TOKEN=your_bearer_token_here

# Vapi API (REQUIRED for phone screen interviews)
VAPI_PRIVATE_KEY=your_vapi_private_key_here
VAPI_PUBLIC_KEY=your_vapi_public_key_here
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id_here

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
5. **Get Vapi API keys (required for phone screens):**
   - Sign up at https://vapi.ai/
   - Get private key, public key, and phone number ID from dashboard
   - Copy to `VAPI_PRIVATE_KEY`, `VAPI_PUBLIC_KEY`, and `VAPI_PHONE_NUMBER_ID`
6. **Verify `.env` is in `.gitignore`** (should already be there)

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
required = ['WEAVIATE_URL', 'GROK_API_KEY', 'VAPI_PRIVATE_KEY', 'VAPI_PHONE_NUMBER_ID']
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

