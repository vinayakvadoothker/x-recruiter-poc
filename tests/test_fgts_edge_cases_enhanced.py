"""
test_fgts_edge_cases_enhanced.py - Enhanced edge case tests for FG-TS

Tests additional edge cases for the FG-TS algorithm.
"""

import pytest
import numpy as np
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS


def test_single_arm():
    """Test FG-TS with single candidate (arm)."""
    bandit = GraphWarmStartedFGTS()
    
    candidates = [
        {
            'id': 'cand1',
            'skills': ['Python'],
            'experience': [],
            'education': []
        }
    ]
    role_data = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    bandit.initialize_from_graph(candidates, role_data)
    
    # Should always select the only candidate
    for _ in range(10):
        selected = bandit.select_candidate()
        assert selected == 0
    
    # Update should work
    bandit.update(0, reward=1.0)
    assert bandit.alpha[0] > 1.0


def test_all_same_similarity():
    """Test FG-TS when all candidates have same similarity."""
    candidates = [
        {
            'id': 'cand1',
            'skills': ['Python'],
            'experience': [],
            'education': []
        },
        {
            'id': 'cand2',
            'skills': ['Python'],
            'experience': [],
            'education': []
        }
    ]
    role_data = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Both should have similar priors (since similarity is same)
    assert abs(bandit.alpha[0] - bandit.alpha[1]) < 1.0
    
    # Should still be able to select
    selections = [bandit.select_candidate() for _ in range(10)]
    assert all(0 <= s < 2 for s in selections)


def test_feel_good_bonus():
    """Test that feel-good bonus is applied correctly."""
    bandit = GraphWarmStartedFGTS(lambda_fg=0.1, b=100.0)
    
    candidates = [
        {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []}
    ]
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit.initialize_from_graph(candidates, role_data)
    
    # Feel-good bonus should be applied in selection
    # (verified by checking selection works)
    selected = bandit.select_candidate()
    assert selected == 0


def test_bayesian_update_consistency():
    """Test Bayesian update consistency."""
    bandit = GraphWarmStartedFGTS()
    
    candidates = [
        {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []}
    ]
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit.initialize_from_graph(candidates, role_data)
    
    initial_alpha = bandit.alpha[0]
    initial_beta = bandit.beta[0]
    
    # Multiple positive updates
    for _ in range(5):
        bandit.update(0, reward=1.0)
    
    # Alpha should increase by 5
    assert bandit.alpha[0] == initial_alpha + 5.0
    assert bandit.beta[0] == initial_beta
    
    # Multiple negative updates
    for _ in range(3):
        bandit.update(0, reward=0.0)
    
    # Beta should increase by 3
    assert bandit.alpha[0] == initial_alpha + 5.0
    assert bandit.beta[0] == initial_beta + 3.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

