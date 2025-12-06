# Vin's Implementation Checklist

## Your Role: Backend Core (Graph + ML Algorithm)

**Goal**: Build graph construction, similarity computation, and Feel-Good Thompson Sampling algorithm

**Timeline**: 3 days, 8 hours/day = 24 hours total

**Your Files** (You own these):
```
backend/
├── graph/
│   ├── graph_builder.py
│   ├── graph_similarity.py
│   └── entity_extractor.py
├── algorithms/
│   ├── fgts_bandit.py
│   └── bandit_utils.py
├── database/
│   ├── neo4j_schema.py
│   ├── neo4j_queries.py
│   └── neo4j_client.py
└── tests/
    ├── test_graph.py
    ├── test_similarity.py
    └── test_fgts.py
```

---

## Day 1: Foundation (8 hours)

### Hour 1-2: Graph Construction

**Task**: Build bipartite graph structure (from GNN paper)

**Checklist**:
- [ ] Create `backend/graph/graph_builder.py`
- [ ] Implement `build_candidate_role_graph(candidate_data, role_data) -> Graph`
- [ ] Create candidate node
- [ ] Create role node
- [ ] Create entity nodes (skills, experience, education) for candidate side
- [ ] Create entity nodes (skills, experience, education) for role side
- [ ] Create edges: candidate → entity nodes
- [ ] Create edges: role → entity nodes
- [ ] Create direct edge: candidate ↔ role
- [ ] Add self-loops for message passing
- [ ] Test with sample data

**Reference**: GNN Candidate-Job Matching paper, Section 4.1

**Code Structure**:
```python
def build_candidate_role_graph(candidate_data, role_data):
    """
    Build bipartite graph following Frazzetto et al. [1]
    
    Structure:
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
    """
    # Your implementation here
    pass
```

---

### Hour 3-4: Graph Similarity Computation

**Task**: Implement kNN-based similarity (from GNN paper)

**Checklist**:
- [ ] Create `backend/graph/graph_similarity.py`
- [ ] Implement `compute_entity_similarity(entity_candidate, entity_role, k=10) -> float`
- [ ] Implement kNN algorithm (use scipy or sklearn)
- [ ] Compute intersection of kNN neighborhoods
- [ ] Compute union of kNN neighborhoods
- [ ] Apply sharpening factor p=4: `(intersection/union)^(1/4)`
- [ ] Implement `compute_graph_similarity(role_graph, candidate_graph) -> float`
- [ ] Compute similarity for each entity type (skills, experience, education)
- [ ] Aggregate entity similarities (weighted average)
- [ ] Test with sample graphs

**Reference**: GNN paper, Equation 1, Section 4.2

**Code Structure**:
```python
def compute_edge_weight(entity_candidate, entity_role, k=10, p=4):
    """
    kNN-based similarity from GNN paper [1], Equation 1
    
    sim_ε(i,j) = (|kNN(v_ε,i) ∩ kNN(v_ε,j)| / |kNN(v_ε,i) ∪ kNN(v_ε,j)|)^(1/p)
    """
    # Your implementation here
    pass

def compute_graph_similarity(role_graph, candidate_graph):
    """
    Compute overall graph similarity by aggregating entity similarities
    """
    # Your implementation here
    pass
```

---

### Hour 5-6: Neo4j Setup

**Task**: Design schema and implement Neo4j integration

**Checklist**:
- [ ] Create `backend/database/neo4j_schema.py`
- [ ] Design node types: Candidate, Role, Skill, Experience, Education
- [ ] Design relationships: HAS_SKILL, REQUIRES_SKILL, MATCHES, HAS_ENTITY
- [ ] Create `neo4j_client.py` with connection handling
- [ ] Implement `create_schema()` - Create constraints and indexes
- [ ] Create `neo4j_queries.py` with Cypher queries:
  - [ ] `store_candidate(candidate_data)`
  - [ ] `store_role(role_data)`
  - [ ] `store_graph(graph)`
  - [ ] `get_candidate_graph(candidate_id)`
  - [ ] `get_role_graph(role_id)`
