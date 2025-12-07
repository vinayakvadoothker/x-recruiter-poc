"""
test_basic_functionality.py - Easy tests for basic bandit functionality

Why this test exists:
This test verifies that the bandit can be initialized with embeddings and
performs basic operations (select, update). This is the foundation - without
working initialization and selection, the entire bandit system fails.

What it validates:
- initialize_from_embeddings() works with valid candidates and position
- select_candidate() returns valid arm indices
- update() correctly updates alpha/beta priors
- Bandit maintains state correctly across operations

Expected behavior:
- Initialization sets alpha/beta priors for all candidates
- Selection returns valid indices (0 to num_arms-1)
- Updates modify priors correctly (alpha increases on reward=1, beta on reward=0)
- All operations complete without errors
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


class TestBasicFunctionality:
    """Test basic bandit functionality with embeddings."""
    
    def setup_method(self):
        """Set up bandit and test data."""
        logger.info("Setting up bandit test")
        self.bandit = GraphWarmStartedFGTS()
        self.embedder = RecruitingKnowledgeGraphEmbedder()
        
        # Create test candidates
        self.candidates = [
            {
                'id': 'candidate_1',
                'skills': ['Python', 'CUDA', 'PyTorch'],
                'experience_years': 5,
                'domains': ['LLM Inference']
            },
            {
                'id': 'candidate_2',
                'skills': ['Java', 'Spring Boot'],
                'experience_years': 3,
                'domains': ['Web Development']
            },
            {
                'id': 'candidate_3',
                'skills': ['CUDA', 'C++', 'GPU Optimization'],
                'experience_years': 7,
                'domains': ['LLM Inference', 'GPU Computing']
            }
        ]
        
        # Create test position
        self.position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++', 'PyTorch'],
            'requirements': ['5+ years experience in LLM inference'],
            'experience_level': 'Senior',
            'domains': ['LLM Inference']
        }
        logger.info(f"Created {len(self.candidates)} test candidates and 1 position")
    
    def test_initialize_from_embeddings(self):
        """Test that initialize_from_embeddings() works correctly."""
        logger.info("Testing initialize_from_embeddings()")
        
        logger.info("Initializing bandit with embeddings...")
        self.bandit.initialize_from_embeddings(self.candidates, self.position)
        
        logger.info(f"Bandit initialized with {self.bandit.num_arms} arms")
        assert self.bandit.num_arms == len(self.candidates), \
            f"Expected {len(self.candidates)} arms, got {self.bandit.num_arms}"
        
        # Verify all candidates have priors set
        for i in range(self.bandit.num_arms):
            logger.debug(f"Arm {i}: alpha={self.bandit.alpha[i]:.2f}, beta={self.bandit.beta[i]:.2f}")
            assert i in self.bandit.alpha, f"Arm {i} missing alpha prior"
            assert i in self.bandit.beta, f"Arm {i} missing beta prior"
            assert self.bandit.alpha[i] > 0, f"Alpha for arm {i} should be > 0"
            assert self.bandit.beta[i] > 0, f"Beta for arm {i} should be > 0"
        
        logger.info("✅ All priors set correctly")
    
    def test_select_candidate(self):
        """Test that select_candidate() returns valid indices."""
        logger.info("Testing select_candidate()")
        
        self.bandit.initialize_from_embeddings(self.candidates, self.position)
        
        # Select multiple times to verify randomness
        selections = []
        for i in range(10):
            selected = self.bandit.select_candidate()
            logger.debug(f"Selection {i+1}: arm {selected}")
            selections.append(selected)
            assert 0 <= selected < self.bandit.num_arms, \
                f"Invalid arm index: {selected} (should be 0-{self.bandit.num_arms-1})"
        
        logger.info(f"Selected arms: {selections}")
        logger.info(f"Unique selections: {len(set(selections))}")
        assert len(set(selections)) > 1, "Should select different arms (bandit explores)"
        
        logger.info("✅ Selection works correctly")
    
    def test_update_positive_reward(self):
        """Test that update() correctly handles positive rewards."""
        logger.info("Testing update() with positive reward")
        
        self.bandit.initialize_from_embeddings(self.candidates, self.position)
        arm_index = 0
        initial_alpha = self.bandit.alpha[arm_index]
        initial_beta = self.bandit.beta[arm_index]
        
        logger.info(f"Arm {arm_index} before update: alpha={initial_alpha:.2f}, beta={initial_beta:.2f}")
        
        logger.info("Updating with reward=1.0...")
        self.bandit.update(arm_index, reward=1.0)
        
        new_alpha = self.bandit.alpha[arm_index]
        new_beta = self.bandit.beta[arm_index]
        
        logger.info(f"Arm {arm_index} after update: alpha={new_alpha:.2f}, beta={new_beta:.2f}")
        
        assert new_alpha == initial_alpha + 1.0, \
            f"Alpha should increase by 1.0, got {new_alpha} vs {initial_alpha}"
        assert new_beta == initial_beta, \
            f"Beta should not change, got {new_beta} vs {initial_beta}"
        
        logger.info("✅ Positive reward update works correctly")
    
    def test_update_negative_reward(self):
        """Test that update() correctly handles negative rewards."""
        logger.info("Testing update() with negative reward")
        
        self.bandit.initialize_from_embeddings(self.candidates, self.position)
        arm_index = 1
        initial_alpha = self.bandit.alpha[arm_index]
        initial_beta = self.bandit.beta[arm_index]
        
        logger.info(f"Arm {arm_index} before update: alpha={initial_alpha:.2f}, beta={initial_beta:.2f}")
        
        logger.info("Updating with reward=0.0...")
        self.bandit.update(arm_index, reward=0.0)
        
        new_alpha = self.bandit.alpha[arm_index]
        new_beta = self.bandit.beta[arm_index]
        
        logger.info(f"Arm {arm_index} after update: alpha={new_alpha:.2f}, beta={new_beta:.2f}")
        
        assert new_alpha == initial_alpha, \
            f"Alpha should not change, got {new_alpha} vs {initial_alpha}"
        assert new_beta == initial_beta + 1.0, \
            f"Beta should increase by 1.0, got {new_beta} vs {initial_beta}"
        
        logger.info("✅ Negative reward update works correctly")
    
    def test_end_to_end_flow(self):
        """Test complete flow: initialize → select → update."""
        logger.info("Testing end-to-end flow")
        
        logger.info("Step 1: Initialize bandit")
        self.bandit.initialize_from_embeddings(self.candidates, self.position)
        logger.info(f"Initialized with {self.bandit.num_arms} arms")
        
        logger.info("Step 2: Select candidate")
        selected = self.bandit.select_candidate()
        logger.info(f"Selected arm: {selected}")
        
        logger.info("Step 3: Update with reward")
        reward = 1.0
        initial_alpha = self.bandit.alpha[selected]
        self.bandit.update(selected, reward)
        new_alpha = self.bandit.alpha[selected]
        logger.info(f"Updated arm {selected}: alpha {initial_alpha:.2f} → {new_alpha:.2f}")
        
        assert new_alpha == initial_alpha + 1.0, "Alpha should increase after positive reward"
        
        logger.info("✅ End-to-end flow works correctly")

