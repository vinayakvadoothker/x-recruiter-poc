# Data Sources for Candidate Information

## Overview

This document lists **all possible data sources** for candidate information, prioritized for MVP and future expansion.

---

## MVP Sources (Must Have - Day 1-3)

### 1. GitHub API ⭐⭐⭐
**Priority**: HIGHEST - Core MVP source

**What we get**:
- Code repositories (languages, topics, stars, forks)
- Contribution history (commits, PRs, issues)
- Profile information (bio, location, company)
- Repository descriptions and READMEs
- Code quality indicators (test coverage, CI/CD)
- Collaboration patterns (contributors, forks)

**API Access**:
- ✅ Public data: No auth needed (rate limited)
- ✅ Authenticated: `GITHUB_TOKEN` (higher rate limits)
- ✅ Endpoints: `/search/users`, `/users/{username}`, `/users/{username}/repos`

**Data Quality**: ⭐⭐⭐⭐⭐
- High signal for technical skills
- Real code samples
- Active contribution history
- Easy to parse and analyze

**MVP Implementation**:
```python
# backend/integrations/github_api.py
- search_users(query, language, topics)
- get_user_profile(username)
- get_user_repos(username)
- analyze_code_quality(repo)
```

**Use Case**: Primary source for "LLM Inference Optimization Engineer"
- Search: `language:Python language:CUDA topic:transformer topic:inference`
- Filter by: stars, recent activity, repo quality

---

### 2. X (Twitter) API ⭐⭐⭐
**Priority**: HIGH - Core MVP source

**What we get**:
- Technical posts and threads
- Engagement metrics (likes, retweets, replies)
- Follower networks (who they follow, who follows them)
- Profile information (bio, location, website)
- Tweet history (technical content, job interests)
- Lists and communities they're part of

**API Access**:
- ⚠️ Requires API approval (hard for hackathon)
- ✅ **MVP Solution**: Simulate X DMs (no real API needed)
- ✅ Future: X API v2 (`/2/users/by/username`, `/2/tweets/search`)

**Data Quality**: ⭐⭐⭐⭐
- High signal for communication skills
- Technical thought leadership
- Community engagement
- Real-time activity

**MVP Implementation**:
```python
# backend/integrations/x_api.py (stub for future)
# backend/simulator/x_dm_simulator.py (for MVP)
- search_profiles(query, keywords)
- get_profile(username)
- get_tweets(username, keywords)
- analyze_engagement(tweets)
```

**Use Case**: Find candidates posting about:
- "CUDA optimization"
- "Transformer inference"
- "LLM performance"
- "Multi-GPU training"

---

### 3. Grok API ⭐⭐⭐
**Priority**: HIGH - Core MVP (entity extraction)

**What we get**:
- Entity extraction (skills, experience, education)
- Text embeddings (for similarity)
- Profile summarization
- Role requirement parsing
- Candidate matching analysis

**API Access**:
- ✅ `GROK_API_KEY` (from xAI)
- ✅ Endpoints: `/v1/chat/completions`, `/v1/embeddings`

**Data Quality**: ⭐⭐⭐⭐⭐
- High accuracy for entity extraction
- Domain-adapted embeddings
- Natural language understanding

**MVP Implementation**:
```python
# backend/integrations/grok_api.py
- extract_entities(text, entity_types)
- get_embeddings(text)
- summarize_profile(candidate_data)
- parse_role_requirements(description)
```

**Use Case**: Extract from GitHub/X profiles:
- Skills: "CUDA", "PyTorch", "Transformer"
- Experience: "5 years ML infrastructure"
- Education: "PhD Computer Science"

---

## Secondary Sources (Future - Post-MVP)

### 4. arXiv API ⭐⭐
**Priority**: MEDIUM - Post-MVP

**What we get**:
- Paper authorship
- Citation networks
- Research areas and expertise
- Publication history
- Co-author relationships

**API Access**:
- ✅ Public API (no auth needed)
- ✅ Endpoint: `http://export.arxiv.org/api/query`

