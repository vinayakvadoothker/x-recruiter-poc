"""
test_integration.py - Full integration tests with embedder and vector DB

Why this test exists:
The knowledge graph must work seamlessly with the embedder and vector DB.
This test verifies the end-to-end flow: add profile → generate embedding →
store in vector DB → retrieve → search. This is critical because all three
components must work together perfectly for the system to function.

What it validates:
- End-to-end flow for all 4 profile types
- Embeddings are generated and stored correctly
- Vector DB search works with knowledge graph profiles
- Updates trigger re-embedding and re-storage
- Relationships work with embeddings
- Large-scale operations work correctly

Expected behavior:
- Profiles added via knowledge graph can be found via vector DB search
- Updates result in new embeddings being stored
- Relationships don't break embedding storage
- System handles multiple profiles correctly
"""

import pytest
import numpy as np
import logging
from backend.database.knowledge_graph import KnowledgeGraph
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestIntegration:
    """Test integration with embedder and vector DB."""
    
    def setup_method(self):
        """Set up knowledge graph and components."""
        self.kg = KnowledgeGraph(url='http://weaviate:8080')
        self.vector_db = self.kg.vector_db
        self.embedder = self.kg.embedder
    
    def teardown_method(self):
        """Close connection after each test."""
        self.kg.close()
    
    def test_end_to_end_candidate(self):
        """Test end-to-end: add → embed → store → retrieve → search."""
        logger.info("Testing end-to-end candidate flow with knowledge graph")
        
        candidate = {
            'id': 'integration_candidate',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        logger.info(f"Adding candidate: {candidate['id']} with skills {candidate['skills']}")
        
        # Add via knowledge graph
        candidate_id = self.kg.add_candidate(candidate)
        logger.info(f"Added candidate, returned ID: {candidate_id}")
        assert candidate_id == 'integration_candidate'
        
        # Retrieve via knowledge graph
        logger.info("Retrieving candidate from knowledge graph...")
        retrieved = self.kg.get_candidate('integration_candidate')
        logger.info(f"Retrieved candidate: {retrieved is not None}")
        assert retrieved is not None
        assert retrieved['skills'] == candidate['skills']
        logger.info(f"Retrieved skills match: {retrieved['skills']}")
        
        # Search via vector DB (should find the candidate)
        logger.info("Generating query embedding for search...")
        query_embedding = self.embedder.embed_candidate(candidate)
        logger.info(f"Query embedding shape: {query_embedding.shape}")
        
        logger.info("Searching for similar candidates (top_k=10)...")
        results = self.vector_db.search_similar_candidates(query_embedding, top_k=10)
        logger.info(f"Search returned {len(results)} results")
        
        if len(results) > 0:
            logger.info(f"Top 3 results: {[(r['profile_id'], r['similarity']) for r in results[:3]]}")
        
        # Should find our candidate
        found = any(r['profile_id'] == 'integration_candidate' for r in results)
        logger.info(f"Found our candidate in search results: {found}")
        if found:
            our_result = next(r for r in results if r['profile_id'] == 'integration_candidate')
            logger.info(f"Our candidate similarity: {our_result['similarity']:.4f}, rank: {results.index(our_result) + 1}")
        assert found, f"Should find candidate via vector search. Results: {[r['profile_id'] for r in results[:5]]}"
        
        logger.info("✅ End-to-end candidate test passed")
    
    def test_end_to_end_all_types(self):
        """Test end-to-end for all 4 profile types."""
        # Add all types
        candidate = {'id': 'c1', 'skills': ['Python']}
        team = {'id': 't1', 'name': 'Team 1', 'needs': ['Python']}
        interviewer = {'id': 'i1', 'name': 'Interviewer 1', 'expertise': ['Python']}
        position = {'id': 'p1', 'title': 'Position 1', 'must_haves': ['Python']}
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        self.kg.add_position(position)
        
        # Verify all can be retrieved
        assert self.kg.get_candidate('c1') is not None
        assert self.kg.get_team('t1') is not None
        assert self.kg.get_interviewer('i1') is not None
        assert self.kg.get_position('p1') is not None
        
        # Verify all can be searched
        c_emb = self.embedder.embed_candidate(candidate)
        t_emb = self.embedder.embed_team(team)
        i_emb = self.embedder.embed_interviewer(interviewer)
        p_emb = self.embedder.embed_position(position)
        
        c_results = self.vector_db.search_similar_candidates(c_emb, top_k=5)
        t_results = self.vector_db.search_similar_teams(t_emb, top_k=5)
        i_results = self.vector_db.search_similar_interviewers(i_emb, top_k=5)
        p_results = self.vector_db.search_similar_positions(p_emb, top_k=5)
        
        assert len(c_results) > 0
        assert len(t_results) > 0
        assert len(i_results) > 0
        assert len(p_results) > 0
    
    def test_update_triggers_re_embedding(self):
        """Test that updates trigger re-embedding."""
        candidate = {
            'id': 'update_embed_test',
            'skills': ['Python'],
            'experience_years': 3
        }
        self.kg.add_candidate(candidate)
        
        # Get original embedding
        original_emb = self.embedder.embed_candidate(candidate)
        
        # Update candidate
        self.kg.update_candidate('update_embed_test', {
            'skills': ['Python', 'CUDA', 'C++'],
            'experience_years': 5
        })
        
        # Get new embedding
        updated_candidate = self.kg.get_candidate('update_embed_test')
        new_emb = self.embedder.embed_candidate(updated_candidate)
        
        # Embeddings should be different
        assert not np.allclose(original_emb, new_emb), "Embeddings should differ after update"
        
        # New embedding should be searchable
        results = self.vector_db.search_similar_candidates(new_emb, top_k=5)
        found = any(r['profile_id'] == 'update_embed_test' for r in results)
        assert found, "Updated candidate should be findable via search"
    
    def test_relationships_with_embeddings(self):
        """Test that relationships work with embeddings."""
        team = {
            'id': 'rel_team',
            'name': 'Team',
            'member_ids': [],
            'member_count': 0
        }
        interviewer = {
            'id': 'rel_interviewer',
            'name': 'Interviewer',
            'team_id': None
        }
        
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        
        # Link them
        self.kg.link_interviewer_to_team('rel_interviewer', 'rel_team')
        
        # Verify both can still be searched
        updated_team = self.kg.get_team('rel_team')
        updated_interviewer = self.kg.get_interviewer('rel_interviewer')
        
        t_emb = self.embedder.embed_team(updated_team)
        i_emb = self.embedder.embed_interviewer(updated_interviewer)
        
        t_results = self.vector_db.search_similar_teams(t_emb, top_k=5)
        i_results = self.vector_db.search_similar_interviewers(i_emb, top_k=5)
        
        assert len(t_results) > 0
        assert len(i_results) > 0
    
    def test_batch_operations(self):
        """Test batch operations with multiple profiles."""
        # Add multiple candidates
        for i in range(5):
            candidate = {
                'id': f'batch_candidate_{i}',
                'skills': [f'Skill{i % 3}'],
                'experience_years': i
            }
            self.kg.add_candidate(candidate)
        
        # Verify all can be retrieved
        all_candidates = self.kg.get_all_candidates()
        batch_candidates = [c for c in all_candidates if c['id'].startswith('batch_candidate_')]
        assert len(batch_candidates) == 5
        
        # Verify all can be searched
        query_candidate = {'id': 'query', 'skills': ['Skill0']}
        query_emb = self.embedder.embed_candidate(query_candidate)
        results = self.vector_db.search_similar_candidates(query_emb, top_k=10)
        
        # Should find at least some of our batch candidates
        found_ids = [r['profile_id'] for r in results]
        batch_found = [id for id in found_ids if id.startswith('batch_candidate_')]
        assert len(batch_found) > 0, "Should find batch candidates via search"

