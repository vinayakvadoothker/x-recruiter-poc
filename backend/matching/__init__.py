"""
matching - Team and interviewer matching system

This module provides matching functionality to find the best team and interviewer
for candidates using vector similarity, bandit selection, and multi-criteria evaluation.

Key module:
- team_matcher: Main matching class for team and interviewer selection
"""

from .team_matcher import TeamPersonMatcher

__all__ = ['TeamPersonMatcher']

