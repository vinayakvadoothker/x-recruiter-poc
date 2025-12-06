"""
test_learning_tracking_hard.py - Hard stress tests for learning tracking

These tests push the learning tracking system to its limits with:
- Thousands of interactions
- Complex learning scenarios
- Edge cases and boundary conditions
- Data integrity verification
"""

import pytest
import json
import os
from backend.algorithms.learning_tracker import LearningTracker
from backend.algorithms.learning_data_export import (
    format_learning_data,
    export_learning_data_json,
    export_learning_data_csv
)


def test_long_running_learning_1000_interactions():
    """Test learning tracker with 1000+ interactions."""
    tracker = LearningTracker()
    
    # Simulate 1000 interactions with varying rewards
    for i in range(1000):
        selected_arm = i % 3  # Cycle through 3 arms
        reward = 1.0 if i % 3 == 0 else (0.5 if i % 3 == 1 else 0.0)
        is_optimal = (i % 3 == 0)
        
        tracker.record_interaction(selected_arm, reward, is_optimal)
    
    # Verify metrics are reasonable
    assert tracker.total_interactions == 1000
    assert tracker.get_response_rate() >= 0.0
    assert tracker.get_response_rate() <= 1.0
    assert tracker.get_precision() >= 0.0
    assert tracker.get_precision() <= 1.0
    assert tracker.get_recall() >= 0.0
    assert tracker.get_recall() <= 1.0
    assert tracker.get_f1_score() >= 0.0
    assert tracker.get_f1_score() <= 1.0
    assert tracker.get_cumulative_regret() >= 0.0
    
    # Verify history is complete
    history = tracker.get_history()
    assert len(history) == 1000
    assert all('timestamp' in entry for entry in history)
    assert all('interaction' in entry for entry in history)


def test_precision_recall_edge_cases():
    """Test precision/recall with extreme edge cases."""
    # Test 1: All false positives
    tracker1 = LearningTracker()
    for _ in range(10):
        tracker1.record_interaction(1, reward=1.0, is_optimal=False)
    
    assert tracker1.get_precision() == 0.0
    assert tracker1.get_recall() == 0.0
    assert tracker1.get_f1_score() == 0.0
    
    # Test 2: All true positives
    tracker2 = LearningTracker()
    for _ in range(10):
        tracker2.record_interaction(0, reward=1.0, is_optimal=True)
    
    assert tracker2.get_precision() == 1.0
    assert tracker2.get_recall() == 1.0
    assert tracker2.get_f1_score() == 1.0
    
    # Test 3: All false negatives
    tracker3 = LearningTracker()
    for _ in range(10):
        tracker3.record_interaction(0, reward=0.0, is_optimal=True)
    
    assert tracker3.get_precision() == 0.0
    assert tracker3.get_recall() == 0.0
    
    # Test 4: Mixed scenario
    tracker4 = LearningTracker()
    # 5 true positives
    for _ in range(5):
        tracker4.record_interaction(0, reward=1.0, is_optimal=True)
    # 3 false positives
    for _ in range(3):
        tracker4.record_interaction(1, reward=1.0, is_optimal=False)
    # 2 false negatives
    for _ in range(2):
        tracker4.record_interaction(0, reward=0.0, is_optimal=True)
    
    precision = tracker4.get_precision()
    recall = tracker4.get_recall()
    f1 = tracker4.get_f1_score()
    
    assert 0.0 < precision < 1.0
    assert 0.0 < recall < 1.0
    assert 0.0 < f1 < 1.0
    assert abs(f1 - (2 * precision * recall / (precision + recall))) < 0.01


def test_cumulative_regret_complex():
    """Test cumulative regret with complex scenarios."""
    tracker = LearningTracker()
    
    # Simulate learning scenario where optimal arm changes
    optimal_arm = 0
    for i in range(500):
        # Optimal arm changes every 100 interactions
        if i % 100 == 0:
            optimal_arm = (optimal_arm + 1) % 3
        
        selected = i % 3
        reward = 1.0 if selected == optimal_arm else 0.0
        is_optimal = (selected == optimal_arm)
        
        tracker.record_interaction(selected, reward, is_optimal)
    
    # Regret should accumulate
    regret = tracker.get_cumulative_regret()
    assert regret >= 0.0
    
    # Verify regret increases with suboptimal selections
    initial_regret = tracker.get_cumulative_regret()
    tracker.record_interaction(1, reward=0.0, is_optimal=False)
    assert tracker.get_cumulative_regret() >= initial_regret


