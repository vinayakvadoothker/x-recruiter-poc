"""
dataset_loader.py - Load datasets into knowledge graph with batch processing

This module provides utilities to load large-scale datasets into the knowledge graph
efficiently using batch processing for performance.

Why batch processing:
- Embedding generation is expensive (1,000+ profiles)
- Vector DB storage benefits from batching
- Memory efficiency for large datasets
- Progress tracking for long-running operations
"""

import logging
from typing import Optional, Iterator, Dict, Any
from backend.database.knowledge_graph import KnowledgeGraph
from .sample_candidates import generate_candidates
from .sample_teams import generate_teams
from .sample_interviewers import generate_interviewers
from .sample_positions import generate_positions

logger = logging.getLogger(__name__)


class DatasetLoader:
    """
    Load datasets into knowledge graph with batch processing.
    
    Handles efficient loading of large-scale datasets (3,300-5,000 profiles)
    with progress tracking and error handling.
    """
    
    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None):
        """
        Initialize dataset loader.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
    
    def load_candidates(self, count: int = 1500, batch_size: int = 100) -> int:
        """
        Load candidate profiles in batches.
        
        Args:
            count: Number of candidates to load
            batch_size: Batch size for processing
        
        Returns:
            Number of candidates loaded
        """
        logger.info(f"Loading {count} candidates in batches of {batch_size}")
        loaded = 0
        
        batch = []
        for candidate in generate_candidates(count):
            batch.append(candidate)
            
            if len(batch) >= batch_size:
                for c in batch:
                    try:
                        self.kg.add_candidate(c)
                        loaded += 1
                    except Exception as e:
                        logger.error(f"Failed to load candidate {c.get('id')}: {e}")
                batch = []
                
                if loaded % 500 == 0:
                    logger.info(f"Loaded {loaded}/{count} candidates")
        
        # Load remaining
        for c in batch:
            try:
                self.kg.add_candidate(c)
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load candidate {c.get('id')}: {e}")
        
        logger.info(f"Loaded {loaded} candidates")
        return loaded
    
    def load_teams(self, count: int = 800, batch_size: int = 50) -> int:
        """Load team profiles in batches."""
        logger.info(f"Loading {count} teams in batches of {batch_size}")
        loaded = 0
        
        batch = []
        for team in generate_teams(count):
            batch.append(team)
            
            if len(batch) >= batch_size:
                for t in batch:
                    try:
                        self.kg.add_team(t)
                        loaded += 1
                    except Exception as e:
                        logger.error(f"Failed to load team {t.get('id')}: {e}")
                batch = []
        
        for t in batch:
            try:
                self.kg.add_team(t)
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load team {t.get('id')}: {e}")
        
        logger.info(f"Loaded {loaded} teams")
        return loaded
    
    def load_interviewers(self, count: int = 1500, batch_size: int = 100) -> int:
        """Load interviewer profiles in batches."""
        logger.info(f"Loading {count} interviewers in batches of {batch_size}")
        loaded = 0
        
        batch = []
        for interviewer in generate_interviewers(count, teams_count=800):
            batch.append(interviewer)
            
            if len(batch) >= batch_size:
                for i in batch:
                    try:
                        self.kg.add_interviewer(i)
                        loaded += 1
                    except Exception as e:
                        logger.error(f"Failed to load interviewer {i.get('id')}: {e}")
                batch = []
        
        for i in batch:
            try:
                self.kg.add_interviewer(i)
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load interviewer {i.get('id')}: {e}")
        
        logger.info(f"Loaded {loaded} interviewers")
        return loaded
    
    def load_positions(self, count: int = 1200, batch_size: int = 100) -> int:
        """Load position profiles in batches."""
        logger.info(f"Loading {count} positions in batches of {batch_size}")
        loaded = 0
        
        batch = []
        for position in generate_positions(count, teams_count=800):
            batch.append(position)
            
            if len(batch) >= batch_size:
                for p in batch:
                    try:
                        self.kg.add_position(p)
                        loaded += 1
                    except Exception as e:
                        logger.error(f"Failed to load position {p.get('id')}: {e}")
                batch = []
        
        for p in batch:
            try:
                self.kg.add_position(p)
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load position {p.get('id')}: {e}")
        
        logger.info(f"Loaded {loaded} positions")
        return loaded
    
    def load_all(self, 
                 candidates: int = 1500,
                 teams: int = 800,
                 interviewers: int = 1500,
                 positions: int = 1200) -> Dict[str, int]:
        """
        Load all datasets.
        
        Args:
            candidates: Number of candidates
            teams: Number of teams
            interviewers: Number of interviewers
            positions: Number of positions
        
        Returns:
            Dictionary with counts of loaded profiles
        """
        logger.info("Loading all datasets...")
        
        # Load in order: teams first (for relationships), then others
        teams_loaded = self.load_teams(teams)
        candidates_loaded = self.load_candidates(candidates)
        interviewers_loaded = self.load_interviewers(interviewers)
        positions_loaded = self.load_positions(positions)
        
        total = teams_loaded + candidates_loaded + interviewers_loaded + positions_loaded
        logger.info(f"Loaded {total} total profiles")
        
        return {
            'candidates': candidates_loaded,
            'teams': teams_loaded,
            'interviewers': interviewers_loaded,
            'positions': positions_loaded,
            'total': total
        }
    
    def close(self):
        """Close knowledge graph connection."""
        self.kg.close()

