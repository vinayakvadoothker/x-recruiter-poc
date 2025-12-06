"""
neo4j_queries.py - Cypher queries for Neo4j operations

This module contains all Cypher queries for storing and retrieving
data from Neo4j, including candidates, roles, graphs, and bandit state.

Key functions:
- create_schema(): Create constraints and indexes
- store_candidate(): Store candidate data
- store_role(): Store role data
- get_candidate_graph(): Retrieve candidate graph
- get_role_graph(): Retrieve role graph

Dependencies:
- backend.database.neo4j_schema: Schema definitions
"""

from typing import Dict, Any, Optional
from backend.database.neo4j_schema import get_schema_constraints


def create_schema(session) -> None:
    """
    Create Neo4j schema (constraints and indexes).
    
    Args:
        session: Neo4j session object
    """
    constraints = get_schema_constraints()
    
    for constraint_query in constraints:
        try:
            session.run(constraint_query)
        except Exception:
            # Constraint might already exist, continue
            pass


def store_candidate(session, candidate_data: Dict[str, Any]) -> None:
    """
    Store candidate node in Neo4j.
    
    Args:
        session: Neo4j session object
        candidate_data: Dictionary with candidate information
            Required: 'id'
            Optional: 'github_handle', 'x_handle', 'created_at'
    """
    query = """
    MERGE (c:Candidate {id: $id})
    SET c.github_handle = $github_handle,
        c.x_handle = $x_handle,
        c.created_at = $created_at
    """
    
    session.run(
        query,
        id=candidate_data.get('id'),
        github_handle=candidate_data.get('github_handle'),
        x_handle=candidate_data.get('x_handle'),
        created_at=candidate_data.get('created_at')
    )


def store_role(session, role_data: Dict[str, Any]) -> None:
    """
    Store role node in Neo4j.
    
    Args:
        session: Neo4j session object
        role_data: Dictionary with role information
            Required: 'id'
            Optional: 'title', 'requirements', 'created_at'
    """
    query = """
    MERGE (r:Role {id: $id})
    SET r.title = $title,
        r.requirements = $requirements,
        r.created_at = $created_at
    """
    
    session.run(
        query,
        id=role_data.get('id'),
        title=role_data.get('title'),
        requirements=role_data.get('requirements'),
        created_at=role_data.get('created_at')
    )


def get_candidate_graph(session, candidate_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve candidate graph from Neo4j.
    
    Args:
        session: Neo4j session object
        candidate_id: Candidate identifier
    
    Returns:
        Dictionary with candidate data and relationships, or None if not found
    """
    query = """
    MATCH (c:Candidate {id: $candidate_id})
    OPTIONAL MATCH (c)-[r]->(related)
    RETURN c, collect(r) as relationships, collect(related) as related_nodes
    """
    
    result = session.run(query, candidate_id=candidate_id)
    record = result.single()
    
    if record is None:
        return None
    
    candidate = dict(record["c"])
    return {
        'candidate': candidate,
        'relationships': [dict(rel) for rel in record["relationships"]],
        'related_nodes': [dict(node) for node in record["related_nodes"]]
    }


def get_role_graph(session, role_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve role graph from Neo4j.
    
    Args:
        session: Neo4j session object
        role_id: Role identifier
    
    Returns:
        Dictionary with role data and relationships, or None if not found
    """
    query = """
    MATCH (r:Role {id: $role_id})
    OPTIONAL MATCH (r)-[rel]->(related)
    RETURN r, collect(rel) as relationships, collect(related) as related_nodes
    """
    
    result = session.run(query, role_id=role_id)
    record = result.single()
    
    if record is None:
        return None
    
    role = dict(record["r"])
    return {
        'role': role,
        'relationships': [dict(rel) for rel in record["relationships"]],
        'related_nodes': [dict(node) for node in record["related_nodes"]]
    }

