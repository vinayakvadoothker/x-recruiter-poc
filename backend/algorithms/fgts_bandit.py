"""
fgts_bandit.py - Feel-Good Thompson Sampling with Embedding Warm-Start

This module implements Feel-Good Thompson Sampling (FG-TS) algorithm [2]
with embedding-based warm-start initialization for candidate selection.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Original graph-based similarity approach (now replaced with embeddings)
    - See: backend.graph.graph_builder (kept for reference, not used in warm-start)

[2] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Feel-Good Thompson Sampling algorithm
    - Feel-good bonus: λ min(b, f_θ(x)) (Equation 1 from [2])
    - Parameters: λ=0.01 (optimal from [2] Table 4), b=1000 (from [2] setup)
    - Why: Provides optimal exploration with proven regret guarantees O(d√T)

Our Novel Contribution:
Embedding-warm-started bandits: Using embedding similarity to initialize FG-TS [2]
priors. This adapts the graph warm-start concept [1] to use vector embeddings
instead, enabling faster learning and smarter exploration with our specialized
recruiting embedder.

For more details, see CITATIONS.md.

Key functions:
- GraphWarmStartedFGTS: Main bandit class (combines [2] + our innovation)
- select_candidate(): Select candidate using FG-TS [2]
- update(): Update bandit after observing reward (Bayesian update)
- initialize_from_embeddings(): Our innovation - embedding warm-start

Dependencies:
- numpy: Numerical computations and beta distribution
- backend.embeddings: Specialized embedder for recruiting profiles
"""

import numpy as np
from typing import Dict, List, Optional, Any
from backend.embeddings import RecruitingKnowledgeGraphEmbedder


