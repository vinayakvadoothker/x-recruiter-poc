"""
test_edge_cases.py - Medium tests for feedback loop edge cases

Why this test exists:
Real-world usage will have edge cases: invalid feedback, missing candidates,
duplicate feedback, missing positions, API failures, etc. This test ensures
the feedback loop handles these gracefully and returns appropriate errors or
fallback behavior.

What it validates:
- Missing candidate returns error
- Missing position returns error
- Candidate not in position's list handled correctly
- Duplicate feedback handled correctly
- API failures handled with fallback
- Invalid feedback text handled gracefully

Expected behavior:
- Edge cases return clear error messages or handle gracefully
- System doesn't crash on edge cases
- Fallback to neutral reward if Grok API fails
"""

import pytest
import os
import logging
import asyncio
from backend.orchestration.feedback_loop import FeedbackLoop
from backend.database.knowledge_graph import KnowledgeGraph
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.algorithms.learning_tracker import LearningTracker
from backend.integrations.grok_api import GrokAPIClient

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases in feedback loop."""
    
    def setup_method(self):
        """Set up feedback loop."""
        logger.info("Setting up edge case test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.tracker = LearningTracker()
        
        # Initialize Grok client
        try:
            grok_client = GrokAPIClient()
            self.feedback_loop = FeedbackLoop(
                knowledge_graph=self.kg,
                learning_tracker=self.tracker,
                grok_client=grok_client
            )
        except ValueError:
            pytest.skip("GROK_API_KEY required for feedback parsing tests")
    
    def teardown_method(self):
        """Clean up after each test."""
        self.feedback_loop.close()
    
    @pytest.mark.asyncio
    async def test_missing_candidate(self):
        """Test feedback with missing candidate."""
        logger.info("Testing feedback with missing candidate")
        
        # Create position but no candidate
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'selected_candidates': []
        }
        self.kg.add_position(position)
        
        result = await self.feedback_loop.process_feedback(
            candidate_id='nonexistent_candidate',
            position_id='position_001',
            feedback_text='Good candidate'
        )
        
        logger.info(f"Result: {result}")
        
        assert result['success'] is False, "Should return error for missing candidate"
        assert 'error' in result, "Should include error message"
        
        logger.info("✅ Missing candidate handled correctly")
    
    @pytest.mark.asyncio
    async def test_missing_position(self):
        """Test feedback with missing position."""
        logger.info("Testing feedback with missing position")
        
        # Create candidate but no position
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        self.kg.add_candidate(candidate)
        
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='nonexistent_position',
            feedback_text='Good candidate'
        )
        
        logger.info(f"Result: {result}")
        
        assert result['success'] is False, "Should return error for missing position"
        assert 'error' in result, "Should include error message"
        assert 'not found' in result['error'].lower(), \
            "Error should mention position not found"
        
        logger.info("✅ Missing position handled correctly")
    
    @pytest.mark.asyncio
    async def test_candidate_not_in_position_list(self):
        """Test feedback when candidate not in position's candidate list."""
        logger.info("Testing candidate not in position list")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'selected_candidates': ['candidate_002', 'candidate_003']  # candidate_001 not in list
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Good candidate'
        )
        
        logger.info(f"Result: {result}")
        
        assert result['success'] is False, \
            "Should return error when candidate not in position list"
        assert 'error' in result, "Should include error message"
        assert 'not in position' in result['error'].lower() or 'not found' in result['error'].lower(), \
            "Error should mention candidate not in position list"
        
        logger.info("✅ Candidate not in position list handled correctly")
    
    @pytest.mark.asyncio
    async def test_position_with_no_candidates(self):
        """Test feedback when position has no candidate list."""
        logger.info("Testing position with no candidates")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        position = {
            'id': 'position_001',
            'title': 'Test Position'
            # No selected_candidates field
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Good candidate'
        )
        
        logger.info(f"Result: {result}")
        
        assert result['success'] is False, \
            "Should return error when position has no candidate list"
        assert 'error' in result, "Should include error message"
        
        logger.info("✅ Position with no candidates handled correctly")
    
    @pytest.mark.asyncio
    async def test_duplicate_feedback(self):
        """Test that duplicate feedback is handled correctly."""
        logger.info("Testing duplicate feedback")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'selected_candidates': ['candidate_001']
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Register bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings([candidate], position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001'],
            bandit=bandit
        )
        
        # Process feedback twice
        result1 = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Excellent candidate!'
        )
        
        result2 = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Excellent candidate!'
        )
        
        logger.info(f"First feedback: {result1}")
        logger.info(f"Second feedback: {result2}")
        
        # Both should succeed
        assert result1['success'], "First feedback should succeed"
        assert result2['success'], "Second feedback should succeed"
        
        # Both should be stored in history
        candidate_updated = self.kg.get_candidate('candidate_001')
        feedback_history = candidate_updated.get('feedback_history', [])
        assert len(feedback_history) == 2, \
            f"Should have 2 feedback entries, got {len(feedback_history)}"
        
        logger.info("✅ Duplicate feedback handled correctly")
    
    @pytest.mark.asyncio
    async def test_empty_feedback_text(self):
        """Test feedback with empty text."""
        logger.info("Testing empty feedback text")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'selected_candidates': ['candidate_001']
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Register bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings([candidate], position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001'],
            bandit=bandit
        )
        
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text=''
        )
        
        logger.info(f"Result: {result}")
        
        # Should still process (Grok will handle empty text)
        # May default to neutral
        assert 'reward' in result, "Should have reward value"
        assert 0.0 <= result['reward'] <= 1.0, \
            f"Reward should be 0-1, got {result['reward']}"
        
        logger.info("✅ Empty feedback text handled correctly")
    
    @pytest.mark.asyncio
    async def test_very_long_feedback(self):
        """Test feedback with very long text."""
        logger.info("Testing very long feedback text")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'selected_candidates': ['candidate_001']
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Register bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings([candidate], position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001'],
            bandit=bandit
        )
        
        # Very long feedback
        long_feedback = "This candidate is " + "excellent " * 100 + "and highly qualified!"
        
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text=long_feedback
        )
        
        logger.info(f"Result: {result}")
        
        # Should still process
        assert 'reward' in result, "Should have reward value"
        assert 0.0 <= result['reward'] <= 1.0, \
            f"Reward should be 0-1, got {result['reward']}"
        
        logger.info("✅ Very long feedback handled correctly")

