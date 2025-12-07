"""
FastAPI application entry point for Grok Recruiter API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.orchestration.dm_polling_service import start_dm_polling, stop_dm_polling

app = FastAPI(
    title="Grok Recruiter API",
    description="API for AI-powered candidate sourcing and recruitment",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["api"])


async def load_data_folder_datasets():
    """Load datasets from data/ folder JSON files into knowledge graph AND PostgreSQL."""
    import json
    import logging
    from pathlib import Path
    from backend.database.knowledge_graph import KnowledgeGraph
    from backend.database.postgres_client import PostgresClient
    from backend.orchestration.company_context import get_company_context
    
    logger = logging.getLogger(__name__)
    data_dir = Path("data")
    
    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist. Skipping dataset preload.")
        return
    
    try:
        kg = KnowledgeGraph()
        postgres = PostgresClient()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        loaded_counts = {"candidates": 0, "teams": 0, "interviewers": 0, "positions": 0}
        
        # Load candidates (into both Knowledge Graph and PostgreSQL)
        candidates_file = data_dir / "candidates.json"
        if candidates_file.exists():
            logger.info(f"Loading candidates from {candidates_file}...")
            with open(candidates_file, 'r') as f:
                candidates = json.load(f)
                for candidate in candidates:
                    try:
                        candidate_id = candidate.get('id')
                        
                        # Check if candidate already exists in PostgreSQL first
                        existing = postgres.execute_one(
                            "SELECT id FROM candidates WHERE id = %s AND company_id = %s",
                            (candidate_id, company_id)
                        )
                        if existing:
                            logger.debug(f"Skipping candidate {candidate_id} - already exists in database (PostgreSQL + Weaviate)")
                            continue
                        
                        # Add to knowledge graph (Weaviate) - only if not in PostgreSQL
                        try:
                            kg.add_candidate(candidate)
                        except Exception as kg_error:
                            logger.warning(f"Error adding candidate {candidate_id} to Weaviate: {kg_error}")
                            # Continue to PostgreSQL insert even if Weaviate fails
                        
                        # Add to PostgreSQL
                        import json as json_module
                        
                        # Convert lists/dicts to JSONB-compatible format (JSON strings)
                        skills = json_module.dumps(candidate.get("skills", []))
                        domains = json_module.dumps(candidate.get("domains", []))
                        experience = json_module.dumps(candidate.get("experience", []))
                        education = json_module.dumps(candidate.get("education", []))
                        projects = json_module.dumps(candidate.get("projects", []))
                        resume_parsed = json_module.dumps(candidate.get("resume_parsed")) if candidate.get("resume_parsed") else None
                        last_gathered_from = json_module.dumps(candidate.get("last_gathered_from", [])) if candidate.get("last_gathered_from") else None
                        gathering_timestamp = json_module.dumps(candidate.get("gathering_timestamp")) if candidate.get("gathering_timestamp") else None
                        
                        postgres.execute_update(
                            """
                            INSERT INTO candidates (
                                id, company_id, name, phone_number, email,
                                github_handle, github_user_id, x_handle, x_user_id,
                                linkedin_url, arxiv_author_id, orcid_id,
                                skills, domains, experience_years, expertise_level,
                                experience, education, projects,
                                resume_text, resume_url, resume_parsed,
                                source, data_completeness, last_gathered_from, gathering_timestamp,
                                repos, papers, github_stats, arxiv_stats
                            ) VALUES (
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s,
                                %s::jsonb, %s::jsonb, %s, %s,
                                %s::jsonb, %s::jsonb, %s::jsonb,
                                %s, %s, %s::jsonb,
                                %s, %s, %s::jsonb, %s::jsonb,
                                %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb
                            )
                            """,
                            (
                                candidate_id, company_id,
                                candidate.get("name"),
                                candidate.get("phone_number"),
                                candidate.get("email"),
                                candidate.get("github_handle"),
                                candidate.get("github_user_id"),
                                candidate.get("x_handle"),
                                candidate.get("x_user_id"),
                                candidate.get("linkedin_url"),
                                candidate.get("arxiv_author_id"),
                                candidate.get("orcid_id"),
                                skills, domains,
                                candidate.get("experience_years"),
                                candidate.get("expertise_level"),
                                experience, education, projects,
                                candidate.get("resume_text"),
                                candidate.get("resume_url"),
                                resume_parsed,
                                candidate.get("source", "outbound"),
                                candidate.get("data_completeness", 0.0),
                                last_gathered_from,
                                gathering_timestamp,
                                json_module.dumps(candidate.get("repos", [])),
                                json_module.dumps(candidate.get("papers", [])),
                                json_module.dumps(candidate.get("github_stats")) if candidate.get("github_stats") else None,
                                json_module.dumps(candidate.get("arxiv_stats")) if candidate.get("arxiv_stats") else None
                            )
                        )
                        
                        loaded_counts["candidates"] += 1
                    except Exception as e:
                        logger.warning(f"Error loading candidate {candidate.get('id', 'unknown')}: {e}")
                logger.info(f"Loaded {loaded_counts['candidates']} candidates (KG + PostgreSQL)")
        
        # Load teams (into both Knowledge Graph and PostgreSQL)
        teams_file = data_dir / "teams.json"
        if teams_file.exists():
            logger.info(f"Loading teams from {teams_file}...")
            with open(teams_file, 'r') as f:
                teams = json.load(f)
                for team in teams:
                    try:
                        team_id = team.get('id')
                        
                        # Check if team already exists in PostgreSQL first
                        existing = postgres.execute_one(
                            "SELECT id FROM teams WHERE id = %s AND company_id = %s",
                            (team_id, company_id)
                        )
                        if existing:
                            logger.debug(f"Skipping team {team_id} - already exists in database (PostgreSQL + Weaviate)")
                            continue
                        
                        # Add to knowledge graph (Weaviate) - only if not in PostgreSQL
                        try:
                            kg.add_team(team)
                        except Exception as kg_error:
                            logger.warning(f"Error adding team {team_id} to Weaviate: {kg_error}")
                            # Continue to PostgreSQL insert even if Weaviate fails
                        
                        postgres.execute_update(
                            """
                            INSERT INTO teams (
                                id, company_id, name, department,
                                needs, expertise, stack, domains,
                                culture, work_style, hiring_priorities,
                                member_count, member_ids, open_positions
                            ) VALUES (
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s
                            )
                            """,
                            (
                                team_id, company_id,
                                team.get("name"),
                                team.get("department"),
                                team.get("needs", []),
                                team.get("expertise", []),
                                team.get("stack", []),
                                team.get("domains", []),
                                team.get("culture"),
                                team.get("work_style"),
                                team.get("hiring_priorities", []),
                                team.get("member_count", 0),
                                team.get("member_ids", []),
                                team.get("open_positions", [])
                            )
                        )
                        
                        loaded_counts["teams"] += 1
                    except Exception as e:
                        logger.warning(f"Error loading team {team.get('id', 'unknown')}: {e}")
                logger.info(f"Loaded {loaded_counts['teams']} teams (KG + PostgreSQL)")
        
        # Load interviewers (into both Knowledge Graph and PostgreSQL)
        interviewers_file = data_dir / "interviewers.json"
        if interviewers_file.exists():
            logger.info(f"Loading interviewers from {interviewers_file}...")
            with open(interviewers_file, 'r') as f:
                interviewers = json.load(f)
                for interviewer in interviewers:
                    try:
                        interviewer_id = interviewer.get('id')
                        
                        # Check if interviewer already exists in PostgreSQL first
                        existing = postgres.execute_one(
                            "SELECT id FROM interviewers WHERE id = %s AND company_id = %s",
                            (interviewer_id, company_id)
                        )
                        if existing:
                            logger.debug(f"Skipping interviewer {interviewer_id} - already exists in database (PostgreSQL + Weaviate)")
                            continue
                        
                        # Add to knowledge graph (Weaviate) - only if not in PostgreSQL
                        try:
                            kg.add_interviewer(interviewer)
                        except Exception as kg_error:
                            logger.warning(f"Error adding interviewer {interviewer_id} to Weaviate: {kg_error}")
                            # Continue to PostgreSQL insert even if Weaviate fails
                        
                        postgres.execute_update(
                            """
                            INSERT INTO interviewers (
                                id, company_id, team_id, name, phone_number, email,
                                expertise, expertise_level, specializations, interview_style,
                                evaluation_focus, question_style, preferred_interview_types,
                                total_interviews, successful_hires, success_rate
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s
                            )
                            """,
                            (
                                interviewer_id, company_id,
                                interviewer.get("team_id"),
                                interviewer.get("name"),
                                interviewer.get("phone_number"),
                                interviewer.get("email"),
                                interviewer.get("expertise", []),
                                interviewer.get("expertise_level"),
                                interviewer.get("specializations", []),
                                interviewer.get("interview_style"),
                                interviewer.get("evaluation_focus", []),
                                interviewer.get("question_style"),
                                interviewer.get("preferred_interview_types", []),
                                interviewer.get("total_interviews", 0),
                                interviewer.get("successful_hires", 0),
                                interviewer.get("success_rate", 0.0)
                            )
                        )
                        
                        loaded_counts["interviewers"] += 1
                    except Exception as e:
                        logger.warning(f"Error loading interviewer {interviewer.get('id', 'unknown')}: {e}")
                logger.info(f"Loaded {loaded_counts['interviewers']} interviewers (KG + PostgreSQL)")
        
        # Load positions (into Knowledge Graph - positions are already in PostgreSQL via API)
        positions_file = data_dir / "positions.json"
        if positions_file.exists():
            logger.info(f"Loading positions from {positions_file}...")
            with open(positions_file, 'r') as f:
                positions = json.load(f)
                for position in positions:
                    try:
                        kg.add_position(position)
                        loaded_counts["positions"] += 1
                    except Exception as e:
                        logger.warning(f"Error loading position {position.get('id', 'unknown')}: {e}")
                logger.info(f"Loaded {loaded_counts['positions']} positions (KG)")
        
        total = sum(loaded_counts.values())
        logger.info(
            f"✅ Dataset preload complete: {total} total profiles loaded "
            f"(candidates: {loaded_counts['candidates']} to KG+PostgreSQL, "
            f"teams: {loaded_counts['teams']} to KG+PostgreSQL, "
            f"interviewers: {loaded_counts['interviewers']} to KG+PostgreSQL, "
            f"positions: {loaded_counts['positions']} to KG)"
        )
        
    except Exception as e:
        logger.error(f"Error loading datasets from data folder: {e}", exc_info=True)


@app.on_event("startup")
async def startup_event():
    """Start background services on application startup."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Preload datasets from data/ folder
        await load_data_folder_datasets()
        
        # Start DM polling service
        await start_dm_polling()
        logger.info("Background services started")
    except Exception as e:
        logger.error(f"Error starting background services: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on application shutdown."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        await stop_dm_polling()
        logger.info("Background services stopped")
    except Exception as e:
        logger.error(f"Error stopping background services: {e}")


@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        API status
    """
    return {"status": "ok", "message": "Grok Recruiter API"}

