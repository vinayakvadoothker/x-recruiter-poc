"""
query_engine.py - Advanced querying system for candidate search

This module provides production-grade querying capabilities for finding candidates
with complex boolean queries, ability-based filtering, and multi-criteria searches.
Supports hybrid queries combining metadata filtering with vector similarity search.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Query structure and filtering methodology
    - Our adaptation: Extending to support complex boolean queries and hybrid search

Our Novel Contribution:
Advanced querying mechanism: Supports complex boolean queries (AND, OR, NOT),
ability cluster filtering, multi-criteria searches, and hybrid vector+metadata
queries. This enables sophisticated candidate discovery beyond basic similarity search.

Key functions:
- QueryEngine: Main query engine class
- query_by_ability_cluster(): Filter by ability cluster
- query_by_skills(): Skill-based filtering with boolean logic
- query_exceptional_talent(): Multi-criteria exceptional talent search
- query_candidates(): Complex boolean queries with similarity
- _apply_filters(): Apply filter logic to candidates
- _combine_with_similarity(): Hybrid search combining filters and vectors

Dependencies:
- backend.database.knowledge_graph: Candidate retrieval
- backend.database.vector_db_client: Vector similarity search
- backend.embeddings: Embedding generation for similarity queries
- backend.matching.talent_clusterer: Ability cluster lookups
"""

import logging
import time
from typing import Dict, List, Any, Optional
import numpy as np
from backend.database.knowledge_graph import KnowledgeGraph
from backend.database.vector_db_client import VectorDBClient
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

logger = logging.getLogger(__name__)


