"""
test_basic_matching.py - Easy tests for basic matching functionality

Why this test exists:
This test verifies that the matching system can find teams and interviewers
for candidates. This is the foundation - without working matching, the entire
recruiting pipeline fails. We need to ensure the matcher correctly identifies
good matches and returns valid results.

What it validates:
- match_to_team() returns valid team match
- match_to_person() returns valid interviewer match
- Match scores are reasonable (0.0-1.0)
- Reasoning is generated and non-empty
- All required fields are present in results

Expected behavior:
- Strong candidates get matched to appropriate teams
- Interviewers are matched from the specified team
- Match scores reflect similarity and fit
- Reasoning explains why the match was made
"""

import pytest
import os
import logging
from backend.matching.team_matcher import TeamPersonMatcher
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestBasicMatching:
    """Test basic team and interviewer matching."""
    
    def setup_method(self):
        """Set up matcher and test data."""
        logger.info("Setting up matching test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.matcher = TeamPersonMatcher(knowledge_graph=self.kg)
        
        # Create test candidate
        self.candidate = {
            'id': 'candidate_001',
            'skills': ['CUDA', 'C++', 'PyTorch', 'LLM Inference'],
            'experience_years': 6,
            'domains': ['LLM Inference', 'GPU Computing'],
            'expertise_level': 'Senior'
        }
        
        # Create test team
        self.team = {
            'id': 'team_001',
            'name': 'LLM Inference Team',
            'department': 'AI Infrastructure',
            'needs': ['CUDA', 'C++', 'LLM Inference'],
            'expertise': ['LLM Inference', 'GPU Computing'],
            'open_positions': ['position_001'],
            'member_count': 5,
            'member_ids': ['interviewer_001', 'interviewer_002']
        }
        
        # Create test interviewers
        self.interviewer1 = {
            'id': 'interviewer_001',
            'name': 'Alex Chen',
            'email': 'alex@company.com',
            'team_id': 'team_001',
            'expertise': ['CUDA', 'LLM Inference'],
            'expertise_level': 'Senior',
            'success_rate': 0.7,
            'cluster_success_rates': {'CUDA Experts': 0.8}
        }
        
        self.interviewer2 = {
            'id': 'interviewer_002',
            'name': 'Sarah Kim',
            'email': 'sarah@company.com',
            'team_id': 'team_001',
            'expertise': ['PyTorch', 'GPU Computing'],
            'expertise_level': 'Senior',
            'success_rate': 0.6,
            'cluster_success_rates': {}
        }
        
        logger.info("Adding test profiles to knowledge graph...")
        self.kg.add_candidate(self.candidate)
        self.kg.add_team(self.team)
        self.kg.add_interviewer(self.interviewer1)
        self.kg.add_interviewer(self.interviewer2)
        logger.info("Test profiles added")
    
    def teardown_method(self):
        """Clean up after each test."""
        self.matcher.close()
    
    def test_match_to_team(self):
        """Test that candidate can be matched to a team."""
        logger.info("Testing team matching")
        
        result = self.matcher.match_to_team('candidate_001')
        
        logger.info(f"Team match result: {result}")
        
        assert 'error' not in result, f"Team matching failed: {result.get('error')}"
        assert 'team_id' in result, "Result should include team_id"
        assert 'match_score' in result, "Result should include match_score"
        assert 'reasoning' in result, "Result should include reasoning"
        
        assert 0.0 <= result['match_score'] <= 1.0, \
            f"Match score should be 0-1, got {result['match_score']}"
        assert len(result['reasoning']) > 0, \
            "Reasoning should be non-empty"
        assert result['team_id'] == 'team_001', \
            f"Should match to team_001, got {result['team_id']}"
        
        logger.info(f"✅ Matched to team {result['team_id']} with score {result['match_score']:.3f}")
    
    def test_match_to_person(self):
        """Test that candidate can be matched to an interviewer."""
        logger.info("Testing interviewer matching")
        
        result = self.matcher.match_to_person('candidate_001', 'team_001')
        
        logger.info(f"Interviewer match result: {result}")
        
        assert 'error' not in result, f"Interviewer matching failed: {result.get('error')}"
        assert 'interviewer_id' in result, "Result should include interviewer_id"
        assert 'match_score' in result, "Result should include match_score"
        assert 'reasoning' in result, "Result should include reasoning"
        
        assert 0.0 <= result['match_score'] <= 1.0, \
            f"Match score should be 0-1, got {result['match_score']}"
        assert len(result['reasoning']) > 0, \
            "Reasoning should be non-empty"
        assert result['interviewer_id'] in ['interviewer_001', 'interviewer_002'], \
            f"Should match to one of the team's interviewers, got {result['interviewer_id']}"
        
        logger.info(f"✅ Matched to interviewer {result['interviewer_id']} with score {result['match_score']:.3f}")
    
    def test_match_result_structure(self):
        """Test that match results have complete structure."""
        logger.info("Testing match result structure")
        
        team_result = self.matcher.match_to_team('candidate_001')
        person_result = self.matcher.match_to_person('candidate_001', 'team_001')
        
        logger.info(f"Team result keys: {list(team_result.keys())}")
        logger.info(f"Person result keys: {list(person_result.keys())}")
        
        # Team match required fields
        required_team_fields = ['candidate_id', 'team_id', 'match_score', 'similarity', 'reasoning']
        for field in required_team_fields:
            assert field in team_result, f"Team match missing required field: {field}"
        
        # Person match required fields
        required_person_fields = ['candidate_id', 'team_id', 'interviewer_id', 'match_score', 'similarity', 'reasoning']
        for field in required_person_fields:
            assert field in person_result, f"Person match missing required field: {field}"
        
        logger.info("✅ Match result structures are complete")
    
    def test_match_scores_are_reasonable(self):
        """Test that match scores are in valid range."""
        logger.info("Testing match score ranges")
        
        team_result = self.matcher.match_to_team('candidate_001')
        person_result = self.matcher.match_to_person('candidate_001', 'team_001')
        
        logger.info(f"Team match score: {team_result['match_score']:.3f}")
        logger.info(f"Person match score: {person_result['match_score']:.3f}")
        
        assert 0.0 <= team_result['match_score'] <= 1.0, \
            f"Team match score out of range: {team_result['match_score']}"
        assert 0.0 <= person_result['match_score'] <= 1.0, \
            f"Person match score out of range: {person_result['match_score']}"
        
        # For a good match, score should be reasonable (at least 0.4)
        # This candidate should match well with the team
        assert team_result['match_score'] >= 0.4, \
            f"Team match score too low for good match: {team_result['match_score']}"
        
        logger.info("✅ Match scores are in valid range")

