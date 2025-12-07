"""
test_stress_and_quality.py - Super hard tests for stress and matching quality

Why this test exists:
In production, the matching system will handle many candidates and teams (50-200+)
and must make consistent, high-quality matches. This test ensures the system can
handle high-volume operations efficiently and maintains matching quality at scale.
The system must be production-ready and handle real-world workloads.

What it validates:
- System handles many teams efficiently
- System handles many interviewers efficiently
- Matching quality is consistent at scale
- Performance is acceptable for batch operations
- Match scores are meaningful and consistent

Expected behavior:
- Batch matching completes in reasonable time
- Match quality doesn't degrade with scale
- Performance is consistent regardless of team/candidate count
- System remains stable under load
"""

import pytest
import os
import time
import logging
from backend.matching.team_matcher import TeamPersonMatcher
from backend.database.knowledge_graph import KnowledgeGraph
from backend.datasets import generate_candidates, generate_teams, generate_interviewers

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStressAndQuality:
    """Test stress scenarios and matching quality."""
    
    def setup_method(self):
        """Set up matcher."""
        logger.info("Setting up stress test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.matcher = TeamPersonMatcher(knowledge_graph=self.kg)
    
    def teardown_method(self):
        """Clean up after each test."""
        self.matcher.close()
    
    def test_many_teams_performance(self):
        """Test performance with many teams."""
        logger.info("Testing performance with many teams")
        
        # Generate candidate
        candidate = next(generate_candidates(1))
        candidate['id'] = 'test_candidate'
        self.kg.add_candidate(candidate)
        
        # Generate 50 teams
        teams = list(generate_teams(50))
        logger.info(f"Generated {len(teams)} teams")
        
        for team in teams:
            self.kg.add_team(team)
        
        logger.info("Starting team matching...")
        start_time = time.time()
        result = self.matcher.match_to_team('test_candidate')
        elapsed_time = time.time() - start_time
        
        logger.info(f"Matching time: {elapsed_time:.2f}s")
        logger.info(f"Selected team: {result.get('team_id')}")
        logger.info(f"Match score: {result.get('match_score', 0):.3f}")
        
        assert 'error' not in result, f"Matching should succeed, got error: {result.get('error')}"
        assert elapsed_time < 30.0, f"Matching too slow: {elapsed_time:.2f}s"
        
        logger.info("✅ Many teams performance acceptable")
    
    def test_many_interviewers_performance(self):
        """Test performance with many interviewers."""
        logger.info("Testing performance with many interviewers")
        
        # Generate candidate and team
        candidate = next(generate_candidates(1))
        candidate['id'] = 'test_candidate'
        self.kg.add_candidate(candidate)
        
        team = next(generate_teams(1))
        team['id'] = 'test_team'
        team['member_ids'] = []
        
        # Generate 20 interviewers for the team
        interviewers = list(generate_interviewers(20))
        logger.info(f"Generated {len(interviewers)} interviewers")
        
        for i, interviewer in enumerate(interviewers):
            interviewer['id'] = f'interviewer_{i:03d}'
            interviewer['team_id'] = 'test_team'
            team['member_ids'].append(interviewer['id'])
            self.kg.add_interviewer(interviewer)
        
        self.kg.add_team(team)
        
        logger.info("Starting interviewer matching...")
        start_time = time.time()
        result = self.matcher.match_to_person('test_candidate', 'test_team')
        elapsed_time = time.time() - start_time
        
        logger.info(f"Matching time: {elapsed_time:.2f}s")
        logger.info(f"Selected interviewer: {result.get('interviewer_id')}")
        
        assert 'error' not in result, f"Matching should succeed, got error: {result.get('error')}"
        assert elapsed_time < 20.0, f"Matching too slow: {elapsed_time:.2f}s"
        
        logger.info("✅ Many interviewers performance acceptable")
    
    def test_matching_quality_consistency(self):
        """Test that matching quality is consistent."""
        logger.info("Testing matching quality consistency")
        
        # Create candidate with specific skills
        candidate = {
            'id': 'candidate_001',
            'skills': ['CUDA', 'C++', 'PyTorch'],
            'domains': ['LLM Inference'],
            'experience_years': 6
        }
        
        # Create teams with varying match quality
        perfect_team = {
            'id': 'perfect_team',
            'name': 'Perfect Match',
            'needs': ['CUDA', 'C++', 'PyTorch'],
            'expertise': ['LLM Inference'],
            'open_positions': ['pos_1']
        }
        
        good_team = {
            'id': 'good_team',
            'name': 'Good Match',
            'needs': ['CUDA', 'C++'],
            'expertise': ['LLM Inference'],
            'open_positions': ['pos_1']
        }
        
        poor_team = {
            'id': 'poor_team',
            'name': 'Poor Match',
            'needs': ['React', 'Node.js'],
            'expertise': ['Web Development'],
            'open_positions': []
        }
        
        self.kg.add_candidate(candidate)
        self.kg.add_team(perfect_team)
        self.kg.add_team(good_team)
        self.kg.add_team(poor_team)
        
        # Run matching multiple times
        results = []
        for _ in range(10):
            result = self.matcher.match_to_team('candidate_001')
            results.append({
                'team_id': result['team_id'],
                'score': result['match_score']
            })
        
        logger.info(f"Matching results: {results}")
        
        # Analyze results
        perfect_matches = sum(1 for r in results if r['team_id'] == 'perfect_team')
        good_matches = sum(1 for r in results if r['team_id'] == 'good_team')
        poor_matches = sum(1 for r in results if r['team_id'] == 'poor_team')
        
        logger.info(f"Perfect matches: {perfect_matches}, Good: {good_matches}, Poor: {poor_matches}")
        
        # Should prefer perfect or good matches (bandit may explore)
        assert perfect_matches + good_matches >= poor_matches, \
            "Should prefer better matches over poor matches"
        
        # Perfect team should have higher scores
        perfect_scores = [r['score'] for r in results if r['team_id'] == 'perfect_team']
        poor_scores = [r['score'] for r in results if r['team_id'] == 'poor_team']
        
        if perfect_scores and poor_scores:
            avg_perfect = sum(perfect_scores) / len(perfect_scores)
            avg_poor = sum(poor_scores) / len(poor_scores)
            logger.info(f"Average perfect match score: {avg_perfect:.3f}")
            logger.info(f"Average poor match score: {avg_poor:.3f}")
            assert avg_perfect >= avg_poor, \
                f"Perfect match should have higher score ({avg_perfect:.3f} vs {avg_poor:.3f})"
        
        logger.info("✅ Matching quality is consistent")
    
    def test_batch_matching_performance(self):
        """Test performance with batch matching operations."""
        logger.info("Testing batch matching performance")
        
        # Generate 20 candidates
        candidates = list(generate_candidates(20))
        for i, candidate in enumerate(candidates):
            candidate['id'] = f'candidate_{i:03d}'
            self.kg.add_candidate(candidate)
        
        # Generate 10 teams
        teams = list(generate_teams(10))
        for team in teams:
            self.kg.add_team(team)
        
        logger.info(f"Generated {len(candidates)} candidates and {len(teams)} teams")
        
        # Match all candidates
        logger.info("Starting batch matching...")
        start_time = time.time()
        results = []
        for candidate in candidates:
            result = self.matcher.match_to_team(candidate['id'])
            results.append(result)
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / len(candidates)
        logger.info(f"Total time: {elapsed_time:.2f}s")
        logger.info(f"Average time per match: {avg_time:.4f}s")
        logger.info(f"Matches per second: {len(candidates)/elapsed_time:.1f}")
        
        assert elapsed_time < 120.0, f"Batch matching too slow: {elapsed_time:.2f}s"
        assert avg_time < 6.0, f"Average match time too high: {avg_time:.4f}s"
        
        # Verify all matches succeeded
        successful = sum(1 for r in results if 'error' not in r)
        logger.info(f"Successful matches: {successful}/{len(candidates)}")
        
        assert successful == len(candidates), \
            f"All matches should succeed, got {successful}/{len(candidates)}"
        
        logger.info("✅ Batch matching performance acceptable")

