#!/usr/bin/env python3
"""
Detailed authentication test script to debug login issues
"""

import requests
import json
import urllib3
import os
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"

LOGIN_PAYLOAD = {
    "user_name": os.environ.get("ATM_USERNAME", "Lucky.Saputra"),
    "password": os.environ.get("ATM_PASSWORD", "TimlesMon2024")
}

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://172.31.1.46",
    "Referer": "https://172.31.1.46/sigitportal/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Connection": "keep-alive"
}

def test_authentication():
    """Test the authentication endpoint with detailed logging"""
    
    print("=" * 80)
    print("DETAILED AUTHENTICATION TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Login URL: {LOGIN_URL}")
    print(f"Username: {LOGIN_PAYLOAD['user_name']}")
    print(f"Password: {'*' * len(LOGIN_PAYLOAD['password'])}")
    print()
    
    # Test the POST request
    try:
        print("Sending POST request for authentication...")
        print("Headers:")
        for key, value in COMMON_HEADERS.items():
            print(f"  {key}: {value}")
        print()
        print("Payload:")
        print(f"  {json.dumps(LOGIN_PAYLOAD, indent=2)}")
        print()
        
        session = requests.Session()
        response = session.post(
            LOGIN_URL,
            json=LOGIN_PAYLOAD,
            headers=COMMON_HEADERS,
            verify=False,
            timeout=30
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Reason: {response.reason}")
        print()
        
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        
        print("Response Content:")
        try:
            # Try to parse as JSON
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            
            # Analyze the response structure
            print("\n" + "=" * 50)
            print("RESPONSE ANALYSIS")
            print("=" * 50)
            
            if isinstance(response_json, dict):
                print("Response is a dictionary with keys:")
                for key in response_json.keys():
                    print(f"  - {key}")
                
                # Look for token in various places
                print("\nToken Search:")
                
                # Direct keys
                for token_key in ['user_token', 'token', 'authToken', 'accessToken']:
                    if token_key in response_json:
                        token_value = response_json[token_key]
                        print(f"  Found token in '{token_key}': {token_value[:20]}..." if len(str(token_value)) > 20 else f"  Found token in '{token_key}': {token_value}")
                
                # Header field
                if 'header' in response_json:
                    print("  Found 'header' field:")
                    header = response_json['header']
                    if isinstance(header, dict):
                        for key in header.keys():
                            print(f"    - {key}")
                        if 'user_token' in header:
                            token = header['user_token']
                            print(f"    Token in header: {token[:20]}..." if len(str(token)) > 20 else f"    Token in header: {token}")
                
                # Check result codes
                if 'header' in response_json and isinstance(response_json['header'], dict):
                    result_code = response_json['header'].get('result_code')
                    result_desc = response_json['header'].get('result_description')
                    if result_code:
                        print(f"\nResult Code: {result_code}")
                    if result_desc:
                        print(f"Result Description: {result_desc}")
                
            else:
                print(f"Response is not a dictionary, type: {type(response_json)}")
                
        except json.JSONDecodeError as e:
            print(f"Response is not valid JSON: {e}")
            print("Raw response content:")
            print(response.text[:1000])  # First 1000 characters
            if len(response.text) > 1000:
                print("... (truncated)")
        
        # Check if request was successful
        if response.status_code == 200:
            print(f"\n✅ HTTP request successful (200 OK)")
        else:
            print(f"\n❌ HTTP request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_authentication()
