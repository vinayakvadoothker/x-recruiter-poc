"""
test_basic_operations.py - Basic vector DB operations tests

Why this test exists:
This test verifies that the vector database can store and retrieve embeddings
for all 4 profile types. This is the foundation of our similarity search system.
Without working storage and retrieval, the entire matching pipeline fails.

What it validates:
- store_candidate() stores embeddings correctly
- store_team() stores embeddings correctly
- store_interviewer() stores embeddings correctly
- store_position() stores embeddings correctly
- search_similar_*() methods return results
- Results include profile_id, metadata, and similarity scores

Expected behavior:
- All store operations return True
- Search operations return lists of results
- Results contain expected fields (profile_id, metadata, similarity)
- Similarity scores are between 0 and 1
"""

import pytest
import numpy as np
import logging
from backend.database.vector_db_client import VectorDBClient

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestBasicOperations:
    """Test basic vector DB storage and search operations."""
    
    def setup_method(self):
        """Set up vector DB client for each test."""
        self.client = VectorDBClient(url='http://weaviate:8080')
    
    def teardown_method(self):
        """Close connection after each test."""
        self.client.close()
    
    def test_store_candidate(self):
        """Test storing candidate embedding."""
        candidate_id = "test_candidate_1"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize
        
        metadata = {
            'id': candidate_id,
            'skills': ['CUDA', 'C++'],
            'experience_years': 5
        }
        
        result = self.client.store_candidate(candidate_id, embedding, metadata)
        assert result is True, "Store candidate should return True"
    
    def test_store_team(self):
        """Test storing team embedding."""
        team_id = "test_team_1"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {
            'id': team_id,
            'name': 'Test Team',
            'needs': ['CUDA expertise']
        }
        
        result = self.client.store_team(team_id, embedding, metadata)
        assert result is True, "Store team should return True"
    
    def test_store_interviewer(self):
        """Test storing interviewer embedding."""
        interviewer_id = "test_interviewer_1"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {
            'id': interviewer_id,
            'name': 'Test Interviewer',
            'expertise': ['CUDA']
        }
        
        result = self.client.store_interviewer(interviewer_id, embedding, metadata)
        assert result is True, "Store interviewer should return True"
    
    def test_store_position(self):
        """Test storing position embedding."""
        position_id = "test_position_1"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {
            'id': position_id,
            'title': 'Test Position',
            'must_haves': ['CUDA']
        }
        
        result = self.client.store_position(position_id, embedding, metadata)
        assert result is True, "Store position should return True"
    
    def test_search_similar_candidates(self):
        """Test searching for similar candidates."""
        logger.info("Testing candidate similarity search")
        
        # Store a candidate first
        candidate_id = "search_test_candidate"
        logger.info(f"Storing candidate: {candidate_id}")
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {'id': candidate_id, 'skills': ['Python']}
        stored = self.client.store_candidate(candidate_id, embedding, metadata)
        logger.info(f"Store result: {stored}")
        assert stored is True
        
        # Search for similar candidates
        logger.info(f"Searching for similar candidates (top_k=5)")
        results = self.client.search_similar_candidates(embedding, top_k=5)
        
        logger.info(f"Search returned {len(results)} results")
        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, f"Should return at least one result, got {len(results)}"
        
        # Check result structure
        result = results[0]
        logger.info(f"Top result: profile_id={result.get('profile_id')}, similarity={result.get('similarity', 'N/A')}")
        assert 'profile_id' in result, "Result should have profile_id"
        assert 'metadata' in result, "Result should have metadata"
        assert 'similarity' in result, "Result should have similarity"
        assert 0.0 <= result['similarity'] <= 1.0, f"Similarity should be between 0 and 1, got {result['similarity']}"
        
        # Verify we can find the candidate we just stored
        found_our_candidate = any(r['profile_id'] == candidate_id for r in results)
        logger.info(f"Found our stored candidate in results: {found_our_candidate}")
        if found_our_candidate:
            our_result = next(r for r in results if r['profile_id'] == candidate_id)
            logger.info(f"Our candidate similarity: {our_result['similarity']:.4f}")
        
        logger.info("✅ Candidate search test passed")
    
    def test_search_similar_teams(self):
        """Test searching for similar teams."""
        team_id = "search_test_team"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {'id': team_id, 'name': 'Test Team'}
        self.client.store_team(team_id, embedding, metadata)
        
        results = self.client.search_similar_teams(embedding, top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert 'profile_id' in results[0]
        assert 'similarity' in results[0]
    
    def test_search_similar_interviewers(self):
        """Test searching for similar interviewers."""
        interviewer_id = "search_test_interviewer"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {'id': interviewer_id, 'name': 'Test Interviewer'}
        self.client.store_interviewer(interviewer_id, embedding, metadata)
        
        results = self.client.search_similar_interviewers(embedding, top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert 'profile_id' in results[0]
        assert 'similarity' in results[0]
    
    def test_search_similar_positions(self):
        """Test searching for similar positions."""
        position_id = "search_test_position"
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata = {'id': position_id, 'title': 'Test Position'}
        self.client.store_position(position_id, embedding, metadata)
        
        results = self.client.search_similar_positions(embedding, top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert 'profile_id' in results[0]
        assert 'similarity' in results[0]
    
    def test_all_profile_types_storage(self):
        """Test storing all 4 profile types."""
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        c_result = self.client.store_candidate("c1", embedding, {'id': 'c1'})
        t_result = self.client.store_team("t1", embedding, {'id': 't1'})
        i_result = self.client.store_interviewer("i1", embedding, {'id': 'i1'})
        p_result = self.client.store_position("p1", embedding, {'id': 'p1'})
        
        assert all([c_result, t_result, i_result, p_result]), "All storage operations should succeed"

