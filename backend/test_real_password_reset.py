#!/usr/bin/env python3
"""
Real Password Reset Test
Test the actual password reset flow with real user data
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8001"  # Assuming your API is running on port 8001
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Your actual user information
USER_DATA = {
    "username": "timlesdev",
    "email": "luckymifta.s@gmail.com"
}

def test_forgot_password():
    """Test the forgot password endpoint with real user data"""
    print("🔐 Testing Password Reset Flow")
    print("=" * 60)
    
    print(f"👤 Username: {USER_DATA['username']}")
    print(f"📧 Email: {USER_DATA['email']}")
    print(f"🌐 API URL: {API_BASE_URL}")
    
    # Test forgot password endpoint
    print("\n📤 Step 1: Sending forgot password request...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/forgot-password",
            headers=HEADERS,
            json=USER_DATA,
            timeout=30  # Increased timeout
        )
        
        print(f"📡 HTTP Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Forgot password request successful!")
            print(f"📝 Message: {result.get('message', 'No message')}")
            print("\n📧 Check your email at: luckymifta.s@gmail.com")
            print("📋 The password reset email should arrive within a few minutes.")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"❌ Error: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"❌ Response text: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print("💡 Make sure your API server is running on http://localhost:8001")
        return False

def test_api_health():
    """Test if the API server is responsive"""
    print("🏥 Testing API Health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running and responsive")
            return True
        else:
            print(f"⚠️ API server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("💡 Make sure your API server is running:")
        print("   uvicorn user_management_api:app --host 0.0.0.0 --port 8001 --reload")
        return False

def test_user_exists():
    """Test if the user exists in the database (optional endpoint)"""
    print("👤 Checking if user exists...")
    
    # Note: This would require authentication, so we'll skip for now
    # The forgot-password endpoint will handle user validation
    print("ℹ️  User validation will be done by the forgot-password endpoint")
    return True

def main():
    """Main test function"""
    print("🏧 ATM Dashboard - Real Password Reset Test")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Test API health
    if not test_api_health():
        print("\n❌ API health check failed. Cannot proceed with tests.")
        return
    
    print("\n" + "=" * 60)
    
    # Step 2: Test user validation (skip for now)
    test_user_exists()
    
    print("\n" + "=" * 60)
    
    # Step 3: Test forgot password with real data
    success = test_forgot_password()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 Password reset email test completed successfully!")
        print("\n📋 Next Steps:")
        print("1. ✅ Check your email: luckymifta.s@gmail.com")
        print("2. ✅ Look for email from: dash@britimorleste.tl")
        print("3. ✅ Subject: '🔐 Password Reset Request - ATM Monitoring Dashboard'")
        print("4. ✅ Click the reset link in the email")
        print("5. ✅ Test the reset password form")
        
        print("\n📧 Email Details to Look For:")
        print("• From: ATM Dashboard <dash@britimorleste.tl>")
        print("• Professional HTML email with security warnings")
        print("• Reset button and secure link")
        print("• 24-hour expiration notice")
        
        print("\n🔍 If email doesn't arrive:")
        print("• Check spam/junk folder")
        print("• Verify Mailjet account is active")
        print("• Check Mailjet logs for delivery status")
        
    else:
        print("❌ Password reset test failed")
        print("\n🔧 Troubleshooting:")
        print("• Verify API server is running")
        print("• Check user exists in database")
        print("• Verify Mailjet credentials")
        print("• Check server logs for errors")

if __name__ == "__main__":
    main()