**Data Quality**: ⭐⭐⭐⭐
- High signal for research roles
- Academic expertise
- Domain knowledge depth

**Implementation**:
```python
# backend/integrations/arxiv_api.py
- search_authors(query)
- get_author_papers(author_id)
- analyze_citations(papers)
- extract_research_areas(papers)
```

**Use Case**: Find researchers working on:
- "Transformer optimization"
- "LLM inference"
- "Multi-GPU parallelism"

---

### 5. LinkedIn API ⭐
**Priority**: LOW - Post-MVP (API restrictions)

**What we get**:
- Work history (companies, roles, duration)
- Skill endorsements
- Education history
- Recommendations
- Connection networks
- Activity posts

**API Access**:
- ⚠️ Very restricted (requires partnership)
- ⚠️ Limited endpoints for most developers
- ✅ Alternative: Web scraping (legal gray area)

**Data Quality**: ⭐⭐⭐
- Good for work history
- Skill endorsements (but can be inflated)
- Connection networks

**Implementation**:
```python
# backend/integrations/linkedin_api.py (future)
- get_profile(profile_url)  # If API access
- scrape_profile(profile_url)  # Alternative
- extract_work_history(profile)
- extract_skills(profile)
```

**Note**: LinkedIn is valuable but hard to access. Consider for Phase 2.

---

### 6. Stack Overflow API ⭐⭐
**Priority**: MEDIUM - Post-MVP

**What we get**:
- Question/answer history
- Reputation and badges
- Tags and expertise areas
- Code samples
- Community engagement

**API Access**:
- ✅ Public API (no auth needed, rate limited)
- ✅ Endpoint: `https://api.stackexchange.com/2.3/`

**Data Quality**: ⭐⭐⭐⭐
- High signal for problem-solving skills
- Real code examples
- Community recognition
- Technical depth

**Implementation**:
```python
# backend/integrations/stackoverflow_api.py
- get_user_profile(user_id)
- get_user_questions(user_id)
- get_user_answers(user_id)
- analyze_expertise_tags(activity)
```

**Use Case**: Find experts in:
- "cuda"
- "pytorch"
- "transformer"
- "inference"

---

### 7. Dev.to API ⭐⭐
**Priority**: MEDIUM - Post-MVP

**What we get**:
- Technical blog posts
- Article topics and tags
- Engagement metrics
- Code examples
- Community engagement

**API Access**:
- ✅ Public API (no auth needed)
- ✅ Endpoint: `https://dev.to/api/`

**Data Quality**: ⭐⭐⭐
- Good for communication skills
- Technical writing ability
- Thought leadership

**Implementation**:
```python
# backend/integrations/devto_api.py
- get_user_articles(username)
- analyze_article_topics(articles)
- extract_code_examples(articles)
```

---

### 8. Medium API ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Technical articles
- Publication history
- Topics and tags
- Engagement metrics

**API Access**:
- ⚠️ Limited API (requires partnership)
- ✅ Alternative: RSS feeds, web scraping

**Data Quality**: ⭐⭐⭐
- Similar to Dev.to
- Broader audience

---

### 9. Personal Websites/Portfolios ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Portfolio projects
- Resume/CV
- Blog posts
- Contact information
- Project demos

**API Access**:
- ⚠️ No API (web scraping required)
- ✅ Can extract from GitHub profile links
- ✅ Can extract from X/LinkedIn bio links

**Data Quality**: ⭐⭐⭐
- Varies by candidate
- High signal when available

**Implementation**:
```python
# backend/integrations/portfolio_scraper.py
- scrape_portfolio(url)
- extract_projects(html)
- extract_resume(html)
```

---

### 10. ResearchGate ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Research publications
- Citation metrics
- Research interests
- Collaboration networks

**API Access**:
- ⚠️ No official API
- ✅ Web scraping (legal considerations)

**Data Quality**: ⭐⭐⭐
- Good for research roles
- Academic focus

---

### 11. Google Scholar ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Publication history
- Citation counts
- H-index
- Research areas

**API Access**:
- ⚠️ No official API
- ✅ Web scraping (legal considerations)