class QueryEngine:
    """
    Advanced query engine for complex candidate searches.
    
    Supports:
    - Ability cluster queries ("show me all CUDA Experts")
    - Skill-based queries with AND/OR/NOT logic
    - Multi-criteria queries (arXiv papers, GitHub stars, X engagement)
    - Complex boolean queries with flexible filters
    - Hybrid search (metadata filtering + vector similarity)
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        vector_db: Optional[VectorDBClient] = None,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None
    ):
        """
        Initialize query engine.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            vector_db: Vector DB client (uses KG's vector_db if None)
            embedder: Embedder instance (uses KG's embedder if None)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.vector_db = vector_db or self.kg.vector_db
        self.embedder = embedder or self.kg.embedder
        logger.info("Initialized QueryEngine")
    
    def query_by_ability_cluster(
        self,
        cluster_name: str,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query candidates by ability cluster.
        
        Example: "Show me all CUDA/GPU Experts"
        
        Args:
            cluster_name: Ability cluster name (e.g., "CUDA/GPU Experts")
            top_k: Maximum number of results
        
        Returns:
            List of candidate profiles matching the cluster
        """
        logger.info(f"Querying by ability cluster: {cluster_name}")
        start_time = time.time()
        
        all_candidates = self.kg.get_all_candidates()
        filtered = [
            c for c in all_candidates
            if c.get('ability_cluster') == cluster_name
        ]
        
        # Sort by similarity if we have a reference (optional enhancement)
        results = filtered[:top_k]
        
        elapsed = time.time() - start_time
        logger.info(f"Found {len(results)} candidates in {elapsed:.3f}s")
        return results
    
    def query_by_skills(
        self,
        required_skills: List[str],
        optional_skills: Optional[List[str]] = None,
        excluded_skills: Optional[List[str]] = None,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query candidates by skills with boolean logic.
        
        Example: Find candidates with CUDA AND PyTorch, optionally TensorRT, but NOT React
        
        Args:
            required_skills: Skills that must be present (AND)
            optional_skills: Skills that should be present (OR - at least one)
            excluded_skills: Skills that must not be present (NOT)
            top_k: Maximum number of results
        
        Returns:
            List of candidate profiles matching skill criteria
        """
        logger.info(f"Querying by skills - required: {required_skills}, "
                   f"optional: {optional_skills}, excluded: {excluded_skills}")
        start_time = time.time()
        
        all_candidates = self.kg.get_all_candidates()
        filtered = []
        
        for candidate in all_candidates:
            candidate_skills = candidate.get('skills', [])
            if not candidate_skills:
                continue
            
            # Convert to lowercase for case-insensitive matching
            candidate_skills_lower = [s.lower() for s in candidate_skills]
            required_lower = [s.lower() for s in required_skills]
            excluded_lower = [s.lower() for s in (excluded_skills or [])]
            optional_lower = [s.lower() for s in (optional_skills or [])]
            
            # Check required skills (AND - all must be present)
            has_all_required = all(
                any(req in skill for skill in candidate_skills_lower)
                for req in required_lower
            )
            if not has_all_required:
                continue
            
            # Check excluded skills (NOT - none should be present)
            has_excluded = any(
                any(exc in skill for skill in candidate_skills_lower)
                for exc in excluded_lower
            )
            if has_excluded:
                continue
            
            # Check optional skills (OR - at least one should be present)
            if optional_lower:
                has_optional = any(
                    any(opt in skill for skill in candidate_skills_lower)
                    for opt in optional_lower
                )
                if not has_optional:
                    continue
            
            filtered.append(candidate)
        
        results = filtered[:top_k]
        elapsed = time.time() - start_time
        logger.info(f"Found {len(results)} candidates in {elapsed:.3f}s")
        return results
    
    def query_exceptional_talent(
        self,
        min_arxiv_papers: int = 0,
        min_github_stars: int = 0,
        min_x_followers: int = 0,
        min_experience_years: int = 0,
        required_domains: Optional[List[str]] = None,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query exceptional talent with multi-criteria filters.
        
        Example: "Find candidates with 10+ arXiv papers AND 1000+ GitHub stars"
        
        Args:
            min_arxiv_papers: Minimum number of arXiv papers
            min_github_stars: Minimum total GitHub stars
            min_x_followers: Minimum X/Twitter followers
            min_experience_years: Minimum years of experience
            required_domains: Required domains (AND - all must be present)
            top_k: Maximum number of results
        
        Returns:
            List of candidate profiles matching criteria
        """
        logger.info(f"Querying exceptional talent - arxiv: {min_arxiv_papers}, "
                   f"github: {min_github_stars}, x: {min_x_followers}, "
                   f"exp: {min_experience_years}, domains: {required_domains}")
        start_time = time.time()
        
        all_candidates = self.kg.get_all_candidates()
        filtered = []
        
        for candidate in all_candidates:
            # Check arXiv papers
            papers = candidate.get('papers', [])
            if len(papers) < min_arxiv_papers:
                continue
            
            # Check GitHub stars
            github_stats = candidate.get('github_stats', {})
            total_stars = github_stats.get('total_stars', 0)
            if total_stars < min_github_stars:
                continue
            
            # Check X followers
            x_analytics = candidate.get('x_analytics_summary', {})
            followers = x_analytics.get('followers_count', 0)
            if followers < min_x_followers:
                continue
            
            # Check experience years
            exp_years = candidate.get('experience_years', 0)
            if exp_years < min_experience_years:
                continue
            
            # Check required domains
            if required_domains:
                candidate_domains = candidate.get('domains', [])
                domains_lower = [d.lower() for d in candidate_domains]
                required_lower = [d.lower() for d in required_domains]
                has_all_domains = all(
                    any(req in domain for domain in domains_lower)
                    for req in required_lower
                )
                if not has_all_domains:
                    continue
            
            filtered.append(candidate)
        
        results = filtered[:top_k]
        elapsed = time.time() - start_time
        logger.info(f"Found {len(results)} exceptional candidates in {elapsed:.3f}s")
        return results
    
    def query_candidates(
        self,
        filters: Dict[str, Any],
        similarity_query: Optional[str] = None,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query candidates with complex boolean filters and optional similarity search.
        
        Example:
        {
            "skills": {"required": ["CUDA"], "excluded": ["React"]},
            "domains": {"required": ["LLM Inference"]},
            "arxiv_papers": {"min": 5},
            "github_stars": {"min": 500},
            "similarity_query": "GPU optimization expert"
        }
        
        Args:
            filters: Flexible filter dictionary with various criteria
            similarity_query: Optional text query for semantic similarity search
            top_k: Maximum number of results
        
        Returns:
            List of candidate profiles matching all criteria
        """
        logger.info(f"Complex query - filters: {filters}, similarity: {similarity_query}")
        start_time = time.time()
        
        # Start with all candidates
        all_candidates = self.kg.get_all_candidates()
        
        # Apply metadata filters
        filtered = self._apply_filters(all_candidates, filters)
        
        # If similarity query provided, combine with vector search
        if similarity_query:
            filtered = self._combine_with_similarity(
                filtered, similarity_query, top_k
            )
        else:
            filtered = filtered[:top_k]
        
        elapsed = time.time() - start_time
        logger.info(f"Found {len(filtered)} candidates in {elapsed:.3f}s")
        return filtered
    
    def _apply_filters(
        self,
        candidates: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply filter logic to candidates.
        
        Args:
            candidates: List of candidate profiles
            filters: Filter dictionary with various criteria
        
        Returns:
            Filtered list of candidates
        """
        filtered = candidates
        
        # Skills filter
        if 'skills' in filters:
            skills_filter = filters['skills']
            required = skills_filter.get('required', [])
            optional = skills_filter.get('optional', [])
            excluded = skills_filter.get('excluded', [])
            filtered = self.query_by_skills(
                required_skills=required,
                optional_skills=optional if optional else None,
                excluded_skills=excluded if excluded else None,
                top_k=len(filtered)  # Don't limit here, limit at end
            )
        
        # Domains filter
        if 'domains' in filters:
            domains_filter = filters['domains']
            required_domains = domains_filter.get('required', [])
            excluded_domains = domains_filter.get('excluded', [])
            
            new_filtered = []
            for candidate in filtered:
                candidate_domains = candidate.get('domains', [])
                domains_lower = [d.lower() for d in candidate_domains]
                
                # Check required
                if required_domains:
                    required_lower = [d.lower() for d in required_domains]
                    has_all = all(
                        any(req in domain for domain in domains_lower)
                        for req in required_lower
                    )
                    if not has_all:
                        continue
                
                # Check excluded
                if excluded_domains:
                    excluded_lower = [d.lower() for d in excluded_domains]
                    has_excluded = any(
                        any(exc in domain for domain in domains_lower)
                        for exc in excluded_lower
                    )
                    if has_excluded:
                        continue
                
                new_filtered.append(candidate)
            filtered = new_filtered
        
        # Numeric range filters
        if 'arxiv_papers' in filters:
            min_papers = filters['arxiv_papers'].get('min', 0)
            filtered = [
                c for c in filtered
                if len(c.get('papers', [])) >= min_papers
            ]
        
        if 'github_stars' in filters:
            min_stars = filters['github_stars'].get('min', 0)
            filtered = [
                c for c in filtered
                if c.get('github_stats', {}).get('total_stars', 0) >= min_stars
            ]
        
        if 'experience_years' in filters:
            min_years = filters['experience_years'].get('min', 0)
            max_years = filters['experience_years'].get('max', 999)
            filtered = [
                c for c in filtered
                if min_years <= c.get('experience_years', 0) <= max_years
            ]
        
        # Ability cluster filter
        if 'ability_cluster' in filters:
            cluster_name = filters['ability_cluster']
            filtered = [
                c for c in filtered
                if c.get('ability_cluster') == cluster_name
            ]
        
        return filtered
    
    def _combine_with_similarity(
        self,
        filtered_candidates: List[Dict[str, Any]],
        query_text: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Combine filtered candidates with vector similarity search.
        
        Args:
            filtered_candidates: Pre-filtered candidates
            query_text: Text query for semantic search
            top_k: Maximum number of results
        
        Returns:
            Hybrid results ranked by similarity
        """
        logger.info(f"Combining {len(filtered_candidates)} candidates with similarity search")
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_candidate({
                'skills': [],
                'experience': [query_text],
                'domains': []
            })
            
            # Get candidate IDs for filtered set
            filtered_ids = {c.get('id') for c in filtered_candidates}
            
            # Perform vector search (get more results to filter)
            # Use threading timeout to handle gRPC failures gracefully
            import threading
            
            vector_results = None
            search_exception = None
            
            def do_search():
                nonlocal vector_results, search_exception
                try:
                    vector_results = self.vector_db.search_similar_candidates(
                        query_embedding, top_k=min(top_k * 2, 100)
                    )
                except Exception as e:
                    search_exception = e
            
            # Run search in a thread with 3-second timeout
            search_thread = threading.Thread(target=do_search)
            search_thread.daemon = True
            search_thread.start()
            search_thread.join(timeout=3.0)  # 3 second timeout
            
            if search_thread.is_alive():
                # Search is still running (likely gRPC retries), fall back to filtered
                logger.warning("Vector search timeout (likely gRPC not available). Using filtered results only.")
                return filtered_candidates[:top_k]
            
            if search_exception:
                # Search failed, fall back to filtered
                logger.warning(f"Vector search failed: {type(search_exception).__name__}. Using filtered results only.")
                return filtered_candidates[:top_k]
            
            if not vector_results:
                # Empty results, fall back to filtered
                logger.warning("Vector search returned empty results. Using filtered results only.")
                return filtered_candidates[:top_k]
            
            # Filter to only include candidates in our filtered set
            # Create a map for fast lookup
            candidate_map = {c.get('id'): c for c in filtered_candidates}
            
            # Combine similarity scores with filtered candidates
            hybrid_results = []
            for result in vector_results:
                candidate_id = result.get('profile_id')
                if candidate_id in filtered_ids and candidate_id in candidate_map:
                    candidate = candidate_map[candidate_id].copy()
                    candidate['similarity_score'] = 1.0 - result.get('distance', 1.0)
                    hybrid_results.append(candidate)
            
            # Sort by similarity and return top_k
            hybrid_results.sort(key=lambda x: x.get('similarity_score', 0.0), reverse=True)
            return hybrid_results[:top_k]
        except Exception as e:
            # If anything fails, return filtered results without similarity
            logger.warning(f"Hybrid search failed: {e}. Returning filtered results only.")
            return filtered_candidates[:top_k]

