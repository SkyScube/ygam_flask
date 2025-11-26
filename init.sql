-- Ygam Database Initialization Script
-- This script is automatically executed when the MySQL container starts for the first time
-- Note: Tables are auto-created by Flask-SQLAlchemy (db.create_all())
-- This script is for additional configuration and initial data

-- Ensure UTF-8 support for international characters and emojis
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Set timezone to UTC
SET time_zone = '+00:00';

-- Optimize MySQL for messaging workload
SET GLOBAL max_connections = 200;
SET GLOBAL wait_timeout = 600;
SET GLOBAL interactive_timeout = 600;

-- Grant additional privileges if needed
FLUSH PRIVILEGES;

-- The following SQL will be executed AFTER Flask creates the tables
-- You can add initial data or additional indexes here

-- Example: Insert default roles (will be created by Flask migration later)
-- INSERT INTO Role (id, Name) VALUES
--   ('role_user_default', 'user'),
--   ('role_admin_default', 'admin'),
--   ('role_moderator', 'moderator');

-- Note: All indexes are already defined in the SQLAlchemy models
-- Additional indexes can be added here if needed for performance
