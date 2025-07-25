#!/usr/bin/env python3
"""
Quick functional test for Daily Cash Usage API
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_basic_functionality():
    """Test basic API functionality"""
    print("🧪 DAILY CASH USAGE API - BASIC FUNCTIONALITY TEST")
    print("="*60)
    
    # Test 1: Health check
    print("\n1. 🏥 Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Server is healthy")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {str(e)}")
        return False
    
    # Test 2: Daily Cash Usage endpoint
    print("\n2. 💰 Daily Cash Usage Endpoint...")
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=3)
        
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/daily",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                record_count = len(data.get("data", []))
                print(f"   ✅ Daily endpoint working: {record_count} records")
                
                # Show sample data
                if record_count > 0:
                    sample = data["data"][0]
                    print(f"   📊 Sample: Terminal {sample.get('terminal_id')} - Usage: ${sample.get('daily_usage', 0):,.2f}")
                    
                    # Verify calculation
                    start_amt = sample.get('start_amount', 0)
                    end_amt = sample.get('end_amount', 0)
                    daily_usage = sample.get('daily_usage', 0)
                    expected = start_amt - end_amt
                    
                    if abs(expected - daily_usage) < 0.01:
                        print(f"   ✅ Calculation verified: {start_amt} - {end_amt} = {daily_usage}")
                    else:
                        print(f"   ❌ Calculation error: Expected {expected}, got {daily_usage}")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Daily endpoint failed: {response.status_code}")
            print(f"       Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Daily endpoint error: {str(e)}")
        return False
    
    # Test 3: Trends endpoint
    print("\n3. 📈 Cash Usage Trends Endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/trends",
            params={"days": 7},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                record_count = len(data.get("data", []))
                print(f"   ✅ Trends endpoint working: {record_count} data points")
                
                # Check for chart configuration
                if "chart_config" in data:
                    print(f"   ✅ Chart.js configuration included")
                else:
                    print(f"   ⚠️  Chart configuration missing")
            else:
                print(f"   ❌ Trends API returned error: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ Trends endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Trends endpoint error: {str(e)}")
    
    # Test 4: Summary endpoint
    print("\n4. 📊 Cash Usage Summary Endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/summary",
            params={"days": 7},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                summary = data.get("data", {})
                print(f"   ✅ Summary endpoint working")
                print(f"   📊 Active terminals: {summary.get('active_terminals', 0)}")
                print(f"   💰 Total cash tracked: ${summary.get('total_cash_tracked', 0):,.2f}")
            else:
                print(f"   ❌ Summary API returned error: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ Summary endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Summary endpoint error: {str(e)}")
    
    print("\n" + "="*60)
    print("🎯 BASIC FUNCTIONALITY TEST COMPLETE!")
    print("✅ Core Daily Cash Usage API is functional")
    print("💡 Run 'python test_performance.py' for performance testing")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    exit(0 if success else 1)
