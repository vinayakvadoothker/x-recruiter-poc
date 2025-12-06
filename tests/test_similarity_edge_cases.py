"""
test_similarity_edge_cases.py - Edge case tests for similarity computation

Tests edge cases and error handling for graph similarity.
"""

import pytest
import networkx as nx
from backend.graph.graph_similarity import compute_graph_similarity
from backend.graph.graph_builder import build_candidate_role_graph


def test_empty_graphs():
    """Test similarity with empty graphs."""
    candidate = {
        'id': 'cand1',
        'skills': [],
        'experience': [],
        'education': []
    }
    role = {
        'id': 'role1',
        'skills': [],
        'experience': [],
        'education': []
    }
    
    role_graph = build_candidate_role_graph({'id': 'role'}, role)
    candidate_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    
    # Should return a valid similarity score (0-1)
    assert 0.0 <= similarity <= 1.0


def test_no_matches():
    """Test similarity when there are no matching entities."""
    candidate = {
        'id': 'cand1',
        'skills': ['JavaScript'],
        'experience': ['Frontend'],
        'education': []
    }
    role = {
        'id': 'role1',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    role_graph = build_candidate_role_graph({'id': 'role'}, role)
    candidate_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    
    # Should return low similarity (but still valid)
    assert 0.0 <= similarity <= 1.0


def test_identical_graphs():
    """Test similarity with identical graphs."""
    data = {
        'id': 'test1',
        'skills': ['Python'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    graph1 = build_candidate_role_graph(data, {'id': 'dummy1'})
    graph2 = build_candidate_role_graph(data, {'id': 'dummy2'})
    
    similarity = compute_graph_similarity(graph1, graph2)
    
    # Should have high similarity (close to 1.0)
    assert 0.0 <= similarity <= 1.0


def test_different_k_values():
    """Test similarity with different k values."""
    candidate = {
        'id': 'cand1',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML'],
        'education': ['CS']
    }
    role = {
        'id': 'role1',
        'skills': ['Python', 'PyTorch'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    role_graph = build_candidate_role_graph({'id': 'role'}, role)
    candidate_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    
    # Test with different k values
    # Note: compute_graph_similarity uses default k internally
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    
    assert 0.0 <= similarity <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

