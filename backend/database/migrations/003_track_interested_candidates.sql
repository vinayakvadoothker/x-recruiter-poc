-- Migration: Track interested candidates from X posts
-- Phase 3.5: Interested Candidates Tracking

-- Position X Posts table (stores X post IDs for positions)
CREATE TABLE IF NOT EXISTS position_x_posts (
    id VARCHAR PRIMARY KEY,
    position_id VARCHAR NOT NULL,
    company_id VARCHAR NOT NULL,
    x_post_id VARCHAR NOT NULL UNIQUE,  -- X API post/tweet ID
    post_text TEXT,
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- Interested Candidates table (tracks who commented "interested")
CREATE TABLE IF NOT EXISTS interested_candidates (
    id VARCHAR PRIMARY KEY,
    position_id VARCHAR NOT NULL,
    company_id VARCHAR NOT NULL,
    x_post_id VARCHAR NOT NULL,  -- The X post they replied to
    x_handle VARCHAR NOT NULL,  -- X username (unique identifier)
    x_user_id VARCHAR,  -- X user ID
    comment_text TEXT,  -- The actual comment/reply text
    comment_id VARCHAR,  -- X reply/tweet ID
    commented_at TIMESTAMP,  -- When they commented
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
    FOREIGN KEY (x_post_id) REFERENCES position_x_posts(x_post_id) ON DELETE CASCADE,
    UNIQUE(position_id, x_handle)  -- One row per candidate per position (regardless of which post they commented on)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_position_x_posts_position_id ON position_x_posts(position_id);
CREATE INDEX IF NOT EXISTS idx_position_x_posts_company_id ON position_x_posts(company_id);
CREATE INDEX IF NOT EXISTS idx_position_x_posts_x_post_id ON position_x_posts(x_post_id);
CREATE INDEX IF NOT EXISTS idx_interested_candidates_position_id ON interested_candidates(position_id);
CREATE INDEX IF NOT EXISTS idx_interested_candidates_company_id ON interested_candidates(company_id);
CREATE INDEX IF NOT EXISTS idx_interested_candidates_x_handle ON interested_candidates(x_handle);
CREATE INDEX IF NOT EXISTS idx_interested_candidates_x_post_id ON interested_candidates(x_post_id);

-- Comments
COMMENT ON TABLE position_x_posts IS 'X posts created for positions';
COMMENT ON COLUMN position_x_posts.x_post_id IS 'X API tweet/post ID';
COMMENT ON TABLE interested_candidates IS 'Candidates who commented "interested" on position X posts';
COMMENT ON COLUMN interested_candidates.x_handle IS 'X username (unique identifier for candidate)';

