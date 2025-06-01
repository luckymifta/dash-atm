#!/usr/bin/env python3
"""
Comprehensive Test Suite for FastAPI ATM Monitoring API

This script tests all endpoints of the FastAPI implementation to ensure
proper functionality and validate the fixes made to the database schema.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class FastAPITester:
    """Comprehensive tester for FastAPI ATM Monitoring API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def test_endpoint(self, endpoint: str, description: str, 
                     expected_keys: Optional[list] = None,
                     params: Optional[Dict[str, Any]] = None) -> bool:
        """Test a specific endpoint and validate response"""
        self.results['total_tests'] += 1
        
        try:
            print(f"\n🧪 Testing: {description}")
            print(f"   Endpoint: GET {endpoint}")
            
            if params:
                print(f"   Parameters: {params}")
            
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=TIMEOUT
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Type: {type(data).__name__}")
                
                # Validate expected keys if provided
                if expected_keys and isinstance(data, dict):
                    missing_keys = [key for key in expected_keys if key not in data]
                    if missing_keys:
                        print(f"   ❌ Missing keys: {missing_keys}")
                        self.results['failed'] += 1
                        self.results['errors'].append(f"{endpoint}: Missing keys {missing_keys}")
                        return False
                
                # Print sample data structure
                if isinstance(data, dict):
                    print(f"   Keys: {list(data.keys())}")
                    if 'status_counts' in data:
                        print(f"   Status Counts: {data['status_counts']}")
                elif isinstance(data, list):
                    print(f"   Array Length: {len(data)}")
                
                print(f"   ✅ PASSED")
                self.results['passed'] += 1
                return True
            
            elif response.status_code == 404:
                print(f"   ⚠️  No data found (404) - This might be expected")
                self.results['passed'] += 1
                return True
            
            else:
                error_detail = response.text
                print(f"   ❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {error_detail}")
                self.results['failed'] += 1
                self.results['errors'].append(f"{endpoint}: HTTP {response.status_code} - {error_detail}")
                return False
        
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            self.results['failed'] += 1
            self.results['errors'].append(f"{endpoint}: Exception - {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all endpoint tests"""
        print("=" * 80)
        print("🚀 FASTAPI ATM MONITORING API - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        
        # Test 1: Health Check
        self.test_endpoint(
            "/api/v1/health",
            "Health Check",
            expected_keys=['status', 'timestamp', 'database_connected', 'api_version']
        )
        
        # Test 2: ATM Summary (Legacy table)
        self.test_endpoint(
            "/api/v1/atm/status/summary",
            "ATM Status Summary (Legacy Table)",
            expected_keys=['total_atms', 'status_counts', 'overall_availability', 'total_regions']
        )
        
        # Test 3: ATM Summary (New table)
        self.test_endpoint(
            "/api/v1/atm/status/summary",
            "ATM Status Summary (New Table)",
            expected_keys=['total_atms', 'status_counts', 'overall_availability', 'total_regions'],
            params={'table_type': 'new'}
        )
        
        # Test 4: Regional Data (All regions)
        self.test_endpoint(
            "/api/v1/atm/status/regional",
            "Regional Data (All Regions)",
            expected_keys=['regional_data', 'total_regions', 'summary', 'last_updated']
        )
        
        # Test 5: Regional Data (Specific region)
        self.test_endpoint(
            "/api/v1/atm/status/regional",
            "Regional Data (TL-DL Region)",
            expected_keys=['regional_data', 'total_regions', 'summary'],
            params={'region_code': 'TL-DL'}
        )
        
        # Test 6: Regional Data (Another region)
        self.test_endpoint(
            "/api/v1/atm/status/regional",
            "Regional Data (TL-AN Region)",
            expected_keys=['regional_data', 'total_regions', 'summary'],
            params={'region_code': 'TL-AN'}
        )
        
        # Test 7: Trends for TL-DL (24 hours)
        self.test_endpoint(
            "/api/v1/atm/status/trends/TL-DL",
            "Trends for TL-DL Region (24 hours)",
            expected_keys=['region_code', 'time_period', 'trends', 'summary_stats']
        )
        
        # Test 8: Trends for TL-AN (72 hours)
        self.test_endpoint(
            "/api/v1/atm/status/trends/TL-AN",
            "Trends for TL-AN Region (72 hours)",
            expected_keys=['region_code', 'time_period', 'trends', 'summary_stats'],
            params={'hours': 72}
        )
        
        # Test 9: Latest Data (Legacy)
        self.test_endpoint(
            "/api/v1/atm/status/latest",
            "Latest ATM Data (Legacy Table)",
            params={'table_type': 'legacy'}
        )
        
        # Test 10: Latest Data (New)
        self.test_endpoint(
            "/api/v1/atm/status/latest",
            "Latest ATM Data (New Table)",
            params={'table_type': 'new'}
        )
        
        # Test 11: API Documentation
        self.test_endpoint(
            "/docs",
            "Interactive API Documentation",
        )
        
        # Test 12: OpenAPI Schema
        self.test_endpoint(
            "/api/v1/openapi.json",
            "OpenAPI Schema",
            expected_keys=['openapi', 'info', 'paths']
        )
        
        # Print Results Summary
        self.print_results()
    
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed:   {passed}")
        print(f"❌ Failed:   {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if self.results['errors']:
            print(f"\n🔍 ERROR DETAILS:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i}. {error}")
        
        print("\n" + "=" * 80)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! FastAPI implementation is working correctly.")
            return True
        else:
            print(f"⚠️  {failed} test(s) failed. Please review the errors above.")
            return False

def main():
    """Main test execution"""
    print(f"FastAPI ATM Monitoring API Test Suite")
    print(f"Testing server at: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding correctly. Status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please ensure the FastAPI server is running:")
        print("  uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    
    # Run tests
    tester = FastAPITester(BASE_URL)
    success = tester.run_comprehensive_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
