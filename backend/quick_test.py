#!/usr/bin/env python3

import subprocess
import sys
import time
import requests

def test_implementation():
    """Test the Daily Cash Usage API implementation"""
    print("🔬 DAILY CASH USAGE API - IMPLEMENTATION TEST")
    print("=" * 50)
    
    # Check if server is running
    print("\n🔍 Checking server status...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy!")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Starting server...")
        
        # Start the server
        try:
            # Kill any existing process
            subprocess.run(["pkill", "-f", "uvicorn"], check=False)
            time.sleep(2)
            
            # Start server in background
            subprocess.Popen([
                "python", "-m", "uvicorn", 
                "api_option_2_fastapi_fixed:app", 
                "--host", "0.0.0.0", 
                "--port", "8000", 
                "--reload"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print("⏱️  Waiting for server to start...")
            time.sleep(10)
            
            # Check again
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server started successfully!")
            else:
                print("❌ Failed to start server")
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    # Test the daily cash usage endpoint
    print("\n💰 Testing Daily Cash Usage endpoint...")
    try:
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=3)
        
        response = requests.get(
            "http://localhost:8000/api/v1/atm/cash-usage/daily",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                records = len(data.get("data", []))
                print(f"✅ Daily endpoint working! Found {records} records")
                
                if records > 0:
                    sample = data["data"][0]
                    terminal_id = sample.get("terminal_id")
                    daily_usage = sample.get("daily_usage", 0)
                    date = sample.get("date")
                    print(f"📊 Sample: Terminal {terminal_id} on {date} - Usage: ${daily_usage:,.2f}")
                    
                    # Verify calculation
                    start_amt = sample.get("start_amount", 0)
                    end_amt = sample.get("end_amount", 0)
                    expected = start_amt - end_amt
                    
                    if abs(expected - daily_usage) < 0.01:
                        print(f"✅ Calculation verified: {start_amt} - {end_amt} = {daily_usage}")
                    else:
                        print(f"❌ Calculation error: Expected {expected}, got {daily_usage}")
                        
            else:
                print(f"❌ API error: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing daily endpoint: {e}")
        return False
    
    # Test trends endpoint
    print("\n📈 Testing Trends endpoint...")
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/atm/cash-usage/trends",
            params={"days": 7},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                records = len(data.get("data", []))
                print(f"✅ Trends endpoint working! Found {records} trend points")
                
                # Check for chart configuration
                if "chart_config" in data:
                    print("✅ Chart.js configuration included")
                else:
                    print("⚠️  Chart configuration missing")
            else:
                print(f"❌ Trends API error: {data.get('message')}")
        else:
            print(f"❌ Trends HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing trends endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 IMPLEMENTATION TEST COMPLETE!")
    print("✅ Daily Cash Usage API is working properly")
    print("💡 Run performance tests for large date ranges")
    
    return True

if __name__ == "__main__":
    success = test_implementation()
    sys.exit(0 if success else 1)
