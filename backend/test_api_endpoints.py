#!/usr/bin/env python3
"""
Complete Password Reset Flow API Test
Tests the actual API endpoints for the password reset functionality
"""

import requests
import json
import time
from datetime import datetime
import sys

# API Configuration
BASE_URL = "http://localhost:8001"  # User Management API port
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n📍 Step {step_num}: {description}")
    print("-" * 40)

def make_request(method, endpoint, data=None, expected_status=200):
    """Make an HTTP request and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=HEADERS, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        print(f"🌐 {method.upper()} {endpoint}")
        print(f"📤 Request: {json.dumps(data, indent=2) if data else 'No body'}")
        print(f"📊 Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"📥 Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📥 Response: {response.text}")
            response_data = {"text": response.text}
        
        if response.status_code != expected_status:
            print(f"⚠️  Expected status {expected_status}, got {response.status_code}")
        else:
            print("✅ Request successful")
        
        return response.status_code, response_data
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {url}")
        print("💡 Make sure the API server is running on the correct port")
        return None, None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None, None

def test_api_health():
    """Test if the API is running"""
    print_section("API Health Check")
    
    # Test if the API is responsive
    status, response = make_request("GET", "/", expected_status=404)  # Root might not exist
    
    if status is None:
        print("❌ API server is not responding")
        print("💡 Please ensure user_management_api.py is running on port 8001")
        return False
    
    print("✅ API server is running and responsive")
    return True

def test_forgot_password_flow():
    """Test the complete forgot password flow"""
    print_section("Forgot Password Flow Test")
    
    # Step 1: Test with valid user (assuming admin user exists)
    print_step(1, "Request password reset for existing user")
    
    forgot_data = {
        "username": "admin",
        "email": "admin@example.com"  # This might need to match the actual admin email
    }
    
    status, response = make_request("POST", "/auth/forgot-password", forgot_data)
    
    if status == 200:
        print("✅ Forgot password request successful")
        print("📧 Check the configured email address for the reset email")
    else:
        print("❌ Forgot password request failed")
        return None
    
    # Step 2: Test with non-existent user (should still return success for security)
    print_step(2, "Request password reset for non-existent user")
    
    fake_data = {
        "username": "nonexistent",
        "email": "fake@example.com"
    }
    
    status, response = make_request("POST", "/auth/forgot-password", fake_data)
    
    if status == 200:
        print("✅ Non-existent user request handled correctly (security)")
    
    return True

def test_reset_password_flow():
    """Test the reset password flow"""
    print_section("Reset Password Flow Test")
    
    print("📝 For this test, you'll need a valid reset token from an email")
    print("💡 Check your email inbox for the reset link and extract the token")
    
    # Get token from user input
    token = input("\n🔑 Enter the reset token from the email (or 'skip' to skip): ").strip()
    
    if token.lower() == 'skip':
        print("⏭️  Skipping reset password test")
        return True
    
    if not token:
        print("❌ No token provided, skipping reset test")
        return True
    
    # Step 1: Verify the token
    print_step(1, "Verify reset token")
    
    status, response = make_request("GET", f"/auth/verify-reset-token/{token}")
    
    if status == 200:
        print("✅ Token is valid")
        print(f"👤 Token is for user: {response.get('username', 'Unknown')}")
    else:
        print("❌ Token verification failed")
        return False
    
    # Step 2: Reset the password
    print_step(2, "Reset password with token")
    
    new_password = "NewSecurePassword123!"
    reset_data = {
        "token": token,
        "new_password": new_password,
        "confirm_password": new_password
    }
    
    status, response = make_request("POST", "/auth/reset-password", reset_data)
    
    if status == 200:
        print("✅ Password reset successful")
        print("🔐 Password has been changed")
        return True
    else:
        print("❌ Password reset failed")
        return False

def test_edge_cases():
    """Test edge cases and error conditions"""
    print_section("Edge Cases and Error Handling")
    
    # Test 1: Invalid email format
    print_step(1, "Test invalid email format")
    
    invalid_data = {
        "username": "admin",
        "email": "invalid-email"
    }
    
    status, response = make_request("POST", "/auth/forgot-password", invalid_data, expected_status=422)
    
    if status == 422:
        print("✅ Invalid email format correctly rejected")
    
    # Test 2: Empty username
    print_step(2, "Test empty username")
    
    empty_data = {
        "username": "",
        "email": "test@example.com"
    }
    
    status, response = make_request("POST", "/auth/forgot-password", empty_data, expected_status=422)
    
    if status == 422:
        print("✅ Empty username correctly rejected")
    
    # Test 3: Invalid token verification
    print_step(3, "Test invalid token verification")
    
    fake_token = "invalid_token_12345"
    status, response = make_request("GET", f"/auth/verify-reset-token/{fake_token}", expected_status=400)
    
    if status == 400:
        print("✅ Invalid token correctly rejected")
    
    # Test 4: Password mismatch
    print_step(4, "Test password mismatch")
    
    mismatch_data = {
        "token": "fake_token",
        "new_password": "password1",
        "confirm_password": "password2"
    }
    
    status, response = make_request("POST", "/auth/reset-password", mismatch_data, expected_status=400)
    
    if status == 400:
        print("✅ Password mismatch correctly rejected")

def test_api_endpoints_documentation():
    """Show available endpoints for testing"""
    print_section("Available Password Reset Endpoints")
    
    endpoints = [
        {
            "method": "POST",
            "endpoint": "/auth/forgot-password",
            "description": "Initiate password reset",
            "body": {
                "username": "string",
                "email": "string (email format)"
            }
        },
        {
            "method": "GET", 
            "endpoint": "/auth/verify-reset-token/{token}",
            "description": "Verify if reset token is valid",
            "body": "None"
        },
        {
            "method": "POST",
            "endpoint": "/auth/reset-password", 
            "description": "Complete password reset",
            "body": {
                "token": "string",
                "new_password": "string (min 8 chars)",
                "confirm_password": "string (must match)"
            }
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n{i}. {endpoint['method']} {endpoint['endpoint']}")
        print(f"   Description: {endpoint['description']}")
        print(f"   Body: {json.dumps(endpoint['body'], indent=8)}")

def main():
    """Main test function"""
    print("🏧 ATM Dashboard - Password Reset API Flow Test")
    print("=" * 60)
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing API at: {BASE_URL}")
    
    # Test API health
    if not test_api_health():
        print("\n❌ API health check failed. Cannot proceed with tests.")
        print("💡 Please start the user_management_api.py server and try again.")
        return
    
    # Show available endpoints
    test_api_endpoints_documentation()
    
    # Test forgot password flow
    test_forgot_password_flow()
    
    # Test edge cases
    test_edge_cases()
    
    # Test reset password flow (interactive)
    test_reset_password_flow()
    
    print_section("Test Summary")
    print("✅ Password reset API flow testing completed!")
    print("\n📋 What was tested:")
    print("   • API health and connectivity")
    print("   • Forgot password endpoint")
    print("   • Token verification endpoint") 
    print("   • Password reset endpoint")
    print("   • Error handling and edge cases")
    print("   • Email integration (if configured)")
    
    print("\n🎯 Next steps:")
    print("   1. Check email inbox for reset emails")
    print("   2. Test the complete flow with a real token")
    print("   3. Integrate with frontend components")
    print("   4. Deploy to production environment")

if __name__ == "__main__":
    main()
