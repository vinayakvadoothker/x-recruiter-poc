"""
test_end_to_end_edge_cases.py - End-to-end edge case tests

Tests edge cases in the complete flow to ensure robustness.
"""

import pytest
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS


def test_empty_candidate_list():
    """Test end-to-end flow with empty candidate list."""
    role_data = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    candidates = []
    
    bandit = GraphWarmStartedFGTS()
    
    # Should handle empty list gracefully
    bandit.initialize_from_graph(candidates, role_data)
    assert bandit.num_arms == 0
    
    # Selection should raise error
    with pytest.raises(ValueError):
        bandit.select_candidate()


def test_no_graph_similarity_matches():
    """Test when candidates have no similarity to role."""
    role_data = {
        'id': 'role_ml',
        'skills': ['Python', 'CUDA', 'PyTorch'],
        'experience': ['ML Engineer'],
        'education': ['CS']
    }
    
    candidates = [
        {
            'id': 'cand_frontend',
            'skills': ['HTML', 'CSS', 'JavaScript'],
            'experience': ['Web Developer'],
            'education': []
        },
        {
            'id': 'cand_designer',
            'skills': ['Photoshop', 'Illustrator'],
            'experience': ['Graphic Designer'],
            'education': []
        }
    ]
    
    # Build graphs
    role_graph = build_candidate_role_graph({'id': 'role'}, role_data)
    candidate_graphs = [
        build_candidate_role_graph(cand, {'id': 'dummy'})
        for cand in candidates
    ]
    
    # Compute similarities (should be low)
    similarities = [
        compute_graph_similarity(role_graph, cand_graph)
        for cand_graph in candidate_graphs
    ]
    
    # All similarities should be valid
    assert all(0.0 <= sim <= 1.0 for sim in similarities)
    
    # Bandit should still work even with different candidates
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Should still be able to select (exploration)
    selected = bandit.select_candidate()
    assert 0 <= selected < 2


def test_all_candidates_same_similarity():
    """Test when all candidates have identical similarity."""
    role_data = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
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
        },
        {
            'id': 'cand3',
            'skills': ['Python'],
            'experience': [],
            'education': []
        }
    ]
    
    # Build graphs
    role_graph = build_candidate_role_graph({'id': 'role'}, role_data)
    candidate_graphs = [
        build_candidate_role_graph(cand, {'id': 'dummy'})
        for cand in candidates
    ]
    
    # Compute similarities
    similarities = [
        compute_graph_similarity(role_graph, cand_graph)
        for cand_graph in candidate_graphs
    ]
    
    # All should have same similarity (within small tolerance)
    assert all(abs(sim - similarities[0]) < 0.1 for sim in similarities)
    
    # Bandit should still work
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # All should have similar priors
    assert abs(bandit.alpha[0] - bandit.alpha[1]) < 1.0
    assert abs(bandit.alpha[1] - bandit.alpha[2]) < 1.0
    
    # Should still explore
    selections = [bandit.select_candidate() for _ in range(10)]
    assert all(0 <= s < 3 for s in selections)


def test_single_candidate_flow():
    """Test complete flow with single candidate."""
    role_data = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    candidates = [
        {
            'id': 'cand1',
            'skills': ['Python'],
            'experience': [],
            'education': []
        }
    ]
    
    # Complete flow
    role_graph = build_candidate_role_graph({'id': 'role'}, role_data)
    candidate_graph = build_candidate_role_graph(candidates[0], {'id': 'dummy'})
    
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    assert 0.0 <= similarity <= 1.0
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Should always select the only candidate
    for _ in range(10):
        selected = bandit.select_candidate()
        assert selected == 0
    
    # Updates should work
    bandit.update(0, reward=1.0)
    assert bandit.alpha[0] > 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

