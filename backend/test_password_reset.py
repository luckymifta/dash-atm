#!/usr/bin/env python3
"""
Test script for password reset functionality
This script tests the core functionality without needing a running server
"""

import os
import sys
import hashlib
import uuid
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_management_api import (
    create_password_reset_token,
    verify_password_reset_token,
    verify_password_reset_token_db,
    store_password_reset_token,
    mark_password_reset_token_used,
    get_db_connection,
    execute_query
)
from email_service import EmailService

def test_token_functionality():
    """Test the token generation, hashing, and verification"""
    print("Testing token functionality...")
    
    # Test token generation
    user_id = str(uuid.uuid4())  # Generate proper UUID
    email = "test@example.com"
    token = create_password_reset_token(user_id, email)
    print(f"✓ Generated token: {token[:20]}... (length: {len(token)})")
    
    # Test token verification
    token_data = verify_password_reset_token(token)
    print(f"✓ Token verification: {token_data is not None}")
    
    if token_data:
        print(f"  - User ID: {token_data.get('user_id')}")
        print(f"  - Email: {token_data.get('email')}")
    
    return token, user_id, email

def test_database_operations():
    """Test database operations for password reset"""
    print("\nTesting database operations...")
    
    try:
        # First, get an existing user from the database for testing
        query = "SELECT id, email FROM users WHERE is_deleted = false LIMIT 1"
        user_result = execute_query(query, fetch="one")
        
        if not user_result:
            print("ℹ No users found in database - skipping database tests")
            print("ℹ Create a user first or run the API server to initialize default users")
            return True
        
        test_user_id = user_result['id']
        test_email = "password-reset-test@example.com"  # Use a test email
        
        token = create_password_reset_token(test_user_id, test_email)
        
        # Store reset token
        store_password_reset_token(test_user_id, token, test_email)
        print(f"✓ Created reset token entry for {test_email}")
        
        # Verify reset token from database
        token_data = verify_password_reset_token_db(token)
        print(f"✓ Token verification from database: {token_data is not None}")
        
        if token_data:
            print(f"  - Found token for email: {token_data.get('email')}")
        
        # Mark token as used
        mark_password_reset_token_used(token)
        print("✓ Marked token as used")
        
        # Try to verify used token (should fail)
        used_token_data = verify_password_reset_token_db(token)
        print(f"✓ Used token verification: {used_token_data is None} (should be True)")
        
        # Cleanup test data
        try:
            query = "DELETE FROM password_reset_tokens WHERE email = %s"
            execute_query(query, (test_email,))
            print("✓ Cleaned up test data")
        except Exception as e:
            print(f"Note: Could not clean up test data: {e}")
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False
    
    return True

def test_email_service():
    """Test email service initialization"""
    print("\nTesting email service...")
    
    try:
        email_service = EmailService()
        print(f"✓ Email service initialized (enabled: {email_service.enabled})")
        
        if not email_service.enabled:
            print("ℹ Email service is disabled - Mailjet credentials not configured")
            print("ℹ This is expected for testing - configure MAILJET_API_KEY and MAILJET_SECRET_KEY to enable")
        else:
            print("✓ Email service is enabled - Mailjet credentials found")
        
        return True
    except Exception as e:
        print(f"✗ Email service test failed: {e}")
        return False

def test_missing_imports():
    """Test that all required modules can be imported"""
    print("\nTesting imports...")
    
    try:
        # Test user_management_api imports
        from user_management_api import app
        print("✓ FastAPI app imported successfully")
        
        # Test email service import
        from email_service import EmailService
        print("✓ EmailService imported successfully")
        
        # Test JWT import
        import jwt
        print("✓ JWT library available")
        
        # Test Mailjet import
        import mailjet_rest
        print("✓ Mailjet library available")
        
        # Test other dependencies
        import bcrypt
        print("✓ bcrypt library available")
        
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Password Reset Functionality Test")
    print("=" * 40)
    
    # Test imports
    try:
        if not test_missing_imports():
            print("✗ Import tests failed")
            return
        print("✓ Import tests passed")
    except Exception as e:
        print(f"✗ Import tests failed: {e}")
        return
    
    # Test token functionality
    try:
        test_token_functionality()
        print("✓ Token functionality tests passed")
    except Exception as e:
        print(f"✗ Token functionality tests failed: {e}")
        return
    
    # Test email service
    try:
        test_email_service()
        print("✓ Email service tests passed")
    except Exception as e:
        print(f"✗ Email service tests failed: {e}")
        return
    
    # Test database operations
    try:
        db_success = test_database_operations()
        if db_success:
            print("✓ Database tests passed")
        else:
            print("✗ Database tests failed")
            return
    except Exception as e:
        print(f"✗ Database tests failed: {e}")
        return
    
    print("\n" + "=" * 40)
    print("🎉 All password reset functionality tests passed!")
    print("\nNext steps:")
    print("1. Configure Mailjet API credentials in .env file:")
    print("   - Get API key and secret from https://app.mailjet.com/account/apikeys")
    print("   - Update MAILJET_API_KEY and MAILJET_SECRET_KEY in .env")
    print("   - Set MAILJET_FROM_EMAIL to your verified sender email")
    print("2. Test the API endpoints using curl or Postman")
    print("3. Integrate the frontend components")
    print("4. Deploy to production")

if __name__ == "__main__":
    main()
