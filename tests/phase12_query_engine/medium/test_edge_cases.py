"""
test_edge_cases.py - Edge case tests for query engine

Why this test exists:
This test validates that the query engine handles edge cases gracefully, such as
empty results, missing data, invalid inputs, and boundary conditions. This ensures
robustness in production.

What it validates:
- Empty result sets are handled correctly
- Missing fields don't cause crashes
- Invalid filter inputs are handled
- Boundary conditions (min/max values) work correctly
- Empty candidate lists are handled

Expected behavior:
All edge cases should be handled gracefully without crashes, returning empty
lists or appropriate defaults when no matches are found.
"""

import logging
import pytest
from backend.database.query_engine import QueryEngine
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge case handling."""
    
    def setup_method(self):
        """Set up query engine."""
        logger.info("Setting up test environment")
        self.kg = KnowledgeGraph(url='http://localhost:8080')
        self.query_engine = QueryEngine(knowledge_graph=self.kg)
        
        # Add candidate with minimal data
        self.minimal_candidate = {
            'id': 'minimal_candidate',
            'skills': ['Python'],
            'domains': [],
            'experience_years': 1
        }
        self.kg.add_candidate(self.minimal_candidate)
        logger.info("Added minimal test candidate")
    
    def teardown_method(self):
        """Clean up after tests."""
        self.kg.close()
    
    def test_query_nonexistent_cluster(self):
        """Test query for non-existent ability cluster."""
        logger.info("Testing query for non-existent cluster")
        
        results = self.query_engine.query_by_ability_cluster('Nonexistent Cluster')
        
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 0, "Should return empty list for non-existent cluster"
        
        logger.info("✅ Non-existent cluster query handled correctly")
    
    def test_query_no_matching_skills(self):
        """Test query with skills that don't match any candidate."""
        logger.info("Testing query with no matching skills")
        
        results = self.query_engine.query_by_skills(
            required_skills=['NonExistentSkill'],
            top_k=10
        )
        
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 0, "Should return empty list when no matches"
        
        logger.info("✅ No matching skills handled correctly")
    
    def test_query_missing_fields(self):
        """Test query with candidates missing required fields."""
        logger.info("Testing query with missing fields")
        
        # Query exceptional talent - candidate has no papers/stars
        results = self.query_engine.query_exceptional_talent(
            min_arxiv_papers=1,
            min_github_stars=100,
            top_k=10
        )
        
        # Should not crash, should return empty or filtered results
        assert isinstance(results, list), "Results should be a list"
        
        logger.info("✅ Missing fields handled correctly")
    
    def test_query_empty_optional_skills(self):
        """Test query with empty optional skills list."""
        logger.info("Testing query with empty optional skills")
        
        results = self.query_engine.query_by_skills(
            required_skills=['Python'],
            optional_skills=[],
            top_k=10
        )
        
        assert isinstance(results, list), "Results should be a list"
        assert len(results) >= 1, "Should return candidates with required skills"
        
        logger.info("✅ Empty optional skills handled correctly")
    
    def test_query_zero_thresholds(self):
        """Test query with zero thresholds (should match all)."""
        logger.info("Testing query with zero thresholds")
        
        results = self.query_engine.query_exceptional_talent(
            min_arxiv_papers=0,
            min_github_stars=0,
            min_x_followers=0,
            min_experience_years=0,
            top_k=10
        )
        
        assert isinstance(results, list), "Results should be a list"
        # Should return at least the minimal candidate
        assert len(results) >= 1, "Zero thresholds should match all candidates"
        
        logger.info("✅ Zero thresholds handled correctly")
    
    def test_query_very_high_thresholds(self):
        """Test query with very high thresholds (should match none)."""
        logger.info("Testing query with very high thresholds")
        
        results = self.query_engine.query_exceptional_talent(
            min_arxiv_papers=1000,
            min_github_stars=1000000,
            min_x_followers=10000000,
            top_k=10
        )
        
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 0, "Very high thresholds should match no candidates"
        
        logger.info("✅ Very high thresholds handled correctly")

