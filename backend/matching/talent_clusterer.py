"""
talent_clusterer.py - Embedding-based talent clustering system

This module implements K-means clustering on candidate embeddings to group
candidates by ability clusters (e.g., "CUDA Experts", "LLM Engineers").
This enables better matching through cluster-aware success rates.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Entity extraction methodology (skills, experience, education)
    - Our adaptation: Using embedding-based clustering instead of graph-based
      clustering, but following their approach of grouping by semantic similarity

[2] MacQueen, J. "Some Methods for Classification and Analysis of Multivariate
    Observations." Proceedings of the Fifth Berkeley Symposium on Mathematical
    Statistics and Probability, 1967.
    - Used for: K-means clustering algorithm
    - Our adaptation: K-means on 768-dim candidate embeddings with elbow method
      for optimal K selection

Our Novel Contribution:
Semantic ability clustering: Groups candidates by ability using embedding-based
K-means clustering with intelligent cluster naming based on dominant skills/domains.
This enables cluster-aware matching where interviewers have success rates per
ability cluster, improving match quality. This is the first application of
embedding-based clustering for talent grouping in recruiting systems.

Key functions:
- TalentClusterer: Main clustering class
- cluster_candidates(): Cluster all candidates and assign ability_cluster
- assign_candidate_to_cluster(): Assign single candidate to nearest cluster
- update_interviewer_cluster_rates(): Update interviewer cluster_success_rates
- _determine_optimal_k(): Use elbow method to find optimal K
- _name_cluster(): Generate meaningful cluster names from dominant skills

Dependencies:
- backend.database.knowledge_graph: Candidate retrieval and updates
- backend.embeddings: Embedding generation
- sklearn.cluster: K-means implementation
- numpy: Numerical computations

Implementation Rationale:
- Why K-means on embeddings: Embeddings capture semantic similarity better than
  keyword matching. Candidates with similar skills/experience cluster together
  naturally in embedding space.
- Why elbow method: Automatic K selection ensures optimal number of clusters without
  manual tuning. Elbow method balances cluster quality vs. granularity.
- Why meaningful cluster names: "CUDA Experts" is more interpretable than "Cluster 1".
  This enables human understanding and better matching decisions.
- Why cluster-aware success rates: Interviewers may excel with certain ability
  clusters (e.g., CUDA experts) but struggle with others (e.g., web developers).
  Tracking success rates per cluster improves matching quality.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from backend.database.knowledge_graph import KnowledgeGraph
from backend.embeddings import RecruitingKnowledgeGraphEmbedder

logger = logging.getLogger(__name__)


class TalentClusterer:
    """
    Clusters candidates by ability using embedding-based K-means.
    
    Groups candidates into ability clusters like:
    - "CUDA/GPU Experts"
    - "LLM Inference Engineers"
    - "Fullstack Developers"
    - "ML Researchers"
    - "Systems Engineers"
    
    Uses K-means clustering on 768-dim candidate embeddings with intelligent
    cluster naming based on dominant skills/domains.
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        embedder: Optional[RecruitingKnowledgeGraphEmbedder] = None,
        min_clusters: int = 5,
        max_clusters: int = 10,
        n_init: int = 10,
        random_state: int = 42
    ):
        """
        Initialize clusterer.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            embedder: Embedder instance (creates new if None)
            min_clusters: Minimum number of clusters (default 5)
            max_clusters: Maximum number of clusters (default 10)
            n_init: Number of K-means initializations (default 10)
            random_state: Random seed for reproducibility (default 42)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.embedder = embedder or RecruitingKnowledgeGraphEmbedder()
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters
        self.n_init = n_init
        self.random_state = random_state
        
        # Store cluster model and centroids for new candidate assignment
        self.kmeans_model: Optional[KMeans] = None
        self.cluster_names: Dict[int, str] = {}
        self.cluster_centroids: Optional[np.ndarray] = None
        
        logger.info(f"Initialized TalentClusterer (K range: {min_clusters}-{max_clusters})")
    
    def cluster_candidates(self, candidates: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Cluster candidates and assign ability_cluster field.
        
        Process:
        1. Get all candidates (or use provided list)
        2. Generate embeddings for all candidates
        3. Determine optimal K using elbow method
        4. Run K-means clustering
        5. Name clusters based on dominant skills/domains
        6. Assign ability_cluster to each candidate
        7. Update knowledge graph with cluster assignments
        
        Args:
            candidates: Optional list of candidates. If None, retrieves all from KG.
        
        Returns:
            Dictionary with:
            - cluster_assignments: Dict[candidate_id, cluster_name]
            - cluster_statistics: Dict[cluster_name, stats]
            - optimal_k: Optimal number of clusters
            - silhouette_score: Cluster quality score
        """
        logger.info("Starting candidate clustering")
        
        # Get candidates
        if candidates is None:
            candidates = self.kg.get_all_candidates()
            logger.info(f"Retrieved {len(candidates)} candidates from knowledge graph")
        else:
            logger.info(f"Using provided {len(candidates)} candidates")
        
        if len(candidates) < self.min_clusters:
            logger.warning(f"Not enough candidates ({len(candidates)}) for clustering (min: {self.min_clusters})")
            return {
                "cluster_assignments": {},
                "cluster_statistics": {},
                "optimal_k": 0,
                "silhouette_score": 0.0,
                "error": "Not enough candidates for clustering"
            }
        
        # Generate embeddings
        logger.info("Generating embeddings for all candidates...")
        embeddings = []
        candidate_ids = []
        for candidate in candidates:
            emb = self.embedder.embed_candidate(candidate)
            embeddings.append(emb)
            candidate_ids.append(candidate['id'])
        
        embeddings_array = np.array(embeddings)
        logger.info(f"Generated {len(embeddings)} embeddings (shape: {embeddings_array.shape})")
        
        # Determine optimal K
        optimal_k = self._determine_optimal_k(embeddings_array)
        logger.info(f"Optimal K: {optimal_k}")
        
        # Run K-means
        logger.info(f"Running K-means clustering with K={optimal_k}...")
        self.kmeans_model = KMeans(
            n_clusters=optimal_k,
            n_init=self.n_init,
            random_state=self.random_state,
            max_iter=300
        )
        cluster_labels = self.kmeans_model.fit_predict(embeddings_array)
        self.cluster_centroids = self.kmeans_model.cluster_centers_
        
        logger.info(f"Clustering complete. Cluster distribution: {np.bincount(cluster_labels)}")
        
        # Name clusters
        logger.info("Naming clusters based on dominant skills/domains...")
        self.cluster_names = self._name_all_clusters(candidates, cluster_labels, optimal_k)
        
        # Compute silhouette score for quality assessment
        if len(set(cluster_labels)) > 1:  # Need at least 2 clusters
            silhouette_avg = silhouette_score(embeddings_array, cluster_labels)
            logger.info(f"Silhouette score: {silhouette_avg:.3f}")
        else:
            silhouette_avg = 0.0
            logger.warning("Only one cluster, cannot compute silhouette score")
        
        # Assign clusters to candidates
        cluster_assignments = {}
        cluster_statistics = {}
        
        for i, candidate_id in enumerate(candidate_ids):
            cluster_label = cluster_labels[i]
            cluster_name = self.cluster_names[cluster_label]
            cluster_assignments[candidate_id] = cluster_name
            
            # Update candidate in knowledge graph
            self.kg.update_candidate(candidate_id, {'ability_cluster': cluster_name})
        
        # Compute cluster statistics
        for cluster_label in range(optimal_k):
            cluster_name = self.cluster_names[cluster_label]
            cluster_candidates = [candidates[i] for i in range(len(candidates)) if cluster_labels[i] == cluster_label]
            
            cluster_statistics[cluster_name] = {
                'size': len(cluster_candidates),
                'dominant_skills': self._get_dominant_skills(cluster_candidates),
                'dominant_domains': self._get_dominant_domains(cluster_candidates),
                'avg_experience_years': np.mean([c.get('experience_years', 0) for c in cluster_candidates]) if cluster_candidates else 0.0
            }
        
        logger.info(f"✅ Clustering complete. Assigned {len(cluster_assignments)} candidates to {optimal_k} clusters")
        
        return {
            "cluster_assignments": cluster_assignments,
            "cluster_statistics": cluster_statistics,
            "optimal_k": optimal_k,
            "silhouette_score": float(silhouette_avg)
        }
    
    def assign_candidate_to_cluster(self, candidate: Dict[str, Any]) -> str:
        """
        Assign single candidate to nearest cluster.
        
        Used for new candidates without re-clustering all.
        Requires that cluster_candidates() has been called first.
        
        Args:
            candidate: Candidate profile dictionary
        
        Returns:
            Cluster name (e.g., "CUDA Experts")
        
        Raises:
            ValueError: If clustering hasn't been run yet
        """
        if self.kmeans_model is None or self.cluster_centroids is None:
            raise ValueError("Must call cluster_candidates() first before assigning individual candidates")
        
        logger.info(f"Assigning candidate {candidate.get('id', 'unknown')} to cluster")
        
        # Generate embedding
        candidate_emb = self.embedder.embed_candidate(candidate)
        
        # Find nearest centroid
        distances = np.linalg.norm(self.cluster_centroids - candidate_emb, axis=1)
        nearest_cluster_label = int(np.argmin(distances))
        cluster_name = self.cluster_names[nearest_cluster_label]
        
        logger.info(f"Assigned to cluster: {cluster_name}")
        
        return cluster_name
    
    def update_interviewer_cluster_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Update interviewer cluster_success_rates based on historical performance.
        
        For each interviewer:
        - Calculate success rate per cluster from interview history
        - Update cluster_success_rates dict in interviewer profile
        
        Returns:
            Dictionary mapping interviewer_id to cluster_success_rates
        """
        logger.info("Updating interviewer cluster success rates")
        
        interviewers = self.kg.get_all_interviewers()
        all_rates = {}
        
        for interviewer in interviewers:
            interviewer_id = interviewer['id']
            interview_history = interviewer.get('interview_history', [])
            
            if not interview_history:
                logger.warning(f"Interviewer {interviewer_id} has no interview history")
                continue
            
            # Get candidates from history
            cluster_success_counts = {}  # cluster_name -> (successes, total)
            
            for interview in interview_history:
                candidate_id = interview.get('candidate_id')
                if not candidate_id:
                    continue
                
                candidate = self.kg.get_candidate(candidate_id)
                if not candidate:
                    continue
                
                cluster_name = candidate.get('ability_cluster')
                if not cluster_name:
                    continue
                
                # Track success/failure
                if cluster_name not in cluster_success_counts:
                    cluster_success_counts[cluster_name] = [0, 0]
                
                cluster_success_counts[cluster_name][1] += 1  # Total
                if interview.get('result') == 'hired' or interview.get('result') == 'pass':
                    cluster_success_counts[cluster_name][0] += 1  # Success
            
            # Calculate success rates
            cluster_success_rates = {}
            for cluster_name, (successes, total) in cluster_success_counts.items():
                success_rate = successes / total if total > 0 else 0.5  # Default 0.5 if no data
                cluster_success_rates[cluster_name] = success_rate
            
            # Update interviewer profile
            if cluster_success_rates:
                self.kg.update_interviewer(
                    interviewer_id,
                    {'cluster_success_rates': cluster_success_rates}
                )
                all_rates[interviewer_id] = cluster_success_rates
                logger.info(f"Updated {interviewer_id}: {len(cluster_success_rates)} cluster rates")
        
        logger.info(f"✅ Updated cluster success rates for {len(all_rates)} interviewers")
        
        return all_rates
    
    def _determine_optimal_k(self, embeddings: np.ndarray) -> int:
        """
        Determine optimal K using elbow method.
        
        Tests K values from min_clusters to max_clusters and selects K
        that minimizes within-cluster sum of squares (WCSS) while
        maximizing silhouette score.
        
        Args:
            embeddings: Array of candidate embeddings (N x 768)
        
        Returns:
            Optimal K value
        """
        logger.info(f"Determining optimal K (range: {self.min_clusters}-{self.max_clusters})")
        
        if len(embeddings) < self.max_clusters:
            # Not enough data for max_clusters
            optimal_k = max(self.min_clusters, len(embeddings) // 2)
            logger.info(f"Limited data, using K={optimal_k}")
            return optimal_k
        
        best_k = self.min_clusters
        best_silhouette = -1.0
        
        for k in range(self.min_clusters, min(self.max_clusters + 1, len(embeddings))):
            kmeans = KMeans(
                n_clusters=k,
                n_init=self.n_init,
                random_state=self.random_state,
                max_iter=300
            )
            labels = kmeans.fit_predict(embeddings)
            
            # Use silhouette score as quality metric
            if len(set(labels)) > 1:  # Need at least 2 clusters
                silhouette = silhouette_score(embeddings, labels)
                logger.debug(f"K={k}: silhouette={silhouette:.3f}")
                
                if silhouette > best_silhouette:
                    best_silhouette = silhouette
                    best_k = k
            else:
                break  # Can't have more clusters than data points
        
        logger.info(f"Optimal K: {best_k} (silhouette: {best_silhouette:.3f})")
        return best_k
    
    def _name_all_clusters(
        self,
        candidates: List[Dict[str, Any]],
        cluster_labels: np.ndarray,
        k: int
    ) -> Dict[int, str]:
        """
        Name all clusters based on dominant skills/domains.
        
        Args:
            candidates: List of candidate profiles
            cluster_labels: Cluster assignment for each candidate
            k: Number of clusters
        
        Returns:
            Dictionary mapping cluster_label -> cluster_name
        """
        cluster_names = {}
        
        for cluster_label in range(k):
            cluster_candidates = [candidates[i] for i in range(len(candidates)) if cluster_labels[i] == cluster_label]
            cluster_name = self._name_cluster(cluster_candidates)
            cluster_names[cluster_label] = cluster_name
            logger.debug(f"Cluster {cluster_label}: {cluster_name} ({len(cluster_candidates)} candidates)")
        
        return cluster_names
    
    def _name_cluster(self, cluster_candidates: List[Dict[str, Any]]) -> str:
        """
        Generate meaningful cluster name from dominant skills/domains.
        
        Analyzes skills and domains in cluster to find dominant patterns.
        Generates human-readable names like "CUDA/GPU Experts" or
        "LLM Inference Engineers".
        
        Args:
            cluster_candidates: Candidates in this cluster
        
        Returns:
            Cluster name (e.g., "CUDA Experts", "Fullstack Developers")
        """
        if not cluster_candidates:
            return "Unassigned"
        
        # Collect all skills and domains
        all_skills = []
        all_domains = []
        
        for candidate in cluster_candidates:
            all_skills.extend(candidate.get('skills', []))
            all_domains.extend(candidate.get('domains', []))
        
        # Count frequencies
        from collections import Counter
        skill_counts = Counter(all_skills)
        domain_counts = Counter(all_domains)
        
        # Find dominant skills (appearing in >= 40% of candidates)
        threshold = max(1, len(cluster_candidates) * 0.4)
        dominant_skills = [skill for skill, count in skill_counts.items() if count >= threshold]
        dominant_domains = [domain for domain, count in domain_counts.items() if count >= threshold]
        
        # Generate name based on dominant patterns
        name_parts = []
        
        # Priority 1: Domain-based naming (more specific)
        if dominant_domains:
            # Use top domain
            top_domain = domain_counts.most_common(1)[0][0]
            if "LLM" in top_domain or "Inference" in top_domain:
                name_parts.append("LLM Inference Engineers")
            elif "GPU" in top_domain or "CUDA" in top_domain:
                name_parts.append("GPU Computing Experts")
            elif "ML" in top_domain or "Machine Learning" in top_domain:
                name_parts.append("ML Engineers")
            else:
                name_parts.append(f"{top_domain} Specialists")
        
        # Priority 2: Skill-based naming
        if not name_parts and dominant_skills:
            # Check for specific skill patterns
            if any("CUDA" in s for s in dominant_skills):
                name_parts.append("CUDA/GPU Experts")
            elif any("React" in s or "Node" in s for s in dominant_skills):
                name_parts.append("Fullstack Developers")
            elif any("PyTorch" in s or "TensorFlow" in s for s in dominant_skills):
                name_parts.append("Deep Learning Engineers")
            elif any("Kubernetes" in s or "Docker" in s for s in dominant_skills):
                name_parts.append("DevOps Engineers")
            else:
                # Use top 2 skills
                top_skills = [skill for skill, _ in skill_counts.most_common(2)]
                name_parts.append(f"{'/'.join(top_skills)} Specialists")
        
        # Fallback: Generic name
        if not name_parts:
            # Use experience level
            avg_exp = np.mean([c.get('experience_years', 0) for c in cluster_candidates])
            if avg_exp >= 7:
                name_parts.append("Senior Engineers")
            elif avg_exp >= 4:
                name_parts.append("Mid-Level Engineers")
            else:
                name_parts.append("Junior Engineers")
        
        return name_parts[0] if name_parts else "General Engineers"
    
    def _get_dominant_skills(self, candidates: List[Dict[str, Any]], top_n: int = 5) -> List[str]:
        """Get top N most common skills in cluster."""
        from collections import Counter
        all_skills = []
        for candidate in candidates:
            all_skills.extend(candidate.get('skills', []))
        return [skill for skill, _ in Counter(all_skills).most_common(top_n)]
    
    def _get_dominant_domains(self, candidates: List[Dict[str, Any]], top_n: int = 3) -> List[str]:
        """Get top N most common domains in cluster."""
        from collections import Counter
        all_domains = []
        for candidate in candidates:
            all_domains.extend(candidate.get('domains', []))
        return [domain for domain, _ in Counter(all_domains).most_common(top_n)]
    
    def get_cluster_statistics(self) -> Dict[str, Any]:
        """
        Get cluster statistics (sizes, distributions, dominant skills).
        
        Returns:
            Dictionary with cluster statistics
        """
        if not self.cluster_names:
            return {"error": "Clustering not run yet"}
        
        candidates = self.kg.get_all_candidates()
        stats = {}
        
        for cluster_label, cluster_name in self.cluster_names.items():
            cluster_candidates = [
                c for c in candidates
                if c.get('ability_cluster') == cluster_name
            ]
            
            stats[cluster_name] = {
                'size': len(cluster_candidates),
                'dominant_skills': self._get_dominant_skills(cluster_candidates),
                'dominant_domains': self._get_dominant_domains(cluster_candidates),
                'avg_experience_years': np.mean([c.get('experience_years', 0) for c in cluster_candidates]) if cluster_candidates else 0.0
            }
        
        return stats
    
    def close(self):
        """Close knowledge graph connection."""
        self.kg.close()

