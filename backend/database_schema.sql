-- CliniMatch Database Schema for Supabase
-- This file contains the SQL commands to create the required tables and indexes

-- Create trials_cache table for caching clinical trial data
CREATE TABLE IF NOT EXISTS trials_cache (
    id SERIAL PRIMARY KEY,
    search_key VARCHAR(255) UNIQUE NOT NULL,
    trial_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_trials_cache_search_key ON trials_cache(search_key);
CREATE INDEX IF NOT EXISTS idx_trials_cache_expires_at ON trials_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_trials_cache_created_at ON trials_cache(created_at);

-- Create user_sessions table for optional analytics (as per design document)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    search_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for session lookups
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);

-- Enable Row Level Security (RLS) for better security
ALTER TABLE trials_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (since this is a public application)
-- Note: Drop existing policies first if they exist, then create new ones
DROP POLICY IF EXISTS "Allow public read access on trials_cache" ON trials_cache;
DROP POLICY IF EXISTS "Allow public insert access on trials_cache" ON trials_cache;
DROP POLICY IF EXISTS "Allow public update access on trials_cache" ON trials_cache;
DROP POLICY IF EXISTS "Allow public delete access on trials_cache" ON trials_cache;

CREATE POLICY "Allow public read access on trials_cache" ON trials_cache
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access on trials_cache" ON trials_cache
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update access on trials_cache" ON trials_cache
    FOR UPDATE USING (true);

CREATE POLICY "Allow public delete access on trials_cache" ON trials_cache
    FOR DELETE USING (true);

DROP POLICY IF EXISTS "Allow public read access on user_sessions" ON user_sessions;
DROP POLICY IF EXISTS "Allow public insert access on user_sessions" ON user_sessions;
DROP POLICY IF EXISTS "Allow public update access on user_sessions" ON user_sessions;
DROP POLICY IF EXISTS "Allow public delete access on user_sessions" ON user_sessions;

CREATE POLICY "Allow public read access on user_sessions" ON user_sessions
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access on user_sessions" ON user_sessions
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update access on user_sessions" ON user_sessions
    FOR UPDATE USING (true);

CREATE POLICY "Allow public delete access on user_sessions" ON user_sessions
    FOR DELETE USING (true);
