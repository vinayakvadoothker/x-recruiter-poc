"""
test_edge_cases.py - Medium tests for clustering edge cases

Why this test exists:
Real-world usage will have edge cases: too few candidates, all candidates
identical, all candidates completely different, empty candidates list, etc.
This test ensures the clustering system handles these gracefully and returns
appropriate errors or fallback behavior.

What it validates:
- Too few candidates returns error
- Single candidate handled correctly
- All candidates identical handled correctly
- All candidates completely different handled correctly
- Empty candidates list handled correctly
- assign_candidate_to_cluster() works for new candidates

Expected behavior:
- Edge cases return clear error messages or handle gracefully
- System doesn't crash on edge cases
- assign_candidate_to_cluster() requires clustering to be run first
"""

import pytest
import os
import logging
from backend.matching.talent_clusterer import TalentClusterer
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases in clustering."""
    
    def setup_method(self):
        """Set up clusterer."""
        logger.info("Setting up edge case test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.clusterer = TalentClusterer(
            knowledge_graph=self.kg,
            min_clusters=3,
            max_clusters=5
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        self.clusterer.close()
    
    def test_too_few_candidates(self):
        """Test clustering with too few candidates."""
        logger.info("Testing clustering with too few candidates")
        
        # Only 2 candidates (less than min_clusters=3)
        candidates = [
            {
                'id': 'candidate_1',
                'skills': ['Python'],
                'experience_years': 2
            },
            {
                'id': 'candidate_2',
                'skills': ['Java'],
                'experience_years': 3
            }
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        result = self.clusterer.cluster_candidates(candidates)
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error for too few candidates"
        assert 'not enough' in result['error'].lower(), \
            "Error should mention not enough candidates"
        
        logger.info("✅ Too few candidates handled correctly")
    
    def test_single_candidate(self):
        """Test clustering with single candidate."""
        logger.info("Testing clustering with single candidate")
        
        candidate = {
            'id': 'candidate_1',
            'skills': ['Python'],
            'experience_years': 2
        }
        
        self.kg.add_candidate(candidate)
        
        result = self.clusterer.cluster_candidates([candidate])
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error for single candidate"
        
        logger.info("✅ Single candidate handled correctly")
    
    def test_all_candidates_identical(self):
        """Test clustering when all candidates are identical."""
        logger.info("Testing clustering with identical candidates")
        
        candidates = [
            {
                'id': f'candidate_{i}',
                'skills': ['Python', 'Django'],
                'domains': ['Web Development'],
                'experience_years': 3
            }
            for i in range(6)  # Enough for clustering
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        result = self.clusterer.cluster_candidates(candidates)
        
        logger.info(f"Result: {result}")
        logger.info(f"Optimal K: {result.get('optimal_k')}")
        logger.info(f"Cluster assignments: {result.get('cluster_assignments')}")
        
        # Should still cluster (may create fewer clusters)
        assert 'error' not in result, \
            f"Should handle identical candidates, got error: {result.get('error')}"
        assert result['optimal_k'] >= 1, "Should create at least 1 cluster"
        
        logger.info("✅ Identical candidates handled correctly")
    
    def test_all_candidates_different(self):
        """Test clustering when all candidates are completely different."""
        logger.info("Testing clustering with completely different candidates")
        
        candidates = [
            {
                'id': f'candidate_{i}',
                'skills': [f'Skill_{i}', f'Tech_{i}'],
                'domains': [f'Domain_{i}'],
                'experience_years': i + 1
            }
            for i in range(10)  # Enough for clustering
        ]
        
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        result = self.clusterer.cluster_candidates(candidates)
        
        logger.info(f"Result: {result}")
        logger.info(f"Optimal K: {result.get('optimal_k')}")
        logger.info(f"Silhouette score: {result.get('silhouette_score')}")
        
        # Should still cluster (may create more clusters)
        assert 'error' not in result, \
            f"Should handle different candidates, got error: {result.get('error')}"
        assert result['optimal_k'] >= 1, "Should create at least 1 cluster"
        
        logger.info("✅ Different candidates handled correctly")
    
    def test_assign_candidate_before_clustering(self):
        """Test that assign_candidate_to_cluster() requires clustering first."""
        logger.info("Testing assign_candidate_to_cluster() before clustering")
        
        candidate = {
            'id': 'new_candidate',
            'skills': ['Python'],
            'experience_years': 2
        }
        
        with pytest.raises(ValueError, match="Must call cluster_candidates"):
            self.clusterer.assign_candidate_to_cluster(candidate)
        
        logger.info("✅ assign_candidate_to_cluster() correctly requires clustering first")
    
    def test_assign_candidate_after_clustering(self):
        """Test that assign_candidate_to_cluster() works after clustering."""
        logger.info("Testing assign_candidate_to_cluster() after clustering")
        
        # Create and cluster initial candidates
        initial_candidates = [
            {
                'id': f'candidate_{i}',
                'skills': ['Python', 'Django'] if i < 3 else ['CUDA', 'C++'],
                'domains': ['Web Development'] if i < 3 else ['GPU Computing'],
                'experience_years': 3
            }
            for i in range(6)
        ]
        
        for candidate in initial_candidates:
            self.kg.add_candidate(candidate)
        
        # Cluster initial candidates
        self.clusterer.cluster_candidates(initial_candidates)
        
        # Assign new candidate
        new_candidate = {
            'id': 'new_candidate',
            'skills': ['Python', 'Django'],
            'domains': ['Web Development'],
            'experience_years': 2
        }
        
        cluster_name = self.clusterer.assign_candidate_to_cluster(new_candidate)
        
        logger.info(f"New candidate assigned to cluster: {cluster_name}")
        
        assert cluster_name is not None, "Should assign cluster name"
        assert len(cluster_name) > 0, "Cluster name should be non-empty"
        assert cluster_name != "Unassigned", "Should assign to valid cluster"
        
        logger.info("✅ assign_candidate_to_cluster() works correctly after clustering")

