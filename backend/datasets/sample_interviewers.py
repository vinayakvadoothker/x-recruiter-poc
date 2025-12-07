"""
sample_interviewers.py - Sample interviewer profiles (1,000-1,500 profiles)

This module generates realistic interviewer profiles for testing at scale.
Uses generators for memory efficiency and variety.
"""

import random
from typing import Dict, List, Any, Iterator, Optional
from datetime import datetime

INTERVIEW_STYLES = [
    'Technical deep-dive', 'Behavioral', 'System design', 'Coding challenge',
    'Mixed technical and behavioral', 'Architecture-focused'
]

EVALUATION_FOCUS_OPTIONS = [
    ['Technical depth', 'Problem-solving', 'Code quality'],
    ['System design', 'Scalability', 'Performance'],
    ['Communication', 'Collaboration', 'Technical skills'],
    ['Algorithm knowledge', 'Data structures', 'Optimization']
]

QUESTION_STYLES = [
    'Open-ended, scenario-based',
    'Structured, step-by-step',
    'Free-form discussion',
    'Problem-solving with constraints'
]


def generate_interviewer_profile(interviewer_id: int, team_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate a single interviewer profile.
    
    Args:
        interviewer_id: Unique interviewer ID number
        team_id: Optional team ID to assign
    
    Returns:
        Interviewer profile dictionary matching schema
    """
    # Randomize characteristics
    interview_style = random.choice(INTERVIEW_STYLES)
    evaluation_focus = random.choice(EVALUATION_FOCUS_OPTIONS)
    question_style = random.choice(QUESTION_STYLES)
    
    # Generate expertise
    expertise_pool = ['CUDA', 'C++', 'Python', 'PyTorch', 'Distributed Systems', 
                     'React', 'TypeScript', 'Go', 'Rust', 'Kubernetes']
    num_expertise = random.randint(2, 5)
    expertise = random.sample(expertise_pool, num_expertise)
    
    # Generate specializations
    specialization_pool = ['LLM Inference', 'GPU Optimization', 'System Design',
                          'Frontend Architecture', 'Backend Scalability']
    num_specializations = random.randint(1, 3)
    specializations = random.sample(specialization_pool, num_specializations)
    
    # Interview history
    total_interviews = random.randint(10, 200)
    success_rate = random.uniform(0.3, 0.9)
    successful_hires = int(total_interviews * success_rate)
    
    # Cluster success rates
    cluster_success_rates = {
        'CUDA Experts': random.uniform(0.4, 0.8),
        'LLM Engineers': random.uniform(0.3, 0.7),
        'General ML': random.uniform(0.2, 0.6)
    }
    
    # Generate phone number (required by database schema)
    phone_number = f'+1{random.randint(2000000000, 9999999999)}'
    
    return {
        'id': f'interviewer_{interviewer_id:04d}',
        'name': f'Interviewer {interviewer_id}',
        'phone_number': phone_number,
        'email': f'interviewer_{interviewer_id:04d}@example.com',
        'team_id': f'team_{team_id:04d}' if team_id is not None else f'team_{random.randint(0, 100):04d}',
        'expertise': expertise,
        'expertise_level': random.choice(['Mid', 'Senior', 'Staff']),
        'specializations': specializations,
        'interview_style': interview_style,
        'evaluation_focus': evaluation_focus,
        'question_style': question_style,
        'total_interviews': total_interviews,
        'successful_hires': successful_hires,
        'success_rate': success_rate,
        'cluster_success_rates': cluster_success_rates,
        'availability': {
            'timezone': random.choice(['PST', 'EST', 'CST', 'GMT']),
            'hours': random.choice(['9am-5pm', '10am-6pm', 'Flexible'])
        },
        'preferred_interview_types': random.sample(['Technical', 'Behavioral', 'System Design'], 2),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


def generate_interviewers(count: int = 6, teams_count: int = 10) -> Iterator[Dict[str, Any]]:
    """
    Generate interviewer profiles using a generator.
    
    Args:
        count: Number of interviewers to generate (default: 1500)
        teams_count: Number of teams (for team_id assignment)
    
    Yields:
        Interviewer profile dictionaries
    """
    for i in range(count):
        team_id = random.randint(0, teams_count - 1) if teams_count > 0 else None
        yield generate_interviewer_profile(i, team_id)


# Pre-generated sample (first 20 for quick access)
SAMPLE_INTERVIEWERS = [generate_interviewer_profile(i) for i in range(20)]