def test_context_tracking_complex():
    """Test context tracking with complex context data."""
    tracker = LearningTracker()
    
    # Record interactions with complex context
    for i in range(100):
        context = {
            'candidate_id': f'cand_{i % 10}',
            'role_id': 'role_ml',
            'similarity': 0.5 + (i % 10) * 0.05,
            'timestamp': f'2025-12-{i % 30 + 1}',
            'metadata': {
                'source': 'github' if i % 2 == 0 else 'x',
                'score': i * 0.1
            }
        }
        
        tracker.record_interaction(
            selected_arm=i % 3,
            reward=1.0 if i % 3 == 0 else 0.0,
            is_optimal=(i % 3 == 0),
            context=context
        )
    
    history = tracker.get_history()
    assert len(history) == 100
    assert all('context' in entry for entry in history)
    assert all('candidate_id' in entry['context'] for entry in history)


def test_large_data_export_json():
    """Test JSON export with large dataset."""
    tracker = LearningTracker()
    
    # Generate large dataset
    for i in range(5000):
        tracker.record_interaction(
            selected_arm=i % 5,
            reward=1.0 if i % 2 == 0 else 0.0,
            is_optimal=(i % 5 == 0)
        )
    
    test_file = 'test_large_export.json'
    try:
        export_learning_data_json(tracker, filepath=test_file)
        
        assert os.path.exists(test_file)
        assert os.path.getsize(test_file) > 0
        
        # Verify JSON is valid and parseable
        with open(test_file, 'r') as f:
            data = json.load(f)
            assert 'warm_start' in data
            assert 'history' in data['warm_start']
            assert len(data['warm_start']['history']) == 5000
            
            # Verify all entries have required fields
            for entry in data['warm_start']['history']:
                assert 'timestamp' in entry
                assert 'interaction' in entry
                assert 'selected_arm' in entry
                assert 'reward' in entry
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_large_data_export_csv():
    """Test CSV export with large dataset."""
    tracker = LearningTracker()
    
    # Generate large dataset
    for i in range(5000):
        tracker.record_interaction(
            selected_arm=i % 5,
            reward=1.0 if i % 2 == 0 else 0.0,
            is_optimal=(i % 5 == 0)
        )
    
    test_file = 'test_large_export.csv'
    try:
        export_learning_data_csv(tracker, filepath=test_file)
        
        assert os.path.exists(test_file)
        assert os.path.getsize(test_file) > 0
        
        # Verify CSV structure
        with open(test_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 5001  # Header + 5000 data rows
            
            # Verify header
            header = lines[0].strip().split(',')
            assert 'timestamp' in header
            assert 'interaction' in header
            assert 'selected_arm' in header
            assert 'reward' in header
            assert 'bandit_type' in header
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_dual_bandit_comparison():
    """Test comparing warm-start vs cold-start with many interactions."""
    warm_tracker = LearningTracker()
    cold_tracker = LearningTracker()
    
    # Simulate 2000 interactions for both
    for i in range(2000):
        # Warm-start: arm 0 is optimal (better initial priors)
        warm_selected = 0 if i % 3 == 0 else (1 if i % 3 == 1 else 2)
        warm_reward = 1.0 if warm_selected == 0 else 0.0
        warm_tracker.record_interaction(
            warm_selected, warm_reward, is_optimal=(warm_selected == 0)
        )
        
        # Cold-start: same scenario but starts from scratch
        cold_selected = 0 if i % 3 == 0 else (1 if i % 3 == 1 else 2)
        cold_reward = 1.0 if cold_selected == 0 else 0.0
        cold_tracker.record_interaction(
            cold_selected, cold_reward, is_optimal=(cold_selected == 0)
        )
    
    # Format and export comparison
    data = format_learning_data(warm_tracker, cold_tracker)
    
    assert 'warm_start' in data
    assert 'cold_start' in data
    assert len(data['warm_start']['history']) == 2000
    assert len(data['cold_start']['history']) == 2000
    
    # Verify metrics are tracked for both
    warm_summary = warm_tracker.get_summary()
    cold_summary = cold_tracker.get_summary()
    
    assert warm_summary['total_interactions'] == 2000
    assert cold_summary['total_interactions'] == 2000


def test_metric_consistency_over_time():
    """Test that metrics remain consistent as data accumulates."""
    tracker = LearningTracker()
    
    metrics_history = []
    
    # Record interactions and track metrics at intervals
    for i in range(1000):
        tracker.record_interaction(
            selected_arm=i % 3,
            reward=1.0 if i % 3 == 0 else 0.0,
            is_optimal=(i % 3 == 0)
        )
        
        # Check metrics every 100 interactions
        if (i + 1) % 100 == 0:
            metrics = {
                'interaction': i + 1,
                'response_rate': tracker.get_response_rate(),
                'precision': tracker.get_precision(),
                'recall': tracker.get_recall(),
                'f1_score': tracker.get_f1_score(),
                'regret': tracker.get_cumulative_regret()
            }
            metrics_history.append(metrics)
    
    # Verify metrics are consistent (no NaN or infinite values)
    for metrics in metrics_history:
        assert not (metrics['response_rate'] != metrics['response_rate'])  # Not NaN
        assert not (metrics['precision'] != metrics['precision'])
        assert not (metrics['recall'] != metrics['recall'])
        assert not (metrics['f1_score'] != metrics['f1_score'])
        assert 0.0 <= metrics['response_rate'] <= 1.0
        assert 0.0 <= metrics['precision'] <= 1.0
        assert 0.0 <= metrics['recall'] <= 1.0
        assert 0.0 <= metrics['f1_score'] <= 1.0


def test_concurrent_like_scenarios():
    """Test scenarios that simulate concurrent operations."""
    tracker = LearningTracker()
    
    # Simulate rapid-fire interactions (like concurrent requests)
    interactions = []
    for i in range(1000):
        interactions.append({
            'arm': i % 5,
            'reward': 1.0 if i % 5 == 0 else 0.0,
            'optimal': (i % 5 == 0)
        })
    
    # Record all interactions
    for interaction in interactions:
        tracker.record_interaction(
            interaction['arm'],
            interaction['reward'],
            interaction['optimal']
        )
    
    # Verify all interactions recorded
    assert tracker.total_interactions == 1000
    assert len(tracker.get_history()) == 1000
    
    # Verify data integrity
    history = tracker.get_history()
    for i, entry in enumerate(history):
        assert entry['interaction'] == i + 1
        assert entry['selected_arm'] == interactions[i]['arm']
        assert entry['reward'] == interactions[i]['reward']


def test_boundary_conditions():
    """Test boundary conditions and limits."""
    tracker = LearningTracker()
    
    # Test with single interaction
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    assert tracker.total_interactions == 1
    assert tracker.get_response_rate() == 1.0
    
    # Test with zero rewards
    tracker2 = LearningTracker()
    for _ in range(100):
        tracker2.record_interaction(0, reward=0.0, is_optimal=False)
    assert tracker2.get_response_rate() == 0.0
    
    # Test with all rewards
    tracker3 = LearningTracker()
    for _ in range(100):
        tracker3.record_interaction(0, reward=1.0, is_optimal=True)
    assert tracker3.get_response_rate() == 1.0
    assert tracker3.get_precision() == 1.0
    assert tracker3.get_recall() == 1.0
    assert tracker3.get_f1_score() == 1.0


def test_data_export_integrity():
    """Test data export maintains integrity with complex data."""
    warm_tracker = LearningTracker()
    cold_tracker = LearningTracker()
    
    # Generate complex data
    for i in range(500):
        context = {
            'iteration': i,
            'complex_data': {
                'nested': {
                    'value': i * 0.1,
                    'array': [i, i+1, i+2]
                }
            }
        }
        
        warm_tracker.record_interaction(
            i % 3, 1.0 if i % 2 == 0 else 0.0, 
            is_optimal=(i % 3 == 0),
            context=context
        )
        
        cold_tracker.record_interaction(
            i % 3, 1.0 if i % 3 == 0 else 0.0,
            is_optimal=(i % 3 == 0)
        )
    
    # Export and verify
    test_json = 'test_integrity.json'
    test_csv = 'test_integrity.csv'
    
    try:
        export_learning_data_json(warm_tracker, cold_tracker, test_json)
        export_learning_data_csv(warm_tracker, cold_tracker, test_csv)
        
        # Verify JSON integrity
        with open(test_json, 'r') as f:
            data = json.load(f)
            assert len(data['warm_start']['history']) == 500
            assert len(data['cold_start']['history']) == 500
            
            # Verify context preserved
            assert 'context' in data['warm_start']['history'][0]
            assert 'complex_data' in data['warm_start']['history'][0]['context']
        
        # Verify CSV integrity
        with open(test_csv, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1001  # Header + 1000 rows (500 warm + 500 cold)
    finally:
        for f in [test_json, test_csv]:
            if os.path.exists(f):
                os.remove(f)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

