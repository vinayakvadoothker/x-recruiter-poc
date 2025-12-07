-- Migration: Create teams table
-- Phase 1: Teams Management

CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    department VARCHAR,
    needs TEXT[],
    expertise TEXT[],
    stack TEXT[],
    domains TEXT[],
    culture TEXT,
    work_style TEXT,
    hiring_priorities TEXT[],
    member_count INTEGER DEFAULT 0,
    member_ids TEXT[],
    open_positions TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_teams_company_id ON teams(company_id);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);

-- Comments
COMMENT ON TABLE teams IS 'Teams within companies (multi-tenant)';
COMMENT ON COLUMN teams.company_id IS 'Company ID for multi-tenancy (hardcoded to "xai" for demo)';
COMMENT ON COLUMN teams.needs IS 'Array of team needs/skills gaps';
COMMENT ON COLUMN teams.expertise IS 'Array of team expertise areas';
COMMENT ON COLUMN teams.stack IS 'Array of technologies used by team';
COMMENT ON COLUMN teams.domains IS 'Array of domain expertise (e.g., LLM Inference, GPU Computing)';
COMMENT ON COLUMN teams.member_ids IS 'Array of interviewer IDs who are members of this team';
COMMENT ON COLUMN teams.open_positions IS 'Array of position IDs that are open for this team';

