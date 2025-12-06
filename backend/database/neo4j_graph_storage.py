"""
neo4j_graph_storage.py - Store and retrieve complete graphs in Neo4j

This module handles storing complete graph structures (nodes and edges)
in Neo4j, including entity nodes and relationships.

Key functions:
- store_graph(): Store complete graph with nodes and edges
- store_entity_nodes(): Store entity nodes (skills, experience, education)
- store_graph_edges(): Store edges between nodes

Dependencies:
- networkx: Graph structure
"""

import networkx as nx
from typing import Dict, Any


def store_graph(session, graph: nx.Graph, graph_id: str, graph_type: str = 'candidate') -> None:
    """
    Store complete graph in Neo4j.
    
    Stores all nodes and edges from a NetworkX graph into Neo4j,
    including candidate/role nodes, entity nodes, and relationships.
    
    Args:
        session: Neo4j session object
        graph: NetworkX Graph object to store
        graph_id: Identifier for the graph
        graph_type: Type of graph ('candidate' or 'role')
    """
    # Store main node (candidate or role)
    if graph_type == 'candidate':
        store_candidate_node(session, graph, graph_id)
    else:
        store_role_node(session, graph, graph_id)
    
    # Store entity nodes
    store_entity_nodes(session, graph, graph_id, graph_type)
    
    # Store edges
    store_graph_edges(session, graph, graph_id, graph_type)


def store_candidate_node(session, graph: nx.Graph, candidate_id: str) -> None:
    """Store candidate node from graph."""
    if candidate_id not in graph.nodes():
        return
    
    node_data = graph.nodes[candidate_id]
    query = """
    MERGE (c:Candidate {id: $id})
    SET c += $properties
    """
    
    properties = {k: v for k, v in node_data.items() if k != 'type'}
    session.run(query, id=candidate_id, properties=properties)


def store_role_node(session, graph: nx.Graph, role_id: str) -> None:
    """Store role node from graph."""
    if role_id not in graph.nodes():
        return
    
    node_data = graph.nodes[role_id]
    query = """
    MERGE (r:Role {id: $id})
    SET r += $properties
    """
    
    properties = {k: v for k, v in node_data.items() if k != 'type'}
    session.run(query, id=role_id, properties=properties)


def store_entity_nodes(session, graph: nx.Graph, graph_id: str, graph_type: str) -> None:
    """Store entity nodes (skills, experience, education) from graph."""
    entity_types = ['skills', 'experience', 'education']
    
    for node_id, node_data in graph.nodes(data=True):
        if node_id == graph_id:
            continue
        
        entity_type = node_data.get('type', '')
        if entity_type not in entity_types:
            continue
        
        # Use Skill, Experience, Education as node labels
        label_map = {
            'skills': 'Skill',
            'experience': 'Experience',
            'education': 'Education'
        }
        label = label_map.get(entity_type, 'Entity')
        
        query = f"""
        MERGE (e:{label} {{id: $id}})
        SET e.name = $name,
            e.parent_id = $parent_id,
            e.parent_type = $parent_type
        """
        
        session.run(
            query,
            id=node_id,
            name=node_data.get('name', ''),
            parent_id=graph_id,
            parent_type=graph_type
        )


def store_graph_edges(session, graph: nx.Graph, graph_id: str, graph_type: str) -> None:
    """Store edges from graph."""
    for source, target, edge_data in graph.edges(data=True):
        weight = edge_data.get('weight', 1.0)
        
        # Determine relationship type based on node types
        source_data = graph.nodes[source]
        target_data = graph.nodes[target]
        
        rel_type = _determine_relationship_type(source_data, target_data)
        
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:{rel_type}]->(b)
        SET r.weight = $weight
        """
        
        try:
            session.run(
                query,
                source_id=source,
                target_id=target,
                weight=weight
            )
        except Exception:
            # Edge might already exist or nodes not found, continue
            pass


def _determine_relationship_type(source_data: Dict, target_data: Dict) -> str:
    """Determine Neo4j relationship type from node data."""
    source_type = source_data.get('type', '')
    target_type = target_data.get('type', '')
    
    if source_type == 'candidate' and target_type in ['skills', 'experience', 'education']:
        return 'HAS_' + target_type.upper()
    elif source_type == 'role' and target_type in ['skills', 'experience', 'education']:
        return 'REQUIRES_' + target_type.upper()
    elif source_type == 'candidate' and target_type == 'role':
        return 'MATCHES'
    else:
        return 'RELATES_TO'



