-- Migration: Create candidates table and pipeline_stages table
-- Phase 4: Candidate Storage & CRUD
-- Phase 5: Pipeline Tracking

-- Candidates table (full candidate profiles)
CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR PRIMARY KEY,  -- Format: "x_{handle}" or "github_{handle}" etc.
    company_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    phone_number VARCHAR,  -- Format: +1234567890
    email VARCHAR,
    
    -- Platform Identifiers
    github_handle VARCHAR,
    github_user_id VARCHAR,
    x_handle VARCHAR,
    x_user_id VARCHAR,
    linkedin_url VARCHAR,
    arxiv_author_id VARCHAR,
    orcid_id VARCHAR,
    
    -- Core Profile Data
    skills JSONB DEFAULT '[]',  -- List of technical skills
    domains JSONB DEFAULT '[]',  -- Domain expertise (LLM Inference, GPU Computing, etc.)
    experience_years INTEGER,
    expertise_level VARCHAR,  -- Junior, Mid, Senior, Staff
    experience JSONB DEFAULT '[]',  -- Work experience descriptions
    education JSONB DEFAULT '[]',  -- Education background
    projects JSONB DEFAULT '[]',  -- Project information
    
    -- Resume Data (from DM)
    resume_text TEXT,
    resume_url VARCHAR,
    resume_parsed JSONB,  -- Parsed resume data
    
    -- DM-Gathered Data
    dm_responses JSONB,  -- DM conversation history
    dm_requested_fields JSONB,  -- Fields we requested
    dm_provided_fields JSONB,  -- Fields they provided
    dm_last_contact TIMESTAMP,
    dm_response_rate FLOAT,  -- 0.0-1.0
    
    -- Screening Data
    screening_score FLOAT,  -- 0.0-1.0 (from DM screening)
    screening_responses JSONB,  -- Screening question responses
    
    -- Source and Metadata
    source VARCHAR,  -- "outbound" or "inbound"
    data_completeness FLOAT DEFAULT 0.0,  -- 0.0-1.0
    last_gathered_from JSONB,  -- ["x", "github", "arxiv"]
    gathering_timestamp JSONB,  -- {"x": "2025-12-06", "github": "2025-12-05"}
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT candidates_company_id_check CHECK (company_id IS NOT NULL)
);

-- Pipeline Stages table (tracks candidate progress through positions)
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    candidate_id VARCHAR NOT NULL,  -- References candidate
    position_id VARCHAR NOT NULL,   -- References position
    stage VARCHAR NOT NULL,           -- Current stage name
    entered_at TIMESTAMP NOT NULL DEFAULT NOW(),  -- When entered this stage
    exited_at TIMESTAMP,              -- When moved to next stage (NULL if current)
    metadata JSONB DEFAULT '{}',      -- Stage-specific data (DM responses, scores, etc.)
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
    
    -- Unique constraint: one active stage per candidate-position pair
    CONSTRAINT unique_active_stage UNIQUE (candidate_id, position_id, stage) 
        DEFERRABLE INITIALLY DEFERRED
);

-- Partial unique index for active stages only
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_active_stage 
    ON pipeline_stages (candidate_id, position_id) 
    WHERE exited_at IS NULL;

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_candidates_company_id ON candidates(company_id);
CREATE INDEX IF NOT EXISTS idx_candidates_x_handle ON candidates(x_handle);
CREATE INDEX IF NOT EXISTS idx_candidates_x_user_id ON candidates(x_user_id);
CREATE INDEX IF NOT EXISTS idx_candidates_github_handle ON candidates(github_handle);
CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name);

CREATE INDEX IF NOT EXISTS idx_pipeline_candidate ON pipeline_stages(candidate_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_position ON pipeline_stages(position_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON pipeline_stages(stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_company ON pipeline_stages(company_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_active ON pipeline_stages(candidate_id, position_id, exited_at);

-- Comments
COMMENT ON TABLE candidates IS 'Full candidate profiles with 500+ datapoints';
COMMENT ON TABLE pipeline_stages IS 'Tracks candidate progress through positions (many-to-many)';
COMMENT ON COLUMN pipeline_stages.stage IS 'Stage name: dm_screening, phone_screen_scheduled, etc.';
COMMENT ON COLUMN pipeline_stages.exited_at IS 'NULL if current stage, timestamp if moved to next stage';

