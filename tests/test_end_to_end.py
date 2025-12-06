"""
test_end_to_end.py - End-to-end integration test

Tests the complete flow from graph construction [1] through
similarity computation [1] to FG-TS candidate selection [2] and updates.

This is the major integration test that verifies all components
work together correctly, including our novel graph warm-start contribution.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Graph construction and kNN-based similarity

[2] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: FG-TS algorithm for candidate selection

Our Innovation:
This test verifies our novel contribution: using graph structure [1]
to warm-start FG-TS [2] priors, enabling faster learning.

For more details, see CITATIONS.md.
"""

import pytest
import networkx as nx
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS


def test_complete_recruiting_flow():
    """
    Test complete recruiting flow: graph → similarity → FG-TS → selection → update.
    
    This test verifies:
    1. Graph construction works
    2. Graph similarity computation works
    3. FG-TS initialization with graph warm-start works
    4. Candidate selection works
    5. Bayesian updates work
    6. Learning improves over time
    """
    # Step 1: Define role and candidates
    role_data = {
        'id': 'role_llm_inference',
        'title': 'LLM Inference Optimization Engineer',
        'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer'],
        'experience': ['ML Infrastructure', 'HPC', 'Distributed Systems'],
        'education': ['Computer Science', 'Machine Learning']
    }
    
    candidates = [
        {
            'id': 'cand_strong',
            'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer', 'C++'],
            'experience': ['ML Engineer', 'HPC', 'GPU Optimization'],
            'education': ['CS PhD', 'ML Specialization']
        },
        {
            'id': 'cand_medium',
            'skills': ['Python', 'PyTorch', 'TensorFlow'],
            'experience': ['ML Engineer', 'Deep Learning'],
            'education': ['CS Masters']
        },
        {
            'id': 'cand_weak',
            'skills': ['JavaScript', 'React'],
            'experience': ['Frontend Developer'],
            'education': ['Bootcamp']
        }
    ]
    
    # Step 2: Build graphs
    role_graph = build_candidate_role_graph({'id': 'role'}, role_data)
    candidate_graphs = [
        build_candidate_role_graph(cand, {'id': 'dummy'})
        for cand in candidates
    ]
    
    # Verify graphs were created
    assert isinstance(role_graph, nx.Graph)
    assert len(candidate_graphs) == 3
    assert all(isinstance(g, nx.Graph) for g in candidate_graphs)
    
    # Step 3: Compute graph similarities
    similarities = []
    for cand_graph in candidate_graphs:
        sim = compute_graph_similarity(role_graph, cand_graph)
        similarities.append(sim)
        assert 0.0 <= sim <= 1.0
    
    # Verify strong candidate has higher similarity
    assert similarities[0] > similarities[2]  # Strong > Weak
    
    # Step 4: Initialize FG-TS with graph warm-start
    bandit = GraphWarmStartedFGTS(lambda_fg=0.01, b=1000.0)
    bandit.initialize_from_graph(candidates, role_data)
    
    # Verify initialization
    assert bandit.num_arms == 3
    assert 0 in bandit.alpha
    assert 1 in bandit.alpha
    assert 2 in bandit.alpha
    
    # Verify warm-start priors (strong candidate should have higher alpha)
    assert bandit.alpha[0] > bandit.alpha[2]  # Strong candidate > Weak candidate
    
    # Step 5: Select candidates multiple times
    selections = []
    for _ in range(20):
        selected = bandit.select_candidate()
        selections.append(selected)
        assert 0 <= selected < 3
    
    # Step 6: Update bandit with rewards
    # Strong candidate gets positive rewards
    # Weak candidate gets negative rewards
    for i in range(20):
        selected = selections[i]
        
        # Simulate rewards based on candidate quality
        if selected == 0:  # Strong candidate
            reward = 1.0  # Positive reward
            is_qualified = True
        elif selected == 1:  # Medium candidate
            reward = 0.5  # Partial reward
            is_qualified = True
        else:  # Weak candidate
            reward = 0.0  # Negative reward
            is_qualified = False
        
        bandit.update(selected, reward)
    
    # Step 7: Verify learning (strong candidate should be selected more)
    # After updates, strong candidate should have higher success rate
    final_alpha_0 = bandit.alpha[0]
    final_beta_0 = bandit.beta[0]
    final_alpha_2 = bandit.alpha[2]
    final_beta_2 = bandit.beta[2]
    
    # Strong candidate should have higher alpha/beta ratio
    success_rate_0 = final_alpha_0 / (final_alpha_0 + final_beta_0)
    success_rate_2 = final_alpha_2 / (final_alpha_2 + final_beta_2)
    
    assert success_rate_0 > success_rate_2  # Strong candidate learned better
    
    # Step 8: Verify bandit continues to select better candidates
    # Run more selections and verify strong candidate is selected more
    recent_selections = [bandit.select_candidate() for _ in range(10)]
    strong_selections = recent_selections.count(0)
    weak_selections = recent_selections.count(2)
    
    # Strong candidate should be selected more often after learning
    assert strong_selections >= weak_selections


def test_warm_start_vs_cold_start_performance():
    """
    Test that warm-start performs better than cold-start.
    
    This verifies the core innovation: graph warm-start leads to
    faster learning and better performance.
    """
    role_data = {
        'id': 'role1',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    candidates = [
        {
            'id': 'cand_good',
            'skills': ['Python', 'CUDA', 'PyTorch'],
            'experience': ['ML Engineer'],
            'education': ['CS']
        },
        {
            'id': 'cand_bad',
            'skills': ['JavaScript'],
            'experience': ['Frontend'],
            'education': []
        }
    ]
    
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
    
    # Simulate 10 interactions with good candidate getting rewards
    for _ in range(10):
        # Warm-start selection
        warm_selected = warm_bandit.select_candidate()
        warm_reward = 1.0 if warm_selected == 0 else 0.0
        warm_bandit.update(warm_selected, warm_reward)
        
        # Cold-start selection
        cold_selected = cold_bandit.select_candidate()
        cold_reward = 1.0 if cold_selected == 0 else 0.0
        cold_bandit.update(cold_selected, cold_reward)
    
    # Warm-start should have better success rate for good candidate
    warm_success = warm_bandit.alpha[0] / (warm_bandit.alpha[0] + warm_bandit.beta[0])
    cold_success = cold_bandit.alpha[0] / (cold_bandit.alpha[0] + cold_bandit.beta[0])
    
    # Warm-start should learn faster (higher success rate)
    assert warm_success >= cold_success


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

