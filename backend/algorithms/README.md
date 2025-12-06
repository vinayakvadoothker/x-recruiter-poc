# Algorithms Module

This module implements the Feel-Good Thompson Sampling algorithm with graph warm-start.

## Modules

### `fgts_bandit.py`
Main bandit algorithm implementation.

**Key Classes:**
- `GraphWarmStartedFGTS`: Feel-Good Thompson Sampling with graph warm-start

**Usage:**
```python
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS

bandit = GraphWarmStartedFGTS(lambda_fg=0.01, b=1000.0)
bandit.initialize_from_graph(candidates, role_data)

selected = bandit.select_candidate()
bandit.update(selected, reward=1.0)
```

### `bandit_utils.py`
Utility functions for bandit operations.

**Key Functions:**
- `get_confidence_interval()`: Calculate confidence intervals
- `compute_f1_score()`: Calculate F1 score

### `learning_tracker.py`
Tracks learning metrics over time.

**Key Classes:**
- `LearningTracker`: Tracks precision/recall, F1, regret, response rates

**Usage:**
```python
from backend.algorithms.learning_tracker import LearningTracker

tracker = LearningTracker()
tracker.record_interaction(selected_arm, reward, is_optimal=True)
summary = tracker.get_summary()
```

### `learning_data_export.py`
Exports learning data for dashboards.

**Key Functions:**
- `export_learning_data_json()`: Export to JSON
- `export_learning_data_csv()`: Export to CSV

## References
[1] Anand & Liaw - Feel-Good Thompson Sampling

