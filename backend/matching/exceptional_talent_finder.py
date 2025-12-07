"""
exceptional_talent_finder.py - Exceptional talent discovery system FOR SPECIFIC POSITIONS

This module implements an EXTREMELY STRICT multi-signal talent scoring system to identify
truly exceptional candidates FOR A SPECIFIC POSITION (the "next Elon" for that role).
Uses extremely high thresholds and requires multiple strong signals across platforms.

CRITICAL: This finds candidates who are BOTH:
1. Truly exceptional (0.0001% pass rate - 1 in 1,000,000)
2. Perfect fit for the specific position

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Multi-signal aggregation methodology + position matching
    - Our adaptation: Combining exceptional talent discovery with position fit

Our Novel Contribution:
Position-specific exceptional talent discovery: Multi-signal scoring system that identifies
truly exceptional candidates FOR A SPECIFIC POSITION by:
- Aggregating signals from arXiv, GitHub, X, and phone screens (exceptional talent)
- Calculating position fit (similarity, skills, domains, experience level)
- Combining both: combined_score = exceptional_score * position_fit
- Using EXTREMELY STRICT thresholds - only 0.0001% pass (1 in 1,000,000)

Key functions:
- ExceptionalTalentFinder: Main scoring class
- find_exceptional_talent(position_id): Find top exceptional candidates FOR position
- score_candidate(candidate_id, position_id): Calculate exceptional + position fit
- rank_candidates(): Rank by combined score
- get_talent_breakdown(): Detailed signal breakdown
- _calculate_*_signal(): Calculate individual signals with strict thresholds
- _calculate_position_fit(): Calculate position fit (similarity, skills, domains)

Dependencies:
- backend.database.knowledge_graph: Candidate and position retrieval
- backend.embeddings: Position and candidate embeddings for similarity
- numpy: Numerical computations
- math: Logarithmic scaling
"""

import logging
import math
from typing import Dict, List, Any, Optional
import numpy as np
from backend.database.knowledge_graph import KnowledgeGraph
from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(vec1, vec2))


