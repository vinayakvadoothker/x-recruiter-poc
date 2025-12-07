"""
sample_candidates.py - Sample candidate profiles (1,000-1,500 profiles)

This module generates realistic candidate profiles for testing at scale.
Uses generators for memory efficiency and variety.

Generates 500+ datapoints per candidate matching CANDIDATE_SCHEMA.md:
- Identifiers (15+ datapoints)
- Core Profile (50+ datapoints)
- Resume Data (30+ datapoints)
- GitHub Data (100+ datapoints)
- arXiv Data (80+ datapoints)
- X Data (150+ datapoints)
- DM Data (25+ datapoints)
- Analytics (50+ datapoints)
- Metadata (10+ datapoints)

REQUIREMENTS:
- Every candidate MUST have a unique x_handle (X/Twitter handle)
- x_handle is a required unique identifier for all candidates
- Format: 'dev_{profile_id:04d}' (e.g., 'dev_0001', 'dev_0002')
- This ensures candidates can be uniquely identified and tracked via X API

Why this scale:
- Tests embedding generation performance (1,000+ profiles)
- Tests vector DB storage/retrieval at scale
- Tests similarity search with large datasets
- Validates system robustness under load
"""

import random
from typing import Dict, List, Any, Iterator, Optional
from datetime import datetime, timedelta

# Skill pools for variety
SKILL_POOLS = {
    'ml': ['PyTorch', 'TensorFlow', 'CUDA', 'C++', 'Python', 'JAX', 'Transformers'],
    'systems': ['C++', 'Rust', 'Go', 'Distributed Systems', 'Kubernetes', 'Docker'],
    'frontend': ['React', 'TypeScript', 'Next.js', 'Vue', 'JavaScript'],
    'backend': ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Redis', 'Kafka'],
    'data': ['Python', 'Pandas', 'Spark', 'SQL', 'Airflow', 'dbt'],
    'mobile': ['Swift', 'Kotlin', 'React Native', 'Flutter', 'iOS', 'Android']
}

DOMAIN_POOLS = [
    'LLM Inference', 'GPU Computing', 'Deep Learning', 'Distributed Systems',
    'Web Development', 'Mobile Development', 'Data Engineering', 'MLOps',
    'Computer Vision', 'NLP', 'Recommendation Systems', 'Search Systems'
]

EXPERIENCE_LEVELS = ['Junior', 'Mid', 'Senior', 'Staff']

# Name pools for variety
FIRST_NAMES = [
    'Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn',
    'Sam', 'Jamie', 'Dakota', 'Cameron', 'Blake', 'Sage', 'River', 'Phoenix',
    'Chris', 'Pat', 'Drew', 'Lee', 'Kai', 'Reese', 'Skylar', 'Rowan'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor',
    'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris', 'Sanchez'
]


def _generate_github_repos(count: int, skills: List[str], domain: str) -> List[Dict[str, Any]]:
    """Generate GitHub repositories with full metadata."""
    repos = []
    languages = ['Python', 'JavaScript', 'TypeScript', 'C++', 'Rust', 'Go', 'Java', 'Swift', 'Kotlin']
    repo_languages = [lang for lang in languages if lang in skills] or languages[:3]
    
    for i in range(count):
        lang = random.choice(repo_languages)
        created_days_ago = random.randint(30, 2000)
        updated_days_ago = random.randint(1, created_days_ago)
        
        repos.append({
            'id': f'repo_{random.randint(100000, 999999)}',
            'name': f'{domain.lower().replace(" ", "-")}-project-{i+1}',
            'description': f'Open source project in {domain} using {lang}',
            'language': lang,
            'stars': random.randint(0, 5000),
            'forks': random.randint(0, 500),
            'created_at': (datetime.now() - timedelta(days=created_days_ago)).isoformat(),
            'updated_at': (datetime.now() - timedelta(days=updated_days_ago)).isoformat(),
            'topics': random.sample(['machine-learning', 'ai', 'deep-learning', 'open-source'], k=random.randint(1, 3)),
            'contributors': [f'contributor_{j}' for j in range(random.randint(1, 10))],
            'commits': random.randint(10, 1000),
            'lines_of_code': random.randint(1000, 50000)
        })
    return repos


