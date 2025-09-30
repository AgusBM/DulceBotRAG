-- Connect to the 'postgres' database (default administrative database)
\c postgres

-- Check if the database exists and create it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'BakeryDB') THEN
        CREATE DATABASE BakeryDB;
    END IF;
END $$;

-- Connect to the BakeryDB database
\c BakeryDB;

-- Create the user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'appwhats') THEN
        CREATE USER appwhats WITH PASSWORD 'KSDF9jihd78fG3ND8';
    END IF;
END $$;

-- Grant privileges to the user (AFTER connecting to BakeryDB and confirming it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'BakeryDB') THEN
        GRANT CONNECT ON DATABASE BakeryDB TO appwhats;
        GRANT USAGE ON SCHEMA public TO appwhats;
        GRANT CREATE ON SCHEMA public TO appwhats; -- Optional: Allow the user to create objects in the schema
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO appwhats;
        ALTER DEFAULT PRIVILEGES FOR ROLE appwhats GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES IN SCHEMA public;
    END IF;
END $$;

-- Create the WhatsAppMessages table if it doesn't exist
CREATE TABLE IF NOT EXISTS WhatsAppMessages (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(100),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the conversation_history table if it doesn't exist
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255),
    role VARCHAR(50),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
