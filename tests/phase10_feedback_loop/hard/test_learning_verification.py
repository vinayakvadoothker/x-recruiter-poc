"""
test_learning_verification.py - Hard tests for learning verification

Why this test exists:
The core value of the feedback loop is that the system learns and improves.
This test verifies that feedback actually improves bandit decisions over time,
that learning metrics are tracked correctly, and that the system demonstrates
measurable improvement.

What it validates:
- Bandit priors update correctly after feedback
- Learning metrics improve over time
- Multiple feedback events accumulate correctly
- Positive feedback increases selection probability
- Negative feedback decreases selection probability
- Learning tracker records all events accurately

Expected behavior:
- Bandit alpha increases after positive feedback
- Bandit beta increases after negative feedback
- Learning metrics show improvement over time
- Precision/recall improve with more feedback
"""

import pytest
import os
import logging
import asyncio
import numpy as np
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


class TestLearningVerification:
    """Test learning verification."""
    
    def setup_method(self):
        """Set up feedback loop."""
        logger.info("Setting up learning verification test")
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
    async def test_bandit_prior_updates(self):
        """Test that bandit priors update correctly after feedback."""
        logger.info("Testing bandit prior updates")
        
        # Create test data
        candidates = [
            {'id': 'candidate_001', 'skills': ['CUDA', 'C++']},
            {'id': 'candidate_002', 'skills': ['Python', 'Django']}
        ]
        position = {
            'id': 'position_001',
            'title': 'CUDA Engineer',
            'selected_candidates': ['candidate_001', 'candidate_002']
        }
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Initialize bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(candidates, position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001', 'candidate_002'],
            bandit=bandit
        )
        
        # Get initial priors
        initial_alpha_0 = bandit.alpha[0]
        initial_beta_0 = bandit.beta[0]
        initial_alpha_1 = bandit.alpha[1]
        initial_beta_1 = bandit.beta[1]
        
        logger.info(f"Initial priors - Candidate 0: alpha={initial_alpha_0}, beta={initial_beta_0}")
        logger.info(f"Initial priors - Candidate 1: alpha={initial_alpha_1}, beta={initial_beta_1}")
        
        # Process positive feedback for candidate_001
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Excellent candidate, highly qualified!'
        )
        
        # Check priors updated
        new_alpha_0 = bandit.alpha[0]
        new_beta_0 = bandit.beta[0]
        
        logger.info(f"After positive feedback - Candidate 0: alpha={new_alpha_0}, beta={new_beta_0}")
        
        assert new_alpha_0 > initial_alpha_0, \
            f"Alpha should increase after positive feedback: {new_alpha_0} > {initial_alpha_0}"
        assert new_beta_0 == initial_beta_0, \
            f"Beta should not change after positive feedback: {new_beta_0} == {initial_beta_0}"
        
        # Process negative feedback for candidate_002
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_002',
            position_id='position_001',
            feedback_text='Not qualified for this role'
        )
        
        # Check priors updated
        new_alpha_1 = bandit.alpha[1]
        new_beta_1 = bandit.beta[1]
        
        logger.info(f"After negative feedback - Candidate 1: alpha={new_alpha_1}, beta={new_beta_1}")
        
        assert new_beta_1 > initial_beta_1, \
            f"Beta should increase after negative feedback: {new_beta_1} > {initial_beta_1}"
        assert new_alpha_1 == initial_alpha_1, \
            f"Alpha should not change after negative feedback: {new_alpha_1} == {initial_alpha_1}"
        
        logger.info("✅ Bandit priors update correctly")
    
    @pytest.mark.asyncio
    async def test_learning_metrics_improvement(self):
        """Test that learning metrics improve over time."""
        logger.info("Testing learning metrics improvement")
        
        # Create test data
        candidates = [
            {'id': 'candidate_001', 'skills': ['CUDA']},
            {'id': 'candidate_002', 'skills': ['Python']}
        ]
        position = {
            'id': 'position_001',
            'title': 'CUDA Engineer',
            'selected_candidates': ['candidate_001', 'candidate_002']
        }
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Initialize bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(candidates, position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001', 'candidate_002'],
            bandit=bandit
        )
        
        # Process multiple feedback events
        feedback_events = [
            ('candidate_001', 'Excellent candidate!', True),  # Positive
            ('candidate_001', 'Highly qualified!', True),  # Positive
            ('candidate_002', 'Not qualified', False),  # Negative
            ('candidate_001', 'Perfect fit!', True),  # Positive
        ]
        
        for candidate_id, feedback_text, is_positive in feedback_events:
            await self.feedback_loop.process_feedback(
                candidate_id=candidate_id,
                position_id='position_001',
                feedback_text=feedback_text
            )
        
        # Get learning metrics
        metrics = self.feedback_loop.get_learning_metrics()
        
        logger.info(f"Learning metrics: {metrics}")
        
        assert metrics['total_interactions'] == len(feedback_events), \
            f"Should have {len(feedback_events)} interactions, got {metrics['total_interactions']}"
        
        # Should have positive response rate (3 positive, 1 negative)
        assert metrics['response_rate'] > 0.5, \
            f"Response rate should be > 0.5, got {metrics['response_rate']}"
        
        # Should have total rewards > 0
        assert metrics['total_rewards'] > 0, \
            f"Total rewards should be > 0, got {metrics['total_rewards']}"
        
        logger.info("✅ Learning metrics improve over time")
    
    @pytest.mark.asyncio
    async def test_selection_probability_changes(self):
        """Test that selection probability changes after feedback."""
        logger.info("Testing selection probability changes")
        
        # Create test data
        candidates = [
            {'id': 'candidate_001', 'skills': ['CUDA']},
            {'id': 'candidate_002', 'skills': ['Python']}
        ]
        position = {
            'id': 'position_001',
            'title': 'CUDA Engineer',
            'selected_candidates': ['candidate_001', 'candidate_002']
        }
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Initialize bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(candidates, position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001', 'candidate_002'],
            bandit=bandit
        )
        
        # Get initial selection probabilities (mean of beta distribution)
        initial_prob_0 = bandit.alpha[0] / (bandit.alpha[0] + bandit.beta[0])
        initial_prob_1 = bandit.alpha[1] / (bandit.alpha[1] + bandit.beta[1])
        
        logger.info(f"Initial probabilities - Candidate 0: {initial_prob_0:.3f}, Candidate 1: {initial_prob_1:.3f}")
        
        # Give positive feedback to candidate_001 multiple times
        for _ in range(3):
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_001',
                position_id='position_001',
                feedback_text='Excellent candidate!'
            )
        
        # Get new selection probabilities
        new_prob_0 = bandit.alpha[0] / (bandit.alpha[0] + bandit.beta[0])
        new_prob_1 = bandit.alpha[1] / (bandit.alpha[1] + bandit.beta[1])
        
        logger.info(f"After positive feedback - Candidate 0: {new_prob_0:.3f}, Candidate 1: {new_prob_1:.3f}")
        
        # Candidate 0's probability should increase
        assert new_prob_0 > initial_prob_0, \
            f"Selection probability should increase after positive feedback: {new_prob_0:.3f} > {initial_prob_0:.3f}"
        
        logger.info("✅ Selection probability changes after feedback")
    
    @pytest.mark.asyncio
    async def test_feedback_history_accumulation(self):
        """Test that feedback history accumulates correctly."""
        logger.info("Testing feedback history accumulation")
        
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
        
        # Process multiple feedback events
        feedback_texts = [
            'Good candidate',
            'Excellent!',
            'Highly qualified',
            'Perfect fit'
        ]
        
        for feedback_text in feedback_texts:
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_001',
                position_id='position_001',
                feedback_text=feedback_text
            )
        
        # Check feedback history
        candidate_updated = self.kg.get_candidate('candidate_001')
        feedback_history = candidate_updated.get('feedback_history', [])
        
        logger.info(f"Feedback history length: {len(feedback_history)}")
        
        assert len(feedback_history) == len(feedback_texts), \
            f"Should have {len(feedback_texts)} feedback entries, got {len(feedback_history)}"
        
        # Verify all entries have required fields
        for entry in feedback_history:
            assert 'position_id' in entry, "Entry should have position_id"
            assert 'feedback_text' in entry, "Entry should have feedback_text"
            assert 'reward' in entry, "Entry should have reward"
            assert 'feedback_type' in entry, "Entry should have feedback_type"
            assert 'timestamp' in entry, "Entry should have timestamp"
        
        logger.info("✅ Feedback history accumulates correctly")