def _generate_arxiv_papers(count: int, domain: str) -> List[Dict[str, Any]]:
    """Generate arXiv papers with full metadata."""
    papers = []
    categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.NE', 'cs.SY', 'cs.DC', 'cs.SE']
    
    for i in range(count):
        year = random.randint(2018, 2024)
        month = random.randint(1, 12)
        paper_id = f'{year}.{random.randint(10000, 99999)}'
        
        papers.append({
            'id': paper_id,
            'title': f'Advances in {domain}: A Novel Approach',
            'authors': [f'Author {j}' for j in range(random.randint(1, 5))],
            'abstract': f'This paper presents novel techniques in {domain}...',
            'categories': random.sample(categories, k=random.randint(1, 2)),
            'published': f'{year}-{month:02d}-{random.randint(1, 28):02d}',
            'updated': f'{year}-{random.randint(month, 12):02d}-{random.randint(1, 28):02d}',
            'pdf_url': f'https://arxiv.org/pdf/{paper_id}.pdf',
            'citation_count': random.randint(0, 500) if random.random() > 0.3 else None,
            'references': [f'arxiv.{random.randint(2015, year)}.{random.randint(10000, 99999)}' 
                          for _ in range(random.randint(5, 30))] if random.random() > 0.5 else None
        })
    return papers


def _generate_x_posts(count: int, domain: str) -> List[Dict[str, Any]]:
    """Generate X/Twitter posts with full metadata."""
    posts = []
    hashtags = ['#AI', '#MachineLearning', '#DeepLearning', '#Tech', '#OpenSource', '#SoftwareEngineering']
    
    for i in range(count):
        days_ago = random.randint(1, 365)
        post_text = f"Excited to share our latest work in {domain}! {random.choice(hashtags)}"
        
        posts.append({
            'id': f'tweet_{random.randint(1000000000000000000, 9999999999999999999)}',
            'text': post_text,
            'created_at': (datetime.now() - timedelta(days=days_ago)).isoformat(),
            'lang': 'en',
            'metrics': {
                'like_count': random.randint(0, 10000),
                'retweet_count': random.randint(0, 1000),
                'reply_count': random.randint(0, 500),
                'quote_count': random.randint(0, 200),
                'impression_count': random.randint(100, 100000),
                'bookmark_count': random.randint(0, 500)
            },
            'entities': {
                'urls': [{'url': f'https://example.com/post-{i}'}] if random.random() > 0.5 else [],
                'mentions': [{'username': f'user_{j}'} for j in range(random.randint(0, 3))],
                'hashtags': [{'tag': tag.replace('#', '')} for tag in random.sample(hashtags, k=random.randint(0, 2))]
            }
        })
    return posts




def _calculate_data_completeness(profile: Dict[str, Any]) -> float:
    """Calculate data completeness score (0.0-1.0)."""
    # x_handle is now a required field (unique identifier)
    required_fields = ['id', 'name', 'phone_number', 'skills', 'domains', 'expertise_level', 'experience_years', 'x_handle']
    optional_fields = [
        'github_handle', 'linkedin_url', 'arxiv_author_id',
        'resume_text', 'repos', 'papers', 'posts'
    ]
    
    required_score = sum(1 for field in required_fields if profile.get(field) is not None) / len(required_fields)
    optional_score = sum(1 for field in optional_fields if profile.get(field) is not None) / len(optional_fields)
    
    return (required_score * 0.7) + (optional_score * 0.3)


