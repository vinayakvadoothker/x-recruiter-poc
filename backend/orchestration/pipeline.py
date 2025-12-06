"""
End-to-end recruitment pipeline.

Orchestrates candidate sourcing, graph building, similarity computation, and bandit selection.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional

from backend.orchestration.candidate_sourcer import CandidateSourcer
from backend.integrations.grok_api import GrokAPIClient

logger = logging.getLogger(__name__)

# ============================================================================
# VIN'S CODE INTEGRATION POINT
# ============================================================================
# TODO: When Vin's code is ready, replace this try/except with direct imports:
#   from backend.graph.graph_builder import build_candidate_role_graph
#   from backend.graph.graph_similarity import compute_graph_similarity
#   from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
# ============================================================================
try:
    from backend.graph.graph_builder import build_candidate_role_graph
    from backend.graph.graph_similarity import compute_graph_similarity
    from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
    USING_MOCKS = False
    logger.info("Using Vin's actual graph and bandit implementations")
except ImportError:
    from backend.orchestration.mocks import (
        mock_build_candidate_role_graph as build_candidate_role_graph,
        mock_compute_graph_similarity as compute_graph_similarity,
        MockGraphWarmStartedFGTS as GraphWarmStartedFGTS
    )
    USING_MOCKS = True
    logger.warning("Using MOCK implementations - Vin's code not yet available")


class RecruitingPipeline:
    """
    End-to-end recruitment pipeline.
    
    Processes role requests: sources candidates, builds graphs, computes similarities,
    and uses bandit algorithm to select candidates.
    """
    
    def __init__(
        self,
        candidate_sourcer: Optional[CandidateSourcer] = None,
        grok_client: Optional[GrokAPIClient] = None
    ):
        """
        Initialize recruitment pipeline.
        
        Args:
            candidate_sourcer: Candidate sourcer instance
            grok_client: Grok API client instance
        """
        self.sourcer = candidate_sourcer or CandidateSourcer()
        self.grok = grok_client or GrokAPIClient()
        self.role_cache: Dict[str, Dict] = {}
        self.candidate_cache: Dict[str, List[Dict]] = {}
        logger.info(f"RecruitingPipeline initialized (using_mocks={USING_MOCKS})")
    
    async def process_role_request(
        self,
        role_description: str,
        role_title: Optional[str] = None,
        max_candidates: int = 50
    ) -> Dict[str, Any]:
        """
        Process a role request end-to-end.
        
        Steps:
        1. Source candidates from GitHub/X
        2. Extract entities using Grok (for role and candidates)
        3. Build graphs (call Vin's function or mock)
        4. Compute similarities (call Vin's function or mock)
        5. Initialize FG-TS (call Vin's class or mock)
        6. Select candidates (FG-TS)
        7. Return candidate list with scores
        
        Args:
            role_description: Text description of the role
            role_title: Optional job title
            max_candidates: Maximum number of candidates to return
        
        Returns:
            Dictionary with:
            - role_id: Unique role identifier
            - role_graph: Role graph structure
            - candidates: List of candidate dictionaries with scores
            - selected_candidates: Top candidates selected by bandit
        """
        try:
            # Generate role ID
            role_id = str(uuid.uuid4())
            
            logger.info(f"Processing role request: {role_id}")
            
            # Step 1: Extract entities from role description
            logger.info("Extracting entities from role description...")
            role_entities = await self.grok.extract_entities_with_grok(
                role_description,
                entity_types=['skills', 'experience', 'education']
            )
            
            role_data = {
                'id': role_id,
                'title': role_title or 'Unknown Role',
                'description': role_description,
                'skills': role_entities.get('skills', []),
                'experience': role_entities.get('experience', []),
                'education': role_entities.get('education', [])
            }
            
            # Step 2: Source candidates
            logger.info("Sourcing candidates from GitHub/X...")
            candidates = await self.sourcer.source_candidates(
                role_description,
                max_candidates=max_candidates
            )
            
            if not candidates:
                logger.warning("No candidates found")
                return {
                    'role_id': role_id,
                    'role_graph': {},
                    'candidates': [],
                    'selected_candidates': []
                }
            
            logger.info(f"Found {len(candidates)} candidates")
            
            # Step 3: Build graphs for role and candidates
            logger.info("Building graphs...")
            role_graph = build_candidate_role_graph({}, role_data)
            
            candidate_graphs = []
            for candidate in candidates:
                candidate_graph = build_candidate_role_graph(candidate, role_data)
                candidate_graphs.append(candidate_graph)
            
            # Step 4: Compute graph similarities
            logger.info("Computing graph similarities...")
            for i, candidate_graph in enumerate(candidate_graphs):
                similarity = compute_graph_similarity(role_graph, candidate_graph)
                candidates[i]['similarity_score'] = similarity
                candidates[i]['graph'] = candidate_graph
            
            # Step 5: Initialize FG-TS bandit
            logger.info("Initializing bandit algorithm...")
            bandit = GraphWarmStartedFGTS()
            bandit.initialize_from_graph(candidates, role_graph)
            
            # Step 6: Select top candidates using bandit
            logger.info("Selecting candidates using bandit...")
            selected_indices = []
            num_to_select = min(10, len(candidates))
            
            for _ in range(num_to_select):
                try:
                    selected_idx = bandit.select_candidate()
                    if selected_idx not in selected_indices:
                        selected_indices.append(selected_idx)
                        candidates[selected_idx]['bandit_score'] = (
                            bandit.alpha.get(selected_idx, 1.0) /
                            (bandit.alpha.get(selected_idx, 1.0) + bandit.beta.get(selected_idx, 1.0))
                        )
                except Exception as e:
                    logger.warning(f"Error selecting candidate: {e}")
                    break
            
            selected_candidates = [candidates[i] for i in selected_indices]
            
            # Cache results
            self.role_cache[role_id] = role_data
            self.candidate_cache[role_id] = candidates
            
            logger.info(f"Pipeline complete: {len(selected_candidates)} candidates selected")
            
            return {
                'role_id': role_id,
                'role_graph': role_graph,
                'candidates': candidates,
                'selected_candidates': selected_candidates,
                'using_mocks': USING_MOCKS
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline: {e}", exc_info=True)
            raise
    
    def get_candidates_for_role(self, role_id: str) -> List[Dict]:
        """
        Get cached candidates for a role.
        
        Args:
            role_id: Role identifier
        
        Returns:
            List of candidate dictionaries
        """
        return self.candidate_cache.get(role_id, [])
    
    def get_role_data(self, role_id: str) -> Optional[Dict]:
        """
        Get cached role data.
        
        Args:
            role_id: Role identifier
        
        Returns:
            Role data dictionary or None
        """
        return self.role_cache.get(role_id)

