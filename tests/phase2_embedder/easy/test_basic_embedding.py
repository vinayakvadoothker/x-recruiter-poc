"""
test_basic_embedding.py - Basic embedding functionality tests

Why this test exists:
This test verifies that all 4 embed methods (candidate, team, interviewer, position)
work correctly with valid input. This is critical because embeddings are the foundation
of our similarity search and matching system. Without working embeddings, the entire
pipeline fails.

What it validates:
- embed_candidate() returns valid embedding vector
- embed_team() returns valid embedding vector
- embed_interviewer() returns valid embedding vector
- embed_position() returns valid embedding vector
- All embeddings have correct dimensions (768 for MPNet)
- All embeddings are normalized (unit vectors)

Expected behavior:
- All 4 methods should return numpy arrays of shape (768,)
- All embeddings should be normalized (||embedding|| ≈ 1.0)
- No errors or exceptions should be raised
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


class TestBasicEmbedding:
    """Test basic embedding functionality for all 4 profile types."""
    
    def setup_method(self):
        """Set up embedder instance for each test."""
        self.embedder = RecruitingKnowledgeGraphEmbedder()
    
    def test_candidate_embedding_basic(self):
        """Test candidate embedding with valid data."""
        candidate = {
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference'],
            'education': ['MS Computer Science'],
            'projects': [{'name': 'LLM Optimizer'}],
            'expertise_level': 'Senior',
            'github_stats': {'total_commits': 100}
        }
        
        embedding = self.embedder.embed_candidate(candidate)
        
        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.shape == (768,), f"Expected shape (768,), got {embedding.shape}"
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01, "Embedding should be normalized"
    
    def test_team_embedding_basic(self):
        """Test team embedding with valid data."""
        team = {
            'name': 'LLM Inference Team',
            'department': 'AI Infrastructure',
            'needs': ['CUDA expertise', 'GPU optimization'],
            'expertise': ['CUDA', 'GPU Computing'],
            'stack': ['CUDA', 'C++', 'PyTorch'],
            'domains': ['LLM Inference'],
            'culture': 'Fast-paced, research-oriented',
            'work_style': 'Hybrid',
            'member_count': 5
        }
        
        embedding = self.embedder.embed_team(team)
        
        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.shape == (768,), f"Expected shape (768,), got {embedding.shape}"
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01, "Embedding should be normalized"
    
    def test_interviewer_embedding_basic(self):
        """Test interviewer embedding with valid data."""
        interviewer = {
            'name': 'Alex Chen',
            'expertise': ['CUDA', 'GPU Optimization'],
            'expertise_level': 'Senior',
            'specializations': ['CUDA kernel optimization'],
            'total_interviews': 50,
            'successful_hires': 38,
            'success_rate': 0.76,
            'interview_style': 'Technical deep-dive',
            'evaluation_focus': ['Technical depth', 'Problem-solving'],
            'question_style': 'Open-ended, scenario-based'
        }
        
        embedding = self.embedder.embed_interviewer(interviewer)
        
        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.shape == (768,), f"Expected shape (768,), got {embedding.shape}"
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01, "Embedding should be normalized"
    
    def test_position_embedding_basic(self):
        """Test position embedding with valid data."""
        position = {
            'title': 'Senior LLM Inference Optimization Engineer',
            'description': 'We are looking for a senior engineer to optimize LLM inference performance.',
            'requirements': ['5+ years CUDA', 'Strong C++', 'PyTorch experience'],
            'must_haves': ['CUDA', 'C++', 'LLM inference experience'],
            'nice_to_haves': ['TensorRT', 'Triton'],
            'experience_level': 'Senior',
            'tech_stack': ['CUDA', 'C++', 'PyTorch'],
            'domains': ['LLM Inference'],
            'responsibilities': ['Optimize LLM inference', 'Build CUDA kernels'],
            'team_context': 'Part of LLM Inference team'
        }
        
        embedding = self.embedder.embed_position(position)
        
        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.shape == (768,), f"Expected shape (768,), got {embedding.shape}"
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01, "Embedding should be normalized"
    
    def test_all_profile_types_work(self):
        """Test that all 4 profile types can be embedded."""
        candidate = {'skills': ['Python'], 'experience_years': 3}
        team = {'name': 'Test Team', 'needs': ['Python']}
        interviewer = {'name': 'Test', 'expertise': ['Python']}
        position = {'title': 'Test Position', 'must_haves': ['Python']}
        
        c_emb = self.embedder.embed_candidate(candidate)
        t_emb = self.embedder.embed_team(team)
        i_emb = self.embedder.embed_interviewer(interviewer)
        p_emb = self.embedder.embed_position(position)
        
        # All should be valid embeddings
        assert c_emb.shape == (768,)
        assert t_emb.shape == (768,)
        assert i_emb.shape == (768,)
        assert p_emb.shape == (768,)
        
        # All should be normalized
        assert abs(np.linalg.norm(c_emb) - 1.0) < 0.01
        assert abs(np.linalg.norm(t_emb) - 1.0) < 0.01
        assert abs(np.linalg.norm(i_emb) - 1.0) < 0.01
        assert abs(np.linalg.norm(p_emb) - 1.0) < 0.01

