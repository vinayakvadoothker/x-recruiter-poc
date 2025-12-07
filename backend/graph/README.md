# Graph Module

This module handles graph construction for candidate-role matching.

**Note**: Graph similarity computation has been removed. We now use embedding similarity instead (vector DB).

## Current Components

### `graph_builder.py`
Builds bipartite graphs for candidate-role matching following Frazzetto et al. [1].

**Key functions:**
- `build_candidate_role_graph()`: Main graph construction

**Usage:**
```python
from backend.graph.graph_builder import build_candidate_role_graph

graph = build_candidate_role_graph(candidate_data, role_data)
```

## Removed Components

### `graph_similarity.py` (REMOVED)
Graph similarity computation has been removed. We now use embedding similarity via vector database instead.
