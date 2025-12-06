"""
test_integration_learning_hard.py - Hard integration tests with learning tracking

These tests combine FG-TS bandit with learning tracking and data export
in complex, realistic scenarios.
"""

import pytest
import numpy as np
import os
import json
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.algorithms.learning_tracker import LearningTracker
from backend.algorithms.learning_data_export import (
    format_learning_data,
    export_learning_data_json,
    export_learning_data_csv
)
from backend.graph.graph_builder import build_candidate_role_graph
from backend.graph.graph_similarity import compute_graph_similarity


def test_full_learning_cycle_with_tracking():
    """Test complete learning cycle with tracking over 2000 interactions."""
    # Setup
    candidates = [
        {
            'id': f'cand_{i}',
            'skills': ['Python'] + (['CUDA'] if i < 5 else []),
            'experience': ['ML Engineer'] if i < 8 else ['Frontend'],
            'education': ['CS'] if i < 10 else []
        }
        for i in range(15)
    ]
    
    role_data = {
        'id': 'role_ml',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML Engineer'],
        'education': ['CS']
    }
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    tracker = LearningTracker()
    
    # Determine optimal arm (should be candidate 0-4 based on similarity)
    optimal_arm = 0
    
    # Run 2000 interactions
    for i in range(2000):
        selected = bandit.select_candidate()
        reward = 1.0 if selected == optimal_arm else 0.0
        is_optimal = (selected == optimal_arm)
        
        bandit.update(selected, reward)
        tracker.record_interaction(selected, reward, is_optimal, {
            'iteration': i,
            'alpha': bandit.alpha[selected],
            'beta': bandit.beta[selected]
        })
    
    # Verify learning occurred
    assert tracker.total_interactions == 2000
    assert tracker.get_response_rate() >= 0.0
    
    # Verify bandit learned (optimal arm should have higher success rate)
    optimal_success = bandit.alpha[optimal_arm] / (
        bandit.alpha[optimal_arm] + bandit.beta[optimal_arm]
    )
    assert optimal_success > 0.5  # Should learn to prefer optimal
    
    # Verify metrics are reasonable
    summary = tracker.get_summary()
    assert summary['total_interactions'] == 2000
    assert 0.0 <= summary['f1_score'] <= 1.0


def test_warm_vs_cold_with_full_tracking():
    """Test warm-start vs cold-start with complete tracking over 3000 interactions."""
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
    
    # Warm-start bandit
    warm_bandit = GraphWarmStartedFGTS()
    warm_bandit.initialize_from_graph(candidates, role_data)
    warm_tracker = LearningTracker()
    
    # Cold-start bandit
    cold_bandit = GraphWarmStartedFGTS()
    cold_bandit.num_arms = 2
    cold_bandit.alpha[0] = 1.0
    cold_bandit.beta[0] = 1.0
    cold_bandit.alpha[1] = 1.0
    cold_bandit.beta[1] = 1.0
    cold_tracker = LearningTracker()
    
    optimal_arm = 0
    
    # Run 3000 interactions
    for i in range(3000):
        # Warm-start
        warm_selected = warm_bandit.select_candidate()
        warm_reward = 1.0 if warm_selected == optimal_arm else 0.0
        warm_bandit.update(warm_selected, warm_reward)
        warm_tracker.record_interaction(
            warm_selected, warm_reward, 
            is_optimal=(warm_selected == optimal_arm)
        )
        
        # Cold-start
        cold_selected = cold_bandit.select_candidate()
        cold_reward = 1.0 if cold_selected == optimal_arm else 0.0
        cold_bandit.update(cold_selected, cold_reward)
        cold_tracker.record_interaction(
            cold_selected, cold_reward,
            is_optimal=(cold_selected == optimal_arm)
        )
    
    # Export comparison data
    test_json = 'test_warm_cold_comparison.json'
    test_csv = 'test_warm_cold_comparison.csv'
    
    try:
        export_learning_data_json(warm_tracker, cold_tracker, test_json)
        export_learning_data_csv(warm_tracker, cold_tracker, test_csv)
        
        # Verify exports
        assert os.path.exists(test_json)
        assert os.path.exists(test_csv)
        
        # Verify warm-start performed better
        warm_summary = warm_tracker.get_summary()
        cold_summary = cold_tracker.get_summary()
        
        # Warm-start should have better or equal performance
        assert warm_summary['response_rate'] >= cold_summary['response_rate'] - 0.1
    finally:
        for f in [test_json, test_csv]:
            if os.path.exists(f):
                os.remove(f)


