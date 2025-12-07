"""
sample_positions.py - Sample position profiles (800-1,200 profiles)

This module generates realistic position profiles for testing at scale.
Uses generators for memory efficiency and variety.
"""

import random
from typing import Dict, List, Any, Iterator, Optional
from datetime import datetime

POSITION_TITLES = [
    'Senior LLM Inference Optimization Engineer',
    'Staff GPU Computing Engineer',
    'Senior ML Infrastructure Engineer',
    'Distributed Systems Engineer',
    'Frontend Platform Engineer',
    'Backend Services Engineer',
    'Data Engineering Lead',
    'MLOps Engineer',
    'Computer Vision Researcher',
    'NLP Research Scientist',
    'Search Systems Engineer',
    'Mobile Platform Engineer'
]

EXPERIENCE_LEVELS = ['Junior', 'Mid', 'Senior', 'Staff']

COMPANY_NAMES = [
    'TechCorp', 'AI Innovations', 'CloudScale', 'DataFlow Systems',
    'ML Dynamics', 'Platform Labs', 'Infrastructure Co', 'DevOps Solutions',
    'Research Labs', 'Engineering Hub', 'Systems Inc', 'TechStart'
]


def generate_position_profile(position_id: int, team_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate a single position profile.
    
    Args:
        position_id: Unique position ID number
        team_id: Optional team ID to assign
    
    Returns:
        Position profile dictionary matching schema
    """
    title = random.choice(POSITION_TITLES)
    experience_level = random.choice(EXPERIENCE_LEVELS)
    
    # Generate requirements based on title
    if 'LLM' in title or 'GPU' in title:
        must_haves = ['CUDA', 'C++', 'PyTorch']
        nice_to_haves = ['TensorRT', 'Triton', 'Distributed systems']
        tech_stack = ['CUDA', 'C++', 'PyTorch', 'TensorRT']
        requirements = [
            f"{random.randint(5, 10)}+ years CUDA experience",
            "Strong PyTorch knowledge",
            "Experience with LLM inference optimization"
        ]
    elif 'Distributed' in title or 'Systems' in title:
        must_haves = ['Go', 'Rust', 'Distributed Systems']
        nice_to_haves = ['Kubernetes', 'Docker', 'Microservices']
        tech_stack = ['Go', 'Rust', 'Kubernetes', 'Docker']
        requirements = [
            f"{random.randint(5, 10)}+ years systems experience",
            "Strong distributed systems knowledge"
        ]
    elif 'Frontend' in title:
        must_haves = ['React', 'TypeScript', 'JavaScript']
        nice_to_haves = ['Next.js', 'Vue', 'GraphQL']
        tech_stack = ['React', 'TypeScript', 'Next.js']
        requirements = [
            f"{random.randint(3, 8)}+ years frontend experience",
            "Strong React and TypeScript skills"
        ]
    elif 'Backend' in title:
        must_haves = ['Python', 'Django', 'PostgreSQL']
        nice_to_haves = ['FastAPI', 'Redis', 'Kafka']
        tech_stack = ['Python', 'Django', 'PostgreSQL', 'Redis']
        requirements = [
            f"{random.randint(3, 8)}+ years backend experience",
            "Strong Python and database skills"
        ]
    else:
        must_haves = ['Python', 'Machine Learning']
        nice_to_haves = ['PyTorch', 'TensorFlow', 'MLOps']
        tech_stack = ['Python', 'PyTorch', 'TensorFlow']
        requirements = [
            f"{random.randint(3, 8)}+ years experience",
            "Strong technical skills"
        ]
    
    responsibilities = [
        f"Build and maintain {title.lower()} systems",
        "Collaborate with cross-functional teams",
        "Drive technical excellence and best practices"
    ]
    
    # Generate company name
    company = random.choice(COMPANY_NAMES)
    
    return {
        'id': f'position_{position_id:04d}',
        'title': title,
        'company': company,
        'team_id': f'team_{team_id:04d}' if team_id is not None else f'team_{random.randint(0, 100):04d}',
        'description': f"We're looking for a {experience_level.lower()} {title.lower()} to join our team...",
        'requirements': requirements,
        'must_haves': must_haves,
        'nice_to_haves': nice_to_haves,
        'experience_level': experience_level,
        'tech_stack': tech_stack,
        'domains': [title.split()[0] if ' ' in title else title],
        'team_context': f"This role is part of the {title.split()[0]} team, working on critical infrastructure.",
        'responsibilities': responsibilities,
        'priority': random.choice(['high', 'medium', 'low']),
        'status': random.choice(['open', 'in-progress', 'on-hold']),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


def generate_positions(count: int = 1200, teams_count: int = 800) -> Iterator[Dict[str, Any]]:
    """
    Generate position profiles using a generator.
    
    Args:
        count: Number of positions to generate (default: 1200)
        teams_count: Number of teams (for team_id assignment)
    
    Yields:
        Position profile dictionaries
    """
    for i in range(count):
        team_id = random.randint(0, teams_count - 1) if teams_count > 0 else None
        yield generate_position_profile(i, team_id)


# Pre-generated sample (first 15 for quick access)
SAMPLE_POSITIONS = [generate_position_profile(i) for i in range(15)]

