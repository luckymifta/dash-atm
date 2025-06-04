#!/usr/bin/env python3
"""
Comprehensive FastAPI ATM API Test Suite - Final Validation

This script tests all endpoints with both legacy and new table types
to ensure complete functionality after fixing the "new" table support.

Author: ATM Monitoring System
Created: 2025-05-31
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0,
    "details": []
}

def log_test(test_name: str, success: bool, details: str = "", response_data: Any = None):
    """Log test results"""
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
        status = "✅ PASS"
    else:
        test_results["failed"] += 1
        status = "❌ FAIL"
    
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")
    
    test_results["details"].append({
        "test": test_name,
        "success": success,
        "details": details,
        "response_data": response_data
    })

def test_endpoint(endpoint: str, expected_status: int = 200, test_name: str = None) -> Dict[str, Any]:
    """Test an endpoint and return response data"""
    if not test_name:
        test_name = endpoint
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        
        if response.status_code == expected_status:
            try:
                data = response.json()
                log_test(test_name, True, f"Status: {response.status_code}", data)
                return data
            except json.JSONDecodeError:
                log_test(test_name, False, f"Invalid JSON response (Status: {response.status_code})")
                return {}
        else:
            log_test(test_name, False, f"Expected {expected_status}, got {response.status_code}")
            return {}
    
    except requests.exceptions.RequestException as e:
        log_test(test_name, False, f"Request failed: {e}")
        return {}

def main():
    """Run comprehensive test suite"""
    print("=" * 80)
    print("🚀 FastAPI ATM API - Final Comprehensive Test Suite")
    print("=" * 80)
    print(f"Testing API at: {BASE_URL}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Health Check
    print("📋 1. HEALTH CHECK")
    print("-" * 40)
    health_data = test_endpoint("/api/v1/health", test_name="Health Check")
    if health_data and health_data.get("database_connected"):
        print(f"    Database: Connected ✅")
    print()

    # 2. Summary Endpoints - Both Table Types
    print("📊 2. SUMMARY ENDPOINTS")
    print("-" * 40)
    
    # Legacy table
    legacy_summary = test_endpoint("/api/v1/atm/status/summary?table_type=legacy", 
                                  test_name="Summary (Legacy Table)")
    if legacy_summary:
        print(f"    Total ATMs: {legacy_summary.get('total_atms', 'N/A')}")
        print(f"    Availability: {legacy_summary.get('overall_availability', 'N/A')}%")
        print(f"    Data Source: {legacy_summary.get('data_source', 'N/A')}")
    
    # New table
    new_summary = test_endpoint("/api/v1/atm/status/summary?table_type=new", 
                               test_name="Summary (New Table)")
    if new_summary:
        print(f"    Total ATMs: {new_summary.get('total_atms', 'N/A')}")
        print(f"    Availability: {new_summary.get('overall_availability', 'N/A')}%")
        print(f"    Data Source: {new_summary.get('data_source', 'N/A')}")
    print()

    # 3. Regional Endpoints - Both Table Types
    print("🌍 3. REGIONAL ENDPOINTS")
    print("-" * 40)
    
    # Legacy regional
    legacy_regional = test_endpoint("/api/v1/atm/status/regional?table_type=legacy", 
                                   test_name="Regional (Legacy Table)")
    if legacy_regional:
        regions = legacy_regional.get('regional_data', [])
        print(f"    Regions found: {len(regions)}")
        for region in regions:
            print(f"    - {region.get('region_code')}: {region.get('availability_percentage')}% ({region.get('health_status')})")
    
    # New regional
    new_regional = test_endpoint("/api/v1/atm/status/regional?table_type=new", 
                                test_name="Regional (New Table)")
    if new_regional:
        regions = new_regional.get('regional_data', [])
        print(f"    Regions found: {len(regions)}")
        for region in regions:
            print(f"    - {region.get('region_code')}: {region.get('availability_percentage')}% ({region.get('health_status')})")
    print()

    # 4. Specific Region Tests
    print("🎯 4. SPECIFIC REGION TESTS")
    print("-" * 40)
    
    test_region = "TL-DL"
    
    # Legacy specific region
    legacy_specific = test_endpoint(f"/api/v1/atm/status/regional?region_code={test_region}&table_type=legacy",
                                   test_name=f"Specific Region {test_region} (Legacy)")
    
    # New specific region
    new_specific = test_endpoint(f"/api/v1/atm/status/regional?region_code={test_region}&table_type=new",
                                test_name=f"Specific Region {test_region} (New)")
    print()

    # 5. Trends Endpoints - Both Table Types
    print("📈 5. TRENDS ENDPOINTS")
    print("-" * 40)
    
    # Legacy trends
    legacy_trends = test_endpoint(f"/api/v1/atm/status/trends/{test_region}?table_type=legacy&hours=24",
                                 test_name=f"Trends {test_region} (Legacy)")
    if legacy_trends:
        trends = legacy_trends.get('trends', [])
        print(f"    Data points: {len(trends)}")
        stats = legacy_trends.get('summary_stats', {})
        print(f"    Avg availability: {stats.get('avg_availability', 'N/A')}%")
    
    # New trends
    new_trends = test_endpoint(f"/api/v1/atm/status/trends/{test_region}?table_type=new&hours=24",
                              test_name=f"Trends {test_region} (New)")
    if new_trends:
        trends = new_trends.get('trends', [])
        print(f"    Data points: {len(trends)}")
        stats = new_trends.get('summary_stats', {})
        print(f"    Avg availability: {stats.get('avg_availability', 'N/A')}%")
    print()

    # 6. Error Handling Tests
    print("⚠️ 6. ERROR HANDLING TESTS")
    print("-" * 40)
    
    # Invalid region
    test_endpoint("/api/v1/atm/status/regional?region_code=INVALID", 404, 
                 "Invalid Region (Expected 404)")
    
    # Invalid trends region
    test_endpoint("/api/v1/atm/status/trends/INVALID", 404, 
                 "Invalid Trends Region (Expected 404)")
    print()

    # 7. Latest Data Endpoint
    print("🔄 7. LATEST DATA ENDPOINT")
    print("-" * 40)
    
    # Both tables
    latest_both = test_endpoint("/api/v1/atm/status/latest?table_type=both",
                               test_name="Latest Data (Both Tables)")
    if latest_both:
        sources = latest_both.get('data_sources', [])
        print(f"    Data sources: {len(sources)}")
        for source in sources:
            print(f"    - {source.get('table')}: {source.get('records')} records")
    
    # Legacy only
    latest_legacy = test_endpoint("/api/v1/atm/status/latest?table_type=legacy",
                                 test_name="Latest Data (Legacy Only)")
    
    # New only
    latest_new = test_endpoint("/api/v1/atm/status/latest?table_type=new",
                              test_name="Latest Data (New Only)")
    print()

    # 8. API Documentation
    print("📚 8. API DOCUMENTATION")
    print("-" * 40)
    
    # OpenAPI Schema
    test_endpoint("/api/v1/openapi.json", test_name="OpenAPI Schema")
    
    # Documentation pages (these return HTML, so we expect different handling)
    try:
        docs_response = requests.get(f"{BASE_URL}/docs")
        if docs_response.status_code == 200:
            log_test("Interactive Documentation (/docs)", True, f"Status: {docs_response.status_code}")
        else:
            log_test("Interactive Documentation (/docs)", False, f"Status: {docs_response.status_code}")
    except Exception as e:
        log_test("Interactive Documentation (/docs)", False, f"Error: {e}")
    print()

    # 9. Performance & Data Consistency
    print("⚡ 9. PERFORMANCE & CONSISTENCY")
    print("-" * 40)
    
    # Compare legacy vs new table results
    if legacy_summary and new_summary:
        legacy_total = legacy_summary.get('total_atms', 0)
        new_total = new_summary.get('total_atms', 0)
        
        if abs(legacy_total - new_total) <= 1:  # Allow small differences
            log_test("Data Consistency Check", True, 
                    f"Legacy: {legacy_total} ATMs, New: {new_total} ATMs (✓ Consistent)")
        else:
            log_test("Data Consistency Check", False, 
                    f"Legacy: {legacy_total} ATMs, New: {new_total} ATMs (✗ Inconsistent)")
    
    # Test response times
    start_time = time.time()
    test_endpoint("/api/v1/atm/status/summary")
    response_time = (time.time() - start_time) * 1000
    
    if response_time < 1000:  # Less than 1 second
        log_test("Response Time Check", True, f"{response_time:.2f}ms (✓ Fast)")
    else:
        log_test("Response Time Check", False, f"{response_time:.2f}ms (✗ Slow)")
    print()

    # Final Results
    print("=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']} ✅")
    print(f"Failed: {test_results['failed']} ❌")
    
    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! FastAPI implementation is fully functional!")
        print("✅ Both legacy and new table types are working correctly")
        print("✅ All endpoints are responding properly")
        print("✅ Error handling is working as expected")
    else:
        print(f"\n⚠️ {test_results['failed']} test(s) failed. Review the details above.")
    
    print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
