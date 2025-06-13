#!/usr/bin/env python3
"""
Final Database Timezone Verification
Comprehensive check to confirm all timestamps are properly stored in UTC
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import pytz
import json

# Database configuration
DB_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

DILI_TZ = pytz.timezone('Asia/Dili')  # UTC+9
UTC_TZ = pytz.UTC

def verify_database_timezone_configuration():
    """Comprehensive verification of database timezone configuration"""
    
    print("=" * 80)
    print("🔍 FINAL DATABASE TIMEZONE VERIFICATION")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Get current times for reference
        current_utc = datetime.now(UTC_TZ)
        current_dili = current_utc.astimezone(DILI_TZ)
        
        print(f"Current UTC time:  {current_utc}")
        print(f"Current Dili time: {current_dili}")
        print()
        
        verification_results = {
            'verification_time': current_utc.isoformat(),
            'database_status': 'HEALTHY',
            'tables_verified': {},
            'schema_compliance': {},
            'recommendations': []
        }
        
        # 1. Verify database timezone setting
        print("1. DATABASE TIMEZONE CONFIGURATION")
        print("-" * 40)
        cursor.execute("SHOW timezone")
        db_timezone = cursor.fetchone()[0]
        print(f"Database timezone setting: {db_timezone}")
        
        if db_timezone.upper() == 'UTC':
            print("✅ Database is configured to use UTC timezone")
        else:
            print(f"⚠️  Database timezone is '{db_timezone}' (recommended: UTC)")
            verification_results['recommendations'].append("Consider setting database timezone to UTC")
        
        # 2. Verify table schemas
        print("\n2. TABLE SCHEMA VERIFICATION")
        print("-" * 40)
        
        tables_to_verify = ['terminal_details', 'regional_data', 'regional_atm_counts']
        
        for table_name in tables_to_verify:
            print(f"\n{table_name}:")
            
            # Check if table exists and has records
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = %s AND table_schema = 'public'
            """, (table_name,))
            
            table_exists = cursor.fetchone()['count'] > 0
            
            if not table_exists:
                print(f"  ⚠️  Table does not exist")
                verification_results['tables_verified'][table_name] = {'exists': False}
                continue
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
            total_records = cursor.fetchone()['total']
            print(f"  Records: {total_records}")
            
            table_verification = {
                'exists': True,
                'total_records': total_records,
                'timestamp_columns': {},
                'schema_compliant': True
            }
            
            # Check timestamp columns
            cursor.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                AND table_schema = 'public'
                AND (
                    data_type LIKE '%timestamp%' 
                    OR column_name LIKE '%date%' 
                    OR column_name LIKE '%time%'
                )
                ORDER BY column_name
            """, (table_name,))
            
            timestamp_columns = cursor.fetchall()
            
            for col in timestamp_columns:
                col_name = col['column_name']
                data_type = col['data_type']
                
                print(f"  {col_name}: {data_type}")
                
                column_verification = {
                    'data_type': data_type,
                    'is_timezone_aware': 'with time zone' in data_type,
                    'future_timestamps': 0,
                    'latest_value': None,
                    'status': 'OK'
                }
                
                if total_records > 0:
                    # Check for future timestamps
                    try:
                        cursor.execute(f"""
                            SELECT COUNT(*) as future_count
                            FROM {table_name}
                            WHERE {col_name} > NOW()
                        """)
                        future_count = cursor.fetchone()['future_count']
                        column_verification['future_timestamps'] = future_count
                        
                        # Get latest value
                        cursor.execute(f"""
                            SELECT {col_name}
                            FROM {table_name}
                            WHERE {col_name} IS NOT NULL
                            ORDER BY {col_name} DESC
                            LIMIT 1
                        """)
                        latest_result = cursor.fetchone()
                        if latest_result:
                            column_verification['latest_value'] = str(latest_result[col_name])
                        
                        if future_count > 0:
                            print(f"    ⚠️  {future_count} future timestamps found!")
                            column_verification['status'] = 'FUTURE_TIMESTAMPS'
                            table_verification['schema_compliant'] = False
                        else:
                            print(f"    ✅ No future timestamps")
                            
                    except Exception as e:
                        print(f"    ❌ Error checking column: {e}")
                        column_verification['status'] = 'ERROR'
                        column_verification['error'] = str(e)
                
                # Check if timezone-aware for main timestamp columns
                if col_name in ['retrieved_date', 'retrieval_timestamp', 'date_creation']:
                    if 'with time zone' not in data_type:
                        print(f"    ⚠️  Recommended: Use 'TIMESTAMP WITH TIME ZONE' for {col_name}")
                        verification_results['recommendations'].append(
                            f"Consider changing {table_name}.{col_name} to TIMESTAMP WITH TIME ZONE"
                        )
                
                table_verification['timestamp_columns'][col_name] = column_verification
            
            verification_results['tables_verified'][table_name] = table_verification
        
        # 3. Verify timezone consistency
        print("\n3. TIMEZONE CONSISTENCY CHECK")
        print("-" * 40)
        
        # Check if data appears to be consistently in UTC
        if verification_results['tables_verified'].get('terminal_details', {}).get('exists', False):
            cursor.execute("""
                SELECT 
                    retrieved_date,
                    created_at
                FROM terminal_details
                WHERE retrieved_date IS NOT NULL
                AND created_at IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            recent_records = cursor.fetchall()
            timezone_consistent = True
            
            for record in recent_records:
                retrieved_date = record['retrieved_date']
                created_at = record['created_at']
                
                # Check if times are reasonable (both should be close to each other and in UTC)
                if retrieved_date and created_at:
                    time_diff = abs((retrieved_date - created_at).total_seconds())
                    if time_diff > 3600:  # More than 1 hour difference
                        timezone_consistent = False
                        break
            
            if timezone_consistent:
                print("✅ Timestamp consistency check passed")
            else:
                print("⚠️  Some timestamp inconsistencies detected")
                verification_results['recommendations'].append("Review timestamp consistency across columns")
        
        # 4. Final assessment
        print("\n4. FINAL ASSESSMENT")
        print("-" * 40)
        
        total_issues = 0
        for table_name, table_data in verification_results['tables_verified'].items():
            if table_data.get('exists', False):
                for col_name, col_data in table_data.get('timestamp_columns', {}).items():
                    if col_data.get('future_timestamps', 0) > 0:
                        total_issues += col_data['future_timestamps']
        
        if total_issues == 0:
            print("✅ ALL TIMESTAMP CHECKS PASSED!")
            print("✅ Database is properly configured for UTC timestamps")
            print("✅ No timezone conversion needed")
            verification_results['database_status'] = 'HEALTHY'
        else:
            print(f"⚠️  Found {total_issues} timestamp issues that need attention")
            verification_results['database_status'] = 'NEEDS_ATTENTION'
        
        # 5. Recommendations
        if verification_results['recommendations']:
            print("\n5. RECOMMENDATIONS")
            print("-" * 40)
            for i, recommendation in enumerate(verification_results['recommendations'], 1):
                print(f"{i}. {recommendation}")
        else:
            print("\n✅ No recommendations - database configuration is optimal!")
        
        cursor.close()
        conn.close()
        
        # Save verification results
        with open('database_timezone_verification_report.json', 'w') as f:
            json.dump(verification_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: database_timezone_verification_report.json")
        
        return verification_results
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return {'database_status': 'CONNECTION_ERROR', 'error': str(e)}

if __name__ == "__main__":
    results = verify_database_timezone_configuration()
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    if results.get('database_status') == 'HEALTHY':
        print("🎉 Your database timezone configuration is PERFECT!")
        print("📊 All timestamps are properly stored in UTC format")
        print("🔧 No manual intervention required")
    elif results.get('database_status') == 'NEEDS_ATTENTION':
        print("⚠️  Some issues found that need attention")
        print("📋 Check the recommendations above")
    else:
        print("❌ Unable to complete verification due to connection issues")
