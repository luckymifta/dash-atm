#!/usr/bin/env python3
"""
Database environment variables verification script

This script verifies that dotenv is loading environment variables correctly
from the .env file for database connections. It shows what database connection
parameters would be used by the main script.
"""

import os
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("❌ python-dotenv not installed. Environment variables will not be loaded from .env file.")

print("\n" + "=" * 80)
print("DATABASE ENVIRONMENT VARIABLES CHECK")
print("=" * 80)

# Check current directory and script location
print(f"\nCurrent directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")

# Check if .env file exists in current directory
env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file_path):
    print(f"\n✅ .env file found at {env_file_path}")
else:
    print(f"\n❌ .env file NOT found at {env_file_path}")
    # Check other common locations
    parent_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(parent_env_path):
        print(f"ℹ️ .env file found in parent directory at {parent_env_path}")

# Get database connection parameters
db_config = {
    "host": os.environ.get("DB_HOST", "[Not set - will default to localhost]"),
    "port": os.environ.get("DB_PORT", "[Not set - will default to 5432]"),
    "database": os.environ.get("DB_NAME", "[Not set - will default to atm_monitor]"),
    "user": os.environ.get("DB_USER", "[Not set - will default to postgres]"),
    "password": os.environ.get("DB_PASSWORD", "[Not set]") if "DB_PASSWORD" in os.environ else 
              os.environ.get("DB_PASS", "[Not set]") if "DB_PASS" in os.environ else "[Not set]"
}

print("\nDatabase connection parameters that would be used:")
for param, value in db_config.items():
    if param != "password":
        print(f"  {param}: {value}")
    else:
        print(f"  {param}: {'[Set but hidden]' if '[Not set]' not in value else '[Not set - connection may fail]'}")

print("\nAll environment variables related to database:")
db_related_vars = [var for var in os.environ.keys() if var.startswith("DB_")]
if db_related_vars:
    for var in sorted(db_related_vars):
        if "PASS" in var or "PASSWORD" in var:
            print(f"  {var}: {'*' * 8} [hidden for security]")
        else:
            print(f"  {var}: {os.environ.get(var)}")
else:
    print("  No database-related environment variables found")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if "[Not set]" in db_config["password"]:
    print("\n❌ Database password not set - connection will likely fail")
    print("Create or edit your .env file with proper database credentials")
    print("Example .env content:")
    print("""
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=atm_monitor
DB_USER=postgres
DB_PASS=your_password
    """)
elif "[Not set]" in db_config["host"]:
    print("\n⚠️ Database host not set - will use default localhost")
    print("For production, consider setting DB_HOST in your .env file")
else:
    print(f"\n✅ Environment variables are properly configured")
    print(f"Database connection would be to: {db_config['host']}:{db_config['port']} as user {db_config['user']}")

print("\n" + "=" * 80)
