"""
Medium tests for interview prep generator - Edge cases.

Why this test exists:
- Validates handling of missing or incomplete profile data
- Ensures error handling for invalid inputs
- Verifies fallback behavior when Grok API is unavailable
- Tests edge cases like missing optional fields

What it validates:
- Error handling for missing profiles
- Handling of incomplete profile data
- Fallback generation when Grok unavailable
- Position ID handling (from team vs provided)

Expected behavior:
- Clear error messages for missing profiles
- Graceful handling of incomplete data
- Fallback generation produces valid output
- Position resolution works correctly
"""

import os
import pytest
import logging
from backend.matching.interview_prep_generator import InterviewPrepGenerator
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestEdgeCases:
    """Test edge cases for interview prep generation."""
    
    def setup_method(self):
        """Set up test data."""
        logger.info("Setting up edge cases test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.generator = InterviewPrepGenerator(knowledge_graph=self.kg)
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'generator'):
            self.generator.close()
        if hasattr(self, 'kg'):
            self.kg.close()
    
    @pytest.mark.asyncio
    async def test_missing_candidate(self):
        """Test error handling for missing candidate."""
        logger.info("Testing missing candidate")
        
        # Create other profiles but not candidate
        position = {
            'id': 'position_001',
            'title': 'Test Position',
            'required_skills': ['Python']
        }
        team = {
            'id': 'team_001',
            'name': 'Test Team',
            'position_ids': ['position_001']
        }
        interviewer = {
            'id': 'interviewer_001',
            'name': 'Test Interviewer'
        }
        
        self.kg.add_position(position)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        
        with pytest.raises(ValueError, match="Candidate.*not found"):
            await self.generator.generate_prep(
                candidate_id='nonexistent',
                team_id='team_001',
                interviewer_id='interviewer_001'
            )
        
        logger.info("✅ Missing candidate error handled correctly")
    
    @pytest.mark.asyncio
    async def test_missing_team(self):
        """Test error handling for missing team."""
        logger.info("Testing missing team")
        
        candidate = {'id': 'candidate_001', 'skills': ['Python']}
        self.kg.add_candidate(candidate)
        
        with pytest.raises(ValueError, match="Team.*not found"):
            await self.generator.generate_prep(
                candidate_id='candidate_001',
                team_id='nonexistent',
                interviewer_id='interviewer_001'
            )
        
        logger.info("✅ Missing team error handled correctly")
    
    @pytest.mark.asyncio
    async def test_missing_interviewer(self):
        """Test error handling for missing interviewer."""
        logger.info("Testing missing interviewer")
        
        candidate = {'id': 'candidate_001', 'skills': ['Python']}
        position = {'id': 'position_001', 'title': 'Test Position'}
        team = {'id': 'team_001', 'name': 'Test Team', 'position_ids': ['position_001']}
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        self.kg.add_team(team)
        
        with pytest.raises(ValueError, match="Interviewer.*not found"):
            await self.generator.generate_prep(
                candidate_id='candidate_001',
                team_id='team_001',
                interviewer_id='nonexistent'
            )
        
        logger.info("✅ Missing interviewer error handled correctly")
    
    @pytest.mark.asyncio
    async def test_missing_position(self):
        """Test error handling for missing position."""
        logger.info("Testing missing position")
        
        candidate = {'id': 'candidate_001', 'skills': ['Python']}
        team = {'id': 'team_001', 'name': 'Test Team'}  # No position_ids
        interviewer = {'id': 'interviewer_001', 'name': 'Test Interviewer'}
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        
        with pytest.raises(ValueError, match="No position found"):
            await self.generator.generate_prep(
                candidate_id='candidate_001',
                team_id='team_001',
                interviewer_id='interviewer_001'
            )
        
        logger.info("✅ Missing position error handled correctly")
    
    @pytest.mark.asyncio
    async def test_incomplete_profile_data(self):
        """Test handling of incomplete profile data."""
        logger.info("Testing incomplete profile data")
        
        # Create profiles with minimal data
        candidate = {'id': 'candidate_001'}  # No skills, experience, etc.
        position = {'id': 'position_001', 'title': 'Test Position'}
        team = {'id': 'team_001', 'name': 'Test Team', 'position_ids': ['position_001']}
        interviewer = {'id': 'interviewer_001', 'name': 'Test Interviewer'}
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        
        # Should still generate prep (with fallbacks)
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        assert prep is not None
        assert 'profile_overview' in prep
        assert 'questions' in prep
        assert 'focus_areas' in prep
        
        logger.info("✅ Incomplete profile data handled gracefully")
    
    @pytest.mark.asyncio
    async def test_position_id_provided(self):
        """Test that provided position_id is used."""
        logger.info("Testing provided position_id")
        
        candidate = {'id': 'candidate_001', 'skills': ['Python']}
        position1 = {'id': 'position_001', 'title': 'Position 1'}
        position2 = {'id': 'position_002', 'title': 'Position 2'}
        team = {'id': 'team_001', 'name': 'Test Team', 'position_ids': ['position_001']}
        interviewer = {'id': 'interviewer_001', 'name': 'Test Interviewer'}
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position1)
        self.kg.add_position(position2)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        
        # Use position2 even though team has position1
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001',
            position_id='position_002'
        )
        
        assert prep['metadata']['position_id'] == 'position_002'
        logger.info("✅ Provided position_id used correctly")
    
    @pytest.mark.asyncio
    async def test_empty_skills_handling(self):
        """Test handling of empty skills lists."""
        logger.info("Testing empty skills handling")
        
        candidate = {'id': 'candidate_001', 'skills': []}  # Empty skills
        position = {'id': 'position_001', 'title': 'Test Position', 'required_skills': ['Python']}
        team = {'id': 'team_001', 'name': 'Test Team', 'position_ids': ['position_001']}
        interviewer = {'id': 'interviewer_001', 'name': 'Test Interviewer'}
        
        self.kg.add_candidate(candidate)
        self.kg.add_position(position)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer)
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        assert prep is not None
        assert len(prep['questions']) > 0
        assert len(prep['focus_areas']) > 0
        
        logger.info("✅ Empty skills handled correctly")

