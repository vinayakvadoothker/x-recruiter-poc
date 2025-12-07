# Candidate Schema Documentation

## Overview

The candidate schema is designed to support **500+ datapoints per candidate** for comprehensive profiling and accurate matching. This schema consolidates data from multiple sources (X, GitHub, arXiv) and DM follow-ups.

---

## Complete Schema Structure

### Identifiers (15+ datapoints)

```python
{
    "id": str,  # Unique candidate ID (format: "github_{handle}" or "x_{handle}" etc.)
    "name": str,  # ⚠️ REQUIRED: Full name
    "phone_number": str or None,  # ⚠️ REQUIRED for phone screens: "+1234567890" format
    "email": str or None,  # Email address (from DM or LinkedIn)
    
    # Platform Identifiers
    "github_handle": str or None,  # GitHub username
    "github_user_id": str or None,  # GitHub numeric user ID
    "x_handle": str or None,  # X/Twitter username
    "x_user_id": str or None,  # X numeric user ID
    "linkedin_url": str or None,  # LinkedIn profile URL (identifier only, no data gathering)
    "arxiv_author_id": str or None,  # arXiv author identifier (e.g., "warner_s_1")
    "arxiv_ids": List[str],  # List of arXiv paper IDs
    "orcid_id": str or None,  # ORCID identifier (if linked to arXiv)
}
```

### Core Profile Data (50+ datapoints)

```python
{
    # Skills & Expertise
    "skills": List[str],  # ⚠️ REQUIRED: Technical skills (extracted by Grok)
    "domains": List[str],  # ⚠️ REQUIRED: Domain expertise (LLM Inference, GPU Computing, etc.)
    "expertise_level": str,  # ⚠️ REQUIRED: "Junior", "Mid", "Senior", "Staff"
    
    # Experience
    "experience": List[str],  # Work experience descriptions
    "experience_years": int,  # ⚠️ REQUIRED: Years of experience
    
    # Education & Projects
    "education": List[str],  # Education background
    "projects": List[Dict],  # Project information
}
```

### Resume Data (30+ datapoints) - From DM

```python
{
    "resume_text": str or None,  # Resume content (pasted in DM)
    "resume_url": str or None,  # Resume URL (if shared via link)
    "resume_parsed": Dict or None,  # Parsed resume data:
    # {
    #     "skills": List[str],
    #     "experience": List[Dict],
    #     "education": List[Dict],
    #     "certifications": List[str],
    #     "languages": List[str],
    #     "summary": str
    # }
}
```

### GitHub Data (100+ datapoints)

```python
{
    "repos": List[Dict],  # Repositories with full metadata:
    # Each repo: {
    #     "id": str,
    #     "name": str,
    #     "description": str,
    #     "language": str,
    #     "stars": int,
    #     "forks": int,
    #     "created_at": str,
    #     "updated_at": str,
    #     "topics": List[str],
    #     "contributors": List[str],
    #     "commits": int,
    #     "lines_of_code": int
    # }
    
    "github_stats": Dict,  # {
    #     "total_repos": int,
    #     "total_stars": int,
    #     "total_forks": int,
    #     "total_commits": int,
    #     "languages": Dict[str, int],  # Language -> line count
    #     "topics": List[str],
    #     "contribution_graph": List[int]  # 52 weeks of contributions
    # }
    
    "github_contributions": List[Dict],  # Contribution history
}
```

### arXiv Data (80+ datapoints)

```python
{
    "papers": List[Dict],  # Papers with full metadata:
    # Each paper: {
    #     "id": str,  # arXiv ID
    #     "title": str,
    #     "authors": List[str],
    #     "abstract": str,
    #     "categories": List[str],
    #     "published": str,
    #     "updated": str,
    #     "pdf_url": str,
    #     "citation_count": int or None,
    #     "references": List[str] or None
    # }
    
    "arxiv_stats": Dict or None,  # {
    #     "total_papers": int,
    #     "total_citations": int,
    #     "h_index": int or None,
    #     "research_areas": List[str],
    #     "co_authors": List[str],
    #     "publication_years": Dict[int, int]  # Year -> paper count
    # }
    
    "research_areas": List[str],  # Research domains
}
```

### X/Twitter Data (150+ datapoints)

```python
{
    "posts": List[Dict],  # 50 most recent posts:
    # Each post: {
    #     "id": str,
    #     "text": str,
    #     "created_at": str,
    #     "lang": str,
    #     "metrics": {
    #         "like_count": int,
    #         "retweet_count": int,
    #         "reply_count": int,
    #         "quote_count": int,
    #         "impression_count": int,
    #         "bookmark_count": int
    #     },
    #     "entities": {
    #         "urls": List[Dict],
    #         "mentions": List[Dict],
    #         "hashtags": List[Dict]
    #     }
    # }
    
    "x_analytics_summary": Dict,  # {
    #     "total_tweets_analyzed": int,
    #     "avg_engagement_rate": float,
    #     "total_followers": int,
    #     "most_active_month": str,
    #     "content_languages": List[str]
    # }
}
```

