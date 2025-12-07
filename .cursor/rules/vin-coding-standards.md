# Vin's Coding Standards - Production Grade MVP

## Core Principles

1. **Production-grade code only** - No simulations, mocks, or prototypes
2. **Test-driven development** - Test plan → Implement → Test → Verify → Move on
3. **Fast iteration** - Don't over-optimize, MVP that works, then move forward
4. **Well-engineered** - Build for maintainability, not hacking

## File Structure Rules

### File Size
- **Maximum 200 lines per file** (non-test files, excluding comments/docstrings)
- **Maximum 100 lines per file** (test files, excluding comments/docstrings)
- Split into focused, single-responsibility modules
- If a file exceeds the limit, refactor into smaller modules

### File Organization
- Each file has **one clear purpose**
- Compartmentalization over convenience
- Reusability (DRY) but not over-abstracted
- If code needs to be repeated, that's fine - clarity > DRY when it makes sense

## Code Documentation Standards

### Every File Must Have:
1. **Research citations** (if applicable):
   - If the file implements algorithms, methods, or concepts from research papers:
     - Include detailed citations in the module docstring
     - Reference specific papers with [1], [2], etc.
     - Cite specific equations, parameters, or methods used
     - Clearly distinguish between cited work and novel contributions
     - See `CITATIONS.md` for paper references and citation format
   - Example:
     ```python
     """
     fgts_bandit.py - Feel-Good Thompson Sampling with Graph Warm-Start
     
     Research Paper Citations:
     [1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
         An Inductive Learning Approach." Data Science and Engineering, 2025.
         - Used for: Graph construction and similarity computation
         - See: backend.graph.graph_builder, backend.graph.graph_similarity
     
     [2] Anand, E., & Liaw, S. "Feel-Good Thompson Sampling for Contextual Bandits:
         a Markov Chain Monte Carlo Showdown." NeurIPS 2025.
         - Used for: Feel-Good Thompson Sampling algorithm
         - Feel-good bonus: λ min(b, f_θ(x)) (Equation 1 from [2])
         - Parameters: λ=0.01 (optimal from [2] Table 4), b=1000 (from [2] setup)
     
     Our Novel Contribution:
     Graph-warm-started bandits: Using graph structure [1] to initialize FG-TS [2]
     priors. This is the first application of graph structure as prior knowledge
     for bandit initialization, enabling faster learning and smarter exploration.
     
     For more details, see CITATIONS.md.
     """
     ```

2. **Implementation Rationale** (MANDATORY):
   Every file must include a section explaining:
   - **Why this implementation approach was chosen** vs alternatives
   - **What alternatives were considered** and why they were rejected
   - **Trade-offs made** (performance, simplicity, maintainability, etc.)
   - **Design decisions** that might not be obvious
   
   This should be in the module docstring after the explainer block:
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
   
   Implementation Rationale:
   We chose [approach] over [alternative] because:
   - [Reason 1]: [explanation]
   - [Reason 2]: [explanation]
   - [Trade-off]: [what we sacrificed for this choice]
   
   Alternatives considered:
   - [Alternative 1]: Rejected because [reason]
   - [Alternative 2]: Rejected because [reason]
   
   Design decisions:
   - [Decision 1]: [why this was chosen]
   - [Decision 2]: [why this was chosen]
   """
   ```

3. **Explainer block at the top** (5-10 lines):
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

3. **LLM-friendly comments** throughout:
   - Explain WHY, not just WHAT
   - Use clear, descriptive variable names
   - Comment complex logic or algorithms
   - Reference papers/equations when applicable

4. **API documentation** for all functions/classes:
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

**Test Structure (MANDATORY)**:
Each phase must have tests organized in 4 difficulty levels:
- `tests/phaseX_name/easy/` - Basic functionality tests
- `tests/phaseX_name/medium/` - Edge cases and error handling
- `tests/phaseX_name/hard/` - Complex scenarios and integration
- `tests/phaseX_name/super_hard/` - Stress tests and performance

**Test Documentation (MANDATORY)**:
Every test file MUST include in its docstring:
- **Why this test exists**: Clear reasoning explaining the purpose
- **What it validates**: Specific functionality being tested
- **Expected behavior**: What should happen when the test passes

Example:
```python
"""
test_basic_embedding.py - Basic embedding functionality tests

Why this test exists:
This test verifies that all 4 embed methods (candidate, team, interviewer, position)
work correctly with valid input. This is critical because embeddings are the foundation
of our similarity search and matching system.

What it validates:
- embed_candidate() returns valid embedding vector
- embed_team() returns valid embedding vector
- embed_interviewer() returns valid embedding vector
- embed_position() returns valid embedding vector
- All embeddings have correct dimensions (768 for MPNet)
- All embeddings are normalized (unit vectors)

