#!/usr/bin/env python3
"""
FastAPI Test Script for ATM Monitoring API

This script tests all the FastAPI endpoints to ensure they're working correctly.
Run this after starting the FastAPI server to validate functionality.

Usage:
python test_fastapi.py
"""

import asyncio
import json
import sys
from datetime import datetime
import aiohttp

# API Base URL
BASE_URL = "http://localhost:8000"

async def test_endpoint(session, endpoint, description):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n[TEST] {description}")
    print(f"[URL]  {url}")
    
    try:
        async with session.get(url) as response:
            status = response.status
            data = await response.json()
            
            if status == 200:
                print(f"[OK]   Status: {status}")
                if isinstance(data, dict):
                    if 'total_atms' in data:
                        print(f"[DATA] Total ATMs: {data.get('total_atms', 'N/A')}")
                    elif 'regional_data' in data:
                        print(f"[DATA] Regions: {len(data.get('regional_data', []))}")
                    elif 'trends' in data:
                        print(f"[DATA] Trend points: {len(data.get('trends', []))}")
                    elif 'data_sources' in data:
                        print(f"[DATA] Data sources: {len(data.get('data_sources', []))}")
                    elif 'database_connected' in data:
                        print(f"[DATA] DB Connected: {data.get('database_connected', False)}")
                return True
            else:
                print(f"[FAIL] Status: {status}")
                print(f"[ERROR] {data.get('detail', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("FastAPI ATM Monitoring API Test Suite")
    print("=" * 60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Started at: {datetime.now()}")
    
    # Test endpoints
    endpoints = [
        ("/api/v1/health", "Health Check"),
        ("/api/v1/atm/status/summary", "ATM Summary (Legacy Table)"),
        ("/api/v1/atm/status/summary?table_type=new", "ATM Summary (New Table)"),
        ("/api/v1/atm/status/regional", "Regional Breakdown"),
        ("/api/v1/atm/status/regional?region_name=JAKARTA", "Regional Data for Jakarta"),
        ("/api/v1/atm/status/latest", "Latest Data (All Tables)"),
        ("/api/v1/atm/status/latest?table_type=legacy", "Latest Data (Legacy Only)"),
        ("/api/v1/atm/status/latest?include_terminal_details=true", "Latest Data with Terminal Details"),
        ("/docs", "API Documentation"),
        ("/redoc", "Alternative Documentation"),
    ]
    
    # Note: Trends endpoint requires actual region name from database
    # We'll test with a placeholder that might exist
    trends_endpoints = [
        ("/api/v1/atm/status/trends/JAKARTA", "Regional Trends for Jakarta"),
        ("/api/v1/atm/status/trends/JAKARTA?hours=48", "Regional Trends (48 hours)"),
    ]
    
    successful_tests = 0
    total_tests = len(endpoints) + len(trends_endpoints)
    
    async with aiohttp.ClientSession() as session:
        # Test main endpoints
        for endpoint, description in endpoints:
            success = await test_endpoint(session, endpoint, description)
            if success:
                successful_tests += 1
        
        # Test trends endpoints (might fail if region doesn't exist)
        print(f"\n{'='*60}")
        print("Testing Trends Endpoints (May fail if region doesn't exist)")
        print("="*60)
        
        for endpoint, description in trends_endpoints:
            success = await test_endpoint(session, endpoint, description)
            if success:
                successful_tests += 1
    
    # Results summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Successful tests: {successful_tests}/{total_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("[SUCCESS] All tests passed! ✅")
        sys.exit(0)
    elif successful_tests >= total_tests * 0.8:
        print("[PARTIAL] Most tests passed! ⚠️")
        sys.exit(0)
    else:
        print("[FAILURE] Many tests failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("You can start it with: ./start_fastapi.sh")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Tests interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test suite failed: {e}")
        sys.exit(1)
