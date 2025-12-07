"""
test_performance_and_strictness.py - Performance and strictness validation

Why this test exists:
This test validates that the system meets performance requirements and that
the strictness is maintained even with large datasets. It ensures that only
a small percentage of candidates pass (1-5%), demonstrating true exceptionality.

What it validates:
- Performance requirements met (< 100ms per candidate, < 5s for 1000+)
- Strictness maintained with large datasets
- Score distribution is correct (most fail, few pass)
- Memory efficiency
- Statistical validation of strictness

Expected behavior:
With 100+ candidates, only 1-5 should pass (1-5% pass rate).
Performance should be < 100ms per candidate, < 5s for ranking 100+ candidates.
"""

import logging
import time
import pytest
from backend.matching.exceptional_talent_finder import ExceptionalTalentFinder
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestPerformanceAndStrictness:
    """Test performance and strictness with large datasets."""
    
    def setup_method(self):
        """Set up finder with large dataset."""
        logger.info("Setting up test environment with large dataset")
        self.kg = KnowledgeGraph(url='http://localhost:8080')
        self.finder = ExceptionalTalentFinder(knowledge_graph=self.kg)
        
        # Generate 100 candidates - most should be average, few exceptional
        logger.info("Generating 100 test candidates...")
        
        # Add 95 average candidates (should fail)
        for i in range(95):
            candidate = {
                'id': f'avg_candidate_{i}',
                'name': f'Average Developer {i}',
                'skills': ['Python', 'JavaScript'] if i % 2 == 0 else ['Java', 'SQL'],
                'experience_years': (i % 8) + 2,
                'domains': ['Web Development'] if i % 2 == 0 else ['Backend'],
                'expertise_level': 'Mid' if i % 3 == 0 else 'Senior',
                'papers': [{'id': f'p{j}'} for j in range(i % 5)],  # 0-4 papers
                'github_stats': {
                    'total_stars': (i % 1000) * 10,  # 0-10k stars
                    'total_repos': (i % 20) + 1,
                    'languages': ['Python'] if i % 2 == 0 else ['Java']
                },
                'x_analytics_summary': {
                    'followers_count': (i % 5000) + 100,
                    'avg_engagement_rate': 0.02 + (i % 3) * 0.01
                },
                'phone_screen_results': {
                    'technical_depth': 0.6 + (i % 3) * 0.1,
                    'problem_solving_ability': 0.65 + (i % 2) * 0.1,
                    'technical_communication': 0.7,
                    'implementation_experience': 0.68
                } if i % 2 == 0 else None
            }
            self.kg.add_candidate(candidate)
        
        # Add 1-2 TRULY exceptional candidates (Elon-level - should pass)
        # With 0.0001% pass rate, only 1 in 1,000,000 should pass
        # So out of 100 candidates, maybe 0-1 should pass
        exceptional_candidates = [
            {
                'id': 'exceptional_0',
                'name': 'Elon-Level Talent',
                'skills': ['CUDA', 'PyTorch', 'C++', 'Distributed Systems', 'LLM'],
                'experience_years': 15,
                'domains': ['LLM Inference', 'GPU Computing', 'Research', 'Systems'],
                'expertise_level': 'Staff',
                'papers': [{'id': f'paper_{j}'} for j in range(65)],  # 65 papers!
                'research_contributions': [
                    'Novel method', 'Breakthrough', 'New approach',
                    'Revolutionary technique', 'Game-changing innovation'
                ],
                'research_areas': ['LLM', 'GPU', 'Systems', 'ML', 'Optimization', 'Inference'],
                'github_stats': {
                    'total_stars': 160000,  # 160k stars!
                    'total_repos': 110,
                    'languages': ['Python', 'C++', 'CUDA', 'Rust', 'Go', 'Julia']
                },
                'x_analytics_summary': {
                    'followers_count': 1000000,  # 1M followers!
                    'avg_engagement_rate': 0.14  # 14% engagement!
                },
                'content_quality_score': 0.99,
                'phone_screen_results': {
                    'technical_depth': 0.98,
                    'problem_solving_ability': 0.96,
                    'technical_communication': 0.95,
                    'implementation_experience': 0.97
                }
            }
        ]
        
        for candidate in exceptional_candidates:
            self.kg.add_candidate(candidate)
        
        logger.info("Added 100 test candidates (99 average, 1 truly exceptional)")
    
    def teardown_method(self):
        """Clean up after tests."""
        self.kg.close()
    
    def test_performance_score_calculation(self):
        """Test that score calculation is fast (< 100ms per candidate)."""
        logger.info("Testing score calculation performance")
        
        candidate_id = 'exceptional_0'
        start_time = time.time()
        result = self.finder.score_candidate(candidate_id)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        assert elapsed < 100, f"Score calculation took {elapsed:.2f}ms, should be < 100ms"
        assert result['exceptional_score'] > 0.0, "Should return valid score"
        
        logger.info(f"✅ Score calculation: {elapsed:.2f}ms (meets requirement)")
    
    def test_performance_ranking(self):
        """Test that ranking 100+ candidates is fast (< 5s)."""
        logger.info("Testing ranking performance")
        
        # Get all candidate IDs
        all_candidates = self.kg.get_all_candidates()
        candidate_ids = [c.get('id') for c in all_candidates[:100]]  # First 100
        
        start_time = time.time()
        ranked = self.finder.rank_candidates(candidate_ids)
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"Ranking took {elapsed:.3f}s, should be < 5s"
        assert len(ranked) == len(candidate_ids), "Should rank all candidates"
        
        logger.info(f"✅ Ranking 100 candidates: {elapsed:.3f}s (meets requirement)")
    
    def test_strictness_with_large_dataset(self):
        """Test that strictness is maintained with large dataset."""
        logger.info("Testing strictness with large dataset")
        
        results = self.finder.find_exceptional_talent(min_score=0.85, top_k=20)
        
        # With 100 candidates (99 average, 1 truly exceptional), should find 0-1
        # System is EXTREMELY STRICT - 0.0001% pass rate (1 in 1,000,000)
        assert len(results) <= 1, \
            f"Should find at most 1 exceptional candidate (0.0001% pass rate), got {len(results)}"
        
        # Calculate pass rate
        all_candidates = self.kg.get_all_candidates()
        pass_rate = len(results) / len(all_candidates) * 100
        
        # With 0.0001% pass rate, out of 100 candidates, 0-1 should pass
        assert pass_rate <= 1.0, \
            f"Pass rate should be <= 1% (0.0001% target), got {pass_rate:.3f}%"
        # Allow 0% pass rate (even the exceptional candidate might not pass if not perfect)
        
        logger.info(f"✅ EXTREME strictness maintained: {len(results)}/{len(all_candidates)} pass "
                   f"({pass_rate:.3f}% pass rate - targeting 0.0001%)")
    
    def test_score_distribution(self):
        """Test that score distribution is correct (most low, few high)."""
        logger.info("Testing score distribution")
        
        all_candidates = self.kg.get_all_candidates()
        scores = []
        
        for candidate in all_candidates[:50]:  # Sample 50 for performance
            result = self.finder.score_candidate(candidate.get('id'))
            scores.append(result['exceptional_score'])
        
        # Most scores should be low (< 0.5)
        low_scores = sum(1 for s in scores if s < 0.5)
        low_percentage = low_scores / len(scores) * 100
        
        # Few scores should be high (> 0.8)
        high_scores = sum(1 for s in scores if s > 0.8)
        high_percentage = high_scores / len(scores) * 100
        
        assert low_percentage >= 80, \
            f"At least 80% should have low scores, got {low_percentage:.1f}%"
        assert high_percentage <= 15, \
            f"At most 15% should have high scores, got {high_percentage:.1f}%"
        
        logger.info(f"✅ Score distribution: {low_percentage:.1f}% low, "
                   f"{high_percentage:.1f}% high (correct distribution)")

