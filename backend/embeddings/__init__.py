"""
embeddings - Specialized embedder for recruiting knowledge graph

This module provides domain-specific embeddings for 4 profile types:
- Candidate profiles
- Team profiles
- Interviewer profiles
- Position profiles

Key module:
- recruiting_embedder: Main embedder class with specialized formatting

Implementation Rationale:

Why a separate embeddings module:
1. **Separation of concerns**: Embeddings are a distinct layer from database/storage
   - Alternative: Embedding logic in database module - Rejected because:
     * Embeddings are used by multiple components (matching, similarity search, bandits)
     * Database module should focus on storage/retrieval, not computation
     * Easier to test embeddings independently
   - Trade-off: Slight import overhead, but better modularity

2. **Single responsibility**: Module only handles embedding generation
   - Alternative: Combine with knowledge graph or vector DB - Rejected because:
     * Embeddings can be generated without storing them (for similarity computation)
     * Vector DB should focus on storage/retrieval, not generation
     * Knowledge graph should focus on relationships, not embeddings
   - Trade-off: More files to manage, but clearer boundaries

3. **Future extensibility**: Easy to add new embedding methods or models
   - Alternative: Hardcode embedding logic in each component - Rejected because:
     * Would duplicate code across multiple files
     * Harder to update embedding approach globally
     * Can't easily swap models or add new profile types
   - Trade-off: Extra abstraction layer, but enables flexibility

Design Decisions:
- **Module structure**: Single class (RecruitingKnowledgeGraphEmbedder) exports all methods
  - Why: All 4 profile types use same model, just different formatting
  - Alternative: Separate classes per profile type - Rejected for simplicity
- **Public API**: Only export the main class, not internal formatting methods
  - Why: Formatting methods are implementation details
  - Alternative: Export everything - Rejected to keep API clean
"""

from backend.embeddings.recruiting_embedder import RecruitingKnowledgeGraphEmbedder

__all__ = ['RecruitingKnowledgeGraphEmbedder']

