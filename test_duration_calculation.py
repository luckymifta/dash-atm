#!/usr/bin/env python3
"""
Test script to verify fault duration calculation logic
This script will:
1. Query the database for fault state transitions
2. Calculate duration from fault start to AVAILABLE
3. Compare with backend API logic
4. Show detailed breakdown of the calculation
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '88.222.214.26'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'development_db'),
    'user': os.getenv('DB_USER', 'timlesdev'),
    'password': os.getenv('DB_PASSWORD', 'timlesdev')
}

# Timezone configuration
DILI_TZ = pytz.timezone('Asia/Dili')  # UTC+9
UTC_TZ = pytz.UTC

def convert_to_dili_time(timestamp: datetime) -> datetime:
    """Convert timestamp to Dili time"""
    try:
        if timestamp.tzinfo is not None:
            if timestamp.utcoffset() == timedelta(hours=9):
                return timestamp.replace(tzinfo=None)
            else:
                dili_timestamp = timestamp.astimezone(DILI_TZ)
                return dili_timestamp.replace(tzinfo=None)
        else:
            return timestamp
    except Exception as e:
        print(f"Error processing timestamp: {e}")
        return timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp

async def test_duration_calculation():
    """Test the duration calculation logic"""
    print("🔍 Testing Fault Duration Calculation Logic")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Connected to database successfully")
        
        # Test date range - last 7 days
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = end_date - timedelta(days=7)
        
        print(f"📅 Testing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print()
        
        # Query for status transitions (similar to backend logic)
        test_query = """
        WITH status_changes AS (
            SELECT 
                terminal_id,
                location,
                fetched_status,
                retrieved_date,
                LAG(fetched_status) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as prev_status,
                LEAD(fetched_status) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as next_status,
                LEAD(retrieved_date) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as next_time,
                fault_data,
                ROW_NUMBER() OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as row_num
            FROM terminal_details td
            WHERE retrieved_date BETWEEN $1 AND $2
            ORDER BY terminal_id, retrieved_date
        ),
        fault_periods AS (
            SELECT 
                terminal_id,
                location,
                fetched_status as fault_state,
                retrieved_date as fault_start,
                next_time as fault_end,
                next_status,
                -- Backend calculation logic
                CASE 
                    WHEN next_status = 'AVAILABLE' OR next_status = 'ONLINE' THEN 
                        EXTRACT(EPOCH FROM (next_time - retrieved_date))/60
                    WHEN next_time IS NULL AND $2 > retrieved_date THEN
                        EXTRACT(EPOCH FROM ($2 - retrieved_date))/60
                    ELSE NULL
                END as backend_duration_minutes,
                -- Simple calculation for comparison
                CASE 
                    WHEN next_time IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (next_time - retrieved_date))/60
                    ELSE
                        EXTRACT(EPOCH FROM ($2 - retrieved_date))/60
                END as simple_duration_minutes,
                fault_data,
                CASE 
                    WHEN next_status = 'AVAILABLE' OR next_status = 'ONLINE' THEN true
                    ELSE false
                END as resolved
            FROM status_changes
            WHERE fetched_status IN ('WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE')
            AND (prev_status IS NULL OR prev_status = 'AVAILABLE' OR prev_status = 'ONLINE' OR prev_status != fetched_status)
        )
        SELECT 
            fp.terminal_id,
            fp.location,
            fp.fault_state,
            fp.fault_start,
            fp.fault_end,
            fp.next_status,
            fp.backend_duration_minutes,
            fp.simple_duration_minutes,
            fp.resolved,
            COALESCE(fp.fault_data->>'agentErrorDescription', 'No description') as error_description
        FROM fault_periods fp
        WHERE fp.backend_duration_minutes IS NOT NULL OR fp.simple_duration_minutes IS NOT NULL
        ORDER BY fp.terminal_id, fp.fault_start
        LIMIT 10
        """
        
        # Execute query
        rows = await conn.fetch(test_query, start_date, end_date)
        
        if not rows:
            print("❌ No fault data found in the specified period")
            print("💡 Try extending the date range or check if there are any faults in the database")
            return
        
        print(f"📊 Found {len(rows)} fault periods to analyze")
        print()
        
        # Analyze each fault period
        for i, row in enumerate(rows, 1):
            print(f"🔢 Fault #{i}")
            print(f"   Terminal: {row['terminal_id']}")
            print(f"   Location: {row['location']}")
            print(f"   Fault State: {row['fault_state']}")
            print(f"   Start Time: {row['fault_start']}")
            print(f"   End Time: {row['fault_end'] if row['fault_end'] else 'Ongoing'}")
            print(f"   Next Status: {row['next_status'] if row['next_status'] else 'None'}")
            print(f"   Resolved: {'Yes' if row['resolved'] else 'No'}")
            
            # Convert times to Dili time for display
            start_dili = convert_to_dili_time(row['fault_start'])
            end_dili = convert_to_dili_time(row['fault_end']) if row['fault_end'] else None
            
            print(f"   Start (Dili): {start_dili}")
            print(f"   End (Dili): {end_dili if end_dili else 'Ongoing'}")
            
            # Duration calculations
            backend_duration = row['backend_duration_minutes']
            simple_duration = row['simple_duration_minutes']
            
            print(f"   💾 Backend Duration: {backend_duration:.2f} minutes" if backend_duration else "   💾 Backend Duration: NULL")
            print(f"   🧮 Simple Duration: {simple_duration:.2f} minutes" if simple_duration else "   🧮 Simple Duration: NULL")
            
            # Frontend-style calculation
            if row['fault_start']:
                start_js = row['fault_start']
                end_js = row['fault_end'] if row['fault_end'] else datetime.now()
                frontend_duration_seconds = (end_js - start_js).total_seconds()
                frontend_duration_minutes = frontend_duration_seconds / 60
                
                print(f"   🌐 Frontend Calc: {frontend_duration_minutes:.2f} minutes")
                
                # Format durations in hours/minutes
                def format_duration(minutes):
                    if minutes is None:
                        return "N/A"
                    hours = int(minutes // 60)
                    mins = int(minutes % 60)
                    return f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                
                print(f"   📝 Backend Formatted: {format_duration(backend_duration)}")
                print(f"   📝 Simple Formatted: {format_duration(simple_duration)}")
                print(f"   📝 Frontend Formatted: {format_duration(frontend_duration_minutes)}")
                
                # Show differences
                if backend_duration and simple_duration:
                    diff_backend_simple = abs(backend_duration - simple_duration)
                    diff_backend_frontend = abs(backend_duration - frontend_duration_minutes)
                    print(f"   ⚖️  Diff (Backend vs Simple): {diff_backend_simple:.2f} minutes")
                    print(f"   ⚖️  Diff (Backend vs Frontend): {diff_backend_frontend:.2f} minutes")
                
            print(f"   🚨 Error: {row['error_description']}")
            print("-" * 50)
        
        # Summary statistics
        print("\n📈 SUMMARY STATISTICS")
        print("=" * 30)
        
        resolved_faults = [r for r in rows if r['resolved']]
        ongoing_faults = [r for r in rows if not r['resolved']]
        
        print(f"Total faults analyzed: {len(rows)}")
        print(f"Resolved faults: {len(resolved_faults)}")
        print(f"Ongoing faults: {len(ongoing_faults)}")
        
        if resolved_faults:
            backend_durations = [r['backend_duration_minutes'] for r in resolved_faults if r['backend_duration_minutes']]
            if backend_durations:
                avg_duration = sum(backend_durations) / len(backend_durations)
                max_duration = max(backend_durations)
                min_duration = min(backend_durations)
                
                print(f"Average resolved fault duration: {avg_duration:.2f} minutes ({avg_duration/60:.1f} hours)")
                print(f"Maximum fault duration: {max_duration:.2f} minutes ({max_duration/60:.1f} hours)")
                print(f"Minimum fault duration: {min_duration:.2f} minutes ({min_duration/60:.1f} hours)")
        
        await conn.close()
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_duration_calculation())