- [ ] Test Neo4j connection
- [ ] Test storing/retrieving graphs

**Neo4j Schema**:
```cypher
// Nodes
(:Candidate {id, github_handle, x_handle, created_at})
(:Role {id, title, requirements, created_at})
(:Skill {name, embedding})
(:Experience {years, domain, embedding})
(:Education {degree, field, embedding})

// Relationships
(:Candidate)-[:HAS_SKILL {weight}]->(:Skill)
(:Role)-[:REQUIRES_SKILL {weight}]->(:Skill)
(:Candidate)-[:MATCHES {score, timestamp}]->(:Role)
```

---

### Hour 7-8: FG-TS Algorithm (Basic)

**Task**: Implement Feel-Good Thompson Sampling (from FG-TS paper)

**Checklist**:
- [ ] Create `backend/algorithms/fgts_bandit.py`
- [ ] Create `GraphWarmStartedFGTS` class
- [ ] Implement `__init__(lambda_fg=0.01, b=1000)` - Initialize parameters
- [ ] Implement `initialize_from_graph(candidates, role_graph)` - Graph warm-start
- [ ] Implement `select_candidate()` - Thompson Sampling selection
- [ ] Implement feel-good bonus computation (from FG-TS paper, Equation 1)
- [ ] Implement `update(arm_index, reward)` - Bayesian update
- [ ] Create `backend/algorithms/bandit_utils.py` for helper functions
- [ ] Test with mock data

**Reference**: FG-TS paper, Section 2, Equation 1

**Code Structure**:
```python
class GraphWarmStartedFGTS:
    def __init__(self, lambda_fg=0.01, b=1000):
        """
        Feel-Good Thompson Sampling with graph warm-start
        
        Parameters from FG-TS paper [2]:
        - lambda_fg: Feel-good parameter (0.01 optimal from Table 4)
        - b: Cap parameter (1000 from experimental setup)
        """
        self.lambda_fg = lambda_fg
        self.b = b
        self.alpha = {}  # Success counts per arm
        self.beta = {}   # Failure counts per arm
    
    def initialize_from_graph(self, candidates, role_graph):
        """
        THE INNOVATION: Use graph structure to initialize priors
        
        High graph similarity → optimistic prior (higher alpha)
        Low graph similarity → pessimistic prior (higher beta)
        """
        # Compute graph similarities
        # Initialize alpha/beta based on similarity
        pass
    
    def select_candidate(self):
        """
        Select using Feel-Good Thompson Sampling [2]
        
        Uses Equation 1 from FG-TS paper:
        L_FG(θ, x, r) = η(f_θ(x) - r)² - λ min(b, f_θ(x))
        """
        # Thompson Sampling
        # Add feel-good bonus
        pass
    
    def update(self, arm_index, reward):
        """
        Bayesian update after observing reward
        """
        pass
```

---

## Day 2: Integration (8 hours)

### Hour 1-2: Graph-Warm-Start Integration

**Task**: Connect graph similarity to FG-TS initialization

**Checklist**:
- [ ] Import graph similarity functions into `fgts_bandit.py`
- [ ] Complete `initialize_from_graph()` implementation
- [ ] Convert graph similarity scores to alpha/beta priors
- [ ] Test warm-start initialization
- [ ] Compare warm-start vs cold-start (uniform priors)
- [ ] Verify priors are set correctly

**Implementation**:
```python
def initialize_from_graph(self, candidates, role_graph):
    # Build graphs for all candidates
    candidate_graphs = [build_candidate_graph(c) for c in candidates]
    
    # Compute graph similarities
    for i, cand_graph in enumerate(candidate_graphs):
        sim = compute_graph_similarity(role_graph, cand_graph)
        
        # Convert similarity to priors
        # High sim → optimistic (explore more)
        # Low sim → pessimistic (explore less)
        self.alpha[i] = 1 + sim * 10
        self.beta[i] = 1 + (1 - sim) * 10
```

