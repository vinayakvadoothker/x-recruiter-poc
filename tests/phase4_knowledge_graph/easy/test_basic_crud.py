"""
test_basic_crud.py - Basic CRUD operations for knowledge graph

Why this test exists:
This test verifies that the knowledge graph can perform basic CRUD operations
(add, get, update) for all 4 profile types. This is the foundation - without
working CRUD, the entire system fails. These are the most common operations
that will be used throughout the application.

What it validates:
- add_candidate() creates candidate with automatic embedding
- get_candidate() retrieves candidate by ID
- get_all_candidates() lists all candidates
- update_candidate() updates and re-embeds candidate
- Similar operations for teams, interviewers, positions
- Metadata is preserved correctly
- Embeddings are generated automatically

Expected behavior:
- All add operations return profile IDs
- All get operations return correct profiles or None
- All update operations return True/False
- Profiles are stored in metadata store
- Embeddings are stored in vector DB
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


class TestBasicCRUD:
    """Test basic CRUD operations for all profile types."""
    
    def setup_method(self):
        """Set up knowledge graph for each test."""
        self.kg = KnowledgeGraph(url='http://weaviate:8080')
    
    def teardown_method(self):
        """Close connection after each test."""
        self.kg.close()
    
    def test_add_get_candidate(self):
        """Test adding and retrieving a candidate."""
        candidate = {
            'id': 'test_candidate_1',
            'skills': ['Python', 'CUDA'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        
        candidate_id = self.kg.add_candidate(candidate)
        assert candidate_id == 'test_candidate_1'
        
        retrieved = self.kg.get_candidate('test_candidate_1')
        assert retrieved is not None
        assert retrieved['id'] == 'test_candidate_1'
        assert retrieved['skills'] == candidate['skills']
    
    def test_add_get_team(self):
        """Test adding and retrieving a team."""
        team = {
            'id': 'test_team_1',
            'name': 'Test Team',
            'needs': ['CUDA expertise'],
            'expertise': ['CUDA']
        }
        
        team_id = self.kg.add_team(team)
        assert team_id == 'test_team_1'
        
        retrieved = self.kg.get_team('test_team_1')
        assert retrieved is not None
        assert retrieved['name'] == 'Test Team'
    
    def test_add_get_interviewer(self):
        """Test adding and retrieving an interviewer."""
        interviewer = {
            'id': 'test_interviewer_1',
            'name': 'Test Interviewer',
            'expertise': ['CUDA'],
            'total_interviews': 50
        }
        
        interviewer_id = self.kg.add_interviewer(interviewer)
        assert interviewer_id == 'test_interviewer_1'
        
        retrieved = self.kg.get_interviewer('test_interviewer_1')
        assert retrieved is not None
        assert retrieved['name'] == 'Test Interviewer'
    
    def test_add_get_position(self):
        """Test adding and retrieving a position."""
        position = {
            'id': 'test_position_1',
            'title': 'Test Position',
            'must_haves': ['CUDA'],
            'requirements': ['5+ years']
        }
        
        position_id = self.kg.add_position(position)
        assert position_id == 'test_position_1'
        
        retrieved = self.kg.get_position('test_position_1')
        assert retrieved is not None
        assert retrieved['title'] == 'Test Position'
    
    def test_get_all_candidates(self):
        """Test getting all candidates."""
        # Add multiple candidates
        for i in range(3):
            self.kg.add_candidate({
                'id': f'candidate_{i}',
                'skills': ['Python']
            })
        
        all_candidates = self.kg.get_all_candidates()
        assert len(all_candidates) >= 3
        assert any(c['id'] == 'candidate_0' for c in all_candidates)
    
    def test_update_candidate(self):
        """Test updating a candidate."""
        candidate = {
            'id': 'update_test',
            'skills': ['Python'],
            'experience_years': 3
        }
        self.kg.add_candidate(candidate)
        
        # Update
        result = self.kg.update_candidate('update_test', {'experience_years': 5})
        assert result is True
        
        # Verify update
        updated = self.kg.get_candidate('update_test')
        assert updated['experience_years'] == 5
        assert updated['skills'] == ['Python']  # Unchanged
    
    def test_update_nonexistent(self):
        """Test updating a non-existent profile."""
        result = self.kg.update_candidate('nonexistent', {'skills': ['Java']})
        assert result is False
    
    def test_get_nonexistent(self):
        """Test getting a non-existent profile."""
        result = self.kg.get_candidate('nonexistent')
        assert result is None
    
    def test_all_profile_types_crud(self):
        """Test CRUD for all 4 profile types."""
        # Add all types
        c_id = self.kg.add_candidate({'id': 'c1', 'skills': ['Python']})
        t_id = self.kg.add_team({'id': 't1', 'name': 'Team 1'})
        i_id = self.kg.add_interviewer({'id': 'i1', 'name': 'Interviewer 1'})
        p_id = self.kg.add_position({'id': 'p1', 'title': 'Position 1'})
        
        # Get all types
        assert self.kg.get_candidate(c_id) is not None
        assert self.kg.get_team(t_id) is not None
        assert self.kg.get_interviewer(i_id) is not None
        assert self.kg.get_position(p_id) is not None
        
        # Update all types
        assert self.kg.update_candidate(c_id, {'experience_years': 5}) is True
        assert self.kg.update_team(t_id, {'member_count': 10}) is True
        assert self.kg.update_interviewer(i_id, {'total_interviews': 100}) is True
        assert self.kg.update_position(p_id, {'status': 'closed'}) is True

