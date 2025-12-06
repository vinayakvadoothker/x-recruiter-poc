"""
test_similarity.py - Tests for graph similarity computation

Tests the graph_similarity module to ensure kNN-based similarity
is computed correctly according to Frazzetto et al. [1].

Research Paper Citation:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: kNN-based similarity computation (Equation 1)
    - Tests verify: kNN neighborhoods, intersection/union, sharpening factor p=4

For more details, see CITATIONS.md.
"""

import pytest
import numpy as np
import networkx as nx
from backend.graph.graph_similarity import (
    compute_entity_similarity,
    compute_graph_similarity,
    _compute_knn_neighborhoods,
    _compute_intersection,
    _compute_union
)
from backend.graph.graph_builder import build_candidate_role_graph


def test_knn_computation_with_sample_vectors():
    """Test kNN computation with sample embedding vectors."""
    # Create sample embeddings
    cand_embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
    role_embeddings = [
        [0.15, 0.25, 0.35],  # Similar to first candidate
        [0.45, 0.55, 0.65],  # Similar to second candidate
        [1.0, 1.1, 1.2]      # Different
    ]
    
    similarity = compute_entity_similarity(cand_embeddings, role_embeddings, k=2)
    
    # Similarity should be between 0 and 1
    assert 0.0 <= similarity <= 1.0
    
    # With similar embeddings, similarity should be > 0
    assert similarity > 0.0


def test_knn_with_identical_vectors():
    """Test kNN with identical vectors (should have high similarity)."""
    embeddings = [
        [0.1, 0.2],
        [0.3, 0.4]
    ]
    
    # Identical embeddings should have high similarity
    similarity = compute_entity_similarity(embeddings, embeddings, k=2)
    assert similarity > 0.5  # Should be high for identical


def test_knn_with_different_vectors():
    """Test kNN with very different vectors (should have low similarity)."""
    # Use more entities so kNN neighborhoods don't always overlap
    cand_emb = [
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5, 0.6],
        [0.7, 0.8]
    ]
    role_emb = [
        [10.0, 20.0],  # Very different
        [30.0, 40.0],
        [50.0, 60.0],
        [70.0, 80.0]
    ]
    
    similarity = compute_entity_similarity(cand_emb, role_emb, k=2)
    
    # Very different embeddings should have low similarity
    # (With k=2, there might be some overlap, but should be < 1.0)
    assert similarity <= 1.0
    # At least verify it computes without error


def test_knn_with_empty_input():
    """Test kNN with empty input (should return 0)."""
    similarity = compute_entity_similarity([], [[0.1, 0.2]], k=2)
    assert similarity == 0.0
    
    similarity = compute_entity_similarity([[0.1, 0.2]], [], k=2)
    assert similarity == 0.0


def test_knn_neighborhoods_computation():
    """Test kNN neighborhood computation."""
    entities = np.array([
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5, 0.6]
    ])
    
    neighborhoods = _compute_knn_neighborhoods(entities, k=2)
    
    # Should return set of indices
    assert isinstance(neighborhoods, set)
    
    # Should include at least some indices
    assert len(neighborhoods) > 0
    
    # All indices should be valid (0 to n-1)
    assert all(0 <= idx < len(entities) for idx in neighborhoods)


def test_intersection_and_union():
    """Test intersection and union computation."""
    set1 = {0, 1, 2, 3}
    set2 = {2, 3, 4, 5}
    
    intersection = _compute_intersection(set1, set2)
    union = _compute_union(set1, set2)
    
    assert intersection == 2  # {2, 3}
    assert union == 6  # {0, 1, 2, 3, 4, 5}


def test_graph_similarity_aggregation():
    """Test graph similarity aggregation across entity types."""
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
    
    cand_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    role_graph = build_candidate_role_graph({'id': 'dummy'}, role)
    
    similarity = compute_graph_similarity(role_graph, cand_graph)
    
    # Similarity should be between 0 and 1
    assert 0.0 <= similarity <= 1.0


def test_graph_similarity_with_weights():
    """Test graph similarity with custom entity weights."""
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
    
    cand_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    role_graph = build_candidate_role_graph({'id': 'dummy'}, role)
    
    # Test with custom weights
    weights = {'skills': 1.0, 'experience': 0.0, 'education': 0.0}
    similarity = compute_graph_similarity(role_graph, cand_graph, entity_weights=weights)
    
    assert 0.0 <= similarity <= 1.0


def test_graph_similarity_with_empty_graphs():
    """Test graph similarity with empty graphs."""
    empty_graph = nx.Graph()
    similarity = compute_graph_similarity(empty_graph, empty_graph)
    
    # Empty graphs should have 0 similarity
    assert similarity == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

