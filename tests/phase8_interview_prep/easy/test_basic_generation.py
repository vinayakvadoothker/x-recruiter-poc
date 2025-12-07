"""
Easy tests for interview prep generator - Basic functionality.

Why this test exists:
- Validates that the interview prep generator can generate prep materials
- Ensures all required components are present in the output
- Verifies basic integration with KnowledgeGraph and Grok API

What it validates:
- generate_prep() returns complete prep materials
- All required fields are present (profile_overview, questions, focus_areas)
- Summaries are generated for all profiles
- Questions are properly formatted
- Focus areas are properly formatted

Expected behavior:
- Prep generation completes without errors
- Output contains all required components
- Questions have category, question, and rationale
- Focus areas have area, type, description, questions_to_ask, rationale
"""

import os
import pytest
import logging
from backend.matching.interview_prep_generator import InterviewPrepGenerator
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestBasicGeneration:
    """Test basic interview prep generation."""
    
    def setup_method(self):
        """Set up test data."""
        logger.info("Setting up basic generation test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.generator = InterviewPrepGenerator(knowledge_graph=self.kg)
        
        # Create test profiles
        self.candidate = {
            'id': 'candidate_001',
            'name': 'Test Candidate',
            'skills': ['Python', 'CUDA', 'LLM Optimization'],
            'experience_years': 5,
            'domains': ['AI/ML'],
            'experience': ['5 years as ML Engineer'],
            'education': ['BS in Computer Science']
        }
        
        self.position = {
            'id': 'position_001',
            'title': 'Senior LLM Inference Engineer',
            'required_skills': ['Python', 'CUDA', 'LLM Optimization'],
            'experience_level': 'Senior',
            'domain': 'AI/ML',
            'description': 'Optimize LLM inference performance'
        }
        
        self.team = {
            'id': 'team_001',
            'name': 'LLM Inference Team',
            'domain': 'AI/ML',
            'expertise_areas': ['CUDA', 'LLM Optimization'],
            'current_projects': ['Inference Optimization'],
            'position_ids': ['position_001']
        }
        
        self.interviewer = {
            'id': 'interviewer_001',
            'name': 'Test Interviewer',
            'role': 'Senior Engineer',
            'expertise_areas': ['CUDA', 'LLM Optimization'],
            'experience_years': 8
        }
        
        # Add to knowledge graph
        self.kg.add_candidate(self.candidate)
        self.kg.add_position(self.position)
        self.kg.add_team(self.team)
        self.kg.add_interviewer(self.interviewer)
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'generator'):
            self.generator.close()
        if hasattr(self, 'kg'):
            self.kg.close()
    
    @pytest.mark.asyncio
    async def test_prep_generation_completes(self):
        """Test that prep generation completes without errors."""
        logger.info("Testing prep generation completes")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        assert prep is not None
        logger.info("✅ Prep generation completed successfully")
    
    @pytest.mark.asyncio
    async def test_all_components_present(self):
        """Test that all required components are present."""
        logger.info("Testing all components present")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        assert 'profile_overview' in prep
        assert 'candidate_summary' in prep
        assert 'position_summary' in prep
        assert 'team_context' in prep
        assert 'interviewer_context' in prep
        assert 'questions' in prep
        assert 'focus_areas' in prep
        assert 'metadata' in prep
        
        logger.info("✅ All components present")
    
    @pytest.mark.asyncio
    async def test_summaries_are_strings(self):
        """Test that summaries are non-empty strings."""
        logger.info("Testing summaries are strings")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        assert isinstance(prep['profile_overview'], str)
        assert len(prep['profile_overview']) > 0
        assert isinstance(prep['candidate_summary'], str)
        assert len(prep['candidate_summary']) > 0
        assert isinstance(prep['position_summary'], str)
        assert len(prep['position_summary']) > 0
        assert isinstance(prep['team_context'], str)
        assert len(prep['team_context']) > 0
        assert isinstance(prep['interviewer_context'], str)
        assert len(prep['interviewer_context']) > 0
        
        logger.info("✅ All summaries are non-empty strings")
    
    @pytest.mark.asyncio
    async def test_questions_format(self):
        """Test that questions are properly formatted."""
        logger.info("Testing questions format")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        questions = prep['questions']
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        for question in questions:
            assert 'category' in question
            assert 'question' in question
            assert 'rationale' in question
            assert isinstance(question['category'], str)
            assert isinstance(question['question'], str)
            assert isinstance(question['rationale'], str)
            assert len(question['question']) > 0
        
        logger.info(f"✅ Questions properly formatted ({len(questions)} questions)")
    
    @pytest.mark.asyncio
    async def test_focus_areas_format(self):
        """Test that focus areas are properly formatted."""
        logger.info("Testing focus areas format")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        focus_areas = prep['focus_areas']
        assert isinstance(focus_areas, list)
        assert len(focus_areas) > 0
        
        for area in focus_areas:
            assert 'area' in area
            assert 'type' in area
            assert 'description' in area
            assert 'questions_to_ask' in area
            assert 'rationale' in area
            assert isinstance(area['area'], str)
            assert isinstance(area['type'], str)
            assert area['type'] in ['strength', 'concern', 'gap']
            assert isinstance(area['description'], str)
            assert isinstance(area['questions_to_ask'], list)
            assert isinstance(area['rationale'], str)
        
        logger.info(f"✅ Focus areas properly formatted ({len(focus_areas)} areas)")
    
    @pytest.mark.asyncio
    async def test_metadata_present(self):
        """Test that metadata is present and correct."""
        logger.info("Testing metadata")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        metadata = prep['metadata']
        assert 'candidate_id' in metadata
        assert 'team_id' in metadata
        assert 'interviewer_id' in metadata
        assert 'position_id' in metadata
        assert 'generated_at' in metadata
        assert metadata['candidate_id'] == 'candidate_001'
        assert metadata['team_id'] == 'team_001'
        assert metadata['interviewer_id'] == 'interviewer_001'
        
        logger.info("✅ Metadata present and correct")

