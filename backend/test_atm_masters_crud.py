#!/usr/bin/env python3
"""
Test Script for ATM Masters CRUD API Endpoints
Demonstrates all CRUD operations on the atm_masters table
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ATM_MASTERS_ENDPOINT = f"{API_BASE_URL}/atm-masters"

def print_response(operation, response):
    """Print formatted API response"""
    print(f"\n{'='*60}")
    print(f"🔧 {operation}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200 or response.status_code == 201:
        print("✅ SUCCESS")
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text)
    else:
        print("❌ ERROR")
        print(response.text)

def test_create_atm():
    """Test creating a new ATM master record"""
    new_atm = {
        "terminal_id": "TEST001",
        "terminal_name": "Test ATM Central",
        "external_id": "EXT001",
        "brand": "NCR",
        "model": "SelfServ 24e",
        "serial_number": "NCR123456789",
        "location": "Test Building, Central Dili",
        "location_type": "Financial Institution Office",
        "address_line_1": "123 Test Street",
        "city": "Dili",
        "region": "TL-DL",
        "country": "Timor-Leste",
        "latitude": -8.5594,
        "longitude": 125.5647,
        "is_active": True,
        "created_by": "test_user"
    }
    
    response = requests.post(ATM_MASTERS_ENDPOINT, json=new_atm)
    print_response("CREATE ATM Master Record", response)
    
    if response.status_code == 201:
        return response.json()["terminal_id"]
    return None

def test_read_atm(terminal_id):
    """Test reading a specific ATM master record"""
    response = requests.get(f"{ATM_MASTERS_ENDPOINT}/{terminal_id}")
    print_response(f"READ ATM Master Record - {terminal_id}", response)

def test_list_atms():
    """Test listing ATM master records with pagination"""
    params = {
        "page": 1,
        "per_page": 5,
        "region": "TL-DL"
    }
    
    response = requests.get(ATM_MASTERS_ENDPOINT, params=params)
    print_response("LIST ATM Master Records (Paginated)", response)

def test_update_atm(terminal_id):
    """Test updating an ATM master record"""
    update_data = {
        "terminal_name": "Updated Test ATM Central",
        "location_type": "Bank Branch",
        "last_maintenance_date": "2025-06-01",
        "next_maintenance_date": "2025-12-01",
        "updated_by": "test_user_2"
    }
    
    response = requests.put(f"{ATM_MASTERS_ENDPOINT}/{terminal_id}", json=update_data)
    print_response(f"UPDATE ATM Master Record - {terminal_id}", response)

def test_regional_query():
    """Test querying ATMs by region"""
    response = requests.get(f"{ATM_MASTERS_ENDPOINT}/by-region/TL-DL")
    print_response("QUERY ATMs by Region - TL-DL", response)

def test_brand_query():
    """Test querying ATMs by brand"""
    response = requests.get(f"{ATM_MASTERS_ENDPOINT}/by-brand/NCR")
    print_response("QUERY ATMs by Brand - NCR", response)

def test_statistics():
    """Test getting ATM statistics"""
    response = requests.get(f"{ATM_MASTERS_ENDPOINT}/statistics")
    print_response("GET ATM Statistics", response)

def test_delete_atm(terminal_id):
    """Test deleting an ATM master record"""
    response = requests.delete(f"{ATM_MASTERS_ENDPOINT}/{terminal_id}")
    print_response(f"DELETE ATM Master Record - {terminal_id}", response)

def main():
    """Run all CRUD tests"""
    print("🚀 ATM Masters CRUD API Test Suite")
    print("="*60)
    print("This script tests all CRUD operations on the ATM Masters API")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print()
    
    # Test API health first
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API Server is not responding correctly")
            return
        print("✅ API Server is running")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server at http://localhost:8000")
        print("Please start the FastAPI server with: uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000")
        return
    
    # 1. Test CREATE
    terminal_id = test_create_atm()
    
    if terminal_id:
        # 2. Test READ
        test_read_atm(terminal_id)
        
        # 3. Test UPDATE
        test_update_atm(terminal_id)
        
        # 4. Test READ after UPDATE
        test_read_atm(terminal_id)
    
    # 5. Test LIST with pagination and filters
    test_list_atms()
    
    # 6. Test regional queries
    test_regional_query()
    
    # 7. Test brand queries
    test_brand_query()
    
    # 8. Test statistics
    test_statistics()
    
    # 9. Test DELETE (cleanup)
    if terminal_id:
        test_delete_atm(terminal_id)
        
        # Verify deletion
        response = requests.get(f"{ATM_MASTERS_ENDPOINT}/{terminal_id}")
        if response.status_code == 404:
            print(f"\n✅ Confirmed: ATM {terminal_id} was successfully deleted")
        else:
            print(f"\n⚠️  ATM {terminal_id} may not have been deleted properly")
    
    print(f"\n{'='*60}")
    print("🎉 ATM Masters CRUD API Test Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
