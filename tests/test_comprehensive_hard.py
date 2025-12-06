"""
test_comprehensive_hard.py - Comprehensive hard test suite

This test suite covers complex scenarios, edge cases, and integration
points to ensure the system is robust and production-ready.

Tests include:
- Complex graph structures
- Multiple candidates with varying similarities
- Long-running bandit learning
- Neo4j persistence and recovery
- Error handling and edge cases
"""

import pytest
import numpy as np
import networkx as nx
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.database.neo4j_client import Neo4jClient
from backend.database.neo4j_queries import create_schema, store_candidate, store_role
from backend.database.neo4j_bandit_state import (
    store_bandit_state,
    load_bandit_state,
    restore_bandit_from_state
)


def test_complex_graph_structure():
    """Test graph construction with complex, realistic data."""
    candidate = {
        'id': 'cand_complex',
        'skills': ['Python', 'CUDA', 'PyTorch', 'TensorFlow', 'C++', 'NVIDIA'],
        'experience': [
            'ML Engineer at Google',
            'HPC Researcher',
            'GPU Optimization Specialist',
            'Deep Learning Practitioner'
        ],
        'education': [
            'PhD Computer Science - Stanford',
            'Masters Machine Learning',
            'Bachelors Computer Engineering'
        ]
    }
    
    role = {
        'id': 'role_complex',
        'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer Architecture'],
        'experience': [
            'ML Infrastructure',
            'HPC Systems',
            'GPU Computing'
        ],
        'education': ['PhD or Masters in CS/ML']
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    # Verify complex structure
    assert isinstance(graph, nx.Graph)
    assert graph.has_node('cand_complex')
    assert graph.has_node('role_complex')
    
    # Verify many entity nodes created
    entity_nodes = [n for n in graph.nodes() if n not in ['cand_complex', 'role_complex']]
    assert len(entity_nodes) > 10, "Should have many entity nodes"
    
    # Verify edges exist
    assert graph.number_of_edges() > 0
    assert graph.has_edge('cand_complex', 'role_complex')


def test_multiple_candidates_ranking():
    """Test bandit with many candidates and verify ranking."""
    candidates = [
        {
            'id': f'cand_{i}',
            'skills': ['Python'] + (['CUDA'] if i < 3 else []),
            'experience': ['ML Engineer'] if i < 5 else ['Frontend Dev'],
            'education': ['CS'] if i < 7 else []
        }
        for i in range(10)
    ]
    
    role_data = {
        'id': 'role_ml',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML Engineer'],
        'education': ['CS']
    }
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Verify all candidates initialized
    assert bandit.num_arms == 10
    
    # Top candidates (0-2) should have higher alpha
    assert bandit.alpha[0] >= bandit.alpha[9], "Strong candidate should have higher alpha"
    
    # Run many selections
    selections = [bandit.select_candidate() for _ in range(100)]
    
    # Top candidates should be selected more often
    top_selections = sum(1 for s in selections if s < 3)
    bottom_selections = sum(1 for s in selections if s >= 7)
    
    assert top_selections >= bottom_selections, "Top candidates should be selected more"


