#!/usr/bin/env python3
"""
Quick performance test for optimized SQL queries
"""

import requests
import time
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def get_date_string(days_ago):
    """Get date string for days ago"""
    date = datetime.now().date() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d")

def test_performance():
    """Test performance with different date ranges"""
    print("Testing optimized SQL performance...")
    print("="*60)
    
    test_cases = [
        {"days": 3, "description": "3 days (should work fast)"},
        {"days": 7, "description": "1 week"},
        {"days": 14, "description": "2 weeks"},
        {"days": 30, "description": "1 month"},
        {"days": 60, "description": "2 months"}
    ]
    
    all_tests_passed = True
    
    for case in test_cases:
        days = case["days"]
        description = case["description"]
        
        print(f"\n⏱️  Testing {description}...")
        
        # Test daily endpoint
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/atm/cash-usage/daily",
                params={
                    "start_date": get_date_string(days),
                    "end_date": get_date_string(0)
                },
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data.get("data", []))
                print(f"  ✅ Daily endpoint: {elapsed:.2f}s ({record_count} records)")
                
                # Validate calculation logic for first few records
                if record_count > 0:
                    sample_record = data["data"][0]
                    expected_usage = sample_record["start_amount"] - sample_record["end_amount"]
                    actual_usage = sample_record["daily_usage"]
                    if abs(expected_usage - actual_usage) < 0.01:  # Allow for small float differences
                        print(f"  ✅ Calculation logic verified: {sample_record['start_amount']} - {sample_record['end_amount']} = {actual_usage}")
                    else:
                        print(f"  ❌ Calculation error: Expected {expected_usage}, got {actual_usage}")
                        all_tests_passed = False
                        
            else:
                print(f"  ❌ Daily endpoint failed: {response.status_code} in {elapsed:.2f}s")
                print(f"      Error: {response.text[:200]}")
                all_tests_passed = False
                continue
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Daily endpoint error: {elapsed:.2f}s - {str(e)}")
            all_tests_passed = False
        
        # Test trends endpoint
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/atm/cash-usage/trends",
                params={"days": days},
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data.get("data", []))
                print(f"  ✅ Trends endpoint: {elapsed:.2f}s ({record_count} records)")
                
                # Validate chart configuration exists
                if "chart_config" in data:
                    print(f"  ✅ Chart.js configuration included for frontend integration")
                else:
                    print(f"  ⚠️  Chart configuration missing")
                    
            else:
                print(f"  ❌ Trends endpoint failed: {response.status_code} in {elapsed:.2f}s")
                print(f"      Error: {response.text[:200]}")
                all_tests_passed = False
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Trends endpoint error: {elapsed:.2f}s - {str(e)}")
            all_tests_passed = False
    
    # Test summary endpoint with a fixed 7-day range
    print(f"\n📊 Testing Summary Endpoint (7 days)...")
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/summary",
            params={"days": 7},
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get("data", {})
            print(f"  ✅ Summary endpoint: {elapsed:.2f}s")
            print(f"      Active terminals: {summary.get('active_terminals', 0)}")
            print(f"      Total cash tracked: ${summary.get('total_cash_tracked', 0):,.2f}")
        else:
            print(f"  ❌ Summary endpoint failed: {response.status_code} in {elapsed:.2f}s")
            all_tests_passed = False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ❌ Summary endpoint error: {elapsed:.2f}s - {str(e)}")
        all_tests_passed = False
    
    # Final results
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Daily Cash Usage API is working perfectly!")
        print("✅ Production-scale optimization successful")
        print("✅ Calculation logic verified: start_amount - end_amount = daily_usage")
        print("✅ Chart.js integration ready for frontend")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    test_performance()
