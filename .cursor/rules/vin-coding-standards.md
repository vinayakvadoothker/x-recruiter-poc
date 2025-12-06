# Vin's Coding Standards - Production Grade MVP

## Core Principles

1. **Production-grade code only** - No simulations, mocks, or prototypes
2. **Test-driven development** - Test plan → Implement → Test → Verify → Move on
3. **Fast iteration** - Don't over-optimize, MVP that works, then move forward
4. **Well-engineered** - Build for maintainability, not hacking

## File Structure Rules

### File Size
- **Maximum 100 lines per file** (excluding comments/docstrings)
- Split into focused, single-responsibility modules
- If a file exceeds 100 lines, refactor into smaller modules

### File Organization
- Each file has **one clear purpose**
- Compartmentalization over convenience
- Reusability (DRY) but not over-abstracted
- If code needs to be repeated, that's fine - clarity > DRY when it makes sense

## Code Documentation Standards

### Every File Must Have:
1. **Explainer block at the top** (5-10 lines):
   ```python
   """
   [File Name] - [One sentence purpose]
   
   This module handles [specific responsibility].
   
   Key functions:
   - function1(): [brief description]
   - function2(): [brief description]
   
   Dependencies:
   - module1: [why we need it]
   - module2: [why we need it]
   """
   ```

2. **LLM-friendly comments** throughout:
   - Explain WHY, not just WHAT
   - Use clear, descriptive variable names
   - Comment complex logic or algorithms
   - Reference papers/equations when applicable

3. **API documentation** for all functions/classes:
   ```python
   def function_name(param1: Type, param2: Type) -> ReturnType:
       """
       [One-line description]
       
       Args:
           param1: [description]
           param2: [description]
       
       Returns:
           [description]
       
       Raises:
           [exceptions if any]
       
       Example:
           >>> result = function_name(value1, value2)
           >>> print(result)
       """
   ```

## Code Quality Rules

### No TODOs
- **Never use TODO comments**
- If something needs to be done, do it now or document it properly
- If it's future work, put it in a separate planning document, not in code

### Code Readability
- Any engineer should understand what a file does by reading it
- Clear variable names (no abbreviations unless standard)
- Logical flow (top to bottom, easy to follow)
- Group related code together

### Error Handling
- Handle errors explicitly
- Don't silently fail
- Provide meaningful error messages
- Log errors appropriately

## Testing Workflow

