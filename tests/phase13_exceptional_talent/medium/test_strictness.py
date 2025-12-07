"""
test_strictness.py - Test strictness of scoring thresholds

Why this test exists:
This test validates that the scoring system is VERY STRICT - most candidates
should fail, only truly exceptional ones should pass. This ensures the system
correctly identifies only the top 1-5% of candidates.

What it validates:
- Candidates with only one strong signal don't pass
- Candidates need multiple strong signals to pass
- Thresholds are strict enough (most candidates fail)
- Missing data results in low scores
- Partial signals don't accumulate enough

Expected behavior:
Most candidates should get scores < 0.5. Only candidates with multiple
strong signals across platforms should get scores > 0.8.
"""

import logging
import pytest
from backend.matching.exceptional_talent_finder import ExceptionalTalentFinder
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestStrictness:
    """Test strictness of scoring thresholds."""
    
    def setup_method(self):
        """Set up finder and test data."""
        logger.info("Setting up test environment")
        self.kg = KnowledgeGraph(url='http://localhost:8080')
        self.finder = ExceptionalTalentFinder(knowledge_graph=self.kg)
        
        # Candidate with only GitHub (should NOT pass - need multiple signals)
        self.github_only = {
            'id': 'github_only',
            'name': 'GitHub Star',
            'skills': ['Python'],
            'experience_years': 5,
            'domains': ['Web Development'],
            'expertise_level': 'Senior',
            'papers': [],  # No research
            'github_stats': {
                'total_stars': 30000,  # High stars
                'total_repos': 60,
                'languages': ['Python', 'JavaScript', 'TypeScript']
            },
            'x_analytics_summary': {'followers_count': 500},  # Low followers
            'phone_screen_results': None  # No phone screen
        }
        
        # Candidate with only arXiv (should NOT pass)
        self.arxiv_only = {
            'id': 'arxiv_only',
            'name': 'Researcher',
            'skills': ['ML', 'Research'],
            'experience_years': 8,
            'domains': ['Machine Learning'],
            'expertise_level': 'Senior',
            'papers': [{'id': f'paper_{i}'} for i in range(20)],  # Many papers
            'research_contributions': ['Novel method', 'New approach'],
            'research_areas': ['ML', 'DL', 'NLP'],
            'github_stats': {'total_stars': 100, 'total_repos': 2},  # Low activity
            'x_analytics_summary': {'followers_count': 200},  # Low followers
            'phone_screen_results': None
        }
        
        # Candidate with partial signals (should NOT pass - need ALL strong)
        self.partial_signals = {
            'id': 'partial_signals',
            'name': 'Partial Talent',
            'skills': ['Python', 'ML'],
            'experience_years': 6,
            'domains': ['ML'],
            'expertise_level': 'Senior',
            'papers': [{'id': f'paper_{i}'} for i in range(12)],  # Some papers
            'github_stats': {
                'total_stars': 8000,  # Good but not exceptional
                'total_repos': 20,
                'languages': ['Python', 'R']
            },
            'x_analytics_summary': {
                'followers_count': 15000,  # Good but not exceptional
                'avg_engagement_rate': 0.04
            },
            'phone_screen_results': {
                'technical_depth': 0.82,  # Good but not exceptional
                'problem_solving_ability': 0.75,
                'technical_communication': 0.78,
                'implementation_experience': 0.80
            }
        }
        
        self.kg.add_candidate(self.github_only)
        self.kg.add_candidate(self.arxiv_only)
        self.kg.add_candidate(self.partial_signals)
        logger.info("Added test candidates for strictness testing")
    
    def teardown_method(self):
        """Clean up after tests."""
        self.kg.close()
    
    def test_single_signal_not_enough(self):
        """Test that single strong signal is not enough to pass."""
        logger.info("Testing single signal candidates")
        
        github_result = self.finder.score_candidate('github_only')
        arxiv_result = self.finder.score_candidate('arxiv_only')
        
        # Even with one strong signal, should NOT pass (need multiple)
        assert github_result['exceptional_score'] < 0.7, \
            f"GitHub-only candidate should not pass, got {github_result['exceptional_score']:.3f}"
        assert arxiv_result['exceptional_score'] < 0.7, \
            f"arXiv-only candidate should not pass, got {arxiv_result['exceptional_score']:.3f}"
        
        logger.info(f"✅ Single signal candidates correctly fail: "
                   f"GitHub={github_result['exceptional_score']:.3f}, "
                   f"arXiv={arxiv_result['exceptional_score']:.3f}")
    
    def test_partial_signals_not_enough(self):
        """Test that partial signals across platforms are not enough."""
        logger.info("Testing partial signals candidate")
        
        result = self.finder.score_candidate('partial_signals')
        score = result['exceptional_score']
        
        # Partial signals should NOT be enough - need STRONG signals
        assert score < 0.75, \
            f"Partial signals candidate should not pass, got {score:.3f}"
        
        logger.info(f"✅ Partial signals candidate correctly fails: {score:.3f}")
    
    def test_missing_data_results_in_low_score(self):
        """Test that missing data results in low scores."""
        logger.info("Testing missing data handling")
        
        # Candidate with no data
        no_data_candidate = {
            'id': 'no_data',
            'name': 'No Data',
            'skills': ['Python'],
            'experience_years': 2,
            'domains': ['Web'],
            'expertise_level': 'Junior',
            'papers': [],
            'github_stats': {},
            'x_analytics_summary': {}
        }
        self.kg.add_candidate(no_data_candidate)
        
        result = self.finder.score_candidate('no_data')
        score = result['exceptional_score']
        
        assert score < 0.2, f"Missing data should result in very low score, got {score:.3f}"
        
        logger.info(f"✅ Missing data correctly results in low score: {score:.3f}")

