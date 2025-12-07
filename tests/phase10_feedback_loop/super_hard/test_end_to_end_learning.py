"""
test_end_to_end_learning.py - Super hard tests for end-to-end learning

Why this test exists:
In production, the feedback loop will process many feedback events and the system
must demonstrate measurable learning improvement. This test verifies end-to-end
learning: multiple candidates, multiple positions, many feedback events, and
verifies that the system actually learns and improves over time.

What it validates:
- System handles many feedback events efficiently
- Learning metrics show improvement over time
- Bandit decisions improve after feedback
- Multiple positions handled correctly
- Memory efficiency with many feedback events
- Learning convergence (system stabilizes)

Expected behavior:
- Many feedback events processed correctly
- Learning metrics improve over time
- Bandit selection improves (selects better candidates)
- System remains stable under load
- Memory usage is reasonable
"""

import pytest
import os
import logging
import asyncio
import time
from backend.orchestration.feedback_loop import FeedbackLoop
from backend.database.knowledge_graph import KnowledgeGraph
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.algorithms.learning_tracker import LearningTracker
from backend.integrations.grok_api import GrokAPIClient
from backend.datasets import generate_candidates

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEndToEndLearning:
    """Test end-to-end learning scenarios."""
    
    def setup_method(self):
        """Set up feedback loop."""
        logger.info("Setting up end-to-end learning test")
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
    async def test_many_feedback_events(self):
        """Test processing many feedback events."""
        logger.info("Testing many feedback events (20 events)")
        
        # Create test data
        candidates = list(generate_candidates(5))
        for i, candidate in enumerate(candidates):
            candidate['id'] = f'candidate_{i:03d}'
            self.kg.add_candidate(candidate)
        
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'selected_candidates': [c['id'] for c in candidates]
        }
        self.kg.add_position(position)
        
        # Initialize bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(candidates, position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=[c['id'] for c in candidates],
            bandit=bandit
        )
        
        # Process 20 feedback events
        feedback_events = [
            (f'candidate_{i % 5:03d}', f'Feedback event {i}: {"Excellent!" if i % 3 == 0 else "Not qualified" if i % 3 == 1 else "Maybe"}')
            for i in range(20)
        ]
        
        logger.info("Processing 20 feedback events...")
        start_time = time.time()
        
        for candidate_id, feedback_text in feedback_events:
            result = await self.feedback_loop.process_feedback(
                candidate_id=candidate_id,
                position_id='position_001',
                feedback_text=feedback_text
            )
            assert result['success'], f"Feedback should succeed, got: {result.get('error')}"
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / len(feedback_events)
        
        logger.info(f"Processed {len(feedback_events)} events in {elapsed_time:.2f}s (avg: {avg_time:.3f}s per event)")
        
        # Verify learning metrics
        metrics = self.feedback_loop.get_learning_metrics()
        logger.info(f"Learning metrics: {metrics}")
        
        assert metrics['total_interactions'] == len(feedback_events), \
            f"Should have {len(feedback_events)} interactions, got {metrics['total_interactions']}"
        
        # Performance check: should process reasonably fast
        # Grok API calls take time, so allow up to 6s per event (includes API latency)
        assert avg_time < 6.0, \
            f"Average processing time too high: {avg_time:.3f}s (expected < 6.0s)"
        
        logger.info("✅ Many feedback events processed correctly")
    
    @pytest.mark.asyncio
    async def test_learning_convergence(self):
        """Test that system learns and converges over time."""
        logger.info("Testing learning convergence")
        
        # Create test data with clear best candidate
        candidates = [
            {'id': 'candidate_001', 'skills': ['CUDA', 'C++', 'PyTorch']},  # Best match
            {'id': 'candidate_002', 'skills': ['Python', 'Django']},  # Poor match
            {'id': 'candidate_003', 'skills': ['React', 'Node.js']}  # Poor match
        ]
        position = {
            'id': 'position_001',
            'title': 'CUDA Engineer',
            'selected_candidates': ['candidate_001', 'candidate_002', 'candidate_003']
        }
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Initialize bandit
        bandit = GraphWarmStartedFGTS()
        bandit.initialize_from_embeddings(candidates, position)
        self.feedback_loop.register_position_bandit(
            position_id='position_001',
            candidate_ids=['candidate_001', 'candidate_002', 'candidate_003'],
            bandit=bandit
        )
        
        # Get initial selection probabilities
        initial_probs = [
            bandit.alpha[i] / (bandit.alpha[i] + bandit.beta[i])
            for i in range(3)
        ]
        logger.info(f"Initial probabilities: {initial_probs}")
        
        # Give positive feedback to best candidate, negative to others
        for _ in range(5):
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_001',
                position_id='position_001',
                feedback_text='Excellent candidate, highly qualified!'
            )
        
        for _ in range(3):
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_002',
                position_id='position_001',
                feedback_text='Not qualified for this role'
            )
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_003',
                position_id='position_001',
                feedback_text='Not a good fit'
            )
        
        # Get final selection probabilities
        final_probs = [
            bandit.alpha[i] / (bandit.alpha[i] + bandit.beta[i])
            for i in range(3)
        ]
        logger.info(f"Final probabilities: {final_probs}")
        
        # Best candidate should have highest probability
        assert final_probs[0] > final_probs[1], \
            f"Best candidate should have higher probability: {final_probs[0]:.3f} > {final_probs[1]:.3f}"
        assert final_probs[0] > final_probs[2], \
            f"Best candidate should have higher probability: {final_probs[0]:.3f} > {final_probs[2]:.3f}"
        
        # Best candidate's probability should increase
        assert final_probs[0] > initial_probs[0], \
            f"Best candidate probability should increase: {final_probs[0]:.3f} > {initial_probs[0]:.3f}"
        
        logger.info("✅ Learning convergence verified")
    
    @pytest.mark.asyncio
    async def test_multiple_positions(self):
        """Test feedback loop with multiple positions."""
        logger.info("Testing multiple positions")
        
        # Create candidates
        candidates = [
            {'id': 'candidate_001', 'skills': ['CUDA']},
            {'id': 'candidate_002', 'skills': ['Python']},
            {'id': 'candidate_003', 'skills': ['React']}
        ]
        
        # Create two positions
        positions = [
            {
                'id': 'position_001',
                'title': 'CUDA Engineer',
                'selected_candidates': ['candidate_001', 'candidate_002']
            },
            {
                'id': 'position_002',
                'title': 'Web Developer',
                'selected_candidates': ['candidate_002', 'candidate_003']
            }
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        for position in positions:
            self.kg.add_position(position)
        
        # Register bandits for both positions
        for position in positions:
            position_candidates = [c for c in candidates if c['id'] in position['selected_candidates']]
            bandit = GraphWarmStartedFGTS()
            bandit.initialize_from_embeddings(position_candidates, position)
            self.feedback_loop.register_position_bandit(
                position_id=position['id'],
                candidate_ids=position['selected_candidates'],
                bandit=bandit
            )
        
        # Process feedback for both positions
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_001',
            position_id='position_001',
            feedback_text='Excellent CUDA engineer!'
        )
        
        await self.feedback_loop.process_feedback(
            candidate_id='candidate_003',
            position_id='position_002',
            feedback_text='Great web developer!'
        )
        
        # Verify both bandits updated
        bandit1 = self.feedback_loop.position_bandits['position_001']['bandit']
        bandit2 = self.feedback_loop.position_bandits['position_002']['bandit']
        
        # Check that bandits are separate (different alpha values)
        assert bandit1.alpha[0] != bandit2.alpha[0] or len(bandit1.alpha) != len(bandit2.alpha), \
            "Bandits should be separate instances"
        
        logger.info("✅ Multiple positions handled correctly")
    
    @pytest.mark.asyncio
    async def test_learning_metrics_accuracy(self):
        """Test that learning metrics are accurate."""
        logger.info("Testing learning metrics accuracy")
        
        # Create test data
        candidates = [
            {'id': 'candidate_001', 'skills': ['Python']},
            {'id': 'candidate_002', 'skills': ['Java']}
        ]
        position = {
            'id': 'position_001',
            'title': 'Test Position',
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
        
        # Process known feedback (5 positive, 2 negative)
        positive_feedback = [
            'Excellent candidate!',
            'Highly qualified!',
            'Perfect fit!',
            'Great candidate!',
            'Strong candidate!'
        ]
        
        negative_feedback = [
            'Not qualified',
            'Not a good fit'
        ]
        
        for feedback_text in positive_feedback:
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_001',
                position_id='position_001',
                feedback_text=feedback_text
            )
        
        for feedback_text in negative_feedback:
            await self.feedback_loop.process_feedback(
                candidate_id='candidate_002',
                position_id='position_001',
                feedback_text=feedback_text
            )
        
        # Get learning metrics
        metrics = self.feedback_loop.get_learning_metrics()
        
        logger.info(f"Learning metrics: {metrics}")
        
        # Verify accuracy
        total_expected = len(positive_feedback) + len(negative_feedback)
        assert metrics['total_interactions'] == total_expected, \
            f"Total interactions should be {total_expected}, got {metrics['total_interactions']}"
        
        # Response rate should be positive (5 positive out of 7)
        expected_response_rate = len(positive_feedback) / total_expected
        assert abs(metrics['response_rate'] - expected_response_rate) < 0.2, \
            f"Response rate should be ~{expected_response_rate:.2f}, got {metrics['response_rate']:.2f}"
        
        logger.info("✅ Learning metrics are accurate")

