#!/usr/bin/env python3
"""
Simple Database Timestamp Checker
Quick analysis of timestamp columns to identify timezone issues
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz

# Database configuration
DB_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

DILI_TZ = pytz.timezone('Asia/Dili')
UTC_TZ = pytz.UTC

def check_timestamps():
    """Quick timestamp check"""
    print("=" * 60)
    print("DATABASE TIMESTAMP ANALYSIS")
    print("=" * 60)
    
    # Get current times
    current_utc = datetime.now(UTC_TZ)
    current_dili = current_utc.astimezone(DILI_TZ)
    
    print(f"Current UTC time:  {current_utc}")
    print(f"Current Dili time: {current_dili}")
    print()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Get all tables with timestamp columns
        cursor.execute("""
            SELECT DISTINCT
                t.table_name,
                c.column_name,
                c.data_type
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
                AND (
                    c.data_type IN ('timestamp with time zone', 'timestamp without time zone', 'date')
                    OR c.column_name ILIKE '%time%'
                    OR c.column_name ILIKE '%date%'
                    OR c.column_name ILIKE '%created%'
                    OR c.column_name ILIKE '%updated%'
                )
            ORDER BY t.table_name, c.column_name
        """)
        
        timestamp_columns = cursor.fetchall()
        print(f"Found {len(timestamp_columns)} timestamp columns:")
        print()
        
        issues_found = 0
        
        for row in timestamp_columns:
            table_name = row['table_name']
            column_name = row['column_name']
            data_type = row['data_type']
            
            print(f"Analyzing {table_name}.{column_name} ({data_type})")
            
            try:
                # Check for future timestamps
                cursor.execute(f"""
                    SELECT COUNT(*) as future_count
                    FROM {table_name}
                    WHERE {column_name} > NOW()
                """)
                future_count = cursor.fetchone()['future_count']
                
                # Get latest timestamp
                cursor.execute(f"""
                    SELECT {column_name} as latest_timestamp
                    FROM {table_name}
                    WHERE {column_name} IS NOT NULL
                    ORDER BY {column_name} DESC
                    LIMIT 1
                """)
                latest_result = cursor.fetchone()
                latest_timestamp = latest_result['latest_timestamp'] if latest_result else None
                
                # Get total record count
                cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                total_records = cursor.fetchone()['total']
                
                print(f"  Total records: {total_records}")
                if latest_timestamp:
                    print(f"  Latest timestamp: {latest_timestamp}")
                    
                if future_count > 0:
                    print(f"  ⚠️  ISSUE: {future_count} future timestamps found!")
                    issues_found += 1
                    
                    # Show sample future timestamps
                    cursor.execute(f"""
                        SELECT {column_name}, COUNT(*) as count
                        FROM {table_name}
                        WHERE {column_name} > NOW()
                        GROUP BY {column_name}
                        ORDER BY {column_name} DESC
                        LIMIT 3
                    """)
                    future_samples = cursor.fetchall()
                    for sample in future_samples:
                        print(f"    Future: {sample[column_name]} ({sample['count']} records)")
                else:
                    print(f"  ✅ No future timestamps")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Error analyzing column: {e}")
                print()
        
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        if issues_found > 0:
            print(f"⚠️  Found {issues_found} columns with future timestamps")
            print("This indicates timezone conversion issues that need to be fixed.")
            print("\nTo fix these issues:")
            print("1. Run the full audit: python3 database_timestamp_audit.py --audit")
            print("2. Apply fixes: python3 database_timestamp_audit.py --fix --apply")
        else:
            print("✅ All timestamps appear to be in correct UTC format")
            print("No timezone conversion needed.")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_timestamps()
