#!/usr/bin/env python3
"""
Final Data Source Verification Script

This script verifies that the data discrepancy between dashboard cards 
and ATM information page has been resolved after our fix.
"""

import requests
import json
from typing import Dict, Any

def test_api_endpoints():
    """Test both API endpoints to verify data consistency"""
    base_url = "http://localhost:8000"
    
    print("🔍 FINAL DATA SOURCE VERIFICATION")
    print("=" * 60)
    
    # Test 1: Dashboard Summary Endpoint
    print("\n1️⃣ Testing Dashboard Summary Endpoint")
    print("   Endpoint: GET /api/v1/atm/status/summary")
    print("   Used by: Dashboard main page cards")
    
    try:
        response = requests.get(f"{base_url}/api/v1/atm/status/summary")
        response.raise_for_status()
        summary_data = response.json()
        
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📊 Data Source: {summary_data.get('data_source', 'Unknown')}")
        print(f"   📈 Total ATMs: {summary_data['total_atms']}")
        print(f"   🟢 Available: {summary_data['status_counts']['available']}")
        print(f"   🟡 Warning: {summary_data['status_counts']['warning']}")
        print(f"   🟠 Wounded: {summary_data['status_counts']['wounded']}")
        print(f"   🔴 Zombie: {summary_data['status_counts']['zombie']}")
        print(f"   ⚫ Out of Service: {summary_data['status_counts']['out_of_service']}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: ATM Information Endpoint  
    print("\n2️⃣ Testing ATM Information Endpoint")
    print("   Endpoint: GET /api/v1/atm/status/latest?include_terminal_details=true")
    print("   Used by: ATM Information page (/atm-information)")
    
    try:
        response = requests.get(f"{base_url}/api/v1/atm/status/latest?include_terminal_details=true")
        response.raise_for_status()
        latest_data = response.json()
        
        print(f"   ✅ Status: {response.status_code}")
        
        # Find terminal_details data source
        terminal_data = None
        for source in latest_data.get('data_sources', []):
            if source.get('table') == 'terminal_details':
                terminal_data = source
                break
        
        if terminal_data:
            # Count statuses from terminal data
            status_counts = {}
            for record in terminal_data.get('data', []):
                status = record.get('fetched_status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Map to standard categories
            available = status_counts.get('AVAILABLE', 0)
            warning = status_counts.get('WARNING', 0)
            wounded = status_counts.get('WOUNDED', 0) + status_counts.get('HARD', 0) + status_counts.get('CASH', 0)
            zombie = status_counts.get('ZOMBIE', 0)
            out_of_service = status_counts.get('OUT_OF_SERVICE', 0) + status_counts.get('UNAVAILABLE', 0)
            total = sum(status_counts.values())
            
            print(f"   📊 Data Source: terminal_details")
            print(f"   📈 Total ATMs: {total}")
            print(f"   🟢 Available: {available}")
            print(f"   🟡 Warning: {warning}")
            print(f"   🟠 Wounded: {wounded}")
            print(f"   🔴 Zombie: {zombie}")
            print(f"   ⚫ Out of Service: {out_of_service}")
            
            # Store for comparison
            atm_info_data = {
                'total': total,
                'available': available,
                'warning': warning,
                'wounded': wounded,
                'zombie': zombie,
                'out_of_service': out_of_service
            }
        else:
            print("   ❌ No terminal_details data found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Data Consistency Check
    print("\n3️⃣ Data Consistency Verification")
    print("   Comparing dashboard cards vs ATM information data...")
    
    dashboard_data = {
        'total': summary_data['total_atms'],
        'available': summary_data['status_counts']['available'],
        'warning': summary_data['status_counts']['warning'],
        'wounded': summary_data['status_counts']['wounded'],
        'zombie': summary_data['status_counts']['zombie'],
        'out_of_service': summary_data['status_counts']['out_of_service']
    }
    
    # Compare the two data sources
    discrepancies = []
    for key in dashboard_data.keys():
        if dashboard_data[key] != atm_info_data[key]:
            discrepancies.append({
                'field': key,
                'dashboard': dashboard_data[key],
                'atm_info': atm_info_data[key],
                'difference': dashboard_data[key] - atm_info_data[key]
            })
    
    if discrepancies:
        print("   ❌ DISCREPANCIES FOUND:")
        for disc in discrepancies:
            print(f"     • {disc['field'].title()}: Dashboard={disc['dashboard']}, ATM Info={disc['atm_info']} (diff: {disc['difference']})")
        return False
    else:
        print("   ✅ DATA IS CONSISTENT!")
        print("     All counts match between dashboard cards and ATM information page")
        return True

def test_data_source_alignment():
    """Test that both endpoints use the same underlying data source"""
    print("\n4️⃣ Data Source Alignment Check")
    print("   Verifying both endpoints use terminal_details table...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Get summary endpoint info
        summary_response = requests.get(f"{base_url}/api/v1/atm/status/summary")
        summary_data = summary_response.json()
        summary_source = summary_data.get('data_source', 'Unknown')
        
        print(f"   Dashboard Summary Source: {summary_source}")
        print(f"   ATM Information Source: terminal_details")
        
        if summary_source == 'terminal_details':
            print("   ✅ BOTH ENDPOINTS USE THE SAME DATA SOURCE!")
            print("   🎯 Fix successful: Data discrepancy resolved")
            return True
        else:
            print("   ❌ Different data sources detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking data sources: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 Starting final verification of card status data source fix...")
    
    # Run all tests
    endpoints_ok = test_api_endpoints()
    sources_aligned = test_data_source_alignment()
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if endpoints_ok and sources_aligned:
        print("✅ SUCCESS: Data source discrepancy has been RESOLVED!")
        print("")
        print("🎯 Both dashboard cards and ATM information page now show:")
        print("   • Same data source (terminal_details)")
        print("   • Identical ATM counts")
        print("   • Consistent status breakdowns")
        print("")
        print("✨ The fix is working correctly!")
        return True
    else:
        print("❌ FAILURE: Data discrepancy still exists")
        print("")
        if not endpoints_ok:
            print("   • Data counts don't match between endpoints")
        if not sources_aligned:
            print("   • Endpoints still use different data sources")
        print("")
        print("🔧 Additional fixes needed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
