"""
kg_relationships.py - Relationship handling for knowledge graph

This module handles relationships between profiles (e.g., team members,
position assignments). Separated from knowledge_graph.py to keep files under 200 lines.

Implementation Rationale:

Why separate relationships module:
- Relationship logic is independent of CRUD operations
- Can be extended with more relationship types without bloating main class
- Easier to test relationship handling separately
- Follows single responsibility principle
"""

import logging
from typing import Dict, List, Any, Optional
from backend.database.kg_crud import KnowledgeGraphCRUD

logger = logging.getLogger(__name__)


class KnowledgeGraphRelationships:
    """
    Relationship management for knowledge graph.
    
    Handles connections between profiles: team members, position assignments, etc.
    """
    
    def __init__(self, crud: KnowledgeGraphCRUD):
        """
        Initialize relationship manager.
        
        Args:
            crud: CRUD operations instance
        """
        self.crud = crud
    
    def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get all interviewers in a team.
        
        Args:
            team_id: Team ID
        
        Returns:
            List of interviewer profiles
        """
        team = self.crud.get_team(team_id)
        if not team:
            return []
        member_ids = team.get('member_ids', [])
        return [self.crud.get_interviewer(id) for id in member_ids 
                if self.crud.get_interviewer(id)]
    
    def get_team_positions(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get all positions for a team.
        
        Args:
            team_id: Team ID
        
        Returns:
            List of position profiles
        """
        team = self.crud.get_team(team_id)
        if not team:
            return []
        position_ids = team.get('open_positions', [])
        return [self.crud.get_position(id) for id in position_ids 
                if self.crud.get_position(id)]
    
    def link_interviewer_to_team(self, interviewer_id: str, team_id: str) -> bool:
        """
        Link interviewer to team.
        
        Updates both interviewer and team metadata, re-embeds both.
        
        Args:
            interviewer_id: Interviewer ID
            team_id: Team ID
        
        Returns:
            True if successful
        """
        interviewer = self.crud.get_interviewer(interviewer_id)
        team = self.crud.get_team(team_id)
        if not interviewer or not team:
            return False
        
        # Update interviewer
        interviewer['team_id'] = team_id
        
        # Update team member list
        member_ids = team.get('member_ids', [])
        if interviewer_id not in member_ids:
            member_ids.append(interviewer_id)
            team['member_ids'] = member_ids
            team['member_count'] = len(member_ids)
        
        # Re-embed both (relationships affect embeddings)
        self.crud.update_interviewer(interviewer_id, {'team_id': team_id})
        self.crud.update_team(team_id, {
            'member_ids': member_ids,
            'member_count': len(member_ids)
        })
        logger.debug(f"Linked interviewer {interviewer_id} to team {team_id}")
        return True

