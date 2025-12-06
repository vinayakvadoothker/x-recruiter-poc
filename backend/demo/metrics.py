"""
Metrics collection and visualization for learning curves.

Tracks response rates, warm-start vs cold-start performance, and learning improvements.
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and stores learning metrics for the recruitment system.
    """
    
    def __init__(self, metrics_file: str = "metrics.json"):
        """
        Initialize metrics collector.
        
        Args:
            metrics_file: Path to JSON file for storing metrics
        """
        self.metrics_file = Path(metrics_file)
        self.metrics: Dict = {
            'warm_start': {
                'response_rates': [],
                'timestamps': [],
                'interactions': []
            },
            'cold_start': {
                'response_rates': [],
                'timestamps': [],
                'interactions': []
            },
            'total_interactions': 0,
            'total_feedback': 0
        }
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Load metrics from file if it exists."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    self.metrics = json.load(f)
                logger.info(f"Loaded metrics from {self.metrics_file}")
            except Exception as e:
                logger.warning(f"Error loading metrics: {e}")
    
    def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def record_interaction(
        self,
        interaction_type: str,
        response_rate: Optional[float] = None,
        using_warm_start: bool = True
    ) -> None:
        """
        Record an interaction and update metrics.
        
        Args:
            interaction_type: Type of interaction ("sourcing", "outreach", "feedback")
            response_rate: Response rate if available
            using_warm_start: Whether warm-start was used
        """
        self.metrics['total_interactions'] += 1
        
        key = 'warm_start' if using_warm_start else 'cold_start'
        timestamp = datetime.now().isoformat()
        
        self.metrics[key]['timestamps'].append(timestamp)
        self.metrics[key]['interactions'].append(interaction_type)
        
        if response_rate is not None:
            self.metrics[key]['response_rates'].append(response_rate)
        else:
            # Use previous rate or default
            prev_rates = self.metrics[key]['response_rates']
            if prev_rates:
                self.metrics[key]['response_rates'].append(prev_rates[-1])
            else:
                self.metrics[key]['response_rates'].append(0.0)
        
        self._save_metrics()
    
    def record_feedback(self, feedback_type: str, reward: float) -> None:
        """
        Record feedback and update metrics.
        
        Args:
            feedback_type: Type of feedback ("positive", "negative", "neutral")
            reward: Reward value (0.0 to 1.0)
        """
        self.metrics['total_feedback'] += 1
        self._save_metrics()
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics.
        
        Returns:
            Metrics dictionary
        """
        return self.metrics.copy()
    
    def get_response_rates(self, warm_start: bool = True) -> List[float]:
        """
        Get response rates for warm-start or cold-start.
        
        Args:
            warm_start: Whether to get warm-start or cold-start rates
        
        Returns:
            List of response rates
        """
        key = 'warm_start' if warm_start else 'cold_start'
        return self.metrics[key]['response_rates'].copy()


def plot_learning_curves(
    warm_start_data: Optional[Dict] = None,
    cold_start_data: Optional[Dict] = None,
    metrics_collector: Optional[MetricsCollector] = None
) -> go.Figure:
    """
    Plot learning curves comparing warm-start vs cold-start.
    
    Args:
        warm_start_data: Warm-start metrics data (optional)
        cold_start_data: Cold-start metrics data (optional)
        metrics_collector: MetricsCollector instance (optional)
    
    Returns:
        Plotly figure object
    """
    # Get data from collector if provided
    if metrics_collector:
        metrics = metrics_collector.get_metrics()
        warm_start_data = metrics.get('warm_start', {})
        cold_start_data = metrics.get('cold_start', {})
    
    # Use provided data or defaults
    warm_rates = warm_start_data.get('response_rates', []) if warm_start_data else []
    cold_rates = cold_start_data.get('response_rates', []) if cold_start_data else []
    
    # Generate x-axis (interaction numbers)
    warm_x = list(range(1, len(warm_rates) + 1)) if warm_rates else []
    cold_x = list(range(1, len(cold_rates) + 1)) if cold_rates else []
    
    # Create figure
    fig = go.Figure()
    
    # Add warm-start curve
    if warm_rates:
        fig.add_trace(go.Scatter(
            x=warm_x,
            y=warm_rates,
            mode='lines+markers',
            name='Graph Warm-Started FG-TS',
            line=dict(color='#1DA1F2', width=2),
            marker=dict(size=6)
        ))
    
    # Add cold-start curve
    if cold_rates:
        fig.add_trace(go.Scatter(
            x=cold_x,
            y=cold_rates,
            mode='lines+markers',
            name='Cold-Start FG-TS',
            line=dict(color='#657786', width=2, dash='dash'),
            marker=dict(size=6)
        ))
    
    # Update layout
    fig.update_layout(
        title="Learning Curves: Warm-Start vs Cold-Start",
        xaxis_title="Interactions",
        yaxis_title="Response Rate",
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        template="plotly_white"
    )
    
    return fig


def plot_response_rate_over_time(
    metrics_collector: MetricsCollector,
    warm_start: bool = True
) -> go.Figure:
    """
    Plot response rate over time.
    
    Args:
        metrics_collector: MetricsCollector instance
        warm_start: Whether to plot warm-start or cold-start
    
    Returns:
        Plotly figure object
    """
    metrics = metrics_collector.get_metrics()
    key = 'warm_start' if warm_start else 'cold_start'
    
    timestamps = metrics[key].get('timestamps', [])
    response_rates = metrics[key].get('response_rates', [])
    
    if not timestamps or not response_rates:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=response_rates,
        mode='lines+markers',
        name='Response Rate',
        line=dict(color='#1DA1F2', width=2)
    ))
    
    fig.update_layout(
        title=f"Response Rate Over Time ({'Warm-Start' if warm_start else 'Cold-Start'})",
        xaxis_title="Time",
        yaxis_title="Response Rate",
        template="plotly_white"
    )
    
    return fig


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get or create global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

