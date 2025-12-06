"""
graph_builder.py - Builds bipartite graphs for candidate-role matching

This module constructs graph structures following Frazzetto et al. [1],
creating bipartite graphs with candidate/role nodes connected via
entity nodes (skills, experience, education).

Research Paper Citation:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.

What we use from [1]:
- Bipartite graph structure (candidate ↔ role with entity nodes)
- Entity extraction methodology (skills, experience, education)
- Graph construction approach for candidate-role matching

Why we use [1]:
Their graph structure effectively captures candidate-role relationships through
semantic entity matching. The bipartite structure allows us to represent
qualifications and requirements in a way that enables similarity computation.

For more details, see CITATIONS.md.

Key functions:
- build_candidate_role_graph(): Main graph construction function
- _create_entity_nodes(): Creates skill/exp/edu nodes

Dependencies:
- networkx: Graph data structure and manipulation
- typing: Type hints for function signatures
"""

import networkx as nx
from typing import Dict, List, Any, Set


def build_candidate_role_graph(
    candidate_data: Dict[str, Any],
    role_data: Dict[str, Any]
) -> nx.Graph:
    """
    Build bipartite graph for candidate-role matching.
    
    Implements the graph construction methodology from Frazzetto et al. [1],
    creating a bipartite structure where candidate and role nodes are
    connected through shared entity nodes (skills, experience, education).
    Edge weights represent similarity scores (initialized to 1.0).
    
    This graph structure is used for computing kNN-based similarity
    (see graph_similarity.py) following Equation 1 from [1].
    
    Graph structure:
        Candidate Node
            |
    ┌───────┼───────┐
    |       |       |
 Skill   Exp    Education
 Node    Node   Node
    |       |       |
    └───────┼───────┘
            |
    ┌───────┼───────┐
    |       |       |
 Skill   Exp    Education
 Node    Node   Node
    |       |       |
    └───────┼───────┘
            |
        Role Node
    
    Args:
        candidate_data: Dictionary with candidate information
            Expected keys: 'id', 'skills', 'experience', 'education'
        role_data: Dictionary with role requirements
            Expected keys: 'id', 'skills', 'experience', 'education'
    
    Returns:
        NetworkX Graph object with candidate, role, and entity nodes
        connected via edges. Nodes have 'type' attribute.
    
    Example:
        >>> candidate = {
        ...     'id': 'cand1',
        ...     'skills': ['Python', 'CUDA'],
        ...     'experience': ['ML Engineer'],
        ...     'education': ['CS Degree']
        ... }
        >>> role = {
        ...     'id': 'role1',
        ...     'skills': ['Python', 'PyTorch'],
        ...     'experience': ['ML'],
        ...     'education': ['CS']
        ... }
        >>> graph = build_candidate_role_graph(candidate, role)
        >>> print(graph.number_of_nodes())
    """
    graph = nx.Graph()
    
    # Create candidate node
    candidate_id = candidate_data.get('id', 'candidate')
    graph.add_node(candidate_id, type='candidate', **candidate_data)
    
    # Create role node
    role_id = role_data.get('id', 'role')
    graph.add_node(role_id, type='role', **role_data)
    
    # Create entity nodes and edges for candidate
    _create_entity_nodes(graph, candidate_id, candidate_data, 'candidate')
    
    # Create entity nodes and edges for role
    _create_entity_nodes(graph, role_id, role_data, 'role')
    
    # Create direct edge between candidate and role
    graph.add_edge(candidate_id, role_id, weight=1.0)
    
    # Add self-loops for message passing (GNN requirement)
    graph.add_edge(candidate_id, candidate_id, weight=1.0)
    graph.add_edge(role_id, role_id, weight=1.0)
    
    return graph


def _create_entity_nodes(
    graph: nx.Graph,
    parent_id: str,
    data: Dict[str, Any],
    parent_type: str
) -> None:
    """
    Create entity nodes (skills, experience, education) and connect to parent.
    
    Creates nodes for each entity type and connects them to the parent node
    (candidate or role) with edges.
    
    Args:
        graph: NetworkX graph to add nodes/edges to
        parent_id: ID of parent node (candidate or role)
        data: Dictionary containing entity lists
        parent_type: Type of parent ('candidate' or 'role')
    """
    entity_types = ['skills', 'experience', 'education']
    
    for entity_type in entity_types:
        entities = data.get(entity_type, [])
        
        # Handle both list and single value
        if not isinstance(entities, list):
            entities = [entities] if entities else []
        
        for entity in entities:
            if entity:  # Skip empty entities
                entity_node_id = f"{entity_type}_{entity}_{parent_type}"
                
                # Create entity node if it doesn't exist
                if not graph.has_node(entity_node_id):
                    graph.add_node(
                        entity_node_id,
                        type=entity_type,
                        name=entity,
                        parent_type=parent_type
                    )
                
                # Connect parent to entity
                graph.add_edge(parent_id, entity_node_id, weight=1.0)

