#!/usr/bin/env python3
"""
Debug script to analyze the SQL queries used by both endpoints
and find the exact cause of the data discrepancy
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def debug_queries():
    """Run the exact queries used by both endpoints and compare results"""
    
    # Database connection parameters
    db_config = {
        'host': '88.222.214.26',
        'port': 5432,
        'database': 'atm_monitoring',
        'user': 'luckyadmin',
        'password': os.getenv('DB_PASS')
    }
    
    if not db_config['password']:
        print("Error: DB_PASS environment variable not set")
        return
    
    try:
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to database successfully\n")
        
        # Query 1: Dashboard Summary Query (with status mapping)
        print("=" * 60)
        print("1. DASHBOARD SUMMARY QUERY (with status mapping)")
        print("=" * 60)
        
        dashboard_query = """
            WITH latest_terminals AS (
                SELECT DISTINCT ON (terminal_id)
                    terminal_id, fetched_status, retrieved_date
                FROM terminal_details
                WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
                ORDER BY terminal_id, retrieved_date DESC
            ),
            status_counts AS (
                SELECT 
                    fetched_status,
                    COUNT(*) as count
                FROM latest_terminals
                GROUP BY fetched_status
            ),
            status_mapping AS (
                SELECT 
                    COALESCE(SUM(CASE WHEN fetched_status = 'AVAILABLE' THEN count ELSE 0 END), 0) as total_available,
                    COALESCE(SUM(CASE WHEN fetched_status = 'WARNING' THEN count ELSE 0 END), 0) as total_warning,
                    COALESCE(SUM(CASE WHEN fetched_status IN ('WOUNDED', 'HARD', 'CASH') THEN count ELSE 0 END), 0) as total_wounded,
                    COALESCE(SUM(CASE WHEN fetched_status = 'ZOMBIE' THEN count ELSE 0 END), 0) as total_zombie,
                    COALESCE(SUM(CASE WHEN fetched_status IN ('OUT_OF_SERVICE', 'UNAVAILABLE') THEN count ELSE 0 END), 0) as total_out_of_service,
                    COUNT(DISTINCT 1) as total_regions,
                    (SELECT MAX(retrieved_date) FROM latest_terminals) as last_updated
                FROM status_counts
            )
            SELECT * FROM status_mapping
        """
        
        dashboard_result = await conn.fetchrow(dashboard_query)
        print(f"Available: {dashboard_result['total_available']}")
        print(f"Warning: {dashboard_result['total_warning']}")  
        print(f"Wounded: {dashboard_result['total_wounded']}")
        print(f"Zombie: {dashboard_result['total_zombie']}")
        print(f"Out of Service: {dashboard_result['total_out_of_service']}")
        total_dashboard = (dashboard_result['total_available'] + dashboard_result['total_warning'] + 
                          dashboard_result['total_wounded'] + dashboard_result['total_zombie'] + 
                          dashboard_result['total_out_of_service'])
        print(f"TOTAL: {total_dashboard}")
        
        print("\n" + "=" * 60)
        print("2. ATM INFORMATION QUERY (raw fetched_status)")
        print("=" * 60)
        
        # Query 2: ATM Information Query (raw status values)
        atm_info_query = """
            SELECT DISTINCT ON (terminal_id)
                terminal_id, location, issue_state_name, serial_number,
                fetched_status, retrieved_date, fault_data, metadata
            FROM terminal_details
            WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
            ORDER BY terminal_id, retrieved_date DESC
        """
        
        atm_info_results = await conn.fetch(atm_info_query)
        
        # Count status values
        status_counts = {}
        for row in atm_info_results:
            status = row['fetched_status'] or 'NULL'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"Raw status counts: {status_counts}")
        print(f"TOTAL: {len(atm_info_results)}")
        
        print("\n" + "=" * 60)
        print("3. DETAILED COMPARISON")
        print("=" * 60)
        
        # Show individual terminals
        print("Terminals from ATM Info Query:")
        for row in sorted(atm_info_results, key=lambda x: x['terminal_id']):
            print(f"  {row['terminal_id']}: {row['fetched_status']} (updated: {row['retrieved_date']})")
        
        print(f"\nDashboard Total: {total_dashboard}")
        print(f"ATM Info Total: {len(atm_info_results)}")
        print(f"Difference: {total_dashboard - len(atm_info_results)}")
        
        if total_dashboard != len(atm_info_results):
            print("\n❌ DISCREPANCY FOUND!")
            print("The dashboard and ATM information queries return different counts.")
            
            # Let's check if it's the status mapping
            mapped_available = sum(1 for row in atm_info_results if row['fetched_status'] == 'AVAILABLE')
            mapped_wounded = sum(1 for row in atm_info_results if row['fetched_status'] in ['WOUNDED', 'HARD', 'CASH'])
            
            print(f"\nStatus mapping check:")
            print(f"Dashboard Available: {dashboard_result['total_available']}")
            print(f"Raw AVAILABLE count: {mapped_available}")
            print(f"Dashboard Wounded: {dashboard_result['total_wounded']}")  
            print(f"Raw WOUNDED/HARD/CASH count: {mapped_wounded}")
            
        else:
            print("\n✅ DATA IS CONSISTENT!")
            
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_queries())