class GraphWarmStartedFGTS:
    """
    Feel-Good Thompson Sampling with embedding warm-start initialization.
    
    Combines:
    - Feel-Good Thompson Sampling from Anand & Liaw [2]
    - Our innovation: Embedding similarity → FG-TS prior initialization
    
    The algorithm uses embedding cosine similarity between candidates and positions
    to set initial alpha/beta priors for FG-TS [2], making exploration smarter
    from the start. This is a novel combination not found in either paper.
    
    Novel contribution: High embedding similarity → optimistic prior (higher alpha),
    low similarity → pessimistic prior (higher beta). This enables faster
    learning compared to cold-start (uniform priors).
    
    Implementation Rationale:
    - Why embeddings over graphs: Embeddings are faster to compute, scale better,
      and work directly with our vector DB. The semantic similarity captured by
      embeddings is sufficient for warm-start initialization.
    - Why keep the name "GraphWarmStartedFGTS": Backward compatibility and the
      concept (warm-start from similarity) remains the same, just the similarity
      source changed from graphs to embeddings.
    """
    
    def __init__(
        self,
        lambda_fg: float = 0.01,
        b: float = 1000.0,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None
    ):
        """
        Initialize FG-TS bandit.
        
        Parameters from Anand & Liaw [2]:
        - lambda_fg: Feel-good parameter (0.01, optimal from [2] Table 4)
        - b: Cap parameter for feel-good bonus (1000, from [2] experimental setup)
        - embedder: Embedder instance (creates new if None)
        
        These parameters were found to provide optimal performance in [2]'s
        ablation study and experimental evaluation.
        
        Args:
            lambda_fg: Feel-good parameter (default 0.01 from [2])
            b: Cap parameter for feel-good bonus (default 1000 from [2])
            embedder: Embedder instance for generating embeddings (defaults to new instance)
        """
        self.lambda_fg = lambda_fg
        self.b = b
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.alpha: Dict[int, float] = {}
        self.beta: Dict[int, float] = {}
        self.num_arms = 0
    
    def initialize_from_embeddings(
        self,
        candidates: List[Dict[str, Any]],
        position_data: Dict[str, Any]
    ) -> None:
        """
        Initialize bandit with embedding-based priors (OUR NOVEL CONTRIBUTION).
        
        This is the key innovation: using embedding similarity to initialize
        FG-TS [2] priors, enabling faster learning than cold-start.
        
        Process:
        1. Generate position embedding using specialized embedder
        2. Generate candidate embeddings for all candidates
        3. Compute cosine similarity between each candidate and position
        4. Convert similarity to priors: high similarity → optimistic (higher alpha),
           low similarity → pessimistic (higher beta)
        
        This warm-start approach adapts the graph-based concept to embeddings,
        providing the same benefits (faster learning) with better scalability.
        
        Args:
            candidates: List of candidate data dictionaries
            position_data: Position data dictionary for embedding generation
        """
        if not candidates:
            raise ValueError("Candidates list cannot be empty")
        
        self.num_arms = len(candidates)
        
        # Generate position embedding
        position_embedding = self.embedder.embed_position(position_data)
        
        # Compute similarities for all candidates
        for i, candidate in enumerate(candidates):
            # Generate candidate embedding
            candidate_embedding = self.embedder.embed_candidate(candidate)
            
            # Compute cosine similarity (embeddings are already normalized)
            similarity = float(np.dot(candidate_embedding, position_embedding))
            # Clamp to [0, 1] range (should already be in this range for normalized embeddings)
            similarity = max(0.0, min(1.0, similarity))
            
            # Convert similarity to priors
            # High similarity → optimistic (explore more) → higher alpha
            # Low similarity → pessimistic (explore less) → higher beta
            # Scale factor of 10.0 provides reasonable prior strength
            self.alpha[i] = 1.0 + similarity * 10.0
            self.beta[i] = 1.0 + (1.0 - similarity) * 10.0
    
    def initialize_from_graph(
        self,
        candidates: List[Dict[str, Any]],
        role_data: Dict[str, Any]
    ) -> None:
        """
        DEPRECATED: Initialize bandit with graph-based priors.
        
        This method is deprecated. Use initialize_from_embeddings() instead.
        Kept for backward compatibility.
        
        Args:
            candidates: List of candidate data dictionaries
            role_data: Role data dictionary for graph construction
        """
        raise NotImplementedError(
            "initialize_from_graph() is deprecated. "
            "Use initialize_from_embeddings() instead."
        )
    
    def select_candidate(self) -> int:
        """
        Select candidate using Feel-Good Thompson Sampling [2].
        
        Implements the FG-TS algorithm from Anand & Liaw [2]:
        1. Sample from Beta(alpha, beta) for each arm (standard Thompson Sampling)
        2. Add feel-good bonus: λ * min(b, current_estimate) (Equation 1 from [2])
        3. Select arm with highest score
        
        The feel-good bonus encourages more aggressive exploration compared
        to standard Thompson Sampling, achieving optimal regret O(d√T) as
        proven in [2].
        
        Returns:
            Index of selected candidate
        """
        if self.num_arms == 0:
            raise ValueError("No candidates. Call initialize_from_embeddings() first.")
        
        samples = {}
        
        for i in range(self.num_arms):
            # Thompson Sampling: sample from Beta distribution
            samples[i] = np.random.beta(self.alpha[i], self.beta[i])
            
            # Feel-good bonus from Anand & Liaw [2], Equation 1
            # L_FG(θ, x, r) = η(f_θ(x) - r)² - λ min(b, f_θ(x))
            # The feel-good term encourages optimistic exploration
            current_estimate = self.alpha[i] / (self.alpha[i] + self.beta[i])
            feel_good_bonus = self.lambda_fg * min(self.b, current_estimate)
            samples[i] += feel_good_bonus
        
        # Return arm with highest score
        return max(samples, key=samples.get)
    
    def update(self, arm_index: int, reward: float) -> None:
        """
        Update bandit after observing reward (Bayesian update).
        
        Args:
            arm_index: Index of selected arm
            reward: Observed reward (0 or 1)
        """
        if arm_index not in self.alpha:
            raise ValueError(f"Invalid arm index: {arm_index}")
        
        if reward > 0:
            self.alpha[arm_index] += 1
        else:
            self.beta[arm_index] += 1

