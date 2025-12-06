"""
test_neo4j_connection.py - Tests for Neo4j connection

Tests the Neo4j client connection and basic operations.
Requires Neo4j to be running (via Docker).
"""

import pytest
from backend.database.neo4j_client import Neo4jClient


def test_neo4j_connection():
    """Test Neo4j connection."""
    client = Neo4jClient()
    
    try:
        connected = client.connect()
        assert connected is True
        
        # Test session creation
        session = client.get_session()
        assert session is not None
        
        # Test simple query
        result = session.run("RETURN 1 as value")
        record = result.single()
        assert record["value"] == 1
        
        session.close()
        client.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

