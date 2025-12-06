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

### Hour 7-8: FG-TS Algorithm (Basic) + Context Space Updates

**Task**: Implement Feel-Good Thompson Sampling (from FG-TS paper) + Track context space updates

**Checklist**:
- [ ] Create `backend/algorithms/fgts_bandit.py`
- [ ] Create `GraphWarmStartedFGTS` class
- [ ] Implement `__init__(lambda_fg=0.01, b=1000)` - Initialize parameters
- [ ] Implement `initialize_from_graph(candidates, role_graph)` - Graph warm-start
- [ ] Implement `select_candidate()` - Thompson Sampling selection
- [ ] Implement feel-good bonus computation (from FG-TS paper, Equation 1)
- [ ] Implement `update(arm_index, reward)` - Bayesian update
- [ ] **NEW: Track context space updates (Track requirement)**
  - [ ] Store context (graph similarity, candidate features) with each selection
  - [ ] Track how context influences decisions
  - [ ] Update context representation based on feedback
  - [ ] This is the "context space updates" the track mentions
- [ ] **NEW: Document how bandit updates = policy updates**
  - [ ] Alpha/beta parameters = policy parameters
  - [ ] Bayesian update = policy gradient update (online RL)
  - [ ] Context (graph similarity) influences policy
- [ ] Create `backend/algorithms/bandit_utils.py` for helper functions
- [ ] Test with mock data

**Key Point for Presentation**:
- Track says "policy gradient or context space updates"
- Our bandit updates ARE context space updates:
  - Context = graph similarity + candidate features
  - Updates = Bayesian updates to alpha/beta (policy parameters)
  - This is online RL that learns from deployment

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

### Hour 7-8: Neo4j Integration + Context Space Persistence

**Task**: Store and retrieve graphs from Neo4j + Store context space for "learning on the job"

**Checklist**:
- [ ] Implement `store_graph(graph, graph_id)` in `neo4j_queries.py`
- [ ] Store candidate nodes
- [ ] Store role nodes
- [ ] Store entity nodes
- [ ] Store edges with weights
- [ ] Implement `get_candidate_graph(candidate_id)`
- [ ] Implement `get_role_graph(role_id)`
- [ ] Store bandit state (alpha, beta values)
- [ ] **NEW: Store context space (Track requirement - "context space updates")**
  - [ ] Store each action with context: `(:Action {context, reward, timestamp})`
  - [ ] Store bandit state snapshots: `(:BanditState {alpha, beta, timestamp})`
  - [ ] Enable "learning on the job" - system remembers across sessions
- [ ] **NEW: Implement `load_bandit_state(role_id)` - Resume learning**
  - [ ] Load previous alpha/beta values from Neo4j
  - [ ] Load precision/recall history
  - [ ] Continue learning from where it left off
- [ ] Test storing/retrieving complete graphs
- [ ] Test loading/resuming bandit state
- [ ] Optimize queries (add indexes)

