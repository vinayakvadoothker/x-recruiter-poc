"""
test_generator_variety.py - Test dataset variety and uniqueness

Why this test exists:
Generated datasets must have sufficient variety to test the system realistically.
If all profiles are identical, tests won't catch edge cases or validate matching
algorithms properly. Variety ensures we test the system with diverse inputs.

What it validates:
- Generated profiles have variety in skills, experience, domains
- No duplicate IDs across profiles
- Profiles have realistic distributions (not all same level)
- Different profile types have appropriate variety
- Generators produce different profiles on each call

Expected behavior:
- Skills vary across candidates
- Experience levels are distributed
- Domains are diverse
- IDs are unique
- Profiles are not identical
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


class TestGeneratorVariety:
    """Test variety and uniqueness of generated profiles."""
    
    def test_candidate_variety(self):
        """Test that candidates have variety."""
        candidates = list(generate_candidates(50))
        
        # Check variety in skills
        all_skills = set()
        for c in candidates:
            all_skills.update(c['skills'])
        assert len(all_skills) > 5, "Should have variety in skills"
        
        # Check variety in experience levels
        experience_levels = [c['expertise_level'] for c in candidates]
        unique_levels = set(experience_levels)
        assert len(unique_levels) >= 2, "Should have multiple experience levels"
        
        # Check variety in domains
        all_domains = set()
        for c in candidates:
            all_domains.update(c['domains'])
        assert len(all_domains) > 3, "Should have variety in domains"
    
    def test_unique_candidate_ids(self):
        """Test that candidate IDs are unique."""
        candidates = list(generate_candidates(100))
        ids = [c['id'] for c in candidates]
        assert len(ids) == len(set(ids)), "All candidate IDs should be unique"
    
    def test_team_variety(self):
        """Test that teams have variety."""
        teams = list(generate_teams(30))
        
        # Check variety in team names
        team_names = [t['name'] for t in teams]
        unique_names = set(team_names)
        assert len(unique_names) > 5, "Should have variety in team names"
        
        # Check variety in needs
        all_needs = set()
        for t in teams:
            all_needs.update(t['needs'])
        assert len(all_needs) > 3, "Should have variety in team needs"
        
        # Check variety in team sizes
        member_counts = [t['member_count'] for t in teams]
        assert max(member_counts) > min(member_counts), "Should have variety in team sizes"
    
    def test_interviewer_variety(self):
        """Test that interviewers have variety."""
        interviewers = list(generate_interviewers(50))
        
        # Check variety in interview styles
        styles = [i['interview_style'] for i in interviewers]
        unique_styles = set(styles)
        assert len(unique_styles) >= 2, "Should have variety in interview styles"
        
        # Check variety in success rates
        success_rates = [i['success_rate'] for i in interviewers]
        assert max(success_rates) > min(success_rates), "Should have variety in success rates"
        
        # Check variety in expertise
        all_expertise = set()
        for i in interviewers:
            all_expertise.update(i['expertise'])
        assert len(all_expertise) > 5, "Should have variety in expertise"
    
    def test_position_variety(self):
        """Test that positions have variety."""
        positions = list(generate_positions(30))
        
        # Check variety in titles
        titles = [p['title'] for p in positions]
        unique_titles = set(titles)
        assert len(unique_titles) > 5, "Should have variety in position titles"
        
        # Check variety in experience levels
        levels = [p['experience_level'] for p in positions]
        unique_levels = set(levels)
        assert len(unique_levels) >= 2, "Should have variety in experience levels"
        
        # Check variety in must-haves
        all_must_haves = set()
        for p in positions:
            all_must_haves.update(p['must_haves'])
        assert len(all_must_haves) > 5, "Should have variety in must-have skills"
    
    def test_profiles_not_identical(self):
        """Test that generated profiles are not identical."""
        candidates = list(generate_candidates(10))
        
        # Check that at least some fields differ
        first_skills = candidates[0]['skills']
        all_same = all(c['skills'] == first_skills for c in candidates)
        assert not all_same, "Profiles should have variety, not all identical"

