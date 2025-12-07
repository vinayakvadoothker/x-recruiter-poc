# Critical Phases for Hackathon Win

## Overview

These phases are **CRITICAL** for winning the hackathon. They address explicit judge requirements and core hackathon themes.

---

## Phase 9: Talent Clustering (3 hours)

### Why This Is Critical
- **Judge 1 explicitly requested**: "group talent abilities"
- Enables better matching (interviewers have cluster_success_rates)
- Shows advanced ML capabilities
- **Without this, you will NOT win**

### Implementation Details

#### File: `backend/matching/talent_clusterer.py`

**Clustering Algorithm**:
```python
class TalentClusterer:
    """
    Clusters candidates by ability using embedding-based K-means.
    
    Groups candidates into ability clusters like:
    - "CUDA/GPU Experts"
    - "LLM Inference Engineers"
    - "Fullstack Developers"
    - "ML Researchers"
    - "Systems Engineers"
    """
    
    def cluster_candidates(self, candidates: List[Dict]) -> Dict[str, List[str]]:
        """
        Cluster candidates and assign ability_cluster field.
        
        Process:
        1. Get embeddings for all candidates
        2. Run K-means clustering (K=5-10, determined by elbow method)
        3. Name clusters based on dominant skills/domains
        4. Assign ability_cluster to each candidate
        5. Return cluster assignments
        """
    
    def assign_candidate_to_cluster(self, candidate: Dict) -> str:
        """
        Assign single candidate to nearest cluster.
        
        Used for new candidates without re-clustering all.
        """
    
    def update_interviewer_cluster_rates(self):
        """
        Update interviewer cluster_success_rates based on historical performance.
        
        For each interviewer:
        - Calculate success rate per cluster
        - Update cluster_success_rates dict
        """
```

**Cluster Naming Strategy**:
- Analyze dominant skills in each cluster
- Use domain knowledge (e.g., CUDA + GPU → "CUDA/GPU Experts")
- Ensure names are human-readable and meaningful

**Integration Points**:
- Called after loading datasets (Phase 4.5)
- Called when new candidates added
- Used in matching (Phase 7) for cluster_success_rates

**Testing Requirements**:
- Test with 1,000+ candidates
- Verify cluster quality (good separation, meaningful names)
- Test edge cases (all candidates same, all different)
- Test re-clustering stability

---

## Phase 10: Feedback Loop Integration (3 hours)

### Why This Is Critical
- **Core hackathon requirement**: "self-improving agent"
- Judges need to see system learning from feedback
- Without this, it's just a static decision engine
- **Without this, you will NOT win**

### Implementation Details

#### File: `backend/orchestration/feedback_loop.py`

**Feedback Flow**:
```
Recruiter Feedback (X DM or API)
    ↓
recruiter_agent.collect_feedback(feedback_text, candidate_id, position_id)
    ↓
feedback_loop.process_feedback(candidate_id, position_id, feedback_text)
    ↓
Parse feedback → reward (positive=1.0, negative=0.0, neutral=0.5)
    ↓
Get candidate index from position's candidate list
    ↓
bandit.update(candidate_index, reward)
    ↓
learning_tracker.record_update(candidate_index, reward)
    ↓
Update knowledge graph with feedback history
    ↓
Return confirmation to recruiter
```

**Key Implementation**:
```python
class FeedbackLoop:
    """
    Processes recruiter feedback and updates bandit learning.
    """
    
    def process_feedback(
        self,
        candidate_id: str,
        position_id: str,
        feedback_text: str
    ) -> Dict:
        """
        Process feedback and update bandit.
        
        Steps:
        1. Parse feedback text → reward (0.0-1.0)
        2. Get position's candidate list
        3. Find candidate index
        4. Update bandit: bandit.update(index, reward)
        5. Track learning: learning_tracker.record_update()
        6. Store feedback in knowledge graph
        7. Return learning metrics
        """
    
    def get_learning_metrics(self) -> Dict:
        """
        Get current learning statistics.
        
        Returns:
        - Total feedback events
        - Average reward
        - Learning curve data
        - Improvement metrics
        """
```

**Modifications to Existing Code**:

1. **`backend/orchestration/recruiter_agent.py`**:
   - Remove TODOs (lines 145, 162)
   - Replace logging with actual `feedback_loop.process_feedback()` call
   - Connect to knowledge graph for candidate/position lookup

2. **Integration with Bandit**:
   - Use existing `bandit.update(arm_index, reward)` method
   - Track which candidates were selected for which positions
   - Map candidate_id → arm_index for updates

3. **Learning Tracker Integration**:
   - Use existing `LearningTracker` class
   - Record each feedback event
   - Track precision/recall over time
   - Export learning curves

**Testing Requirements**:
- Test positive/negative/neutral feedback
- Test feedback updates bandit priors correctly
- Test learning_tracker records updates
- Test feedback history stored in knowledge graph
- Test multiple feedback events (learning over time)

---

## Phase 11: Online Learning Demonstration (2 hours)

### Why This Is Critical
- Judges need to **SEE** the system learning
- Visual demonstration is more powerful than code
- Shows the innovation (embedding-warm-started FG-TS)
- **Without this, judges won't understand the innovation**

