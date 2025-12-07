"""
knowledge_graph.py - Knowledge graph abstraction for recruiting domain

This module provides a high-level abstraction over the vector DB and embedder,
managing all 4 profile types (candidates, teams, interviewers, positions) with
automatic embedding generation and relationship handling.

Implementation Rationale:

Why this abstraction layer:
1. **Simplifies API**: Higher-level operations (add/get/update) vs low-level vector operations
   - Alternative: Direct vector DB usage - Rejected because:
     * Requires manual embedding generation for every operation
     * No relationship management
     * More complex code for common operations
   - Our approach: Single method calls handle embedding + storage + metadata

2. **Metadata + Embeddings**: Separate storage for full data vs vectors
   - Alternative: Store everything in vector DB - Rejected because:
     * Vector DB metadata is limited (JSON strings)
     * Harder to query/update specific fields
     * No relationship queries
   - Our approach: Vector DB for similarity search, in-memory dict for full data

3. **Relationship Management**: Track connections between profiles
   - Alternative: No relationship tracking - Rejected because:
     * Need to find team members, candidate positions, etc.
     * Relationships are key for matching
   - Our approach: Store relationship IDs in metadata, provide helper methods

4. **Automatic Embedding**: Generate embeddings on add/update
   - Alternative: Manual embedding generation - Rejected because:
     * Error-prone (forget to embed)
     * Inconsistent (some profiles embedded, some not)
   - Our approach: Always generate embeddings when adding/updating

Design Decisions:
- **In-memory metadata store**: Fast for MVP, can upgrade to PostgreSQL later
- **Separate methods per profile type**: Clear API, type-safe
- **Relationship helpers**: get_team_members(), get_position_candidates(), etc.
- **Update triggers re-embedding**: Ensures embeddings stay in sync with data
- **Modular design**: CRUD and relationships split into separate modules
"""

from typing import Dict, Optional
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder
from backend.database.kg_crud import KnowledgeGraphCRUD
from backend.database.kg_relationships import KnowledgeGraphRelationships


class KnowledgeGraph:
    """
    Knowledge graph abstraction for recruiting domain.
    
    Handles 4 profile types: Candidates, Teams, Interviewers, Positions
    Uses vector DB for embeddings, in-memory dict for metadata.
    Automatically generates embeddings when adding/updating profiles.
    """
    
    def __init__(self, 
                 vector_db: Optional[VectorDBClient] = None,
                 embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None,
                 url: Optional[str] = None):
        """
        Initialize knowledge graph.
        
        Args:
            vector_db: Vector DB client (defaults to new instance)
            embedder: Embedder instance (defaults to new instance)
            url: Weaviate URL (used if vector_db is None)
        """
        self.vector_db = vector_db or VectorDBClient(url=url)
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.metadata_store: Dict[str, Dict] = {}
        
        # Initialize CRUD and relationships
        self.crud = KnowledgeGraphCRUD(self.vector_db, self.embedder, self.metadata_store)
        self.relationships = KnowledgeGraphRelationships(self.crud)
    
    # Delegate all methods to CRUD and relationships
    # Candidates
    def add_candidate(self, candidate_data: Dict) -> str:
        return self.crud.add_candidate(candidate_data)
    
    def get_candidate(self, candidate_id: str) -> Optional[Dict]:
        return self.crud.get_candidate(candidate_id)
    
    def get_all_candidates(self):
        return self.crud.get_all_candidates()
    
    def update_candidate(self, candidate_id: str, updates: Dict) -> bool:
        return self.crud.update_candidate(candidate_id, updates)
    
    # Teams
    def add_team(self, team_data: Dict) -> str:
        return self.crud.add_team(team_data)
    
    def get_team(self, team_id: str) -> Optional[Dict]:
        return self.crud.get_team(team_id)
    
    def get_all_teams(self):
        return self.crud.get_all_teams()
    
    def update_team(self, team_id: str, updates: Dict) -> bool:
        return self.crud.update_team(team_id, updates)
    
    def get_team_members(self, team_id: str):
        return self.relationships.get_team_members(team_id)
    
    def get_team_positions(self, team_id: str):
        return self.relationships.get_team_positions(team_id)
    
    # Interviewers
    def add_interviewer(self, interviewer_data: Dict) -> str:
        return self.crud.add_interviewer(interviewer_data)
    
    def get_interviewer(self, interviewer_id: str) -> Optional[Dict]:
        return self.crud.get_interviewer(interviewer_id)
    
    def get_all_interviewers(self):
        return self.crud.get_all_interviewers()
    
    def update_interviewer(self, interviewer_id: str, updates: Dict) -> bool:
        return self.crud.update_interviewer(interviewer_id, updates)
    
    # Positions
    def add_position(self, position_data: Dict) -> str:
        return self.crud.add_position(position_data)
    
    def get_position(self, position_id: str) -> Optional[Dict]:
        return self.crud.get_position(position_id)
    
    def get_all_positions(self):
        return self.crud.get_all_positions()
    
    def update_position(self, position_id: str, updates: Dict) -> bool:
        return self.crud.update_position(position_id, updates)
    
    # Relationships
    def link_interviewer_to_team(self, interviewer_id: str, team_id: str) -> bool:
        return self.relationships.link_interviewer_to_team(interviewer_id, team_id)
    
    def close(self):
        """Close vector DB connection."""
        self.vector_db.close()