**Cypher Queries**:
```cypher
// Store graph
CREATE (c:Candidate {id: $candidate_id, ...})
CREATE (r:Role {id: $role_id, ...})
CREATE (c)-[:MATCHES {score: $score}]->(r)

// NEW: Store action with context (for "context space updates")
CREATE (a:Action {
    id: $action_id,
    arm_index: $arm_index,
    context: $context,  // {graph_similarity, candidate_features}
    reward: $reward,
    is_qualified: $is_qualified,
    timestamp: $timestamp
})
CREATE (r:Role {id: $role_id})-[:HAS_ACTION]->(a)

// NEW: Store bandit state (for "learning on the job")
CREATE (bs:BanditState {
    role_id: $role_id,
    alpha: $alpha,  // JSON array
    beta: $beta,    // JSON array
    precision_history: $precision_history,
    recall_history: $recall_history,
    timestamp: $timestamp
})

// NEW: Load bandit state (resume learning)
MATCH (bs:BanditState {role_id: $role_id})
ORDER BY bs.timestamp DESC
LIMIT 1
RETURN bs.alpha, bs.beta, bs.precision_history, bs.recall_history

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

### Hour 3-4: Learning Curve Generation + Precision/Recall Metrics

**Task**: Track and visualize learning + Add precision/recall metrics (CRITICAL FOR 100%)

**Checklist**:
- [ ] Add learning curve tracking to `fgts_bandit.py`
- [ ] Track response rates over time
- [ ] Track warm-start vs cold-start performance
- [ ] **ADD: Precision/Recall tracking (CRITICAL - Track requirement)**
  - [ ] Track true positives (selected + qualified)
  - [ ] Track false positives (selected + not qualified)
  - [ ] Track false negatives (not selected + qualified)
  - [ ] Calculate precision = TP / (TP + FP)
  - [ ] Calculate recall = TP / (TP + FN)
  - [ ] Calculate F1 score = 2 * (precision * recall) / (precision + recall)
- [ ] **ADD: Context space tracking (Track mentions "context space updates")**
  - [ ] Store context (graph similarity, candidate features) with each action
  - [ ] Track how context influences decisions over time
  - [ ] Store in Neo4j as `(:Action {context, timestamp, reward})`
- [ ] **ADD: Cumulative regret tracking (Bandit metric)**
  - [ ] Track regret = best_arm_reward - selected_arm_reward
  - [ ] Cumulative regret shows learning efficiency
- [ ] Generate data for visualization
- [ ] Export to JSON/CSV for Ishaan's dashboard
- [ ] Test with simulated data

**Data Format** (for Ishaan's dashboard):
```python
learning_data = {
    'warm_start': {
        'response_rates': [0.15, 0.18, 0.22, ...],
        'precision': [0.60, 0.65, 0.70, ...],  # NEW
        'recall': [0.50, 0.55, 0.60, ...],     # NEW
        'f1_score': [0.55, 0.60, 0.65, ...],  # NEW
        'cumulative_regret': [0.5, 0.8, 1.0, ...],  # NEW
        'timestamps': [...]
    },
    'cold_start': {
        'response_rates': [0.10, 0.12, 0.15, ...],
        'precision': [0.50, 0.52, 0.55, ...],  # NEW
        'recall': [0.40, 0.42, 0.45, ...],     # NEW
        'f1_score': [0.44, 0.47, 0.50, ...],   # NEW
        'cumulative_regret': [1.0, 1.5, 2.0, ...],  # NEW
        'timestamps': [...]
    }
}
```

**Precision/Recall Implementation** (Add to `fgts_bandit.py`):
```python
class GraphWarmStartedFGTS:
    def __init__(self, ...):
        # ... existing code ...
        self.true_positives = 0   # NEW
        self.false_positives = 0   # NEW
        self.false_negatives = 0 # NEW
        self.precision_history = []  # NEW
        self.recall_history = []     # NEW
    
    def update(self, arm_index, reward, is_qualified=None):
        """
        Update after observing reward
        
        NEW: Track precision/recall if is_qualified is provided
        """
        if reward > 0:
            self.alpha[arm_index] += 1
            if is_qualified is not None:
                if is_qualified:
                    self.true_positives += 1
                else:
                    self.false_positives += 1
        else:
            self.beta[arm_index] += 1
            if is_qualified is not None and is_qualified:
                self.false_negatives += 1
        
        # Calculate precision/recall
        if self.true_positives + self.false_positives > 0:
            precision = self.true_positives / (self.true_positives + self.false_positives)
            self.precision_history.append(precision)
        
        if self.true_positives + self.false_negatives > 0:
            recall = self.true_positives / (self.true_positives + self.false_negatives)
            self.recall_history.append(recall)
    
    def get_metrics(self):
        """Return current precision/recall/F1"""
        precision = self.precision_history[-1] if self.precision_history else 0.0
        recall = self.recall_history[-1] if self.recall_history else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return {'precision': precision, 'recall': recall, 'f1': f1}
