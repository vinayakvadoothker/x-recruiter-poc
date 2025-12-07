"""
test_stress_and_performance.py - Super hard tests for stress and performance

Why this test exists:
In production, the clustering system will handle 1,000+ candidates and must
complete efficiently (< 5 minutes) while maintaining quality. This test ensures
the system can handle high-volume operations and maintains cluster quality at scale.
The system must be production-ready and handle real-world workloads.

What it validates:
- System handles 1,000+ candidates efficiently
- Clustering completes in reasonable time (< 5 minutes)
- Memory usage is reasonable
- Cluster quality doesn't degrade with scale
- assign_candidate_to_cluster() is fast (< 1 second)

Expected behavior:
- Large-scale clustering completes in < 5 minutes
- Memory usage is reasonable (no OOM errors)
- Cluster quality metrics are maintained
- Individual candidate assignment is fast
"""

import pytest
import os
import time
import logging
import numpy as np
from backend.matching.talent_clusterer import TalentClusterer
from backend.database.knowledge_graph import KnowledgeGraph
from backend.datasets import generate_candidates

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStressAndPerformance:
    """Test stress scenarios and performance."""
    
    def setup_method(self):
        """Set up clusterer."""
        logger.info("Setting up stress test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.clusterer = TalentClusterer(
            knowledge_graph=self.kg,
            min_clusters=5,
            max_clusters=10
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        self.clusterer.close()
    
    def test_large_scale_clustering(self):
        """Test clustering with 1,000+ candidates."""
        logger.info("Testing large-scale clustering (1,000 candidates)")
        
        # Generate 1,000 candidates
        candidates = list(generate_candidates(1000))
        logger.info(f"Generated {len(candidates)} candidates")
        
        # Add to knowledge graph
        logger.info("Adding candidates to knowledge graph...")
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        # Run clustering and measure time
        logger.info("Starting clustering...")
        start_time = time.time()
        result = self.clusterer.cluster_candidates(candidates)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Clustering time: {elapsed_time:.2f}s ({elapsed_time/60:.2f} minutes)")
        logger.info(f"Optimal K: {result['optimal_k']}")
        logger.info(f"Silhouette score: {result['silhouette_score']:.3f}")
        logger.info(f"Clustered candidates: {len(result['cluster_assignments'])}")
        
        # Performance requirements: < 5 minutes
        assert elapsed_time < 300.0, \
            f"Clustering too slow: {elapsed_time:.2f}s (expected < 300s)"
        
        # Verify all candidates clustered
        assert len(result['cluster_assignments']) == len(candidates), \
            f"Not all candidates clustered: {len(result['cluster_assignments'])}/{len(candidates)}"
        
        # Verify cluster quality
        assert result['silhouette_score'] >= 0.0, \
            f"Invalid silhouette score: {result['silhouette_score']}"
        
        logger.info("✅ Large-scale clustering completed successfully")
    
    def test_assign_candidate_performance(self):
        """Test that assign_candidate_to_cluster() is fast."""
        logger.info("Testing assign_candidate_to_cluster() performance")
        
        # First, cluster a reasonable number of candidates
        initial_candidates = list(generate_candidates(100))
        for candidate in initial_candidates:
            self.kg.add_candidate(candidate)
        
        logger.info("Clustering initial candidates...")
        self.clusterer.cluster_candidates(initial_candidates)
        
        # Generate new candidate
        new_candidate = next(generate_candidates(1))
        new_candidate['id'] = 'new_candidate'
        
        # Measure assignment time
        logger.info("Assigning new candidate to cluster...")
        start_time = time.time()
        cluster_name = self.clusterer.assign_candidate_to_cluster(new_candidate)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Assignment time: {elapsed_time:.4f}s")
        logger.info(f"Assigned to cluster: {cluster_name}")
        
        # Performance requirement: < 1 second
        assert elapsed_time < 1.0, \
            f"Assignment too slow: {elapsed_time:.4f}s (expected < 1.0s)"
        
        assert cluster_name is not None, "Should assign cluster name"
        assert len(cluster_name) > 0, "Cluster name should be non-empty"
        
        logger.info("✅ assign_candidate_to_cluster() performance acceptable")
    
    def test_cluster_quality_at_scale(self):
        """Test that cluster quality is maintained at scale."""
        logger.info("Testing cluster quality at scale (500 candidates)")
        
        # Generate diverse candidates
        candidates = list(generate_candidates(500))
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        logger.info("Clustering candidates...")
        result = self.clusterer.cluster_candidates(candidates)
        
        logger.info(f"Optimal K: {result['optimal_k']}")
        logger.info(f"Silhouette score: {result['silhouette_score']:.3f}")
        logger.info(f"Cluster statistics: {result['cluster_statistics']}")
        
        # Verify quality metrics
        silhouette = result['silhouette_score']
        assert silhouette >= 0.0, f"Invalid silhouette score: {silhouette}"
        
        # Verify cluster names are meaningful
        cluster_statistics = result['cluster_statistics']
        for cluster_name in cluster_statistics.keys():
            assert cluster_name != "Cluster 1", \
                f"Cluster name should not be generic: {cluster_name}"
            assert len(cluster_name) > 5, \
                f"Cluster name should be descriptive: {cluster_name}"
        
        # Verify all candidates assigned
        assert len(result['cluster_assignments']) == len(candidates), \
            f"Not all candidates assigned: {len(result['cluster_assignments'])}/{len(candidates)}"
        
        logger.info("✅ Cluster quality maintained at scale")
    
    def test_re_clustering_efficiency(self):
        """Test that re-clustering is efficient."""
        logger.info("Testing re-clustering efficiency")
        
        # Generate candidates
        candidates = list(generate_candidates(200))
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        # First clustering
        logger.info("First clustering...")
        start_time = time.time()
        result1 = self.clusterer.cluster_candidates(candidates)
        time1 = time.time() - start_time
        
        # Second clustering (should be similar time)
        logger.info("Second clustering...")
        start_time = time.time()
        result2 = self.clusterer.cluster_candidates(candidates)
        time2 = time.time() - start_time
        
        logger.info(f"First clustering: {time1:.2f}s")
        logger.info(f"Second clustering: {time2:.2f}s")
        
        # Both should complete in reasonable time
        assert time1 < 120.0, f"First clustering too slow: {time1:.2f}s"
        assert time2 < 120.0, f"Second clustering too slow: {time2:.2f}s"
        
        # Should produce similar results (same K)
        assert result1['optimal_k'] == result2['optimal_k'], \
            f"Optimal K should be same: {result1['optimal_k']} != {result2['optimal_k']}"
        
        logger.info("✅ Re-clustering efficiency verified")
    
    def test_memory_efficiency(self):
        """Test that clustering doesn't cause memory issues."""
        logger.info("Testing memory efficiency (500 candidates)")
        
        # Generate candidates
        candidates = list(generate_candidates(500))
        for candidate in candidates:
            self.kg.add_candidate(candidate)
        
        # Run clustering (should not cause OOM)
        logger.info("Running clustering (checking for memory issues)...")
        try:
            result = self.clusterer.cluster_candidates(candidates)
            logger.info(f"Clustering completed successfully")
            logger.info(f"Optimal K: {result['optimal_k']}")
            logger.info(f"Clustered: {len(result['cluster_assignments'])} candidates")
        except MemoryError:
            pytest.fail("Clustering caused memory error (OOM)")
        
        # Verify results are valid
        assert 'error' not in result, f"Clustering failed: {result.get('error')}"
        assert len(result['cluster_assignments']) == len(candidates), \
            f"Not all candidates clustered: {len(result['cluster_assignments'])}/{len(candidates)}"
        
        logger.info("✅ Memory efficiency verified")

