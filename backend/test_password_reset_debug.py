#!/usr/bin/env python3

import requests
import json

# First, request a password reset
print("1. Requesting password reset...")
forgot_response = requests.post(
    "http://localhost:8001/auth/forgot-password",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"email": "luckymifta.s@gmail.com"})
)

print(f"Forgot password response: {forgot_response.status_code}")
print(f"Response: {forgot_response.text}")

# You'll need to get the actual token from the email
print("\n2. Please check your email and copy the token from the reset link")
print("The token is the part after 'token=' in the URL")

token = input("Enter the token from the email: ").strip()

if token:
    print(f"\n3. Testing token verification...")
    verify_response = requests.get(
        f"http://localhost:8001/auth/verify-reset-token/{token}",
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Verify response: {verify_response.status_code}")
    print(f"Response: {verify_response.text}")
    
    if verify_response.status_code == 200:
        print(f"\n4. Testing password reset...")
        reset_response = requests.post(
            "http://localhost:8001/auth/reset-password",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "token": token,
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            })
        )
        
        print(f"Reset response: {verify_response.status_code}")
        print(f"Response: {reset_response.text}")
    else:
        print("Token verification failed, cannot proceed with reset")
else:
    print("No token provided, cannot test reset")
