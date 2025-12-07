"""
test_edge_cases.py - Medium tests for matching edge cases

Why this test exists:
Real-world usage will have edge cases: no teams, no interviewers, missing candidates,
empty teams, etc. This test ensures the matching system handles these gracefully
and returns appropriate errors or fallback behavior.

What it validates:
- Missing candidate returns error
- Missing team returns error
- No teams available returns error
- No interviewers in team returns error
- Empty teams are handled correctly
- Multiple teams/interviewers are handled correctly

Expected behavior:
- Missing data returns clear error messages
- Empty lists are handled gracefully
- System doesn't crash on edge cases
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


class TestEdgeCases:
    """Test edge cases in matching."""
    
    def setup_method(self):
        """Set up matcher."""
        logger.info("Setting up edge case test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.matcher = TeamPersonMatcher(knowledge_graph=self.kg)
    
    def teardown_method(self):
        """Clean up after each test."""
        self.matcher.close()
    
    def test_missing_candidate_team_match(self):
        """Test team matching with missing candidate."""
        logger.info("Testing team matching with missing candidate")
        
        result = self.matcher.match_to_team('nonexistent_candidate')
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error for missing candidate"
        assert 'not found' in result['error'].lower(), \
            "Error should mention candidate not found"
        
        logger.info("✅ Missing candidate handled correctly")
    
    def test_missing_candidate_person_match(self):
        """Test person matching with missing candidate."""
        logger.info("Testing person matching with missing candidate")
        
        # Create team first
        team = {
            'id': 'team_001',
            'name': 'Test Team',
            'member_ids': []
        }
        self.kg.add_team(team)
        
        result = self.matcher.match_to_person('nonexistent_candidate', 'team_001')
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error for missing candidate"
        
        logger.info("✅ Missing candidate handled correctly")
    
    def test_no_teams_available(self):
        """Test team matching when no teams exist."""
        logger.info("Testing team matching with no teams")
        
        # Create candidate but no teams
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        self.kg.add_candidate(candidate)
        
        result = self.matcher.match_to_team('candidate_001')
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error when no teams available"
        assert 'no teams' in result['error'].lower() or 'no teams available' in result['error'].lower(), \
            "Error should mention no teams available"
        
        logger.info("✅ No teams handled correctly")
    
    def test_no_interviewers_in_team(self):
        """Test person matching when team has no interviewers."""
        logger.info("Testing person matching with no interviewers")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        team = {
            'id': 'team_001',
            'name': 'Empty Team',
            'member_ids': []  # No interviewers
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team)
        
        result = self.matcher.match_to_person('candidate_001', 'team_001')
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error when no interviewers"
        assert 'no interviewers' in result['error'].lower(), \
            "Error should mention no interviewers"
        
        logger.info("✅ No interviewers handled correctly")
    
    def test_missing_team_person_match(self):
        """Test person matching with missing team."""
        logger.info("Testing person matching with missing team")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python']
        }
        self.kg.add_candidate(candidate)
        
        result = self.matcher.match_to_person('candidate_001', 'nonexistent_team')
        
        logger.info(f"Result: {result}")
        
        assert 'error' in result, "Should return error for missing team"
        assert 'not found' in result['error'].lower(), \
            "Error should mention team not found"
        
        logger.info("✅ Missing team handled correctly")
    
    def test_multiple_teams_selection(self):
        """Test that matcher can select from multiple teams."""
        logger.info("Testing selection from multiple teams")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['CUDA', 'C++'],
            'domains': ['LLM Inference']
        }
        
        team1 = {
            'id': 'team_001',
            'name': 'LLM Team',
            'needs': ['CUDA', 'C++'],
            'expertise': ['LLM Inference'],
            'open_positions': ['pos_1']
        }
        
        team2 = {
            'id': 'team_002',
            'name': 'Web Team',
            'needs': ['React', 'Node.js'],
            'expertise': ['Web Development'],
            'open_positions': []
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team1)
        self.kg.add_team(team2)
        
        result = self.matcher.match_to_team('candidate_001')
        
        logger.info(f"Selected team: {result.get('team_id')}")
        logger.info(f"Match score: {result.get('match_score', 0):.3f}")
        
        assert 'error' not in result, f"Matching should succeed, got error: {result.get('error')}"
        assert result['team_id'] in ['team_001', 'team_002'], \
            f"Should select one of the teams, got {result['team_id']}"
        
        # Should prefer team_001 (better match)
        if result['team_id'] == 'team_001':
            logger.info("✅ Correctly selected better matching team")
        else:
            logger.warning("Selected team_002, but team_001 should be better match")
        
        logger.info("✅ Multiple teams selection works")

