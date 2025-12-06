# Database Module

This module handles Neo4j database operations for storing graphs and bandit state.

## Modules

### `neo4j_client.py`
Neo4j database connection management.

**Key Classes:**
- `Neo4jClient`: Context manager for Neo4j connections

**Usage:**
```python
from backend.database.neo4j_client import Neo4jClient

with Neo4jClient() as client:
    session = client.get_session()
    # Use session for queries
    session.close()
```

### `neo4j_schema.py`
Neo4j schema definitions (constraints and indexes).

**Key Functions:**
- `get_schema_constraints()`: Get all schema constraints

### `neo4j_queries.py`
Basic Cypher queries for storing/retrieving data.

**Key Functions:**
- `create_schema()`: Create schema
- `store_candidate()`: Store candidate node
- `store_role()`: Store role node
- `get_candidate_graph()`: Retrieve candidate graph
- `get_role_graph()`: Retrieve role graph

### `neo4j_graph_storage.py`
Store complete graphs in Neo4j.

**Key Functions:**
- `store_graph()`: Store complete graph with nodes and edges

### `neo4j_bandit_state.py`
Store and retrieve bandit state.

**Key Functions:**
- `store_bandit_state()`: Store bandit alpha/beta values
- `load_bandit_state()`: Load previous state
- `restore_bandit_from_state()`: Restore bandit from state

**Usage:**
```python
from backend.database.neo4j_bandit_state import (
    store_bandit_state,
    load_bandit_state,
    restore_bandit_from_state
)

# Store state
store_bandit_state(session, 'role_id', bandit)

# Load and restore
state = load_bandit_state(session, 'role_id')
restore_bandit_from_state(new_bandit, state)
```

