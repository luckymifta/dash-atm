#!/usr/bin/env python3
"""
Debug script to find the root cause of data discrepancy between 
dashboard summary and ATM information endpoints
"""

import requests
import json

def test_endpoints():
    """Test both endpoints and compare results"""
    base_url = "http://localhost:8000"
    
    print("=== DEBUGGING DATA DISCREPANCY ===\n")
    
    # Test dashboard summary endpoint
    print("1. Dashboard Summary Endpoint:")
    try:
        dashboard_response = requests.get(f"{base_url}/api/v1/atm/status/summary")
        dashboard_data = dashboard_response.json()
        
        print(f"Total ATMs: {dashboard_data['total_atms']}")
        print(f"Status Counts: {json.dumps(dashboard_data['status_counts'], indent=2)}")
        print(f"Data Source: {dashboard_data['data_source']}")
        
    except Exception as e:
        print(f"Error testing dashboard endpoint: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test ATM information endpoint
    print("2. ATM Information Endpoint:")
    try:
        atm_info_response = requests.get(f"{base_url}/api/v1/atm/status/latest?include_terminal_details=true")
        atm_info_data = atm_info_response.json()
        
        # Find terminal_data source
        terminal_data = None
        for source in atm_info_data.get('data_sources', []):
            if source.get('type') == 'terminal_data':
                terminal_data = source['data']
                break
        
        if terminal_data:
            print(f"Total Terminals: {len(terminal_data)}")
            
            # Count by status
            status_counts = {}
            for terminal in terminal_data:
                status = terminal.get('fetched_status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"Status Breakdown: {json.dumps(status_counts, indent=2)}")
            
            # Show all terminal IDs
            print(f"\nTerminal IDs: {sorted([t['terminal_id'] for t in terminal_data])}")
            
        else:
            print("No terminal_data found in response")
            
    except Exception as e:
        print(f"Error testing ATM information endpoint: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Show the discrepancy
    dashboard_total = dashboard_data['status_counts']['total']
    atm_info_total = len(terminal_data) if terminal_data else 0
    
    print("3. DISCREPANCY ANALYSIS:")
    print(f"Dashboard Total: {dashboard_total}")
    print(f"ATM Info Total: {atm_info_total}")
    print(f"Difference: {dashboard_total - atm_info_total}")
    
    if dashboard_total != atm_info_total:
        print(f"\n❌ INCONSISTENCY DETECTED!")
        print(f"Dashboard and ATM Information page show different counts.")
        print(f"This suggests there's a terminal that the dashboard counts but ATM info page doesn't show.")
    else:
        print(f"\n✅ DATA IS CONSISTENT!")

if __name__ == "__main__":
    test_endpoints()
