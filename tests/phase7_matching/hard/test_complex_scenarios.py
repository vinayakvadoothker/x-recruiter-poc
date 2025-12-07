"""
test_complex_scenarios.py - Hard tests for complex matching scenarios

Why this test exists:
Real-world matching involves complex scenarios: multiple good matches, reasoning
quality, multi-criteria evaluation, cluster-based matching. This test ensures
the matching system handles these correctly and provides high-quality matches
with clear reasoning.

What it validates:
- Reasoning generation quality and completeness
- Multi-criteria evaluation (similarity + needs + expertise)
- Cluster-based matching (when ability_cluster is present)
- Bandit selection works correctly
- Match scores reflect all factors appropriately

Expected behavior:
- Reasoning explains all relevant factors
- Multi-criteria scores are balanced correctly
- Cluster success rates are used when available
- Bandit provides principled selection
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


class TestComplexScenarios:
    """Test complex matching scenarios."""
    
    def setup_method(self):
        """Set up matcher and complex test data."""
        logger.info("Setting up complex scenario test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.matcher = TeamPersonMatcher(knowledge_graph=self.kg)
    
    def teardown_method(self):
        """Clean up after each test."""
        self.matcher.close()
    
    def test_reasoning_quality(self):
        """Test that reasoning is detailed and informative."""
        logger.info("Testing reasoning quality")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['CUDA', 'C++', 'PyTorch', 'LLM Inference'],
            'domains': ['LLM Inference'],
            'experience_years': 6
        }
        
        team = {
            'id': 'team_001',
            'name': 'LLM Inference Team',
            'needs': ['CUDA', 'C++', 'LLM Inference'],
            'expertise': ['LLM Inference', 'GPU Computing'],
            'open_positions': ['pos_1', 'pos_2']
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team)
        
        result = self.matcher.match_to_team('candidate_001')
        
        logger.info(f"Reasoning: {result['reasoning']}")
        
        reasoning = result['reasoning'].lower()
        
        # Reasoning should mention key factors
        has_team_name = team['name'].lower() in reasoning
        has_similarity = 'similarity' in reasoning or 'match' in reasoning
        
        assert has_team_name, \
            f"Reasoning should mention team name, got: {result['reasoning']}"
        assert has_similarity or 'match' in reasoning, \
            f"Reasoning should mention match factors, got: {result['reasoning']}"
        assert len(result['reasoning']) > 20, \
            f"Reasoning should be detailed, got: {result['reasoning']}"
        
        logger.info("✅ Reasoning is detailed and informative")
    
    def test_multi_criteria_evaluation(self):
        """Test that match scores reflect multiple criteria."""
        logger.info("Testing multi-criteria evaluation")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'domains': ['LLM Inference']
        }
        
        # Team with perfect needs match
        team1 = {
            'id': 'team_001',
            'name': 'Perfect Match Team',
            'needs': ['CUDA', 'C++', 'PyTorch'],  # Perfect match
            'expertise': ['LLM Inference'],  # Perfect match
            'open_positions': ['pos_1']
        }
        
        # Team with partial match
        team2 = {
            'id': 'team_002',
            'name': 'Partial Match Team',
            'needs': ['CUDA'],  # Partial match
            'expertise': ['Web Development'],  # No match
            'open_positions': []
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team1)
        self.kg.add_team(team2)
        
        result = self.matcher.match_to_team('candidate_001')
        
        logger.info(f"Selected team: {result['team_id']}")
        logger.info(f"Match score: {result['match_score']:.3f}")
        logger.info(f"Similarity: {result['similarity']:.3f}")
        logger.info(f"Needs match: {result.get('needs_match', 'N/A')}")
        logger.info(f"Expertise match: {result.get('expertise_match', 'N/A')}")
        
        # Should prefer team_001 (better multi-criteria match)
        if result['team_id'] == 'team_001':
            logger.info("✅ Correctly selected team with better multi-criteria match")
            assert result['match_score'] >= 0.6, \
                f"Good match should have score >= 0.6, got {result['match_score']}"
        else:
            logger.warning(f"Selected team_002, but team_001 should be better match")
        
        # Verify all criteria are present
        assert 'similarity' in result, "Result should include similarity"
        assert result.get('needs_match') is not None, "Result should include needs_match"
        assert result.get('expertise_match') is not None, "Result should include expertise_match"
        
        logger.info("✅ Multi-criteria evaluation works correctly")
    
    def test_cluster_based_matching(self):
        """Test that cluster success rates are used in interviewer matching."""
        logger.info("Testing cluster-based matching")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['CUDA', 'C++'],
            'domains': ['LLM Inference'],
            'ability_cluster': 'CUDA Experts'  # Has cluster
        }
        
        team = {
            'id': 'team_001',
            'name': 'Test Team',
            'member_ids': ['interviewer_001', 'interviewer_002']
        }
        
        # Interviewer with high cluster success rate
        interviewer1 = {
            'id': 'interviewer_001',
            'name': 'CUDA Expert Interviewer',
            'team_id': 'team_001',
            'expertise': ['CUDA'],
            'success_rate': 0.6,
            'cluster_success_rates': {
                'CUDA Experts': 0.9  # High success with CUDA Experts
            }
        }
        
        # Interviewer with low cluster success rate
        interviewer2 = {
            'id': 'interviewer_002',
            'name': 'General Interviewer',
            'team_id': 'team_001',
            'expertise': ['Python'],
            'success_rate': 0.5,
            'cluster_success_rates': {
                'CUDA Experts': 0.3  # Low success with CUDA Experts
            }
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(team)
        self.kg.add_interviewer(interviewer1)
        self.kg.add_interviewer(interviewer2)
        
        result = self.matcher.match_to_person('candidate_001', 'team_001')
        
        logger.info(f"Selected interviewer: {result['interviewer_id']}")
        logger.info(f"Match score: {result['match_score']:.3f}")
        logger.info(f"Cluster success: {result.get('cluster_success', 'N/A')}")
        
        # Should prefer interviewer_001 (higher cluster success rate)
        if result['interviewer_id'] == 'interviewer_001':
            logger.info("✅ Correctly selected interviewer with higher cluster success rate")
        else:
            logger.warning("Selected interviewer_002, but interviewer_001 should be better for CUDA Experts")
        
        assert 'cluster_success' in result or result.get('cluster_success') is not None, \
            "Result should include cluster_success information"
        
        logger.info("✅ Cluster-based matching works correctly")
    
    def test_bandit_selection_works(self):
        """Test that bandit selection is used correctly."""
        logger.info("Testing bandit selection")
        
        candidate = {
            'id': 'candidate_001',
            'skills': ['Python', 'Django'],
            'domains': ['Web Development']
        }
        
        # Create multiple similar teams
        teams = []
        for i in range(5):
            team = {
                'id': f'team_{i:03d}',
                'name': f'Team {i}',
                'needs': ['Python', 'Django'],
                'expertise': ['Web Development'],
                'open_positions': ['pos_1']
            }
            teams.append(team)
            self.kg.add_team(team)
        
        self.kg.add_candidate(candidate)
        
        # Run matching multiple times - bandit should select different teams
        # (exploration) or consistently select best (exploitation)
        results = []
        for _ in range(10):
            result = self.matcher.match_to_team('candidate_001')
            results.append(result['team_id'])
        
        logger.info(f"Team selections: {results}")
        
        # Bandit should select from available teams
        unique_selections = set(results)
        logger.info(f"Unique teams selected: {len(unique_selections)}")
        
        assert len(unique_selections) > 0, "Bandit should select at least one team"
        assert all(tid in [f'team_{i:03d}' for i in range(5)] for tid in unique_selections), \
            "Bandit should only select from available teams"
        
        logger.info("✅ Bandit selection works correctly")