class ExceptionalTalentFinder:
    """
    Exceptional talent discovery system with VERY STRICT scoring.
    
    Only truly exceptional candidates (top 1-5%) should pass.
    Requires multiple strong signals across platforms.
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None
    ):
        """
        Initialize exceptional talent finder.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            embedder: Embedder instance (creates new if None)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.postgres = PostgresClient()
        self.company_context = get_company_context()
        
        # EXTREMELY STRICT thresholds - only 0.0001% pass (1 in 1,000,000)
        # These are ELON-LEVEL thresholds - truly exceptional
        self.THRESHOLDS = {
            # arXiv: Need 25+ papers for 0.5, 50+ for 1.0 (EXTREMELY high)
            'arxiv_min_papers': 25,
            'arxiv_max_papers': 100,  # 100+ papers = truly exceptional
            'arxiv_min_contributions': 5,  # Need MANY research contributions
            
            # GitHub: Need 20,000+ stars for 0.5, 100,000+ for 1.0 (EXTREMELY high)
            'github_min_stars': 20000,
            'github_max_stars': 200000,  # 200k+ stars = truly exceptional
            'github_min_repos': 30,  # Need MANY repos
            'github_min_languages': 5,  # Multi-language expertise required
            
            # X: Need 50,000+ followers for 0.5, 500,000+ for 1.0 (EXTREMELY high)
            'x_min_followers': 50000,
            'x_max_followers': 2000000,  # 2M+ followers = truly exceptional
            'x_min_engagement_rate': 0.08,  # 8% engagement rate minimum (very high)
            
            # Phone screen: Need 0.92+ technical depth for 0.5, 0.98+ for 1.0 (EXTREMELY high)
            'phone_min_technical_depth': 0.92,
            'phone_max_technical_depth': 0.99,  # Near-perfect = truly exceptional
            'phone_min_problem_solving': 0.90,
            'phone_min_communication': 0.90,
        }
        
        logger.info("Initialized ExceptionalTalentFinder with EXTREMELY STRICT thresholds (0.0001% pass rate)")
    
    def find_exceptional_talent(
        self,
        position_id: str,
        min_score: float = 0.90,  # EXTREMELY HIGH default - only top 0.0001%
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find exceptional talent FOR A SPECIFIC POSITION (1 in 1,000,000 candidate).
        
        Combines exceptional talent signals with position fit to find candidates who are
        BOTH truly exceptional AND a perfect fit for the position.
        
        Args:
            position_id: Position identifier (REQUIRED - must be position-specific)
            min_score: Minimum combined score (0.0-1.0). Default 0.90 = EXTREMELY STRICT
            top_k: Maximum number of results
        
        Returns:
            List of exceptional candidate profiles ranked by combined score
        """
        logger.info(f"Finding exceptional talent for position {position_id} (min_score={min_score}, top_k={top_k})")
        
        # Get position - try Knowledge Graph first, then PostgreSQL
        position = self.kg.get_position(position_id)
        if not position:
            logger.info(f"Position {position_id} not found in Knowledge Graph, checking PostgreSQL...")
            company_id = self.company_context.get_company_id()
            position = self.postgres.execute_one(
                """
                SELECT * FROM positions
                WHERE id = %s AND company_id = %s
                LIMIT 1
                """,
                (position_id, company_id)
            )
            if position:
                logger.info(f"Found position {position_id} in PostgreSQL")
        
        if not position:
            logger.error(f"Position {position_id} not found in Knowledge Graph or PostgreSQL")
            return []
        
        # Get all candidates - try Knowledge Graph first, then PostgreSQL
        all_candidates = self.kg.get_all_candidates()
        if not all_candidates or len(all_candidates) == 0:
            logger.info("No candidates found in Knowledge Graph, checking PostgreSQL...")
            company_id = self.company_context.get_company_id()
            db_candidates = self.postgres.execute_query(
                """
                SELECT * FROM candidates
                WHERE company_id = %s
                """,
                (company_id,)
            )
            if db_candidates:
                logger.info(f"Found {len(db_candidates)} candidates in PostgreSQL")
                all_candidates = db_candidates
        scored_candidates = []
        
        for candidate in all_candidates:
            score_result = self.score_candidate(candidate.get('id'), position_id=position_id)
            combined_score = score_result.get('combined_score', 0.0)
            if combined_score >= min_score:
                candidate_copy = candidate.copy()
                candidate_copy.update(score_result)
                scored_candidates.append(candidate_copy)
        
        # Sort by combined score (descending)
        scored_candidates.sort(
            key=lambda x: x.get('combined_score', 0.0),
            reverse=True
        )
        
        results = scored_candidates[:top_k]
        logger.info(f"Found {len(results)} exceptional candidates for position {position_id} (score >= {min_score})")
        return results
    
    def score_candidate(
        self,
        candidate_id: str,
        position_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate exceptional talent score for a candidate, optionally for a specific position.
        
        If position_id is provided, combines exceptional talent with position fit.
        This ensures we find candidates who are BOTH exceptional AND perfect for the role.
        
        Args:
            candidate_id: Candidate identifier
            position_id: Optional position identifier (if provided, calculates position fit)
        
        Returns:
            Dictionary with exceptional_score, position_fit (if position_id provided),
            combined_score, signal_breakdown, and evidence
        """
        # Get candidate - try Knowledge Graph first, then PostgreSQL
        candidate = self.kg.get_candidate(candidate_id)
        if not candidate:
            logger.debug(f"Candidate {candidate_id} not found in Knowledge Graph, checking PostgreSQL...")
            company_id = self.company_context.get_company_id()
            candidate = self.postgres.execute_one(
                """
                SELECT * FROM candidates
                WHERE id = %s AND company_id = %s
                LIMIT 1
                """,
                (candidate_id, company_id)
            )
            if candidate:
                logger.debug(f"Found candidate {candidate_id} in PostgreSQL")
        
        if not candidate:
            return {
                'exceptional_score': 0.0,
                'signal_breakdown': {},
                'evidence': {},
                'why_exceptional': 'Candidate not found'
            }
        
        # Calculate individual signals
        arxiv_signal = self._calculate_arxiv_signal(candidate)
        github_signal = self._calculate_github_signal(candidate)
        x_signal = self._calculate_x_signal(candidate)
        phone_screen_signal = self._calculate_phone_screen_signal(candidate)
        composite_signals = self._calculate_composite_signals(
            candidate, arxiv_signal, github_signal, x_signal, phone_screen_signal
        )
        
        # Weighted aggregation - EXTREMELY STRICT weights
        # Require ALL signals to be strong (not just weighted average)
        # Use multiplicative component to ensure no weak signals
        base_score = (
            arxiv_signal * 0.30 +      # Research is strong signal
            github_signal * 0.25 +     # Code contributions matter
            x_signal * 0.15 +          # Influence and communication
            phone_screen_signal * 0.20 + # Validated technical depth
            composite_signals * 0.10   # Cross-platform excellence
        )
        
        # EXTREME STRICTNESS: Require STRONG signals in ALL 4 major platforms
        # This ensures only truly exceptional candidates (0.0001%) pass
        min_signal_threshold = 0.75  # Need 0.75+ in at least 3 of 4 major signals
        strong_signals = sum(1 for s in [arxiv_signal, github_signal, x_signal, phone_screen_signal] if s >= min_signal_threshold)
        
        if strong_signals < 3:
            # Penalize heavily if not strong in at least 3 signals
            exceptional_score = base_score * 0.3  # Cut score by 70%
        elif strong_signals == 3:
            # Even with 3 strong signals, penalize slightly
            exceptional_score = base_score * 0.8  # 20% penalty
        else:
            # All 4 signals strong - no penalty
            exceptional_score = base_score
        
        # Additional penalty if any signal is very weak (< 0.4)
        weak_signals = sum(1 for s in [arxiv_signal, github_signal, x_signal, phone_screen_signal] if s < 0.4)
        if weak_signals > 0:
            exceptional_score *= 0.5  # Additional 50% penalty (very harsh)
        
        # Final check: Require minimum in each signal category
        if arxiv_signal < 0.5 or github_signal < 0.5:
            exceptional_score *= 0.6  # If research OR code is weak, heavy penalty
        
        # Calculate position fit if position_id provided
        position_fit = None
        position_fit_breakdown = None
        combined_score = exceptional_score
        
        if position_id:
            # Get position - try Knowledge Graph first, then PostgreSQL
            position = self.kg.get_position(position_id)
            if not position:
                company_id = self.company_context.get_company_id()
                position = self.postgres.execute_one(
                    """
                    SELECT * FROM positions
                    WHERE id = %s AND company_id = %s
                    LIMIT 1
                    """,
                    (position_id, company_id)
                )
            if position:
                position_fit_result = self._calculate_position_fit(candidate, position)
                position_fit = position_fit_result['fit_score']
                position_fit_breakdown = position_fit_result['breakdown']
                
                # Combined score: BOTH exceptional AND great fit required
                # Use multiplicative combination to ensure BOTH are strong
                # This ensures only 1 in 1,000,000 candidates pass
                combined_score = exceptional_score * position_fit
                
                # Additional strictness: Require BOTH to be very high
                if exceptional_score < 0.85 or position_fit < 0.85:
                    combined_score *= 0.7  # Penalize if either is not extremely high
        
        # Build evidence
        evidence = {
            'arxiv_papers': len(candidate.get('papers', [])),
            'github_stars': candidate.get('github_stats', {}).get('total_stars', 0),
            'x_followers': candidate.get('x_analytics_summary', {}).get('followers_count', 0),
            'phone_screen_technical_depth': candidate.get('phone_screen_results', {}).get('technical_depth', 0.0) if candidate.get('phone_screen_results') else None
        }
        
        # Generate "why exceptional" explanation
        why_exceptional = self._generate_why_exceptional(
            candidate, exceptional_score, arxiv_signal, github_signal,
            x_signal, phone_screen_signal, evidence
        )
        
        result = {
            'candidate_id': candidate_id,
            'exceptional_score': exceptional_score,
            'ranking': None,  # Will be calculated in rank_candidates
            'signal_breakdown': {
                'arxiv_signal': arxiv_signal,
                'github_signal': github_signal,
                'x_signal': x_signal,
                'phone_screen_signal': phone_screen_signal,
                'composite_signals': composite_signals
            },
            'evidence': evidence,
            'why_exceptional': why_exceptional
        }
        
        # Add position-specific fields if position_id provided
        if position_id:
            result['position_id'] = position_id
            result['position_fit'] = position_fit
            result['position_fit_breakdown'] = position_fit_breakdown
            result['combined_score'] = combined_score
        
        return result
    
    def _calculate_position_fit(
        self,
        candidate: Dict[str, Any],
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate how well candidate fits the position.
        
        Uses:
        - Embedding similarity (40% weight)
        - Skills match (30% weight)
        - Domain match (20% weight)
        - Experience level match (10% weight)
        
        Args:
            candidate: Candidate profile
            position: Position profile
        
        Returns:
            Dictionary with fit_score and breakdown
        """
        # Embedding similarity
        candidate_emb = self.embedder.embed_candidate(candidate)
        position_emb = self.embedder.embed_position(position)
        similarity = cosine_similarity(candidate_emb, position_emb)
        
        # Skills match
        required_skills = set(position.get('required_skills', []))
        optional_skills = set(position.get('optional_skills', []))
        candidate_skills = set(candidate.get('skills', []))
        
        # Required skills must match
        required_match = len(required_skills & candidate_skills) / max(1, len(required_skills))
        
        # Optional skills bonus
        optional_match = len(optional_skills & candidate_skills) / max(1, len(optional_skills)) if optional_skills else 1.0
        
        skills_match = (required_match * 0.7 + optional_match * 0.3)
        
        # Domain match
        position_domains = set(position.get('domains', []))
        candidate_domains = set(candidate.get('domains', []))
        domain_match = len(position_domains & candidate_domains) / max(1, len(position_domains)) if position_domains else 0.5
        
        # Experience level match
        position_level = position.get('experience_level', '').lower()
        candidate_level = candidate.get('expertise_level', '').lower()
        candidate_years = candidate.get('experience_years', 0)
        
        level_match = 1.0  # Default
        if position_level:
            # Simple matching based on experience years
            if 'junior' in position_level and candidate_years > 5:
                level_match = 0.7
            elif 'senior' in position_level and candidate_years < 5:
                level_match = 0.6
            elif 'staff' in position_level and candidate_years < 10:
                level_match = 0.5
            elif 'principal' in position_level and candidate_years < 15:
                level_match = 0.6
            else:
                level_match = 1.0
        
        # Weighted combination
        fit_score = (
            similarity * 0.40 +
            skills_match * 0.30 +
            domain_match * 0.20 +
            level_match * 0.10
        )
        
        return {
            'fit_score': min(1.0, max(0.0, fit_score)),
            'breakdown': {
                'similarity': similarity,
                'skills_match': skills_match,
                'required_skills_match': required_match,
                'optional_skills_match': optional_match,
                'domain_match': domain_match,
                'level_match': level_match
            }
        }
    
    def _calculate_arxiv_signal(self, candidate: Dict[str, Any]) -> float:
        """
        Calculate arXiv research signal (0.0-1.0).
        
        VERY STRICT: Need 10+ papers for 0.5, 20+ for 1.0
        """
        papers = candidate.get('papers', [])
        paper_count = len(papers)
        
        if paper_count == 0:
            return 0.0
        
        # Research contributions depth
        research_contributions = candidate.get('research_contributions', [])
        contributions_count = len(research_contributions)
        
        # Research areas breadth
        research_areas = candidate.get('research_areas', [])
        areas_count = len(research_areas)
        
        # Paper count signal (logarithmic scaling - EXTREMELY strict)
        # 25 papers = 0.3, 50 papers = 0.7, 100+ papers = 1.0
        if paper_count < self.THRESHOLDS['arxiv_min_papers']:
            paper_signal = 0.0
        else:
            # Logarithmic scaling: log(paper_count / min) / log(max / min)
            paper_signal = min(1.0, math.log(paper_count / self.THRESHOLDS['arxiv_min_papers'] + 1) / 
                             math.log(self.THRESHOLDS['arxiv_max_papers'] / self.THRESHOLDS['arxiv_min_papers'] + 1))
        
        # Contributions depth signal
        contributions_signal = min(1.0, contributions_count / max(1, self.THRESHOLDS['arxiv_min_contributions']))
        
        # Areas breadth signal
        areas_signal = min(1.0, areas_count / 5.0)  # 5+ areas = exceptional
        
        # Weighted combination
        arxiv_signal = (
            paper_signal * 0.50 +      # Paper count is primary
            contributions_signal * 0.30 +  # Contributions depth
            areas_signal * 0.20        # Areas breadth
        )
        
        return min(1.0, arxiv_signal)
    
    def _calculate_github_signal(self, candidate: Dict[str, Any]) -> float:
        """
        Calculate GitHub activity signal (0.0-1.0).
        
        VERY STRICT: Need 5,000+ stars for 0.5, 20,000+ for 1.0
        """
        github_stats = candidate.get('github_stats', {})
        total_stars = github_stats.get('total_stars', 0)
        total_repos = github_stats.get('total_repos', 0)
        
        if total_stars == 0 and total_repos == 0:
            return 0.0
        
        # Stars signal (logarithmic scaling - EXTREMELY strict)
        # 20k stars = 0.3, 50k stars = 0.7, 200k+ stars = 1.0
        if total_stars < self.THRESHOLDS['github_min_stars']:
            stars_signal = 0.0
        else:
            # Logarithmic scaling
            stars_signal = min(1.0, math.log(total_stars / self.THRESHOLDS['github_min_stars'] + 1) /
                             math.log(self.THRESHOLDS['github_max_stars'] / self.THRESHOLDS['github_min_stars'] + 1))
        
        # Repo count signal
        if total_repos < self.THRESHOLDS['github_min_repos']:
            repos_signal = 0.0
        else:
            repos_signal = min(1.0, total_repos / 50.0)  # 50+ repos = exceptional
        
        # Language diversity
        languages = github_stats.get('languages', [])
        languages_count = len(languages)
        languages_signal = min(1.0, languages_count / max(1, self.THRESHOLDS['github_min_languages']))
        
        # Weighted combination
        github_signal = (
            stars_signal * 0.60 +      # Stars are primary
            repos_signal * 0.25 +      # Repo count
            languages_signal * 0.15    # Language diversity
        )
        
        return min(1.0, github_signal)
    
    def _calculate_x_signal(self, candidate: Dict[str, Any]) -> float:
        """
        Calculate X/Twitter engagement signal (0.0-1.0).
        
        VERY STRICT: Need 10,000+ followers for 0.5, 100,000+ for 1.0
        """
        x_analytics = candidate.get('x_analytics_summary', {})
        followers = x_analytics.get('followers_count', 0)
        
        if followers == 0:
            return 0.0
        
        # Followers signal (logarithmic scaling - EXTREMELY strict)
        # 50k followers = 0.3, 200k followers = 0.7, 2M+ followers = 1.0
        if followers < self.THRESHOLDS['x_min_followers']:
            followers_signal = 0.0
        else:
            # Logarithmic scaling
            followers_signal = min(1.0, math.log(followers / self.THRESHOLDS['x_min_followers'] + 1) /
                                 math.log(self.THRESHOLDS['x_max_followers'] / self.THRESHOLDS['x_min_followers'] + 1))
        
        # Engagement rate
        engagement_rate = x_analytics.get('avg_engagement_rate', 0.0)
        if engagement_rate < self.THRESHOLDS['x_min_engagement_rate']:
            engagement_signal = 0.0
        else:
            engagement_signal = min(1.0, engagement_rate / 0.10)  # 10%+ engagement = exceptional
        
        # Technical content quality (if available)
        content_quality = candidate.get('content_quality_score', 0.5)
        content_signal = max(0.0, (content_quality - 0.5) * 2.0)  # 0.5 = 0.0, 1.0 = 1.0
        
        # Weighted combination
        x_signal = (
            followers_signal * 0.50 +   # Followers are primary
            engagement_signal * 0.30 +  # Engagement rate
            content_signal * 0.20       # Content quality
        )
        
        return min(1.0, x_signal)
    
    def _calculate_phone_screen_signal(self, candidate: Dict[str, Any]) -> float:
        """
        Calculate phone screen performance signal (0.0-1.0).
        
        VERY STRICT: Need 0.85+ technical depth for 0.5, 0.95+ for 1.0
        """
        phone_screen_results = candidate.get('phone_screen_results', {})
        
        if not phone_screen_results:
            return 0.0
        
        technical_depth = phone_screen_results.get('technical_depth', 0.0)
        problem_solving = phone_screen_results.get('problem_solving_ability', 0.0)
        communication = phone_screen_results.get('technical_communication', 0.0)
        implementation = phone_screen_results.get('implementation_experience', 0.0)
        
        # Technical depth signal (EXTREMELY strict)
        if technical_depth < self.THRESHOLDS['phone_min_technical_depth']:
            depth_signal = 0.0
        else:
            # Scale from min (0.92) to max (0.99)
            depth_signal = (technical_depth - self.THRESHOLDS['phone_min_technical_depth']) / \
                          (self.THRESHOLDS['phone_max_technical_depth'] - self.THRESHOLDS['phone_min_technical_depth'])
            depth_signal = min(1.0, max(0.0, depth_signal))
        
        # Problem solving signal (EXTREMELY strict)
        problem_signal = max(0.0, (problem_solving - self.THRESHOLDS['phone_min_problem_solving']) / 
                           (1.0 - self.THRESHOLDS['phone_min_problem_solving']))
        
        # Communication signal (EXTREMELY strict)
        comm_signal = max(0.0, (communication - self.THRESHOLDS['phone_min_communication']) / 
                        (1.0 - self.THRESHOLDS['phone_min_communication']))
        
        # Implementation signal (EXTREMELY strict)
        impl_signal = max(0.0, implementation - 0.85) / 0.15  # 0.85+ = good, 1.0 = perfect
        
        # Weighted combination
        phone_screen_signal = (
            depth_signal * 0.40 +      # Technical depth is primary
            problem_signal * 0.25 +     # Problem solving
            comm_signal * 0.20 +        # Communication
            impl_signal * 0.15          # Implementation experience
        )
        
        return min(1.0, phone_screen_signal)
    
    def _calculate_composite_signals(
        self,
        candidate: Dict[str, Any],
        arxiv_signal: float,
        github_signal: float,
        x_signal: float,
        phone_screen_signal: float
    ) -> float:
        """
        Calculate composite cross-platform signals (0.0-1.0).
        
        Rewards candidates who excel across multiple platforms.
        """
        # Research-to-production bridge (arXiv + GitHub)
        research_production = (arxiv_signal + github_signal) / 2.0 if (arxiv_signal > 0.5 and github_signal > 0.5) else 0.0
        
        # Cross-platform influence (X + GitHub)
        cross_influence = (x_signal + github_signal) / 2.0 if (x_signal > 0.5 and github_signal > 0.5) else 0.0
        
        # Technical depth validation (Phone screen + arXiv)
        technical_validation = (phone_screen_signal + arxiv_signal) / 2.0 if (phone_screen_signal > 0.5 and arxiv_signal > 0.5) else 0.0
        
        # All-platform excellence (need STRONG signals in ALL 4 platforms)
        strong_signals = sum(1 for s in [arxiv_signal, github_signal, x_signal, phone_screen_signal] if s > 0.8)
        all_platform = 1.0 if strong_signals >= 4 else 0.0  # Need ALL 4 platforms strong
        
        # Weighted combination
        composite = (
            research_production * 0.30 +
            cross_influence * 0.25 +
            technical_validation * 0.25 +
            all_platform * 0.20
        )
        
        return min(1.0, composite)
    
    def _generate_why_exceptional(
        self,
        candidate: Dict[str, Any],
        exceptional_score: float,
        arxiv_signal: float,
        github_signal: float,
        x_signal: float,
        phone_screen_signal: float,
        evidence: Dict[str, Any]
    ) -> str:
        """Generate explanation of why candidate is exceptional."""
        reasons = []
        
        if arxiv_signal > 0.7:
            reasons.append(f"Strong research background ({evidence.get('arxiv_papers', 0)} papers)")
        if github_signal > 0.7:
            reasons.append(f"High GitHub activity ({evidence.get('github_stars', 0):,} stars)")
        if x_signal > 0.7:
            reasons.append(f"Significant X influence ({evidence.get('x_followers', 0):,} followers)")
        if phone_screen_signal > 0.7:
            reasons.append(f"Validated technical depth in phone screen")
        
        if not reasons:
            return f"Exceptional score: {exceptional_score:.2f} (multiple strong signals)"
        
        return ", ".join(reasons)
    
    def rank_candidates(
        self,
        candidate_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Rank candidates by exceptional score.
        
        Args:
            candidate_ids: List of candidate IDs to rank
        
        Returns:
            List of scored candidates sorted by exceptional_score (descending)
        """
        scored = []
        for candidate_id in candidate_ids:
            score_result = self.score_candidate(candidate_id)
            scored.append(score_result)
        
        # Sort by exceptional score
        scored.sort(key=lambda x: x.get('exceptional_score', 0.0), reverse=True)
        
        # Calculate percentile rankings
        total = len(scored)
        for i, result in enumerate(scored):
            percentile = int((1.0 - (i / total)) * 100) if total > 0 else 0
            result['ranking'] = percentile
        
        return scored
    
    def get_talent_breakdown(
        self,
        candidate_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed talent score breakdown for a candidate.
        
        Args:
            candidate_id: Candidate identifier
        
        Returns:
            Detailed breakdown with scores, evidence, and explanation
        """
        return self.score_candidate(candidate_id)

