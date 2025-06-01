#!/usr/bin/env python3
"""
Test script to compare the working crawler method vs the problematic script method
"""

import requests
import urllib3
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("MethodComparison")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
DASHBOARD_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"

LOGIN_PAYLOAD = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2024"
}

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://172.31.1.46",
    "Referer": "https://172.31.1.46/sigitportal/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Connection": "keep-alive"
}

def authenticate():
    """Authenticate and get token"""
    session = requests.Session()
    
    try:
        log.info("Authenticating...")
        response = session.post(
            LOGIN_URL,
            json=LOGIN_PAYLOAD,
            headers=COMMON_HEADERS,
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        
        auth_data = response.json()
        
        # Extract token using the same method as working crawler
        user_token = None
        for key in ['user_token', 'token']:
            if key in auth_data:
                user_token = auth_data[key]
                log.info(f"Token extracted with key '{key}'")
                break
                
        if not user_token:
            user_token = auth_data.get("header", {}).get("user_token")
            if user_token:
                log.info("Token extracted from 'header' field")
        
        if user_token:
            log.info("✅ Authentication successful")
            return session, user_token
        else:
            log.error("❌ Failed to extract token")
            return None, None
            
    except Exception as e:
        log.error(f"❌ Authentication failed: {str(e)}")
        return None, None

def test_crawler_method(session, user_token, status):
    """Test the working crawler method"""
    log.info(f"\n🔍 TESTING CRAWLER METHOD FOR STATUS: {status}")
    
    payload = {
        "header": {
            "logged_user": LOGIN_PAYLOAD["user_name"],
            "user_token": user_token
        },
        "body": {
            "parameters_list": [
                {
                    "parameter_name": "issueStateName",
                    "parameter_values": [status]
                }
            ]
        }
    }
    
    try:
        log.info(f"Making PUT request to: {DASHBOARD_URL}")
        log.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = session.put(
            DASHBOARD_URL,
            json=payload,
            headers=COMMON_HEADERS,
            verify=False,
            timeout=30
        )
        
        log.info(f"Response status: {response.status_code}")
        log.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            log.info("✅ SUCCESS - Crawler method works!")
            data = response.json()
            log.info(f"Response structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict) and "body" in data:
                body = data["body"]
                log.info(f"Body type: {type(body)}, Length: {len(body) if isinstance(body, list) else 'N/A'}")
            return True
        else:
            log.error(f"❌ FAILED - Status: {response.status_code}")
            log.error(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        log.error(f"❌ Exception in crawler method: {str(e)}")
        return False

def main():
    """Main test function"""
    log.info("="*60)
    log.info("METHOD COMPARISON TEST")
    log.info("="*60)
    
    # Authenticate
    session, user_token = authenticate()
    if not session or not user_token:
        log.error("Cannot proceed without authentication")
        return
    
    # Test with AVAILABLE status (same as problematic script)
    test_statuses = ["AVAILABLE", "WOUNDED", "WARNING"]
    
    for status in test_statuses:
        success = test_crawler_method(session, user_token, status)
        if not success:
            log.warning(f"Method failed for status: {status}")
        log.info("-" * 40)

if __name__ == "__main__":
    main()
