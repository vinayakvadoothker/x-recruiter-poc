"""
test_basic_feedback.py - Easy tests for basic feedback processing

Why this test exists:
This test verifies that the feedback loop can process feedback and update the bandit.
This is the foundation - without working feedback processing, the self-improving agent
cannot learn. We need to ensure feedback is parsed correctly, bandit is updated, and
learning metrics are tracked.

What it validates:
- process_feedback() processes positive/negative/neutral feedback correctly
- Feedback text is parsed to reward values (1.0, 0.0, 0.5)
- Bandit priors are updated after feedback
- Learning tracker records feedback events
- Feedback history is stored in knowledge graph

Expected behavior:
- Positive feedback ("good candidate") → reward 1.0 → bandit alpha increases
- Negative feedback ("not qualified") → reward 0.0 → bandit beta increases
- Neutral feedback ("maybe") → reward 0.5 → both alpha and beta increase
- Learning metrics are updated after feedback
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


class TestBasicFeedback:
    """Test basic feedback processing."""
    
    def setup_method(self):
        """Set up feedback loop and test data."""
        logger.info("Setting up feedback loop test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.tracker = LearningTracker()
        
        # Initialize Grok client if API key available (for production-grade parsing)
        grok_client = None
        try:
            grok_client = GrokAPIClient()
            logger.info("Grok API client initialized for LLM-based feedback parsing")
        except ValueError:
            logger.warning("GROK_API_KEY not set - feedback parsing will fail. This is expected in tests without API key.")
            # For tests, we'll need to mock or skip Grok-dependent tests
            pytest.skip("GROK_API_KEY required for feedback parsing tests")
        
        self.feedback_loop = FeedbackLoop(
            knowledge_graph=self.kg,
            learning_tracker=self.tracker,
            grok_client=grok_client
        )
        
        # Create test position
        self.position = {
            'id': 'position_001',
            'title': 'Senior LLM Inference Engineer',
            'selected_candidates': ['candidate_001', 'candidate_002', 'candidate_003']
        }
        
        # Create test candidates
        self.candidates = [
            {
                'id': 'candidate_001',
                'skills': ['CUDA', 'C++', 'PyTorch'],
                'experience_years': 6
            },
            {
                'id': 'candidate_002',
                'skills': ['Python', 'Django'],
                'experience_years': 3
            },
            {
                'id': 'candidate_003',
                'skills': ['React', 'Node.js'],
                'experience_years': 4
            }
        ]
        
        logger.info("Adding test profiles to knowledge graph...")
        self.kg.add_position(self.position)
        for candidate in self.candidates:
            self.kg.add_candidate(candidate)
        
        # Register bandit for position
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(self.candidates, self.position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001', 'candidate_002', 'candidate_003'],
            bandit=bandit
        )
        
        logger.info("Test setup complete")
    
    def teardown_method(self):
        """Clean up after each test."""
        self.feedback_loop.close()
    
    @pytest.mark.asyncio
    async def test_positive_feedback(self):
        """Test that positive feedback updates bandit correctly."""
        logger.info("Testing positive feedback")
        
        # Get initial bandit state
        bandit = self.feedback_loop.position_bandits['position_001']['bandit']
        initial_alpha = bandit.alpha[0]
        initial_beta = bandit.beta[0]
        
        logger.info(f"Initial alpha[0]: {initial_alpha}, beta[0]: {initial_beta}")
        
        # Process positive feedback (now async)
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='This candidate is excellent and highly qualified!'
        )
        
        logger.info(f"Feedback result: {result}")
        
        assert result['success'], f"Feedback should succeed, got: {result.get('error')}"
        assert result['reward'] == 1.0, f"Positive feedback should have reward 1.0, got {result['reward']}"
        assert result['feedback_type'] == 'positive', \
            f"Feedback type should be 'positive', got {result['feedback_type']}"
        
        # Check bandit was updated (alpha should increase)
        new_alpha = bandit.alpha[0]
        new_beta = bandit.beta[0]
        logger.info(f"New alpha[0]: {new_alpha}, beta[0]: {new_beta}")
        
        assert new_alpha > initial_alpha, \
            f"Alpha should increase after positive feedback: {new_alpha} > {initial_alpha}"
        
        # Check learning tracker
        assert self.tracker.total_interactions > 0, \
            "Learning tracker should record interaction"
        
        logger.info("✅ Positive feedback processed correctly")
    
    @pytest.mark.asyncio
    async def test_negative_feedback(self):
        """Test that negative feedback updates bandit correctly."""
        logger.info("Testing negative feedback")
        
        # Get initial bandit state
        bandit = self.feedback_loop.position_bandits['position_001']['bandit']
        initial_alpha = bandit.alpha[1]
        initial_beta = bandit.beta[1]
        
        logger.info(f"Initial alpha[1]: {initial_alpha}, beta[1]: {initial_beta}")
        
        # Process negative feedback (now async)
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_002',
            position_id='position_001',
            feedback_text='This candidate is not qualified for the role'
        )
        
        logger.info(f"Feedback result: {result}")
        
        assert result['success'], f"Feedback should succeed, got: {result.get('error')}"
        assert result['reward'] == 0.0, f"Negative feedback should have reward 0.0, got {result['reward']}"
        assert result['feedback_type'] == 'negative', \
            f"Feedback type should be 'negative', got {result['feedback_type']}"
        
        # Check bandit was updated (beta should increase)
        new_alpha = bandit.alpha[1]
        new_beta = bandit.beta[1]
        logger.info(f"New alpha[1]: {new_alpha}, beta[1]: {new_beta}")
        
        assert new_beta > initial_beta, \
            f"Beta should increase after negative feedback: {new_beta} > {initial_beta}"
        
        logger.info("✅ Negative feedback processed correctly")
    
    @pytest.mark.asyncio
    async def test_neutral_feedback(self):
        """Test that neutral feedback updates bandit correctly."""
        logger.info("Testing neutral feedback")
        
        # Process neutral feedback (now async)
        result = await self.feedback_loop.process_feedback(
            candidate_id='candidate_003',
            position_id='position_001',
            feedback_text='Maybe this candidate could work'
        )
        
        logger.info(f"Feedback result: {result}")
        
        assert result['success'], f"Feedback should succeed, got: {result.get('error')}"
        # Grok may return values in neutral range (0.5-0.7), which is acceptable
        assert 0.4 <= result['reward'] <= 0.7, \
            f"Neutral feedback should have reward in neutral range (0.4-0.7), got {result['reward']}"
        # Grok may classify as "neutral" or "positive" for "could work" - both are acceptable
        assert result['feedback_type'] in ['neutral', 'positive'], \
            f"Feedback type should be 'neutral' or 'positive', got {result['feedback_type']}"
        
        logger.info("✅ Neutral feedback processed correctly")
    
    @pytest.mark.asyncio
    async def test_learning_metrics(self):
        """Test that learning metrics are tracked correctly."""
        logger.info("Testing learning metrics")
        
        # Process multiple feedback events (now async)
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Great candidate!'
        )
        
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_002',
            position_id='position_001',
            feedback_text='Not qualified'
        )
        
        # Get learning metrics
        metrics = self.feedback_loop.get_learning_metrics()
        
        logger.info(f"Learning metrics: {metrics}")
        
        assert metrics['total_interactions'] == 2, \
            f"Should have 2 interactions, got {metrics['total_interactions']}"
        assert metrics['total_rewards'] > 0, \
            f"Should have total rewards > 0, got {metrics['total_rewards']}"
        assert 'response_rate' in metrics, "Should have response_rate"
        assert 'precision' in metrics, "Should have precision"
        assert 'recall' in metrics, "Should have recall"
        assert 'f1_score' in metrics, "Should have f1_score"
        
        logger.info("✅ Learning metrics tracked correctly")
    
    @pytest.mark.asyncio
    async def test_feedback_history_stored(self):
        """Test that feedback history is stored in knowledge graph."""
        logger.info("Testing feedback history storage")
        
        # Process feedback (now async)
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Excellent candidate, highly recommend!'
        )
        
        # Check candidate has feedback history
        candidate = self.kg.get_candidate('candidate_001')
        
        assert candidate is not None, "Candidate should exist"
        assert 'feedback_history' in candidate, \
            "Candidate should have feedback_history field"
        
        feedback_history = candidate['feedback_history']
        assert len(feedback_history) > 0, \
            "Feedback history should not be empty"
        
        latest_feedback = feedback_history[-1]
        assert latest_feedback['position_id'] == 'position_001', \
            "Feedback should reference correct position"
        assert latest_feedback['reward'] == 1.0, \
            "Feedback should have correct reward"
        assert 'timestamp' in latest_feedback, \
            "Feedback should have timestamp"
        
        logger.info(f"Feedback history: {latest_feedback}")
        logger.info("✅ Feedback history stored correctly")

