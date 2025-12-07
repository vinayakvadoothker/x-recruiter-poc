-- Migration: Create interviewers table
-- Phase 2: Interviewers Management

CREATE TABLE IF NOT EXISTS interviewers (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    team_id VARCHAR,  -- Optional: interviewers can exist without a team
    name VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    expertise TEXT[],
    expertise_level VARCHAR,
    specializations TEXT[],
    interview_style TEXT,
    evaluation_focus TEXT[],
    question_style VARCHAR,
    preferred_interview_types TEXT[],
    total_interviews INTEGER DEFAULT 0,
    successful_hires INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_interviewers_company_id ON interviewers(company_id);
CREATE INDEX IF NOT EXISTS idx_interviewers_team_id ON interviewers(team_id);
CREATE INDEX IF NOT EXISTS idx_interviewers_name ON interviewers(name);
CREATE INDEX IF NOT EXISTS idx_interviewers_email ON interviewers(email);

-- Comments
COMMENT ON TABLE interviewers IS 'Interviewers within companies (multi-tenant)';
COMMENT ON COLUMN interviewers.company_id IS 'Company ID for multi-tenancy (hardcoded to "xai" for demo)';
COMMENT ON COLUMN interviewers.team_id IS 'Optional team assignment - interviewers can exist without a team';
COMMENT ON COLUMN interviewers.expertise IS 'Array of technical expertise areas';
COMMENT ON COLUMN interviewers.specializations IS 'Array of specialized areas';
COMMENT ON COLUMN interviewers.evaluation_focus IS 'Array of what they focus on during interviews';
COMMENT ON COLUMN interviewers.preferred_interview_types IS 'Array of interview types they prefer';

