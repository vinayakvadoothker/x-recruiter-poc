"""
Demo dashboard for Grok Recruiter.

Displays candidate list, graph similarities, bandit state, and learning metrics.
"""

import streamlit as st
import logging
from typing import List, Dict, Optional

from backend.orchestration.pipeline import RecruitingPipeline
from backend.orchestration.recruiter_agent import RecruiterAgent
from backend.simulator.x_dm_simulator import XDMSimulator

logger = logging.getLogger(__name__)

# Initialize components
pipeline = RecruitingPipeline()
simulator = XDMSimulator()
recruiter_agent = RecruiterAgent(pipeline=pipeline, simulator=simulator)


def display_candidate_list(candidates: List[Dict]) -> None:
    """
    Display candidate list with scores.
    
    Args:
        candidates: List of candidate dictionaries
    """
    st.header("Candidates")
    
    if not candidates:
        st.info("No candidates found. Submit a role request to source candidates.")
        return
    
    # Sort by similarity score
    sorted_candidates = sorted(
        candidates,
        key=lambda x: x.get('similarity_score', 0.0),
        reverse=True
    )
    
    for i, candidate in enumerate(sorted_candidates[:20], 1):
        with st.expander(f"{i}. @{candidate.get('github_handle', 'Unknown')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Similarity Score", f"{candidate.get('similarity_score', 0.0):.1%}")
                if candidate.get('bandit_score'):
                    st.metric("Bandit Score", f"{candidate.get('bandit_score', 0.0):.2f}")
            
            with col2:
                profile = candidate.get('profile_data', {})
                if profile.get('avatar_url'):
                    st.image(profile.get('avatar_url'), width=100)
            
            st.write("**Skills:**", ", ".join(candidate.get('skills', [])[:10]))
            st.write("**Experience:**", ", ".join(candidate.get('experience', [])[:3]))
            st.write("**Repos:**", len(candidate.get('repos', [])))


def display_bandit_state(role_id: Optional[str] = None) -> None:
    """
    Display bandit algorithm state.
    
    Args:
        role_id: Role identifier (optional)
    """
    st.header("Bandit Algorithm State")
    
    # TODO: Get actual bandit state from pipeline when Vin's code is ready
    st.info("Bandit state will be displayed here when algorithm is fully integrated.")
    
    # Mock display
    st.write("**Alpha values:** (Success counts per candidate)")
    st.write("**Beta values:** (Failure counts per candidate)")
    st.write("**Status:** Using mock implementation")


def display_learning_metrics() -> None:
    """
    Display basic learning metrics.
    """
    st.header("Learning Metrics")
    
    # Get chat history for interaction count
    chat_history = simulator.get_chat_history()
    interactions = len([msg for msg in chat_history if msg.get('role') == 'user'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Interactions", interactions)
    
    with col2:
        st.metric("Response Rate", "N/A")  # Will be calculated from feedback
    
    with col3:
        st.metric("Candidates Sourced", len(pipeline.candidate_cache))
    
    st.info("Detailed learning curves available in Metrics tab.")


def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="Grok Recruiter Dashboard",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Grok Recruiter Dashboard")
    st.markdown("AI-powered candidate sourcing and recruitment system")
    
    # Sidebar for role input
    with st.sidebar:
        st.header("Role Request")
        role_title = st.text_input("Job Title", placeholder="e.g., LLM Inference Engineer")
        role_description = st.text_area(
            "Role Description",
            placeholder="Describe the role, required skills, experience level, etc.",
            height=200
        )
        
        if st.button("Source Candidates", type="primary"):
            if role_description:
                with st.spinner("Sourcing candidates..."):
                    # Process role request
                    import asyncio
                    result = asyncio.run(
                        pipeline.process_role_request(role_description, role_title=role_title)
                    )
                    
                    if result.get('error'):
                        st.error(result.get('error'))
                    else:
                        st.success(f"Found {len(result.get('candidates', []))} candidates!")
                        st.session_state['current_role_id'] = result.get('role_id')
                        st.session_state['candidates'] = result.get('candidates', [])
            else:
                st.warning("Please enter a role description")
        
        st.divider()
        st.header("Chat History")
        chat_history = simulator.get_chat_history()
        if chat_history:
            for msg in chat_history[-5:]:  # Show last 5 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100]
                if role == 'user':
                    st.write(f"**You:** {content}...")
                else:
                    st.write(f"**@x_recruiting:** {content}...")
        else:
            st.info("No messages yet")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["Candidates", "Bandit State", "Metrics"])
    
    with tab1:
        candidates = st.session_state.get('candidates', [])
        display_candidate_list(candidates)
    
    with tab2:
        role_id = st.session_state.get('current_role_id')
        display_bandit_state(role_id)
    
    with tab3:
        display_learning_metrics()
        
        # Import metrics visualization
        try:
            from backend.demo.metrics import plot_learning_curves
            st.subheader("Learning Curves")
            st.info("Learning curves will be displayed here when metrics are collected.")
        except ImportError:
            st.info("Metrics module not yet available.")


if __name__ == "__main__":
    main()

