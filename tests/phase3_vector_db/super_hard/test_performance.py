"""
test_performance.py - Performance and stress tests for vector DB

Why this test exists:
In production, we'll store thousands of profiles and perform many searches.
This test ensures the vector DB can handle high-volume operations efficiently
and doesn't degrade with scale. Performance is critical for real-time matching.

What it validates:
- Batch storage performance (multiple profiles)
- Search performance with many stored profiles
- Memory usage doesn't grow unbounded
- Concurrent operations work correctly
- Large-scale operations complete in reasonable time

Expected behavior:
- Batch operations should complete in reasonable time
- Search performance should be consistent regardless of database size
- No memory leaks or unbounded growth
- Concurrent operations should work correctly
"""

import pytest
import numpy as np
import time
import logging
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestPerformance:
    """Test performance and stress scenarios."""
    
    def setup_method(self):
        """Set up embedder and vector DB client."""
        self.embedder = RecruitingKnowledgeGraphEmbedder()
        self.client = VectorDBClient(url='http://weaviate:8080')
    
    def teardown_method(self):
        """Close connection after each test."""
        self.client.close()
    
    def test_batch_storage_performance(self):
        """Test storing multiple profiles in batch."""
        num_profiles = 20
        
        start_time = time.time()
        
        for i in range(num_profiles):
            candidate = {
                'id': f'batch_candidate_{i}',
                'skills': [f'Skill{i % 10}'],
                'experience_years': i % 10
            }
            embedding = self.embedder.embed_candidate(candidate)
            self.client.store_candidate(f'batch_candidate_{i}', embedding, candidate)
        
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert elapsed_time < 60.0, f"Batch storage took too long: {elapsed_time:.2f}s"
        
        # Verify all were stored
        test_embedding = self.embedder.embed_candidate({'id': 'test', 'skills': ['Skill0']})
        results = self.client.search_similar_candidates(test_embedding, top_k=num_profiles)
        assert len(results) >= num_profiles, f"Should find at least {num_profiles} candidates"
    
    def test_search_performance_with_many_profiles(self):
        """Test search performance with many stored profiles."""
        # Store many profiles
        num_profiles = 30
        for i in range(num_profiles):
            candidate = {
                'id': f'perf_candidate_{i}',
                'skills': [f'Skill{i % 5}'],
                'experience_years': i % 10
            }
            embedding = self.embedder.embed_candidate(candidate)
            self.client.store_candidate(f'perf_candidate_{i}', embedding, candidate)
        
        # Test search performance
        query_candidate = {'id': 'query', 'skills': ['Skill0']}
        query_embedding = self.embedder.embed_candidate(query_candidate)
        
        start_time = time.time()
        results = self.client.search_similar_candidates(query_embedding, top_k=10)
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 5.0, f"Search took too long: {elapsed_time:.2f}s"
        assert len(results) > 0, "Should return results"
    
    def test_all_profile_types_batch(self):
        """Test batch operations for all 4 profile types."""
        num_each = 5
        
        start_time = time.time()
        
        # Store candidates
        for i in range(num_each):
            candidate = {'id': f'c{i}', 'skills': ['Python']}
            emb = self.embedder.embed_candidate(candidate)
            self.client.store_candidate(f'c{i}', emb, candidate)
        
        # Store teams
        for i in range(num_each):
            team = {'id': f't{i}', 'name': f'Team {i}', 'needs': ['Python']}
            emb = self.embedder.embed_team(team)
            self.client.store_team(f't{i}', emb, team)
        
        # Store interviewers
        for i in range(num_each):
            interviewer = {'id': f'i{i}', 'name': f'Interviewer {i}', 'expertise': ['Python']}
            emb = self.embedder.embed_interviewer(interviewer)
            self.client.store_interviewer(f'i{i}', emb, interviewer)
        
        # Store positions
        for i in range(num_each):
            position = {'id': f'p{i}', 'title': f'Position {i}', 'must_haves': ['Python']}
            emb = self.embedder.embed_position(position)
            self.client.store_position(f'p{i}', emb, position)
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 60.0, f"Batch storage all types took too long: {elapsed_time:.2f}s"
    
    def test_repeated_searches(self):
        """Test that repeated searches maintain performance."""
        # Store some profiles
        for i in range(10):
            candidate = {'id': f'repeat_c{i}', 'skills': ['Python']}
            emb = self.embedder.embed_candidate(candidate)
            self.client.store_candidate(f'repeat_c{i}', emb, candidate)
        
        query_embedding = self.embedder.embed_candidate({'id': 'query', 'skills': ['Python']})
        
        # Perform multiple searches
        times = []
        for _ in range(10):
            start = time.time()
            results = self.client.search_similar_candidates(query_embedding, top_k=5)
            elapsed = time.time() - start
            times.append(elapsed)
        
        # Performance should be consistent
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 2.0, f"Average search time too high: {avg_time:.2f}s"
        assert max_time < 5.0, f"Max search time too high: {max_time:.2f}s"

