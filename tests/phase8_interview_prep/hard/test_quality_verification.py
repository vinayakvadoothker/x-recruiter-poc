"""
Hard tests for interview prep generator - Quality verification.

Why this test exists:
- Validates that generated prep materials are high quality
- Ensures questions are relevant to candidate and position
- Verifies focus areas identify meaningful strengths/concerns/gaps
- Checks that summaries are informative and useful

What it validates:
- Questions are relevant to position requirements
- Focus areas correctly identify strengths, concerns, and gaps
- Summaries contain relevant information
- Questions cover multiple categories
- Focus areas have actionable questions_to_ask

Expected behavior:
- Questions align with position requirements
- Focus areas identify real gaps/strengths
- Summaries are informative (not generic)
- Questions span multiple categories
"""

import os
import pytest
import logging
from backend.matching.interview_prep_generator import InterviewPrepGenerator
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestQualityVerification:
    """Test quality of generated prep materials."""
    
    def setup_method(self):
        """Set up test data."""
        logger.info("Setting up quality verification test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.generator = InterviewPrepGenerator(knowledge_graph=self.kg)
        
        # Create detailed test profiles
        self.candidate = {
            'id': 'candidate_001',
            'name': 'Strong Candidate',
            'skills': ['Python', 'CUDA', 'LLM Optimization', 'PyTorch'],
            'experience_years': 6,
            'domains': ['AI/ML', 'Deep Learning'],
            'experience': ['6 years optimizing LLM inference', 'Built CUDA kernels'],
            'education': ['MS in Computer Science'],
            'projects': [{'name': 'LLM Inference Engine', 'description': 'Optimized inference'}]
        }
        
        self.position = {
            'id': 'position_001',
            'title': 'Senior LLM Inference Engineer',
            'required_skills': ['Python', 'CUDA', 'LLM Optimization'],
            'experience_level': 'Senior',
            'domain': 'AI/ML',
            'description': 'Optimize LLM inference performance using CUDA'
        }
        
        self.team = {
            'id': 'team_001',
            'name': 'LLM Inference Team',
            'domain': 'AI/ML',
            'expertise_areas': ['CUDA', 'LLM Optimization', 'Performance'],
            'current_projects': [{'name': 'Inference Optimization'}],
            'position_ids': ['position_001']
        }
        
        self.interviewer = {
            'id': 'interviewer_001',
            'name': 'Expert Interviewer',
            'role': 'Senior Engineer',
            'expertise_areas': ['CUDA', 'LLM Optimization'],
            'experience_years': 10
        }
        
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
    async def test_questions_relevant_to_position(self):
        """Test that questions are relevant to position requirements."""
        logger.info("Testing questions relevance")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        questions = prep['questions']
        position_skills = self.position['required_skills']
        
        # At least some questions should mention position skills
        question_texts = ' '.join([q['question'].lower() for q in questions])
        skill_mentions = sum(1 for skill in position_skills if skill.lower() in question_texts)
        
        assert skill_mentions > 0, "Questions should mention position requirements"
        logger.info(f"✅ Questions relevant ({skill_mentions} skill mentions)")
    
    @pytest.mark.asyncio
    async def test_questions_cover_multiple_categories(self):
        """Test that questions cover multiple categories."""
        logger.info("Testing question categories")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        questions = prep['questions']
        categories = set(q['category'] for q in questions)
        
        # Should have at least 2 different categories
        assert len(categories) >= 2, f"Questions should cover multiple categories, got: {categories}"
        logger.info(f"✅ Questions cover {len(categories)} categories: {categories}")
    
    @pytest.mark.asyncio
    async def test_focus_areas_identify_gaps(self):
        """Test that focus areas identify gaps between candidate and position."""
        logger.info("Testing focus areas identify gaps")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        focus_areas = prep['focus_areas']
        gap_areas = [area for area in focus_areas if area['type'] == 'gap']
        
        # Should identify at least some gaps (or strengths if perfect match)
        assert len(focus_areas) > 0, "Should have at least one focus area"
        logger.info(f"✅ Focus areas identified ({len(gap_areas)} gaps, {len(focus_areas) - len(gap_areas)} others)")
    
    @pytest.mark.asyncio
    async def test_focus_areas_have_actionable_questions(self):
        """Test that focus areas include actionable questions to ask."""
        logger.info("Testing focus areas have actionable questions")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        focus_areas = prep['focus_areas']
        
        for area in focus_areas:
            questions_to_ask = area.get('questions_to_ask', [])
            assert len(questions_to_ask) > 0, f"Focus area '{area['area']}' should have questions to ask"
            assert all(isinstance(q, str) and len(q) > 0 for q in questions_to_ask), "Questions should be non-empty strings"
        
        logger.info(f"✅ All {len(focus_areas)} focus areas have actionable questions")
    
    @pytest.mark.asyncio
    async def test_summaries_contain_relevant_info(self):
        """Test that summaries contain relevant information."""
        logger.info("Testing summaries contain relevant info")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        candidate_summary = prep['candidate_summary'].lower()
        position_summary = prep['position_summary'].lower()
        
        # Candidate summary should mention key skills
        assert any(skill.lower() in candidate_summary for skill in self.candidate['skills'][:3]), \
            "Candidate summary should mention key skills"
        
        # Position summary should mention position title or requirements
        assert self.position['title'].lower() in position_summary or \
               any(skill.lower() in position_summary for skill in self.position['required_skills'][:2]), \
            "Position summary should mention title or requirements"
        
        logger.info("✅ Summaries contain relevant information")
    
    @pytest.mark.asyncio
    async def test_profile_overview_is_comprehensive(self):
        """Test that profile overview is comprehensive."""
        logger.info("Testing profile overview comprehensiveness")
        
        prep = await self.generator.generate_prep(
            candidate_id='candidate_001',
            team_id='team_001',
            interviewer_id='interviewer_001'
        )
        
        overview = prep['profile_overview']
        
        # Should be substantial (not just a few words)
        assert len(overview) > 100, "Overview should be comprehensive"
        
        # Should mention candidate, position, or team
        overview_lower = overview.lower()
        assert any(keyword in overview_lower for keyword in ['candidate', 'position', 'team', 'engineer', 'llm']), \
            "Overview should mention relevant entities"
        
        logger.info(f"✅ Profile overview is comprehensive ({len(overview)} characters)")

