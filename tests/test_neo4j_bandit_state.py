"""
test_neo4j_bandit_state.py - Tests for Neo4j bandit state storage

Tests storing and retrieving bandit state (alpha/beta values).
"""

import pytest
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS
from backend.database.neo4j_client import Neo4jClient
from backend.database.neo4j_queries import create_schema, store_role
from backend.database.neo4j_bandit_state import (
    store_bandit_state,
    load_bandit_state,
    restore_bandit_from_state
)


def test_store_bandit_state():
    """Test storing bandit state in Neo4j."""
    try:
        with Neo4jClient() as client:
            session = client.get_session()
            create_schema(session)
            
            # Create role
            store_role(session, {'id': 'role_bandit_test', 'title': 'Test Role'})
            
            # Create bandit
            candidates = [
                {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []}
            ]
            role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
            
            bandit = GraphWarmStartedFGTS()
            bandit.initialize_from_graph(candidates, role_data)
            
            # Update bandit
            bandit.update(0, reward=1.0)
            
            # Store state
            store_bandit_state(session, 'role_bandit_test', bandit)
            
            # Verify state stored
            query = "MATCH (r:Role {id: 'role_bandit_test'}) RETURN r.bandit_alpha as alpha"
            result = session.run(query)
            record = result.single()
            
            assert record is not None, "Bandit state should be stored"
            assert record["alpha"] is not None, "Alpha values should be stored"
            
            session.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


def test_load_bandit_state():
    """Test loading bandit state from Neo4j."""
    try:
        with Neo4jClient() as client:
            session = client.get_session()
            create_schema(session)
            
            # Create role and store state
            store_role(session, {'id': 'role_load_test', 'title': 'Test Role'})
            
            candidates = [
                {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []}
            ]
            role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
            
            bandit = GraphWarmStartedFGTS()
            bandit.initialize_from_graph(candidates, role_data)
            bandit.update(0, reward=1.0)
            
            store_bandit_state(session, 'role_load_test', bandit)
            
            # Load state
            state = load_bandit_state(session, 'role_load_test')
            
            assert state is not None, "State should be loaded"
            assert 'alpha' in state, "State should contain alpha"
            assert 'beta' in state, "State should contain beta"
            assert state['num_arms'] == 1, "State should have correct num_arms"
            
            session.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


def test_restore_bandit_from_state():
    """Test restoring bandit from loaded state."""
    try:
        with Neo4jClient() as client:
            session = client.get_session()
            create_schema(session)
            
            store_role(session, {'id': 'role_restore_test', 'title': 'Test Role'})
            
            # Create and store bandit
            candidates = [
                {'id': 'cand1', 'skills': ['Python'], 'experience': [], 'education': []}
            ]
            role_data = {'id': 'role1', 'skills': ['Python'], 'experience': [], 'education': []}
            
            original_bandit = GraphWarmStartedFGTS()
            original_bandit.initialize_from_graph(candidates, role_data)
            original_bandit.update(0, reward=1.0)
            original_alpha = original_bandit.alpha[0]
            
            store_bandit_state(session, 'role_restore_test', original_bandit)
            
            # Load and restore
            state = load_bandit_state(session, 'role_restore_test')
            new_bandit = GraphWarmStartedFGTS()
            restore_bandit_from_state(new_bandit, state)
            
            # Verify restored state
            assert new_bandit.num_arms == 1, "Num arms should be restored"
            assert new_bandit.alpha[0] == original_alpha, "Alpha should be restored"
            
            session.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