Expected behavior:
- All 4 methods should return numpy arrays of shape (768,)
- All embeddings should be normalized (||embedding|| ≈ 1.0)
- No errors or exceptions should be raised
"""
```

**Test Requirements**:
- Test happy path (easy tests)
- Test edge cases (medium tests)
- Test error conditions (medium/hard tests)
- Test complex scenarios (hard tests)
- Test performance/stress (super_hard tests)
- Verify it works before moving on

## Development Process

### Iteration Speed
- Build → Test → Verify → Move on
- Don't get stuck optimizing
- MVP that works > perfect code that's incomplete
- Fast feedback loops

### Code Review Checklist
Before considering code "done":
- [ ] File is under 200 lines (non-test files) or 100 lines (test files)
- [ ] Has research citations (if applicable)
- [ ] Has explainer block at top
- [ ] Has implementation rationale (why this approach vs alternatives)
- [ ] Has API documentation
- [ ] Has LLM-friendly comments
- [ ] No TODO comments
- [ ] Tests written and passing (all 4 levels: easy, medium, hard, super_hard)
- [ ] All test files have clear reasoning in docstrings (why each test exists)
- [ ] Code is readable by any engineer

## Examples

### Good File Structure:
```python
"""
graph_builder.py - Builds bipartite graphs for candidate-role matching

This module constructs graph structures following the GNN paper [1],
creating bipartite graphs with candidate/role nodes connected via
entity nodes (skills, experience, education).

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Bipartite graph construction methodology
    - See CITATIONS.md for full citation details

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
1. **API Keys**: Grok API key, GitHub token, X API key, arXiv API key, LinkedIn access, etc.
2. **API Access**: API account creation, API approval, rate limits, authentication setup
3. **API Documentation**: Official API docs, endpoint specifications, request/response formats
4. **Database Credentials**: Neo4j password, connection strings, Weaviate setup, vector DB credentials
5. **Docker Setup**: If Docker containers need to be started, Docker Compose configuration
6. **Testing**: Real API calls, real database connections, test data access
7. **Environment Setup**: Missing dependencies, configuration issues, environment variable values
8. **External Services**: Access to third-party services, account setup, service configuration
9. **Documentation**: Research papers, technical specifications, implementation guides
10. **Any Blockers**: If you're stuck and need help, ask immediately

**How to Ask:**
- Be specific: "I need the GROK_API_KEY added to .env"
- Provide context: "For entity extraction in Hour 2"
- Include what you need: "I need access to the X API documentation for implementing the X API client"
- Don't proceed with mocks - wait for real values
- If blocked: "I'm blocked on [X] and need [Y] to proceed"

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
- **Ask human assistant** for real API keys, real database access, API documentation, etc.
- If something isn't ready, **wait and ask** rather than mocking
- **Never guess** API endpoints, request formats, or authentication methods - ask for documentation

### Asking for Help
- **Ask early, ask often** - Don't waste time trying to figure out API details
- **Be specific** - "I need the X API documentation" not "I need help with X API"
- **Provide context** - Explain what you're trying to build and why you need it
- **List what you need** - If you need multiple things, list them all at once
- **Don't assume** - If you're not sure about something, ask rather than guessing

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

## Checklist Management

### Always Check Off Checklist Items
- **MANDATORY**: After completing each phase, check off ALL checklist items in `vin_pivot_plan.md`
- **Update checklist immediately** after completing tasks - don't wait until the end
- **Verify completion**: Before moving to next phase, ensure all items are checked off
- **Track progress**: Use checklist to track what's done and what's left

### Error Checking
- **Check for errors after EVERY phase**: Run tests, check imports, verify linting
- **No errors allowed**: Fix all errors before moving to next phase
- **Test before moving on**: Always run `pytest tests/ -v` after each phase
- **Import verification**: Always verify imports work: `python -c "from backend.module import Class"`
- **Linting check**: Run linting checks to catch errors early
- **Don't accumulate errors**: Fix errors immediately, don't let them pile up

### Phase Completion Checklist
At the end of each phase, ALWAYS:
1. [ ] Check off all checklist items for that phase
2. [ ] Run all tests for that phase: `pytest tests/phaseX_name/ -v` (all 4 levels: easy, medium, hard, super_hard)
3. [ ] Verify no import errors: `python -c "from backend.module import Class"`
4. [ ] Check for linting errors: `pytest --collect-only` (should not error)
5. [ ] Verify functionality works as expected
6. [ ] Verify all test files have clear reasoning in docstrings (why each test exists)
7. [ ] Update checklist in `vin_pivot_plan.md`
8. [ ] Only then move to next phase

## Remember

- **Production-grade, not prototype**
- **Test everything**
- **Move fast, but verify**
- **Code for humans, not just machines**
- **No TODOs in code**
- **Use the right tool for the job** - Don't over-engineer
- **Proper .gitignore** - Never commit secrets or artifacts
- **ALWAYS check off checklist items** - Track progress in real-time
- **ALWAYS check for errors** - Fix errors immediately, don't accumulate them

