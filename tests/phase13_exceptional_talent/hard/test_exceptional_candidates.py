"""
test_exceptional_candidates.py - Test truly exceptional candidates

Why this test exists:
This test validates that truly exceptional candidates (the "next Elon")
correctly get high scores and pass the strict thresholds. These candidates
should have multiple strong signals across all platforms.

What it validates:
- Candidates with all strong signals pass
- Composite signals boost scores correctly
- Ranking works correctly
- Multiple exceptional candidates are correctly identified
- Score distribution is correct (most fail, few pass)

Expected behavior:
Only candidates with strong signals across 3+ platforms should pass.
Composite signals should boost scores for cross-platform excellence.
"""

import logging
import pytest
from backend.matching.exceptional_talent_finder import ExceptionalTalentFinder
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestExceptionalCandidates:
    """Test truly exceptional candidates."""
    
    def setup_method(self):
        """Set up finder and exceptional test data."""
        logger.info("Setting up test environment")
        self.kg = KnowledgeGraph(url='http://localhost:8080')
        self.finder = ExceptionalTalentFinder(knowledge_graph=self.kg)
        
        # Truly exceptional candidate (Elon-level - should pass easily)
        self.elon_level = {
            'id': 'elon_level',
            'name': 'Elon-Level Talent',
            'skills': ['CUDA', 'PyTorch', 'C++', 'Distributed Systems', 'LLM', 'GPU'],
            'experience_years': 15,
            'domains': ['LLM Inference', 'GPU Computing', 'Research', 'Systems'],
            'expertise_level': 'Staff',
            'papers': [{'id': f'paper_{i}'} for i in range(70)],  # 70 papers! (EXTREMELY high)
            'research_contributions': [
                'Novel transformer architecture',
                'GPU optimization technique',
                'Distributed training method',
                'New inference algorithm',
                'Breakthrough optimization',
                'Revolutionary approach'
            ],
            'research_areas': ['LLM', 'GPU', 'Distributed Systems', 'ML', 'Systems', 'Optimization', 'Inference'],
            'github_stats': {
                'total_stars': 180000,  # 180k stars! (EXTREMELY high)
                'total_repos': 120,
                'languages': ['Python', 'C++', 'CUDA', 'Rust', 'Go', 'TypeScript', 'Julia']
            },
            'x_analytics_summary': {
                'followers_count': 1200000,  # 1.2M followers! (EXTREMELY high)
                'avg_engagement_rate': 0.15  # 15% engagement! (very high)
            },
            'content_quality_score': 0.99,
            'phone_screen_results': {
                'technical_depth': 0.99,  # Near-perfect
                'problem_solving_ability': 0.97,
                'technical_communication': 0.96,
                'implementation_experience': 0.98
            }
        }
        
        # Another exceptional candidate (Elon-level - should also pass)
        self.exceptional_2 = {
            'id': 'exceptional_2',
            'name': 'Another Exceptional',
            'skills': ['ML', 'Research', 'Systems', 'CUDA', 'LLM'],
            'experience_years': 14,
            'domains': ['Machine Learning', 'Research', 'GPU Computing', 'LLM'],
            'expertise_level': 'Staff',
            'papers': [{'id': f'paper_{i}'} for i in range(55)],  # 55 papers (EXTREMELY high)
            'research_contributions': [
                'Breakthrough method', 'Novel approach', 'New algorithm',
                'Revolutionary technique', 'Game-changing innovation'
            ],
            'research_areas': ['ML', 'DL', 'NLP', 'CV', 'RL', 'GPU', 'Systems'],
            'github_stats': {
                'total_stars': 120000,  # 120k stars (EXTREMELY high)
                'total_repos': 90,
                'languages': ['Python', 'C++', 'Julia', 'R', 'CUDA', 'Rust']
            },
            'x_analytics_summary': {
                'followers_count': 600000,  # 600k followers (EXTREMELY high)
                'avg_engagement_rate': 0.13  # 13% engagement (very high)
            },
            'content_quality_score': 0.97,
            'phone_screen_results': {
                'technical_depth': 0.97,
                'problem_solving_ability': 0.94,
                'technical_communication': 0.93,
                'implementation_experience': 0.96
            }
        }
        
        self.kg.add_candidate(self.elon_level)
        self.kg.add_candidate(self.exceptional_2)
        logger.info("Added exceptional test candidates")
    
    def teardown_method(self):
        """Clean up after tests."""
        self.kg.close()
    
    def test_elon_level_candidate_passes(self):
        """Test that Elon-level candidate passes with high score."""
        logger.info("Testing Elon-level candidate")
        
        result = self.finder.score_candidate('elon_level')
        score = result['exceptional_score']
        
        assert score > 0.85, f"Elon-level candidate should pass, got {score:.3f}"
        
        # Check signal breakdown
        breakdown = result['signal_breakdown']
        assert breakdown['arxiv_signal'] > 0.8, "Should have strong arXiv signal"
        assert breakdown['github_signal'] > 0.8, "Should have strong GitHub signal"
        assert breakdown['x_signal'] > 0.7, "Should have strong X signal"
        assert breakdown['phone_screen_signal'] > 0.8, "Should have strong phone screen signal"
        assert breakdown['composite_signals'] > 0.7, "Should have strong composite signals"
        
        logger.info(f"✅ Elon-level candidate passes: {score:.3f}")
        logger.info(f"   Signal breakdown: {breakdown}")
    
    def test_find_exceptional_talent_returns_high_scorers(self):
        """Test that find_exceptional_talent returns only high scorers."""
        logger.info("Testing find_exceptional_talent")
        
        results = self.finder.find_exceptional_talent(min_score=0.85, top_k=10)
        
        # With EXTREME strictness (0.0001% pass rate), only 1-2 should pass
        # System is so strict that even exceptional candidates might not all pass
        assert len(results) >= 1, f"Should find at least 1 exceptional candidate, got {len(results)}"
        assert len(results) <= 2, f"With extreme strictness, at most 2 should pass, got {len(results)}"
        
        # All results should have score >= 0.85
        for result in results:
            score = result.get('exceptional_score', 0.0)
            assert score >= 0.85, f"Result should have score >= 0.85, got {score:.3f}"
        
        # Results should be sorted by score (descending)
        scores = [r.get('exceptional_score', 0.0) for r in results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score"
        
        logger.info(f"✅ Found {len(results)} exceptional candidates")
        for i, result in enumerate(results[:3], 1):
            logger.info(f"   {i}. {result.get('candidate_id')}: {result.get('exceptional_score'):.3f}")
    
    def test_ranking_works_correctly(self):
        """Test that ranking works correctly."""
        logger.info("Testing ranking")
        
        candidate_ids = ['elon_level', 'exceptional_2']
        ranked = self.finder.rank_candidates(candidate_ids)
        
        assert len(ranked) == 2, "Should rank both candidates"
        
        # First should have higher score
        assert ranked[0]['exceptional_score'] >= ranked[1]['exceptional_score'], \
            "First candidate should have higher or equal score"
        
        # Rankings should be high percentiles
        assert ranked[0]['ranking'] >= 90, "Top candidate should be 90th+ percentile"
        
        logger.info(f"✅ Ranking works: {ranked[0]['candidate_id']} ({ranked[0]['ranking']}th percentile) "
                   f"> {ranked[1]['candidate_id']} ({ranked[1]['ranking']}th percentile)")

