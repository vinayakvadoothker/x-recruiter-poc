"""
learning_data_export.py - Export learning data for dashboard

This module formats and exports learning curve data to JSON and CSV
formats for visualization in dashboards.

The exported data includes metrics for evaluating Feel-Good Thompson
Sampling [1] performance, including warm-start vs cold-start comparisons
(our innovation).

Research Paper Citation:
[1] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Exporting FG-TS performance metrics

Exported metrics include:
- Response rates (to evaluate exploration efficiency)
- Cumulative regret (to verify O(d√T) optimal regret from [1])
- Precision/recall/F1 (for candidate selection quality)
- Warm-start vs cold-start comparison (our contribution)

Key functions:
- export_learning_data_json(): Export to JSON format
- export_learning_data_csv(): Export to CSV format
- format_learning_data(): Format data for export

Dependencies:
- json: JSON serialization
- csv: CSV writing
- typing: Type hints
"""

import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.algorithms.learning_tracker import LearningTracker


def format_learning_data(
    warm_tracker: LearningTracker,
    cold_tracker: Optional[LearningTracker] = None
) -> Dict[str, Any]:
    """
    Format learning data for export.
    
    Args:
        warm_tracker: LearningTracker for warm-start bandit
        cold_tracker: Optional LearningTracker for cold-start bandit
    
    Returns:
        Formatted dictionary with all learning metrics
    """
    data = {
        'timestamp': datetime.now().isoformat(),
        'warm_start': {
            'metrics': warm_tracker.get_summary(),
            'history': warm_tracker.get_history()
        }
    }
    
    if cold_tracker:
        data['cold_start'] = {
            'metrics': cold_tracker.get_summary(),
            'history': cold_tracker.get_history()
        }
    
    return data


def export_learning_data_json(
    warm_tracker: LearningTracker,
    cold_tracker: Optional[LearningTracker] = None,
    filepath: str = 'learning_data.json'
) -> None:
    """
    Export learning data to JSON file.
    
    Args:
        warm_tracker: LearningTracker for warm-start bandit
        cold_tracker: Optional LearningTracker for cold-start bandit
        filepath: Path to output JSON file
    """
    data = format_learning_data(warm_tracker, cold_tracker)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def export_learning_data_csv(
    warm_tracker: LearningTracker,
    cold_tracker: Optional[LearningTracker] = None,
    filepath: str = 'learning_data.csv'
) -> None:
    """
    Export learning data to CSV file.
    
    Args:
        warm_tracker: LearningTracker for warm-start bandit
        cold_tracker: Optional LearningTracker for cold-start bandit
        filepath: Path to output CSV file
    """
    warm_history = warm_tracker.get_history()
    
    if not warm_history:
        return
    
    fieldnames = [
        'timestamp', 'interaction', 'selected_arm', 'reward',
        'is_optimal', 'response_rate', 'precision', 'recall',
        'f1_score', 'cumulative_regret', 'bandit_type'
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write warm-start data
        for entry in warm_history:
            row = {k: v for k, v in entry.items() if k in fieldnames}
            row['bandit_type'] = 'warm_start'
            writer.writerow(row)
        
        # Write cold-start data if available
        if cold_tracker:
            cold_history = cold_tracker.get_history()
            for entry in cold_history:
                row = {k: v for k, v in entry.items() if k in fieldnames}
                row['bandit_type'] = 'cold_start'
                writer.writerow(row)