### Implementation Details

#### File: `backend/orchestration/learning_demo.py`

**Demonstration Flow**:
```python
class LearningDemo:
    """
    Demonstrates self-improving agent with learning curves.
    """
    
    def run_learning_simulation(
        self,
        candidates: List[Dict],
        positions: List[Dict],
        num_feedback_events: int = 100
    ) -> Dict:
        """
        Run learning simulation comparing warm-start vs cold-start.
        
        Process:
        1. Initialize two bandits:
           - Warm-start: initialize_from_embeddings()
           - Cold-start: uniform priors (alpha=1, beta=1)
        
        2. For each feedback event:
           - Select candidate using bandit
           - Generate feedback (simulated: 70% positive for good matches)
           - Update both bandits
           - Track metrics (regret, precision, recall)
        
        3. Compare results:
           - Learning speed (warm-start learns 3x faster)
           - Regret (warm-start has lower cumulative regret)
           - Precision/Recall (warm-start achieves higher accuracy faster)
        
        4. Export data:
           - Learning curves (JSON/CSV)
           - Metrics summary
           - Visualization-ready data
        """
    
    def compare_warm_vs_cold_start(self) -> Dict:
        """
        Compare warm-start vs cold-start learning.
        
        Returns:
        - Speedup factor (e.g., 3x faster)
        - Regret reduction (e.g., 40% lower regret)
        - Accuracy improvement (e.g., 20% higher precision)
        """
    
    def generate_learning_curves(self) -> Dict:
        """
        Generate learning curve data for visualization.
        
        Returns:
        - Regret over time (both bandits)
        - Precision over time (both bandits)
        - Recall over time (both bandits)
        - F1 score over time (both bandits)
        """
    
    def export_visualization_data(self, filepath: str = 'learning_data.json'):
        """
        Export learning data for plotting.
        
        Format:
        {
            "warm_start": {
                "regret": [0.5, 0.4, 0.3, ...],
                "precision": [0.6, 0.7, 0.8, ...],
                "recall": [0.5, 0.6, 0.7, ...],
                "f1": [0.55, 0.65, 0.75, ...]
            },
            "cold_start": {
                "regret": [0.8, 0.7, 0.6, ...],
                "precision": [0.5, 0.55, 0.6, ...],
                "recall": [0.4, 0.5, 0.6, ...],
                "f1": [0.45, 0.525, 0.6, ...]
            },
            "improvement": {
                "speedup": 3.0,
                "regret_reduction": 0.4,
                "precision_improvement": 0.2
            }
        }
        """
```

**Visualization Output**:
- JSON file with learning curves
- CSV file for spreadsheet plotting
- Summary metrics (speedup, regret reduction)
- Ready for plotting with matplotlib/plotly/external tools

**Testing Requirements**:
- Verify simulation runs without errors
- Verify learning curves show improvement
- Verify warm-start outperforms cold-start
- Calculate and verify improvement metrics
- Test with different numbers of feedback events

---

## Integration Checklist

### Phase 9: Clustering
- [ ] Create `backend/matching/talent_clusterer.py`
- [ ] Implement K-means clustering
- [ ] Integrate with knowledge graph
- [ ] Update candidate profiles
- [ ] Update interviewer cluster_success_rates
- [ ] Write tests
- [ ] Test with 1,000+ candidates

### Phase 10: Feedback Loop
- [ ] Create `backend/orchestration/feedback_loop.py`
- [ ] Connect recruiter_agent → feedback_loop
- [ ] Connect feedback_loop → bandit.update()
- [ ] Integrate learning_tracker
- [ ] Remove TODOs from recruiter_agent.py
- [ ] Write tests
- [ ] Test feedback updates

### Phase 11: Learning Demo
- [ ] Create `backend/orchestration/learning_demo.py`
- [ ] Implement simulation
- [ ] Compare warm vs cold start
- [ ] Generate learning curves
- [ ] Export visualization data
- [ ] Write tests
- [ ] Verify improvement metrics

---

## Success Metrics

### Phase 9: Clustering
- ✅ All candidates assigned to meaningful clusters
- ✅ Cluster names are human-readable (not "Cluster 1")
- ✅ Clusters show good separation (low intra-cluster variance)
- ✅ Interviewer cluster_success_rates updated

### Phase 10: Feedback Loop
- ✅ Feedback updates bandit priors correctly
- ✅ Learning_tracker records all updates
- ✅ Bandit decisions improve after feedback
- ✅ No TODOs remaining in recruiter_agent.py

### Phase 11: Learning Demo
- ✅ Warm-start learns 3x faster than cold-start
- ✅ Warm-start has 40% lower cumulative regret
- ✅ Learning curves exported (JSON/CSV)
- ✅ Improvement metrics calculated and verified

---

## Timeline

**Total Time**: 8 hours (3 + 3 + 2)

**Priority**: **CRITICAL** - Do these before Phase 7-8 if time is limited

**Dependencies**:
- Phase 9: Needs Phase 4.5 (datasets) complete
- Phase 10: Needs Phase 6 (decision engine) complete
- Phase 11: Needs Phase 10 (feedback loop) complete

**Order**: Phase 9 → Phase 10 → Phase 11 (sequential)

