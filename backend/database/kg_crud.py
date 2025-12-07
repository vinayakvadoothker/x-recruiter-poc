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
                 metadata_store: Dict[str, Dict[str, Any]]):
        """
        Initialize CRUD operations.
        
        Args:
            vector_db: Vector DB client
            embedder: Embedder instance
            metadata_store: Shared metadata store dictionary
        """
        self.vector_db = vector_db
        self.embedder = embedder
        self.metadata_store = metadata_store
    
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
        """Add team with automatic embedding."""
        team_id = team_data['id']
        embedding = self.embedder.embed_team(team_data)
        self.vector_db.store_team(team_id, embedding, team_data)
        self.metadata_store[f"team:{team_id}"] = team_data
        logger.debug(f"Added team: {team_id}")
        return team_id
    
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID."""
        return self.metadata_store.get(f"team:{team_id}")
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all teams."""
        return [v for k, v in self.metadata_store.items() if k.startswith("team:")]
    
    def update_team(self, team_id: str, updates: Dict[str, Any]) -> bool:
        """Update team and re-embed."""
        team = self.get_team(team_id)
        if not team:
            return False
        team.update(updates)
        embedding = self.embedder.embed_team(team)
        self.vector_db.store_team(team_id, embedding, team)
        self.metadata_store[f"team:{team_id}"] = team
        return True
    
    # ========== Interviewer CRUD ==========
    
    def add_interviewer(self, interviewer_data: Dict[str, Any]) -> str:
        """Add interviewer with automatic embedding."""
        interviewer_id = interviewer_data['id']
        embedding = self.embedder.embed_interviewer(interviewer_data)
        self.vector_db.store_interviewer(interviewer_id, embedding, interviewer_data)
        self.metadata_store[f"interviewer:{interviewer_id}"] = interviewer_data
        logger.debug(f"Added interviewer: {interviewer_id}")
        return interviewer_id
    
    def get_interviewer(self, interviewer_id: str) -> Optional[Dict[str, Any]]:
        """Get interviewer by ID."""
        return self.metadata_store.get(f"interviewer:{interviewer_id}")
    
    def get_all_interviewers(self) -> List[Dict[str, Any]]:
        """Get all interviewers."""
        return [v for k, v in self.metadata_store.items() if k.startswith("interviewer:")]
    
    def update_interviewer(self, interviewer_id: str, updates: Dict[str, Any]) -> bool:
        """Update interviewer and re-embed."""
        interviewer = self.get_interviewer(interviewer_id)
        if not interviewer:
            return False
        interviewer.update(updates)
        embedding = self.embedder.embed_interviewer(interviewer)
        self.vector_db.store_interviewer(interviewer_id, embedding, interviewer)
        self.metadata_store[f"interviewer:{interviewer_id}"] = interviewer
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

