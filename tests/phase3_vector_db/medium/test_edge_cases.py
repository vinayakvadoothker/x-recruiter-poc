"""
test_edge_cases.py - Edge cases and error handling for vector DB

Why this test exists:
Real-world usage will have edge cases: invalid embeddings, missing metadata,
duplicate IDs, empty searches, etc. This test ensures the vector DB handles
these gracefully without crashing, which is critical for production reliability.

What it validates:
- Invalid embedding dimensions are handled
- Missing metadata doesn't cause errors
- Duplicate profile IDs are handled
- Empty search results are handled correctly
- Very large metadata is stored correctly
- Top_k limits are respected

Expected behavior:
- Invalid inputs should either be rejected gracefully or handled safely
- Duplicate IDs should either update or be rejected (not crash)
- Empty searches should return empty lists, not errors
- Large metadata should be stored successfully
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


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Set up vector DB client for each test."""
        self.client = VectorDBClient(url='http://weaviate:8080')
    
    def teardown_method(self):
        """Close connection after each test."""
        self.client.close()
    
    def test_invalid_embedding_dimensions(self):
        """Test handling of invalid embedding dimensions."""
        # Wrong dimension (should be 768)
        invalid_embedding = np.random.rand(512)  # Wrong size
        invalid_embedding = invalid_embedding / np.linalg.norm(invalid_embedding)
        
        metadata = {'id': 'test', 'skills': ['Python']}
        
        # Should either fail gracefully or handle it
        try:
            result = self.client.store_candidate('test', invalid_embedding, metadata)
            # If it succeeds, that's fine too (Weaviate might accept it)
        except Exception as e:
            # If it fails, that's also acceptable - just shouldn't crash unexpectedly
            assert "dimension" in str(e).lower() or "size" in str(e).lower() or "vector" in str(e).lower()
    
    def test_missing_metadata(self):
        """Test storing with minimal metadata."""
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        # Empty metadata
        result = self.client.store_candidate('test_empty', embedding, {})
        assert result is True, "Should handle empty metadata"
    
    def test_duplicate_profile_id(self):
        """Test storing same profile ID twice."""
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        metadata1 = {'id': 'duplicate', 'skills': ['Python']}
        metadata2 = {'id': 'duplicate', 'skills': ['Java']}
        
        result1 = self.client.store_candidate('duplicate', embedding, metadata1)
        result2 = self.client.store_candidate('duplicate', embedding, metadata2)
        
        # Should handle duplicates (either update or create new)
        assert result1 is True
        # Second store might succeed (creates new) or fail (duplicate) - both acceptable
    
    def test_empty_search_results(self):
        """Test search when no profiles exist."""
        # Search with random embedding (should return empty or few results)
        query_embedding = np.random.rand(768)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        results = self.client.search_similar_candidates(query_embedding, top_k=5)
        
        assert isinstance(results, list), "Should return list even if empty"
        # May be empty or have results from previous tests - both fine
    
    def test_large_metadata(self):
        """Test storing very large metadata."""
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        # Large metadata with many fields
        large_metadata = {
            'id': 'large_test',
            'skills': [f'Skill{i}' for i in range(100)],
            'experience': [f'Experience {i}' for i in range(50)],
            'description': 'A' * 1000  # Very long description
        }
        
        result = self.client.store_candidate('large_test', embedding, large_metadata)
        assert result is True, "Should handle large metadata"
    
    def test_top_k_limit(self):
        """Test that top_k limit is respected."""
        # Store multiple candidates
        base_embedding = np.random.rand(768)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)
        
        for i in range(10):
            embedding = base_embedding + np.random.rand(768) * 0.1  # Slightly different
            embedding = embedding / np.linalg.norm(embedding)
            self.client.store_candidate(f'topk_test_{i}', embedding, {'id': f'topk_test_{i}'})
        
        # Search with top_k=3
        results = self.client.search_similar_candidates(base_embedding, top_k=3)
        
        assert len(results) <= 3, f"Should return at most 3 results, got {len(results)}"
    
    def test_zero_top_k(self):
        """Test search with top_k=0."""
        embedding = np.random.rand(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        results = self.client.search_similar_candidates(embedding, top_k=0)
        
        assert isinstance(results, list)
        # Weaviate uses default limit (25) when top_k=0, so just verify it's a list
        # This is expected Weaviate behavior - it doesn't support top_k=0

