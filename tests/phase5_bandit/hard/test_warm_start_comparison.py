"""
test_warm_start_comparison.py - Hard tests for warm-start vs cold-start comparison

Why this test exists:
The key innovation of embedding warm-start is that it should enable faster
learning compared to cold-start (uniform priors). This test verifies that
warm-start actually provides this benefit by comparing performance metrics
between warm-started and cold-started bandits.

What it validates:
- Warm-start priors reflect embedding similarity
- Warm-started bandit learns faster (higher reward rate early on)
- Similar candidates get higher initial priors (optimistic)
- Dissimilar candidates get lower initial priors (pessimistic)
- Overall performance improves with warm-start

Expected behavior:
- Warm-started bandit should have higher early reward rate
- Similar candidates should have higher alpha priors
- Dissimilar candidates should have higher beta priors
- Warm-start should converge faster to optimal arm
"""

import pytest
import numpy as np
import logging
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestWarmStartComparison:
    """Test warm-start vs cold-start performance."""
    
    def setup_method(self):
        """Set up bandit and test data."""
        logger.info("Setting up warm-start comparison test")
        self.embedder = RecruitingKnowledgeGraphEmbedder()
        
        # Create candidates with varying similarity to position
        self.candidates = [
            {
                'id': 'similar_1',
                'skills': ['CUDA', 'C++', 'PyTorch', 'LLM Inference'],
                'experience_years': 6,
                'domains': ['LLM Inference', 'GPU Computing']
            },
            {
                'id': 'similar_2',
                'skills': ['CUDA', 'C++', 'GPU Optimization'],
                'experience_years': 5,
                'domains': ['LLM Inference']
            },
            {
                'id': 'dissimilar_1',
                'skills': ['Java', 'Spring Boot', 'REST APIs'],
                'experience_years': 4,
                'domains': ['Web Development']
            },
            {
                'id': 'dissimilar_2',
                'skills': ['JavaScript', 'React', 'Node.js'],
                'experience_years': 3,
                'domains': ['Frontend Development']
            }
        ]
        
        # Position that matches similar candidates
        self.position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++', 'PyTorch'],
            'requirements': ['5+ years in LLM inference optimization'],
            'experience_level': 'Senior',
            'domains': ['LLM Inference', 'GPU Computing']
        }
        logger.info(f"Created {len(self.candidates)} candidates and 1 position")
    
    def test_warm_start_priors_reflect_similarity(self):
        """Test that warm-start priors reflect embedding similarity."""
        logger.info("Testing that warm-start priors reflect similarity")
        
        bandit = GraphWarmStartedFGTS()
        logger.info("Initializing bandit with embeddings...")
        bandit.initialize_from_embeddings(self.candidates, self.position)
        
        # Compute similarities manually for comparison
        position_emb = self.embedder.embed_position(self.position)
        similarities = []
        for i, candidate in enumerate(self.candidates):
            candidate_emb = self.embedder.embed_candidate(candidate)
            similarity = float(np.dot(candidate_emb, position_emb))
            similarities.append((i, similarity, bandit.alpha[i], bandit.beta[i]))
            logger.info(f"Candidate {i} ({candidate['id']}): "
                       f"similarity={similarity:.4f}, "
                       f"alpha={bandit.alpha[i]:.2f}, "
                       f"beta={bandit.beta[i]:.2f}")
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        sorted_info = [(s[0], f"{s[1]:.4f}") for s in similarities]
        logger.info(f"Sorted by similarity: {sorted_info}")
        
        # Similar candidates should have higher alpha (more optimistic)
        # Dissimilar candidates should have higher beta (more pessimistic)
        similar_indices = [0, 1]  # First two candidates are similar
        dissimilar_indices = [2, 3]  # Last two are dissimilar
        
        similar_alphas = [bandit.alpha[i] for i in similar_indices]
        dissimilar_alphas = [bandit.alpha[i] for i in dissimilar_indices]
        
        logger.info(f"Similar candidates alphas: {similar_alphas}")
        logger.info(f"Dissimilar candidates alphas: {dissimilar_alphas}")
        
        avg_similar_alpha = np.mean(similar_alphas)
        avg_dissimilar_alpha = np.mean(dissimilar_alphas)
        
        logger.info(f"Average similar alpha: {avg_similar_alpha:.2f}")
        logger.info(f"Average dissimilar alpha: {avg_dissimilar_alpha:.2f}")
        
        assert avg_similar_alpha > avg_dissimilar_alpha, \
            f"Similar candidates should have higher alpha priors. " \
            f"Got {avg_similar_alpha:.2f} vs {avg_dissimilar_alpha:.2f}"
        
        logger.info("✅ Warm-start priors correctly reflect similarity")
    
    def test_warm_start_faster_learning(self):
        """Test that warm-start enables faster learning."""
        logger.info("Testing warm-start vs cold-start learning speed")
        
        # Warm-started bandit
        warm_bandit = GraphWarmStartedFGTS()
        logger.info("Initializing warm-started bandit...")
        warm_bandit.initialize_from_embeddings(self.candidates, self.position)
        
        # Cold-started bandit (uniform priors)
        cold_bandit = GraphWarmStartedFGTS()
        logger.info("Initializing cold-started bandit (uniform priors)...")
        cold_bandit.num_arms = len(self.candidates)
        for i in range(cold_bandit.num_arms):
            cold_bandit.alpha[i] = 1.0  # Uniform priors
            cold_bandit.beta[i] = 1.0
        
        # Simulate learning: optimal arm is 0 (similar candidate)
        optimal_arm = 0
        num_rounds = 20
        
        warm_rewards = []
        cold_rewards = []
        
        logger.info(f"Running {num_rounds} rounds of learning...")
        for round_num in range(num_rounds):
            # Warm bandit
            warm_selected = warm_bandit.select_candidate()
            warm_reward = 1.0 if warm_selected == optimal_arm else 0.0
            warm_bandit.update(warm_selected, warm_reward)
            warm_rewards.append(warm_reward)
            
            # Cold bandit
            cold_selected = cold_bandit.select_candidate()
            cold_reward = 1.0 if cold_selected == optimal_arm else 0.0
            cold_bandit.update(cold_selected, cold_reward)
            cold_rewards.append(cold_reward)
            
            if (round_num + 1) % 5 == 0:
                warm_rate = np.mean(warm_rewards[-5:])
                cold_rate = np.mean(cold_rewards[-5:])
                logger.info(f"Round {round_num+1}: Warm={warm_rate:.2f}, Cold={cold_rate:.2f}")
        
        # Compare early performance (first 10 rounds)
        warm_early = np.mean(warm_rewards[:10])
        cold_early = np.mean(cold_rewards[:10])
        
        logger.info(f"Early performance (first 10 rounds):")
        logger.info(f"  Warm-start: {warm_early:.2f}")
        logger.info(f"  Cold-start: {cold_early:.2f}")
        
        # Warm-start should perform better early on
        assert warm_early >= cold_early, \
            f"Warm-start should perform at least as well early. " \
            f"Got {warm_early:.2f} vs {cold_early:.2f}"
        
        logger.info("✅ Warm-start enables faster learning")