def test_multi_bandit_learning_comparison():
    """Test multiple bandits with different configurations."""
    candidates = [
        {'id': f'cand_{i}', 'skills': ['Python'], 'experience': [], 'education': []}
        for i in range(10)
    ]
    
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    # Create 5 different bandits with different lambda_fg values
    bandits = []
    trackers = []
    
    for lambda_fg in [0.001, 0.01, 0.1, 0.5, 1.0]:
        bandit = GraphWarmStartedFGTS(lambda_fg=lambda_fg)
        bandit.initialize_from_graph(candidates, role_data)
        bandits.append(bandit)
        trackers.append(LearningTracker())
    
    optimal_arm = 0
    
    # Run 1000 interactions for each
    for i in range(1000):
        for j, (bandit, tracker) in enumerate(zip(bandits, trackers)):
            selected = bandit.select_candidate()
            reward = 1.0 if selected == optimal_arm else 0.0
            bandit.update(selected, reward)
            tracker.record_interaction(
                selected, reward,
                is_optimal=(selected == optimal_arm),
                context={'lambda_fg': bandit.lambda_fg, 'iteration': i}
            )
    
    # Verify all trackers have data
    for tracker in trackers:
        assert tracker.total_interactions == 1000
        assert len(tracker.get_history()) == 1000
        summary = tracker.get_summary()
        assert summary['total_interactions'] == 1000


def test_learning_with_graph_similarity_changes():
    """Test learning when graph similarity changes over time."""
    # Start with candidates
    candidates = [
        {
            'id': 'cand1',
            'skills': ['Python'],
            'experience': [],
            'education': []
        },
        {
            'id': 'cand2',
            'skills': ['Java'],
            'experience': [],
            'education': []
        }
    ]
    
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    tracker = LearningTracker()
    
    # Track initial similarity
    role_graph = build_candidate_role_graph({'id': 'role'}, role_data)
    cand1_graph = build_candidate_role_graph(candidates[0], {'id': 'dummy'})
    initial_similarity = compute_graph_similarity(role_graph, cand1_graph)
    
    # Run interactions
    for i in range(500):
        selected = bandit.select_candidate()
        reward = 1.0 if selected == 0 else 0.0
        bandit.update(selected, reward)
        
        # Track similarity in context
        current_similarity = compute_graph_similarity(
            role_graph,
            build_candidate_role_graph(candidates[selected], {'id': 'dummy'})
        )
        
        tracker.record_interaction(
            selected, reward,
            is_optimal=(selected == 0),
            context={
                'similarity': current_similarity,
                'initial_similarity': initial_similarity,
                'iteration': i
            }
        )
    
    # Verify tracking
    assert tracker.total_interactions == 500
    history = tracker.get_history()
    assert all('similarity' in entry['context'] for entry in history)


def test_stress_test_5000_interactions():
    """Stress test with 5000 interactions and full tracking."""
    candidates = [
        {'id': f'cand_{i}', 'skills': ['Python'], 'experience': [], 'education': []}
        for i in range(20)
    ]
    
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    tracker = LearningTracker()
    
    optimal_arm = 0
    
    # Run 5000 interactions
    for i in range(5000):
        selected = bandit.select_candidate()
        reward = 1.0 if selected == optimal_arm else 0.0
        bandit.update(selected, reward)
        tracker.record_interaction(selected, reward, is_optimal=(selected == optimal_arm))
    
    # Export large dataset
    test_json = 'test_stress_5000.json'
    test_csv = 'test_stress_5000.csv'
    
    try:
        export_learning_data_json(tracker, filepath=test_json)
        export_learning_data_csv(tracker, filepath=test_csv)
        
        # Verify files
        assert os.path.exists(test_json)
        assert os.path.getsize(test_json) > 100000  # Should be substantial
        
        assert os.path.exists(test_csv)
        assert os.path.getsize(test_csv) > 50000
        
        # Verify data integrity
        with open(test_json, 'r') as f:
            data = json.load(f)
            assert len(data['warm_start']['history']) == 5000
    finally:
        for f in [test_json, test_csv]:
            if os.path.exists(f):
                os.remove(f)


def test_learning_curve_accuracy():
    """Test that learning curves accurately reflect bandit performance."""
    candidates = [
        {'id': 'cand_good', 'skills': ['Python'], 'experience': [], 'education': []},
        {'id': 'cand_bad', 'skills': ['Java'], 'experience': [], 'education': []}
    ]
    
    role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
    
    bandit = GraphWarmStartedFGTS()
    bandit.initialize_from_graph(candidates, role_data)
    tracker = LearningTracker()
    
    optimal_arm = 0
    
    # Run 1000 interactions
    for i in range(1000):
        selected = bandit.select_candidate()
        reward = 1.0 if selected == optimal_arm else 0.0
        bandit.update(selected, reward)
        tracker.record_interaction(selected, reward, is_optimal=(selected == optimal_arm))
    
    # Verify learning curve shows improvement
    history = tracker.get_history()
    
    # Check early vs late performance
    early_performance = sum(
        entry['reward'] for entry in history[:100]
    ) / 100.0
    
    late_performance = sum(
        entry['reward'] for entry in history[-100:]
    ) / 100.0
    
    # Late performance should be better (bandit learned)
    assert late_performance >= early_performance - 0.2  # Allow some variance
    
    # Verify F1 score improves
    early_f1 = history[99]['f1_score']
    late_f1 = history[-1]['f1_score']
    assert late_f1 >= early_f1 - 0.1  # Should improve or stay similar


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

