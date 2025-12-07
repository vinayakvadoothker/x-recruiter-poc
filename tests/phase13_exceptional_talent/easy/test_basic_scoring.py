"""
test_basic_scoring.py - Basic scoring functionality tests

Why this test exists:
This test validates that the exceptional talent scoring system works correctly
for basic cases. It ensures that scoring calculations are correct and that
the system correctly identifies exceptional vs non-exceptional candidates.

What it validates:
- Score calculation returns valid scores (0.0-1.0)
- Signal breakdown is complete
- Evidence is correctly extracted
- Non-exceptional candidates get low scores
- Exceptional candidates get high scores

Expected behavior:
Scoring should work correctly, with most candidates getting low scores (< 0.5)
and only truly exceptional candidates getting high scores (> 0.8).
"""

import logging
import pytest
from backend.matching.exceptional_talent_finder import ExceptionalTalentFinder
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestBasicScoring:
    """Test basic scoring functionality."""
    
    def setup_method(self):
        """Set up finder and test data."""
        logger.info("Setting up test environment")
        self.kg = KnowledgeGraph(url='http://localhost:8080')
        self.finder = ExceptionalTalentFinder(knowledge_graph=self.kg)
        
        # Add non-exceptional candidate (should get low score)
        self.average_candidate = {
            'id': 'average_candidate',
            'name': 'Average Developer',
            'skills': ['Python', 'JavaScript'],
            'experience_years': 3,
            'domains': ['Web Development'],
            'expertise_level': 'Mid',
            'papers': [],  # No research
            'github_stats': {'total_stars': 50, 'total_repos': 3},  # Low activity
            'x_analytics_summary': {'followers_count': 100},  # Low followers
            'phone_screen_results': None  # No phone screen
        }
        
        # Add TRULY exceptional candidate (Elon-level - should get high score)
        # Must meet ALL thresholds to pass (0.0001% pass rate)
        self.exceptional_candidate = {
            'id': 'exceptional_candidate',
            'name': 'Elon-Level Talent',
            'skills': ['CUDA', 'PyTorch', 'C++', 'Distributed Systems', 'LLM', 'GPU'],
            'experience_years': 18,
            'domains': ['LLM Inference', 'GPU Computing', 'Research', 'Systems'],
            'expertise_level': 'Staff',
            'papers': [{'id': f'paper_{i}'} for i in range(85)],  # 85 papers! (EXTREMELY high)
            'research_contributions': [
                'Novel architecture', 'Optimization technique', 'New algorithm', 
                'Breakthrough method', 'Revolutionary approach', 'Game-changing innovation',
                'Industry-changing discovery'
            ],
            'research_areas': ['LLM', 'GPU', 'Distributed Systems', 'ML', 'Systems', 'Optimization', 'Inference', 'Research'],
            'github_stats': {
                'total_stars': 180000,  # 180k stars! (EXTREMELY high)
                'total_repos': 150,
                'languages': ['Python', 'C++', 'CUDA', 'Rust', 'Go', 'TypeScript', 'Julia', 'C']
            },
            'x_analytics_summary': {
                'followers_count': 1500000,  # 1.5M followers! (EXTREMELY high)
                'avg_engagement_rate': 0.15  # 15% engagement (very high)
            },
            'content_quality_score': 0.99,
            'phone_screen_results': {
                'technical_depth': 0.99,  # Near-perfect
                'problem_solving_ability': 0.97,
                'technical_communication': 0.96,
                'implementation_experience': 0.98
            }
        }
        
        self.kg.add_candidate(self.average_candidate)
        self.kg.add_candidate(self.exceptional_candidate)
        logger.info("Added test candidates")
    
    def teardown_method(self):
        """Clean up after tests."""
        self.kg.close()
    
    def test_score_candidate_returns_valid_structure(self):
        """Test that score_candidate returns valid structure."""
        logger.info("Testing score_candidate structure")
        
        result = self.finder.score_candidate('average_candidate')
        
        assert 'exceptional_score' in result, "Should have exceptional_score"
        assert 'signal_breakdown' in result, "Should have signal_breakdown"
        assert 'evidence' in result, "Should have evidence"
        assert 'why_exceptional' in result, "Should have why_exceptional"
        
        assert 0.0 <= result['exceptional_score'] <= 1.0, "Score should be 0.0-1.0"
        
        logger.info("✅ Score structure is valid")
    
    def test_average_candidate_gets_low_score(self):
        """Test that average candidate gets low score (< 0.3)."""
        logger.info("Testing average candidate scoring")
        
        result = self.finder.score_candidate('average_candidate')
        score = result['exceptional_score']
        
        assert score < 0.3, f"Average candidate should get low score, got {score:.3f}"
        logger.info(f"✅ Average candidate score: {score:.3f} (correctly low)")
    
    def test_exceptional_candidate_gets_high_score(self):
        """Test that exceptional candidate gets high score (> 0.8)."""
        logger.info("Testing exceptional candidate scoring")
        
        result = self.finder.score_candidate('exceptional_candidate')
        score = result['exceptional_score']
        
        assert score > 0.8, f"Exceptional candidate should get high score, got {score:.3f}"
        logger.info(f"✅ Exceptional candidate score: {score:.3f} (correctly high)")
    
    def test_signal_breakdown_complete(self):
        """Test that signal breakdown includes all signals."""
        logger.info("Testing signal breakdown completeness")
        
        result = self.finder.score_candidate('exceptional_candidate')
        breakdown = result['signal_breakdown']
        
        assert 'arxiv_signal' in breakdown, "Should have arxiv_signal"
        assert 'github_signal' in breakdown, "Should have github_signal"
        assert 'x_signal' in breakdown, "Should have x_signal"
        assert 'phone_screen_signal' in breakdown, "Should have phone_screen_signal"
        assert 'composite_signals' in breakdown, "Should have composite_signals"
        
        # All signals should be 0.0-1.0
        for signal_name, signal_value in breakdown.items():
            assert 0.0 <= signal_value <= 1.0, f"{signal_name} should be 0.0-1.0, got {signal_value}"
        
        logger.info("✅ Signal breakdown is complete and valid")

