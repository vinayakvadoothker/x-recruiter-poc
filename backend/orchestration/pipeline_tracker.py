"""
pipeline_tracker.py - Pipeline tracking system for candidate-position relationships

This module manages the candidate pipeline, tracking candidates through stages
for each position they're interested in. Supports many-to-many relationships:
- One candidate can be in multiple positions' pipelines
- One position can have many candidates in its pipeline

Pipeline Stages:
1. dm_screening - DM sent, waiting for response
2. dm_screening_completed - DM responses received, screening score calculated
3. dm_screening_passed - Passed screening (score >= 0.5), ready for phone screen
4. dm_screening_failed - Failed screening (score < 0.5), rejected
5. phone_screen_scheduled - Phone screen call scheduled
6. phone_screen_completed - Phone screen completed, decision made
7. phone_screen_passed - Passed phone screen, ready for matching
8. phone_screen_failed - Failed phone screen, rejected
9. matched_to_team - Team matching completed
10. matched_to_interviewer - Interviewer matching completed
11. rejected - Rejected at any stage
12. accepted - Accepted (future: offer extended)
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context

logger = logging.getLogger(__name__)


class PipelineTracker:
    """
    Pipeline tracker for managing candidate progress through positions.
    
    Tracks many-to-many relationships: candidates ↔ positions
    Each candidate-position pair has its own pipeline state.
    """
    
    def __init__(self, postgres_client: Optional[PostgresClient] = None):
        """
        Initialize pipeline tracker.
        
        Args:
            postgres_client: PostgreSQL client instance (creates new if None)
        """
        self.postgres = postgres_client or PostgresClient()
        self.company_context = get_company_context()
    
    def enter_stage(
        self,
        candidate_id: str,
        position_id: str,
        stage: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Enter a new pipeline stage for a candidate-position pair.
        
        If there's an active stage, it will be exited (exited_at set) and
        a new stage entry created.
        
        Args:
            candidate_id: Candidate identifier
            position_id: Position ID
            stage: Stage name (e.g., "dm_screening")
            metadata: Optional stage-specific data (DM responses, scores, etc.)
        
        Returns:
            Pipeline stage ID
        """
        company_id = self.company_context.get_company_id()
        metadata = metadata or {}
        
        try:
            # Check if already in this stage (active or not - constraint applies to all)
            # The unique constraint is on (candidate_id, position_id, stage) regardless of exited_at
            existing = self.postgres.execute_one(
                """
                SELECT id, exited_at FROM pipeline_stages
                WHERE candidate_id = %s
                  AND position_id = %s
                  AND stage = %s
                  AND company_id = %s
                ORDER BY entered_at DESC
                LIMIT 1
                """,
                (candidate_id, position_id, stage, company_id)
            )
            
            if existing:
                # If it's active, just return it
                if not existing.get('exited_at'):
                    logger.info(
                        f"Candidate {candidate_id} already in stage '{stage}' for position {position_id}, skipping"
                    )
                    return existing['id']
                else:
                    # If it's exited, we can't re-enter due to unique constraint
                    # Instead, update the existing record to reactivate it
                    logger.info(
                        f"Reactivating exited stage '{stage}' for candidate {candidate_id} in position {position_id}"
                    )
                    self.postgres.execute_update(
                        """
                        UPDATE pipeline_stages
                        SET exited_at = NULL, entered_at = NOW(), updated_at = NOW(), metadata = %s::jsonb
                        WHERE id = %s AND company_id = %s
                        """,
                        (json.dumps(metadata) if metadata else None, existing['id'], company_id)
                    )
                    return existing['id']
            
            # First, exit any other active stage for this candidate-position pair
            self.postgres.execute_update(
                """
                UPDATE pipeline_stages
                SET exited_at = NOW(), updated_at = NOW()
                WHERE candidate_id = %s
                  AND position_id = %s
                  AND exited_at IS NULL
                  AND company_id = %s
                """,
                (candidate_id, position_id, company_id)
            )
            
            # Create new stage entry
            result = self.postgres.execute_one(
                """
                INSERT INTO pipeline_stages 
                    (company_id, candidate_id, position_id, stage, entered_at, metadata)
                VALUES (%s, %s, %s, %s, NOW(), %s::jsonb)
                RETURNING id
                """,
                (company_id, candidate_id, position_id, stage, json.dumps(metadata) if metadata else None)
            )
            
            stage_id = result['id'] if result else None
            logger.info(
                f"Entered stage '{stage}' for candidate {candidate_id} "
                f"in position {position_id} (stage_id: {stage_id})"
            )
            return stage_id
            
        except Exception as e:
            logger.error(f"Error entering stage: {e}")
            raise
    
    def get_current_stage(
        self,
        candidate_id: str,
        position_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current active stage for a candidate-position pair.
        
        Args:
            candidate_id: Candidate identifier
            position_id: Position ID
        
        Returns:
            Current stage dict with stage, entered_at, metadata, or None if not in pipeline
        """
        company_id = self.company_context.get_company_id()
        
        try:
            result = self.postgres.execute_one(
                """
                SELECT id, stage, entered_at, metadata, created_at
                FROM pipeline_stages
                WHERE candidate_id = %s
                  AND position_id = %s
                  AND exited_at IS NULL
                  AND company_id = %s
                ORDER BY entered_at DESC
                LIMIT 1
                """,
                (candidate_id, position_id, company_id)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting current stage: {e}")
            return None
    
    def get_candidates_in_pipeline(
        self,
        position_id: str,
        stage: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all candidates in a position's pipeline.
        
        Args:
            position_id: Position ID
            stage: Optional stage filter (if None, returns all active stages)
        
        Returns:
            List of candidate dicts with pipeline info (candidate data + stage info)
        """
        company_id = self.company_context.get_company_id()
        
        try:
            if stage:
                query = """
                    SELECT 
                        c.*,
                        ps.stage,
                        ps.entered_at as stage_entered_at,
                        ps.metadata as stage_metadata,
                        ps.id as pipeline_stage_id
                    FROM candidates c
                    JOIN pipeline_stages ps ON c.id = ps.candidate_id
                    WHERE ps.position_id = %s
                      AND ps.stage = %s
                      AND ps.exited_at IS NULL
                      AND ps.company_id = %s
                    ORDER BY ps.entered_at DESC
                """
                params = (position_id, stage, company_id)
            else:
                query = """
                    SELECT 
                        c.*,
                        ps.stage,
                        ps.entered_at as stage_entered_at,
                        ps.metadata as stage_metadata,
                        ps.id as pipeline_stage_id
                    FROM candidates c
                    JOIN pipeline_stages ps ON c.id = ps.candidate_id
                    WHERE ps.position_id = %s
                      AND ps.exited_at IS NULL
                      AND ps.company_id = %s
                    ORDER BY ps.entered_at DESC
                """
                params = (position_id, company_id)
            
            results = self.postgres.execute_query(query, params)
            return results or []
            
        except Exception as e:
            logger.error(f"Error getting candidates in pipeline: {e}")
            return []
    
    def get_positions_for_candidate(
        self,
        candidate_id: str,
        stage: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all positions a candidate is in pipeline for.
        
        Args:
            candidate_id: Candidate identifier
            stage: Optional stage filter (if None, returns all active stages)
        
        Returns:
            List of position dicts with pipeline info (position data + stage info)
        """
        company_id = self.company_context.get_company_id()
        
        try:
            if stage:
                query = """
                    SELECT 
                        p.*,
                        ps.stage,
                        ps.entered_at as stage_entered_at,
                        ps.metadata as stage_metadata,
                        ps.id as pipeline_stage_id
                    FROM positions p
                    JOIN pipeline_stages ps ON p.id = ps.position_id
                    WHERE ps.candidate_id = %s
                      AND ps.stage = %s
                      AND ps.exited_at IS NULL
                      AND ps.company_id = %s
                    ORDER BY ps.entered_at DESC
                """
                params = (candidate_id, stage, company_id)
            else:
                query = """
                    SELECT 
                        p.*,
                        ps.stage,
                        ps.entered_at as stage_entered_at,
                        ps.metadata as stage_metadata,
                        ps.id as pipeline_stage_id
                    FROM positions p
                    JOIN pipeline_stages ps ON p.id = ps.position_id
                    WHERE ps.candidate_id = %s
                      AND ps.exited_at IS NULL
                      AND ps.company_id = %s
                    ORDER BY ps.entered_at DESC
                """
                params = (candidate_id, company_id)
            
            results = self.postgres.execute_query(query, params)
            return results or []
            
        except Exception as e:
            logger.error(f"Error getting positions for candidate: {e}")
            return []
    
    def get_pipeline_history(
        self,
        candidate_id: str,
        position_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get full pipeline history for a candidate-position pair.
        
        Args:
            candidate_id: Candidate identifier
            position_id: Position ID
        
        Returns:
            List of stage transitions in chronological order
        """
        company_id = self.company_context.get_company_id()
        
        try:
            results = self.postgres.execute_query(
                """
                SELECT 
                    id,
                    stage,
                    entered_at,
                    exited_at,
                    metadata,
                    created_at
                FROM pipeline_stages
                WHERE candidate_id = %s
                  AND position_id = %s
                  AND company_id = %s
                ORDER BY entered_at ASC
                """,
                (candidate_id, position_id, company_id)
            )
            
            return results or []
            
        except Exception as e:
            logger.error(f"Error getting pipeline history: {e}")
            return []
    
    def transition_stage(
        self,
        candidate_id: str,
        position_id: str,
        new_stage: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Transition to a new stage (exits current, enters new).
        
        Args:
            candidate_id: Candidate identifier
            position_id: Position ID
            new_stage: New stage name
            metadata: Optional metadata for new stage
        
        Returns:
            New pipeline stage ID
        """
        return self.enter_stage(candidate_id, position_id, new_stage, metadata)
    
    def get_candidates_by_stage(
        self,
        stage: str
    ) -> List[Dict[str, Any]]:
        """
        Get all candidates at a specific stage across all positions.
        
        Args:
            stage: Stage name
        
        Returns:
            List of candidate dicts with position and stage info
        """
        company_id = self.company_context.get_company_id()
        
        try:
            results = self.postgres.execute_query(
                """
                SELECT 
                    c.*,
                    p.id as position_id,
                    p.title as position_title,
                    ps.stage,
                    ps.entered_at as stage_entered_at,
                    ps.metadata as stage_metadata,
                    ps.id as pipeline_stage_id
                FROM candidates c
                JOIN pipeline_stages ps ON c.id = ps.candidate_id
                JOIN positions p ON ps.position_id = p.id
                WHERE ps.stage = %s
                  AND ps.exited_at IS NULL
                  AND ps.company_id = %s
                ORDER BY ps.entered_at DESC
                """,
                (stage, company_id)
            )
            
            return results or []
            
        except Exception as e:
            logger.error(f"Error getting candidates by stage: {e}")
            return []

