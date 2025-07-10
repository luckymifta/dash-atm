#!/usr/bin/env python3
"""
Quick Database Connection Test

This script tests the database connection using the current configuration.
Use this to verify your .env settings before running the main script.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_db_connection():
    """Test database connection with current configuration"""
    print("Testing Database Connection...")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("ERROR: .env file not found!")
        print("Please create a .env file with your database credentials.")
        print("You can copy from .env.template and update the values.")
        return False
    
    # Check environment variables
    print("Checking environment variables...")
    db_config = {
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'database': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD') or os.environ.get('DB_PASS', '')
    }
    
    for key, value in db_config.items():
        if key == 'password':
            print(f"   {key}: {'SET' if value else 'NOT SET'}")
        else:
            print(f"   {key}: {value or 'NOT SET'}")
    
    # Check for missing values
    missing = [k for k, v in db_config.items() if not v]
    if missing:
        print(f"\nERROR: Missing required database settings: {', '.join(missing)}")
        print("Please update your .env file with the correct database credentials.")
        return False
    
    print("\nSUCCESS: All database settings are configured")
    
    # Test actual connection
    print("\nTesting database connection...")
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print("SUCCESS: Database connection successful!")
        if version and len(version) > 0:
            print(f"   PostgreSQL version: {version[0]}")
        return True
        
    except ImportError:
        print("ERROR: psycopg2 not installed. Please install it with:")
        print("   pip install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        print("\nPossible issues:")
        print("   - Incorrect host, port, or database name")
        print("   - Invalid username or password")
        print("   - Database server not running or not accessible")
        print("   - Firewall blocking the connection")
        return False

if __name__ == "__main__":
    print("ATM System - Database Connection Test")
    print("=" * 50)
    
    success = test_db_connection()
    
    if success:
        print("\nSUCCESS: Database connection test passed!")
        print("You can now run the ATM data retrieval script.")
    else:
        print("\nERROR: Database connection test failed!")
        print("Please fix the issues above before running the main script.")
        
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
