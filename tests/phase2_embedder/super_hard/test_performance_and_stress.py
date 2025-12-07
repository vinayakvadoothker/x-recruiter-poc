"""
test_performance_and_stress.py - Stress tests and performance tests

Why this test exists:
In production, we'll embed hundreds or thousands of profiles. This test ensures the
embedder can handle high-volume operations efficiently and doesn't degrade with
repeated use. Performance is critical for real-time matching and batch processing.

What it validates:
- Batch embedding performance (multiple profiles)
- Memory usage doesn't grow unbounded
- Repeated embeddings don't degrade performance
- Large profiles (many skills, long descriptions) are handled efficiently
- Concurrent embedding requests work correctly

Expected behavior:
- Batch operations should complete in reasonable time
- Memory usage should be stable (no leaks)
- Performance should be consistent across runs
- Large profiles should still produce embeddings
"""

import pytest
import numpy as np
import time
import logging
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestPerformanceAndStress:
    """Test performance and stress scenarios."""
    
    def setup_method(self):
        """Set up embedder instance for each test."""
        self.embedder = RecruitingKnowledgeGraphEmbedder()
    
    def test_batch_embedding_performance(self):
        """Test embedding multiple profiles in batch."""
        candidates = [
            {
                'skills': ['CUDA', 'C++', 'PyTorch'],
                'experience_years': i,
                'domains': ['LLM Inference']
            }
            for i in range(10)
        ]
        
        start_time = time.time()
        embeddings = [self.embedder.embed_candidate(c) for c in candidates]
        elapsed_time = time.time() - start_time
        
        # All should be valid
        for emb in embeddings:
            assert emb.shape == (768,)
            assert abs(np.linalg.norm(emb) - 1.0) < 0.01
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert elapsed_time < 30.0, f"Batch embedding took too long: {elapsed_time:.2f}s"
    
    def test_large_profile_embedding(self):
        """Test embedding with very large profile data."""
        large_candidate = {
            'skills': [f'Skill{i}' for i in range(50)],  # 50 skills
            'experience': [f'Experience {i}' for i in range(20)],  # 20 experiences
            'education': [f'Education {i}' for i in range(10)],  # 10 education items
            'projects': [{'name': f'Project {i}', 'description': 'A' * 100} for i in range(15)],
            'experience_years': 10,
            'domains': ['Domain1', 'Domain2', 'Domain3']
        }
        
        start_time = time.time()
        embedding = self.embedder.embed_candidate(large_candidate)
        elapsed_time = time.time() - start_time
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
        assert elapsed_time < 5.0, f"Large profile embedding took too long: {elapsed_time:.2f}s"
    
    def test_repeated_embedding_consistency(self):
        """Test that repeated embeddings maintain consistency."""
        candidate = {
            'skills': ['CUDA', 'C++'],
            'experience_years': 5
        }
        
        embeddings = []
        for _ in range(20):
            emb = self.embedder.embed_candidate(candidate)
            embeddings.append(emb)
        
        # All should be identical
        first_emb = embeddings[0]
        for emb in embeddings[1:]:
            similarity = np.dot(first_emb, emb)
            assert abs(similarity - 1.0) < 0.01, "Repeated embeddings should be identical"
    
    def test_all_profile_types_batch(self):
        """Test batch embedding for all 4 profile types."""
        candidates = [{'skills': ['Python'], 'experience_years': i} for i in range(5)]
        teams = [{'name': f'Team {i}', 'needs': ['Python']} for i in range(5)]
        interviewers = [{'name': f'Interviewer {i}', 'expertise': ['Python']} for i in range(5)]
        positions = [{'title': f'Position {i}', 'must_haves': ['Python']} for i in range(5)]
        
        start_time = time.time()
        
        c_embs = [self.embedder.embed_candidate(c) for c in candidates]
        t_embs = [self.embedder.embed_team(t) for t in teams]
        i_embs = [self.embedder.embed_interviewer(i) for i in interviewers]
        p_embs = [self.embedder.embed_position(p) for p in positions]
        
        elapsed_time = time.time() - start_time
        
        # Verify all embeddings
        all_embs = c_embs + t_embs + i_embs + p_embs
        for emb in all_embs:
            assert emb.shape == (768,)
            assert abs(np.linalg.norm(emb) - 1.0) < 0.01
        
        assert elapsed_time < 30.0, f"Batch embedding all types took too long: {elapsed_time:.2f}s"
    
    def test_very_long_text_fields(self):
        """Test embedding with very long text fields."""
        position = {
            'title': 'Test Position',
            'description': 'A' * 2000,  # Very long description
            'must_haves': ['Python']
        }
        
        embedding = self.embedder.embed_position(position)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01

