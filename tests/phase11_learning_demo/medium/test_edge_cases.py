"""
test_edge_cases.py - Medium tests for edge cases

Why this test exists:
This test verifies that the learning demo handles edge cases gracefully.
Real-world scenarios include empty candidate lists, single candidates, and
scenarios where improvement may not occur. We need to ensure the system
handles these cases without crashing.

What it validates:
- Empty candidate list raises appropriate error
- Single candidate simulation works
- Simulation with minimal feedback events works
- Scenarios where warm-start may not show improvement
- Missing data handling

Expected behavior:
- Empty candidates → ValueError
- Single candidate → Simulation runs (trivial case)
- Minimal events → Simulation completes with fewer data points
- No improvement → Metrics still calculated correctly
"""

import pytest
import os
import logging
from backend.orchestration.learning_demo import LearningDemo
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases for learning demo."""
    
    def setup_method(self):
        """Set up learning demo."""
        logger.info("Setting up edge case tests")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.demo = LearningDemo(knowledge_graph=self.kg)
        
        self.position = {
            'id': 'position_001',
            'title': 'Software Engineer',
            'required_skills': ['Python'],
            'experience_level': 'Mid',
            'domain': 'Software'
        }
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'demo'):
            self.demo.close()
        if hasattr(self, 'kg'):
            self.kg.close()
    
    def test_empty_candidates_raises_error(self):
        """Test that empty candidates list raises error."""
        logger.info("Testing empty candidates list")
        
        with pytest.raises(ValueError, match="Candidates list cannot be empty"):
            self.demo.run_learning_simulation(
                candidates=[],
                position=self.position,
                num_feedback_events=10
            )
        
        logger.info("✅ Empty candidates correctly raises ValueError")
    
    def test_single_candidate_simulation(self):
        """Test simulation with single candidate."""
        logger.info("Testing single candidate simulation")
        
        candidate = {
            'id': 'candidate_001',
            'name': 'Single Candidate',
            'skills': ['Python'],
            'experience_years': 5,
            'domain': 'Software'
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(self.position)
        
        result = self.demo.run_learning_simulation(
            candidates=[candidate],
            position=self.position,
            num_feedback_events=20
        )
        
        # Verify simulation completes
        assert 'warm_start_metrics' in result
        assert 'cold_start_metrics' in result
        assert result['simulation_config']['num_candidates'] == 1
        
        logger.info("✅ Single candidate simulation works")
    
    def test_minimal_feedback_events(self):
        """Test simulation with minimal feedback events."""
        logger.info("Testing minimal feedback events")
        
        candidates = [
            {
                'id': f'candidate_{i:03d}',
                'name': f'Candidate {i}',
                'skills': ['Python'],
                'experience_years': 5,
                'domain': 'Software'
            }
            for i in range(5)
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(self.position)
        
        result = self.demo.run_learning_simulation(
            candidates=candidates,
            position=self.position,
            num_feedback_events=5  # Very few events
        )
        
        # Verify simulation completes
        assert 'warm_start_metrics' in result
        assert 'cold_start_metrics' in result
        assert result['simulation_config']['num_feedback_events'] == 5
        
        # Verify learning curves have data
        curves = result['learning_curves']
        assert len(curves['warm_start']['events']) == 5
        assert len(curves['cold_start']['events']) == 5
        
        logger.info("✅ Minimal feedback events simulation works")
    
    def test_all_candidates_similar(self):
        """Test scenario where all candidates are similar (may not show improvement)."""
        logger.info("Testing all candidates similar scenario")
        
        # All candidates have same skills and experience
        candidates = [
            {
                'id': f'candidate_{i:03d}',
                'name': f'Candidate {i}',
                'skills': ['Python', 'Java'],
                'experience_years': 5,
                'domain': 'Software'
            }
            for i in range(5)
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(self.position)
        
        result = self.demo.run_learning_simulation(
            candidates=candidates,
            position=self.position,
            num_feedback_events=50
        )
        
        # Verify simulation completes even if improvement is minimal
        assert 'improvement_metrics' in result
        improvement = result['improvement_metrics']
        
        # Improvement may be small or None, but metrics should still be calculated
        assert 'speedup' in improvement
        assert 'regret_reduction' in improvement
        
        logger.info(f"✅ All candidates similar scenario works (speedup: {improvement.get('speedup')})")
    
    def test_compare_warm_vs_cold_start(self):
        """Test compare_warm_vs_cold_start method."""
        logger.info("Testing compare_warm_vs_cold_start")
        
        candidates = [
            {
                'id': f'candidate_{i:03d}',
                'name': f'Candidate {i}',
                'skills': ['Python'] if i < 3 else ['Java'],
                'experience_years': 5,
                'domain': 'Software'
            }
            for i in range(5)
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(self.position)
        
        comparison = self.demo.compare_warm_vs_cold_start(
            candidates=candidates,
            position=self.position,
            num_feedback_events=50
        )
        
        # Verify comparison structure
        assert 'warm_start' in comparison
        assert 'cold_start' in comparison
        assert 'improvement' in comparison
        
        # Verify metrics are present
        assert 'final_precision' in comparison['warm_start']
        assert 'final_precision' in comparison['cold_start']
        
        logger.info("✅ compare_warm_vs_cold_start works correctly")

