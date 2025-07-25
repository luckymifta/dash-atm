#!/usr/bin/env python3
"""
Test script for the new Daily Cash Usage API endpoints

This script demonstrates how to use the new cash usage calculation endpoints
to get daily terminal cash usage data and create line charts.

Usage:
python test_cash_usage_api.py

Make sure the FastAPI server is running:
uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000
"""

import requests
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import sys

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

async def make_request(endpoint: str) -> Dict[Any, Any]:
    """Make async request to API endpoint"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        print(f"Request error: {str(e)}")
        return {}

def test_api_connection():
    """Test if the API is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API connection successful")
            health_data = response.json()
            print(f"   Database connected: {health_data.get('database_connected', 'Unknown')}")
            return True
        else:
            print(f"❌ API connection failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection error: {e}")
        return False

def test_daily_cash_usage(start_date: str, end_date: str):
    """Test the daily cash usage calculation endpoint"""
    print(f"\n🧮 Testing Daily Cash Usage Calculation ({start_date} to {end_date})")
    
    try:
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'terminal_ids': 'all',
            'include_partial_data': True
        }
        
        response = requests.get(f"{BASE_URL}/atm/cash-usage/daily", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Daily cash usage data retrieved successfully")
            print(f"   📊 Records found: {len(data['daily_usage_data'])}")
            print(f"   🏧 Terminals covered: {data['terminal_count']}")
            print(f"   📅 Days analyzed: {data['date_range']['days_covered']}")
            
            # Summary statistics
            summary = data['summary_stats']
            print(f"   💰 Total usage: ${summary['total_usage']:,.2f}")
            print(f"   📈 Average daily usage: ${summary['avg_daily_usage']:,.2f}")
            print(f"   📊 Data quality breakdown:")
            print(f"      - Complete records: {summary['complete_records']}")
            print(f"      - Partial records: {summary['partial_records']}")
            print(f"      - Missing records: {summary['missing_records']}")
            
            # Show sample records
            if data['daily_usage_data']:
                print(f"\n   📋 Sample records (first 3):")
                for i, record in enumerate(data['daily_usage_data'][:3]):
                    usage = record['daily_usage']
                    usage_str = f"${usage:.2f}" if usage is not None else "N/A"
                    print(f"      {i+1}. {record['terminal_id']} on {record['date']}: {usage_str} ({record['data_quality']})")
            
            return data
        else:
            print(f"❌ Daily cash usage request failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Daily cash usage request error: {e}")
        return None

def test_cash_usage_trends(days: int = 30):
    """Test the cash usage trends endpoint for line chart data"""
    print(f"\n📈 Testing Cash Usage Trends (last {days} days)")
    
    try:
        params = {
            'days': days,
            'aggregation': 'daily'
        }
        
        response = requests.get(f"{BASE_URL}/atm/cash-usage/trends", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Cash usage trends data retrieved successfully")
            print(f"   📊 Data points: {len(data['trend_data'])}")
            print(f"   📅 Date range: {data['date_range']['start_date']} to {data['date_range']['end_date']}")
            
            # Summary statistics
            summary = data['summary_stats']
            print(f"   💰 Total usage in period: ${summary['total_usage']:,.2f}")
            print(f"   📈 Average daily usage: ${summary['avg_daily_usage']:,.2f}")
            if summary['peak_usage_date']:
                print(f"   🏆 Peak usage: ${summary['peak_usage_amount']:,.2f} on {summary['peak_usage_date']}")
            
            # Chart configuration
            chart_config = data['chart_config']
            print(f"   📊 Chart type: {chart_config['chart_type']}")
            print(f"   📏 X-axis: {chart_config['x_axis']['title']} ({chart_config['x_axis']['type']})")
            print(f"   📏 Y-axis: {chart_config['y_axis']['title']} ({chart_config['y_axis']['type']})")
            
            # Show sample data points
            if data['trend_data']:
                print(f"\n   📋 Sample trend points (first 5):")
                for i, point in enumerate(data['trend_data'][:5]):
                    print(f"      {i+1}. {point['date']}: ${point['total_usage']:,.2f} total, "
                          f"${point['average_usage_per_terminal']:,.2f} avg/terminal "
                          f"({point['terminal_count']} terminals)")
            
            return data
        else:
            print(f"❌ Cash usage trends request failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cash usage trends request error: {e}")
        return None

def test_terminal_specific_usage(terminal_id: str, days: int = 30):
    """Test the terminal-specific cash usage history endpoint"""
    print(f"\n🏧 Testing Terminal-Specific Cash Usage History ({terminal_id}, last {days} days)")
    
    try:
        params = {
            'days': days,
            'include_raw_readings': False
        }
        
        response = requests.get(f"{BASE_URL}/atm/{terminal_id}/cash-usage/history", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Terminal {terminal_id} cash usage history retrieved successfully")
            print(f"   📊 Data points: {len(data['trend_data'])}")
            
            if data['trend_data']:
                # Calculate some basic statistics
                usages = [point['total_usage'] for point in data['trend_data'] if point['total_usage'] > 0]
                if usages:
                    avg_usage = sum(usages) / len(usages)
                    max_usage = max(usages)
                    min_usage = min(usages)
                    
                    print(f"   💰 Average daily usage: ${avg_usage:,.2f}")
                    print(f"   📈 Maximum daily usage: ${max_usage:,.2f}")
                    print(f"   📉 Minimum daily usage: ${min_usage:,.2f}")
                
                # Show last few data points
                print(f"\n   📋 Recent usage (last 5 days):")
                for point in data['trend_data'][-5:]:
                    print(f"      {point['date']}: ${point['total_usage']:,.2f}")
            
            return data
        else:
            print(f"❌ Terminal cash usage request failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Terminal cash usage request error: {e}")
        return None

def test_cash_usage_summary(days: int = 7):
    """Test the cash usage summary endpoint"""
    print(f"\n📊 Testing Cash Usage Summary (last {days} days)")
    
    try:
        params = {'days': days}
        
        response = requests.get(f"{BASE_URL}/atm/cash-usage/summary", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Cash usage summary retrieved successfully")
            
            summary = data['summary']
            print(f"   🏧 Active terminals: {summary['active_terminals']}")
            print(f"   💰 Fleet total usage: ${summary['fleet_total_usage']:,.2f}")
            print(f"   📈 Fleet average daily usage: ${summary['fleet_avg_daily_usage']:,.2f}")
            print(f"   📅 Analysis period: {summary['period_start']} to {summary['period_end']}")
            
            # Top terminals
            if data['top_terminals']:
                print(f"\n   🏆 Top performing terminals:")
                for i, terminal in enumerate(data['top_terminals'][:3], 1):
                    location = terminal['location'] or 'Unknown location'
                    print(f"      {i}. {terminal['terminal_id']} ({location}): ${terminal['total_usage']:,.2f}")
            
            # Insights
            if data['insights']:
                print(f"\n   💡 Key insights:")
                for insight in data['insights']:
                    print(f"      • {insight}")
            
            return data
        else:
            print(f"❌ Cash usage summary request failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cash usage summary request error: {e}")
        return None

def get_sample_terminal_id():
    """Get a sample terminal ID for testing"""
    try:
        response = requests.get(f"{BASE_URL}/atm/terminals", timeout=10)
        if response.status_code == 200:
            terminals = response.json()
            if terminals and 'terminals' in terminals and terminals['terminals']:
                return terminals['terminals'][0]['terminal_id']
    except:
        pass
    
    # Fallback to a common terminal ID pattern
    return "ATM001"  # You may need to adjust this based on your actual terminal IDs

async def main():
    """Main test function"""
    print("🚀 Testing Daily Cash Usage API Endpoints")
    print("=" * 50)
    
    # Test API connection first
    if not test_api_connection():
        print("❌ Cannot proceed without API connection")
        sys.exit(1)
    
    # Calculate date ranges for testing
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Test 1: Daily cash usage calculation
    daily_usage_data = test_daily_cash_usage(start_date_str, end_date_str)
    
    # Test 2: Cash usage trends for line charts
    trends_data = test_cash_usage_trends(30)
    
    # Test 3: Terminal-specific usage history
    sample_terminal = get_sample_terminal_id()
    terminal_data = test_terminal_specific_usage(sample_terminal, 30)
    
    # Test 4: Cash usage summary
    summary_data = test_cash_usage_summary(7)
    
    print("\n" + "=" * 50)
    print("🎉 API Testing Complete!")
    
    # Summary of results
    tests_passed = sum([
        daily_usage_data is not None,
        trends_data is not None,
        terminal_data is not None,
        summary_data is not None
    ])
    
    print(f"✅ Tests passed: {tests_passed}/4")
    
    if tests_passed == 4:
        print("\n💡 Next steps for frontend integration:")
        print("   1. Use /atm/cash-usage/trends for line chart data")
        print("   2. Use /atm/cash-usage/daily for detailed analysis")
        print("   3. Use /atm/cash-usage/summary for dashboard widgets")
        print("   4. Use /atm/{terminal_id}/cash-usage/history for individual terminal charts")
        print("\n📊 Chart configuration is included in API responses for easy frontend integration!")
    else:
        print(f"⚠️  Some tests failed. Check the API server logs for details.")

async def test_performance_large_date_ranges():
    """Test the API with large date ranges to verify optimization"""
    print("\n" + "="*80)
    print("PERFORMANCE TEST - LARGE DATE RANGES")
    print("="*80)
    
    test_cases = [
        {"days": 7, "description": "1 week"},
        {"days": 14, "description": "2 weeks"},
        {"days": 30, "description": "1 month"},
        {"days": 60, "description": "2 months"},
        {"days": 90, "description": "3 months"}
    ]
    
    for case in test_cases:
        days = case["days"]
        description = case["description"]
        
        print(f"\nTesting {description} ({days} days)...")
        
        try:
            start_time = time.time()
            
            # Test daily cash usage endpoint
            response = await make_request(
                f"/api/v1/atm/cash-usage/daily?start_date={get_date_string(days)}&end_date={get_date_string(0)}"
            )
            
            daily_time = time.time() - start_time
            
            if response and response.get("status") == "success":
                data_count = len(response.get("data", []))
                print(f"  ✅ Daily endpoint: {daily_time:.2f}s ({data_count} records)")
            else:
                print(f"  ❌ Daily endpoint failed: {daily_time:.2f}s")
                continue
            
            # Test trends endpoint
            start_time = time.time()
            response = await make_request(f"/api/v1/atm/cash-usage/trends?days={days}")
            trends_time = time.time() - start_time
            
            if response and response.get("status") == "success":
                data_count = len(response.get("data", []))
                print(f"  ✅ Trends endpoint: {trends_time:.2f}s ({data_count} records)")
            else:
                print(f"  ❌ Trends endpoint failed: {trends_time:.2f}s")
            
            # Test summary endpoint  
            start_time = time.time()
            response = await make_request(f"/api/v1/atm/cash-usage/summary?days={days}")
            summary_time = time.time() - start_time
            
            if response and response.get("status") == "success":
                print(f"  ✅ Summary endpoint: {summary_time:.2f}s")
            else:
                print(f"  ❌ Summary endpoint failed: {summary_time:.2f}s")
                
        except Exception as e:
            print(f"  ❌ Error testing {description}: {str(e)}")
    
    print("\nPerformance test completed!")

def get_date_string(days_ago):
    """Get date string for days ago"""
    date = datetime.now().date() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--performance":
        asyncio.run(test_performance_large_date_ranges())
    else:
        asyncio.run(main())
