#!/usr/bin/env python3
"""
Database connection test script for ATM cash information.
This script tests if the database connection parameters are correct
and if the terminal_cash_information table can be accessed.
"""

import os
import sys
import psycopg2
import argparse
from datetime import datetime

# Configure command line arguments
parser = argparse.ArgumentParser(description="Test database connection for ATM cash information")
parser.add_argument("--host", default="localhost", help="Database host")
parser.add_argument("--port", default="5432", help="Database port")
parser.add_argument("--dbname", default="atm_monitor", help="Database name")
parser.add_argument("--user", default="postgres", help="Database user")
parser.add_argument("--password", default="", help="Database password")
args = parser.parse_args()

print("=" * 80)
print("DATABASE CONNECTION TEST")
print("=" * 80)

# Test environment variables
print("\nTesting environment variables:")
env_vars = {
    "DB_HOST": os.environ.get("DB_HOST", "[Not set]"),
    "DB_PORT": os.environ.get("DB_PORT", "[Not set]"),
    "DB_NAME": os.environ.get("DB_NAME", "[Not set]"),
    "DB_USER": os.environ.get("DB_USER", "[Not set]"),
    "DB_PASSWORD": os.environ.get("DB_PASSWORD", "[Not set - hidden]") if "DB_PASSWORD" in os.environ else "[Not set]"
}

for var, value in env_vars.items():
    print(f"  {var}: {value}")

# Use command line arguments if provided, otherwise use environment variables
db_config = {
    "host": args.host if args.host != "localhost" else os.environ.get("DB_HOST", "localhost"),
    "port": args.port if args.port != "5432" else os.environ.get("DB_PORT", "5432"),
    "dbname": args.dbname if args.dbname != "atm_monitor" else os.environ.get("DB_NAME", "atm_monitor"),
    "user": args.user if args.user != "postgres" else os.environ.get("DB_USER", "postgres"),
    "password": args.password if args.password else os.environ.get("DB_PASSWORD", "")
}

print("\nUsing connection parameters:")
for param, value in db_config.items():
    if param != "password":
        print(f"  {param}: {value}")
    else:
        print(f"  {param}: {'*' * (len(value) if value else 0)}")

# Test database connection
print("\nTesting database connection...")
try:
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"]
    )
    print("✅ Successfully connected to database")
    
    # Test if table exists
    print("\nChecking if terminal_cash_information table exists...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'terminal_cash_information'
        )
    """)
    
    result = cursor.fetchone()
    table_exists = result[0] if result else False
    if table_exists:
        print("✅ Table terminal_cash_information exists")
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM terminal_cash_information")
        result = cursor.fetchone()
        row_count = result[0] if result else 0
        print(f"   Table contains {row_count} records")
        
        # Check table structure
        print("\nChecking table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'terminal_cash_information'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        for col_name, col_type, nullable in columns:
            print(f"  • {col_name}: {col_type} {'(nullable)' if nullable == 'YES' else ''}")
            
        # Test insert capability with a dummy record
        print("\nTesting insert capability with dummy record...")
        try:
            # Start a transaction
            cursor.execute("""
                INSERT INTO terminal_cash_information (
                    unique_request_id,
                    terminal_id,
                    retrieval_timestamp,
                    cassettes_data,
                    is_null_record
                ) VALUES (
                    '00000000-0000-0000-0000-000000000000',
                    'TEST_TERMINAL',
                    %s,
                    '[]'::jsonb,
                    TRUE
                )
            """, (datetime.now(),))
            
            # Get the ID of the inserted row
            cursor.execute("SELECT lastval()")
            result = cursor.fetchone()
            inserted_id = result[0] if result else None
            
            # Delete the test record
            cursor.execute("DELETE FROM terminal_cash_information WHERE id = %s", (inserted_id,))
            
            # Commit everything
            conn.commit()
            print("✅ Insert test successful (test record removed)")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Insert test failed: {str(e)}")
    else:
        print("❌ Table terminal_cash_information does not exist")
        
        # Try to create the table
        print("\nAttempting to create the table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminal_cash_information (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL,
                    terminal_id VARCHAR(50) NOT NULL,
                    business_code VARCHAR(50),
                    technical_code VARCHAR(50),
                    external_id VARCHAR(50),
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    event_date TIMESTAMP WITH TIME ZONE,
                    total_cash_amount DECIMAL(15, 2),
                    total_currency VARCHAR(10),
                    cassettes_data JSONB NOT NULL DEFAULT '[]'::jsonb,
                    raw_cash_data JSONB,
                    cassette_count INTEGER DEFAULT 0,
                    has_low_cash_warning BOOLEAN DEFAULT FALSE,
                    has_cash_errors BOOLEAN DEFAULT FALSE,
                    is_null_record BOOLEAN DEFAULT FALSE,
                    null_reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_cash_terminal_id 
                ON terminal_cash_information(terminal_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_cash_timestamp 
                ON terminal_cash_information(retrieval_timestamp DESC)
            """)
            
            conn.commit()
            print("✅ Table created successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to create table: {str(e)}")
        
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")
    print("\nPossible solutions:")
    print("1. Make sure PostgreSQL is running on the specified host and port")
    print("2. Verify username and password are correct")
    print("3. Check that the database name exists")
    print("4. Ensure firewall allows connections to the database port")
    print("5. Set DB_* environment variables correctly before running the script")

print("\n" + "=" * 80)
print("COMMON WINDOWS ENVIRONMENT VARIABLE SETUP")
print("=" * 80)
print("\nTo set environment variables in Windows Command Prompt:")
print("  set DB_HOST=your_host")
print("  set DB_PORT=5432")
print("  set DB_NAME=atm_monitor")
print("  set DB_USER=postgres")
print("  set DB_PASSWORD=your_password")
print("\nTo set environment variables in Windows PowerShell:")
print("  $env:DB_HOST=\"your_host\"")
print("  $env:DB_PORT=\"5432\"")
print("  $env:DB_NAME=\"atm_monitor\"")
print("  $env:DB_USER=\"postgres\"")
print("  $env:DB_PASSWORD=\"your_password\"")
print("\nTo set environment variables permanently in Windows:")
print("1. Search for 'environment variables' in Windows search")
print("2. Click 'Edit the system environment variables'")
print("3. Click 'Environment Variables...' button")
print("4. Add each variable under 'User variables' or 'System variables'")
print("\n" + "=" * 80)
