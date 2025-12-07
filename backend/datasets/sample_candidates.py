"""
sample_candidates.py - Sample candidate profiles (1,000-1,500 profiles)

This module generates realistic candidate profiles for testing at scale.
Uses generators for memory efficiency and variety.

Why this scale:
- Tests embedding generation performance (1,000+ profiles)
- Tests vector DB storage/retrieval at scale
- Tests similarity search with large datasets
- Validates system robustness under load
"""

import random
from typing import Dict, List, Any, Iterator
from datetime import datetime

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


def generate_candidate_profile(profile_id: int) -> Dict[str, Any]:
    """
    Generate a single candidate profile.
    
    Args:
        profile_id: Unique profile ID number
    
    Returns:
        Candidate profile dictionary matching schema
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
            'description': f"High-impact project in {domain}"
        }
        for i in range(num_projects)
    ]
    
    # Generate GitHub stats
    github_stats = {
        'total_commits': random.randint(100, 5000),
        'total_stars': random.randint(0, 1000),
        'total_repos': random.randint(5, 50)
    }
    
    return {
        'id': f'candidate_{profile_id:04d}',
        'github_handle': f'dev_{profile_id:04d}',
        'x_handle': f'@dev_{profile_id:04d}' if random.random() > 0.3 else None,
        'linkedin_url': f'https://linkedin.com/in/dev-{profile_id:04d}' if random.random() > 0.2 else None,
        'arxiv_ids': [f'arxiv.{random.randint(2000, 2024)}.{random.randint(10000, 99999)}'] if random.random() > 0.7 else [],
        'skills': skills,
        'experience': experience,
        'experience_years': experience_years,
        'domains': [domain],
        'education': [f"{random.choice(['BS', 'MS', 'PhD'])} Computer Science, {random.choice(['Stanford', 'MIT', 'Berkeley', 'CMU'])}"],
        'projects': projects,
        'github_stats': github_stats,
        'expertise_level': experience_level,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'source': 'inbound' if random.random() > 0.3 else 'outbound',
        'ability_cluster': f"{domain} Experts" if random.random() > 0.5 else None
    }


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

