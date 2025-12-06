"""
test_graph_edge_cases.py - Edge case tests for graph construction

Tests edge cases and error handling for graph building.
"""

import pytest
import networkx as nx
from backend.graph.graph_builder import build_candidate_role_graph


def test_empty_candidate_list():
    """Test handling of empty candidate data."""
    candidate = {
        'id': 'cand1',
        'skills': [],
        'experience': [],
        'education': []
    }
    role = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    # Graph should still be created
    assert isinstance(graph, nx.Graph)
    assert graph.has_node('cand1')
    assert graph.has_node('role1')
    
    # No entity nodes for candidate
    candidate_entity_nodes = [n for n in graph.nodes() if 'cand1' in str(n)]
    assert len(candidate_entity_nodes) == 1  # Only candidate node itself


def test_missing_fields():
    """Test handling of missing fields in candidate/role data."""
    candidate = {
        'id': 'cand1'
        # Missing skills, experience, education
    }
    role = {
        'id': 'role1'
        # Missing skills, experience, education
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    # Graph should still be created
    assert isinstance(graph, nx.Graph)
    assert graph.has_node('cand1')
    assert graph.has_node('role1')
    assert graph.has_edge('cand1', 'role1')


def test_single_candidate():
    """Test graph with single candidate."""
    candidate = {
        'id': 'cand1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    role = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    assert isinstance(graph, nx.Graph)
    assert graph.has_node('cand1')
    assert graph.has_node('role1')
    assert graph.has_edge('cand1', 'role1')


def test_all_same_similarity():
    """Test graph with candidates having identical similarity."""
    candidate1 = {
        'id': 'cand1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    candidate2 = {
        'id': 'cand2',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    role = {
        'id': 'role1',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    graph1 = build_candidate_role_graph(candidate1, role)
    graph2 = build_candidate_role_graph(candidate2, role)
    
    # Both graphs should be valid
    assert isinstance(graph1, nx.Graph)
    assert isinstance(graph2, nx.Graph)
    
    # Both should have same structure
    assert graph1.has_node('cand1')
    assert graph2.has_node('cand2')
    assert graph1.has_node('role1')
    assert graph2.has_node('role1')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