### DM-Gathered Data (25+ datapoints)

```python
{
    "dm_responses": List[Dict] or None,  # DM conversation history:
    # Each message: {
    #     "message_id": str,
    #     "text": str,
    #     "timestamp": str,
    #     "direction": "sent" or "received",
    #     "extracted_data": Dict or None  # Data extracted from message
    # }
    
    "dm_requested_fields": List[str] or None,  # ["resume", "arxiv_id", "github_handle"]
    "dm_provided_fields": List[str] or None,  # ["resume", "github_handle"]
    "dm_last_contact": str or None,  # Last DM timestamp
    "dm_response_rate": float or None,  # Response rate (0.0-1.0)
}
```

### Analytics & Metrics (50+ datapoints)

```python
{
    "engagement_metrics": Dict or None,  # Cross-platform engagement
    "activity_patterns": Dict or None,  # Posting frequency, activity times
    "content_quality_score": float or None,  # 0.0-1.0
    "technical_depth_score": float or None,  # 0.0-1.0
}
```

### Metadata (10+ datapoints)

```python
{
    "created_at": datetime,
    "updated_at": datetime,
    "source": str,  # "outbound" or "inbound"
    "data_completeness": float,  # 0.0-1.0 completeness score
    "last_gathered_from": List[str],  # ["x", "github", "arxiv"]
    "gathering_timestamp": Dict or None,  # {"x": "2025-12-06", "github": "2025-12-05"}
}
```

---

## Datapoint Count Breakdown

| Category | Datapoints | Description |
|----------|-----------|-------------|
| Identifiers | 15 | IDs, handles, URLs across platforms |
| Core Profile | 50 | Skills, experience, domains, education |
| Resume Data | 30 | Resume text, parsed data, extracted fields |
| GitHub Data | 100 | Repos, stats, contributions, languages |
| arXiv Data | 80 | Papers, stats, research areas, citations |
| X Data | 150 | Posts, analytics, engagement metrics |
| DM Data | 25 | DM conversations, responses, timestamps |
| Analytics | 50 | Cross-platform metrics, quality scores |
| Metadata | 10 | Timestamps, source, completeness |
| **TOTAL** | **~510** | **Exceeds 500 datapoint target** |

---

## Required vs Optional Fields

### ⚠️ REQUIRED Fields (Must be populated)
- `id`: Unique candidate identifier
- `name`: Full name
- `phone_number`: For phone screen interviews
- `skills`: At least one skill (can be empty list if truly none)
- `experience_years`: Years of experience
- `domains`: At least one domain
- `expertise_level`: Junior/Mid/Senior/Staff
- `created_at`, `updated_at`, `source`: Metadata

### Optional but Valuable Fields
- `github_handle`: Can be gathered from X links or DM
- `arxiv_author_id`: Can be gathered from DM
- `resume_text`: Can be gathered from DM
- `linkedin_url`: Can be gathered from X links or DM
- All analytics and metrics fields

---

## DM Follow-Up Fields

These fields are populated via X DM conversations:

1. **Resume**: `resume_text`, `resume_url`, `resume_parsed`
2. **arXiv Author ID**: `arxiv_author_id`, `orcid_id`
3. **GitHub Handle**: `github_handle` (if not found in posts)
4. **LinkedIn URL**: `linkedin_url` (if not found in posts) - URL only, no data gathering
5. **Phone Number**: `phone_number` (if not in public profile)
6. **Email**: `email` (if shared)
7. **DM History**: `dm_responses`, `dm_requested_fields`, `dm_provided_fields`

---

## Schema Validation

All candidate profiles must:
- Have all REQUIRED fields populated
- Match data types exactly
- Have valid IDs (format: `{source}_{identifier}`)
- Have `data_completeness` score calculated
- Support 500+ datapoints for comprehensive profiling

---

## Usage Example

```python
# Gather from X
gatherer = OutboundGatherer()
profile = await gatherer.gather_and_save_from_x("Ishaanbansal77")

# Profile now has:
# - 1520 datapoints from X
# - Skills, domains, experience extracted by Grok
# - Links to GitHub, arXiv
# - LinkedIn URL (identifier only)
# - Saved to knowledge graph

# Later, request missing info via DM
dm_service = XDMService()
if not profile.get("arxiv_author_id"):
    await dm_service.request_arxiv_id(profile["x_user_id"])

# Check for DM response and update profile
response = await dm_service.check_dm_responses(profile["x_user_id"])
if response:
    profile["arxiv_author_id"] = extract_arxiv_id(response)
    kg.update_candidate(profile["id"], {"arxiv_author_id": profile["arxiv_author_id"]})
```

