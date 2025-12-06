"""
test_graph_warm_start_integration.py - Test graph warm-start integration

This test verifies that graph similarity [1] is correctly integrated with
FG-TS initialization [2], ensuring priors are set correctly based on graph structure.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Graph similarity computation (kNN-based, Equation 1)

[2] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: FG-TS algorithm and prior initialization

Our Innovation:
These tests verify our novel contribution: using graph structure [1] to
warm-start FG-TS [2] priors. This is the first application of graph
structure as prior knowledge for bandit initialization.

For more details, see CITATIONS.md.
"""

import pytest
import numpy as np
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity


def test_graph_warm_start_priors_correct():
    """
    Test that graph similarity correctly sets priors.
    
    Strong candidates should have higher alpha (optimistic),
    weak candidates should have higher beta (pessimistic).
    """
    candidates = [
        {
            'id': 'cand_strong',
            'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer'],
            'experience': ['ML Engineer', 'HPC'],
            'education': ['CS PhD']
        },
        {
            'id': 'cand_medium',
            'skills': ['Python', 'PyTorch'],
            'experience': ['ML Engineer'],
            'education': ['CS Masters']
        },
        {
            'id': 'cand_weak',
            'skills': ['JavaScript'],
            'experience': ['Frontend Developer'],
            'education': []
        }
    ]
    
    role_data = {
        'id': 'role_llm_inference',
        'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer'],
        'experience': ['ML Infrastructure', 'HPC'],
        'education': ['Computer Science']
    }
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Verify all arms initialized
    assert bandit.num_arms == 3
    assert all(i in bandit.alpha for i in range(3))
    assert all(i in bandit.beta for i in range(3))
    
    # Verify priors are set (not uniform)
    # Strong candidate should have highest alpha
    assert bandit.alpha[0] > bandit.alpha[2], "Strong candidate should have higher alpha"
    
    # Weak candidate should have higher beta (pessimistic)
    assert bandit.beta[2] > bandit.beta[0], "Weak candidate should have higher beta"
    
    # All priors should be >= 1.0 (graph similarity affects them)
    assert all(bandit.alpha[i] >= 1.0 for i in range(3))
    assert all(bandit.beta[i] >= 1.0 for i in range(3))
    
    # At least one should be > 1.0 (graph similarity affects them)
    assert any(bandit.alpha[i] > 1.0 for i in range(3)) or any(bandit.beta[i] > 1.0 for i in range(3))


def test_warm_start_vs_cold_start_initial_advantage():
    """
    Test that warm-start has initial advantage over cold-start.
    
    Warm-start should start with better priors, leading to better
    initial selection behavior.
    """
    candidates = [
        {
            'id': 'cand_strong',
            'skills': ['Python', 'CUDA', 'PyTorch'],
            'experience': ['ML Engineer'],
            'education': ['CS']
        },
        {
            'id': 'cand_weak',
            'skills': ['JavaScript'],
            'experience': ['Frontend'],
            'education': []
        }
    ]
    
    role_data = {
        'id': 'role1',
        'skills': ['Python', 'CUDA'],
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
    
    # Warm-start should have different priors
    assert warm_bandit.alpha[0] != cold_bandit.alpha[0], "Warm-start should have different priors"
    
    # Strong candidate should have higher alpha in warm-start
    assert warm_bandit.alpha[0] > warm_bandit.alpha[1], "Strong candidate should have higher alpha"
    
    # Warm-start initial estimate should favor strong candidate
    warm_estimate_0 = warm_bandit.alpha[0] / (warm_bandit.alpha[0] + warm_bandit.beta[0])
    warm_estimate_1 = warm_bandit.alpha[1] / (warm_bandit.alpha[1] + warm_bandit.beta[1])
    
    assert warm_estimate_0 > warm_estimate_1, "Warm-start should favor strong candidate initially"


def test_graph_similarity_to_prior_conversion():
    """
    Test that graph similarity is correctly converted to priors.
    
    Verify the conversion formula: alpha = 1 + similarity * 10
    """
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
    
    # Build graphs and compute similarity manually
    role_graph = build_candidate_role_graph({'id': 'role'}, role_data)
    candidate_graph = build_candidate_role_graph(candidates[0], {'id': 'dummy'})
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    
    # Initialize bandit
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Verify conversion formula
    expected_alpha = 1.0 + similarity * 10.0
    expected_beta = 1.0 + (1.0 - similarity) * 10.0
    
    assert abs(bandit.alpha[0] - expected_alpha) < 0.01, "Alpha should match conversion formula"
    assert abs(bandit.beta[0] - expected_beta) < 0.01, "Beta should match conversion formula"


def test_warm_start_selection_behavior():
    """
    Test that warm-start leads to better initial selection behavior.
    
    Over many selections, warm-start should select strong candidates
    more often than cold-start.
    """
    candidates = [
        {
            'id': 'cand_strong',
            'skills': ['Python', 'CUDA', 'PyTorch'],
            'experience': ['ML Engineer'],
            'education': ['CS']
        },
        {
            'id': 'cand_weak',
            'skills': ['JavaScript'],
            'experience': ['Frontend'],
            'education': []
        }
    ]
    
    role_data = {
        'id': 'role1',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    # Warm-start bandit
    warm_bandit = GraphWarmStartedFGTS()
    warm_bandit.initialize_from_graph(candidates, role_data)
    
    # Cold-start bandit
    cold_bandit = GraphWarmStartedFGTS()
    cold_bandit.num_arms = 2
    cold_bandit.alpha[0] = 1.0
    cold_bandit.beta[0] = 1.0
    cold_bandit.alpha[1] = 1.0
    cold_bandit.beta[1] = 1.0
    
    # Run many selections
    warm_selections = [warm_bandit.select_candidate() for _ in range(100)]
    cold_selections = [cold_bandit.select_candidate() for _ in range(100)]
    
    # Count selections of strong candidate (index 0)
    warm_strong_count = sum(1 for s in warm_selections if s == 0)
    cold_strong_count = sum(1 for s in cold_selections if s == 0)
    
    # Warm-start should select strong candidate more often
    # (due to better initial priors)
    assert warm_strong_count >= cold_strong_count, "Warm-start should favor strong candidate more"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

