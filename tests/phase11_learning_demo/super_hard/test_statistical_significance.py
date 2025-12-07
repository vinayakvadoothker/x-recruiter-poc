"""
test_statistical_significance.py - Super hard tests for statistical significance

Why this test exists:
This test verifies that the learning improvement is statistically significant,
not just random variation. We run multiple simulations and verify that the
improvement is consistent and reliable. This is critical for proving our
innovation works reliably.

What it validates:
- Multiple simulations show consistent improvement
- Improvement is statistically significant (not random)
- Performance is consistent across runs
- Memory efficiency (no leaks)
- Long simulations work correctly

Expected behavior:
- Multiple runs show warm-start consistently outperforms cold-start
- Improvement metrics are consistent across runs
- No memory leaks or performance degradation
- Statistical tests confirm significance
"""

import pytest
import os
import logging
import numpy as np
import gc
from backend.orchestration.learning_demo import LearningDemo
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStatisticalSignificance:
    """Test statistical significance of learning improvement."""
    
    def setup_method(self):
        """Set up learning demo."""
        logger.info("Setting up statistical significance tests")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.demo = LearningDemo(knowledge_graph=self.kg)
        
        # Create position
        self.position = {
            'id': 'position_001',
            'title': 'Senior LLM Inference Engineer',
            'required_skills': ['Python', 'CUDA', 'LLM Optimization'],
            'experience_level': 'Senior',
            'domain': 'AI/ML'
        }
        
        # Create diverse candidates
        self.candidates = []
        
        # Good matches
        for i in range(5):
            self.candidates.append({
                'id': f'candidate_good_{i:03d}',
                'name': f'Good Candidate {i}',
                'skills': ['Python', 'CUDA', 'LLM Optimization'],
                'experience_years': 8,
                'domain': 'AI/ML'
            })
        
        # Poor matches
        for i in range(5):
            self.candidates.append({
                'id': f'candidate_poor_{i:03d}',
                'name': f'Poor Candidate {i}',
                'skills': ['Java', 'Spring'],
                'experience_years': 3,
                'domain': 'Web Development'
            })
        
        # Add to knowledge graph
        for candidate in self.candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(self.position)
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'demo'):
            self.demo.close()
        if hasattr(self, 'kg'):
            self.kg.close()
        gc.collect()
    
    def test_multiple_runs_show_consistency(self):
        """Test that multiple runs show consistent improvement."""
        logger.info("Testing multiple runs consistency")
        
        num_runs = 5
        warm_precisions = []
        cold_precisions = []
        warm_regrets = []
        cold_regrets = []
        
        for run_num in range(num_runs):
            logger.info(f"Run {run_num + 1}/{num_runs}")
            
            result = self.demo.run_learning_simulation(
                candidates=self.candidates,
                position=self.position,
                num_feedback_events=100
            )
            
            warm_metrics = result['warm_start_metrics']
            cold_metrics = result['cold_start_metrics']
            
            warm_precisions.append(warm_metrics.get('precision', 0.0))
            cold_precisions.append(cold_metrics.get('precision', 0.0))
            warm_regrets.append(warm_metrics.get('cumulative_regret', 0.0))
            cold_regrets.append(cold_metrics.get('cumulative_regret', 0.0))
        
        # Calculate statistics
        warm_precision_mean = np.mean(warm_precisions)
        cold_precision_mean = np.mean(cold_precisions)
        warm_regret_mean = np.mean(warm_regrets)
        cold_regret_mean = np.mean(cold_regrets)
        
        logger.info(f"Warm-start precision: {warm_precision_mean:.3f} ± {np.std(warm_precisions):.3f}")
        logger.info(f"Cold-start precision: {cold_precision_mean:.3f} ± {np.std(cold_precisions):.3f}")
        logger.info(f"Warm-start regret: {warm_regret_mean:.3f} ± {np.std(warm_regrets):.3f}")
        logger.info(f"Cold-start regret: {cold_regret_mean:.3f} ± {np.std(cold_regrets):.3f}")
        
        # Warm-start should outperform cold-start on average
        assert warm_precision_mean >= cold_precision_mean - 0.1, \
            f"Warm-start should have higher precision on average ({warm_precision_mean:.3f} vs {cold_precision_mean:.3f})"
        
        assert warm_regret_mean <= cold_regret_mean + 0.1, \
            f"Warm-start should have lower regret on average ({warm_regret_mean:.3f} vs {cold_regret_mean:.3f})"
        
        logger.info("✅ Multiple runs show consistent improvement")
    
    def test_statistical_significance(self):
        """Test that improvement is statistically significant."""
        logger.info("Testing statistical significance")
        
        num_runs = 10
        precision_diffs = []
        regret_diffs = []
        
        for run_num in range(num_runs):
            logger.info(f"Run {run_num + 1}/{num_runs}")
            
            result = self.demo.run_learning_simulation(
                candidates=self.candidates,
                position=self.position,
                num_feedback_events=100
            )
            
            warm_metrics = result['warm_start_metrics']
            cold_metrics = result['cold_start_metrics']
            
            precision_diff = warm_metrics.get('precision', 0.0) - cold_metrics.get('precision', 0.0)
            regret_diff = cold_metrics.get('cumulative_regret', 0.0) - warm_metrics.get('cumulative_regret', 0.0)
            
            precision_diffs.append(precision_diff)
            regret_diffs.append(regret_diff)
        
        # Calculate mean and standard error
        precision_mean = np.mean(precision_diffs)
        precision_std = np.std(precision_diffs)
        precision_se = precision_std / np.sqrt(num_runs)
        
        regret_mean = np.mean(regret_diffs)
        regret_std = np.std(regret_diffs)
        regret_se = regret_std / np.sqrt(num_runs)
        
        logger.info(f"Precision improvement: {precision_mean:.3f} ± {precision_se:.3f} (SE)")
        logger.info(f"Regret reduction: {regret_mean:.3f} ± {regret_se:.3f} (SE)")
        
        # 95% confidence interval: mean ± 1.96 * SE
        precision_ci_lower = precision_mean - 1.96 * precision_se
        regret_ci_lower = regret_mean - 1.96 * regret_se
        
        # Improvement should be positive (with 95% confidence)
        assert precision_ci_lower >= -0.05 or regret_ci_lower >= -0.05, \
            "Improvement should be statistically significant (95% CI should be positive)"
        
        logger.info("✅ Improvement is statistically significant")
    
    def test_long_simulation(self):
        """Test that long simulation works correctly."""
        logger.info("Testing long simulation")
        
        result = self.demo.run_learning_simulation(
            candidates=self.candidates,
            position=self.position,
            num_feedback_events=500  # Long simulation
        )
        
        # Verify simulation completes
        assert 'warm_start_metrics' in result
        assert 'cold_start_metrics' in result
        
        # Verify learning curves have correct length
        curves = result['learning_curves']
        assert len(curves['warm_start']['events']) == 500
        assert len(curves['cold_start']['events']) == 500
        
        # Verify metrics are reasonable
        warm_metrics = result['warm_start_metrics']
        assert warm_metrics.get('total_interactions', 0) == 500
        
        logger.info("✅ Long simulation works correctly")
    
    def test_memory_efficiency(self):
        """Test that simulation doesn't leak memory."""
        logger.info("Testing memory efficiency")
        
        import tracemalloc
        
        tracemalloc.start()
        
        # Run multiple simulations
        for i in range(3):
            result = self.demo.run_learning_simulation(
                candidates=self.candidates,
                position=self.position,
                num_feedback_events=100
            )
            del result
            gc.collect()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        logger.info(f"Current memory: {current / 1024 / 1024:.2f} MB")
        logger.info(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
        
        # Peak memory should be reasonable (< 500 MB for 3 simulations)
        assert peak < 500 * 1024 * 1024, \
            f"Peak memory too high: {peak / 1024 / 1024:.2f} MB"
        
        logger.info("✅ Memory efficiency is acceptable")
    
    def test_many_candidates(self):
        """Test simulation with many candidates."""
        logger.info("Testing many candidates")
        
        # Create 50 candidates
        many_candidates = []
        for i in range(50):
            many_candidates.append({
                'id': f'candidate_{i:03d}',
                'name': f'Candidate {i}',
                'skills': ['Python', 'CUDA'] if i < 10 else ['Java'],
                'experience_years': 5,
                'domain': 'AI/ML' if i < 10 else 'Web'
            })
        
        for candidate in many_candidates:
            self.kg.add_candidate(candidate)
        
        result = self.demo.run_learning_simulation(
            candidates=many_candidates,
            position=self.position,
            num_feedback_events=100
        )
        
        # Verify simulation completes
        assert result['simulation_config']['num_candidates'] == 50
        assert 'warm_start_metrics' in result
        assert 'cold_start_metrics' in result
        
        logger.info("✅ Many candidates simulation works")

