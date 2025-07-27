#!/usr/bin/env python3
"""
Test script to verify Decimal/JSON serialization fixes in cash usage endpoints
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime, timedelta

async def test_cash_usage_endpoints():
    """Test the fixed cash usage endpoints for Decimal serialization issues"""
    
    base_url = "http://localhost:8001"
    
    # Test endpoints with their expected JSON serialization
    endpoints = [
        {
            "name": "Daily Cash Usage",
            "url": f"{base_url}/api/v1/atm/cash-usage/daily",
            "params": {
                "start_date": "2025-07-25",
                "end_date": "2025-07-27",
                "terminal_ids": "147,169"
            }
        },
        {
            "name": "Cash Usage Summary", 
            "url": f"{base_url}/api/v1/atm/cash-usage/summary",
            "params": {
                "days": 7
            }
        },
        {
            "name": "Cash Usage Trends",
            "url": f"{base_url}/api/v1/atm/cash-usage/trends",
            "params": {
                "start_date": "2025-07-25",
                "end_date": "2025-07-27"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Decimal/JSON Serialization Fixes")
        print("=" * 50)
        
        for endpoint in endpoints:
            print(f"\n🔍 Testing: {endpoint['name']}")
            start_time = time.time()
            
            try:
                async with session.get(endpoint['url'], params=endpoint['params']) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        # Try to parse JSON - this will fail if there are Decimal serialization issues
                        data = await response.json()
                        
                        # Check for proper JSON serialization
                        json_test = json.dumps(data)  # This will fail if Decimals are present
                        
                        print(f"   ✅ Status: {response.status}")
                        print(f"   ✅ Response Time: {response_time:.2f}ms")
                        print(f"   ✅ JSON Serialization: PASSED")
                        print(f"   ✅ Data Size: {len(json_test):,} bytes")
                        
                        # Quick data validation
                        if isinstance(data, dict):
                            print(f"   ✅ Response Structure: Valid dictionary")
                            
                            # Check for specific data types in response
                            sample_data = str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                            if "Decimal" in sample_data:
                                print(f"   ⚠️  WARNING: Decimal objects may still be present")
                            else:
                                print(f"   ✅ No Decimal objects detected in response")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Status: {response.status}")
                        print(f"   ❌ Response Time: {response_time:.2f}ms")
                        print(f"   ❌ Error: {error_text[:200]}...")
                        
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Decode Error: {e}")
                print(f"   ❌ This indicates Decimal serialization issues still exist")
            except Exception as e:
                print(f"   ❌ Request Error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 Decimal Fix Testing Complete")

if __name__ == "__main__":
    asyncio.run(test_cash_usage_endpoints())