```

**Context Space Tracking** (Add to Neo4j schema):
```cypher
// NEW: Store context with each action
(:Action {
    id,
    arm_index,
    context: {graph_similarity, candidate_features},
    reward,
    is_qualified,
    timestamp
})
```

---

### Hour 5-6: Final Testing + Confidence Intervals

**Task**: End-to-end algorithm tests + Add confidence intervals for bandit estimates

**Checklist**:
- [ ] Test complete flow: graph → similarity → FG-TS → update
- [ ] Test with real candidate data (from Ishaan's sourcing)
- [ ] Test edge cases:
  - [ ] Empty candidate list
  - [ ] No graph similarity matches
  - [ ] All candidates have same similarity
- [ ] **NEW: Add confidence intervals (shows uncertainty in estimates)**
  - [ ] Calculate 95% confidence interval for each arm: `beta_confidence_interval(alpha, beta)`
  - [ ] Track confidence intervals over time
  - [ ] Show in learning curves (bandit is more confident as it learns)
- [ ] **NEW: Test precision/recall calculation**
  - [ ] Test with known qualified/unqualified candidates
  - [ ] Verify precision/recall metrics are correct
  - [ ] Test edge cases (no positives, all positives)
- [ ] **NEW: Test context space persistence**
  - [ ] Save bandit state, reload, verify it continues learning
  - [ ] Test "learning on the job" - system remembers across sessions
- [ ] Performance benchmarks
- [ ] Verify learning improvement (warm-start > cold-start)
- [ ] Verify precision/recall improves over time
- [ ] Document any issues

**Confidence Interval Implementation** (Add to `bandit_utils.py`):
```python
import scipy.stats as stats

def get_confidence_interval(alpha, beta, confidence=0.95):
    """
    Get confidence interval for beta distribution
    
    Returns (lower_bound, upper_bound) for the mean
    """
    mean = alpha / (alpha + beta)
    variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    std = np.sqrt(variance)
    
    # Use normal approximation (works well for large alpha+beta)
    z_score = stats.norm.ppf((1 + confidence) / 2)
    lower = max(0, mean - z_score * std)
    upper = min(1, mean + z_score * std)
    
    return (lower, upper, mean)
```

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

---

## 🎯 CONCRETE ADDITIONS TO REACH 100% ALIGNMENT

**These are specific, doable additions that address track requirements:**

### 1. Precision/Recall Metrics (CRITICAL - Track Requirement)
**What**: Track precision/recall against real hiring benchmarks
**Where**: Add to `fgts_bandit.py` update() method
**Time**: 30 minutes
**Code**: See "Hour 3-4" section above - precision/recall implementation

### 2. Context Space Tracking (Track Requirement)
**What**: Store context (graph similarity, features) with each action
**Where**: Add to Neo4j schema + `fgts_bandit.py`
**Time**: 1 hour
**Code**: See "Hour 7-8 Neo4j" section - Action nodes with context

### 3. Bandit State Persistence (Learning on the Job)
**What**: Save/load bandit state so system remembers across sessions
**Where**: Add to `neo4j_queries.py`
**Time**: 1 hour
**Code**: See "Hour 7-8 Neo4j" section - BanditState nodes

### 4. Confidence Intervals (Shows Uncertainty)
**What**: Calculate 95% confidence intervals for bandit estimates
**Where**: Add to `bandit_utils.py`
**Time**: 30 minutes
**Code**: See "Hour 5-6" section - confidence interval function

### 5. Cumulative Regret (Bandit Metric)
**What**: Track regret = best_arm_reward - selected_arm_reward
**Where**: Add to `fgts_bandit.py`
**Time**: 20 minutes
**Code**: Track in update() method, store in learning_data

### 6. F1 Score (Precision/Recall Combined)
**What**: Calculate F1 = 2 * (precision * recall) / (precision + recall)
**Where**: Add to `fgts_bandit.py` get_metrics()
**Time**: 10 minutes
**Code**: See precision/recall implementation above

**Total Additional Time**: ~3.5 hours (fits in Day 3)

**Why These Matter**:
- Precision/Recall: Explicit track requirement ("measurable precision/recall")
- Context Space: Track mentions "context space updates" - this is it
- State Persistence: Enables "learning on the job" across sessions
- Confidence Intervals: Shows technical depth, proper bandit metrics
- Regret: Standard bandit metric, shows learning efficiency
- F1 Score: Standard ML metric, shows overall performance

**All of these are concrete, proven approaches - no experimental stuff.**

