"""
neo4j_schema.py - Neo4j database schema definition

This module defines the Neo4j graph database schema for storing
candidate and role data, including nodes, relationships, and constraints.

Schema Design:
- Nodes: Candidate, Role, Skill, Experience, Education, Action, BanditState
- Relationships: HAS_SKILL, REQUIRES_SKILL, MATCHES, HAS_ENTITY, HAS_ACTION

Dependencies:
- neo4j: Neo4j Python driver for database operations
"""

from typing import Dict, List, Any


# Node types
NODE_TYPES = {
    'CANDIDATE': 'Candidate',
    'ROLE': 'Role',
    'SKILL': 'Skill',
    'EXPERIENCE': 'Experience',
    'EDUCATION': 'Education',
    'ACTION': 'Action',
    'BANDIT_STATE': 'BanditState'
}

# Relationship types
RELATIONSHIP_TYPES = {
    'HAS_SKILL': 'HAS_SKILL',
    'REQUIRES_SKILL': 'REQUIRES_SKILL',
    'HAS_EXPERIENCE': 'HAS_EXPERIENCE',
    'REQUIRES_EXPERIENCE': 'REQUIRES_EXPERIENCE',
    'HAS_EDUCATION': 'HAS_EDUCATION',
    'REQUIRES_EDUCATION': 'REQUIRES_EDUCATION',
    'MATCHES': 'MATCHES',
    'HAS_ACTION': 'HAS_ACTION'
}


def get_schema_constraints() -> List[str]:
    """
    Get Cypher queries to create constraints and indexes.
    
    Returns:
        List of Cypher constraint/index creation queries
    """
    constraints = [
        # Unique constraints
        "CREATE CONSTRAINT candidate_id IF NOT EXISTS FOR (c:Candidate) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT role_id IF NOT EXISTS FOR (r:Role) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        
        # Indexes for performance
        "CREATE INDEX candidate_github IF NOT EXISTS FOR (c:Candidate) ON (c.github_handle)",
        "CREATE INDEX role_title IF NOT EXISTS FOR (r:Role) ON (r.title)",
        "CREATE INDEX action_timestamp IF NOT EXISTS FOR (a:Action) ON (a.timestamp)",
    ]
    
    return constraints


def get_node_properties(node_type: str) -> Dict[str, Any]:
    """
    Get expected properties for a node type.
    
    Args:
        node_type: Type of node (from NODE_TYPES)
    
    Returns:
        Dictionary of property names and descriptions
    """
    properties = {
        'Candidate': {
            'id': 'Unique candidate identifier',
            'github_handle': 'GitHub username',
            'x_handle': 'X/Twitter username',
            'created_at': 'Timestamp when created'
        },
        'Role': {
            'id': 'Unique role identifier',
            'title': 'Job title',
            'requirements': 'Role requirements text',
            'created_at': 'Timestamp when created'
        },
        'Skill': {
            'name': 'Skill name',
            'embedding': 'Skill embedding vector (JSON)'
        },
        'Experience': {
            'years': 'Years of experience',
            'domain': 'Domain/field',
            'embedding': 'Experience embedding vector (JSON)'
        },
        'Education': {
            'degree': 'Degree type',
            'field': 'Field of study',
            'embedding': 'Education embedding vector (JSON)'
        },
        'Action': {
            'id': 'Unique action identifier',
            'arm_index': 'Selected arm/candidate index',
            'context': 'Context data (JSON)',
            'reward': 'Reward value',
            'is_qualified': 'Whether candidate was qualified',
            'timestamp': 'Action timestamp'
        },
        'BanditState': {
            'role_id': 'Role identifier',
            'alpha': 'Alpha values (JSON array)',
            'beta': 'Beta values (JSON array)',
            'precision_history': 'Precision history (JSON array)',
            'recall_history': 'Recall history (JSON array)',
            'timestamp': 'State timestamp'
        }
    }
    
    return properties.get(node_type, {})

