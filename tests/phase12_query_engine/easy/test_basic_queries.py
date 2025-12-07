"""
test_basic_queries.py - Basic query functionality tests

Why this test exists:
This test validates that the core query methods work correctly for simple use cases.
It ensures that ability cluster queries, skill-based queries, and multi-criteria
queries return expected results.

What it validates:
- Ability cluster queries return candidates with matching cluster
- Skill-based queries with required skills work
- Multi-criteria queries filter correctly
- Query methods don't crash on valid inputs

Expected behavior:
All query methods should return lists of candidates matching the criteria,
with correct filtering applied.
"""

import logging
import pytest
from backend.database.query_engine import QueryEngine
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestBasicQueries:
    """Test basic query functionality."""
    
    def setup_method(self):
        """Set up query engine and test data."""
        logger.info("Setting up test environment")
        self.kg = KnowledgeGraph(url='http://localhost:8080')
        self.query_engine = QueryEngine(knowledge_graph=self.kg)
        
        # Add test candidates
        self.candidate1 = {
            'id': 'test_candidate_1',
            'skills': ['CUDA', 'PyTorch', 'C++'],
            'domains': ['LLM Inference'],
            'experience_years': 5,
            'ability_cluster': 'CUDA/GPU Experts',
            'papers': [{'id': 'paper1'}, {'id': 'paper2'}],
            'github_stats': {'total_stars': 1000},
            'x_analytics_summary': {'followers_count': 5000}
        }
        
        self.candidate2 = {
            'id': 'test_candidate_2',
            'skills': ['React', 'TypeScript', 'Node.js'],
            'domains': ['Frontend'],
            'experience_years': 3,
            'ability_cluster': 'Fullstack Developers',
            'papers': [],
            'github_stats': {'total_stars': 500},
            'x_analytics_summary': {'followers_count': 1000}
        }
        
        self.candidate3 = {
            'id': 'test_candidate_3',
            'skills': ['CUDA', 'TensorRT', 'PyTorch'],
            'domains': ['LLM Inference', 'GPU Computing'],
            'experience_years': 7,
            'ability_cluster': 'CUDA/GPU Experts',
            'papers': [{'id': 'paper3'}, {'id': 'paper4'}, {'id': 'paper5'}],
            'github_stats': {'total_stars': 2000},
            'x_analytics_summary': {'followers_count': 8000}
        }
        
        # Add to knowledge graph
        self.kg.add_candidate(self.candidate1)
        self.kg.add_candidate(self.candidate2)
        self.kg.add_candidate(self.candidate3)
        logger.info("Added 3 test candidates")
    
    def teardown_method(self):
        """Clean up after tests."""
        self.kg.close()
    
    def test_query_by_ability_cluster(self):
        """Test ability cluster query returns correct candidates."""
        logger.info("Testing ability cluster query")
        
        results = self.query_engine.query_by_ability_cluster('CUDA/GPU Experts')
        
        assert len(results) == 2, f"Expected 2 candidates, got {len(results)}"
        candidate_ids = {c['id'] for c in results}
        assert 'test_candidate_1' in candidate_ids
        assert 'test_candidate_3' in candidate_ids
        assert 'test_candidate_2' not in candidate_ids
        
        logger.info("✅ Ability cluster query works correctly")
    
    def test_query_by_skills_required(self):
        """Test skill-based query with required skills."""
        logger.info("Testing skill-based query with required skills")
        
        results = self.query_engine.query_by_skills(
            required_skills=['CUDA'],
            top_k=10
        )
        
        assert len(results) == 2, f"Expected 2 candidates, got {len(results)}"
        candidate_ids = {c['id'] for c in results}
        assert 'test_candidate_1' in candidate_ids
        assert 'test_candidate_3' in candidate_ids
        
        logger.info("✅ Skill-based query with required skills works")
    
    def test_query_by_skills_excluded(self):
        """Test skill-based query with excluded skills."""
        logger.info("Testing skill-based query with excluded skills")
        
        results = self.query_engine.query_by_skills(
            required_skills=['CUDA'],
            excluded_skills=['React'],
            top_k=10
        )
        
        assert len(results) == 2, f"Expected 2 candidates, got {len(results)}"
        candidate_ids = {c['id'] for c in results}
        assert 'test_candidate_1' in candidate_ids
        assert 'test_candidate_3' in candidate_ids
        assert 'test_candidate_2' not in candidate_ids
        
        logger.info("✅ Skill-based query with excluded skills works")
    
    def test_query_exceptional_talent(self):
        """Test multi-criteria exceptional talent query."""
        logger.info("Testing exceptional talent query")
        
        results = self.query_engine.query_exceptional_talent(
            min_arxiv_papers=2,
            min_github_stars=1000,
            min_x_followers=4000,
            top_k=10
        )
        
        assert len(results) >= 1, f"Expected at least 1 candidate, got {len(results)}"
        candidate_ids = {c['id'] for c in results}
        assert 'test_candidate_1' in candidate_ids or 'test_candidate_3' in candidate_ids
        
        logger.info("✅ Exceptional talent query works correctly")

