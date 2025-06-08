#!/usr/bin/env python3
"""
Database Setup Script for ATM Data Retrieval System
This script will create all necessary tables and indexes for the development_db
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our new database connector
from db_connector_new import DatabaseConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s",
    handlers=[
        logging.FileHandler("database_setup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("DatabaseSetup")

def main():
    """Main setup function"""
    print("=" * 80)
    print("ATM DATA RETRIEVAL SYSTEM - DATABASE SETUP")
    print("=" * 80)
    print(f"Setup started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database configuration info
    print("Database Configuration:")
    print("  Host: 88.222.214.26")
    print("  Port: 5432")
    print("  Database: development_db")
    print("  Username: timlesdev")
    print()
    
    # Initialize database connector
    log.info("Initializing database connector...")
    connector = DatabaseConnector()
    
    # Step 1: Test connection
    print("Step 1: Testing database connection...")
    if not connector.test_connection():
        print("❌ FAILED: Cannot connect to database")
        print("Please check:")
        print("- Database server is running")
        print("- Network connectivity to 88.222.214.26:5432")
        print("- Username and password are correct")
        print("- Database 'development_db' exists")
        return False
    
    print("✅ SUCCESS: Database connection established")
    print()
    
    # Step 2: Create tables
    print("Step 2: Creating database tables...")
    if not connector.create_tables():
        print("❌ FAILED: Cannot create tables")
        return False
    
    print("✅ SUCCESS: All tables created successfully")
    print()
    
    # Step 3: Verify setup
    print("Step 3: Verifying database setup...")
    table_info = connector.get_table_info()
    
    if not table_info.get('tables'):
        print("❌ FAILED: No tables found after creation")
        return False
    
    print("✅ SUCCESS: Database setup verified")
    print()
    
    # Step 4: Display summary
    print("Database Setup Summary:")
    print("-" * 40)
    
    expected_tables = ['regional_data', 'terminal_details', 'regional_atm_counts']
    created_tables = table_info.get('tables', [])
    
    for table in expected_tables:
        if table in created_tables:
            count = table_info.get('row_counts', {}).get(table, 0)
            print(f"✅ {table}: Created ({count} rows)")
        else:
            print(f"❌ {table}: Missing")
    
    # Show any additional tables
    additional_tables = [t for t in created_tables if t not in expected_tables]
    if additional_tables:
        print("\nAdditional tables found:")
        for table in additional_tables:
            count = table_info.get('row_counts', {}).get(table, 0)
            print(f"   {table}: {count} rows")
    
    print()
    print("=" * 80)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Test your ATM retrieval script with --demo mode")
    print("2. Run: python combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables")
    print("3. Check data insertion with the --save-json option")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("Setup completed successfully!")
            sys.exit(0)
        else:
            print("Setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error during setup: {e}")
        print(f"❌ FAILED: Unexpected error - {e}")
        sys.exit(1)
