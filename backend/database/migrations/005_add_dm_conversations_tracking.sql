-- Migration: Add DM conversations tracking table
-- Tracks DM conversations for pipeline candidates

CREATE TABLE IF NOT EXISTS dm_conversations (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    candidate_id VARCHAR NOT NULL,
    position_id VARCHAR NOT NULL,
    x_conversation_id VARCHAR NOT NULL UNIQUE,  -- X API conversation ID
    x_participant_id VARCHAR NOT NULL,  -- X user ID of candidate
    x_participant_handle VARCHAR,  -- X handle of candidate
    last_message_id VARCHAR,  -- Last message ID we've processed
    last_polled_at TIMESTAMP,  -- Last time we polled for new messages
    status VARCHAR DEFAULT 'active',  -- active, completed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
    
    UNIQUE(candidate_id, position_id)  -- One conversation per candidate-position pair
);

CREATE INDEX IF NOT EXISTS idx_dm_conversations_candidate ON dm_conversations(candidate_id);
CREATE INDEX IF NOT EXISTS idx_dm_conversations_position ON dm_conversations(position_id);
CREATE INDEX IF NOT EXISTS idx_dm_conversations_company ON dm_conversations(company_id);
CREATE INDEX IF NOT EXISTS idx_dm_conversations_status ON dm_conversations(status);
CREATE INDEX IF NOT EXISTS idx_dm_conversations_last_polled ON dm_conversations(last_polled_at);

COMMENT ON TABLE dm_conversations IS 'Tracks DM conversations for pipeline candidates';
COMMENT ON COLUMN dm_conversations.x_conversation_id IS 'X API conversation ID';
COMMENT ON COLUMN dm_conversations.last_message_id IS 'Last message ID we have processed (to avoid duplicates)';

