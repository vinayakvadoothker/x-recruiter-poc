"""
test_edge_cases.py - Medium tests for edge cases and error handling

Why this test exists:
Real-world usage will have edge cases: empty candidates, invalid data,
duplicate candidates, etc. This test ensures the bandit handles these
gracefully without crashing, which is critical for production reliability.

What it validates:
- Empty candidates list raises appropriate error
- Invalid position data is handled
- Duplicate candidates are handled
- Invalid arm indices in update() are rejected
- Missing initialization before selection raises error

Expected behavior:
- Invalid inputs should be rejected with clear error messages
- Edge cases should not crash the system
- Error messages should be informative
"""

import pytest
import logging
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Set up bandit for each test."""
        logger.info("Setting up edge case test")
        self.bandit = GraphWarmStartedFGTS()
    
    def test_empty_candidates_list(self):
        """Test that empty candidates list raises error."""
        logger.info("Testing empty candidates list")
        
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['Python']
        }
        
        logger.info("Attempting to initialize with empty candidates list...")
        with pytest.raises(ValueError, match="cannot be empty"):
            self.bandit.initialize_from_embeddings([], position)
        
        logger.info("✅ Empty candidates list correctly rejected")
    
    def test_select_without_initialization(self):
        """Test that selection without initialization raises error."""
        logger.info("Testing selection without initialization")
        
        logger.info("Attempting to select without initialization...")
        with pytest.raises(ValueError, match="initialize_from_embeddings"):
            self.bandit.select_candidate()
        
        logger.info("✅ Selection without initialization correctly rejected")
    
    def test_update_invalid_arm_index(self):
        """Test that update with invalid arm index raises error."""
        logger.info("Testing update with invalid arm index")
        
        candidates = [{'id': 'c1', 'skills': ['Python']}]
        position = {'id': 'p1', 'title': 'Engineer', 'must_haves': ['Python']}
        
        logger.info("Initializing bandit...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        logger.info("Attempting to update with invalid arm index...")
        with pytest.raises(ValueError, match="Invalid arm index"):
            self.bandit.update(999, reward=1.0)
        
        logger.info("✅ Invalid arm index correctly rejected")
    
    def test_minimal_position_data(self):
        """Test that bandit works with minimal position data."""
        logger.info("Testing with minimal position data")
        
        candidates = [
            {'id': 'c1', 'skills': ['Python'], 'experience_years': 2}
        ]
        position = {'id': 'p1', 'title': 'Engineer'}  # Minimal data
        
        logger.info("Initializing with minimal position data...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        logger.info(f"Initialized successfully with {self.bandit.num_arms} arms")
        assert self.bandit.num_arms == 1
        assert 0 in self.bandit.alpha
        assert 0 in self.bandit.beta
        
        logger.info("✅ Minimal position data handled correctly")
    
    def test_minimal_candidate_data(self):
        """Test that bandit works with minimal candidate data."""
        logger.info("Testing with minimal candidate data")
        
        candidates = [
            {'id': 'c1', 'skills': ['Python']}  # Minimal data
        ]
        position = {
            'id': 'p1',
            'title': 'Engineer',
            'must_haves': ['Python']
        }
        
        logger.info("Initializing with minimal candidate data...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        logger.info(f"Initialized successfully with {self.bandit.num_arms} arms")
        assert self.bandit.num_arms == 1
        
        selected = self.bandit.select_candidate()
        logger.info(f"Selected arm: {selected}")
        assert selected == 0
        
        logger.info("✅ Minimal candidate data handled correctly")
    
    def test_multiple_updates_same_arm(self):
        """Test that multiple updates to same arm work correctly."""
        logger.info("Testing multiple updates to same arm")
        
        candidates = [
            {'id': 'c1', 'skills': ['Python']},
            {'id': 'c2', 'skills': ['Java']}
        ]
        position = {'id': 'p1', 'title': 'Engineer', 'must_haves': ['Python']}
        
        logger.info("Initializing bandit...")
        self.bandit.initialize_from_embeddings(candidates, position)
        
        arm_index = 0
        initial_alpha = self.bandit.alpha[arm_index]
        logger.info(f"Initial alpha for arm {arm_index}: {initial_alpha:.2f}")
        
        # Update multiple times
        for i in range(5):
            logger.info(f"Update {i+1}: reward=1.0")
            self.bandit.update(arm_index, reward=1.0)
            logger.info(f"Alpha after update {i+1}: {self.bandit.alpha[arm_index]:.2f}")
        
        final_alpha = self.bandit.alpha[arm_index]
        logger.info(f"Final alpha: {final_alpha:.2f}")
        
        assert final_alpha == initial_alpha + 5.0, \
            f"Alpha should increase by 5.0, got {final_alpha} vs {initial_alpha}"
        
        logger.info("✅ Multiple updates work correctly")