---

### Hour 3-4: Entity Extraction Integration

**Task**: Integrate with Ishaan's Grok API for entity extraction

**Checklist**:
- [ ] Create `backend/graph/entity_extractor.py`
- [ ] Import Ishaan's `grok_api.py` (from `backend/integrations/`)
- [ ] Implement `extract_entities(text, entity_types) -> dict`
- [ ] Call Grok API for entity extraction
- [ ] Parse response (skills, experience, education)
- [ ] Structure entities for graph construction
- [ ] Test with sample candidate/role text
- [ ] Handle errors gracefully

**Interface with Ishaan**:
```python
# You call Ishaan's function
from backend.integrations.grok_api import extract_entities_with_grok

def extract_entities(candidate_text, role_text):
    """
    Extract entities using Grok API (via Ishaan's wrapper)
    """
    candidate_entities = extract_entities_with_grok(candidate_text)
    role_entities = extract_entities_with_grok(role_text)
    return {
        'candidate': candidate_entities,
        'role': role_entities
    }
```

---

### Hour 5-6: Algorithm Testing

**Task**: Write comprehensive tests

**Checklist**:
- [ ] Create `tests/test_graph.py`
  - [ ] Test graph construction
  - [ ] Test graph structure (nodes, edges)
  - [ ] Test with different entity types
- [ ] Create `tests/test_similarity.py`
  - [ ] Test kNN similarity computation
  - [ ] Test graph similarity aggregation
  - [ ] Test edge cases (empty graphs, no matches)
- [ ] Create `tests/test_fgts.py`
  - [ ] Test FG-TS initialization
  - [ ] Test graph warm-start
  - [ ] Test candidate selection
  - [ ] Test Bayesian updates
  - [ ] Test feel-good bonus
- [ ] Run all tests: `pytest tests/`
- [ ] Fix any failures

---

### Hour 7-8: Neo4j Integration

**Task**: Store and retrieve graphs from Neo4j

**Checklist**:
- [ ] Implement `store_graph(graph, graph_id)` in `neo4j_queries.py`
- [ ] Store candidate nodes
- [ ] Store role nodes
- [ ] Store entity nodes
- [ ] Store edges with weights
- [ ] Implement `get_candidate_graph(candidate_id)`
- [ ] Implement `get_role_graph(role_id)`
- [ ] Store bandit state (alpha, beta values)
- [ ] Test storing/retrieving complete graphs
- [ ] Optimize queries (add indexes)

**Cypher Queries**:
```cypher
// Store graph
CREATE (c:Candidate {id: $candidate_id, ...})
CREATE (r:Role {id: $role_id, ...})
CREATE (c)-[:MATCHES {score: $score}]->(r)

// Retrieve graph
MATCH (c:Candidate {id: $candidate_id})-[r:MATCHES]->(role:Role)
RETURN c, r, role
```

---

## Day 3: Polish & Demo (8 hours)

### Hour 1-2: Performance Optimization

**Task**: Optimize graph similarity and Neo4j queries

**Checklist**:
- [ ] Profile graph similarity computation
- [ ] Cache kNN computations
- [ ] Optimize similarity aggregation
- [ ] Add indexes to Neo4j (if needed)
- [ ] Optimize Cypher queries
- [ ] Test performance improvements

---

### Hour 3-4: Learning Curve Generation

**Task**: Track and visualize learning

**Checklist**:
- [ ] Add learning curve tracking to `fgts_bandit.py`
- [ ] Track response rates over time
- [ ] Track warm-start vs cold-start performance
- [ ] Generate data for visualization
- [ ] Export to JSON/CSV for Ishaan's dashboard
- [ ] Test with simulated data

