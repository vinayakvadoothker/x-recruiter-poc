-- Migration: Add fields for storing GitHub repos and arXiv papers
-- These fields store the actual data gathered from external sources

ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS repos JSONB DEFAULT '[]',  -- GitHub repositories
ADD COLUMN IF NOT EXISTS papers JSONB DEFAULT '[]',  -- arXiv papers
ADD COLUMN IF NOT EXISTS github_stats JSONB,  -- GitHub statistics (stars, commits, etc.)
ADD COLUMN IF NOT EXISTS arxiv_stats JSONB;  -- arXiv statistics (paper count, citations, etc.)

-- Indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_candidates_repos ON candidates USING GIN (repos);
CREATE INDEX IF NOT EXISTS idx_candidates_papers ON candidates USING GIN (papers);

COMMENT ON COLUMN candidates.repos IS 'GitHub repositories data (from gather_from_github)';
COMMENT ON COLUMN candidates.papers IS 'arXiv papers data (from gather_from_arxiv)';
COMMENT ON COLUMN candidates.github_stats IS 'GitHub statistics (total stars, repos, etc.)';
COMMENT ON COLUMN candidates.arxiv_stats IS 'arXiv statistics (paper count, citations, h-index, etc.)';