def generate_candidate_profile(profile_id: int) -> Dict[str, Any]:
    """
    Generate a single candidate profile with 500+ datapoints matching CANDIDATE_SCHEMA.md.
    
    Args:
        profile_id: Unique profile ID number
    
    Returns:
        Candidate profile dictionary matching comprehensive schema
    """
    # Randomize profile characteristics
    domain = random.choice(DOMAIN_POOLS)
    experience_level = random.choice(EXPERIENCE_LEVELS)
    experience_years = {
        'Junior': random.randint(1, 2),
        'Mid': random.randint(3, 5),
        'Senior': random.randint(6, 10),
        'Staff': random.randint(11, 15)
    }[experience_level]
    
    # Select skills based on domain
    if 'LLM' in domain or 'GPU' in domain:
        skill_pool = SKILL_POOLS['ml']
    elif 'Distributed' in domain or 'Systems' in domain:
        skill_pool = SKILL_POOLS['systems']
    elif 'Web' in domain:
        skill_pool = SKILL_POOLS['frontend'] + SKILL_POOLS['backend']
    elif 'Data' in domain:
        skill_pool = SKILL_POOLS['data']
    elif 'Mobile' in domain:
        skill_pool = SKILL_POOLS['mobile']
    else:
        skill_pool = SKILL_POOLS['ml'] + SKILL_POOLS['backend']
    
    num_skills = random.randint(3, 8)
    skills = random.sample(skill_pool, min(num_skills, len(skill_pool)))
    
    # Generate name and identifiers
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    
    # Determine which platforms this candidate is on
    has_github = random.random() > 0.2
    has_x = random.random() > 0.3
    has_linkedin_url = random.random() > 0.2  # Only URL, no data gathering
    has_arxiv = random.random() > 0.5
    
    # REQUIREMENT: Every candidate MUST have a unique x_handle
    # x_handle is a required unique identifier for tracking via X API
    github_handle = f'dev_{profile_id:04d}' if has_github else None
    x_handle = f'dev_{profile_id:04d}'  # Always present, unique per candidate
    
    # Generate GitHub data
    num_repos = random.randint(5, 50) if has_github else 0
    repos = _generate_github_repos(num_repos, skills, domain) if has_github else []
    
    github_stats = {
        'total_repos': len(repos),
        'total_stars': sum(r['stars'] for r in repos),
        'total_forks': sum(r['forks'] for r in repos),
        'total_commits': sum(r['commits'] for r in repos),
        'languages': {lang: random.randint(1000, 50000) for lang in skills[:5]},
        'topics': list(set([topic for repo in repos for topic in repo.get('topics', [])])),
        'contribution_graph': [random.randint(0, 20) for _ in range(52)]
    } if has_github else {}
    
    github_contributions = [
        {
            'date': (datetime.now() - timedelta(days=i)).isoformat(),
            'count': random.randint(0, 10)
        }
        for i in range(365)
    ] if has_github else []
    
    # Generate arXiv data
    num_papers = random.randint(1, 10) if has_arxiv else 0
    papers = _generate_arxiv_papers(num_papers, domain) if has_arxiv else []
    
    arxiv_author_id = f"{last_name.lower()}_{first_name[0].lower()}_1" if has_arxiv and random.random() > 0.5 else None
    arxiv_ids = [p['id'] for p in papers]
    
    arxiv_stats = {
        'total_papers': len(papers),
        'total_citations': sum(p.get('citation_count', 0) or 0 for p in papers),
        'h_index': random.randint(2, 15) if papers else None,
        'research_areas': [domain, random.choice(DOMAIN_POOLS)],
        'co_authors': [f'coauthor_{i}' for i in range(random.randint(5, 20))],
        'publication_years': {year: sum(1 for p in papers if p['published'].startswith(str(year))) 
                             for year in range(2018, 2025)}
    } if has_arxiv else None
    
    research_areas = [domain] + random.sample(DOMAIN_POOLS, k=random.randint(0, 2))
    
    # Generate X/Twitter data
    num_posts = random.randint(10, 50) if has_x else 0
    posts = _generate_x_posts(num_posts, domain) if has_x else []
    
    x_analytics_summary = {
        'total_tweets_analyzed': len(posts),
        'avg_engagement_rate': random.uniform(0.01, 0.10),
        'total_followers': random.randint(100, 100000),
        'most_active_month': random.choice(['January', 'February', 'March', 'April', 'May', 'June']),
        'content_languages': ['en']
    } if has_x else {}
    
    # LinkedIn: Only URL, no data gathering
    
    # Generate resume data
    has_resume = random.random() > 0.4
    resume_text = f"""
    {name}
    {domain} Expert
    
    Experience:
    {chr(10).join([f"- {exp}" for exp in [f"{experience_years} years in {domain}", f"Built scalable {domain.lower()} systems"]])}
    
    Skills: {', '.join(skills)}
    Education: {random.choice(['BS', 'MS', 'PhD'])} Computer Science, {random.choice(['Stanford', 'MIT', 'Berkeley', 'CMU'])}
    """ if has_resume else None
    
    resume_parsed = {
        'skills': skills,
        'experience': [
            {
                'title': 'Software Engineer',
                'company': random.choice(['Google', 'Microsoft', 'Meta']),
                'duration': f'{experience_years} years',
                'description': f'Worked on {domain} projects'
            }
        ],
        'education': [
            {
                'degree': random.choice(['BS', 'MS', 'PhD']),
                'school': random.choice(['Stanford', 'MIT', 'Berkeley', 'CMU']),
                'field': 'Computer Science'
            }
        ],
        'certifications': random.sample(['AWS Certified', 'Google Cloud', 'Kubernetes'], k=random.randint(0, 2)),
        'languages': ['English', random.choice(['Spanish', 'French', 'Mandarin'])],
        'summary': f'Experienced {domain} professional with {experience_years} years of experience'
    } if has_resume else None
    
    # Generate DM data
    has_dm_history = random.random() > 0.6
    dm_responses = [
        {
            'message_id': f'msg_{i}',
            'text': random.choice([
                'Here is my resume',
                'My GitHub is github.com/username',
                'I can share my arXiv author ID'
            ]),
            'timestamp': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            'direction': random.choice(['sent', 'received']),
            'extracted_data': {'field': 'resume'} if random.random() > 0.5 else None
        }
        for i in range(random.randint(1, 5))
    ] if has_dm_history else None
    
    dm_requested_fields = random.sample(['resume', 'arxiv_id', 'github_handle', 'linkedin_url'], 
                                       k=random.randint(0, 3)) if has_dm_history else None
    dm_provided_fields = random.sample(dm_requested_fields or [], 
                                      k=random.randint(0, len(dm_requested_fields or []))) if has_dm_history else None
    dm_last_contact = (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat() if has_dm_history else None
    dm_response_rate = random.uniform(0.5, 1.0) if has_dm_history else None
    
    # Generate analytics
    engagement_metrics = {
        'cross_platform_score': random.uniform(0.5, 1.0),
        'github_activity': random.uniform(0.3, 1.0) if has_github else 0.0,
        'x_engagement': random.uniform(0.2, 0.8) if has_x else 0.0,
        'arxiv_impact': random.uniform(0.0, 1.0) if has_arxiv else 0.0
    }
    
    activity_patterns = {
        'posting_frequency': random.uniform(0.1, 2.0),  # posts per day
        'most_active_day': random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']),
        'most_active_hour': random.randint(9, 17),
        'timezone': random.choice(['PST', 'EST', 'UTC'])
    }
    
    content_quality_score = random.uniform(0.6, 1.0)
    technical_depth_score = random.uniform(0.5, 1.0)
    
    # Generate experience descriptions
    experience = [
        f"{experience_years} years in {domain}",
        f"Built scalable {domain.lower()} systems",
        f"Expert in {random.choice(skills)}"
    ]
    
    # Generate projects
    num_projects = random.randint(1, 4)
    projects = [
        {
            'name': f"{domain} Project {i+1}",
            'description': f"High-impact project in {domain}",
            'technologies': random.sample(skills, k=min(3, len(skills)))
        }
        for i in range(num_projects)
    ]
    
    # Generate education
    education = [
        f"{random.choice(['BS', 'MS', 'PhD'])} Computer Science, {random.choice(['Stanford', 'MIT', 'Berkeley', 'CMU'])}"
    ]
    
    # Generate metadata
    created_at = datetime.now() - timedelta(days=random.randint(1, 365))
    updated_at = datetime.now() - timedelta(days=random.randint(0, 30))
    
    last_gathered_from = []
    if has_github:
        last_gathered_from.append('github')
    if has_x:
        last_gathered_from.append('x')
    if has_arxiv:
        last_gathered_from.append('arxiv')
    
    gathering_timestamp = {
        platform: (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        for platform in last_gathered_from
    } if last_gathered_from else None
    
    # Build complete profile
    profile = {
        # Identifiers (15+ datapoints)
        'id': f'candidate_{profile_id:04d}',
        'name': name,
        'phone_number': f'+1{random.randint(2000000000, 9999999999)}',
        'email': f'{first_name.lower()}.{last_name.lower()}@example.com' if random.random() > 0.3 else None,
        'github_handle': github_handle,
        'github_user_id': str(random.randint(100000, 999999)) if has_github else None,
        'x_handle': x_handle,  # REQUIRED: Unique identifier for all candidates
        'x_user_id': str(random.randint(1000000000000000000, 9999999999999999999)) if has_x else None,
        'linkedin_url': f'https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{profile_id:04d}' if has_linkedin_url else None,
        'arxiv_author_id': arxiv_author_id,
        'arxiv_ids': arxiv_ids,
        'orcid_id': f'0000-0000-0000-{random.randint(1000, 9999)}' if has_arxiv and random.random() > 0.7 else None,
        
        # Core Profile Data (50+ datapoints)
        'skills': skills,
        'domains': [domain] + random.sample([d for d in DOMAIN_POOLS if d != domain], k=random.randint(0, 2)),
        'expertise_level': experience_level,
        'experience': experience,
        'experience_years': experience_years,
        'education': education,
        'projects': projects,
        
        # Resume Data (30+ datapoints)
        'resume_text': resume_text,
        'resume_url': f'https://example.com/resumes/{profile_id:04d}.pdf' if has_resume and random.random() > 0.5 else None,
        'resume_parsed': resume_parsed,
        
        # GitHub Data (100+ datapoints)
        'repos': repos,
        'github_stats': github_stats,
        'github_contributions': github_contributions,
        
        # arXiv Data (80+ datapoints)
        'papers': papers,
        'arxiv_stats': arxiv_stats,
        'research_areas': research_areas,
        
        # X Data (150+ datapoints)
        'posts': posts,
        'x_analytics_summary': x_analytics_summary,
        
        # DM-Gathered Data (25+ datapoints)
        'dm_responses': dm_responses,
        'dm_requested_fields': dm_requested_fields,
        'dm_provided_fields': dm_provided_fields,
        'dm_last_contact': dm_last_contact,
        'dm_response_rate': dm_response_rate,
        
        # Analytics & Metrics (50+ datapoints)
        'engagement_metrics': engagement_metrics,
        'activity_patterns': activity_patterns,
        'content_quality_score': content_quality_score,
        'technical_depth_score': technical_depth_score,
        
        # Metadata (10+ datapoints)
        'created_at': created_at,
        'updated_at': updated_at,
        'source': 'inbound' if random.random() > 0.3 else 'outbound',
        'data_completeness': 0.0,  # Will be calculated below
        'last_gathered_from': last_gathered_from,
        'gathering_timestamp': gathering_timestamp,
        
        # Legacy field (for backward compatibility)
        'ability_cluster': f"{domain} Experts" if random.random() > 0.5 else None
    }
    
    # Calculate data completeness
    profile['data_completeness'] = _calculate_data_completeness(profile)
    
    return profile


def generate_candidates(count: int = 1500) -> Iterator[Dict[str, Any]]:
    """
    Generate candidate profiles using a generator for memory efficiency.
    
    Args:
        count: Number of candidates to generate (default: 1500)
    
    Yields:
        Candidate profile dictionaries
    """
    for i in range(count):
        yield generate_candidate_profile(i)


# Pre-generated sample (first 20 for quick access)
SAMPLE_CANDIDATES = [generate_candidate_profile(i) for i in range(20)]

