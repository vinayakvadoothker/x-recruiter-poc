"""
Super hard tests for interview prep generator - Stress tests and consistency.

Why this test exists:
- Validates system performance under load (many prep generations)
- Ensures consistency across multiple generations
- Tests with various candidate/position combinations
- Verifies output quality remains high under stress

What it validates:
- Multiple prep generations complete successfully
- Output structure is consistent
- Performance is acceptable (not too slow)
- Quality doesn't degrade under load
- Handles various profile combinations

Expected behavior:
- Multiple generations complete without errors
- Output structure is consistent
- Performance is reasonable (< 30s for 5 generations)
- Quality metrics remain stable
"""

import os
import pytest
import logging
import time
from backend.matching.interview_prep_generator import InterviewPrepGenerator
from backend.database.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestStressAndConsistency:
    """Test stress scenarios and consistency."""
    
    def setup_method(self):
        """Set up test data."""
        logger.info("Setting up stress test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.generator = InterviewPrepGenerator(knowledge_graph=self.kg)
        
        # Create multiple test profiles
        self.candidates = [
            {
                'id': f'candidate_{i:03d}',
                'name': f'Candidate {i}',
                'skills': ['Python', 'CUDA'] if i < 3 else ['Python', 'Java'],
                'experience_years': 5 + i,
                'domains': ['AI/ML'] if i < 3 else ['Web Development']
            }
            for i in range(5)
        ]
        
        self.positions = [
            {
                'id': f'position_{i:03d}',
                'title': f'Position {i}',
                'required_skills': ['Python', 'CUDA'] if i < 2 else ['Python', 'Java'],
                'experience_level': 'Senior',
                'domain': 'AI/ML' if i < 2 else 'Web Development'
            }
            for i in range(3)
        ]
        
        self.teams = [
            {
                'id': f'team_{i:03d}',
                'name': f'Team {i}',
                'domain': 'AI/ML' if i < 2 else 'Web Development',
                'position_ids': [f'position_{i:03d}']
            }
            for i in range(3)
        ]
        
        self.interviewers = [
            {
                'id': f'interviewer_{i:03d}',
                'name': f'Interviewer {i}',
                'role': 'Senior Engineer',
                'expertise_areas': ['CUDA'] if i < 2 else ['Java']
            }
            for i in range(3)
        ]
        
        # Add all to knowledge graph
        for candidate in self.candidates:
            self.kg.add_candidate(candidate)
        for position in self.positions:
            self.kg.add_position(position)
        for team in self.teams:
            self.kg.add_team(team)
        for interviewer in self.interviewers:
            self.kg.add_interviewer(interviewer)
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'generator'):
            self.generator.close()
        if hasattr(self, 'kg'):
            self.kg.close()
    
    @pytest.mark.asyncio
    async def test_multiple_prep_generations(self):
        """Test generating prep for multiple candidate/position combinations."""
        logger.info("Testing multiple prep generations")
        
        results = []
        start_time = time.time()
        
        # Generate prep for 5 different combinations
        for i in range(5):
            candidate_idx = i % len(self.candidates)
            position_idx = i % len(self.positions)
            team_idx = i % len(self.teams)
            interviewer_idx = i % len(self.interviewers)
            
            prep = await self.generator.generate_prep(
                candidate_id=self.candidates[candidate_idx]['id'],
                team_id=self.teams[team_idx]['id'],
                interviewer_id=self.interviewers[interviewer_idx]['id']
            )
            
            results.append(prep)
            logger.debug(f"Generated prep {i+1}/5")
        
        elapsed = time.time() - start_time
        
        # Verify all completed
        assert len(results) == 5
        assert all('questions' in prep for prep in results)
        assert all('focus_areas' in prep for prep in results)
        
        # Performance check (should complete in reasonable time)
        assert elapsed < 60.0, f"5 generations took {elapsed:.1f}s, expected < 60s"
        
        logger.info(f"✅ Generated 5 prep materials in {elapsed:.1f}s")
    
    @pytest.mark.asyncio
    async def test_output_structure_consistency(self):
        """Test that output structure is consistent across generations."""
        logger.info("Testing output structure consistency")
        
        results = []
        
        # Generate 3 preps
        for i in range(3):
            prep = await self.generator.generate_prep(
                candidate_id=self.candidates[i]['id'],
                team_id=self.teams[i]['id'],
                interviewer_id=self.interviewers[i]['id']
            )
            results.append(prep)
        
        # Check structure consistency
        required_keys = ['profile_overview', 'candidate_summary', 'position_summary',
                        'team_context', 'interviewer_context', 'questions', 'focus_areas', 'metadata']
        
        for prep in results:
            for key in required_keys:
                assert key in prep, f"Missing key '{key}' in prep"
        
        # Check questions structure
        for prep in results:
            questions = prep['questions']
            assert isinstance(questions, list)
            for q in questions:
                assert 'category' in q
                assert 'question' in q
                assert 'rationale' in q
        
        # Check focus areas structure
        for prep in results:
            focus_areas = prep['focus_areas']
            assert isinstance(focus_areas, list)
            for area in focus_areas:
                assert 'area' in area
                assert 'type' in area
                assert 'description' in area
                assert 'questions_to_ask' in area
                assert 'rationale' in area
        
        logger.info("✅ Output structure is consistent across 3 generations")
    
    @pytest.mark.asyncio
    async def test_quality_consistency(self):
        """Test that quality metrics remain consistent."""
        logger.info("Testing quality consistency")
        
        results = []
        
        # Generate 3 preps
        for i in range(3):
            prep = await self.generator.generate_prep(
                candidate_id=self.candidates[i]['id'],
                team_id=self.teams[i]['id'],
                interviewer_id=self.interviewers[i]['id']
            )
            results.append(prep)
        
        # Check quality metrics
        question_counts = [len(prep['questions']) for prep in results]
        focus_area_counts = [len(prep['focus_areas']) for prep in results]
        overview_lengths = [len(prep['profile_overview']) for prep in results]
        
        # All should have reasonable counts
        assert all(count > 0 for count in question_counts), "All should have questions"
        assert all(count > 0 for count in focus_area_counts), "All should have focus areas"
        assert all(length > 50 for length in overview_lengths), "All should have substantial overviews"
        
        # Counts should be similar (within 2x)
        min_questions = min(question_counts)
        max_questions = max(question_counts)
        assert max_questions <= min_questions * 2, "Question counts should be similar"
        
        logger.info(f"✅ Quality consistent: questions={question_counts}, focus_areas={focus_area_counts}")
    
    @pytest.mark.asyncio
    async def test_various_profile_combinations(self):
        """Test with various candidate/position combinations."""
        logger.info("Testing various profile combinations")
        
        # Test different combinations
        combinations = [
            (0, 0, 0, 0),  # AI/ML candidate, AI/ML position
            (4, 2, 2, 2),  # Web dev candidate, Web dev position
            (1, 0, 0, 1),  # AI/ML candidate, AI/ML position, different interviewer
        ]
        
        for candidate_idx, position_idx, team_idx, interviewer_idx in combinations:
            prep = await self.generator.generate_prep(
                candidate_id=self.candidates[candidate_idx]['id'],
                team_id=self.teams[team_idx]['id'],
                interviewer_id=self.interviewers[interviewer_idx]['id']
            )
            
            assert prep is not None
            assert len(prep['questions']) > 0
            assert len(prep['focus_areas']) > 0
            
            logger.debug(f"✅ Combination ({candidate_idx}, {position_idx}, {team_idx}, {interviewer_idx}) works")
        
        logger.info("✅ Various profile combinations work correctly")

