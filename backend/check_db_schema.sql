-- Commands to check existing database schema for ATM tables

-- Check if tables exist and get their structure
\dt+ regional_data;
\dt+ terminal_details; 
\dt+ terminal_cash_information;

-- Get detailed schema for regional_data table
\d+ regional_data;

-- Get detailed schema for terminal_details table  
\d+ terminal_details;

-- Get detailed schema for terminal_cash_information table
\d+ terminal_cash_information;

-- Alternative: Get all table schemas in one query
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name IN ('regional_data', 'terminal_details', 'terminal_cash_information')
ORDER BY table_name, ordinal_position;

-- Check indexes and constraints
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type, 
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name IN ('regional_data', 'terminal_details', 'terminal_cash_information')
ORDER BY tc.table_name, tc.constraint_type;
