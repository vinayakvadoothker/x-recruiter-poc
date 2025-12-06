"""
test_graph.py - Tests for graph construction

Tests the graph_builder module to ensure bipartite graphs are
constructed correctly with candidate, role, and entity nodes.

Research Paper Citation:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Bipartite graph construction methodology
    - Tests verify: Graph structure, entity nodes, edges

For more details, see CITATIONS.md.
"""

import pytest
import networkx as nx
from backend.graph.graph_builder import build_candidate_role_graph


def test_build_graph_with_minimal_data():
    """Test graph construction with minimal candidate and role data."""
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
    
    # Verify graph was created
    assert isinstance(graph, nx.Graph)
    
    # Verify candidate and role nodes exist
    assert graph.has_node('cand1')
    assert graph.has_node('role1')
    assert graph.nodes['cand1']['type'] == 'candidate'
    assert graph.nodes['role1']['type'] == 'role'
    
    # Verify direct edge exists
    assert graph.has_edge('cand1', 'role1')
    
    # Verify self-loops exist
    assert graph.has_edge('cand1', 'cand1')
    assert graph.has_edge('role1', 'role1')


def test_graph_structure_with_entities():
    """Test graph structure with entity nodes (skills, experience, education)."""
    candidate = {
        'id': 'cand1',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML Engineer'],
        'education': ['CS Degree']
    }
    role = {
        'id': 'role1',
        'skills': ['Python', 'PyTorch'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    # Verify entity nodes were created for candidate
    assert graph.has_node('skills_Python_candidate')
    assert graph.has_node('skills_CUDA_candidate')
    assert graph.has_node('experience_ML Engineer_candidate')
    assert graph.has_node('education_CS Degree_candidate')
    
    # Verify entity nodes were created for role
    assert graph.has_node('skills_Python_role')
    assert graph.has_node('skills_PyTorch_role')
    assert graph.has_node('experience_ML_role')
    assert graph.has_node('education_CS_role')
    
    # Verify edges from candidate to entities
    assert graph.has_edge('cand1', 'skills_Python_candidate')
    assert graph.has_edge('cand1', 'skills_CUDA_candidate')
    
    # Verify edges from role to entities
    assert graph.has_edge('role1', 'skills_Python_role')
    assert graph.has_edge('role1', 'skills_PyTorch_role')
    
    # Verify entity node properties
    assert graph.nodes['skills_Python_candidate']['type'] == 'skills'
    assert graph.nodes['skills_Python_candidate']['parent_type'] == 'candidate'


def test_graph_with_different_entity_types():
    """Test graph with different entity types and edge cases."""
    candidate = {
        'id': 'cand2',
        'skills': ['JavaScript'],  # Single skill
        'experience': ['Frontend Dev', 'Backend Dev'],  # Multiple
        'education': ''  # Empty string
    }
    role = {
        'id': 'role2',
        'skills': ['TypeScript'],
        'experience': [],
        'education': ['Bootcamp']
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    # Verify skills node created
    assert graph.has_node('skills_JavaScript_candidate')
    
    # Verify multiple experience nodes
    assert graph.has_node('experience_Frontend Dev_candidate')
    assert graph.has_node('experience_Backend Dev_candidate')
    
    # Verify empty education doesn't create node
    education_nodes = [n for n in graph.nodes() if 'education' in n and 'candidate' in n]
    assert len(education_nodes) == 0
    
    # Verify role education node created
    assert graph.has_node('education_Bootcamp_role')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

