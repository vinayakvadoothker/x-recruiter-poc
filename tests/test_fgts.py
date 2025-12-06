"""
test_fgts.py - Tests for Feel-Good Thompson Sampling algorithm

Tests the FG-TS bandit implementation including graph warm-start,
candidate selection, and Bayesian updates.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Graph construction and similarity (graph warm-start)

[2] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Feel-Good Thompson Sampling algorithm
    - Tests verify: FG-TS selection, feel-good bonus, Bayesian updates

Our Innovation:
Graph-warm-started bandits: Using [1] to initialize [2] priors.
Tests verify this novel combination works correctly.

For more details, see CITATIONS.md.
"""

import pytest
import numpy as np
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS


def test_fgts_initialization():
    """Test FG-TS bandit initialization."""
    bandit = GraphWarmStartedFGTS(lambda_fg=0.01, b=1000.0)
    
    assert bandit.lambda_fg == 0.01
    assert bandit.b == 1000.0
    assert len(bandit.alpha) == 0
    assert len(bandit.beta) == 0


def test_fgts_graph_warm_start():
    """Test graph warm-start initialization."""
    bandit = GraphWarmStartedFGTS()
    
    candidates = [
        {
            'id': 'cand1',
            'skills': ['Python', 'CUDA'],
            'experience': ['ML Engineer'],
            'education': ['CS Degree']
        },
        {
            'id': 'cand2',
            'skills': ['JavaScript'],
            'experience': ['Frontend Dev'],
            'education': []
        }
    ]
    
    role_data = {
        'id': 'role1',
        'skills': ['Python', 'PyTorch'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    bandit.initialize_from_graph(candidates, role_data)
    
    # Verify priors are set
    assert bandit.num_arms == 2
    assert 0 in bandit.alpha
    assert 1 in bandit.alpha
    
    # Verify priors are set (graph similarity should affect them)
    # Candidate 0 should have higher alpha (more similar to role)
    assert bandit.alpha[0] >= 1.0
    assert bandit.beta[0] >= 1.0
    
    # At least one should be > 1.0 (graph similarity affects priors)
    assert bandit.alpha[0] > 1.0 or bandit.beta[0] > 1.0


def test_fgts_candidate_selection():
    """Test candidate selection using FG-TS."""
    bandit = GraphWarmStartedFGTS()
    
    candidates = [
        {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []},
        {'id': 'cand2', 'skills': ['Java'], 'experience': [], 'education': []}
    ]
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit.initialize_from_graph(candidates, role_data)
    
    # Select candidate multiple times to verify it works
    selections = [bandit.select_candidate() for _ in range(10)]
    
    # All selections should be valid arm indices
    assert all(0 <= sel < 2 for sel in selections)
    
    # Should select both candidates at some point (exploration)
    assert 0 in selections
    assert 1 in selections


def test_fgts_bayesian_update():
    """Test Bayesian update after observing reward."""
    bandit = GraphWarmStartedFGTS()
    
    candidates = [
        {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []}
    ]
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit.initialize_from_graph(candidates, role_data)
    
    initial_alpha = bandit.alpha[0]
    initial_beta = bandit.beta[0]
    
    # Update with positive reward
    bandit.update(0, reward=1.0)
    assert bandit.alpha[0] == initial_alpha + 1.0
    assert bandit.beta[0] == initial_beta
    
    # Update with negative reward
    bandit.update(0, reward=0.0)
    assert bandit.alpha[0] == initial_alpha + 1.0
    assert bandit.beta[0] == initial_beta + 1.0


def test_fgts_warm_start_vs_cold_start():
    """Test warm-start vs cold-start comparison."""
    candidates = [
        {
            'id': 'cand1',
            'skills': ['Python', 'CUDA'],
            'experience': ['ML Engineer'],
            'education': ['CS']
        },
        {
            'id': 'cand2',
            'skills': ['JavaScript'],
            'experience': ['Frontend'],
            'education': []
        }
    ]
    role_data = {
        'id': 'role1',
        'skills': ['Python', 'PyTorch'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    # Warm-start bandit
    warm_bandit = GraphWarmStartedFGTS()
    warm_bandit.initialize_from_graph(candidates, role_data)
    
    # Cold-start bandit (uniform priors)
    cold_bandit = GraphWarmStartedFGTS()
    cold_bandit.num_arms = 2
    cold_bandit.alpha[0] = 1.0
    cold_bandit.beta[0] = 1.0
    cold_bandit.alpha[1] = 1.0
    cold_bandit.beta[1] = 1.0
    
    # Warm-start should have different priors (at least alpha should differ)
    assert warm_bandit.alpha[0] != cold_bandit.alpha[0] or warm_bandit.beta[0] != cold_bandit.beta[0]
    
    # Candidate 0 should have higher alpha in warm-start (more similar to role)
    assert warm_bandit.alpha[0] >= warm_bandit.alpha[1]


def test_fgts_edge_cases():
    """Test edge cases."""
    bandit = GraphWarmStartedFGTS()
    
    # Test selection before initialization
    with pytest.raises(ValueError):
        bandit.select_candidate()
    
    # Test update with invalid arm
    candidates = [{'id': 'cand1', 'skills': [], 'experience': [], 'education': []}]
    role_data = {'id': 'role1', 'skills': [], 'experience': [], 'education': []}
    bandit.initialize_from_graph(candidates, role_data)
    
    with pytest.raises(ValueError):
        bandit.update(999, reward=1.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