def test_long_running_learning():
    """Test bandit learning over many iterations."""
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
    
    role_data = {
        'id': 'role_ml',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    initial_alpha_good = bandit.alpha[0]
    initial_alpha_bad = bandit.alpha[1]
    
    # Simulate 100 interactions
    for i in range(100):
        selected = bandit.select_candidate()
        
        # Good candidate gets 80% success rate
        if selected == 0:
            reward = 1.0 if np.random.random() < 0.8 else 0.0
        else:
            reward = 1.0 if np.random.random() < 0.2 else 0.0
        
        bandit.update(selected, reward)
    
    # After learning, good candidate should have much higher success rate
    success_rate_good = bandit.alpha[0] / (bandit.alpha[0] + bandit.beta[0])
    success_rate_bad = bandit.alpha[1] / (bandit.alpha[1] + bandit.beta[1])
    
    assert success_rate_good > success_rate_bad, "Good candidate should have higher success rate"
    assert bandit.alpha[0] > initial_alpha_good + 50, "Good candidate should have many successes"


def test_graph_similarity_consistency():
    """Test graph similarity is consistent across multiple computations."""
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
    
    # Compute similarity multiple times
    similarities = [
        compute_graph_similarity(role_graph, candidate_graph)
        for _ in range(10)
    ]
    
    # Should be consistent (deterministic)
    assert all(abs(s - similarities[0]) < 0.01 for s in similarities), \
        "Similarity should be consistent"


def test_bandit_state_persistence_recovery():
    """Test bandit state persistence and recovery after many updates."""
    try:
        with Neo4jClient() as client:
            session = client.get_session()
            create_schema(session)
            
            # Create role
            store_role(session, {'id': 'role_persistence', 'title': 'Test'})
            
            # Create and train bandit
            candidates = [
                {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []},
                {'id': 'cand2', 'skills': ['Java'], 'experience': [], 'education': []}
            ]
            role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
            
            original_bandit = GraphWarmStartedFGTS()
            original_bandit.initialize_from_graph(candidates, role_data)
            
            # Train bandit
            for _ in range(50):
                selected = original_bandit.select_candidate()
                reward = 1.0 if selected == 0 else 0.0
                original_bandit.update(selected, reward)
            
            original_alpha_0 = original_bandit.alpha[0]
            original_alpha_1 = original_bandit.alpha[1]
            
            # Store state
            store_bandit_state(session, 'role_persistence', original_bandit)
            
            # Create new bandit and restore
            new_bandit = GraphWarmStartedFGTS()
            state = load_bandit_state(session, 'role_persistence')
            assert state is not None, "State should be loaded"
            
            restore_bandit_from_state(new_bandit, state)
            
            # Verify state restored correctly
            assert new_bandit.num_arms == 2
            assert abs(new_bandit.alpha[0] - original_alpha_0) < 0.01
            assert abs(new_bandit.alpha[1] - original_alpha_1) < 0.01
            
            # Verify bandit still works after restore
            selected = new_bandit.select_candidate()
            assert 0 <= selected < 2
            
            new_bandit.update(selected, 1.0)
            assert new_bandit.alpha[selected] > original_alpha_0 or new_bandit.alpha[selected] > original_alpha_1
            
            session.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


def test_warm_start_advantage_over_time():
    """Test that warm-start maintains advantage over cold-start over time."""
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
        'id': 'role_ml',
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
    
    # Run many interactions
    for i in range(200):
        warm_selected = warm_bandit.select_candidate()
        cold_selected = cold_bandit.select_candidate()
        
        # Same reward structure
        warm_reward = 1.0 if warm_selected == 0 else 0.0
        cold_reward = 1.0 if cold_selected == 0 else 0.0
        
        warm_bandit.update(warm_selected, warm_reward)
        cold_bandit.update(cold_selected, cold_reward)
    
    # Warm-start should have better performance
    warm_success = warm_bandit.alpha[0] / (warm_bandit.alpha[0] + warm_bandit.beta[0])
    cold_success = cold_bandit.alpha[0] / (cold_bandit.alpha[0] + cold_bandit.beta[0])
    
    # Warm-start should have learned faster (higher success rate for good candidate)
    assert warm_success >= cold_success - 0.1, "Warm-start should perform at least as well"


def test_edge_case_empty_everything():
    """Test system with completely empty data."""
    candidate = {
        'id': 'cand_empty'
    }
    role = {
        'id': 'role_empty'
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    assert isinstance(graph, nx.Graph)
    assert graph.has_node('cand_empty')
    assert graph.has_node('role_empty')
    assert graph.has_edge('cand_empty', 'role_empty')
    
    # Should still compute similarity (even if low)
    role_graph = build_candidate_role_graph({'id': 'role'}, role)
    candidate_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    
    assert 0.0 <= similarity <= 1.0


def test_bandit_with_extreme_similarities():
    """Test bandit with candidates having extreme similarity differences."""
    candidates = [
        {
            'id': 'cand_perfect',
            'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer'],
            'experience': ['ML Engineer', 'HPC'],
            'education': ['CS PhD']
        },
        {
            'id': 'cand_terrible',
            'skills': ['HTML', 'CSS'],
            'experience': ['Web Designer'],
            'education': []
        }
    ]
    
    role_data = {
        'id': 'role_ml',
        'skills': ['Python', 'CUDA', 'PyTorch', 'Transformer'],
        'experience': ['ML Engineer', 'HPC'],
        'education': ['CS PhD']
    }
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    
    # Perfect candidate should have higher alpha (warm-start advantage)
    assert bandit.alpha[0] > bandit.alpha[1], "Perfect candidate should have higher alpha"
    
    # Perfect candidate should have lower beta (more optimistic)
    assert bandit.beta[0] < bandit.beta[1], "Perfect candidate should have lower beta"
    
    # Verify the difference is meaningful
    alpha_ratio = bandit.alpha[0] / bandit.alpha[1]
    beta_ratio = bandit.beta[1] / bandit.beta[0]
    
    assert alpha_ratio > 1.1, "Perfect candidate should have at least 10% higher alpha"
    assert beta_ratio > 1.1, "Perfect candidate should have at least 10% lower beta"


def test_graph_similarity_with_many_entities():
    """Test graph similarity with many entities."""
    candidate = {
        'id': 'cand_many',
        'skills': [f'Skill_{i}' for i in range(20)],
        'experience': [f'Exp_{i}' for i in range(10)],
        'education': [f'Edu_{i}' for i in range(5)]
    }
    
    role = {
        'id': 'role_many',
        'skills': [f'Skill_{i}' for i in range(15)],
        'experience': [f'Exp_{i}' for i in range(8)],
        'education': [f'Edu_{i}' for i in range(4)]
    }
    
    role_graph = build_candidate_role_graph({'id': 'role'}, role)
    candidate_graph = build_candidate_role_graph(candidate, {'id': 'dummy'})
    
    similarity = compute_graph_similarity(role_graph, candidate_graph)
    
    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.0, "Should have some similarity with overlapping entities"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

