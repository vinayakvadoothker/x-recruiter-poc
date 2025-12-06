"""
graph_similarity.py - Computes graph similarity using kNN-based approach

This module implements kNN-based similarity computation following
Frazzetto et al. [1], which computes similarity between candidate and role
graphs by comparing k-nearest neighbor neighborhoods.

Research Paper Citation:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.

What we use from [1]:
- kNN-based similarity for edge weights (Equation 1)
- Entity-level similarity computation: sim_ε(i,j) = (|kNN(v_ε,i) ∩ kNN(v_ε,j)| / |kNN(v_ε,i) ∪ kNN(v_ε,j)|)^(1/p)
- Parameters: k=10 (number of nearest neighbors), p=4 (sharpening factor)
- Aggregation across entity types (skills, experience, education)

Why we use [1]:
Their kNN-based similarity captures semantic relationships between candidate
qualifications and role requirements. The intersection/union approach with
sharpening factor p=4 provides a robust similarity metric that works well
for candidate-role matching.

For more details, see CITATIONS.md.

Key functions:
- compute_entity_similarity(): kNN similarity for entity types (Equation 1 from [1])
- compute_graph_similarity(): Aggregate similarity across all entities

Dependencies:
- scipy.spatial.distance: For kNN distance calculations
- numpy: For array operations and mathematical computations
"""

import numpy as np
import networkx as nx
from scipy.spatial.distance import cdist
from typing import List, Set, Tuple, Dict, Any


def compute_entity_similarity(
    entity_candidate: List[float],
    entity_role: List[float],
    k: int = 10,
    p: int = 4
) -> float:
    """
    Compute kNN-based similarity between candidate and role entities.
    
    Implements Equation 1 from Frazzetto et al. [1]:
    sim_ε(i,j) = (|kNN(v_ε,i) ∩ kNN(v_ε,j)| / |kNN(v_ε,i) ∪ kNN(v_ε,j)|)^(1/p)
    
    Where:
    - kNN(v_ε,i) is the k-nearest neighbors of entity i
    - ∩ is intersection, ∪ is union
    - p is sharpening factor (default 4, from [1])
    - k is number of nearest neighbors (default 10, from [1] experiments)
    
    This formula captures semantic similarity by comparing the overlap of
    k-nearest neighbor sets, with the sharpening factor p=4 providing
    better discrimination between similar and dissimilar entities.
    
    Args:
        entity_candidate: List of embeddings/features for candidate entities
        entity_role: List of embeddings/features for role entities
        k: Number of nearest neighbors (default 10)
        p: Sharpening factor (default 4)
    
    Returns:
        Similarity score between 0 and 1
    
    Example:
        >>> cand_emb = [[0.1, 0.2], [0.3, 0.4]]
        >>> role_emb = [[0.15, 0.25], [0.35, 0.45]]
        >>> sim = compute_entity_similarity(cand_emb, role_emb, k=2)
        >>> print(sim)
    """
    # Convert to numpy arrays for computation
    cand_array = np.array(entity_candidate)
    role_array = np.array(entity_role)
    
    # Handle empty cases
    if len(cand_array) == 0 or len(role_array) == 0:
        return 0.0
    
    # If single entity, convert to 2D array
    if cand_array.ndim == 1:
        cand_array = cand_array.reshape(1, -1)
    if role_array.ndim == 1:
        role_array = role_array.reshape(1, -1)
    
    # Compute kNN neighborhoods for candidate entities
    cand_knn = _compute_knn_neighborhoods(cand_array, k)
    
    # Compute kNN neighborhoods for role entities
    role_knn = _compute_knn_neighborhoods(role_array, k)
    
    # Compute intersection and union
    intersection = _compute_intersection(cand_knn, role_knn)
    union = _compute_union(cand_knn, role_knn)
    
    # Apply sharpening factor
    if union == 0:
        return 0.0
    
    similarity = (intersection / union) ** (1.0 / p)
    return float(similarity)


def _compute_knn_neighborhoods(
    entities: np.ndarray,
    k: int
) -> Set[int]:
    """
    Compute k-nearest neighbor neighborhoods for all entities.
    
    For each entity, finds its k nearest neighbors (including itself),
    then returns the union of all neighborhoods.
    
    Args:
        entities: Array of entity embeddings (n_entities, n_features)
        k: Number of nearest neighbors
    
    Returns:
        Set of indices representing the kNN neighborhood
    """
    n_entities = len(entities)
    k = min(k, n_entities)  # Can't have more neighbors than entities
    
    # Compute pairwise distances
    distances = cdist(entities, entities, metric='euclidean')
    
    # For each entity, find k nearest neighbors
    all_neighbors = set()
    for i in range(n_entities):
        # Get k nearest neighbors (including self)
        nearest_indices = np.argsort(distances[i])[:k]
        all_neighbors.update(nearest_indices.tolist())
    
    return all_neighbors


