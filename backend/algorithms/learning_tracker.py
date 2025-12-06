"""
learning_tracker.py - Learning curve tracking for FG-TS bandit

This module tracks learning metrics over time for evaluating the
Feel-Good Thompson Sampling algorithm [1] performance, including
response rates, precision/recall, F1 score, and cumulative regret.

Research Paper Citation:
[1] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Tracking performance of FG-TS algorithm
    - Metrics: Response rates, cumulative regret (to evaluate O(d√T) guarantee)

This tracker enables evaluation of:
- FG-TS [1] learning performance over time
- Warm-start vs cold-start comparison (our innovation)
- Cumulative regret to verify optimal regret guarantees from [1]

Key functions:
- LearningTracker: Tracks metrics over time
- get_precision_recall(): Calculate precision and recall
- get_f1_score(): Calculate F1 score
- get_cumulative_regret(): Calculate cumulative regret

Dependencies:
- numpy: Numerical computations
- backend.algorithms.bandit_utils: Utility functions
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.algorithms.bandit_utils import compute_f1_score


class LearningTracker:
    """
    Tracks learning metrics over time for bandit algorithm.
    
    Tracks:
    - Response rates over time
    - Precision/recall over time
    - F1 score over time
    - Cumulative regret
    - Warm-start vs cold-start performance
    """
    
    def __init__(self):
        """Initialize learning tracker."""
        self.history: List[Dict[str, Any]] = []
        self.total_interactions = 0
        self.total_rewards = 0
        self.total_positive_rewards = 0
        self.total_negative_rewards = 0
        
        # For precision/recall tracking
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        
        # For regret tracking
        self.cumulative_regret = 0.0
        self.optimal_reward = 0.0
    
    def record_interaction(
        self,
        selected_arm: int,
        reward: float,
        is_optimal: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an interaction with the bandit.
        
        Args:
            selected_arm: Index of selected arm
            reward: Observed reward (0 or 1)
            is_optimal: Whether this was the optimal arm
            context: Optional context information
        """
        self.total_interactions += 1
        self.total_rewards += reward
        
        if reward > 0:
            self.total_positive_rewards += 1
            if is_optimal:
                self.true_positives += 1
            else:
                self.false_positives += 1
        else:
            self.total_negative_rewards += 1
            if is_optimal:
                self.false_negatives += 1
        
        # Update regret
        if is_optimal and reward == 0:
            self.cumulative_regret += 1.0
        elif not is_optimal and reward == 0:
            self.cumulative_regret += 0.0  # No regret if we didn't expect reward
        elif not is_optimal and reward > 0:
            self.cumulative_regret += 0.0  # Bonus, not regret
        
        # Record in history
        entry = {
            'timestamp': datetime.now().isoformat(),
            'interaction': self.total_interactions,
            'selected_arm': selected_arm,
            'reward': reward,
            'is_optimal': is_optimal,
            'response_rate': self.get_response_rate(),
            'precision': self.get_precision(),
            'recall': self.get_recall(),
            'f1_score': self.get_f1_score(),
            'cumulative_regret': self.cumulative_regret,
            'context': context or {}
        }
        self.history.append(entry)
    
    def get_response_rate(self) -> float:
        """Get current response rate (positive rewards / total interactions)."""
        if self.total_interactions == 0:
            return 0.0
        return self.total_positive_rewards / self.total_interactions
    
    def get_precision(self) -> float:
        """Get precision (true positives / (true positives + false positives))."""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    def get_recall(self) -> float:
        """Get recall (true positives / (true positives + false negatives))."""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    def get_f1_score(self) -> float:
        """Get F1 score (harmonic mean of precision and recall)."""
        precision = self.get_precision()
        recall = self.get_recall()
        return compute_f1_score(precision, recall)
    
    def get_cumulative_regret(self) -> float:
        """Get cumulative regret."""
        return self.cumulative_regret
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full learning history."""
        return self.history.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of learning metrics."""
        return {
            'total_interactions': self.total_interactions,
            'total_rewards': self.total_rewards,
            'response_rate': self.get_response_rate(),
            'precision': self.get_precision(),
            'recall': self.get_recall(),
            'f1_score': self.get_f1_score(),
            'cumulative_regret': self.cumulative_regret,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives
        }

