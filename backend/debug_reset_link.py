#!/usr/bin/env python3
"""
Debug script to check password reset link generation
Run this on your VPS to see what's happening with environment variables
"""

import os
import sys
from dotenv import load_dotenv

def debug_environment_variables():
    """Debug environment variables for password reset"""
    
    print("🔍 Password Reset Link Generation Debug")
    print("=" * 50)
    
    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_files = ['.env', '.env.production', '.env.local']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ Found {env_file}")
        else:
            print(f"❌ Missing {env_file}")
    
    print("\n" + "-" * 30)
    print("Environment Variables BEFORE loading .env:")
    print(f"FRONTEND_BASE_URL (system): {os.environ.get('FRONTEND_BASE_URL', 'NOT_SET')}")
    
    # Try loading .env file
    print("\n" + "-" * 30)
    print("Loading .env file...")
    
    if os.path.exists('.env'):
        load_dotenv('.env', override=True)
        print("✅ .env file loaded")
    else:
        print("❌ .env file not found")
    
    print("\nEnvironment Variables AFTER loading .env:")
    print(f"FRONTEND_BASE_URL: {os.getenv('FRONTEND_BASE_URL', 'NOT_FOUND')}")
    
    # Check what would be used in the actual code
    frontend_base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
    print(f"\nActual value that would be used: {frontend_base_url}")
    
    # Simulate reset link generation
    test_token = "test_token_123"
    reset_link = f"{frontend_base_url}/auth/reset-password?token={test_token}"
    print(f"Generated reset link: {reset_link}")
    
    # Check .env file contents
    print("\n" + "-" * 30)
    print(".env file contents:")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'FRONTEND' in line.upper():
                    print(f"Line {i}: {line.strip()}")
    else:
        print("❌ .env file not found")
    
    # Check all environment variables that contain 'frontend' or 'url'
    print("\n" + "-" * 30)
    print("All environment variables containing 'frontend' or 'url':")
    for key, value in os.environ.items():
        if 'frontend' in key.lower() or 'url' in key.lower():
            print(f"{key}: {value}")

if __name__ == "__main__":
    debug_environment_variables()
