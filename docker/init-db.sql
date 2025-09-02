-- PostgreSQL initialization script for MVS Designer
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to the mvs_user
GRANT ALL PRIVILEGES ON DATABASE mvs_designer TO mvs_user;

-- Set timezone
SET timezone = 'UTC';