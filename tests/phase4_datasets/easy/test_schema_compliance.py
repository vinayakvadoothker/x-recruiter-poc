"""
test_schema_compliance.py - Schema compliance tests for datasets

Why this test exists:
All datasets must match the exact schema defined in the pivot plan. This test
verifies that generated profiles have all required fields and correct data types.
Schema compliance is critical - mismatched schemas will break the knowledge graph,
embedder, and vector DB operations.

What it validates:
- All required fields are present in candidate profiles
- All required fields are present in team profiles
- All required fields are present in interviewer profiles
- All required fields are present in position profiles
- Data types match schema (strings, lists, dicts, ints, floats)
- Optional fields are handled correctly

Expected behavior:
- All profiles have 'id' field
- All profiles have required fields for their type
- Data types match schema exactly
- No missing required fields
"""

import pytest
import logging
from backend.datasets import (
    generate_candidates, generate_teams, 
    generate_interviewers, generate_positions
)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSchemaCompliance:
    """Test schema compliance for all profile types."""
    
    def test_candidate_schema(self):
        """Test candidate profile schema compliance."""
        candidates = list(generate_candidates(10))
        
        for candidate in candidates:
            # Required fields
            assert 'id' in candidate, "Candidate must have 'id'"
            assert 'skills' in candidate, "Candidate must have 'skills'"
            assert 'experience_years' in candidate, "Candidate must have 'experience_years'"
            assert 'domains' in candidate, "Candidate must have 'domains'"
            assert 'expertise_level' in candidate, "Candidate must have 'expertise_level'"
            
            # Data types
            assert isinstance(candidate['id'], str)
            assert isinstance(candidate['skills'], list)
            assert isinstance(candidate['experience_years'], int)
            assert isinstance(candidate['domains'], list)
            assert isinstance(candidate['expertise_level'], str)
            
            # Optional fields (should exist but may be None/empty)
            assert 'github_handle' in candidate
            assert 'x_handle' in candidate
            assert 'linkedin_url' in candidate
            assert 'projects' in candidate
            assert 'github_stats' in candidate
    
    def test_team_schema(self):
        """Test team profile schema compliance."""
        teams = list(generate_teams(10))
        
        for team in teams:
            # Required fields
            assert 'id' in team, "Team must have 'id'"
            assert 'name' in team, "Team must have 'name'"
            assert 'needs' in team, "Team must have 'needs'"
            assert 'expertise' in team, "Team must have 'expertise'"
            assert 'member_count' in team, "Team must have 'member_count'"
            
            # Data types
            assert isinstance(team['id'], str)
            assert isinstance(team['name'], str)
            assert isinstance(team['needs'], list)
            assert isinstance(team['expertise'], list)
            assert isinstance(team['member_count'], int)
            
            # Optional fields
            assert 'open_positions' in team
            assert 'member_ids' in team
            assert 'culture' in team
            assert 'work_style' in team
    
    def test_interviewer_schema(self):
        """Test interviewer profile schema compliance."""
        interviewers = list(generate_interviewers(10))
        
        for interviewer in interviewers:
            # Required fields
            assert 'id' in interviewer, "Interviewer must have 'id'"
            assert 'name' in interviewer, "Interviewer must have 'name'"
            assert 'expertise' in interviewer, "Interviewer must have 'expertise'"
            assert 'total_interviews' in interviewer, "Interviewer must have 'total_interviews'"
            assert 'success_rate' in interviewer, "Interviewer must have 'success_rate'"
            
            # Data types
            assert isinstance(interviewer['id'], str)
            assert isinstance(interviewer['name'], str)
            assert isinstance(interviewer['expertise'], list)
            assert isinstance(interviewer['total_interviews'], int)
            assert isinstance(interviewer['success_rate'], float)
            
            # Optional fields
            assert 'team_id' in interviewer
            assert 'interview_style' in interviewer
            assert 'cluster_success_rates' in interviewer
    
    def test_position_schema(self):
        """Test position profile schema compliance."""
        positions = list(generate_positions(10))
        
        for position in positions:
            # Required fields
            assert 'id' in position, "Position must have 'id'"
            assert 'title' in position, "Position must have 'title'"
            assert 'must_haves' in position, "Position must have 'must_haves'"
            assert 'requirements' in position, "Position must have 'requirements'"
            assert 'experience_level' in position, "Position must have 'experience_level'"
            
            # Data types
            assert isinstance(position['id'], str)
            assert isinstance(position['title'], str)
            assert isinstance(position['must_haves'], list)
            assert isinstance(position['requirements'], list)
            assert isinstance(position['experience_level'], str)
            
            # Optional fields
            assert 'team_id' in position
            assert 'nice_to_haves' in position
            assert 'tech_stack' in position
            assert 'status' in position
    
    def test_all_profile_types_have_id(self):
        """Test that all profile types have 'id' field."""
        candidate = next(generate_candidates(1))
        team = next(generate_teams(1))
        interviewer = next(generate_interviewers(1))
        position = next(generate_positions(1))
        
        assert 'id' in candidate
        assert 'id' in team
        assert 'id' in interviewer
        assert 'id' in position

