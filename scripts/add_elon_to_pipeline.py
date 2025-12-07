"""
Add the exceptional candidate to the Computer Vision Researcher position pipeline.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.orchestration.pipeline_tracker import PipelineTracker
from backend.orchestration.company_context import get_company_context
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_elon_to_pipeline():
    """Add exceptional candidate to Computer Vision Researcher pipeline."""
    logger.info("Adding exceptional candidate to Computer Vision Researcher pipeline...")
    
    pipeline = PipelineTracker()
    candidate_id = "candidate_elon_001"
    position_id = "position_0021"  # Computer Vision Researcher
    
    # Enter at dm_screening_passed stage (they've already passed screening)
    pipeline.enter_stage(
        candidate_id=candidate_id,
        position_id=position_id,
        stage="dm_screening_passed",
        metadata={
            "auto_created": True,
            "exceptional_talent": True,
            "screening_score": 1.0,
            "match_type": "exceptional_talent"
        }
    )
    
    # Promote to phone_screen_passed (ready for phone screen)
    pipeline.transition_stage(
        candidate_id=candidate_id,
        position_id=position_id,
        new_stage="phone_screen_passed",
        metadata={
            "auto_promoted": True,
            "exceptional_talent": True,
            "screening_score": 1.0,
            "match_type": "exceptional_talent"
        }
    )
    
    logger.info(f"✅ Added {candidate_id} to {position_id} pipeline at phone_screen_passed stage")
    logger.info("   Candidate is now ready for phone screen!")

if __name__ == "__main__":
    add_elon_to_pipeline()

