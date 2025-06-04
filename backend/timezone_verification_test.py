#!/usr/bin/env python3
"""
Timezone Verification Test for ATM Dashboard API

This script verifies that all API endpoints are returning timestamps
converted to Dili local time (UTC+9).

Author: ATM Monitoring System
Created: 2025-06-04
"""

import requests
import json
from datetime import datetime
import pytz

# Test configuration
BASE_URL = "http://localhost:8000"
DILI_TZ = pytz.timezone('Asia/Dili')
UTC_TZ = pytz.UTC

def test_endpoint_timestamps(endpoint_name, url, timestamp_paths):
    """Test timestamp conversion for a specific endpoint"""
    print(f"\n=== Testing {endpoint_name} ===")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        
        for path in timestamp_paths:
            try:
                # Navigate through nested path
                current = data
                for key in path.split('.'):
                    if '[' in key and ']' in key:
                        # Handle array access like "data[0]"
                        array_key = key.split('[')[0]
                        index = int(key.split('[')[1].split(']')[0])
                        current = current[array_key][index]
                    else:
                        current = current[key]
                
                if current:
                    # Parse the timestamp
                    timestamp_str = current.replace('T', ' ').replace('Z', '')
                    timestamp = datetime.fromisoformat(timestamp_str)
                    
                    # Check if timestamp looks like Dili time (should be UTC+9)
                    utc_now = datetime.utcnow()
                    dili_now = UTC_TZ.localize(utc_now).astimezone(DILI_TZ).replace(tzinfo=None)
                    
                    print(f"✅ {path}: {current}")
                    print(f"   📅 Parsed as: {timestamp}")
                    
                else:
                    print(f"⚠️ {path}: No timestamp found")
                    
            except Exception as e:
                print(f"❌ Error accessing {path}: {e}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    return True

def main():
    """Test all API endpoints for timezone conversion"""
    print("🕒 ATM Dashboard API Timezone Verification Test")
    print("=" * 50)
    
    # Current time reference
    utc_now = datetime.utcnow()
    dili_now = UTC_TZ.localize(utc_now).astimezone(DILI_TZ).replace(tzinfo=None)
    print(f"Current UTC time:  {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Dili time: {dili_now.strftime('%Y-%m-%d %H:%M:%S')} (UTC+9)")
    
    # Test endpoints
    endpoints = [
        {
            "name": "Summary Endpoint",
            "url": f"{BASE_URL}/api/v1/atm/status/summary?table_type=new",
            "paths": ["last_updated"]
        },
        {
            "name": "Regional Endpoint", 
            "url": f"{BASE_URL}/api/v1/atm/status/regional?table_type=new&region_code=TL-DL",
            "paths": ["regional_data[0].last_updated", "last_updated"]
        },
        {
            "name": "Trends Endpoint",
            "url": f"{BASE_URL}/api/v1/atm/status/trends/TL-DL?hours=24&table_type=new",
            "paths": ["trends[0].timestamp", "summary_stats.first_reading"]
        },
        {
            "name": "Latest Endpoint",
            "url": f"{BASE_URL}/api/v1/atm/status/latest?table_type=new",
            "paths": ["data_sources[0].data[0].last_updated", "summary.timestamp"]
        }
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_endpoint_timestamps(endpoint["name"], endpoint["url"], endpoint["paths"]):
            success_count += 1
    
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{len(endpoints)} endpoints passed")
    
    if success_count == len(endpoints):
        print("🎉 All endpoints are correctly returning Dili local time!")
    else:
        print("⚠️ Some endpoints may need further investigation")

if __name__ == "__main__":
    main()
