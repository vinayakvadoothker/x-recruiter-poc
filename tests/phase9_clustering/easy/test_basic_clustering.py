"""
test_basic_clustering.py - Easy tests for basic clustering functionality

Why this test exists:
This test verifies that the clustering system can group candidates by ability
and assign meaningful cluster names. This is the foundation - without working
clustering, the entire cluster-aware matching system fails. We need to ensure
the clusterer correctly groups candidates and assigns valid cluster names.

What it validates:
- cluster_candidates() assigns clusters to all candidates
- Cluster names are meaningful (e.g., "CUDA Experts", not "Cluster 1")
- All candidates get assigned to a cluster
- Cluster statistics are computed correctly
- ability_cluster field is updated in knowledge graph

Expected behavior:
- Candidates with similar skills cluster together
- Cluster names reflect dominant skills/domains
- All candidates are assigned to exactly one cluster
- Cluster statistics show size, dominant skills, etc.
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


class TestBasicClustering:
    """Test basic clustering functionality."""
    
    def setup_method(self):
        """Set up clusterer and test data."""
        logger.info("Setting up clustering test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.clusterer = TalentClusterer(
            knowledge_graph=self.kg,
            min_clusters=3,
            max_clusters=5
        )
        
        # Create diverse candidates for clustering
        self.candidates = [
            {
                'id': 'cuda_expert_1',
                'skills': ['CUDA', 'C++', 'PyTorch', 'GPU Optimization'],
                'domains': ['LLM Inference', 'GPU Computing'],
                'experience_years': 6
            },
            {
                'id': 'cuda_expert_2',
                'skills': ['CUDA', 'C++', 'TensorRT', 'GPU Computing'],
                'domains': ['GPU Computing', 'LLM Inference'],
                'experience_years': 7
            },
            {
                'id': 'web_dev_1',
                'skills': ['React', 'Node.js', 'TypeScript', 'JavaScript'],
                'domains': ['Web Development'],
                'experience_years': 4
            },
            {
                'id': 'web_dev_2',
                'skills': ['React', 'Node.js', 'Express', 'MongoDB'],
                'domains': ['Web Development', 'Fullstack'],
                'experience_years': 5
            },
            {
                'id': 'ml_engineer_1',
                'skills': ['PyTorch', 'TensorFlow', 'Python', 'ML'],
                'domains': ['Machine Learning', 'Deep Learning'],
                'experience_years': 5
            },
            {
                'id': 'ml_engineer_2',
                'skills': ['PyTorch', 'Scikit-learn', 'Python', 'NLP'],
                'domains': ['Machine Learning', 'NLP'],
                'experience_years': 6
            }
        ]
        
        logger.info("Adding test candidates to knowledge graph...")
        for candidate in self.candidates:
            self.kg.add_candidate(candidate)
        logger.info("Test candidates added")
    
    def teardown_method(self):
        """Clean up after each test."""
        self.clusterer.close()
    
    def test_cluster_candidates(self):
        """Test that clustering assigns clusters to all candidates."""
        logger.info("Testing candidate clustering")
        
        result = self.clusterer.cluster_candidates()
        
        logger.info(f"Clustering result: {result}")
        
        assert 'error' not in result, f"Clustering failed: {result.get('error')}"
        assert 'cluster_assignments' in result, "Result should include cluster_assignments"
        assert 'cluster_statistics' in result, "Result should include cluster_statistics"
        assert 'optimal_k' in result, "Result should include optimal_k"
        
        cluster_assignments = result['cluster_assignments']
        assert len(cluster_assignments) == len(self.candidates), \
            f"All candidates should be assigned, got {len(cluster_assignments)}/{len(self.candidates)}"
        
        logger.info(f"✅ Assigned {len(cluster_assignments)} candidates to {result['optimal_k']} clusters")
    
    def test_cluster_names_are_meaningful(self):
        """Test that cluster names are meaningful (not generic)."""
        logger.info("Testing cluster name quality")
        
        result = self.clusterer.cluster_candidates()
        
        cluster_statistics = result['cluster_statistics']
        logger.info(f"Cluster statistics: {cluster_statistics}")
        
        # Check that cluster names are meaningful
        for cluster_name in cluster_statistics.keys():
            logger.info(f"Cluster name: {cluster_name}")
            
            # Should not be generic names
            assert cluster_name != "Cluster 1", \
                f"Cluster name should not be generic: {cluster_name}"
            assert cluster_name != "Cluster 0", \
                f"Cluster name should not be generic: {cluster_name}"
            assert "Cluster" not in cluster_name or "Experts" in cluster_name or "Engineers" in cluster_name or "Developers" in cluster_name, \
                f"Cluster name should be meaningful: {cluster_name}"
            
            # Should contain relevant keywords
            assert len(cluster_name) > 5, \
                f"Cluster name should be descriptive: {cluster_name}"
        
        logger.info("✅ All cluster names are meaningful")
    
    def test_all_candidates_assigned(self):
        """Test that all candidates are assigned to exactly one cluster."""
        logger.info("Testing complete candidate assignment")
        
        result = self.clusterer.cluster_candidates()
        
        cluster_assignments = result['cluster_assignments']
        
        # Verify all candidates are assigned
        for candidate in self.candidates:
            candidate_id = candidate['id']
            assert candidate_id in cluster_assignments, \
                f"Candidate {candidate_id} not assigned to cluster"
            
            cluster_name = cluster_assignments[candidate_id]
            assert cluster_name is not None, \
                f"Candidate {candidate_id} has None cluster"
            assert len(cluster_name) > 0, \
                f"Candidate {candidate_id} has empty cluster name"
        
        logger.info("✅ All candidates assigned to clusters")
    
    def test_cluster_statistics(self):
        """Test that cluster statistics are computed correctly."""
        logger.info("Testing cluster statistics")
        
        result = self.clusterer.cluster_candidates()
        
        cluster_statistics = result['cluster_statistics']
        
        assert len(cluster_statistics) > 0, "Should have cluster statistics"
        
        for cluster_name, stats in cluster_statistics.items():
            logger.info(f"Cluster {cluster_name}: {stats}")
            
            assert 'size' in stats, f"Stats missing 'size' for {cluster_name}"
            assert stats['size'] > 0, f"Cluster {cluster_name} should have candidates"
            assert 'dominant_skills' in stats, f"Stats missing 'dominant_skills' for {cluster_name}"
            assert isinstance(stats['dominant_skills'], list), \
                f"dominant_skills should be list for {cluster_name}"
        
        logger.info("✅ Cluster statistics are complete and valid")
    
    def test_ability_cluster_updated_in_kg(self):
        """Test that ability_cluster field is updated in knowledge graph."""
        logger.info("Testing knowledge graph updates")
        
        result = self.clusterer.cluster_candidates()
        
        cluster_assignments = result['cluster_assignments']
        
        # Verify candidates in KG have ability_cluster
        for candidate_id, cluster_name in cluster_assignments.items():
            candidate = self.kg.get_candidate(candidate_id)
            assert candidate is not None, f"Candidate {candidate_id} not found in KG"
            assert 'ability_cluster' in candidate, \
                f"Candidate {candidate_id} missing ability_cluster field"
            assert candidate['ability_cluster'] == cluster_name, \
                f"Candidate {candidate_id} cluster mismatch: {candidate['ability_cluster']} != {cluster_name}"
        
        logger.info("✅ All candidates have ability_cluster updated in knowledge graph")