**Data Quality**: ⭐⭐⭐⭐
- High signal for research roles
- Academic metrics

---

### 12. Patents (USPTO, Google Patents) ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Patent filings
- Inventor information
- Technical domains
- Innovation history

**API Access**:
- ✅ USPTO API (public)
- ✅ Google Patents (web scraping)

**Data Quality**: ⭐⭐⭐
- Good for innovation roles
- Technical depth

---

### 13. Conference Speakers/Attendees ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Conference presentations
- Speaker profiles
- Talk topics
- Community involvement

**API Access**:
- ⚠️ No unified API
- ✅ Scrape conference websites
- ✅ Extract from event pages

**Data Quality**: ⭐⭐⭐
- High signal for thought leadership
- Domain expertise

**Examples**:
- NeurIPS, ICML, ICLR (ML conferences)
- PyData, PyTorch DevCon
- CUDA conferences

---

### 14. Open Source Contributions (Beyond GitHub) ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Contributions to other platforms
- Package maintainership
- Community leadership

**Platforms**:
- PyPI (Python packages)
- npm (JavaScript packages)
- CRAN (R packages)
- Maven (Java packages)

**API Access**:
- ✅ PyPI API: `https://pypi.org/pypi/{package}/json`
- ✅ npm API: `https://registry.npmjs.org/{package}`

---

### 15. Code Repositories (Beyond GitHub) ⭐
**Priority**: LOW - Post-MVP

**Platforms**:
- GitLab
- Bitbucket
- SourceForge
- Codeberg

**API Access**:
- ✅ GitLab API (public)
- ✅ Bitbucket API (public)

---

### 16. Technical Forums/Communities ⭐
**Priority**: LOW - Post-MVP

**Platforms**:
- Reddit (r/MachineLearning, r/cuda, etc.)
- Discord servers
- Slack communities
- Hacker News

**API Access**:
- ✅ Reddit API (public)
- ⚠️ Discord/Slack (requires bot access)

**Data Quality**: ⭐⭐
- Community engagement
- Technical discussions

---

### 17. YouTube Channels ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Technical tutorials
- Conference talks
- Project demos
- Communication skills

**API Access**:
- ✅ YouTube Data API (public, requires key)

**Data Quality**: ⭐⭐⭐
- Communication skills
- Technical depth
- Teaching ability

---

### 18. Podcast Appearances ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Technical discussions
- Thought leadership
- Communication skills

**API Access**:
- ⚠️ No unified API
- ✅ Scrape podcast websites

---

### 19. Kaggle ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Competition rankings
- Notebooks and kernels
- Datasets
- Community engagement

**API Access**:
- ✅ Kaggle API (public, requires key)

**Data Quality**: ⭐⭐⭐
- Good for data science roles
- Competition performance

---

### 20. LeetCode / HackerRank / CodeSignal ⭐
**Priority**: LOW - Post-MVP

**What we get**:
- Coding challenge performance
- Problem-solving skills
- Algorithm knowledge

**API Access**:
- ⚠️ Limited APIs
- ✅ Web scraping (legal considerations)

**Data Quality**: ⭐⭐
- Good for screening
- Algorithm skills

---

## MVP Data Source Strategy

### Phase 1: MVP (Days 1-3)
**Primary Sources**:
1. ✅ **GitHub API** - Core sourcing (code, repos, profiles)
2. ✅ **X API (Simulated)** - Profile analysis, DM interface
3. ✅ **Grok API** - Entity extraction, embeddings

**Why These Three**:
- All have accessible APIs (or can be simulated)
- High signal-to-noise ratio
- Fast to implement
- Covers technical skills, communication, and profile data

### Phase 2: Enhanced Sourcing (Post-MVP)
**Add**:
- arXiv (research roles)
- Stack Overflow (problem-solving)
- Dev.to (technical writing)
- Personal websites (portfolios)

### Phase 3: Comprehensive Sourcing (Future)
**Add**:
- LinkedIn (work history)
- Conference speakers
- Patents
- All other sources

---

## Data Source Priority Matrix

