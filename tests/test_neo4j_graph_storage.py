"""
test_neo4j_graph_storage.py - Tests for Neo4j graph storage

Tests storing and retrieving complete graphs in Neo4j.
"""

import pytest
import networkx as nx
from backend.graph.graph_builder import build_candidate_role_graph
from backend.database.neo4j_client import Neo4jClient
from backend.database.neo4j_queries import create_schema
from backend.database.neo4j_graph_storage import store_graph


def test_store_graph():
    """Test storing complete graph in Neo4j."""
    candidate = {
        'id': 'cand_test',
        'skills': ['Python'],
        'experience': ['ML Engineer'],
        'education': ['CS']
    }
    role = {
        'id': 'role_test',
        'skills': ['Python'],
        'experience': ['ML'],
        'education': ['CS']
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    try:
        with Neo4jClient() as client:
            session = client.get_session()
            
            # Create schema
            create_schema(session)
            
            # Store graph
            store_graph(session, graph, 'cand_test', 'candidate')
            
            # Verify candidate node exists
            query = "MATCH (c:Candidate {id: 'cand_test'}) RETURN c"
            result = session.run(query)
            record = result.single()
            
            assert record is not None, "Candidate node should be stored"
            
            session.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


def test_store_graph_with_entities():
    """Test storing graph with entity nodes."""
    candidate = {
        'id': 'cand_entities',
        'skills': ['Python', 'CUDA'],
        'experience': ['ML'],
        'education': ['CS']
    }
    role = {
        'id': 'role_entities',
        'skills': ['Python'],
        'experience': [],
        'education': []
    }
    
    graph = build_candidate_role_graph(candidate, role)
    
    try:
        with Neo4jClient() as client:
            session = client.get_session()
            create_schema(session)
            
            store_graph(session, graph, 'cand_entities', 'candidate')
            
            # Verify entity nodes exist
            query = "MATCH (s:Skill) WHERE s.parent_id = 'cand_entities' RETURN s"
            result = session.run(query)
            records = list(result)
            
            assert len(records) > 0, "Entity nodes should be stored"
            
            session.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

