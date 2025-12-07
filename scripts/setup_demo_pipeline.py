#!/usr/bin/env python3
"""
setup_demo_pipeline.py - Setup demo pipeline with candidate-position matches

This script:
1. Loads all positions from data/positions.json
2. Matches each candidate to 4 positions (good match, bad match, maybe, on fence)
3. Creates pipeline entries for all candidates
4. Passes top 10% candidates for each position to phone_screen_passed stage
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.postgres_client import PostgresClient
from backend.database.knowledge_graph import KnowledgeGraph
from backend.orchestration.pipeline_tracker import PipelineTracker
from backend.embeddings.recruiting_embedder import RecruitingKnowledgeGraphEmbedder
from backend.orchestration.company_context import get_company_context
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(vec1, vec2))


def calculate_match_score(candidate: Dict, position: Dict, embedder=None) -> float:
    """Calculate match score between candidate and position (fast version without embeddings)."""
    # Fast matching without embeddings - use skill/domain overlap
    candidate_skills = set(candidate.get('skills', []))
    position_skills = set(position.get('tech_stack', []) or position.get('skills', []) or [])
    position_requirements = set(position.get('requirements', []) or [])
    
    # Skill overlap
    skill_overlap = len(candidate_skills & position_skills) / max(len(position_skills), 1) if position_skills else 0.5
    requirement_match = len(candidate_skills & position_requirements) / max(len(position_requirements), 1) if position_requirements else 0.5
    
    # Domain overlap
    candidate_domains = set(candidate.get('domains', []))
    position_domains = set(position.get('domains', []) or [])
    domain_overlap = len(candidate_domains & position_domains) / max(len(position_domains), 1) if position_domains else 0.5
    
    # Experience level match
    candidate_level = candidate.get('expertise_level', 'Mid')
    position_level = position.get('experience_level', 'Mid')
    level_match = 1.0 if candidate_level == position_level else 0.7
    
    # Weighted score (no embedding similarity for speed)
    score = (
        skill_overlap * 0.40 +
        requirement_match * 0.30 +
        domain_overlap * 0.20 +
        level_match * 0.10
    )
    
    # Add some randomness for variety
    import random
    score += random.uniform(-0.1, 0.1)
    return max(0.0, min(1.0, score))


def match_candidates_to_positions():
    """Match each candidate to 4 positions with different match qualities."""
    logger.info("=" * 60)
    logger.info("SETTING UP DEMO PIPELINE")
    logger.info("=" * 60)
    
    # Load data
    data_dir = Path("data")
    positions_file = data_dir / "positions.json"
    candidates_file = data_dir / "candidates.json"
    
    if not positions_file.exists():
        logger.error(f"Positions file not found: {positions_file}")
        return
    
    if not candidates_file.exists():
        logger.error(f"Candidates file not found: {candidates_file}")
        return
    
    logger.info("Loading positions and candidates...")
    with open(positions_file, 'r') as f:
        positions = json.load(f)
    
    with open(candidates_file, 'r') as f:
        candidates = json.load(f)
    
    logger.info(f"Loaded {len(positions)} positions and {len(candidates)} candidates")
    
    # Initialize services
    postgres = PostgresClient()
    kg = KnowledgeGraph()
    pipeline = PipelineTracker(postgres)
    embedder = RecruitingKnowledgeGraphEmbedder()
    company_context = get_company_context()
    company_id = company_context.get_company_id()
    
    # Ensure all positions are in PostgreSQL
    logger.info("Ensuring all positions are in PostgreSQL...")
    for position in positions:
        position_id = position.get('id')
        existing = postgres.execute_one(
            "SELECT id FROM positions WHERE id = %s AND company_id = %s",
            (position_id, company_id)
        )
        if not existing:
            # Insert position
            postgres.execute_update(
                """
                INSERT INTO positions (
                    id, company_id, title, team_id, description,
                    requirements, responsibilities, tech_stack, domains,
                    experience_level, status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                )
                """,
                (
                    position_id, company_id,
                    position.get('title'),
                    position.get('team_id'),
                    position.get('description'),
                    position.get('requirements', []),  # TEXT[]
                    position.get('responsibilities', []),  # TEXT[]
                    position.get('tech_stack', []) or position.get('skills', []),  # TEXT[]
                    position.get('domains', []),  # TEXT[]
                    position.get('experience_level', 'Mid'),
                    'open'
                )
            )
    
    # Get all candidates from PostgreSQL
    logger.info("Getting candidates from database...")
    db_candidates = postgres.execute_query(
        "SELECT id, name, skills, domains, experience_years, expertise_level FROM candidates WHERE company_id = %s LIMIT 1000",
        (company_id,)
    )
    logger.info(f"Found {len(db_candidates)} candidates in database")
    
    # Convert to candidate dicts for matching
    candidates_dict = {}
    for c in db_candidates:
        import json as json_module
        candidates_dict[c['id']] = {
            'id': c['id'],
            'name': c.get('name', ''),
            'skills': json_module.loads(c.get('skills', '[]')) if isinstance(c.get('skills'), str) else c.get('skills', []),
            'domains': json_module.loads(c.get('domains', '[]')) if isinstance(c.get('domains'), str) else c.get('domains', []),
            'experience_years': c.get('experience_years', 0),
            'expertise_level': c.get('expertise_level', 'Mid')
        }
    
    candidate_ids = list(candidates_dict.keys())
    
    # Calculate match scores for all candidate-position pairs
    logger.info("Calculating match scores...")
    all_matches = []
    for candidate_id in candidate_ids:
        candidate = candidates_dict[candidate_id]
        
        for position in positions:
            score = calculate_match_score(candidate, position)  # No embedder for speed
            all_matches.append({
                'candidate_id': candidate_id,
                'position_id': position['id'],
                'score': score,
                'candidate': candidate,
                'position': position
            })
    
    # Sort matches by score
    all_matches.sort(key=lambda x: x['score'], reverse=True)
    
    # For each candidate, select 4 positions:
    # 1. Good match (top 10%)
    # 2. Bad match (bottom 10%)
    # 3. Maybe (middle 50%)
    # 4. On fence (30th percentile)
    logger.info("Selecting 4 positions per candidate...")
    candidate_matches = {}
    
    for candidate_id in candidate_ids:
        candidate_matches_list = [m for m in all_matches if m['candidate_id'] == candidate_id]
        if not candidate_matches_list:
            continue
        candidate_matches_list.sort(key=lambda x: x['score'], reverse=True)
        
        if len(candidate_matches_list) < 4:
            # If not enough positions, just use what we have
            selected = candidate_matches_list
        else:
            total = len(candidate_matches_list)
            good_idx = min(int(total * 0.1), total - 1)  # Top 10%
            bad_idx = max(int(total * 0.9), 0)  # Bottom 10%
            maybe_idx = int(total * 0.5)  # Middle
            fence_idx = int(total * 0.3)  # 30th percentile
            
            selected = [
                candidate_matches_list[good_idx],  # Good match
                candidate_matches_list[bad_idx],   # Bad match
                candidate_matches_list[maybe_idx], # Maybe
                candidate_matches_list[fence_idx]  # On fence
            ]
        
        candidate_matches[candidate_id] = selected
    
    # Create pipeline entries
    logger.info("Creating pipeline entries...")
    pipeline_entries = 0
    for candidate_id, matches in candidate_matches.items():
        for match in matches:
            try:
                pipeline.enter_stage(
                    candidate_id=candidate_id,
                    position_id=match['position_id'],
                    stage='dm_screening_passed',  # Start at passed DM screening
                    metadata={
                        'match_score': match['score'],
                        'match_type': 'demo_setup',
                        'auto_created': True
                    }
                )
                pipeline_entries += 1
            except Exception as e:
                logger.warning(f"Failed to create pipeline entry for {candidate_id} -> {match['position_id']}: {e}")
    
    logger.info(f"Created {pipeline_entries} pipeline entries")
    
    # Pass top 10% candidates for each position to phone_screen_passed
    logger.info("Promoting top 10% candidates to phone_screen_passed...")
    promoted = 0
    
    for position in positions:
        position_id = position['id']
        position_matches = [m for m in all_matches if m['position_id'] == position_id]
        position_matches.sort(key=lambda x: x['score'], reverse=True)
        
        top_10_percent = max(1, int(len(position_matches) * 0.1))
        top_candidates = position_matches[:top_10_percent]
        
        for match in top_candidates:
            try:
                # Transition to phone_screen_passed
                pipeline.transition_stage(
                    candidate_id=match['candidate_id'],
                    position_id=position_id,
                    new_stage='phone_screen_passed',
                    metadata={
                        'match_score': match['score'],
                        'top_10_percent': True,
                        'auto_promoted': True
                    }
                )
                promoted += 1
            except Exception as e:
                logger.warning(f"Failed to promote {match['candidate_id']} for {position_id}: {e}")
    
    logger.info(f"Promoted {promoted} candidates to phone_screen_passed")
    
    logger.info("=" * 60)
    logger.info("✅ DEMO PIPELINE SETUP COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  - Pipeline entries created: {pipeline_entries}")
    logger.info(f"  - Top candidates promoted: {promoted}")
    logger.info(f"  - Positions: {len(positions)}")
    logger.info(f"  - Candidates: {len(candidate_ids)}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        match_candidates_to_positions()
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}", exc_info=True)
        sys.exit(1)

