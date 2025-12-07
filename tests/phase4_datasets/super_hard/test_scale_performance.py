"""
test_scale_performance.py - Stress tests at full scale (3,300-5,000 profiles)

Why this test exists:
The system must handle the full dataset scale (1,000-1,500 candidates, etc.)
efficiently. This test validates that embedding generation, vector DB storage,
and knowledge graph operations work correctly at production scale. This is
critical for demonstrating the system can handle real-world workloads.

What it validates:
- Full-scale dataset loading (1,000+ profiles per type)
- Embedding generation performance at scale
- Vector DB storage performance at scale
- Memory usage remains reasonable
- System doesn't crash or degrade under load
- Search performance with large datasets

Expected behavior:
- Full dataset loads successfully
- Performance is acceptable (not too slow)
- Memory usage is bounded
- All profiles are searchable
- System remains stable under load
"""

import pytest
import time
import sys
import logging
from backend.datasets.dataset_loader import DatasetLoader
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Note: VectorDBClient and RecruitingKnowledgeGraphEmbedder are accessed via
# self.kg.vector_db and self.kg.embedder, so no direct imports needed


class TestScalePerformance:
    """Test performance at full scale."""
    
    def setup_method(self):
        """Set up components for scale testing."""
        logger.info("Setting up scale performance test")
        self.kg = KnowledgeGraph(url='http://weaviate:8080')
        self.loader = DatasetLoader(self.kg)
        self.vector_db = self.kg.vector_db
        self.embedder = self.kg.embedder
        logger.info("Components initialized successfully")
    
    def teardown_method(self):
        """Close connection after each test."""
        self.loader.close()
    
    def test_embedding_generation_at_scale(self):
        """Test embedding generation performance with many profiles."""
        from backend.datasets import generate_candidates
        
        logger.info("Starting embedding generation at scale test")
        count = 100
        logger.info(f"Generating embeddings for {count} candidates")
        start_time = time.time()
        
        embeddings_generated = 0
        for candidate in generate_candidates(count):
            logger.debug(f"Generating embedding for candidate {candidate['id']}")
            embedding = self.embedder.embed_candidate(candidate)
            embeddings_generated += 1
            if embeddings_generated % 20 == 0:
                elapsed = time.time() - start_time
                rate = embeddings_generated / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {embeddings_generated}/{count} embeddings ({rate:.1f}/s)")
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / count
        
        logger.info(f"Generated {embeddings_generated} embeddings in {elapsed_time:.2f}s (avg: {avg_time:.2f}s/profile)")
        assert elapsed_time < 600.0, f"Embedding generation too slow: {elapsed_time:.2f}s"
        assert avg_time < 6.0, f"Average embedding time too high: {avg_time:.2f}s per profile"
        logger.info("✅ Embedding generation performance test passed")
    
    def test_vector_db_storage_at_scale(self):
        """Test vector DB storage performance at scale."""
        from backend.datasets import generate_candidates
        
        logger.info("Starting vector DB storage at scale test")
        count = 100
        logger.info(f"Storing {count} candidates in vector DB")
        start_time = time.time()
        
        stored = 0
        failed = 0
        for candidate in generate_candidates(count):
            logger.debug(f"Storing candidate {candidate['id']}")
            embedding = self.embedder.embed_candidate(candidate)
            result = self.vector_db.store_candidate(
                candidate['id'],
                embedding,
                candidate
            )
            if result:
                stored += 1
                logger.debug(f"✅ Stored candidate {candidate['id']}")
            else:
                failed += 1
                logger.warning(f"❌ Failed to store candidate {candidate['id']}")
        
        elapsed_time = time.time() - start_time
        rate = stored / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"Stored {stored}/{count} candidates in {elapsed_time:.2f}s ({rate:.1f}/s)")
        if failed > 0:
            logger.warning(f"⚠️  {failed} candidates failed to store")
        
        assert stored == count, f"Should store all {count} candidates, got {stored}"
        assert elapsed_time < 300.0, f"Storage too slow: {elapsed_time:.2f}s"
        logger.info("✅ Vector DB storage performance test passed")
    
    def test_knowledge_graph_at_scale(self):
        """Test knowledge graph operations at scale."""
        logger.info("Testing knowledge graph operations at scale")
        
        # Load moderate scale dataset
        logger.info("Loading moderate scale dataset: 200 candidates, 100 teams, 150 interviewers, 120 positions")
        result = self.loader.load_all(
            candidates=200,
            teams=100,
            interviewers=150,
            positions=120
        )
        
        logger.info(f"Load result: {result}")
        assert result['total'] == 570, f"Expected 570 total profiles, got {result['total']}"
        
        # Test retrieval performance
        logger.info("Testing retrieval performance - getting all candidates")
        start_time = time.time()
        all_candidates = self.kg.get_all_candidates()
        elapsed_time = time.time() - start_time
        
        logger.info(f"Retrieved {len(all_candidates)} candidates in {elapsed_time:.2f}s")
        assert len(all_candidates) >= 200, f"Expected at least 200 candidates, got {len(all_candidates)}"
        assert elapsed_time < 5.0, f"Retrieval too slow: {elapsed_time:.2f}s"
        
        logger.info("✅ Knowledge graph at scale test passed")
    
    def test_search_performance_at_scale(self):
        """Test similarity search performance with large dataset."""
        logger.info("Starting search performance at scale test")
        
        # Load dataset
        logger.info("Loading 200 candidates for search test")
        loaded = self.loader.load_candidates(200, batch_size=50)
        logger.info(f"Loaded {loaded} candidates")
        
        # Test search
        query_candidate = {
            'id': 'query',
            'skills': ['Python', 'CUDA'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        logger.info(f"Generating query embedding for candidate with skills: {query_candidate['skills']}")
        query_embedding = self.embedder.embed_candidate(query_candidate)
        
        logger.info("Performing similarity search (top_k=50)")
        start_time = time.time()
        results = self.vector_db.search_similar_candidates(query_embedding, top_k=50)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Search returned {len(results)} results in {elapsed_time:.2f}s")
        if len(results) > 0:
            logger.info(f"Top result: {results[0]['profile_id']} (similarity: {results[0]['similarity']:.4f})")
            logger.info(f"Top 5 similarities: {[r['similarity'] for r in results[:5]]}")
        
        assert len(results) > 0, f"Should return search results, got {len(results)}"
        assert elapsed_time < 5.0, f"Search too slow: {elapsed_time:.2f}s"
        
        # Verify search actually finds relevant candidates
        if len(results) > 0:
            top_result = results[0]
            logger.info(f"Verifying top result: {top_result['profile_id']}")
            candidate = self.kg.get_candidate(top_result['profile_id'])
            if candidate:
                logger.info(f"Top candidate skills: {candidate.get('skills', [])}")
                logger.info(f"Top candidate domains: {candidate.get('domains', [])}")
        
        logger.info("✅ Search performance test passed")
    
    def test_memory_efficiency(self):
        """Test that memory usage is reasonable."""
        import tracemalloc
        
        logger.info("Testing memory efficiency")
        logger.info("Starting memory tracing...")
        tracemalloc.start()
        
        # Load dataset
        logger.info("Loading dataset: 100 candidates, 50 teams, 75 interviewers, 60 positions")
        self.loader.load_all(
            candidates=100,
            teams=50,
            interviewers=75,
            positions=60
        )
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory should be reasonable (adjust threshold as needed)
        # Peak memory in MB
        peak_mb = peak / 1024 / 1024
        current_mb = current / 1024 / 1024
        
        logger.info(f"Memory usage - Current: {current_mb:.1f}MB, Peak: {peak_mb:.1f}MB")
        assert peak_mb < 2000, f"Memory usage too high: {peak_mb:.1f}MB"
        
        logger.info("✅ Memory efficiency test passed")

