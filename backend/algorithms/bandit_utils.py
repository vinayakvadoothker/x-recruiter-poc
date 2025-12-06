"""
bandit_utils.py - Utility functions for bandit algorithms

This module provides helper functions for bandit operations,
including confidence intervals and statistical computations.

These utilities support the Feel-Good Thompson Sampling algorithm [1]
by providing statistical measures for bandit performance evaluation.

Research Paper Citation:
[1] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Supporting statistical computations for FG-TS evaluation

Key functions:
- get_confidence_interval(): Calculate confidence intervals for beta distribution
- beta_mean(): Calculate mean of beta distribution
- compute_f1_score(): Calculate F1 score for precision/recall evaluation

Dependencies:
- numpy: Numerical computations
- scipy.stats: Statistical distributions
"""

import numpy as np
import scipy.stats as stats
from typing import Tuple


def get_confidence_interval(
    alpha: float,
    beta: float,
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """
    Get confidence interval for beta distribution.
    
    Computes confidence intervals for the beta distribution used in
    Thompson Sampling (part of FG-TS algorithm [1]). Uses normal
    approximation for large alpha+beta, which works well for bandit
    applications after a few updates.
    
    This is used to evaluate uncertainty in bandit arm estimates,
    supporting the evaluation of FG-TS performance.
    
    Args:
        alpha: Alpha parameter of beta distribution
        beta: Beta parameter of beta distribution
        confidence: Confidence level (default 0.95 for 95%)
    
    Returns:
        Tuple of (lower_bound, upper_bound, mean)
    """
    mean = alpha / (alpha + beta)
    variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    std = np.sqrt(variance)
    
    # Use normal approximation (works well for large alpha+beta)
    z_score = stats.norm.ppf((1 + confidence) / 2)
    lower = max(0.0, mean - z_score * std)
    upper = min(1.0, mean + z_score * std)
    
    return (lower, upper, mean)


def beta_mean(alpha: float, beta: float) -> float:
    """
    Calculate mean of beta distribution.
    
    Args:
        alpha: Alpha parameter
        beta: Beta parameter
    
    Returns:
        Mean value (alpha / (alpha + beta))
    """
    if alpha + beta == 0:
        return 0.0
    return alpha / (alpha + beta)


def compute_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score (harmonic mean of precision and recall).
    
    Args:
        precision: Precision value (0-1)
        recall: Recall value (0-1)
    
    Returns:
        F1 score (0-1)
    """
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

