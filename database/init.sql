-- AlumDash PostgreSQL Database Initialization
-- This script creates the database schema for the alumni tracking system

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE degree_program AS ENUM (
    'Film Production',
    'Screenwriting', 
    'Animation',
    'Documentary',
    'Television'
);

CREATE TYPE achievement_type AS ENUM (
    'Award',
    'Production Credit',
    'Festival Selection',
    'Review/Reception',
    'Industry Recognition'
);

CREATE TYPE project_type AS ENUM (
    'Feature Film',
    'Short Film',
    'TV Series',
    'TV Movie',
    'Web Series',
    'Documentary',
    'Animation'
);

-- Alumni table
CREATE TABLE alumni (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    graduation_year INTEGER NOT NULL CHECK (graduation_year >= 1970 AND graduation_year <= 2030),
    degree_program degree_program NOT NULL,
    email VARCHAR(255),
    linkedin_url TEXT,
    imdb_url TEXT,
    website TEXT,
    public_profile BOOLEAN DEFAULT TRUE,
    show_email BOOLEAN DEFAULT FALSE,
    allow_notifications BOOLEAN DEFAULT TRUE,
    show_achievements BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_email CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_linkedin CHECK (linkedin_url IS NULL OR linkedin_url ~* '^https?://'),
    CONSTRAINT valid_imdb CHECK (imdb_url IS NULL OR imdb_url ~* '^https?://'),
    CONSTRAINT valid_website CHECK (website IS NULL OR website ~* '^https?://')
);

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    release_date DATE,
    type project_type NOT NULL,
    imdb_id VARCHAR(20),
    tmdb_id VARCHAR(20),
    poster_url TEXT,
    synopsis TEXT,
    runtime_minutes INTEGER CHECK (runtime_minutes > 0),
    budget NUMERIC(15,2),
    box_office NUMERIC(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_imdb_id CHECK (imdb_id IS NULL OR imdb_id ~* '^tt[0-9]+$')
);

-- Project streaming platforms (many-to-many)
CREATE TABLE project_streaming_platforms (
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    platform_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (project_id, platform_name)
);

-- Achievements table
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    alumni_id INTEGER NOT NULL REFERENCES alumni(id) ON DELETE CASCADE,
    type achievement_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    verified BOOLEAN DEFAULT FALSE,
    source VARCHAR(200) NOT NULL,
    source_url TEXT,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for performance
    INDEX idx_achievements_alumni_id (alumni_id),
    INDEX idx_achievements_date (date),
    INDEX idx_achievements_type (type)
);

