"""
datasets - Sample datasets for testing and development

This module provides large-scale sample datasets for all 4 profile types:
- Candidates: 1,000-1,500 profiles
- Teams: 500-800 profiles
- Interviewers: 1,000-1,500 profiles
- Positions: 800-1,200 profiles

All datasets use generators for memory efficiency and batch processing.
"""

from .sample_candidates import generate_candidates, SAMPLE_CANDIDATES
from .sample_teams import generate_teams, SAMPLE_TEAMS
from .sample_interviewers import generate_interviewers, SAMPLE_INTERVIEWERS
from .sample_positions import generate_positions, SAMPLE_POSITIONS

__all__ = [
    'generate_candidates',
    'SAMPLE_CANDIDATES',
    'generate_teams',
    'SAMPLE_TEAMS',
    'generate_interviewers',
    'SAMPLE_INTERVIEWERS',
    'generate_positions',
    'SAMPLE_POSITIONS'
]

