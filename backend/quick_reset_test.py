#!/usr/bin/env python3
"""
Quick Password Reset Test
Simple script to test password reset with a fresh token
"""

import requests
import sys

# API Configuration
API_BASE_URL = "http://localhost:8001"
HEADERS = {"Content-Type": "application/json"}

def test_with_token(token):
    """Test password reset with provided token"""
    print(f"🔍 Testing token: {token[:50]}...")
    
    # Step 1: Verify token
    print("\n1️⃣ Verifying token...")
    try:
        response = requests.get(f"{API_BASE_URL}/auth/verify-reset-token/{token}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token valid for user: {data.get('username')} ({data.get('email')})")
        else:
            print(f"❌ Token verification failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False
    
    # Step 2: Reset password
    print("\n2️⃣ Resetting password...")
    new_password = "NewSecurePassword123!"
    reset_data = {
        "token": token,
        "new_password": new_password,
        "confirm_password": new_password
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/reset-password", 
                               headers=HEADERS, json=reset_data, timeout=30)
        if response.status_code == 200:
            print("✅ Password reset successful!")
            print(f"🔑 New password: {new_password}")
            return True
        else:
            print(f"❌ Password reset failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

def main():
    """Main function"""
    print("🔐 Quick Password Reset Test")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("📧 Check your email for the new reset link.")
        print("📋 Copy the token from the URL (the part after 'token=')")
        token = input("\n🎫 Enter your reset token: ").strip()
    
    if not token:
        print("❌ No token provided")
        return
    
    success = test_with_token(token)
    
    if success:
        print("\n🎉 Password reset completed successfully!")
        print("🔑 You can now login with: NewSecurePassword123!")
    else:
        print("\n❌ Password reset failed. Try with a fresh token.")

if __name__ == "__main__":
    main()
