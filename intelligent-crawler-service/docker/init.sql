-- Initialize crawler database schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create tables
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    urls TEXT[] NOT NULL,
    config JSONB NOT NULL,
    collection_name VARCHAR(255) NOT NULL DEFAULT 'default',
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    progress FLOAT DEFAULT 0,
    
    -- Results
    urls_crawled INTEGER DEFAULT 0,
    pages_discovered INTEGER DEFAULT 0,
    pages_processed INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Callback
    callback_url TEXT,
    
    -- Results storage
    results_location TEXT,
    
    -- Indexes
    CONSTRAINT valid_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_created_at ON crawl_jobs(created_at);
CREATE INDEX idx_crawl_jobs_collection ON crawl_jobs(collection_name);

-- Crawled pages
CREATE TABLE IF NOT EXISTS crawled_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) REFERENCES crawl_jobs(job_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    url_hash VARCHAR(64) NOT NULL,
    
    -- Content
    title TEXT,
    content_hash VARCHAR(64),
    content_length INTEGER,
    
    -- Metadata
    depth INTEGER NOT NULL,
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    
    -- Status
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_type VARCHAR(100),
    
    -- AI Evaluation
    quality_score FLOAT,
    relevance_score FLOAT,
    content_type VARCHAR(50),
    
    -- Unique constraint
    UNIQUE(job_id, url_hash)
);

CREATE INDEX idx_crawled_pages_job_id ON crawled_pages(job_id);
CREATE INDEX idx_crawled_pages_url_hash ON crawled_pages(url_hash);
CREATE INDEX idx_crawled_pages_crawled_at ON crawled_pages(crawled_at);
CREATE INDEX idx_crawled_pages_quality_score ON crawled_pages(quality_score);

-- URL monitoring for incremental updates
CREATE TABLE IF NOT EXISTS monitored_urls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT UNIQUE NOT NULL,
    url_hash VARCHAR(64) UNIQUE NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    
    -- Monitoring config
    check_frequency INTERVAL DEFAULT '1 day',
    last_checked_at TIMESTAMP WITH TIME ZONE,
    next_check_at TIMESTAMP WITH TIME ZONE,
    
    -- Content tracking
    last_content_hash VARCHAR(64),
    last_modified_header TEXT,
    etag_header TEXT,
    
    -- Change tracking
    change_count INTEGER DEFAULT 0,
    last_change_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    active BOOLEAN DEFAULT true,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitored_urls_next_check ON monitored_urls(next_check_at) WHERE active = true;
CREATE INDEX idx_monitored_urls_collection ON monitored_urls(collection_name);

-- Vector collections metadata
CREATE TABLE IF NOT EXISTS vector_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    
    -- Configuration
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    chunk_size INTEGER DEFAULT 1000,
    chunk_overlap INTEGER DEFAULT 200,
    
    -- Statistics
    document_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    config JSONB DEFAULT '{}'::jsonb
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Request info
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    user_id VARCHAR(255),
    ip_address INET,
    
    -- Usage metrics
    tokens_used INTEGER DEFAULT 0,
    embeddings_created INTEGER DEFAULT 0,
    pages_crawled INTEGER DEFAULT 0,
    
    -- Response
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT
);

CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);

-- Create functions for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at trigger to monitored_urls
CREATE TRIGGER update_monitored_urls_updated_at BEFORE UPDATE
    ON monitored_urls FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initial data
INSERT INTO vector_collections (name, description) 
VALUES ('default', 'Default collection for general content')
ON CONFLICT (name) DO NOTHING;