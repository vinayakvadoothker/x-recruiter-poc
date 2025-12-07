"""
kg_crud.py - CRUD operations for knowledge graph profiles

This module contains the core CRUD (Create, Read, Update) operations for all
4 profile types. Separated from knowledge_graph.py to keep files under 200 lines.

Implementation Rationale:

Why separate CRUD module:
- Keeps knowledge_graph.py focused on high-level orchestration
- CRUD operations are independent and can be tested separately
- Easier to maintain and understand
- Follows single responsibility principle
"""

import logging
from typing import Dict, List, Any, Optional
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder
from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context

logger = logging.getLogger(__name__)


class KnowledgeGraphCRUD:
    """
    CRUD operations for knowledge graph profiles.
    
    Handles add/get/update operations for all 4 profile types with
    automatic embedding generation.
    """
    
    def __init__(self,
                 vector_db: VectorDBClient,
                 embedder: RecruitingKnowledgeGraphEmbedder,
                 metadata_store: Dict[str, Dict[str, Any]],
                 postgres_client: Optional[PostgresClient] = None):
        """
        Initialize CRUD operations.
        
        Args:
            vector_db: Vector DB client
            embedder: Embedder instance
            metadata_store: Shared metadata store dictionary (for candidates only)
            postgres_client: PostgreSQL client (for teams/interviewers/positions - source of truth)
        """
        self.vector_db = vector_db
        self.embedder = embedder
        self.metadata_store = metadata_store
        self.postgres_client = postgres_client
        self.company_context = get_company_context()
    
    # ========== Candidate CRUD ==========
    
    def add_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Add candidate with automatic embedding."""
        candidate_id = candidate_data['id']
        embedding = self.embedder.embed_candidate(candidate_data)
        self.vector_db.store_candidate(candidate_id, embedding, candidate_data)
        self.metadata_store[f"candidate:{candidate_id}"] = candidate_data
        logger.debug(f"Added candidate: {candidate_id}")
        return candidate_id
    
    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get candidate by ID."""
        return self.metadata_store.get(f"candidate:{candidate_id}")
    
    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates."""
        return [v for k, v in self.metadata_store.items() if k.startswith("candidate:")]
    
    def update_candidate(self, candidate_id: str, updates: Dict[str, Any]) -> bool:
        """Update candidate and re-embed."""
        candidate = self.get_candidate(candidate_id)
        if not candidate:
            return False
        candidate.update(updates)
        embedding = self.embedder.embed_candidate(candidate)
        self.vector_db.store_candidate(candidate_id, embedding, candidate)
        self.metadata_store[f"candidate:{candidate_id}"] = candidate
        return True
    
    # ========== Team CRUD ==========
    
    def add_team(self, team_data: Dict[str, Any]) -> str:
        """Add team with automatic embedding (stores in Weaviate only, PostgreSQL is source of truth)."""
        team_id = team_data['id']
        embedding = self.embedder.embed_team(team_data)
        self.vector_db.store_team(team_id, embedding, team_data)
        # Don't store in metadata_store - PostgreSQL is source of truth
        logger.debug(f"Added team to Weaviate: {team_id}")
        return team_id
    
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID from PostgreSQL (source of truth)."""
        if not self.postgres_client:
            logger.warning("PostgreSQL client not available, cannot fetch team")
            return None
        
        company_id = self.company_context.get_company_id()
        team = self.postgres_client.execute_one(
            "SELECT * FROM teams WHERE id = %s AND company_id = %s",
            (team_id, company_id)
        )
        
        if team:
            # Convert to dict format
            return dict(team)
        return None
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all teams from PostgreSQL (source of truth)."""
        if not self.postgres_client:
            logger.warning("PostgreSQL client not available, cannot fetch teams")
            return []
        
        company_id = self.company_context.get_company_id()
        teams = self.postgres_client.execute_query(
            "SELECT * FROM teams WHERE company_id = %s ORDER BY created_at DESC",
            (company_id,)
        )
        
        return [dict(team) for team in teams]
    
    def update_team(self, team_id: str, updates: Dict[str, Any]) -> bool:
        """Update team and re-embed (PostgreSQL is source of truth, update Weaviate embeddings)."""
        # Get current team from PostgreSQL
        team = self.get_team(team_id)
        if not team:
            return False
        
        # Merge updates
        team.update(updates)
        
        # Re-embed and update Weaviate
        embedding = self.embedder.embed_team(team)
        self.vector_db.store_team(team_id, embedding, team)
        
        # Note: PostgreSQL update should be done by API routes, not here
        # This method only updates Weaviate embeddings
        logger.debug(f"Updated team embeddings in Weaviate: {team_id}")
        return True
    
    # ========== Interviewer CRUD ==========
    
    def add_interviewer(self, interviewer_data: Dict[str, Any]) -> str:
        """Add interviewer with automatic embedding (stores in Weaviate only, PostgreSQL is source of truth)."""
        interviewer_id = interviewer_data['id']
        embedding = self.embedder.embed_interviewer(interviewer_data)
        self.vector_db.store_interviewer(interviewer_id, embedding, interviewer_data)
        # Don't store in metadata_store - PostgreSQL is source of truth
        logger.debug(f"Added interviewer to Weaviate: {interviewer_id}")
        return interviewer_id
    
    def get_interviewer(self, interviewer_id: str) -> Optional[Dict[str, Any]]:
        """Get interviewer by ID from PostgreSQL (source of truth)."""
        if not self.postgres_client:
            logger.warning("PostgreSQL client not available, cannot fetch interviewer")
            return None
        
        company_id = self.company_context.get_company_id()
        interviewer = self.postgres_client.execute_one(
            "SELECT * FROM interviewers WHERE id = %s AND company_id = %s",
            (interviewer_id, company_id)
        )
        
        if interviewer:
            # Convert to dict format
            return dict(interviewer)
        return None
    
    def get_all_interviewers(self) -> List[Dict[str, Any]]:
        """Get all interviewers from PostgreSQL (source of truth)."""
        if not self.postgres_client:
            logger.warning("PostgreSQL client not available, cannot fetch interviewers")
            return []
        
        company_id = self.company_context.get_company_id()
        interviewers = self.postgres_client.execute_query(
            "SELECT * FROM interviewers WHERE company_id = %s ORDER BY created_at DESC",
            (company_id,)
        )
        
        return [dict(interviewer) for interviewer in interviewers]
    
    def update_interviewer(self, interviewer_id: str, updates: Dict[str, Any]) -> bool:
        """Update interviewer and re-embed (PostgreSQL is source of truth, update Weaviate embeddings)."""
        # Get current interviewer from PostgreSQL
        interviewer = self.get_interviewer(interviewer_id)
        if not interviewer:
            return False
        
        # Merge updates
        interviewer.update(updates)
        
        # Re-embed and update Weaviate
        embedding = self.embedder.embed_interviewer(interviewer)
        self.vector_db.store_interviewer(interviewer_id, embedding, interviewer)
        
        # Note: PostgreSQL update should be done by API routes, not here
        # This method only updates Weaviate embeddings
        logger.debug(f"Updated interviewer embeddings in Weaviate: {interviewer_id}")
        return True
    
    # ========== Position CRUD ==========
    
    def add_position(self, position_data: Dict[str, Any]) -> str:
        """Add position with automatic embedding."""
        position_id = position_data['id']
        embedding = self.embedder.embed_position(position_data)
        self.vector_db.store_position(position_id, embedding, position_data)
        self.metadata_store[f"position:{position_id}"] = position_data
        logger.debug(f"Added position: {position_id}")
        return position_id
    
    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position by ID."""
        return self.metadata_store.get(f"position:{position_id}")
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        return [v for k, v in self.metadata_store.items() if k.startswith("position:")]
    
    def update_position(self, position_id: str, updates: Dict[str, Any]) -> bool:
        """Update position and re-embed."""
        position = self.get_position(position_id)
        if not position:
            return False
        position.update(updates)
        embedding = self.embedder.embed_position(position)
        self.vector_db.store_position(position_id, embedding, position)
        self.metadata_store[f"position:{position_id}"] = position
        return True

