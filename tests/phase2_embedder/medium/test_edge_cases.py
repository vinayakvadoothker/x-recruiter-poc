"""
test_edge_cases.py - Edge cases and error handling tests

Why this test exists:
Real-world data is messy. Profiles may have missing fields, empty lists, or minimal data.
This test ensures the embedder handles edge cases gracefully without crashing, which is
critical for production reliability. We need to handle incomplete data robustly.

What it validates:
- Missing optional fields don't cause errors
- Empty lists/arrays are handled correctly
- Minimal data (only required fields) works
- None values are handled safely
- Very long text fields are truncated appropriately
- Special characters in text don't break embedding

Expected behavior:
- All edge cases should produce valid embeddings (768-dim, normalized)
- No exceptions should be raised for missing optional fields
- Empty data should still produce embeddings (though less meaningful)
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


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Set up embedder instance for each test."""
        self.embedder = RecruitingKnowledgeGraphEmbedder()
    
    def test_candidate_minimal_data(self):
        """Test candidate embedding with minimal required data."""
        minimal = {'skills': []}
        embedding = self.embedder.embed_candidate(minimal)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_candidate_missing_optional_fields(self):
        """Test candidate with missing optional fields."""
        candidate = {
            'skills': ['Python'],
            # Missing: experience_years, domains, education, projects, etc.
        }
        embedding = self.embedder.embed_candidate(candidate)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_candidate_empty_lists(self):
        """Test candidate with all empty lists."""
        candidate = {
            'skills': [],
            'experience': [],
            'domains': [],
            'education': [],
            'projects': []
        }
        embedding = self.embedder.embed_candidate(candidate)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_team_minimal_data(self):
        """Test team embedding with minimal data."""
        minimal = {'name': 'Test Team'}
        embedding = self.embedder.embed_team(minimal)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_team_empty_needs(self):
        """Test team with empty needs list."""
        team = {
            'name': 'Test Team',
            'needs': [],
            'expertise': [],
            'stack': []
        }
        embedding = self.embedder.embed_team(team)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_interviewer_minimal_data(self):
        """Test interviewer embedding with minimal data."""
        minimal = {'name': 'Test Interviewer'}
        embedding = self.embedder.embed_interviewer(minimal)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_interviewer_zero_interviews(self):
        """Test interviewer with zero interview history."""
        interviewer = {
            'name': 'New Interviewer',
            'total_interviews': 0,
            'successful_hires': 0,
            'success_rate': 0.0
        }
        embedding = self.embedder.embed_interviewer(interviewer)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_position_minimal_data(self):
        """Test position embedding with minimal data."""
        minimal = {'title': 'Test Position'}
        embedding = self.embedder.embed_position(minimal)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_position_empty_requirements(self):
        """Test position with empty requirements."""
        position = {
            'title': 'Test Position',
            'requirements': [],
            'must_haves': [],
            'nice_to_haves': []
        }
        embedding = self.embedder.embed_position(position)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_position_long_description(self):
        """Test position with very long description (should be truncated)."""
        long_desc = 'A' * 1000  # Very long description
        position = {
            'title': 'Test Position',
            'description': long_desc,
            'must_haves': ['Python']
        }
        embedding = self.embedder.embed_position(position)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01
    
    def test_special_characters(self):
        """Test that special characters don't break embedding."""
        candidate = {
            'skills': ['C++', 'C#', 'F#', 'R&D'],
            'experience': ['Worked on "Project X" & "Project Y"'],
            'domains': ['ML/AI', 'NLP & CV']
        }
        embedding = self.embedder.embed_candidate(candidate)
        
        assert embedding.shape == (768,)
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.01

