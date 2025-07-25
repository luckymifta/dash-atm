#!/usr/bin/env python3
"""
Comprehensive test for Daily Cash Usage API functionality
"""

import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def get_date_string(days_ago):
    """Get date string for days ago"""
    date = datetime.now().date() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d")

def test_individual_terminal():
    """Test individual terminal functionality"""
    print("\n🏧 Testing Individual Terminal History...")
    print("="*50)
    
    # Test with known terminals from previous testing
    test_terminals = ["147", "2605", "93"]
    
    for terminal_id in test_terminals:
        print(f"\n📊 Testing Terminal {terminal_id}...")
        
        start_time = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/atm/{terminal_id}/cash-usage/history",
                params={"days": 7},
                timeout=30
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data.get("data", []))
                print(f"  ✅ Terminal {terminal_id}: {elapsed:.2f}s ({record_count} days)")
                
                # Show sample calculation if data exists
                if record_count > 0:
                    sample = data["data"][0]
                    print(f"      Sample: {sample['date']} - Usage: ${sample.get('daily_usage', 0):,.2f}")
                    
            else:
                print(f"  ❌ Terminal {terminal_id} failed: {response.status_code} in {elapsed:.2f}s")
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Terminal {terminal_id} error: {elapsed:.2f}s - {str(e)}")

def test_data_validation():
    """Test data validation and edge cases"""
    print("\n🔍 Testing Data Validation...")
    print("="*40)
    
    # Test invalid date range
    print("\n⚠️  Testing invalid date ranges...")
    try:
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/daily",
            params={
                "start_date": "2025-12-31",  # Future date
                "end_date": "2025-01-01"     # End before start
            },
            timeout=15
        )
        
        if response.status_code == 422:
            print("  ✅ Correctly rejected invalid date range")
        else:
            print(f"  ⚠️  Unexpected response for invalid dates: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error testing invalid dates: {str(e)}")
    
    # Test very large days parameter
    print("\n📅 Testing edge case: very large days parameter...")
    try:
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/trends",
            params={"days": 500},  # Larger than allowed
            timeout=15
        )
        
        if response.status_code == 422:
            print("  ✅ Correctly rejected days > 365")
        else:
            print(f"  ⚠️  Unexpected response for large days: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error testing large days: {str(e)}")

def test_chart_integration():
    """Test Chart.js integration features"""
    print("\n📈 Testing Chart.js Integration...")
    print("="*45)
    
    try:
        response = requests.get(
            f"{BASE_URL}/atm/cash-usage/trends",
            params={"days": 7},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for chart configuration
            if "chart_config" in data:
                chart_config = data["chart_config"]
                print("  ✅ Chart configuration present")
                
                # Validate chart structure
                required_fields = ["type", "data", "options"]
                for field in required_fields:
                    if field in chart_config:
                        print(f"      ✅ {field} configuration found")
                    else:
                        print(f"      ❌ Missing {field} configuration")
                
                # Check data structure
                if "data" in chart_config and "datasets" in chart_config["data"]:
                    datasets = chart_config["data"]["datasets"]
                    print(f"      ✅ Chart datasets: {len(datasets)} series")
                    
            else:
                print("  ❌ Chart configuration missing")
                
        else:
            print(f"  ❌ Failed to get trends data: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error testing chart integration: {str(e)}")

def main():
    """Run comprehensive tests"""
    print("🧪 COMPREHENSIVE DAILY CASH USAGE API TEST")
    print("="*60)
    
    # Check server health first
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy and ready for testing")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {str(e)}")
        return
    
    # Run all test suites
    test_individual_terminal()
    test_data_validation()
    test_chart_integration()
    
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE TESTING COMPLETE!")
    print("💡 Next step: Run performance tests with 'python test_performance.py'")

if __name__ == "__main__":
    main()
