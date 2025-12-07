# Database Module

This module handles vector database operations for storing embeddings and metadata.

**Note**: This module is being refactored as part of the pivot. Neo4j has been replaced with Weaviate (vector database).

## Current Status

- ✅ Neo4j files removed (replaced with vector DB)
- 🚧 Vector DB client (coming in Phase 3)
- 🚧 Knowledge graph abstraction (coming in Phase 4)

## Future Components

### `vector_db_client.py` (Phase 3)
Weaviate client for storing embeddings and fast similarity search.

### `knowledge_graph.py` (Phase 4)
Knowledge graph abstraction for managing 4 profile types:
- Candidates
- Teams
- Interviewers
- Positions
