# Graph Module

This module handles graph construction and similarity computation for candidate-role matching.

## Modules

### `graph_builder.py`
Builds bipartite graphs for candidate-role matching following the GNN paper [1].

**Key Functions:**
- `build_candidate_role_graph()`: Main function to build bipartite graph

**Usage:**
```python
from backend.graph.graph_builder import build_candidate_role_graph

candidate = {
    'id': 'cand1',
    'skills': ['Python', 'CUDA'],
    'experience': ['ML Engineer'],
    'education': ['CS']
}

role = {
    'id': 'role1',
    'skills': ['Python', 'PyTorch'],
    'experience': ['ML'],
    'education': ['CS']
}

graph = build_candidate_role_graph(candidate, role)
```

### `graph_similarity.py`
Computes kNN-based graph similarity following Equation 1 from [1].

**Key Functions:**
- `compute_graph_similarity()`: Compute similarity between two graphs
- `compute_entity_similarity()`: Compute kNN similarity for entities

**Usage:**
```python
from backend.graph.graph_similarity import compute_graph_similarity

similarity = compute_graph_similarity(role_graph, candidate_graph)
# Returns: float between 0 and 1
```

## References
[1] Frazzetto et al. - Graph Neural Networks for Candidate-Job Matching

