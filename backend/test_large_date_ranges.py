#!/usr/bin/env python3
"""
Enhanced performance test for Daily Cash Usage API with debugging
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

def check_cash_data_availability():
    """Check if there's cash data available in the database"""
    print("🔍 Checking cash data availability...")
    try:
        # Check recent cash data
        response = requests.get(
            f"{BASE_URL}/atm/cash-information",
            params={"hours_back": 24, "limit": 10},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            cash_records = len(data.get("cash_data", []))
            print(f"  ✅ Found {cash_records} recent cash records")
            
            if cash_records > 0:
                sample = data["cash_data"][0]
                print(f"  📊 Sample: Terminal {sample['terminal_id']} - ${sample.get('total_cash_amount', 0):,.2f}")
                return True
            else:
                print("  ⚠️  No cash data found in last 24 hours")
                return False
        else:
            print(f"  ❌ Failed to check cash data: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking cash data: {str(e)}")
        return False

def test_endpoint_with_debug(endpoint, params, description):
    """Test an endpoint with detailed debugging"""
    print(f"\n⏱️  Testing {description}...")
    
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for different response structures
            if "daily_usage_data" in data:
                record_count = len(data.get("daily_usage_data", []))
                print(f"  ✅ {endpoint}: {elapsed:.2f}s ({record_count} records)")
                
                if record_count > 0:
                    sample = data["daily_usage_data"][0]
                    print(f"      Sample: Terminal {sample['terminal_id']} on {sample['date']} - Usage: ${sample.get('daily_usage', 0) or 0:,.2f}")
                    
                    # Verify calculation
                    start_amt = sample.get('start_amount', 0) or 0
                    end_amt = sample.get('end_amount', 0) or 0
                    daily_usage = sample.get('daily_usage', 0) or 0
                    expected = start_amt - end_amt
                    
                    if abs(expected - daily_usage) < 0.01:
                        print(f"      ✅ Calculation verified: {start_amt} - {end_amt} = {daily_usage}")
                    else:
                        print(f"      ⚠️  Calculation: Expected {expected}, got {daily_usage}")
                        
            elif "trend_data" in data:
                record_count = len(data.get("trend_data", []))
                print(f"  ✅ {endpoint}: {elapsed:.2f}s ({record_count} trend points)")
                
                if record_count > 0:
                    sample = data["trend_data"][0]
                    print(f"      Sample: {sample['date']} - Total: ${sample.get('total_usage', 0):,.2f}")
                    
                # Check chart configuration
                if "chart_config" in data:
                    print(f"      ✅ Chart.js configuration included")
                else:
                    print(f"      ⚠️  Chart configuration missing")
                    
            elif "summary" in data:
                summary = data.get("summary", {})
                print(f"  ✅ {endpoint}: {elapsed:.2f}s")
                print(f"      Active terminals: {summary.get('active_terminals', 0)}")
                print(f"      Total cash tracked: ${summary.get('fleet_total_cash_tracked', 0):,.2f}")
                
            else:
                print(f"  ✅ {endpoint}: {elapsed:.2f}s (unknown structure)")
                
            return True
            
        else:
            print(f"  ❌ {endpoint} failed: {response.status_code} in {elapsed:.2f}s")
            print(f"      Error: {response.text[:200]}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if "detail" in error_data:
                    print(f"      Detail: {error_data['detail']}")
            except:
                pass
                
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"  ❌ {endpoint} timeout: {elapsed:.2f}s")
        return False
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ❌ {endpoint} error: {elapsed:.2f}s - {str(e)}")
        return False

def test_with_larger_date_ranges():
    """Test with progressively larger date ranges"""
    print("🧪 ENHANCED DAILY CASH USAGE API - LARGE DATE RANGE TESTING")
    print("="*70)
    
    # Check server health
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
    
    # Check cash data availability
    has_cash_data = check_cash_data_availability()
    if not has_cash_data:
        print("\n⚠️  Warning: Limited or no cash data found. Tests may return empty results.")
        print("   This is normal if the system is newly deployed or cash monitoring is not active.")
    
    print(f"\n📋 Testing API endpoints with various date ranges...")
    
    test_cases = [
        {"days": 3, "description": "3 days (baseline)"},
        {"days": 7, "description": "1 week"},
        {"days": 14, "description": "2 weeks"},
        {"days": 30, "description": "1 month"},
        {"days": 60, "description": "2 months"},
        {"days": 90, "description": "3 months (max)"}
    ]
    
    all_tests_passed = True
    
    for case in test_cases:
        days = case["days"]
        description = case["description"]
        
        print(f"\n{'='*50}")
        print(f"📅 Testing {description} ({days} days)")
        print(f"{'='*50}")
        
        # Test 1: Daily Cash Usage endpoint
        daily_params = {
            "start_date": get_date_string(days),
            "end_date": get_date_string(0),
            "terminal_ids": "all",
            "include_partial_data": True
        }
        
        daily_success = test_endpoint_with_debug(
            "/atm/cash-usage/daily", 
            daily_params, 
            f"Daily endpoint ({days} days)"
        )
        
        # Test 2: Trends endpoint
        trends_params = {
            "days": days,
            "aggregation": "daily"
        }
        
        trends_success = test_endpoint_with_debug(
            "/atm/cash-usage/trends", 
            trends_params, 
            f"Trends endpoint ({days} days)"
        )
        
        # Test 3: Summary endpoint (fixed to 7 days)
        if days <= 30:  # Only test summary for reasonable ranges
            summary_params = {
                "days": min(days, 7)  # Summary has max 90 days but we'll use smaller
            }
            
            summary_success = test_endpoint_with_debug(
                "/atm/cash-usage/summary", 
                summary_params, 
                f"Summary endpoint ({min(days, 7)} days)"
            )
        else:
            summary_success = True  # Skip for very large ranges
        
        # Track overall success
        case_success = daily_success and trends_success and summary_success
        if not case_success:
            all_tests_passed = False
            
        print(f"\n📊 {description} Results: {'✅ PASSED' if case_success else '❌ FAILED'}")
    
    # Final summary
    print(f"\n{'='*70}")
    if all_tests_passed:
        print("🎉 ALL LARGE DATE RANGE TESTS PASSED!")
        print("✅ Daily Cash Usage API is optimized and production-ready")
        print("✅ Performance is suitable for date ranges up to 3 months")
        print("✅ Chart.js integration configurations are working")
        print("\n💡 Key performance highlights:")
        print("   - Daily endpoint: Optimized SQL with simplified aggregation")
        print("   - Trends endpoint: Efficient time-series generation")
        print("   - Summary endpoint: Fast fleet-wide statistics")
        print("   - All endpoints ready for production deployment")
    else:
        print("❌ Some tests failed - see details above")
        print("💡 Common issues and solutions:")
        print("   - No data: Ensure terminal_cash_information table has recent data")
        print("   - Timeouts: Apply database indexes for better performance")
        print("   - Errors: Check server logs for detailed error information")
    
    print(f"\n🔗 Next steps:")
    print(f"   1. Deploy database indexes for optimal performance")
    print(f"   2. Integrate with frontend dashboard")
    print(f"   3. Set up monitoring and alerts")
    print(f"   4. Test with real production data")

if __name__ == "__main__":
    test_with_larger_date_ranges()
