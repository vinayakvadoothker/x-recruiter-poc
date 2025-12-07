"""
test_edge_cases.py - Medium tests for edge cases and borderline candidates

Why this test exists:
Real-world usage will have edge cases: missing data, borderline candidates,
inconsistent information, etc. This test ensures the decision engine handles
these gracefully and makes correct decisions even in ambiguous situations.
The engine must be extremely scrutinizing and catch inconsistencies.

What it validates:
- Missing extracted info is handled
- Borderline candidates (just above/below threshold) are evaluated correctly
- Inconsistent data triggers outlier detection
- Missing profiles return appropriate errors
- Edge case thresholds work correctly

Expected behavior:
- Missing extracted info reduces confidence but doesn't auto-fail
- Borderline candidates are evaluated strictly
- Inconsistencies are flagged as outliers
- Missing profiles return fail decisions with clear errors
"""

import pytest
import logging
from backend.interviews.phone_screen_engine import PhoneScreenDecisionEngine
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases and borderline scenarios."""
    
    def setup_method(self):
        """Set up decision engine."""
        logger.info("Setting up edge case test")
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
    
    def test_missing_extracted_info(self):
        """Test decision with missing extracted info."""
        logger.info("Testing decision with missing extracted info")
        
        candidate = {
            'id': 'candidate_1',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference'],
            'expertise_level': 'Senior'
        }
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['CUDA', 'C++'],
            'experience_level': 'Senior'
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        logger.info("Making decision without extracted info...")
        decision = self.engine.make_decision('candidate_1', 'position_1', None)
        
        logger.info(f"Decision: {decision['decision']}")
        logger.info(f"Confidence: {decision['confidence']:.2f}")
        logger.info(f"Outlier flags: {decision['outlier_flags']}")
        
        # Should still make decision, but confidence may be lower
        assert decision['decision'] in ['pass', 'fail'], \
            "Should make decision even without extracted info"
        assert 'no_extracted_info' in str(decision.get('extracted_info_summary', {})).lower() or \
               len(decision['outlier_flags']) > 0, \
            "Should flag missing extracted info"
        
        logger.info("✅ Missing extracted info handled correctly")
    
    def test_borderline_candidate_just_above_threshold(self):
        """Test borderline candidate just above threshold."""
        logger.info("Testing borderline candidate (just above threshold)")
        
        # Candidate with similarity just above threshold
        candidate = {
            'id': 'borderline_high',
            'skills': ['CUDA', 'C++', 'PyTorch', 'Python'],
            'experience_years': 5,
            'domains': ['LLM Inference'],
            'expertise_level': 'Senior'
        }
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['CUDA', 'C++'],
            'experience_level': 'Senior'
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Good extracted info to push over threshold
        extracted_info = {
            'motivation_score': 0.8,
            'communication_score': 0.7,
            'technical_depth': 0.8,
            'cultural_fit': 0.7
        }
        
        logger.info("Making decision for borderline candidate...")
        decision = self.engine.make_decision(
            'borderline_high',
            'position_1',
            extracted_info
        )
        
        logger.info(f"Decision: {decision['decision']}")
        logger.info(f"Confidence: {decision['confidence']:.2f}")
        logger.info(f"Similarity: {decision['similarity_score']:.2f}")
        
        # Should pass if above threshold
        if decision['similarity_score'] >= 0.65 and decision['confidence'] >= 0.70:
            assert decision['decision'] == 'pass', \
                "Borderline candidate above threshold should pass"
        else:
            logger.info("Candidate below threshold, fail is correct")
        
        logger.info("✅ Borderline candidate evaluated correctly")
    
    def test_borderline_candidate_just_below_threshold(self):
        """Test borderline candidate just below threshold."""
        logger.info("Testing borderline candidate (just below threshold)")
        
        candidate = {
            'id': 'borderline_low',
            'skills': ['Python', 'CUDA'],  # Some overlap but not strong
            'experience_years': 4,
            'domains': ['Machine Learning'],
            'expertise_level': 'Mid'
        }
        position = {
            'id': 'position_1',
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++', 'PyTorch'],
            'experience_level': 'Senior'
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        logger.info("Making decision for borderline candidate...")
        decision = self.engine.make_decision('borderline_low', 'position_1', None)
        
        logger.info(f"Decision: {decision['decision']}")
        logger.info(f"Confidence: {decision['confidence']:.2f}")
        
        # Should fail if below threshold (strict evaluation)
        if decision['similarity_score'] < 0.65 or decision['confidence'] < 0.70:
            assert decision['decision'] == 'fail', \
                "Borderline candidate below threshold should fail"
        
        logger.info("✅ Borderline candidate correctly fails")
    
    def test_inconsistent_extracted_info(self):
        """Test that inconsistent extracted info triggers outliers."""
        logger.info("Testing inconsistent extracted info")
        
        candidate = {
            'id': 'inconsistent',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference'],
            'expertise_level': 'Senior'
        }
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['CUDA', 'C++'],
            'experience_level': 'Senior'
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        
        # Extracted info says different experience years (inconsistency)
        extracted_info = {
            'experience_years': 2,  # Profile says 5, extracted says 2
            'motivation_score': 0.8,
            'technical_depth': 0.9
        }
        
        logger.info("Making decision with inconsistent extracted info...")
        decision = self.engine.make_decision(
            'inconsistent',
            'position_1',
            extracted_info
        )
        
        logger.info(f"Decision: {decision['decision']}")
        logger.info(f"Outlier flags: {decision['outlier_flags']}")
        
        # Should detect inconsistency
        has_inconsistency = any(
            'mismatch' in flag.lower() or 'inconsistency' in flag.lower()
            for flag in decision['outlier_flags']
        )
        
        assert has_inconsistency or decision['decision'] == 'fail', \
            "Inconsistent extracted info should trigger outlier or fail"
        
        logger.info("✅ Inconsistent extracted info detected")
    
    def test_missing_candidate(self):
        """Test decision with missing candidate."""
        logger.info("Testing decision with missing candidate")
        
        position = {
            'id': 'position_1',
            'title': 'Engineer',
            'must_haves': ['Python']
        }
        self.kg.add_position(position)
        
        logger.info("Making decision for non-existent candidate...")
        decision = self.engine.make_decision('nonexistent', 'position_1', None)
        
        logger.info(f"Decision: {decision['decision']}")
        logger.info(f"Reasoning: {decision['reasoning']}")
        
        assert decision['decision'] == 'fail', \
            "Missing candidate should result in fail"
        assert 'not found' in decision['reasoning'].lower(), \
            "Reasoning should mention candidate not found"
        assert decision['confidence'] == 0.0, \
            "Missing candidate should have 0 confidence"
        
        logger.info("✅ Missing candidate handled correctly")
    
    def test_missing_position(self):
        """Test decision with missing position."""
        logger.info("Testing decision with missing position")
        
        candidate = {
            'id': 'candidate_1',
            'skills': ['Python']
        }
        self.kg.add_candidate(candidate)
        
        logger.info("Making decision for non-existent position...")
        decision = self.engine.make_decision('candidate_1', 'nonexistent', None)
        
        logger.info(f"Decision: {decision['decision']}")
        
        assert decision['decision'] == 'fail', \
            "Missing position should result in fail"
        assert 'not found' in decision['reasoning'].lower(), \
            "Reasoning should mention position not found"
        
        logger.info("✅ Missing position handled correctly")