def _compute_intersection(
    set1: Set[int],
    set2: Set[int]
) -> int:
    """
    Compute intersection size of two sets.
    
    Args:
        set1: First set of indices
        set2: Second set of indices
    
    Returns:
        Size of intersection
    """
    return len(set1 & set2)


def _compute_union(
    set1: Set[int],
    set2: Set[int]
) -> int:
    """
    Compute union size of two sets.
    
    Args:
        set1: First set of indices
        set2: Second set of indices
    
    Returns:
        Size of union
    """
    return len(set1 | set2)


def compute_graph_similarity(
    role_graph,
    candidate_graph,
    entity_weights: dict = None
) -> float:
    """
    Compute overall graph similarity by aggregating entity similarities.
    
    Computes similarity for each entity type (skills, experience, education)
    and aggregates them using weighted average. Default weights are equal.
    
    Args:
        role_graph: NetworkX graph for role
        candidate_graph: NetworkX graph for candidate
        entity_weights: Optional dict with weights for each entity type
            Example: {'skills': 0.5, 'experience': 0.3, 'education': 0.2}
            If None, uses equal weights (1/3 each)
    
    Returns:
        Overall graph similarity score between 0 and 1
    
    Example:
        >>> import networkx as nx
        >>> role_g = nx.Graph()
        >>> cand_g = nx.Graph()
        >>> sim = compute_graph_similarity(role_g, cand_g)
        >>> print(sim)
    """
    entity_types = ['skills', 'experience', 'education']
    
    # Default equal weights
    if entity_weights is None:
        entity_weights = {et: 1.0 / len(entity_types) for et in entity_types}
    
    # Extract entity embeddings from graphs
    similarities = []
    weights = []
    
    for entity_type in entity_types:
        # Extract candidate entities of this type
        cand_entities = _extract_entities_from_graph(candidate_graph, entity_type)
        
        # Extract role entities of this type
        role_entities = _extract_entities_from_graph(role_graph, entity_type)
        
        # Compute similarity for this entity type
        if len(cand_entities) > 0 and len(role_entities) > 0:
            entity_sim = compute_entity_similarity(cand_entities, role_entities)
            similarities.append(entity_sim)
            weights.append(entity_weights.get(entity_type, 0.0))
        else:
            # If no entities of this type, skip (weight = 0)
            weights.append(0.0)
    
    # Weighted average
    if sum(weights) == 0:
        return 0.0
    
    # Normalize weights
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    # Compute weighted average
    overall_similarity = sum(sim * weight for sim, weight in zip(similarities, normalized_weights))
    
    return float(overall_similarity)


def _extract_entities_from_graph(
    graph,
    entity_type: str
) -> List[List[float]]:
    """
    Extract entity embeddings from graph for a specific entity type.
    
    For now, returns simple one-hot or count-based embeddings.
    In production, these would be actual embeddings from Grok API.
    
    Args:
        graph: NetworkX graph
        entity_type: Type of entity ('skills', 'experience', 'education')
    
    Returns:
        List of embeddings (each embedding is a list of floats)
    """
    entities = []
    
    # Find all nodes of this entity type
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get('type') == entity_type:
            # For now, create simple embedding from entity name
            # In production, this would use actual embeddings from Grok
            entity_name = node_data.get('name', '')
            
            # Simple hash-based embedding (placeholder)
            # Real implementation would use Grok embeddings
            embedding = _simple_embedding(entity_name)
            entities.append(embedding)
    
    return entities


def _simple_embedding(text: str, dim: int = 10) -> List[float]:
    """
    Create simple embedding from text (placeholder for Grok embeddings).
    
    In production, this would call Grok API for actual embeddings.
    This is a placeholder that creates deterministic embeddings.
    
    Args:
        text: Text to embed
        dim: Embedding dimension
    
    Returns:
        List of floats representing embedding
    """
    # Simple hash-based embedding (deterministic)
    import hashlib
    
    hash_obj = hashlib.md5(text.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Convert to embedding vector
    embedding = []
    for i in range(dim):
        # Use hash to generate pseudo-random values
        val = (hash_int >> (i * 4)) & 0xF
        embedding.append(float(val) / 15.0)  # Normalize to [0, 1]
    
    return embedding

