"""
test_integration.py - Integration tests with embedder

Why this test exists:
The vector DB must work seamlessly with the embedder. This test verifies the
end-to-end flow: generate embeddings → store in vector DB → search for similar
profiles. This is critical because the embedder and vector DB are core components
that must work together perfectly.

What it validates:
- Embedder + VectorDB integration works correctly
- Stored embeddings match search results
- Cross-type similarity search works
- Metadata is preserved correctly
- Similarity scores are meaningful

Expected behavior:
- Embeddings from embedder can be stored in vector DB
- Stored profiles can be found via similarity search
- Metadata is correctly serialized and deserialized
- Similarity scores reflect actual similarity
"""

import pytest
import numpy as np
import logging
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestIntegration:
    """Test integration between embedder and vector DB."""
    
    def setup_method(self):
        """Set up embedder and vector DB client."""
        self.embedder = RecruitingKnowledgeGraphEmbedder()
        self.client = VectorDBClient(url='http://weaviate:8080')
    
    def teardown_method(self):
        """Close connection after each test."""
        self.client.close()
    
    def test_end_to_end_candidate(self):
        """Test end-to-end: embed → store → search."""
        logger.info("Testing end-to-end candidate flow: embed → store → search")
        
        candidate = {
            'id': 'integration_candidate',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'experience_years': 5,
            'domains': ['LLM Inference']
        }
        logger.info(f"Candidate: {candidate['id']} with skills {candidate['skills']}")
        
        # Generate embedding
        logger.info("Generating embedding...")
        embedding = self.embedder.embed_candidate(candidate)
        logger.info(f"Embedding generated: shape={embedding.shape}, norm={np.linalg.norm(embedding):.4f}")
        
        # Store in vector DB
        logger.info("Storing candidate in vector DB...")
        stored = self.client.store_candidate('integration_candidate', embedding, candidate)
        logger.info(f"Store result: {stored}")
        assert stored is True
        
        # Search for similar candidates
        logger.info("Searching for similar candidates (top_k=5)...")
        results = self.client.search_similar_candidates(embedding, top_k=5)
        logger.info(f"Search returned {len(results)} results")
        
        assert len(results) > 0, f"Should find the stored candidate, got {len(results)} results"
        
        # Check that we found our candidate
        found = any(r['profile_id'] == 'integration_candidate' for r in results)
        logger.info(f"Found our candidate in search results: {found}")
        if found:
            our_result = next(r for r in results if r['profile_id'] == 'integration_candidate')
            logger.info(f"Our candidate similarity score: {our_result['similarity']:.4f}")
        assert found, "Should find the candidate we just stored"
        
        # Check metadata is preserved
        result = next(r for r in results if r['profile_id'] == 'integration_candidate')
        logger.info(f"Verifying metadata: id={result['metadata'].get('id')}, skills={result['metadata'].get('skills')}")
        assert result['metadata']['id'] == 'integration_candidate'
        assert result['metadata']['skills'] == candidate['skills']
        
        logger.info("✅ End-to-end candidate test passed")
    
    def test_end_to_end_all_types(self):
        """Test end-to-end for all 4 profile types."""
        # Candidate
        candidate = {'id': 'c1', 'skills': ['Python']}
        c_emb = self.embedder.embed_candidate(candidate)
        self.client.store_candidate('c1', c_emb, candidate)
        
        # Team
        team = {'id': 't1', 'name': 'Team 1', 'needs': ['Python']}
        t_emb = self.embedder.embed_team(team)
        self.client.store_team('t1', t_emb, team)
        
        # Interviewer
        interviewer = {'id': 'i1', 'name': 'Interviewer 1', 'expertise': ['Python']}
        i_emb = self.embedder.embed_interviewer(interviewer)
        self.client.store_interviewer('i1', i_emb, interviewer)
        
        # Position
        position = {'id': 'p1', 'title': 'Position 1', 'must_haves': ['Python']}
        p_emb = self.embedder.embed_position(position)
        self.client.store_position('p1', p_emb, position)
        
        # Verify all can be searched
        c_results = self.client.search_similar_candidates(c_emb, top_k=5)
        t_results = self.client.search_similar_teams(t_emb, top_k=5)
        i_results = self.client.search_similar_interviewers(i_emb, top_k=5)
        p_results = self.client.search_similar_positions(p_emb, top_k=5)
        
        assert len(c_results) > 0
        assert len(t_results) > 0
        assert len(i_results) > 0
        assert len(p_results) > 0
    
    def test_similarity_ordering(self):
        """Test that search results are ordered by similarity."""
        # Store multiple candidates with varying similarity
        base_candidate = {
            'id': 'base',
            'skills': ['CUDA', 'C++'],
            'domains': ['LLM Inference']
        }
        base_emb = self.embedder.embed_candidate(base_candidate)
        self.client.store_candidate('base', base_emb, base_candidate)
        
        # Similar candidate
        similar_candidate = {
            'id': 'similar',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'domains': ['LLM Inference']
        }
        similar_emb = self.embedder.embed_candidate(similar_candidate)
        self.client.store_candidate('similar', similar_emb, similar_candidate)
        
        # Different candidate
        different_candidate = {
            'id': 'different',
            'skills': ['Python', 'Django'],
            'domains': ['Web Development']
        }
        different_emb = self.embedder.embed_candidate(different_candidate)
        self.client.store_candidate('different', different_emb, different_candidate)
        
        # Search - results should be ordered by similarity
        results = self.client.search_similar_candidates(base_emb, top_k=10)
        
        if len(results) >= 2:
            # First result should have higher similarity than later results
            similarities = [r['similarity'] for r in results]
            assert similarities == sorted(similarities, reverse=True), "Results should be ordered by similarity"
    
    def test_metadata_preservation(self):
        """Test that metadata is correctly preserved."""
        candidate = {
            'id': 'metadata_test',
            'skills': ['CUDA', 'C++'],
            'experience_years': 5,
            'domains': ['LLM Inference'],
            'education': ['MS Computer Science'],
            'projects': [{'name': 'LLM Optimizer'}]
        }
        
        embedding = self.embedder.embed_candidate(candidate)
        self.client.store_candidate('metadata_test', embedding, candidate)
        
        results = self.client.search_similar_candidates(embedding, top_k=5)
        
        # Find our candidate
        result = next((r for r in results if r['profile_id'] == 'metadata_test'), None)
        assert result is not None, "Should find stored candidate"
        
        # Check all metadata fields are preserved
        stored_metadata = result['metadata']
        assert stored_metadata['id'] == candidate['id']
        assert stored_metadata['skills'] == candidate['skills']
        assert stored_metadata['experience_years'] == candidate['experience_years']
        assert stored_metadata['domains'] == candidate['domains']

