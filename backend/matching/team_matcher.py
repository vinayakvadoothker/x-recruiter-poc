"""
team_matcher.py - Team and interviewer matching system

This module provides matching functionality to find the best team and interviewer
for a candidate using vector similarity, bandit selection, and multi-criteria evaluation.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Multi-criteria matching methodology (similarity + needs + expertise)
    - Our adaptation: Using embedding similarity instead of graph similarity

[2] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Candidate selection algorithm via bandit
    - Our adaptation: Using bandit for team/interviewer selection

Our Novel Contribution:
Multi-criteria matching with embedding similarity: Combines embedding cosine similarity,
team needs matching, expertise overlap, and interviewer success rates to find optimal
team and interviewer matches. Uses bandit algorithm for principled selection.

Key functions:
- TeamPersonMatcher: Main matching class
- match_to_team(): Find best team for candidate
- match_to_person(): Find best interviewer for candidate
- _check_needs_match(): Team needs vs candidate skills
- _check_expertise_match(): Domain overlap check
- _generate_reasoning(): Human-readable explanations

Dependencies:
- backend.database.knowledge_graph: Profile retrieval
- backend.embeddings: Embedding generation
- backend.algorithms.fgts_bandit: Selection algorithm
- numpy: Numerical computations

Implementation Rationale:
- Why multi-criteria matching: Single-factor matching (just similarity) misses
  important factors like team needs, expertise overlap, and interviewer success rates.
  Combining multiple factors provides better matches.
- Why bandit for selection: Bandit provides principled exploration/exploitation
  trade-off, especially useful when multiple good matches exist. It balances
  selecting high-scoring matches with exploring potentially better options.
- Why embedding similarity: Fast, scalable, captures semantic relationships
  between candidates and teams/interviewers better than keyword matching.
- Why reasoning generation: Transparency is critical. Recruiters need to understand
  why a match was made to trust the system.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from backend.database.knowledge_graph import KnowledgeGraph
from backend.embeddings import RecruitingKnowledgeGraphEmbedder
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(vec1, vec2))


class TeamPersonMatcher:
    """
    Matches candidates to teams and interviewers.
    
    Uses multi-criteria evaluation:
    - Embedding similarity (30% weight)
    - Team needs match (25% weight)
    - Expertise match (15% weight)
    - arXiv research (25% weight) - HEAVILY WEIGHTED
    - Success rates/capacity (5% weight)
    
    Uses bandit algorithm for principled selection.
    
    Note: arXiv research is heavily weighted because published research indicates
    strong technical depth, research experience, and proven contributions.
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None,
        bandit: Optional[GraphWarmStartedFGTS] = None
    ):
        """
        Initialize matcher.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            embedder: Embedder instance (creates new if None)
            bandit: Bandit instance (creates new if None)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.bandit = bandit or GraphWarmStartedFGTS()
        
        logger.info("Initialized TeamPersonMatcher")
    
    def match_to_team(self, candidate_id: str) -> Dict[str, Any]:
        """
        Find best team for candidate.
        
        Evaluates all teams using:
        - Embedding similarity (30%)
        - Team needs match (25%)
        - Expertise match (15%)
        - arXiv research (25%) - HEAVILY WEIGHTED
        - Team size/capacity (5%)
        
        Uses bandit for final selection.
        
        Args:
            candidate_id: Candidate ID
        
        Returns:
            Match result with team_id, score, reasoning
        """
        logger.info(f"Matching candidate {candidate_id} to team")
        
        candidate = self.kg.get_candidate(candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return {"error": f"Candidate {candidate_id} not found"}
        
        # Get all teams
        teams = self.kg.get_all_teams()
        if not teams:
            logger.warning("No teams found")
            return {"error": "No teams available"}
        
        logger.info(f"Evaluating {len(teams)} teams")
        
        # Generate candidate embedding
        candidate_emb = self.embedder.embed_candidate(candidate)
        
        # Compute match scores for all teams
        matches = []
        for team in teams:
            team_emb = self.embedder.embed_team(team)
            similarity = cosine_similarity(candidate_emb, team_emb)
            
            # Additional factors
            needs_match = self._check_needs_match(candidate, team)
            expertise_match = self._check_expertise_match(candidate, team)
            
            # arXiv research boost (HEAVILY WEIGHTED - research is a strong signal)
            arxiv_boost = self._check_arxiv_research(candidate)
            
            # Team capacity factor (prefer teams with open positions)
            open_positions = len(team.get('open_positions', []))
            capacity_factor = min(open_positions / 3.0, 1.0) if open_positions > 0 else 0.5
            
            # Weighted score - arXiv research gets 25% weight (very significant)
            # Adjusted weights: similarity 30%, needs 25%, expertise 15%, arxiv 25%, capacity 5%
            score = (
                similarity * 0.30 +
                needs_match * 0.25 +
                expertise_match * 0.15 +
                arxiv_boost * 0.25 +  # HEAVY WEIGHT for arXiv research
                capacity_factor * 0.05
            )
            
            matches.append({
                "team_id": team['id'],
                "team": team,
                "score": score,
                "similarity": similarity,
                "needs_match": needs_match,
                "expertise_match": expertise_match,
                "arxiv_boost": arxiv_boost,
                "capacity_factor": capacity_factor
            })
        
        logger.info(f"Computed {len(matches)} team match scores")
        
        # Use bandit to select best team
        # Initialize bandit with teams as arms, candidate as context
        self.bandit.initialize_from_embeddings(
            [m['team'] for m in matches],
            candidate
        )
        
        selected_idx = self.bandit.select_candidate()
        best_match = matches[selected_idx]
        
        logger.info(f"Selected team {best_match['team_id']} with score {best_match['score']:.3f}")
        
        return {
            "candidate_id": candidate_id,
            "team_id": best_match['team_id'],
            "team": best_match['team'],
            "match_score": best_match['score'],
            "similarity": best_match['similarity'],
            "needs_match": best_match['needs_match'],
            "expertise_match": best_match['expertise_match'],
            "arxiv_boost": best_match.get('arxiv_boost', 0.0),
            "reasoning": self._generate_team_reasoning(candidate, best_match['team'], best_match)
        }
    
    def match_to_person(self, candidate_id: str, team_id: str) -> Dict[str, Any]:
        """
        Find best interviewer for candidate within a team.
        
        Evaluates team's interviewers using:
        - Embedding similarity (30%)
        - Expertise match (20%)
        - arXiv research (25%) - HEAVILY WEIGHTED
        - Success rate (15%)
        - Cluster success rate (10%)
        
        Uses bandit for final selection.
        
        Args:
            candidate_id: Candidate ID
            team_id: Team ID
        
        Returns:
            Match result with interviewer_id, score, reasoning
        """
        logger.info(f"Matching candidate {candidate_id} to interviewer in team {team_id}")
        
        candidate = self.kg.get_candidate(candidate_id)
        team = self.kg.get_team(team_id)
        
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return {"error": f"Candidate {candidate_id} not found"}
        
        if not team:
            logger.error(f"Team {team_id} not found")
            return {"error": f"Team {team_id} not found"}
        
        # Get team members (interviewers)
        interviewers = self.kg.get_team_members(team_id)
        if not interviewers:
            logger.warning(f"No interviewers found for team {team_id}")
            return {"error": f"No interviewers found for team {team_id}"}
        
        logger.info(f"Evaluating {len(interviewers)} interviewers")
        
        # Generate candidate embedding
        candidate_emb = self.embedder.embed_candidate(candidate)
        
        # Compute match scores for all interviewers
        matches = []
        for interviewer in interviewers:
            interviewer_emb = self.embedder.embed_interviewer(interviewer)
            similarity = cosine_similarity(candidate_emb, interviewer_emb)
            
            # Additional factors
            expertise_match = self._check_expertise_match(candidate, interviewer)
            success_rate = interviewer.get('success_rate', 0.5)
            
            # arXiv research boost (HEAVILY WEIGHTED)
            arxiv_boost = self._check_arxiv_research(candidate)
            
            # Cluster success rate (if candidate has ability_cluster)
            candidate_cluster = candidate.get('ability_cluster')
            cluster_success = 0.5  # Default
            if candidate_cluster:
                cluster_success = interviewer.get('cluster_success_rates', {}).get(
                    candidate_cluster, 0.5
                )
            
            # Weighted score - arXiv research gets 25% weight
            # Adjusted weights: similarity 30%, expertise 20%, arxiv 25%, success 15%, cluster 10%
            score = (
                similarity * 0.30 +
                expertise_match * 0.20 +
                arxiv_boost * 0.25 +  # HEAVY WEIGHT for arXiv research
                success_rate * 0.15 +
                cluster_success * 0.10
            )
            
            matches.append({
                "interviewer_id": interviewer['id'],
                "interviewer": interviewer,
                "score": score,
                "similarity": similarity,
                "expertise_match": expertise_match,
                "arxiv_boost": arxiv_boost,
                "success_rate": success_rate,
                "cluster_success": cluster_success
            })
        
        logger.info(f"Computed {len(matches)} interviewer match scores")
        
        # Use bandit to select best interviewer
        # Initialize bandit with interviewers as arms, candidate as context
        self.bandit.initialize_from_embeddings(
            [m['interviewer'] for m in matches],
            candidate
        )
        
        selected_idx = self.bandit.select_candidate()
        best_match = matches[selected_idx]
        
        logger.info(f"Selected interviewer {best_match['interviewer_id']} with score {best_match['score']:.3f}")
        
        return {
            "candidate_id": candidate_id,
            "team_id": team_id,
            "interviewer_id": best_match['interviewer_id'],
            "interviewer": best_match['interviewer'],
            "match_score": best_match['score'],
            "similarity": best_match['similarity'],
            "expertise_match": best_match['expertise_match'],
            "arxiv_boost": best_match.get('arxiv_boost', 0.0),
            "success_rate": best_match['success_rate'],
            "cluster_success": best_match['cluster_success'],
            "reasoning": self._generate_person_reasoning(candidate, best_match['interviewer'], best_match)
        }
    
    def _check_needs_match(self, candidate: Dict[str, Any], team: Dict[str, Any]) -> float:
        """
        Check how well candidate matches team needs.
        
        Args:
            candidate: Candidate profile
            team: Team profile
        
        Returns:
            Match score (0.0-1.0)
        """
        team_needs = set(need.lower() for need in team.get('needs', []))
        candidate_skills = set(skill.lower() for skill in candidate.get('skills', []))
        
        if not team_needs:
            return 0.5  # Neutral if no needs specified
        
        overlap = len(team_needs.intersection(candidate_skills))
        return min(overlap / len(team_needs), 1.0)
    
    def _check_expertise_match(self, candidate: Dict[str, Any], team_or_interviewer: Dict[str, Any]) -> float:
        """
        Check expertise/domain overlap.
        
        Args:
            candidate: Candidate profile
            team_or_interviewer: Team or interviewer profile
        
        Returns:
            Match score (0.0-1.0)
        """
        candidate_domains = set(d.lower() for d in candidate.get('domains', []))
        other_expertise = set(e.lower() for e in team_or_interviewer.get('expertise', []))
        
        if not other_expertise:
            return 0.5
        
        overlap = len(candidate_domains.intersection(other_expertise))
        return min(overlap / len(other_expertise), 1.0)
    
    def _check_arxiv_research(self, candidate: Dict[str, Any]) -> float:
        """
        Check if candidate has arXiv research and return boost factor.
        
        arXiv research is heavily weighted because it indicates:
        - Strong technical depth
        - Research experience
        - Published contributions
        - Academic rigor
        
        Args:
            candidate: Candidate profile
        
        Returns:
            Boost factor (0.0-1.0), where 1.0 = significant arXiv research
        """
        papers = candidate.get('papers', [])
        arxiv_author_id = candidate.get('arxiv_author_id')
        orcid_id = candidate.get('orcid_id')
        research_contributions = candidate.get('research_contributions', [])
        
        # Check if candidate has arXiv research
        has_arxiv = bool(
            papers or 
            arxiv_author_id or 
            orcid_id or
            research_contributions
        )
        
        if not has_arxiv:
            return 0.0
        
        # Calculate boost based on research depth
        boost = 0.0
        
        # Base boost for having any arXiv research
        if papers or arxiv_author_id or orcid_id:
            boost += 0.3
        
        # Additional boost for number of papers
        if papers:
            paper_count = len(papers)
            if paper_count >= 20:
                boost += 0.4  # Very experienced researcher
            elif paper_count >= 10:
                boost += 0.3  # Experienced researcher
            elif paper_count >= 5:
                boost += 0.2  # Active researcher
            else:
                boost += 0.1  # Some research
        
        # Boost for research contributions (actual work, not just papers)
        if research_contributions:
            boost += 0.2
        
        # Boost for having research areas/domains from arXiv
        research_areas = candidate.get('research_areas', [])
        if research_areas:
            boost += 0.1
        
        # Cap at 1.0
        return min(boost, 1.0)
    
    def _generate_team_reasoning(
        self,
        candidate: Dict[str, Any],
        team: Dict[str, Any],
        match_data: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable reasoning for team match.
        
        Args:
            candidate: Candidate profile
            team: Team profile
            match_data: Match score data
        
        Returns:
            Reasoning string
        """
        parts = []
        
        if match_data['similarity'] >= 0.7:
            parts.append(f"Strong embedding similarity ({match_data['similarity']:.2f})")
        
        if match_data['needs_match'] >= 0.7:
            parts.append(f"Excellent team needs match ({match_data['needs_match']:.1%})")
        
        if match_data['expertise_match'] >= 0.7:
            parts.append(f"Strong expertise overlap ({match_data['expertise_match']:.1%})")
        
        # Highlight arXiv research boost
        arxiv_boost = match_data.get('arxiv_boost', 0.0)
        if arxiv_boost >= 0.5:
            papers = candidate.get('papers', [])
            paper_count = len(papers) if papers else 0
            if paper_count > 0:
                parts.append(f"Strong arXiv research background ({paper_count} papers, boost: {arxiv_boost:.1%})")
            else:
                parts.append(f"arXiv research background (boost: {arxiv_boost:.1%})")
        
        if len(team.get('open_positions', [])) > 0:
            parts.append(f"Team has {len(team.get('open_positions', []))} open position(s)")
        
        if not parts:
            parts.append(f"Moderate match (score: {match_data['score']:.2f})")
        
        return f"Matched to {team.get('name', team['id'])}: {'; '.join(parts)}"
    
    def _generate_person_reasoning(
        self,
        candidate: Dict[str, Any],
        interviewer: Dict[str, Any],
        match_data: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable reasoning for interviewer match.
        
        Args:
            candidate: Candidate profile
            interviewer: Interviewer profile
            match_data: Match score data
        
        Returns:
            Reasoning string
        """
        parts = []
        
        if match_data['similarity'] >= 0.7:
            parts.append(f"Strong embedding similarity ({match_data['similarity']:.2f})")
        
        if match_data['expertise_match'] >= 0.7:
            parts.append(f"Strong expertise match ({match_data['expertise_match']:.1%})")
        
        # Highlight arXiv research boost
        arxiv_boost = match_data.get('arxiv_boost', 0.0)
        if arxiv_boost >= 0.5:
            papers = candidate.get('papers', [])
            paper_count = len(papers) if papers else 0
            if paper_count > 0:
                parts.append(f"Strong arXiv research background ({paper_count} papers, boost: {arxiv_boost:.1%})")
            else:
                parts.append(f"arXiv research background (boost: {arxiv_boost:.1%})")
        
        if match_data['success_rate'] >= 0.6:
            parts.append(f"High success rate ({match_data['success_rate']:.1%})")
        
        candidate_cluster = candidate.get('ability_cluster')
        if candidate_cluster and match_data.get('cluster_success', 0.5) >= 0.6:
            parts.append(f"Strong track record with {candidate_cluster} candidates")
        
        if not parts:
            parts.append(f"Moderate match (score: {match_data['score']:.2f})")
        
        return f"Matched to {interviewer.get('name', interviewer['id'])}: {'; '.join(parts)}"
    
    def close(self):
        """Close knowledge graph connection."""
        self.kg.close()

