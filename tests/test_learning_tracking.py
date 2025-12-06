"""
test_learning_tracking.py - Tests for learning curve tracking

Tests the learning tracker and data export functionality.
"""

import pytest
import os
from backend.algorithms.learning_tracker import LearningTracker
from backend.algorithms.learning_data_export import (
    format_learning_data,
    export_learning_data_json,
    export_learning_data_csv
)


def test_learning_tracker_basic():
    """Test basic learning tracker functionality."""
    tracker = LearningTracker()
    
    # Record interactions
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    tracker.record_interaction(1, reward=0.0, is_optimal=False)
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    
    # Check metrics
    assert tracker.total_interactions == 3
    assert tracker.get_response_rate() == 2.0 / 3.0
    assert tracker.get_precision() > 0.0
    assert tracker.get_f1_score() >= 0.0
    assert tracker.get_cumulative_regret() >= 0.0


def test_learning_tracker_precision_recall():
    """Test precision/recall computation."""
    tracker = LearningTracker()
    
    # True positives
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    
    # False positives
    tracker.record_interaction(1, reward=1.0, is_optimal=False)
    
    # False negatives
    tracker.record_interaction(0, reward=0.0, is_optimal=True)
    
    precision = tracker.get_precision()
    recall = tracker.get_recall()
    f1 = tracker.get_f1_score()
    
    assert 0.0 <= precision <= 1.0
    assert 0.0 <= recall <= 1.0
    assert 0.0 <= f1 <= 1.0


def test_learning_data_export():
    """Test learning data export."""
    warm_tracker = LearningTracker()
    warm_tracker.record_interaction(0, reward=1.0, is_optimal=True)
    warm_tracker.record_interaction(0, reward=1.0, is_optimal=True)
    
    cold_tracker = LearningTracker()
    cold_tracker.record_interaction(0, reward=1.0, is_optimal=True)
    
    # Test formatting
    data = format_learning_data(warm_tracker, cold_tracker)
    
    assert 'warm_start' in data
    assert 'cold_start' in data
    assert 'timestamp' in data
    assert 'metrics' in data['warm_start']
    assert 'history' in data['warm_start']


def test_export_json():
    """Test JSON export."""
    tracker = LearningTracker()
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    
    test_file = 'test_learning_data.json'
    try:
        export_learning_data_json(tracker, filepath=test_file)
        assert os.path.exists(test_file)
        
        # Verify file is valid JSON
        import json
        with open(test_file, 'r') as f:
            data = json.load(f)
            assert 'warm_start' in data
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_export_csv():
    """Test CSV export."""
    tracker = LearningTracker()
    tracker.record_interaction(0, reward=1.0, is_optimal=True)
    
    test_file = 'test_learning_data.csv'
    try:
        export_learning_data_csv(tracker, filepath=test_file)
        assert os.path.exists(test_file)
        
        # Verify file has content
        with open(test_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1  # Header + at least one data row
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

