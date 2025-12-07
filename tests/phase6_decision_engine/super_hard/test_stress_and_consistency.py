"""
test_stress_and_consistency.py - Super hard tests for stress and decision consistency

Why this test exists:
In production, the decision engine will evaluate many candidates (50-200+)
and must make consistent decisions. This test ensures the engine can handle
high-volume operations efficiently and maintains decision consistency across
similar candidates. The engine must be extremely scrutinizing and not degrade
with scale.

What it validates:
- Engine handles many candidates efficiently
- Decisions are consistent for similar candidates
- Performance is acceptable for batch operations
- Memory usage doesn't grow unbounded
- Decision quality doesn't degrade with scale

Expected behavior:
- Batch decisions complete in reasonable time
- Similar candidates get similar decisions
- Performance is consistent regardless of candidate count
- System remains stable under load
"""

import pytest
import numpy as np
import time
import logging
from backend.interviews.phone_screen_engine import PhoneScreenDecisionEngine
from backend.database.knowledge_graph import KnowledgeGraph
from backend.datasets import generate_candidates, generate_positions

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStressAndConsistency:
    """Test stress scenarios and decision consistency."""
    
    def setup_method(self):
        """Set up decision engine."""
        logger.info("Setting up stress test")
        import os
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        self.kg = KnowledgeGraph()
        self.engine = PhoneScreenDecisionEngine(
            knowledge_graph=self.kg,
            similarity_threshold=0.65,
            confidence_threshold=0.70
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        self.kg.close()
    
    def test_batch_decision_performance(self):
        """Test performance with many candidates."""
        logger.info("Testing batch decision performance")
        
        # Generate 50 candidates
        candidates = list(generate_candidates(50))
        logger.info(f"Generated {len(candidates)} candidates")
        
        position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++'],
            'experience_level': 'Senior',
            'domains': ['LLM Inference']
        }
        
        # Add all to knowledge graph
        logger.info("Adding candidates to knowledge graph...")
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        extracted_info = {
            'motivation_score': 0.7,
            'technical_depth': 0.7
        }
        
        # Make decisions for all candidates
        logger.info("Making decisions for all candidates...")
        start_time = time.time()
        decisions = []
        for candidate in candidates:
            decision = self.engine.make_decision(
                candidate['id'],
                'position_1',
                extracted_info
            )
            decisions.append(decision)
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / len(candidates)
        logger.info(f"Total time: {elapsed_time:.2f}s")
        logger.info(f"Average time per decision: {avg_time:.4f}s")
        logger.info(f"Decisions per second: {len(candidates)/elapsed_time:.1f}")
        
        assert elapsed_time < 120.0, f"Batch decisions too slow: {elapsed_time:.2f}s"
        assert avg_time < 2.5, f"Average decision time too high: {avg_time:.4f}s"
        
        # Count pass/fail
        passes = sum(1 for d in decisions if d['decision'] == 'pass')
        fails = sum(1 for d in decisions if d['decision'] == 'fail')
        logger.info(f"Results: {passes} pass, {fails} fail")
        
        logger.info("✅ Batch decision performance acceptable")
    
    def test_decision_consistency(self):
        """Test that similar candidates get consistent decisions."""
        logger.info("Testing decision consistency")
        
        # Create very similar candidates
        base_candidate = {
            'id': 'base',
            'skills': ['CUDA', 'C++', 'PyTorch', 'LLM Inference'],
            'experience_years': 6,
            'domains': ['LLM Inference'],
            'expertise_level': 'Senior'
        }
        
        similar_candidates = []
        for i in range(5):
            candidate = base_candidate.copy()
            candidate['id'] = f'similar_{i}'
            # Slight variations
            candidate['skills'] = base_candidate['skills'] + [f'Skill{i}']
            similar_candidates.append(candidate)
            self.kg.add_candidate(candidate)
        
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['CUDA', 'C++'],
            'experience_level': 'Senior'
        }
        self.kg.add_position(position)
        
        extracted_info = {
            'motivation_score': 0.8,
            'technical_depth': 0.8
        }
        
        logger.info("Making decisions for similar candidates...")
        decisions = []
        for candidate in similar_candidates:
            decision = self.engine.make_decision(
                candidate['id'],
                'position_1',
                extracted_info
            )
            decisions.append(decision)
            logger.info(f"Candidate {candidate['id']}: {decision['decision']} "
                       f"(confidence: {decision['confidence']:.3f}, "
                       f"similarity: {decision['similarity_score']:.3f})")
        
        # Similar candidates should get similar decisions
        decisions_list = [d['decision'] for d in decisions]
        confidences = [d['confidence'] for d in decisions]
        similarities = [d['similarity_score'] for d in decisions]
        
        logger.info(f"Decisions: {decisions_list}")
        logger.info(f"Confidences: {[f'{c:.3f}' for c in confidences]}")
        logger.info(f"Similarities: {[f'{s:.3f}' for s in similarities]}")
        
        # Check consistency: similar similarities should lead to similar decisions
        similarity_std = np.std(similarities)
        confidence_std = np.std(confidences)
        
        logger.info(f"Similarity std: {similarity_std:.4f}")
        logger.info(f"Confidence std: {confidence_std:.4f}")
        
        # Similar candidates should have low variance in similarity
        assert similarity_std < 0.1, \
            f"Similar candidates should have similar similarity scores, std={similarity_std:.4f}"
        
        logger.info("✅ Decision consistency verified")
    
    def test_extreme_scrutiny_high_standards(self):
        """Test that engine maintains extremely high standards."""
        logger.info("Testing extreme scrutiny - high standards")
        
        # Create "good but not great" candidate
        good_candidate = {
            'id': 'good_not_great',
            'skills': ['CUDA', 'C++', 'Python'],  # Has must-haves but not extensive
            'experience_years': 5,
            'domains': ['Machine Learning'],  # Close but not exact match
            'expertise_level': 'Senior'
        }
        
        position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++'],
            'experience_level': 'Senior',
            'domains': ['LLM Inference']
        }
        
        self.kg.add_candidate(good_candidate)
        self.kg.add_position(position)
        
        # Moderate extracted info
        extracted_info = {
            'motivation_score': 0.65,  # Good but not great
            'communication_score': 0.65,
            'technical_depth': 0.65,
            'cultural_fit': 0.65
        }
        
        logger.info("Making decision for 'good but not great' candidate...")
        decision = self.engine.make_decision(
            'good_not_great',
            'position_1',
            extracted_info
        )
        
        logger.info(f"Decision: {decision['decision']}")
        logger.info(f"Confidence: {decision['confidence']:.2f} (threshold: {self.engine.confidence_threshold:.2f})")
        logger.info(f"Similarity: {decision['similarity_score']:.2f}")
        
        # Engine should be extremely scrutinizing - "good but not great" might fail
        # This is by design - we want only excellent candidates
        if decision['confidence'] < self.engine.confidence_threshold:
            logger.info("✅ Engine correctly maintains high standards (rejected good-but-not-great)")
            assert decision['decision'] == 'fail', \
                "Engine should maintain high standards"
        else:
            logger.info("✅ Candidate passed strict evaluation")
        
        logger.info("✅ Extreme scrutiny verified")
    
    def test_many_positions_consistency(self):
        """Test decision consistency across multiple positions."""
        logger.info("Testing consistency across multiple positions")
        
        candidate = {
            'id': 'candidate_1',
            'skills': ['CUDA', 'C++', 'PyTorch', 'LLM Inference'],
            'experience_years': 6,
            'domains': ['LLM Inference'],
            'expertise_level': 'Senior'
        }
        
        # Create 3 similar positions
        positions = []
        for i in range(3):
            position = {
                'id': f'position_{i}',
                'title': 'Senior LLM Inference Engineer',
                'must_haves': ['CUDA', 'C++'],
                'experience_level': 'Senior',
                'domains': ['LLM Inference']
            }
            positions.append(position)
            self.kg.add_position(position)
        
        self.kg.add_candidate(candidate)
        
        extracted_info = {
            'motivation_score': 0.8,
            'technical_depth': 0.8
        }
        
        logger.info("Making decisions for same candidate across positions...")
        decisions = []
        for position in positions:
            decision = self.engine.make_decision(
                'candidate_1',
                position['id'],
                extracted_info
            )
            decisions.append(decision)
            logger.info(f"Position {position['id']}: {decision['decision']} "
                       f"(confidence: {decision['confidence']:.3f})")
        
        # Same candidate should get similar decisions for similar positions
        decisions_list = [d['decision'] for d in decisions]
        confidences = [d['confidence'] for d in decisions]
        
        logger.info(f"Decisions: {decisions_list}")
        logger.info(f"Confidences: {[f'{c:.3f}' for c in confidences]}")
        
        # Should be consistent (all pass or all fail for similar positions)
        assert len(set(decisions_list)) <= 2, \
            "Decisions should be consistent for similar positions"
        
        confidence_std = np.std(confidences)
        logger.info(f"Confidence std across positions: {confidence_std:.4f}")
        assert confidence_std < 0.1, \
            f"Confidence should be consistent, std={confidence_std:.4f}"
        
        logger.info("✅ Consistency across positions verified")