### For Each Component:
1. **Write test plan first** (what are we testing?)
2. **Implement the code**
3. **Write tests**
4. **Run tests and verify**
5. **Move on** (don't over-optimize)

### Test Requirements:
- Test happy path
- Test edge cases
- Test error conditions
- Verify it works before moving on

## Development Process

### Iteration Speed
- Build → Test → Verify → Move on
- Don't get stuck optimizing
- MVP that works > perfect code that's incomplete
- Fast feedback loops

### Code Review Checklist
Before considering code "done":
- [ ] File is under 100 lines
- [ ] Has explainer block at top
- [ ] Has API documentation
- [ ] Has LLM-friendly comments
- [ ] No TODO comments
- [ ] Tests written and passing
- [ ] Code is readable by any engineer

## Examples

### Good File Structure:
```python
"""
graph_builder.py - Builds bipartite graphs for candidate-role matching

This module constructs graph structures following the GNN paper [1],
creating bipartite graphs with candidate/role nodes connected via
entity nodes (skills, experience, education).

Key functions:
- build_candidate_role_graph(): Main graph construction
- create_entity_nodes(): Creates skill/exp/edu nodes
- create_edges(): Connects nodes with weights

Dependencies:
- networkx: Graph data structure
- entity_extractor: Extracts entities from text
"""

import networkx as nx
from typing import Dict, List
from backend.graph.entity_extractor import extract_entities

def build_candidate_role_graph(candidate_data: Dict, role_data: Dict) -> nx.Graph:
    """
    Build bipartite graph for candidate-role matching.
    
    Creates a graph structure where candidate and role nodes are
    connected through shared entity nodes (skills, experience, education).
    Edge weights represent similarity scores.
    
    Args:
        candidate_data: Dictionary with candidate information
        role_data: Dictionary with role requirements
    
    Returns:
        NetworkX Graph object with candidate, role, and entity nodes
    
    Example:
        >>> candidate = {"skills": ["Python", "CUDA"], ...}
        >>> role = {"skills": ["Python", "PyTorch"], ...}
        >>> graph = build_candidate_role_graph(candidate, role)
        >>> print(graph.number_of_nodes())
    """
    # Implementation here
    pass
```

### Bad File Structure:
```python
# TODO: Add error handling
# TODO: Optimize this
def build_graph(c, r):  # What are c and r?
    # Does stuff
    pass
```

## Technology Stack

### Core Language & Runtime
- **Python 3.11+** - Modern Python with type hints
- **Poetry** or **pip** - Dependency management
- **Git** - Version control

### Graph & ML Libraries (Vin's Domain)
- **networkx>=3.0** - Graph data structures and algorithms
- **numpy>=1.24** - Numerical computations (arrays, math operations)
- **scipy>=1.10** - Scientific computing (kNN algorithms, statistical functions)

### Database
- **neo4j>=5.0** - Graph database driver (Python client)
- **Neo4j Database** - Run via Docker: `docker run -d -p 7474:7474 -p 7687:7687 neo4j:latest`

### Testing
- **pytest>=7.0** - Testing framework
- **pytest-cov** (optional) - Code coverage

### Environment & Configuration
- **python-dotenv>=1.0** - Load environment variables from `.env` file

### APIs (Used by Ishaan, but Vin may need to know about)
- **Grok API** - Entity extraction, embeddings (via Ishaan's wrapper)
- **GitHub API** - Candidate sourcing (via Ishaan's wrapper)
- **X API** - Profile data, DMs (via Ishaan's wrapper)

### Type Hints & Validation
- **typing** (built-in) - Type hints for function signatures
- Use type hints everywhere: `def func(param: Type) -> ReturnType:`

### Code Style
- Follow PEP 8
- Use type hints for all function parameters and returns
- Use descriptive variable names

### Dependencies File
Vin's dependencies should be in `requirements-vin.txt`:
```
networkx>=3.0
numpy>=1.24
scipy>=1.10
neo4j>=5.0
pytest>=7.0
python-dotenv>=1.0
```

### Environment Variables (.env)
Vin needs these (human assistant will add):
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
GROK_API_KEY=xxx  # (via Ishaan's integration)
```

### When to Use Each Technology

**NetworkX**: 
- Graph construction (bipartite graphs)
- Graph manipulation (nodes, edges, properties)
- Graph algorithms (if needed)

**NumPy**:
- Array operations
- Mathematical computations
- Statistical calculations (mean, std, etc.)

**SciPy**:
- kNN algorithms for graph similarity
- Statistical distributions (beta distribution for Thompson Sampling)
- Distance calculations

**Neo4j**:
- Store graph structures persistently
- Store candidate/role data
- Store bandit state (alpha, beta values)
- Store context space (actions with context)
- Query graph relationships

**pytest**:
- All unit tests
- Integration tests
- Test fixtures for mock data

**Docker**:
- **All development and testing in Docker** - No manual venv activation
- Neo4j database (standardized setup)
- Python app runs in Docker container
- Use Docker Compose for multi-container setups
- Always use Docker for external services (databases, etc.)
- Run tests: `docker-compose run app pytest tests/ -v`
- Run specific test: `docker-compose run app pytest tests/test_end_to_end.py -v`

## Environment Variables & Human Assistant Collaboration

### .env File Management
- **Never hardcode secrets or API keys**
- **Never simulate or mock** - ask human assistant for real values
- Human assistant will manage `.env` file
- All environment variables loaded via `python-dotenv`

### When to Ask Human Assistant

**Ask immediately when you need:**
1. **API Keys**: Grok API key, GitHub token (if needed)
2. **Database Credentials**: Neo4j password, connection strings
3. **Docker Setup**: If Docker containers need to be started
4. **Testing**: Real API calls, real database connections
5. **Environment Setup**: Missing dependencies, configuration issues

**How to Ask:**
- Be specific: "I need the GROK_API_KEY added to .env"
- Provide context: "For entity extraction in Hour 2"
- Don't proceed with mocks - wait for real values

### .env File Structure
Human assistant will create/maintain `.env`:
```bash
# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<human assistant sets this>

# Grok API (via Ishaan's integration)
GROK_API_KEY=<human assistant sets this>

# GitHub API (if needed)
GITHUB_TOKEN=<human assistant sets this>
```

### Docker Standardization
- **Always use Docker** for external services
- Neo4j runs in Docker: `docker run -d -p 7474:7474 -p 7687:7687 neo4j:latest`
- Human assistant will start Docker containers when needed
- Ask human assistant to verify Docker containers are running

### No Mocking Policy
- **Never create mock functions** for APIs or databases
- **Never simulate** responses or data
- **Ask human assistant** for real API keys, real database access
- If something isn't ready, **wait and ask** rather than mocking

## Git & Version Control

### .gitignore Requirements
- **Always maintain proper .gitignore**
- Never commit sensitive files (.env, API keys, passwords)
- Never commit build artifacts or cache files
- Never commit virtual environments

### What Should Be Ignored
- **Python artifacts**: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `.Python`
- **Virtual environments**: `venv/`, `env/`, `.venv/`
- **Environment variables**: `.env`, `.env.local`, `.env.*.local`
- **IDE files**: `.vscode/`, `.idea/`, `*.swp`, `*.swo`
- **Test artifacts**: `.pytest_cache/`, `.coverage`, `htmlcov/`
- **OS files**: `.DS_Store`, `Thumbs.db`
- **Docker volumes**: `neo4j_data/`, `neo4j_logs/`
- **Build artifacts**: `build/`, `dist/`, `*.egg-info/`

### What Should Be Committed
- Source code (`.py` files)
- Test files (`tests/`)
- Configuration files (`requirements*.txt`, `docker-compose.yml`, `Dockerfile`)
- Documentation (`.md` files)
- `.gitignore` itself
- `.cursor/rules/` (coding standards)

### Git Workflow
- Commit frequently with clear messages
- Never commit `.env` files (use `.env.example` if needed)
- Review `.gitignore` before first commit
- Verify sensitive data isn't tracked: `git status` before committing

## Remember

- **Production-grade, not prototype**
- **Test everything**
- **Move fast, but verify**
- **Code for humans, not just machines**
- **No TODOs in code**
- **Use the right tool for the job** - Don't over-engineer
- **Proper .gitignore** - Never commit secrets or artifacts