**Data Format** (for Ishaan's dashboard):
```python
learning_data = {
    'warm_start': {
        'response_rates': [0.15, 0.18, 0.22, ...],
        'timestamps': [...]
    },
    'cold_start': {
        'response_rates': [0.10, 0.12, 0.15, ...],
        'timestamps': [...]
    }
}
```

---

### Hour 5-6: Final Testing

**Task**: End-to-end algorithm tests

**Checklist**:
- [ ] Test complete flow: graph → similarity → FG-TS → update
- [ ] Test with real candidate data (from Ishaan's sourcing)
- [ ] Test edge cases:
  - [ ] Empty candidate list
  - [ ] No graph similarity matches
  - [ ] All candidates have same similarity
- [ ] Performance benchmarks
- [ ] Verify learning improvement (warm-start > cold-start)
- [ ] Document any issues

---

### Hour 7-8: Documentation

**Task**: Code documentation and examples

**Checklist**:
- [ ] Add docstrings to all functions
- [ ] Add comments explaining algorithm steps
- [ ] Add paper citations in code comments
- [ ] Create usage examples
- [ ] Document parameters and return values
- [ ] Create README for your modules

**Example Docstring**:
```python
def compute_graph_similarity(role_graph, candidate_graph):
    """
    Compute graph similarity using kNN-based approach from Frazzetto et al. [1].
    
    Uses Equation 1 from GNN paper:
    sim_ε(i,j) = (|kNN(v_ε,i) ∩ kNN(v_ε,j)| / |kNN(v_ε,i) ∪ kNN(v_ε,j)|)^(1/p)
    
    Args:
        role_graph: Graph object for role
        candidate_graph: Graph object for candidate
    
    Returns:
        float: Similarity score between 0 and 1
    """
    pass
```

---

## Interface with Ishaan

### What You Provide (Ishaan calls these)

**Functions**:
```python
# graph_builder.py
def build_candidate_role_graph(candidate_data, role_data) -> Graph

# graph_similarity.py
def compute_graph_similarity(role_graph, candidate_graph) -> float

# fgts_bandit.py
class GraphWarmStartedFGTS:
    def initialize(candidates, role_graph) -> None
    def select() -> int
    def update(arm_index, reward) -> None
```

**Make sure these are stable and well-documented!**

---

### What You Need from Ishaan

**Functions** (Ishaan provides):
```python
# backend/integrations/grok_api.py
def extract_entities_with_grok(text, entity_types) -> dict

# backend/database/neo4j_client.py (if Ishaan sets it up)
def store_graph(graph, graph_id) -> None
def get_candidate_graph(candidate_id) -> Graph
```

**If Ishaan's code isn't ready**: Use mock data, implement later

---

## Success Criteria

**You're done when**:
- [ ] Graph construction works (bipartite graphs created)
- [ ] Graph similarity works (kNN-based, from paper)
- [ ] FG-TS algorithm works (with graph warm-start)
- [ ] Neo4j integration works (store/retrieve graphs)
- [ ] Learning curves show improvement (warm-start > cold-start)
- [ ] All tests pass
- [ ] Code is documented

---

## Quick Reference

**Papers to cite**:
- [1] Frazzetto et al. - Graph construction, kNN similarity
- [2] Anand & Liaw - Feel-Good Thompson Sampling

**Key algorithms**:
- kNN similarity: `(intersection/union)^(1/4)` where k=10, p=4
- FG-TS: `L_FG = η(f_θ(x) - r)² - λ min(b, f_θ(x))` where λ=0.01, b=1000
- Graph warm-start: `alpha = 1 + sim * 10`, `beta = 1 + (1-sim) * 10`

**Tech Stack**:
- `networkx` - Graphs
- `numpy` - Math
- `scipy` - kNN
- `neo4j` - Database
- `pytest` - Testing

---

**Remember**: Focus on your domain. Don't touch Ishaan's files. Daily sync at end of day. Ship it! 🚀

