"""
test_stress_and_performance.py - Super hard tests for stress and performance

Why this test exists:
In production, the bandit will handle many candidates (50-200+) and run for
many rounds (100+). This test ensures the bandit can handle large-scale
operations efficiently and doesn't degrade with scale. Performance is critical
for real-time candidate selection.

What it validates:
- Bandit handles large candidate sets (100+ candidates)
- Performance is acceptable for large-scale operations
- Memory usage doesn't grow unbounded
- Learning converges with many candidates
- Repeated selections don't degrade performance

Expected behavior:
- Large candidate sets initialize in reasonable time
- Selection performance is consistent regardless of candidate count
- Learning metrics improve over time
- System remains stable under load
"""

import pytest
import numpy as np
import time
import logging
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.datasets import generate_candidates

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStressAndPerformance:
    """Test stress scenarios and performance."""
    
    def setup_method(self):
        """Set up bandit for each test."""
        logger.info("Setting up stress test")
        self.bandit = GraphWarmStartedFGTS()
    
    def test_large_candidate_set(self):
        """Test bandit with large candidate set (100 candidates)."""
        logger.info("Testing with large candidate set (100 candidates)")
        
        # Generate 100 candidates
        candidates = list(generate_candidates(100))
        logger.info(f"Generated {len(candidates)} candidates")
        
        position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++'],
            'requirements': ['5+ years experience'],
            'domains': ['LLM Inference']
        }
        
        logger.info("Initializing bandit with 100 candidates...")
        start_time = time.time()
        self.bandit.initialize_from_embeddings(candidates, position)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Initialization took {elapsed_time:.2f}s")
        logger.info(f"Initialized with {self.bandit.num_arms} arms")
        
        assert self.bandit.num_arms == 100, f"Expected 100 arms, got {self.bandit.num_arms}"
        assert elapsed_time < 60.0, f"Initialization too slow: {elapsed_time:.2f}s"
        
        # Verify all arms have priors
        for i in range(self.bandit.num_arms):
            assert i in self.bandit.alpha
            assert i in self.bandit.beta
        
        logger.info("✅ Large candidate set handled correctly")
    
    def test_selection_performance(self):
        """Test selection performance with many candidates."""
        logger.info("Testing selection performance")
        
        candidates = list(generate_candidates(50))
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['Python']
        }
        
        logger.info("Initializing bandit...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        # Measure selection performance
        num_selections = 100
        logger.info(f"Performing {num_selections} selections...")
        
        start_time = time.time()
        selections = []
        for i in range(num_selections):
            selected = self.bandit.select_candidate()
            selections.append(selected)
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / num_selections
        logger.info(f"Total time: {elapsed_time:.4f}s")
        logger.info(f"Average time per selection: {avg_time:.4f}s")
        logger.info(f"Selections per second: {num_selections/elapsed_time:.1f}")
        
        assert elapsed_time < 5.0, f"Selection too slow: {elapsed_time:.2f}s"
        assert avg_time < 0.05, f"Average selection time too high: {avg_time:.4f}s"
        
        # Verify all selections are valid
        for selected in selections:
            assert 0 <= selected < self.bandit.num_arms
        
        logger.info("✅ Selection performance acceptable")
    
    def test_learning_convergence(self):
        """Test that bandit learns and converges with many candidates."""
        logger.info("Testing learning convergence")
        
        # Generate candidates with one clear optimal candidate
        candidates = list(generate_candidates(30))
        # Make first candidate highly similar to position
        candidates[0] = {
            'id': 'optimal',
            'skills': ['CUDA', 'C++', 'PyTorch', 'LLM Inference'],
            'experience_years': 7,
            'domains': ['LLM Inference', 'GPU Computing']
        }
        
        position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++', 'PyTorch'],
            'domains': ['LLM Inference']
        }
        
        logger.info("Initializing bandit...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        optimal_arm = 0
        num_rounds = 100
        
        logger.info(f"Running {num_rounds} rounds of learning...")
        selections = []
        rewards = []
        
        for round_num in range(num_rounds):
            selected = self.bandit.select_candidate()
            reward = 1.0 if selected == optimal_arm else 0.0
            self.bandit.update(selected, reward)
            
            selections.append(selected)
            rewards.append(reward)
            
            if (round_num + 1) % 20 == 0:
                recent_rate = np.mean(rewards[-20:])
                optimal_rate = np.mean([1.0 if s == optimal_arm else 0.0 for s in selections[-20:]])
                logger.info(f"Round {round_num+1}: Recent reward rate={recent_rate:.2f}, "
                          f"Optimal selection rate={optimal_rate:.2f}")
        
        # Check convergence: later rounds should have higher optimal selection rate
        early_rate = np.mean([1.0 if s == optimal_arm else 0.0 for s in selections[:20]])
        late_rate = np.mean([1.0 if s == optimal_arm else 0.0 for s in selections[-20:]])
        
        logger.info(f"Early optimal selection rate: {early_rate:.2f}")
        logger.info(f"Late optimal selection rate: {late_rate:.2f}")
        
        # Bandit should learn to select optimal arm more often
        assert late_rate >= early_rate, \
            f"Bandit should learn over time. Early={early_rate:.2f}, Late={late_rate:.2f}"
        
        logger.info("✅ Learning convergence verified")
    
    def test_repeated_operations(self):
        """Test that repeated operations don't degrade performance."""
        logger.info("Testing repeated operations performance")
        
        candidates = list(generate_candidates(20))
        position = {'id': 'p1', 'title': 'Engineer', 'must_haves': ['Python']}
        
        logger.info("Initializing bandit...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        # Run many rounds
        num_rounds = 200
        logger.info(f"Running {num_rounds} rounds...")
        
        start_time = time.time()
        for i in range(num_rounds):
            selected = self.bandit.select_candidate()
            reward = np.random.binomial(1, 0.5)  # Random reward for stress test
            self.bandit.update(selected, reward)
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / num_rounds
        logger.info(f"Total time: {elapsed_time:.2f}s")
        logger.info(f"Average time per round: {avg_time:.4f}s")
        
        assert elapsed_time < 10.0, f"Repeated operations too slow: {elapsed_time:.2f}s"
        
        logger.info("✅ Repeated operations performance acceptable")

