"""
neo4j_bandit_state.py - Store and retrieve bandit state in Neo4j

This module handles persistence of FG-TS bandit state (alpha/beta values)
in Neo4j for learning continuity across sessions.

Key functions:
- store_bandit_state(): Store bandit alpha/beta values
- load_bandit_state(): Load previous bandit state

Dependencies:
- backend.algorithms.fgts_bandit: GraphWarmStartedFGTS
"""

from typing import Dict, Any, Optional
from backend.algorithms.fgts_bandit import GraphWarmStartedFGTS


def store_bandit_state(session, role_id: str, bandit: GraphWarmStartedFGTS) -> None:
    """
    Store bandit state (alpha/beta values) in Neo4j.
    
    Args:
        session: Neo4j session object
        role_id: Role identifier
        bandit: GraphWarmStartedFGTS instance to store
    """
    query = """
    MERGE (r:Role {id: $role_id})
    SET r.bandit_alpha = $alpha,
        r.bandit_beta = $beta,
        r.bandit_num_arms = $num_arms,
        r.bandit_lambda_fg = $lambda_fg,
        r.bandit_b = $b
    """
    
    # Convert alpha/beta dicts to lists for storage
    alpha_list = [bandit.alpha.get(i, 1.0) for i in range(bandit.num_arms)]
    beta_list = [bandit.beta.get(i, 1.0) for i in range(bandit.num_arms)]
    
    session.run(
        query,
        role_id=role_id,
        alpha=alpha_list,
        beta=beta_list,
        num_arms=bandit.num_arms,
        lambda_fg=bandit.lambda_fg,
        b=bandit.b
    )


def load_bandit_state(session, role_id: str) -> Optional[Dict[str, Any]]:
    """
    Load bandit state from Neo4j.
    
    Args:
        session: Neo4j session object
        role_id: Role identifier
    
    Returns:
        Dictionary with bandit state, or None if not found
    """
    query = """
    MATCH (r:Role {id: $role_id})
    RETURN r.bandit_alpha as alpha,
           r.bandit_beta as beta,
           r.bandit_num_arms as num_arms,
           r.bandit_lambda_fg as lambda_fg,
           r.bandit_b as b
    """
    
    result = session.run(query, role_id=role_id)
    record = result.single()
    
    if record is None or record["alpha"] is None:
        return None
    
    return {
        'alpha': record["alpha"],
        'beta': record["beta"],
        'num_arms': record["num_arms"],
        'lambda_fg': record["lambda_fg"],
        'b': record["b"]
    }


def restore_bandit_from_state(bandit: GraphWarmStartedFGTS, state: Dict[str, Any]) -> None:
    """
    Restore bandit from loaded state.
    
    Args:
        bandit: GraphWarmStartedFGTS instance to restore
        state: Dictionary with bandit state
    """
    bandit.num_arms = state['num_arms']
    bandit.lambda_fg = state.get('lambda_fg', 0.01)
    bandit.b = state.get('b', 1000.0)
    
    # Restore alpha/beta values
    alpha_list = state['alpha']
    beta_list = state['beta']
    
    for i in range(bandit.num_arms):
        bandit.alpha[i] = alpha_list[i]
        bandit.beta[i] = beta_list[i]

