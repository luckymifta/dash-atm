#!/usr/bin/env python3
"""
ATM Card Status Data Source Verification Tool

This script verifies the data sources used by:
1. Dashboard main page card status (Total ATMs, Available, Warning, Wounded, Out Of Service)
2. ATM Information page terminal details

Purpose: Identify why these two pages show different data
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Any

# Database configuration
DATABASE_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

class ATMDataVerifier:
    def __init__(self):
        self.conn = None
    
    async def connect(self):
        """Connect to the database"""
        try:
            self.conn = await asyncpg.connect(**DATABASE_CONFIG)
            print("✅ Connected to database successfully")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
    
    async def check_dashboard_summary_data_source(self):
        """Check data source used by dashboard summary endpoint"""
        print("\n" + "="*80)
        print("🔍 DASHBOARD SUMMARY DATA SOURCE ANALYSIS")
        print("="*80)
        print("Endpoint: GET /api/v1/atm/status/summary")
        print("Used by: Dashboard main page cards (Total ATMs, Available, etc.)")
        
        # Check regional_data table (NEW table - used by default)
        print("\n📊 Checking 'regional_data' table:")
        try:
            query = """
                WITH latest_data AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        retrieval_timestamp
                    FROM regional_data
                    WHERE region_code = 'TL-DL'
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    SUM(COALESCE(count_available, 0)) as total_available,
                    SUM(COALESCE(count_warning, 0)) as total_warning,
                    SUM(COALESCE(count_zombie, 0)) as total_zombie,
                    SUM(COALESCE(count_wounded, 0)) as total_wounded,
                    SUM(COALESCE(count_out_of_service, 0)) as total_out_of_service,
                    SUM(COALESCE(total_atms_in_region, 0)) as total_atms,
                    MAX(retrieval_timestamp) as last_updated
                FROM latest_data
            """
            
            row = await self.conn.fetchrow(query)
            if row:
                total_atms = (row['total_available'] or 0) + (row['total_warning'] or 0) + \
                           (row['total_zombie'] or 0) + (row['total_wounded'] or 0) + \
                           (row['total_out_of_service'] or 0)
                
                print(f"  📈 Total ATMs: {total_atms}")
                print(f"  🟢 Available: {row['total_available'] or 0}")
                print(f"  🟡 Warning: {row['total_warning'] or 0}")
                print(f"  🟠 Wounded: {row['total_wounded'] or 0}")
                print(f"  🔴 Zombie: {row['total_zombie'] or 0}")
                print(f"  ⚫ Out of Service: {row['total_out_of_service'] or 0}")
                print(f"  🕒 Last Updated: {row['last_updated']}")
                
                return {
                    'source': 'regional_data',
                    'total_atms': total_atms,
                    'available': row['total_available'] or 0,
                    'warning': row['total_warning'] or 0,
                    'wounded': row['total_wounded'] or 0,
                    'zombie': row['total_zombie'] or 0,
                    'out_of_service': row['total_out_of_service'] or 0,
                    'last_updated': row['last_updated']
                }
            else:
                print("  ❌ No data found in regional_data table")
                
        except Exception as e:
            print(f"  ❌ Error querying regional_data: {e}")
        
        # Check regional_atm_counts table (LEGACY table)
        print("\n📊 Checking 'regional_atm_counts' table (legacy):")
        try:
            query = """
                WITH latest_data AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        date_creation
                    FROM regional_atm_counts
                    ORDER BY region_code, date_creation DESC
                )
                SELECT 
                    SUM(COALESCE(count_available, 0)) as total_available,
                    SUM(COALESCE(count_warning, 0)) as total_warning,
                    SUM(COALESCE(count_zombie, 0)) as total_zombie,
                    SUM(COALESCE(count_wounded, 0)) as total_wounded,
                    SUM(COALESCE(count_out_of_service, 0)) as total_out_of_service,
                    SUM(COALESCE(total_atms_in_region, 0)) as total_atms,
                    MAX(date_creation) as last_updated
                FROM latest_data
            """
            
            row = await self.conn.fetchrow(query)
            if row:
                total_atms = (row['total_available'] or 0) + (row['total_warning'] or 0) + \
                           (row['total_zombie'] or 0) + (row['total_wounded'] or 0) + \
                           (row['total_out_of_service'] or 0)
                
                print(f"  📈 Total ATMs: {total_atms}")
                print(f"  🟢 Available: {row['total_available'] or 0}")
                print(f"  🟡 Warning: {row['total_warning'] or 0}")
                print(f"  🟠 Wounded: {row['total_wounded'] or 0}")
                print(f"  🔴 Zombie: {row['total_zombie'] or 0}")
                print(f"  ⚫ Out of Service: {row['total_out_of_service'] or 0}")
                print(f"  🕒 Last Updated: {row['last_updated']}")
            else:
                print("  ❌ No data found in regional_atm_counts table")
                
        except Exception as e:
            print(f"  ❌ Error querying regional_atm_counts: {e}")
        
        return None
    
    async def check_atm_information_data_source(self):
        """Check data source used by ATM information page"""
        print("\n" + "="*80)
        print("🔍 ATM INFORMATION PAGE DATA SOURCE ANALYSIS")
        print("="*80)
        print("Endpoint: GET /api/v1/atm/status/latest (with include_terminal_details=true)")
        print("Used by: ATM Information page (/atm-information)")
        
        # Check terminal_details table
        print("\n📊 Checking 'terminal_details' table:")
        try:
            # Get latest data for each terminal
            query = """
                WITH latest_terminals AS (
                    SELECT DISTINCT ON (terminal_id)
                        terminal_id, location, issue_state_name, serial_number,
                        retrieved_date, fetched_status, fault_data
                    FROM terminal_details
                    ORDER BY terminal_id, retrieved_date DESC
                )
                SELECT 
                    fetched_status,
                    COUNT(*) as count
                FROM latest_terminals
                GROUP BY fetched_status
                ORDER BY count DESC
            """
            
            rows = await self.conn.fetch(query)
            
            status_counts = {}
            total_terminals = 0
            
            print("  📋 Terminal Status Distribution:")
            for row in rows:
                status = row['fetched_status']
                count = row['count']
                status_counts[status] = count
                total_terminals += count
                print(f"    {status}: {count} terminals")
            
            print(f"\n  📈 Total Terminals: {total_terminals}")
            
            # Map statuses to standard categories
            available = status_counts.get('AVAILABLE', 0)
            warning = status_counts.get('WARNING', 0)
            wounded = status_counts.get('WOUNDED', 0) + status_counts.get('HARD', 0) + status_counts.get('CASH', 0)
            zombie = status_counts.get('ZOMBIE', 0)
            out_of_service = status_counts.get('OUT_OF_SERVICE', 0) + status_counts.get('UNAVAILABLE', 0)
            
            print(f"\n  📊 Mapped to Standard Categories:")
            print(f"    🟢 Available: {available}")
            print(f"    🟡 Warning: {warning}")
            print(f"    🟠 Wounded: {wounded} (includes WOUNDED, HARD, CASH)")
            print(f"    🔴 Zombie: {zombie}")
            print(f"    ⚫ Out of Service: {out_of_service} (includes OUT_OF_SERVICE, UNAVAILABLE)")
            
            return {
                'source': 'terminal_details',
                'total_atms': total_terminals,
                'available': available,
                'warning': warning,
                'wounded': wounded,
                'zombie': zombie,
                'out_of_service': out_of_service,
                'raw_status_counts': status_counts
            }
            
        except Exception as e:
            print(f"  ❌ Error querying terminal_details: {e}")
        
        return None
    
    async def compare_data_sources(self, dashboard_data, atm_info_data):
        """Compare the two data sources"""
        print("\n" + "="*80)
        print("📊 DATA SOURCE COMPARISON")
        print("="*80)
        
        if not dashboard_data or not atm_info_data:
            print("❌ Cannot compare - missing data from one or both sources")
            return
        
        print(f"\n📋 Data Source Summary:")
        print(f"  Dashboard Cards: {dashboard_data['source']} table")
        print(f"  ATM Information: {atm_info_data['source']} table")
        
        print(f"\n📊 Status Count Comparison:")
        print(f"{'Status':<15} {'Dashboard':<12} {'ATM Info':<12} {'Difference':<12} {'Match'}")
        print("-" * 70)
        
        categories = ['total_atms', 'available', 'warning', 'wounded', 'zombie', 'out_of_service']
        mismatches = []
        
        for category in categories:
            dashboard_val = dashboard_data[category]
            atm_info_val = atm_info_data[category]
            difference = abs(dashboard_val - atm_info_val)
            match = "✅" if difference == 0 else "❌"
            
            if difference > 0:
                mismatches.append({
                    'category': category,
                    'dashboard': dashboard_val,
                    'atm_info': atm_info_val,
                    'difference': difference
                })
            
            print(f"{category.replace('_', ' ').title():<15} {dashboard_val:<12} {atm_info_val:<12} {difference:<12} {match}")
        
        if mismatches:
            print(f"\n⚠️  DISCREPANCIES FOUND:")
            print(f"   {len(mismatches)} categories show different values between data sources")
            
            print(f"\n🔍 ROOT CAUSE ANALYSIS:")
            print(f"   1. Dashboard uses '{dashboard_data['source']}' table (aggregated regional data)")
            print(f"   2. ATM Information uses '{atm_info_data['source']}' table (individual terminal data)")
            print(f"   3. These tables may be updated at different times or from different sources")
            
            print(f"\n💡 RECOMMENDATIONS:")
            print(f"   1. Check if both tables are updated from the same data source")
            print(f"   2. Verify update timestamps to see which is more recent")
            print(f"   3. Consider using a single source of truth for both pages")
            print(f"   4. Implement data synchronization between tables")
            
        else:
            print(f"\n✅ SUCCESS: All status counts match between data sources!")
    
    async def check_update_timestamps(self):
        """Check when each table was last updated"""
        print("\n" + "="*80)
        print("🕒 UPDATE TIMESTAMP ANALYSIS")
        print("="*80)
        
        # Check regional_data timestamps
        try:
            query = "SELECT MAX(retrieval_timestamp) as last_update FROM regional_data"
            row = await self.conn.fetchrow(query)
            regional_last_update = row['last_update'] if row else None
            print(f"📊 regional_data last update: {regional_last_update}")
        except Exception as e:
            print(f"❌ Error checking regional_data timestamps: {e}")
            regional_last_update = None
        
        # Check terminal_details timestamps
        try:
            query = "SELECT MAX(retrieved_date) as last_update FROM terminal_details"
            row = await self.conn.fetchrow(query)
            terminal_last_update = row['last_update'] if row else None
            print(f"📊 terminal_details last update: {terminal_last_update}")
        except Exception as e:
            print(f"❌ Error checking terminal_details timestamps: {e}")
            terminal_last_update = None
        
        # Check regional_atm_counts timestamps
        try:
            query = "SELECT MAX(date_creation) as last_update FROM regional_atm_counts"
            row = await self.conn.fetchrow(query)
            legacy_last_update = row['last_update'] if row else None
            print(f"📊 regional_atm_counts last update: {legacy_last_update}")
        except Exception as e:
            print(f"❌ Error checking regional_atm_counts timestamps: {e}")
            legacy_last_update = None
        
        # Compare timestamps
        if regional_last_update and terminal_last_update:
            time_diff = abs((regional_last_update - terminal_last_update).total_seconds())
            print(f"\n⏰ Time difference between data sources: {time_diff:.0f} seconds")
            
            if time_diff > 3600:  # More than 1 hour
                print(f"⚠️  WARNING: Large time difference detected!")
                print(f"   This could explain the data discrepancies")
            else:
                print(f"✅ Data sources are relatively synchronized")
    
    async def get_detailed_terminal_breakdown(self):
        """Get detailed breakdown of terminal statuses"""
        print("\n" + "="*80)
        print("🔍 DETAILED TERMINAL STATUS BREAKDOWN")
        print("="*80)
        
        try:
            query = """
                WITH latest_terminals AS (
                    SELECT DISTINCT ON (terminal_id)
                        terminal_id, location, issue_state_name, 
                        fetched_status, retrieved_date
                    FROM terminal_details
                    ORDER BY terminal_id, retrieved_date DESC
                )
                SELECT 
                    terminal_id,
                    COALESCE(location, 'Unknown') as location,
                    COALESCE(issue_state_name, fetched_status, 'Unknown') as status
                FROM latest_terminals
                ORDER BY terminal_id
            """
            
            rows = await self.conn.fetch(query)
            
            print(f"📋 Individual Terminal Status:")
            print(f"{'Terminal ID':<12} {'Status':<15} {'Location'}")
            print("-" * 70)
            
            status_summary = {}
            for row in rows:
                terminal_id = row['terminal_id']
                status = row['status']
                location = row['location'][:40] if row['location'] else 'Unknown'
                
                print(f"{terminal_id:<12} {status:<15} {location}")
                
                # Count by status
                if status in status_summary:
                    status_summary[status] += 1
                else:
                    status_summary[status] = 1
            
            print(f"\n📊 Status Summary from Terminal Details:")
            for status, count in sorted(status_summary.items()):
                print(f"  {status}: {count} terminals")
            
            return status_summary
            
        except Exception as e:
            print(f"❌ Error getting terminal breakdown: {e}")
            return {}

async def main():
    """Main verification function"""
    print("🔍 ATM CARD STATUS DATA SOURCE VERIFICATION")
    print("=" * 80)
    print("This tool verifies why dashboard cards and ATM information page show different data")
    
    verifier = ATMDataVerifier()
    
    # Connect to database
    if not await verifier.connect():
        return
    
    try:
        # Check dashboard summary data source
        dashboard_data = await verifier.check_dashboard_summary_data_source()
        
        # Check ATM information data source
        atm_info_data = await verifier.check_atm_information_data_source()
        
        # Compare the two data sources
        await verifier.compare_data_sources(dashboard_data, atm_info_data)
        
        # Check update timestamps
        await verifier.check_update_timestamps()
        
        # Get detailed terminal breakdown
        await verifier.get_detailed_terminal_breakdown()
        
        print("\n" + "="*80)
        print("✅ VERIFICATION COMPLETE")
        print("="*80)
        print("Check the analysis above to identify the root cause of data discrepancies.")
        
    finally:
        await verifier.close()

if __name__ == "__main__":
    asyncio.run(main())
