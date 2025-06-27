#!/usr/bin/env python3
"""
Debug script to test password reset functionality and trace environment variables
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_password_reset():
    """Debug the password reset process"""
    
    print("🔍 Password Reset Process Debug")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('.env', override=True)
    
    # Show current environment
    print(f"Working directory: {os.getcwd()}")
    print(f"FRONTEND_BASE_URL from env: {os.getenv('FRONTEND_BASE_URL', 'NOT_SET')}")
    
    try:
        # Import the email service to test
        from email_service import EmailService
        
        print("\n✅ Successfully imported EmailService")
        
        # Test environment variable reading in the actual context
        frontend_base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
        print(f"frontend_base_url variable: {frontend_base_url}")
        
        # Simulate the exact code from user_management_api.py
        reset_token = "debug_token_12345"
        reset_link = f"{frontend_base_url}/auth/reset-password?token={reset_token}"
        
        print(f"\n🔗 Generated reset link: {reset_link}")
        
        # Test email service initialization
        email_service = EmailService()
        print(f"Email service enabled: {email_service.enabled}")
        
        # Test sending email (this will just log if disabled)
        test_email = "test@example.com"
        test_username = "Test User"
        
        print(f"\n📧 Testing email send to {test_email}")
        print(f"Reset link in email: {reset_link}")
        
        # This will show what would be sent
        result = await email_service.send_password_reset_email(test_email, test_username, reset_link)
        print(f"Email send result: {result}")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

def check_environment_file():
    """Check the contents of the .env file"""
    print("\n" + "=" * 50)
    print("📄 Checking .env file contents")
    print("=" * 50)
    
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ {env_file} exists")
        with open(env_file, 'r') as f:
            content = f.read()
            print("File contents:")
            print("-" * 30)
            for i, line in enumerate(content.split('\n'), 1):
                if line.strip():  # Only show non-empty lines
                    print(f"{i:2d}: {line}")
            print("-" * 30)
    else:
        print(f"❌ {env_file} not found")
        print("Available files:")
        for file in os.listdir('.'):
            if file.startswith('.env'):
                print(f"  - {file}")

if __name__ == "__main__":
    print("Starting password reset debug...")
    
    # Check environment file first
    check_environment_file()
    
    # Run the async debug
    asyncio.run(debug_password_reset())