| Source | MVP | Post-MVP | API Access | Data Quality | Implementation Time |
|--------|-----|----------|------------|--------------|---------------------|
| GitHub | ✅ | ✅ | Easy | ⭐⭐⭐⭐⭐ | 2 hours |
| X (Simulated) | ✅ | ✅ | Simulated | ⭐⭐⭐⭐ | 4 hours |
| Grok | ✅ | ✅ | Easy | ⭐⭐⭐⭐⭐ | 2 hours |
| arXiv | ❌ | ✅ | Easy | ⭐⭐⭐⭐ | 4 hours |
| Stack Overflow | ❌ | ✅ | Easy | ⭐⭐⭐⭐ | 3 hours |
| Dev.to | ❌ | ✅ | Easy | ⭐⭐⭐ | 2 hours |
| LinkedIn | ❌ | ⚠️ | Hard | ⭐⭐⭐ | 8+ hours |
| Personal Websites | ❌ | ✅ | Scraping | ⭐⭐⭐ | 4 hours |
| ResearchGate | ❌ | ⚠️ | Scraping | ⭐⭐⭐ | 6 hours |
| Google Scholar | ❌ | ⚠️ | Scraping | ⭐⭐⭐⭐ | 6 hours |
| Patents | ❌ | ⚠️ | Medium | ⭐⭐⭐ | 4 hours |
| Conference Speakers | ❌ | ⚠️ | Scraping | ⭐⭐⭐ | 6 hours |
| GitLab/Bitbucket | ❌ | ✅ | Easy | ⭐⭐⭐ | 2 hours |
| Reddit | ❌ | ✅ | Easy | ⭐⭐ | 3 hours |
| YouTube | ❌ | ✅ | Easy | ⭐⭐⭐ | 3 hours |
| Kaggle | ❌ | ✅ | Easy | ⭐⭐⭐ | 2 hours |

---

## Implementation Plan

### MVP (Days 1-3)
**Ishaan's Tasks**:
1. ✅ GitHub API client (`github_api.py`)
   - Search users by language/topics
   - Get profiles and repos
   - Extract candidate data

2. ✅ X DM Simulator (`x_dm_simulator.py`)
   - Simulate X DM interface
   - Profile search (simulated)
   - Message handling

3. ✅ Grok API client (`grok_api.py`)
   - Entity extraction
   - Embeddings
   - Profile summarization

**Total Time**: ~8 hours

### Post-MVP (Future)
**Add sources incrementally**:
- Week 1: arXiv, Stack Overflow
- Week 2: Dev.to, Personal websites
- Week 3: LinkedIn (if API access), Conference speakers
- Week 4+: All other sources

---

## Data Quality Metrics

### For Each Source, Track:
1. **Signal Strength**: How well does it predict candidate quality?
2. **Coverage**: What % of candidates have this data?
3. **Freshness**: How often is data updated?
4. **Reliability**: How accurate is the data?

### MVP Sources Quality:
- **GitHub**: ⭐⭐⭐⭐⭐ (high signal, high coverage, fresh, reliable)
- **X**: ⭐⭐⭐⭐ (good signal, medium coverage, very fresh, reliable)
- **Grok**: ⭐⭐⭐⭐⭐ (excellent for extraction, always available)

---

## Recommendations

### For MVP:
**Stick to 3 sources**: GitHub + X (simulated) + Grok
- Fast to implement
- High quality data
- Covers all needs
- Can demo end-to-end

### For Post-MVP:
**Add incrementally**:
1. arXiv (for research roles)
2. Stack Overflow (for problem-solving)
3. Dev.to (for technical writing)
4. Personal websites (for portfolios)

### For Future:
**Comprehensive sourcing**:
- Add all sources
- Multi-source aggregation
- Confidence scoring
- Data fusion algorithms

---

## Key Takeaways

1. **MVP = 3 sources**: GitHub, X (simulated), Grok
2. **Post-MVP = Add 3-5 more**: arXiv, Stack Overflow, Dev.to, etc.
3. **Future = All sources**: Comprehensive multi-source system

**Focus on quality over quantity for MVP!**

