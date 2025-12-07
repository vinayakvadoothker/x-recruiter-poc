"""
sample_teams.py - Sample team profiles (500-800 profiles)

This module generates realistic team profiles for testing at scale.
Uses generators for memory efficiency and variety.
"""

import random
from typing import Dict, List, Any, Iterator
from datetime import datetime

TEAM_NAMES = [
    'LLM Inference Optimization', 'GPU Computing', 'ML Infrastructure',
    'Distributed Systems', 'Frontend Platform', 'Backend Services',
    'Data Engineering', 'MLOps', 'Computer Vision', 'NLP Research',
    'Search Systems', 'Recommendation Engine', 'Mobile Platform',
    'Developer Tools', 'Security Engineering', 'DevOps', 'SRE'
]

DEPARTMENTS = [
    'AI Infrastructure', 'Platform Engineering', 'Product Engineering',
    'Research', 'Infrastructure', 'Data Platform', 'Mobile Engineering'
]

WORK_STYLES = ['Remote', 'Hybrid (2 days in office)', 'Hybrid (3 days in office)', 'On-site']


def generate_team_profile(team_id: int) -> Dict[str, Any]:
    """
    Generate a single team profile.
    
    Args:
        team_id: Unique team ID number
    
    Returns:
        Team profile dictionary matching schema
    """
    team_name = random.choice(TEAM_NAMES)
    department = random.choice(DEPARTMENTS)
    
    # Generate needs based on team name
    if 'LLM' in team_name or 'GPU' in team_name:
        needs = ['CUDA expertise', 'GPU optimization', 'LLM inference specialists']
        expertise = ['CUDA', 'GPU Computing', 'LLM Inference', 'PyTorch']
        stack = ['CUDA', 'C++', 'PyTorch', 'TensorRT']
    elif 'Distributed' in team_name or 'Systems' in team_name:
        needs = ['Systems engineers', 'Distributed systems expertise']
        expertise = ['Distributed Systems', 'Kubernetes', 'Go', 'Rust']
        stack = ['Go', 'Rust', 'Kubernetes', 'Docker']
    elif 'Frontend' in team_name:
        needs = ['Frontend engineers', 'React experts']
        expertise = ['React', 'TypeScript', 'Next.js']
        stack = ['React', 'TypeScript', 'Next.js', 'Node.js']
    elif 'Backend' in team_name:
        needs = ['Backend engineers', 'API developers']
        expertise = ['Python', 'Django', 'PostgreSQL']
        stack = ['Python', 'Django', 'PostgreSQL', 'Redis']
    else:
        needs = ['Software engineers', 'Full-stack developers']
        expertise = ['Python', 'JavaScript', 'PostgreSQL']
        stack = ['Python', 'JavaScript', 'PostgreSQL']
    
    member_count = random.randint(3, 15)
    num_open_positions = random.randint(0, 3)
    open_positions = [f'position_{team_id}_{i}' for i in range(num_open_positions)]
    
    return {
        'id': f'team_{team_id:04d}',
        'name': f'{team_name} Team {team_id}',
        'department': department,
        'member_count': member_count,
        'member_ids': [f'interviewer_{team_id}_{i}' for i in range(member_count)],
        'needs': needs,
        'open_positions': open_positions,
        'hiring_priorities': needs[:2],  # Top 2 needs
        'expertise': expertise,
        'stack': stack,
        'domains': [team_name.split()[0] if ' ' in team_name else team_name],
        'culture': random.choice([
            'Fast-paced, research-oriented, high-impact',
            'Collaborative, mentorship-focused, growth-oriented',
            'Data-driven, results-focused, innovative',
            'Engineering excellence, technical depth, ownership'
        ]),
        'work_style': random.choice(WORK_STYLES),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


def generate_teams(count: int = 800) -> Iterator[Dict[str, Any]]:
    """
    Generate team profiles using a generator.
    
    Args:
        count: Number of teams to generate (default: 800)
    
    Yields:
        Team profile dictionaries
    """
    for i in range(count):
        yield generate_team_profile(i)


# Pre-generated sample (first 10 for quick access)
SAMPLE_TEAMS = [generate_team_profile(i) for i in range(10)]

