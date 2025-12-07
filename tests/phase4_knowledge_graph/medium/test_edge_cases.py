"""
test_edge_cases.py - Edge cases and error handling for knowledge graph

Why this test exists:
Real-world usage will have edge cases: missing IDs, invalid data, duplicate IDs,
empty updates, etc. This test ensures the knowledge graph handles these gracefully
without crashing, which is critical for production reliability.

What it validates:
- Missing 'id' field in profile data
- Invalid profile data structures
- Duplicate profile IDs
- Empty update dictionaries
- Updating non-existent profiles
- Getting profiles with invalid IDs
- Relationship operations with invalid IDs

Expected behavior:
- Invalid inputs should be rejected gracefully or handled safely
- Missing IDs should raise clear errors
- Duplicate IDs should either update or be rejected (not crash)
- Empty updates should be handled (no-op or error)
- Invalid relationship operations should return False
"""

import pytest
import logging
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Set up knowledge graph for each test."""
        self.kg = KnowledgeGraph(url='http://weaviate:8080')
    
    def teardown_method(self):
        """Close connection after each test."""
        self.kg.close()
    
    def test_missing_id_field(self):
        """Test adding profile without 'id' field."""
        candidate = {'skills': ['Python']}  # Missing 'id'
        
        with pytest.raises(KeyError):
            self.kg.add_candidate(candidate)
    
    def test_empty_profile_data(self):
        """Test adding profile with minimal data."""
        candidate = {'id': 'minimal_candidate'}
        candidate_id = self.kg.add_candidate(candidate)
        
        assert candidate_id == 'minimal_candidate'
        retrieved = self.kg.get_candidate('minimal_candidate')
        assert retrieved is not None
        assert retrieved['id'] == 'minimal_candidate'
    
    def test_duplicate_profile_id(self):
        """Test adding profile with duplicate ID."""
        candidate1 = {'id': 'duplicate', 'skills': ['Python']}
        candidate2 = {'id': 'duplicate', 'skills': ['Java']}
        
        self.kg.add_candidate(candidate1)
        # Second add should overwrite (or succeed as update)
        candidate_id = self.kg.add_candidate(candidate2)
        
        assert candidate_id == 'duplicate'
        retrieved = self.kg.get_candidate('duplicate')
        # Should have latest data
        assert retrieved is not None
    
    def test_empty_update(self):
        """Test updating with empty update dict."""
        candidate = {'id': 'empty_update', 'skills': ['Python']}
        self.kg.add_candidate(candidate)
        
        # Empty update should either be no-op or error
        result = self.kg.update_candidate('empty_update', {})
        # Should succeed (no-op) or fail gracefully
        assert isinstance(result, bool)
    
    def test_update_nonexistent_profile(self):
        """Test updating a profile that doesn't exist."""
        result = self.kg.update_candidate('nonexistent', {'skills': ['Java']})
        assert result is False
    
    def test_get_invalid_id(self):
        """Test getting profile with invalid ID."""
        result = self.kg.get_candidate('')
        assert result is None
        
        result = self.kg.get_candidate('invalid_id_12345')
        assert result is None
    
    def test_relationship_invalid_ids(self):
        """Test relationship operations with invalid IDs."""
        # Link with non-existent interviewer
        result = self.kg.link_interviewer_to_team('invalid_interviewer', 'invalid_team')
        assert result is False
        
        # Link with non-existent team
        interviewer = {'id': 'valid_interviewer', 'name': 'Test'}
        self.kg.add_interviewer(interviewer)
        result = self.kg.link_interviewer_to_team('valid_interviewer', 'invalid_team')
        assert result is False
    
    def test_get_team_members_nonexistent_team(self):
        """Test getting team members for non-existent team."""
        members = self.kg.get_team_members('nonexistent_team')
        assert members == []
    
    def test_get_team_positions_nonexistent_team(self):
        """Test getting team positions for non-existent team."""
        positions = self.kg.get_team_positions('nonexistent_team')
        assert positions == []
    
    def test_update_preserves_other_fields(self):
        """Test that update doesn't remove other fields."""
        candidate = {
            'id': 'preserve_test',
            'skills': ['Python', 'CUDA'],
            'experience_years': 5,
            'domains': ['ML']
        }
        self.kg.add_candidate(candidate)
        
        # Update only one field
        self.kg.update_candidate('preserve_test', {'experience_years': 7})
        
        updated = self.kg.get_candidate('preserve_test')
        assert updated['experience_years'] == 7
        assert updated['skills'] == ['Python', 'CUDA']  # Preserved
        assert updated['domains'] == ['ML']  # Preserved

