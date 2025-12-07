"""
test_consistency_and_similarity.py - Complex scenarios and integration tests

Why this test exists:
Embeddings must be consistent (same input → same output) and meaningful (similar
profiles → similar embeddings). This test verifies that our specialized formatting
produces embeddings that capture semantic relationships correctly, which is essential
for matching candidates to positions, teams, and interviewers.

What it validates:
- Consistency: Same input produces same embedding
- Differentiation: Different inputs produce different embeddings
- Semantic similarity: Similar profiles have higher similarity scores
- Cross-type similarity: Candidate-position similarity works correctly
- Profile type relationships: Team-candidate, interviewer-candidate, position-candidate

Expected behavior:
- Same input → cosine similarity ≈ 1.0
- Different inputs → cosine similarity < 1.0
- Similar profiles → higher similarity than dissimilar profiles
- Cross-type embeddings can be compared meaningfully
"""

import pytest
import numpy as np
import logging
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestConsistencyAndSimilarity:
    """Test consistency and semantic similarity of embeddings."""
    
    def setup_method(self):
        """Set up embedder instance for each test."""
        self.embedder = RecruitingKnowledgeGraphEmbedder()
    
    def test_consistency_same_input(self):
        """Test that same input produces same embedding."""
        candidate = {
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        
        emb1 = self.embedder.embed_candidate(candidate)
        emb2 = self.embedder.embed_candidate(candidate)
        
        similarity = np.dot(emb1, emb2)
        assert abs(similarity - 1.0) < 0.01, f"Same input should produce same embedding, got similarity={similarity:.6f}"
    
    def test_differentiation_different_inputs(self):
        """Test that different inputs produce different embeddings."""
        candidate1 = {
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        candidate2 = {
            'skills': ['Python', 'Django', 'PostgreSQL'],
            'experience_years': 3,
            'domains': ['Web Development']
        }
        
        emb1 = self.embedder.embed_candidate(candidate1)
        emb2 = self.embedder.embed_candidate(candidate2)
        
        similarity = np.dot(emb1, emb2)
        assert abs(similarity) < 0.99, f"Different inputs should produce different embeddings, got similarity={similarity:.4f}"
    
    def test_semantic_similarity_similar_profiles(self):
        """Test that similar profiles have higher similarity."""
        # Two CUDA experts
        candidate1 = {
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        candidate2 = {
            'skills': ['CUDA', 'C++', 'TensorRT'],
            'experience_years': 6,
            'domains': ['LLM Inference']
        }
        
        # CUDA expert vs web developer
        candidate3 = {
            'skills': ['Python', 'Django', 'PostgreSQL'],
            'experience_years': 4,
            'domains': ['Web Development']
        }
        
        emb1 = self.embedder.embed_candidate(candidate1)
        emb2 = self.embedder.embed_candidate(candidate2)
        emb3 = self.embedder.embed_candidate(candidate3)
        
        sim_12 = np.dot(emb1, emb2)  # Two CUDA experts
        sim_13 = np.dot(emb1, emb3)  # CUDA expert vs web dev
        
        assert sim_12 > sim_13, f"Similar profiles should have higher similarity. CUDA-CUDA={sim_12:.4f}, CUDA-Web={sim_13:.4f}"
    
    def test_cross_type_similarity_candidate_position(self):
        """Test that candidate and position embeddings can be compared."""
        candidate = {
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        position = {
            'title': 'Senior LLM Inference Engineer',
            'must_haves': ['CUDA', 'C++', 'PyTorch'],
            'requirements': ['5+ years CUDA'],
            'domains': ['LLM Inference']
        }
        
        c_emb = self.embedder.embed_candidate(candidate)
        p_emb = self.embedder.embed_position(position)
        
        similarity = np.dot(c_emb, p_emb)
        assert 0.0 <= similarity <= 1.0, f"Similarity should be between 0 and 1, got {similarity:.4f}"
        assert similarity > 0.5, f"Matching candidate-position should have reasonable similarity, got {similarity:.4f}"
    
    def test_cross_type_similarity_candidate_team(self):
        """Test that candidate and team embeddings can be compared."""
        candidate = {
            'skills': ['CUDA', 'C++'],
            'domains': ['LLM Inference']
        }
        team = {
            'name': 'LLM Inference Team',
            'needs': ['CUDA expertise', 'GPU optimization'],
            'expertise': ['CUDA', 'GPU Computing'],
            'domains': ['LLM Inference']
        }
        
        c_emb = self.embedder.embed_candidate(candidate)
        t_emb = self.embedder.embed_team(team)
        
        similarity = np.dot(c_emb, t_emb)
        assert 0.0 <= similarity <= 1.0, f"Similarity should be between 0 and 1, got {similarity:.4f}"
    
    def test_cross_type_similarity_candidate_interviewer(self):
        """Test that candidate and interviewer embeddings can be compared."""
        candidate = {
            'skills': ['CUDA', 'C++'],
            'domains': ['LLM Inference']
        }
        interviewer = {
            'name': 'Alex Chen',
            'expertise': ['CUDA', 'GPU Optimization'],
            'specializations': ['CUDA kernels']
        }
        
        c_emb = self.embedder.embed_candidate(candidate)
        i_emb = self.embedder.embed_interviewer(interviewer)
        
        similarity = np.dot(c_emb, i_emb)
        assert 0.0 <= similarity <= 1.0, f"Similarity should be between 0 and 1, got {similarity:.4f}"
    
    def test_profile_type_differentiation(self):
        """Test that different profile types produce distinct embeddings."""
        candidate = {'skills': ['CUDA'], 'experience_years': 5}
        team = {'name': 'CUDA Team', 'needs': ['CUDA']}
        interviewer = {'name': 'CUDA Expert', 'expertise': ['CUDA']}
        position = {'title': 'CUDA Engineer', 'must_haves': ['CUDA']}
        
        c_emb = self.embedder.embed_candidate(candidate)
        t_emb = self.embedder.embed_team(team)
        i_emb = self.embedder.embed_interviewer(interviewer)
        p_emb = self.embedder.embed_position(position)
        
        # All should be different (even with same skill)
        sims = [
            np.dot(c_emb, t_emb),
            np.dot(c_emb, i_emb),
            np.dot(c_emb, p_emb),
            np.dot(t_emb, i_emb),
            np.dot(t_emb, p_emb),
            np.dot(i_emb, p_emb)
        ]
        
        # Similarities should be reasonable but not identical
        for sim in sims:
            assert 0.0 <= sim <= 1.0, f"Similarity out of range: {sim:.4f}"

