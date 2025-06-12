#!/usr/bin/env python3
"""
Simple Data Source Verification
Confirms the fix for dashboard vs ATM information data discrepancy
"""

import requests
import json

def main():
    print("🔍 VERIFICATION: Dashboard vs ATM Information Data Source Fix")
    print("=" * 65)
    
    # Test dashboard summary
    try:
        response = requests.get("http://localhost:8000/api/v1/atm/status/summary", timeout=5)
        dashboard_data = response.json()
        
        print("\n📊 Dashboard Summary Endpoint:")
        print(f"   Data Source: {dashboard_data.get('data_source', 'Unknown')}")
        print(f"   Available: {dashboard_data['status_counts']['available']}")
        print(f"   Out of Service: {dashboard_data['status_counts']['out_of_service']}")
        
    except Exception as e:
        print(f"❌ Dashboard endpoint error: {e}")
        return
    
    # Test ATM information
    try:
        response = requests.get("http://localhost:8000/api/v1/atm/status/latest?include_terminal_details=true", timeout=5)
        latest_data = response.json()
        
        # Find terminal data
        for source in latest_data.get('data_sources', []):
            if source.get('table') == 'terminal_details':
                statuses = {}
                for record in source.get('data', []):
                    status = record.get('fetched_status', 'UNKNOWN')
                    statuses[status] = statuses.get(status, 0) + 1
                
                available = statuses.get('AVAILABLE', 0)
                out_of_service = statuses.get('OUT_OF_SERVICE', 0) + statuses.get('UNAVAILABLE', 0)
                
                print("\n📋 ATM Information Endpoint:")
                print(f"   Data Source: terminal_details")
                print(f"   Available: {available}")
                print(f"   Out of Service: {out_of_service}")
                
                # Compare
                print("\n🎯 COMPARISON RESULT:")
                if (dashboard_data['status_counts']['available'] == available and 
                    dashboard_data['status_counts']['out_of_service'] == out_of_service and
                    dashboard_data.get('data_source') == 'terminal_details'):
                    
                    print("   ✅ SUCCESS: Data discrepancy RESOLVED!")
                    print("   • Both endpoints use terminal_details table")
                    print("   • Available counts match exactly")
                    print("   • Out of Service counts match exactly")
                    print("\n🎉 The fix is working correctly!")
                else:
                    print("   ❌ FAILURE: Data still inconsistent")
                
                break
        else:
            print("❌ No terminal_details data found")
            
    except Exception as e:
        print(f"❌ ATM information endpoint error: {e}")

if __name__ == "__main__":
    main()
