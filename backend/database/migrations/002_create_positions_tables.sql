-- Migration: Create positions, conversations, and position_distribution tables
-- Phase 3: Position Creation

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    team_id VARCHAR,
    description TEXT,
    requirements TEXT[],
    must_haves TEXT[],
    nice_to_haves TEXT[],
    experience_level VARCHAR,  -- Junior, Mid, Senior, Staff
    responsibilities TEXT[],
    tech_stack TEXT[],
    domains TEXT[],
    team_context TEXT,
    reporting_to VARCHAR,
    collaboration TEXT[],
    priority VARCHAR,  -- high, medium, low
    status VARCHAR DEFAULT 'open',  -- open, in-progress, on-hold, filled, cancelled
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
);

-- Conversations table (for Grok position creation chat)
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL,  -- 'position_creation', 'team_creation', etc.
    session_id VARCHAR NOT NULL UNIQUE,
    messages JSONB,  -- Store conversation history as JSON
    current_data JSONB,  -- Store extracted data so far
    is_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Position distribution table (for distribution flags)
CREATE TABLE IF NOT EXISTS position_distribution (
    id VARCHAR PRIMARY KEY,
    position_id VARCHAR NOT NULL UNIQUE,
    company_id VARCHAR NOT NULL,
    post_to_x BOOLEAN DEFAULT FALSE,
    available_to_grok BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_positions_company_id ON positions(company_id);
CREATE INDEX IF NOT EXISTS idx_positions_team_id ON positions(team_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_title ON positions(title);
CREATE INDEX IF NOT EXISTS idx_conversations_company_id ON conversations(company_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(type);
CREATE INDEX IF NOT EXISTS idx_position_distribution_position_id ON position_distribution(position_id);
CREATE INDEX IF NOT EXISTS idx_position_distribution_company_id ON position_distribution(company_id);

-- Comments
COMMENT ON TABLE positions IS 'Job positions within companies (multi-tenant)';
COMMENT ON COLUMN positions.company_id IS 'Company ID for multi-tenancy (hardcoded to "xai" for demo)';
COMMENT ON COLUMN positions.team_id IS 'Team that is hiring for this position (foreign key to teams)';
COMMENT ON COLUMN positions.status IS 'Position status: open, in-progress, on-hold, filled, cancelled';
COMMENT ON COLUMN positions.priority IS 'Hiring priority: high, medium, low';
COMMENT ON TABLE conversations IS 'Grok conversation state for position/team creation';
COMMENT ON COLUMN conversations.type IS 'Type of conversation: position_creation, team_creation, etc.';
COMMENT ON COLUMN conversations.messages IS 'Conversation history stored as JSONB array';
COMMENT ON COLUMN conversations.current_data IS 'Extracted data so far, stored as JSONB';
COMMENT ON TABLE position_distribution IS 'Distribution flags for positions (post to X, available to Grok)';

