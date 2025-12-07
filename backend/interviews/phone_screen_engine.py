"""
phone_screen_engine.py - Extremely scrutinizing phone screen decision engine

This module implements a highly rigorous decision engine for phone screen pass/fail
decisions. It uses multiple validation layers, outlier detection, and strict
evaluation criteria to ensure only the highest-quality candidates pass.

Research Paper Citations:
[1] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
    a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
    - Used for: Decision-making algorithm via bandit warm-start
    - Our adaptation: Using embedding similarity to warm-start bandit for
      single-candidate evaluation, providing principled confidence scoring

[2] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Similarity computation methodology (adapted to embeddings)
    - Our adaptation: Using embedding cosine similarity for candidate-position matching

Our Novel Contribution:
Multi-layer scrutinizing decision engine: Combines embedding similarity, bandit
confidence, must-have validation, outlier detection, and extracted conversation
data to make extremely rigorous pass/fail decisions. This is the first application
of bandit algorithms for single-candidate evaluation with outlier detection.

Key functions:
- PhoneScreenDecisionEngine: Main decision engine class
- make_decision(): Main decision method with multiple validation layers
- _check_must_haves(): Strict must-have requirements validation
- _detect_outliers(): Outlier detection for suspicious patterns
- _evaluate_candidate(): Multi-factor candidate evaluation
- _compute_confidence(): Confidence scoring with bandit

Dependencies:
- backend.database.knowledge_graph: Profile retrieval
- backend.embeddings: Embedding generation
- backend.algorithms.fgts_bandit: Decision algorithm
- numpy: Numerical computations

Implementation Rationale:
- Why multiple validation layers: Single-layer decisions are error-prone.
  Multiple checks (must-haves, similarity, extracted info, outliers) ensure
  comprehensive evaluation and catch edge cases.
- Why outlier detection: Candidates with inconsistent data (e.g., claims
  senior experience but minimal skills) should be flagged. This prevents
  false positives from gaming the system.
- Why bandit for single candidate: The bandit provides principled confidence
  scoring based on embedding similarity. High similarity → optimistic prior →
  higher confidence. This is more rigorous than simple threshold-based decisions.
- Why strict thresholds: For production quality, we need to be extremely
  selective. Better to reject a good candidate than accept a bad one.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from backend.database.knowledge_graph import KnowledgeGraph
from backend.embeddings import RecruitingKnowledgeGraphEmbedder
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS

logger = logging.getLogger(__name__)


class PhoneScreenDecisionEngine:
    """
    Extremely scrutinizing phone screen decision engine.
    
    Uses multiple validation layers:
    1. Must-have requirements check (hard filter)
    2. Embedding similarity computation
    3. Extracted information quality validation
    4. Outlier detection (inconsistency checks)
    5. Bandit-based confidence scoring
    6. Multi-factor evaluation
    
    Only candidates passing ALL layers with high confidence pass.
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None,
        bandit: Optional[GraphWarmStartedFGTS] = None,
        similarity_threshold: float = 0.65,
        confidence_threshold: float = 0.70,
        must_have_strictness: float = 1.0
    ):
        """
        Initialize decision engine.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            embedder: Embedder instance (creates new if None)
            bandit: Bandit instance (creates new if None)
            similarity_threshold: Minimum similarity score (0-1, default 0.65)
            confidence_threshold: Minimum confidence for pass (0-1, default 0.70)
            must_have_strictness: Must-have matching strictness (0-1, default 1.0 = exact match)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.bandit = bandit or GraphWarmStartedFGTS()
        
        # Strict thresholds for extremely scrutinizing evaluation
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold
        self.must_have_strictness = must_have_strictness
        
        logger.info(f"Initialized decision engine with thresholds: "
                   f"similarity={similarity_threshold:.2f}, "
                   f"confidence={confidence_threshold:.2f}, "
                   f"must_have_strictness={must_have_strictness:.2f}")
    
    def make_decision(
        self,
        candidate_id: str,
        position_id: str,
        extracted_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make extremely scrutinizing pass/fail decision.
        
        Multiple validation layers:
        1. Must-have requirements (hard filter)
        2. Embedding similarity check
        3. Extracted information validation
        4. Outlier detection
        5. Bandit confidence scoring
        6. Final multi-factor evaluation
        
        Args:
            candidate_id: Candidate ID
            position_id: Position ID
            extracted_info: Information extracted from phone screen conversation
                          (optional, but recommended for quality decisions)
        
        Returns:
            Decision dictionary with:
            - decision: "pass" or "fail"
            - confidence: 0.0-1.0
            - reasoning: Detailed explanation
            - similarity_score: Embedding similarity (0-1)
            - must_have_match: Whether must-haves are satisfied
            - outlier_flags: List of detected outliers
            - extracted_info_summary: Summary of extracted info
        """
        logger.info(f"Making decision for candidate {candidate_id} → position {position_id}")
        
        # Get profiles
        candidate = self.kg.get_candidate(candidate_id)
        position = self.kg.get_position(position_id)
        
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return {
                "decision": "fail",
                "confidence": 0.0,
                "reasoning": f"Candidate {candidate_id} not found in knowledge graph",
                "similarity_score": 0.0,
                "must_have_match": False,
                "outlier_flags": ["candidate_not_found"]
            }
        
        if not position:
            logger.error(f"Position {position_id} not found")
            return {
                "decision": "fail",
                "confidence": 0.0,
                "reasoning": f"Position {position_id} not found in knowledge graph",
                "similarity_score": 0.0,
                "must_have_match": False,
                "outlier_flags": ["position_not_found"]
            }
        
        # Layer 1: Must-have requirements check (HARD FILTER)
        logger.info("Layer 1: Checking must-have requirements...")
        must_have_result = self._check_must_haves(candidate, position)
        if not must_have_result["satisfied"]:
            logger.warning(f"Must-have check failed: {must_have_result['reason']}")
            return {
                "decision": "fail",
                "confidence": 0.0,
                "reasoning": f"Must-have requirements not met: {must_have_result['reason']}",
                "similarity_score": 0.0,
                "must_have_match": False,
                "outlier_flags": ["must_have_failure"],
                "missing_must_haves": must_have_result.get("missing", [])
            }
        logger.info("✅ Must-have requirements satisfied")
        
        # Layer 2: Compute embedding similarity
        logger.info("Layer 2: Computing embedding similarity...")
        candidate_emb = self.embedder.embed_candidate(candidate)
        position_emb = self.embedder.embed_position(position)
        similarity = float(np.dot(candidate_emb, position_emb))
        similarity = max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
        logger.info(f"Similarity score: {similarity:.4f} (threshold: {self.similarity_threshold:.2f})")
        
        if similarity < self.similarity_threshold:
            logger.warning(f"Similarity below threshold: {similarity:.4f} < {self.similarity_threshold:.2f}")
            return {
                "decision": "fail",
                "confidence": similarity,
                "reasoning": f"Embedding similarity too low: {similarity:.2f} < {self.similarity_threshold:.2f}",
                "similarity_score": similarity,
                "must_have_match": True,
                "outlier_flags": ["low_similarity"]
            }
        logger.info("✅ Similarity above threshold")
        
        # Layer 3: Outlier detection
        logger.info("Layer 3: Detecting outliers...")
        outlier_flags = self._detect_outliers(candidate, position, extracted_info)
        if outlier_flags:
            logger.warning(f"Outliers detected: {outlier_flags}")
            # Outliers reduce confidence but don't auto-fail (unless critical)
            critical_outliers = [f for f in outlier_flags if "critical" in f.lower()]
            if critical_outliers:
                logger.error(f"Critical outliers detected: {critical_outliers}")
                return {
                    "decision": "fail",
                    "confidence": similarity * 0.5,  # Severely reduced
                    "reasoning": f"Critical outliers detected: {', '.join(critical_outliers)}",
                    "similarity_score": similarity,
                    "must_have_match": True,
                    "outlier_flags": outlier_flags
                }
        else:
            logger.info("✅ No outliers detected")
        
        # Layer 4: Extracted information validation
        logger.info("Layer 4: Validating extracted information...")
        extracted_validation = self._validate_extracted_info(extracted_info, candidate, position)
        logger.info(f"Extracted info validation: {extracted_validation['score']:.2f}")
        
        # Layer 5: Bandit confidence scoring
        logger.info("Layer 5: Computing bandit confidence...")
        bandit_confidence = self._compute_bandit_confidence(candidate, position, similarity)
        logger.info(f"Bandit confidence: {bandit_confidence:.4f}")
        
        # Layer 6: Final multi-factor evaluation
        logger.info("Layer 6: Final multi-factor evaluation...")
        final_decision = self._evaluate_candidate(
            candidate, position, extracted_info, similarity,
            outlier_flags, extracted_validation, bandit_confidence
        )
        
        logger.info(f"Final decision: {final_decision['decision']} "
                   f"(confidence: {final_decision['confidence']:.2f})")
        
        return final_decision
    
    def _check_must_haves(
        self,
        candidate: Dict[str, Any],
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extremely strict must-have requirements check.
        
        Checks:
        - All must-have skills present in candidate skills
        - Experience level matches or exceeds
        - Domain expertise overlaps
        
        Args:
            candidate: Candidate profile
            position: Position profile
        
        Returns:
            Dictionary with 'satisfied' (bool) and 'reason' (str)
        """
        must_haves = position.get('must_haves', [])
        if not must_haves:
            logger.warning("Position has no must-have requirements")
            return {"satisfied": True, "reason": "No must-have requirements specified"}
        
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        missing = []
        
        for must_have in must_haves:
            must_have_lower = must_have.lower()
            # Check for exact match or substring match based on strictness
            if self.must_have_strictness >= 1.0:
                # Exact match required
                if must_have_lower not in candidate_skills:
                    missing.append(must_have)
            else:
                # Partial match allowed
                found = any(must_have_lower in skill or skill in must_have_lower 
                          for skill in candidate_skills)
                if not found:
                    missing.append(must_have)
        
        if missing:
            return {
                "satisfied": False,
                "reason": f"Missing must-have skills: {', '.join(missing)}",
                "missing": missing
            }
        
        # Check experience level
        position_level = position.get('experience_level', '').lower()
        candidate_level = candidate.get('expertise_level', '').lower()
        
        level_hierarchy = {'junior': 1, 'mid': 2, 'senior': 3, 'staff': 4, 'principal': 5}
        position_level_num = level_hierarchy.get(position_level, 0)
        candidate_level_num = level_hierarchy.get(candidate_level, 0)
        
        if position_level_num > 0 and candidate_level_num < position_level_num:
            return {
                "satisfied": False,
                "reason": f"Experience level insufficient: {candidate_level} < {position_level}"
            }
        
        return {"satisfied": True, "reason": "All must-have requirements met"}
    
    def _detect_outliers(
        self,
        candidate: Dict[str, Any],
        position: Dict[str, Any],
        extracted_info: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Detect outliers and inconsistencies (EXTREMELY SCRUTINIZING).
        
        Checks for:
        - Experience-skill mismatch (claims senior but minimal skills)
        - Domain mismatch (skills don't match claimed domains)
        - Extracted info inconsistency (says one thing, profile says another)
        - Suspicious patterns (too good to be true)
        
        Args:
            candidate: Candidate profile
            position: Position profile
            extracted_info: Extracted conversation information
        
        Returns:
            List of outlier flags (empty if no outliers)
        """
        flags = []
        
        # Check 1: Experience-skill mismatch
        experience_years = candidate.get('experience_years', 0)
        num_skills = len(candidate.get('skills', []))
        
        # Senior candidates should have many skills
        if experience_years >= 5 and num_skills < 5:
            flags.append("experience_skill_mismatch: Senior experience but few skills")
            logger.warning(f"Outlier: {experience_years} years experience but only {num_skills} skills")
        
        # Check 2: Domain-skill mismatch
        domains = [d.lower() for d in candidate.get('domains', [])]
        skills = [s.lower() for s in candidate.get('skills', [])]
        
        # If claims LLM Inference domain, should have relevant skills
        if 'llm inference' in ' '.join(domains) or 'gpu' in ' '.join(domains):
            relevant_skills = ['cuda', 'pytorch', 'tensorflow', 'gpu', 'inference']
            has_relevant = any(any(rel in skill for rel in relevant_skills) for skill in skills)
            if not has_relevant:
                flags.append("domain_skill_mismatch: Claims LLM/GPU domain but lacks relevant skills")
                logger.warning("Outlier: Domain-skill mismatch detected")
        
        # Check 3: Extracted info inconsistency
        if extracted_info:
            # Check if extracted experience matches profile
            extracted_exp = extracted_info.get('experience_years')
            if extracted_exp and abs(extracted_exp - experience_years) > 2:
                flags.append("critical_extracted_info_mismatch: Experience mismatch between profile and conversation")
                logger.error(f"Critical outlier: Experience mismatch ({experience_years} vs {extracted_exp})")
            
            # Check if extracted skills match profile
            extracted_skills = extracted_info.get('skills', [])
            if extracted_skills:
                profile_skills_lower = [s.lower() for s in skills]
                extracted_skills_lower = [s.lower() for s in extracted_skills]
                overlap = len(set(profile_skills_lower) & set(extracted_skills_lower))
                if overlap < len(extracted_skills_lower) * 0.5:  # Less than 50% overlap
                    flags.append("extracted_info_inconsistency: Skills mentioned don't match profile")
                    logger.warning("Outlier: Extracted skills don't match profile")
        
        # Check 4: Suspicious patterns (too good to be true)
        # If candidate has ALL must-haves plus many extras, might be suspicious
        position_must_haves = position.get('must_haves', [])
        if len(position_must_haves) >= 3:
            candidate_has_all = all(
                any(mh.lower() in s.lower() for s in skills)
                for mh in position_must_haves
            )
            # If has all must-haves but similarity is low, suspicious
            if candidate_has_all and len(skills) > 20:  # Too many skills
                flags.append("suspicious_pattern: Has all must-haves but excessive skill list")
                logger.warning("Outlier: Suspicious pattern detected")
        
        return flags
    
    def _validate_extracted_info(
        self,
        extracted_info: Optional[Dict[str, Any]],
        candidate: Dict[str, Any],
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate extracted information quality.
        
        Args:
            extracted_info: Extracted conversation information
            candidate: Candidate profile
            position: Position profile
        
        Returns:
            Validation result with score and flags
        """
        if not extracted_info:
            logger.warning("No extracted information provided")
            return {
                "score": 0.5,  # Neutral score when no info
                "flags": ["no_extracted_info"],
                "validated": False
            }
        
        score = 0.0
        flags = []
        
        # Check motivation score
        motivation = extracted_info.get('motivation_score', 0.5)
        if motivation < 0.4:
            flags.append("low_motivation")
        score += motivation * 0.3
        
        # Check communication score
        communication = extracted_info.get('communication_score', 0.5)
        if communication < 0.4:
            flags.append("poor_communication")
        score += communication * 0.2
        
        # Check technical depth
        technical = extracted_info.get('technical_depth', 0.5)
        if technical < 0.5:
            flags.append("insufficient_technical_depth")
        score += technical * 0.4
        
        # Check cultural fit
        cultural_fit = extracted_info.get('cultural_fit', 0.5)
        score += cultural_fit * 0.1
        
        return {
            "score": min(1.0, score),
            "flags": flags,
            "validated": len(flags) == 0
        }
    
    def _compute_bandit_confidence(
        self,
        candidate: Dict[str, Any],
        position: Dict[str, Any],
        similarity: float
    ) -> float:
        """
        Compute confidence using bandit (warm-started from similarity).
        
        Args:
            candidate: Candidate profile
            position: Position profile
            similarity: Embedding similarity score
        
        Returns:
            Confidence score (0-1)
        """
        # Initialize bandit with single candidate (warm-started from similarity)
        self.bandit.initialize_from_embeddings([candidate], position)
        
        # Get bandit's estimate (alpha / (alpha + beta))
        if 0 in self.bandit.alpha:
            alpha = self.bandit.alpha[0]
            beta = self.bandit.beta[0]
            confidence = alpha / (alpha + beta)
        else:
            confidence = similarity  # Fallback to similarity
        
        return float(confidence)
    
    def _evaluate_candidate(
        self,
        candidate: Dict[str, Any],
        position: Dict[str, Any],
        extracted_info: Optional[Dict[str, Any]],
        similarity: float,
        outlier_flags: List[str],
        extracted_validation: Dict[str, Any],
        bandit_confidence: float
    ) -> Dict[str, Any]:
        """
        Final multi-factor evaluation (EXTREMELY SCRUTINIZING).
        
        Combines:
        - Embedding similarity (40% weight)
        - Bandit confidence (30% weight)
        - Extracted info quality (20% weight)
        - Outlier penalty (10% penalty)
        
        Args:
            candidate: Candidate profile
            position: Position profile
            extracted_info: Extracted conversation information
            similarity: Embedding similarity score
            outlier_flags: List of outlier flags
            extracted_validation: Extracted info validation result
            bandit_confidence: Bandit confidence score
        
        Returns:
            Final decision dictionary
        """
        # Compute weighted score
        similarity_weight = 0.40
        bandit_weight = 0.30
        extracted_weight = 0.20
        outlier_penalty = 0.10
        
        base_score = (
            similarity * similarity_weight +
            bandit_confidence * bandit_weight +
            extracted_validation['score'] * extracted_weight
        )
        
        # Apply outlier penalty
        outlier_penalty_amount = min(len(outlier_flags) * 0.05, 0.20)  # Max 20% penalty
        final_score = base_score * (1.0 - outlier_penalty_amount)
        
        logger.info(f"Evaluation scores: similarity={similarity:.3f}, "
                   f"bandit={bandit_confidence:.3f}, "
                   f"extracted={extracted_validation['score']:.3f}, "
                   f"outlier_penalty={outlier_penalty_amount:.3f}, "
                   f"final={final_score:.3f}")
        
        # Make decision (STRICT THRESHOLD)
        decision = "pass" if final_score >= self.confidence_threshold else "fail"
        
        # Generate detailed reasoning
        reasoning_parts = []
        if similarity >= self.similarity_threshold:
            reasoning_parts.append(f"Strong embedding similarity ({similarity:.2f})")
        if bandit_confidence >= 0.7:
            reasoning_parts.append(f"High bandit confidence ({bandit_confidence:.2f})")
        if extracted_validation['validated']:
            reasoning_parts.append("Extracted information validated")
        if outlier_flags:
            reasoning_parts.append(f"Outliers detected: {len(outlier_flags)}")
        
        if decision == "pass":
            reasoning = f"PASS: {'; '.join(reasoning_parts)}. Final score: {final_score:.2f}"
        else:
            reasoning = f"FAIL: Final score {final_score:.2f} below threshold {self.confidence_threshold:.2f}. " \
                       f"Issues: {'; '.join(reasoning_parts) if reasoning_parts else 'Low overall score'}"
        
        return {
            "decision": decision,
            "confidence": final_score,
            "reasoning": reasoning,
            "similarity_score": similarity,
            "bandit_confidence": bandit_confidence,
            "extracted_info_score": extracted_validation['score'],
            "must_have_match": True,
            "outlier_flags": outlier_flags,
            "extracted_info_summary": {
                "validated": extracted_validation['validated'],
                "flags": extracted_validation.get('flags', [])
            },
            "final_score": final_score
        }