-- Alumni-Project relationships (many-to-many)
CREATE TABLE alumni_projects (
    id SERIAL PRIMARY KEY,
    alumni_id INTEGER NOT NULL REFERENCES alumni(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL,
    character_name VARCHAR(100),
    billing_order INTEGER CHECK (billing_order > 0),
    verified_status BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique alumni-project-role combinations
    UNIQUE(alumni_id, project_id, role)
);

-- Data sources table for tracking external APIs and scraping sources
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('API', 'RSS', 'Web Scraping')),
    url TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER DEFAULT 60,
    api_key_encrypted TEXT, -- Store encrypted API keys
    last_checked TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    success_rate NUMERIC(3,2) DEFAULT 1.0 CHECK (success_rate >= 0 AND success_rate <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Import logs for tracking CSV uploads and data imports
CREATE TABLE import_logs (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    import_type VARCHAR(50) NOT NULL, -- 'alumni_csv', 'achievements_csv', etc.
    status VARCHAR(20) NOT NULL DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    total_records INTEGER,
    successful_records INTEGER,
    failed_records INTEGER,
    error_details JSONB,
    imported_by VARCHAR(100), -- Could be user ID in future
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic updated_at timestamps
CREATE TRIGGER update_alumni_updated_at BEFORE UPDATE ON alumni
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO alumni (name, graduation_year, degree_program, email, linkedin_url, imdb_url) VALUES
('Sarah Chen', 2018, 'Film Production', 's.chen@example.com', 'https://linkedin.com/in/sarahchen', 'https://www.imdb.com/name/nm1234567'),
('James Mitchell', 2020, 'Documentary', 'j.mitchell@example.com', NULL, NULL),
('Emma Rodriguez', 2019, 'Animation', 'e.rodriguez@example.com', 'https://linkedin.com/in/emmarodriguez', NULL),
('Michael O''Brien', 2017, 'Screenwriting', 'm.obrien@example.com', NULL, 'https://www.imdb.com/name/nm2345678'),
('Priya Sharma', 2021, 'Television', 'p.sharma@example.com', NULL, NULL);

INSERT INTO projects (title, release_date, type, imdb_id, tmdb_id, runtime_minutes, synopsis) VALUES
('Silent Echoes', '2024-06-15', 'Short Film', 'tt1234567', '123456', 15, 'A haunting exploration of memory and loss in modern Melbourne.'),
('Urban Voices', '2024-03-10', 'Documentary', NULL, NULL, 90, 'Documentary exploring the diverse communities of Australian cities.'),
('Dream Weavers', '2023-09-01', 'TV Series', NULL, NULL, NULL, 'An animated series about children who can enter each other''s dreams.'),
('The Last Station', '2023-11-20', 'Feature Film', 'tt3456789', NULL, 120, 'A drama about the final days of a remote railway station.');

INSERT INTO project_streaming_platforms (project_id, platform_name) VALUES
(2, 'Netflix'), (2, 'Stan'),
(3, 'Netflix');

INSERT INTO achievements (alumni_id, type, title, date, description, confidence_score, verified, source, project_id) VALUES
(1, 'Award', 'AACTA Award - Best Short Film', '2024-12-01', 'Won AACTA Award for Best Short Film for ''Silent Echoes''', 0.95, TRUE, 'AACTA Official Website', 1),
(2, 'Festival Selection', 'Sundance Film Festival - Official Selection', '2024-01-20', 'Documentary ''Urban Voices'' selected for Sundance 2024', 0.90, TRUE, 'Sundance Institute', 2),
(3, 'Production Credit', 'Lead Animator - ''Dream Weavers''', '2023-06-15', 'Lead animator on Netflix animated series', 0.88, FALSE, 'TMDb API', 3),
(1, 'Festival Selection', 'Melbourne International Film Festival - Premiere', '2024-08-10', 'World premiere of ''Silent Echoes'' at MIFF', 0.92, TRUE, 'MIFF Official Program', 1),
(4, 'Production Credit', 'Screenwriter - ''The Last Station''', '2023-11-20', 'Wrote screenplay for feature film', 0.85, TRUE, 'Screen Australia', 4);

INSERT INTO alumni_projects (alumni_id, project_id, role, verified_status) VALUES
(1, 1, 'Director', TRUE),
(2, 2, 'Director/Producer', TRUE),
(3, 3, 'Lead Animator', FALSE),
(4, 4, 'Screenwriter', TRUE);

INSERT INTO data_sources (name, type, url, active, rate_limit) VALUES
('TMDb API', 'API', 'https://api.themoviedb.org/3', TRUE, 40),
('OMDb API', 'API', 'http://www.omdbapi.com', TRUE, 1000),
('Screen Australia', 'RSS', 'https://www.screenaustralia.gov.au/rss', TRUE, 10),
('IF Magazine', 'Web Scraping', 'https://if.com.au', TRUE, 6),
('AACTA Awards', 'Web Scraping', 'https://www.aacta.org', FALSE, 5);

-- Create indexes for performance
CREATE INDEX idx_alumni_graduation_year ON alumni(graduation_year);
CREATE INDEX idx_alumni_degree_program ON alumni(degree_program);
CREATE INDEX idx_projects_release_date ON projects(release_date);
CREATE INDEX idx_projects_type ON projects(type);

COMMIT;
