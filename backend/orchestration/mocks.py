"""
Mock implementations for Vin's graph and bandit code.

These mocks match Vin's exact interface and can be easily swapped when his code is ready.
All functions are clearly marked with comments indicating where to switch.
"""

import logging
import random
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# ============================================================================
# MOCK IMPLEMENTATION - REPLACE WHEN VIN'S CODE IS READY
# ============================================================================
# TODO: Replace this mock with:
#   from backend.graph.graph_builder import build_candidate_role_graph
# Expected interface:
#   def build_candidate_role_graph(candidate_data: dict, role_data: dict) -> Graph
#   Returns: Graph object (NetworkX or custom Graph class)
# ============================================================================
def mock_build_candidate_role_graph(
    candidate_data: Dict[str, Any],
    role_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock implementation of graph builder.
    
    Returns a simple graph structure dictionary.
    Will be replaced with Vin's actual graph_builder.build_candidate_role_graph().
    
    Args:
        candidate_data: Candidate profile data dictionary
        role_data: Role requirements data dictionary
    
    Returns:
        Dictionary representing a graph structure (mock)
    """
    logger.warning("Using MOCK build_candidate_role_graph - replace with Vin's implementation")
    
    # Return a simple mock graph structure
    return {
        'nodes': {
            'candidate': candidate_data.get('github_handle', 'unknown'),
            'role': role_data.get('title', 'unknown'),
            'entities': candidate_data.get('skills', [])[:5]
        },
        'edges': [
            {'from': 'candidate', 'to': entity, 'weight': random.random()}
            for entity in candidate_data.get('skills', [])[:5]
        ],
        'type': 'bipartite',
        'mock': True
    }


# ============================================================================
# MOCK IMPLEMENTATION - REPLACE WHEN VIN'S CODE IS READY
# ============================================================================
# TODO: Replace this mock with:
#   from backend.graph.graph_similarity import compute_graph_similarity
# Expected interface:
#   def compute_graph_similarity(role_graph: Graph, candidate_graph: Graph) -> float
#   Returns: Similarity score between 0.0 and 1.0
# ============================================================================
def mock_compute_graph_similarity(
    role_graph: Dict[str, Any],
    candidate_graph: Dict[str, Any]
) -> float:
    """
    Mock implementation of graph similarity computation.
    
    Returns a random similarity score between 0 and 1.
    Will be replaced with Vin's actual graph_similarity.compute_graph_similarity().
    
    Args:
        role_graph: Role graph structure
        candidate_graph: Candidate graph structure
    
    Returns:
        Similarity score between 0.0 and 1.0 (mock - random value)
    """
    logger.warning("Using MOCK compute_graph_similarity - replace with Vin's implementation")
    
    # Return a random similarity score (mock)
    # In real implementation, this would use kNN-based similarity
    return random.uniform(0.3, 0.95)


# ============================================================================
# MOCK IMPLEMENTATION - REPLACE WHEN VIN'S CODE IS READY
# ============================================================================
# TODO: Replace this mock class with:
#   from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
# Expected interface:
#   class GraphWarmStartedFGTS:
#       def __init__(self, lambda_fg=0.01, b=1000)
#       def initialize_from_graph(self, candidates: List[Dict], role_graph: Graph) -> None
#       def select_candidate(self) -> int
#       def update(self, arm_index: int, reward: float) -> None
# ============================================================================
class MockGraphWarmStartedFGTS:
    """
    Mock implementation of Feel-Good Thompson Sampling bandit.
    
    Provides basic functionality for testing pipeline.
    Will be replaced with Vin's actual fgts_bandit.GraphWarmStartedFGTS.
    """
    
    def __init__(self, lambda_fg: float = 0.01, b: int = 1000):
        """
        Initialize mock bandit.
        
        Args:
            lambda_fg: Feel-good parameter (not used in mock)
            b: Cap parameter (not used in mock)
        """
        logger.warning("Using MOCK GraphWarmStartedFGTS - replace with Vin's implementation")
        self.lambda_fg = lambda_fg
        self.b = b
        self.alpha: Dict[int, float] = {}
        self.beta: Dict[int, float] = {}
        self.candidates: List[Dict] = []
        self.role_graph: Dict[str, Any] = {}
        self.initialized = False
    
    def initialize_from_graph(
        self,
        candidates: List[Dict[str, Any]],
        role_graph: Dict[str, Any]
    ) -> None:
        """
        Initialize bandit with graph-based priors (mock).
        
        Args:
            candidates: List of candidate dictionaries
            role_graph: Role graph structure
        """
        self.candidates = candidates
        self.role_graph = role_graph
        
        # Initialize alpha/beta for each candidate (mock)
        for i in range(len(candidates)):
            # Mock: use random similarity to set priors
            similarity = random.uniform(0.4, 0.9)
            self.alpha[i] = 1.0 + similarity * 10.0
            self.beta[i] = 1.0 + (1.0 - similarity) * 10.0
        
        self.initialized = True
        logger.info(f"Mock bandit initialized with {len(candidates)} candidates")
    
    def select_candidate(self) -> int:
        """
        Select candidate using Thompson Sampling (mock).
        
        Returns:
            Index of selected candidate
        """
        if not self.initialized:
            raise ValueError("Bandit not initialized. Call initialize_from_graph() first.")
        
        if not self.candidates:
            raise ValueError("No candidates available")
        
        # Mock: select based on alpha/beta ratios (simplified Thompson Sampling)
        scores = []
        for i in range(len(self.candidates)):
            # Mock Thompson Sampling: sample from beta distribution
            import numpy as np
            try:
                score = np.random.beta(self.alpha.get(i, 1.0), self.beta.get(i, 1.0))
            except ImportError:
                # Fallback if numpy not available
                score = self.alpha.get(i, 1.0) / (self.alpha.get(i, 1.0) + self.beta.get(i, 1.0))
            scores.append((i, score))
        
        # Select candidate with highest score
        selected = max(scores, key=lambda x: x[1])[0]
        logger.debug(f"Mock bandit selected candidate {selected}")
        return selected
    
    def update(self, arm_index: int, reward: float) -> None:
        """
        Update bandit after observing reward (mock).
        
        Args:
            arm_index: Index of the candidate (arm) that was selected
            reward: Reward value (0.0 to 1.0)
        """
        if arm_index not in self.alpha:
            self.alpha[arm_index] = 1.0
            self.beta[arm_index] = 1.0
        
        # Update alpha/beta based on reward (Bayesian update)
        if reward > 0.5:
            self.alpha[arm_index] += 1.0
        else:
            self.beta[arm_index] += 1.0
        
        logger.debug(f"Mock bandit updated: arm {arm_index}, reward {reward}, alpha={self.alpha[arm_index]}, beta={self.beta[arm_index]}")

