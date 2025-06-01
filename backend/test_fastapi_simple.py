#!/usr/bin/env python3
"""
Simple FastAPI Test Script for ATM Monitoring API
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, description):
    """Test an endpoint and print results"""
    print(f"\n🧪 Testing: {description}")
    print(f"   Endpoint: GET {endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Response type: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())}")
        elif response.status_code == 404:
            print(f"   ⚠️  No data found (404) - Expected for some endpoints")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

def main():
    print("=" * 60)
    print("🚀 FastAPI ATM Monitoring API - Basic Test Suite")
    print("=" * 60)
    
    # Test endpoints
    test_endpoint("/api/v1/health", "Health Check")
    test_endpoint("/api/v1/atm/status/summary", "ATM Summary")
    test_endpoint("/api/v1/atm/status/regional", "Regional Data")
    test_endpoint("/api/v1/atm/status/regional?region_code=TL-DL", "Regional Data - TL-DL")
    test_endpoint("/api/v1/atm/status/trends/TL-DL", "Trends - TL-DL")
    test_endpoint("/api/v1/atm/status/latest", "Latest Data")
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
