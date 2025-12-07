"""
test_basic_simulation.py - Easy tests for basic learning simulation

Why this test exists:
This test verifies that the learning demo can run a basic simulation without errors.
This is the foundation - without a working simulation, we cannot demonstrate the
self-improving agent. We need to ensure the simulation runs, generates data, and
exports files correctly.

What it validates:
- run_learning_simulation() runs without errors
- Simulation generates learning curves (regret, precision, recall, f1)
- Export functions work (JSON and CSV)
- Both warm-start and cold-start bandits are initialized
- Learning metrics are tracked for both bandits

Expected behavior:
- Simulation completes with 100 feedback events
- Learning curves contain data for both warm-start and cold-start
- JSON and CSV files are created and contain valid data
- Improvement metrics are calculated
"""

import pytest
import os
import logging
import json
import csv
from backend.orchestration.learning_demo import LearningDemo
from backend.database.knowledge_graph import KnowledgeGraph

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestBasicSimulation:
    """Test basic learning simulation."""
    
    def setup_method(self):
        """Set up learning demo and test data."""
        logger.info("Setting up learning demo test")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        os.environ["WEAVIATE_URL"] = weaviate_url
        
        self.kg = KnowledgeGraph()
        self.demo = LearningDemo(knowledge_graph=self.kg)
        
        # Create test position
        self.position = {
            'id': 'position_001',
            'title': 'Senior LLM Inference Engineer',
            'required_skills': ['Python', 'CUDA', 'LLM Optimization'],
            'experience_level': 'Senior',
            'domain': 'AI/ML'
        }
        
        # Create test candidates (10 candidates for simulation)
        self.candidates = [
            {
                'id': f'candidate_{i:03d}',
                'name': f'Candidate {i}',
                'skills': ['Python', 'CUDA', 'LLM Optimization'] if i < 3 else ['Python', 'Java'],
                'experience_years': 5 + i,
                'domain': 'AI/ML' if i < 3 else 'Web Development'
            }
            for i in range(10)
        ]
        
        # Add candidates to knowledge graph
        for candidate in self.candidates:
            self.kg.add_candidate(candidate)
        self.kg.add_position(self.position)
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'demo'):
            self.demo.close()
        if hasattr(self, 'kg'):
            self.kg.close()
    
    def test_simulation_runs_without_errors(self):
        """Test that simulation runs without errors."""
        logger.info("Testing simulation runs without errors")
        
        result = self.demo.run_learning_simulation(
            candidates=self.candidates,
            position=self.position,
            num_feedback_events=50  # Smaller for faster tests
        )
        
        # Verify result structure
        assert 'warm_start_metrics' in result
        assert 'cold_start_metrics' in result
        assert 'learning_curves' in result
        assert 'improvement_metrics' in result
        assert 'simulation_config' in result
        
        logger.info("✅ Simulation completed successfully")
    
    def test_learning_curves_generated(self):
        """Test that learning curves are generated."""
        logger.info("Testing learning curves generation")
        
        result = self.demo.run_learning_simulation(
            candidates=self.candidates,
            position=self.position,
            num_feedback_events=50
        )
        
        curves = result['learning_curves']
        
        # Verify warm-start curves
        assert 'warm_start' in curves
        warm_curves = curves['warm_start']
        assert 'regret' in warm_curves
        assert 'precision' in warm_curves
        assert 'recall' in warm_curves
        assert 'f1' in warm_curves
        assert 'events' in warm_curves
        
        # Verify cold-start curves
        assert 'cold_start' in curves
        cold_curves = curves['cold_start']
        assert 'regret' in cold_curves
        assert 'precision' in cold_curves
        assert 'recall' in cold_curves
        assert 'f1' in cold_curves
        assert 'events' in cold_curves
        
        # Verify curves have data
        assert len(warm_curves['events']) > 0
        assert len(cold_curves['events']) > 0
        
        logger.info(f"✅ Learning curves generated: {len(warm_curves['events'])} events")
    
    def test_export_json_works(self):
        """Test that JSON export works."""
        logger.info("Testing JSON export")
        
        result = self.demo.run_learning_simulation(
            candidates=self.candidates,
            position=self.position,
            num_feedback_events=50
        )
        
        json_filepath = "test_learning_data.json"
        export_result = self.demo.export_visualization_data(result, json_filepath=json_filepath)
        
        # Verify file was created
        assert os.path.exists(json_filepath)
        assert export_result['json_file'] == json_filepath
        
        # Verify JSON is valid
        with open(json_filepath, 'r') as f:
            data = json.load(f)
            assert 'warm_start_metrics' in data
            assert 'cold_start_metrics' in data
            assert 'learning_curves' in data
        
        # Clean up
        if os.path.exists(json_filepath):
            os.remove(json_filepath)
        
        logger.info("✅ JSON export works correctly")
    
    def test_export_csv_works(self):
        """Test that CSV export works."""
        logger.info("Testing CSV export")
        
        result = self.demo.run_learning_simulation(
            candidates=self.candidates,
            position=self.position,
            num_feedback_events=50
        )
        
        csv_filepath = "test_learning_data.csv"
        export_result = self.demo.export_visualization_data(result, csv_filepath=csv_filepath)
        
        # Verify file was created
        assert os.path.exists(csv_filepath)
        assert export_result['csv_file'] == csv_filepath
        
        # Verify CSV is valid
        with open(csv_filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert 'event' in header
            assert 'warm_regret' in header
            assert 'cold_regret' in header
            
            # Verify data rows exist
            rows = list(reader)
            assert len(rows) > 0
        
        # Clean up
        if os.path.exists(csv_filepath):
            os.remove(csv_filepath)
        
        logger.info("✅ CSV export works correctly")
    
    def test_improvement_metrics_calculated(self):
        """Test that improvement metrics are calculated."""
        logger.info("Testing improvement metrics calculation")
        
        result = self.demo.run_learning_simulation(
            candidates=self.candidates,
            position=self.position,
            num_feedback_events=50
        )
        
        improvement = result['improvement_metrics']
        
        # Verify improvement metrics structure
        assert 'speedup' in improvement or improvement['speedup'] is None
        assert 'regret_reduction' in improvement
        assert 'precision_improvement' in improvement
        assert 'f1_improvement' in improvement
        assert 'events_to_80_percent_precision' in improvement
        assert 'final_metrics' in improvement
        
        logger.info(f"✅ Improvement metrics calculated: speedup={improvement.get('speedup')}, regret_reduction={improvement.get('regret_reduction'):.2f}")

