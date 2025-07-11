#!/usr/bin/env python3
"""
SAFE Database Schema Verification Script (PRODUCTION-SAFE)

This script ONLY performs READ-ONLY operations:
1. Checks database schema consistency with code expectations
2. Verifies timezone handling for timestamp columns
3. Examines existing data format (READ-ONLY)
4. Compares actual database schema with code insert logic

NO DATA IS INSERTED, MODIFIED, OR DELETED
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor
    DB_AVAILABLE = True
except ImportError:
    log.error("psycopg2 not available - cannot run database verification")
    DB_AVAILABLE = False
    exit(1)

from atm_config import get_db_config, DILI_TIMEZONE

class SafeDatabaseVerifier:
    """PRODUCTION-SAFE database schema verifier - READ-ONLY operations only"""
    
    def __init__(self):
        self.db_config = get_db_config()
        self.dili_tz = pytz.timezone(DILI_TIMEZONE)
        
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config["host"],
            port=self.db_config["port"],
            database=self.db_config["database"],
            user=self.db_config["user"],
            password=self.db_config["password"]
        )
    
    def check_timezone_handling(self):
        """Check how timestamps are being handled in the database (READ-ONLY)"""
        log.info("=== Checking Timezone Handling (READ-ONLY) ===")
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check database timezone
            cursor.execute("SHOW timezone;")
            result = cursor.fetchone()
            db_timezone = result[0] if result else 'Unknown'
            log.info(f"Database timezone: {db_timezone}")
            
            # Check current timestamp with timezone
            cursor.execute("SELECT CURRENT_TIMESTAMP as current_ts, CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Dili' as dili_ts;")
            result = cursor.fetchone()
            if result:
                log.info(f"Database current timestamp: {result['current_ts']}")
                log.info(f"Dili timezone timestamp: {result['dili_ts']}")
            else:
                log.warning("Could not retrieve timestamp information")
            
            # Check Python timezone handling
            now_utc = datetime.now(pytz.UTC)
            now_dili = datetime.now(self.dili_tz)
            log.info(f"Python UTC timestamp: {now_utc}")
            log.info(f"Python Dili timestamp: {now_dili}")
            
            return True
            
        except Exception as e:
            log.error(f"Error checking timezone handling: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def verify_table_schemas(self):
        """Verify the actual table schemas match our expectations (READ-ONLY)"""
        log.info("=== Verifying Table Schemas (READ-ONLY) ===")
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            tables_to_check = [
                'regional_data',
                'terminal_details', 
                'terminal_cash_information'
            ]
            
            for table_name in tables_to_check:
                log.info(f"\nChecking table: {table_name}")
                
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                result = cursor.fetchone()
                exists = result['exists'] if result else False
                if not exists:
                    log.warning(f"Table {table_name} does not exist")
                    continue
                
                # Get column information
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                log.info(f"Table {table_name} columns:")
                for col in columns:
                    log.info(f"  {col['column_name']}: {col['data_type']} "
                           f"(nullable: {col['is_nullable']}, default: {col['column_default']})")
                
                # Check for timestamp columns specifically
                timestamp_columns = [col for col in columns if 'timestamp' in col['data_type'].lower()]
                if timestamp_columns:
                    log.info(f"  Timestamp columns found: {[col['column_name'] for col in timestamp_columns]}")
            
            return True
            
        except Exception as e:
            log.error(f"Error verifying table schemas: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def compare_schema_with_code(self):
        """Compare database schema with code expectations (READ-ONLY)"""
        log.info("=== Comparing Schema with Code Expectations (READ-ONLY) ===")
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Define expected schemas from the code (based on atm_database.py)
            expected_schemas = {
                'regional_data': {
                    'columns': {
                        'id': 'serial',
                        'unique_request_id': 'text',
                        'region_code': 'character varying',
                        'count_available': 'integer',
                        'count_warning': 'integer', 
                        'count_zombie': 'integer',
                        'count_wounded': 'integer',
                        'count_out_of_service': 'integer',
                        'total_atms_in_region': 'integer',
                        'created_at': 'timestamp with time zone',
                        'retrieval_timestamp': 'timestamp with time zone',
                        'raw_regional_data': 'jsonb'
                    }
                },
                'terminal_details': {
                    'columns': {
                        'id': 'serial',
                        'unique_request_id': 'text',
                        'terminal_id': 'character varying',
                        'terminal_name': 'text',
                        'location': 'text',
                        'availability_status': 'character varying',
                        'card_status': 'character varying',
                        'cash_status': 'character varying',
                        'retrieved_date': 'timestamp with time zone',
                        'raw_terminal_data': 'jsonb'
                    }
                },
                'terminal_cash_information': {
                    'columns': {
                        'id': 'serial',
                        'unique_request_id': 'text',
                        'terminal_id': 'character varying',
                        'event_date': 'timestamp with time zone',
                        'retrieval_timestamp': 'timestamp with time zone',
                        'cash_information': 'jsonb'
                    }
                }
            }
            
            all_compatible = True
            
            for table_name, expected_schema in expected_schemas.items():
                log.info(f"\nAnalyzing table: {table_name}")
                
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                result = cursor.fetchone()
                exists = result['exists'] if result else False
                if not exists:
                    log.error(f"❌ Table {table_name} does not exist in database")
                    all_compatible = False
                    continue
                
                log.info(f"✅ Table {table_name} exists")
                
                # Get actual column information
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                actual_columns = {col['column_name']: col for col in cursor.fetchall()}
                
                # Compare expected vs actual columns
                expected_columns = expected_schema['columns']
                
                # Check for missing columns
                missing_columns = set(expected_columns.keys()) - set(actual_columns.keys())
                if missing_columns:
                    log.error(f"❌ Missing columns in {table_name}: {missing_columns}")
                    all_compatible = False
                
                # Check for extra columns (informational only)
                extra_columns = set(actual_columns.keys()) - set(expected_columns.keys())
                if extra_columns:
                    log.info(f"ℹ️ Extra columns in {table_name}: {extra_columns}")
                
                # Check column types
                for col_name, expected_type in expected_columns.items():
                    if col_name in actual_columns:
                        actual_type = actual_columns[col_name]['data_type']
                        
                        # Type compatibility check
                        type_compatible = self._check_type_compatibility(expected_type, actual_type)
                        
                        if type_compatible:
                            log.info(f"✅ {col_name}: {actual_type} (compatible with {expected_type})")
                        else:
                            log.error(f"❌ {col_name}: Expected {expected_type}, got {actual_type}")
                            all_compatible = False
                    
            return all_compatible
            
        except Exception as e:
            log.error(f"Error comparing schema with code: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _check_type_compatibility(self, expected_type: str, actual_type: str) -> bool:
        """Check if database type is compatible with expected type"""
        # Type mapping for compatibility
        type_mappings = {
            'serial': ['integer', 'bigint'],
            'text': ['text', 'character varying'],
            'character varying': ['character varying', 'text'],
            'integer': ['integer', 'bigint', 'smallint'],
            'timestamp with time zone': ['timestamp with time zone', 'timestamptz'],
            'jsonb': ['jsonb', 'json']
        }
        
        if expected_type in type_mappings:
            return actual_type in type_mappings[expected_type]
        else:
            return expected_type == actual_type
    
    def check_existing_data_format(self):
        """Check the format of existing data in the database (READ-ONLY)"""
        log.info("=== Checking Existing Data Format (READ-ONLY) ===")
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            tables_with_timestamps = [
                ('regional_data', ['created_at', 'retrieval_timestamp']),
                ('terminal_details', ['retrieved_date']),
                ('terminal_cash_information', ['retrieval_timestamp', 'event_date'])
            ]
            
            for table_name, timestamp_cols in tables_with_timestamps:
                log.info(f"\nChecking existing data in {table_name}:")
                
                # Check if table exists and has data
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
                    result = cursor.fetchone()
                    count = result['count'] if result else 0
                    log.info(f"  Records count: {count}")
                    
                    if count > 0:
                        # Get sample of recent records
                        for col in timestamp_cols:
                            try:
                                cursor.execute(f"""
                                    SELECT {col}, EXTRACT(timezone FROM {col}) as tz_offset
                                    FROM {table_name} 
                                    WHERE {col} IS NOT NULL
                                    ORDER BY {col} DESC 
                                    LIMIT 3;
                                """)
                                
                                samples = cursor.fetchall()
                                log.info(f"  Sample {col} values:")
                                for sample in samples:
                                    log.info(f"    {sample[col]} (tz offset: {sample['tz_offset']} seconds)")
                                    
                            except Exception as e:
                                log.warning(f"    Could not check {col}: {e}")
                                
                except Exception as e:
                    log.warning(f"  Could not access table {table_name}: {e}")
            
            return True
            
        except Exception as e:
            log.error(f"Error checking existing data format: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        log.info("=== Recommendations ===")
        
        log.info("1. SCHEMA COMPATIBILITY:")
        log.info("   - Ensure all required columns exist in production tables")
        log.info("   - Verify data types match code expectations")
        log.info("   - Check for any missing JSONB or timestamp columns")
        
        log.info("\n2. TIMEZONE HANDLING:")
        log.info("   - All timestamp columns should use 'timestamp with time zone'")
        log.info("   - Ensure consistent Dili timezone (+09:00) usage")
        log.info("   - Verify created_at defaults to CURRENT_TIMESTAMP")
        
        log.info("\n3. CODE ALIGNMENT:")
        log.info("   - Update insert statements if schema mismatches found")
        log.info("   - Ensure JSONB columns use json.dumps() for compatibility")
        log.info("   - Use timezone-aware datetime objects for all inserts")
        
        log.info("\n4. PRODUCTION SAFETY:")
        log.info("   - Test inserts in staging environment first")
        log.info("   - Monitor timezone offset in stored data")
        log.info("   - Consider adding database constraints for data integrity")
    
    def run_safe_verification(self):
        """Run complete READ-ONLY database verification"""
        log.info("🛡️  Starting SAFE database verification (READ-ONLY operations)...")
        log.info("🚨 NO DATA WILL BE INSERTED, MODIFIED, OR DELETED")
        
        results = {
            'timezone_check': self.check_timezone_handling(),
            'schema_verification': self.verify_table_schemas(),
            'schema_code_comparison': self.compare_schema_with_code(),
            'data_format_check': self.check_existing_data_format()
        }
        
        self.generate_recommendations()
        
        log.info("\n=== VERIFICATION RESULTS ===")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            log.info(f"{test}: {status}")
        
        all_passed = all(results.values())
        final_status = "✅ PASS" if all_passed else "⚠️  ISSUES FOUND"
        log.info(f"\nOverall result: {final_status}")
        
        if not all_passed:
            log.warning("\n⚠️  Please review the issues above before running data inserts")
            log.warning("🔧 Consider updating code or database schema as recommended")
        else:
            log.info("\n🎉 Database schema is compatible with code expectations!")
            log.info("✅ Safe to proceed with data insertion operations")
        
        return all_passed

if __name__ == "__main__":
    print("🛡️  SAFE ATM Database Schema Verification Tool")
    print("🚨 READ-ONLY OPERATIONS ONLY - PRODUCTION SAFE")
    print("=" * 60)
    
    verifier = SafeDatabaseVerifier()
    success = verifier.run_safe_verification()
    
    if success:
        print("\n✅ SUCCESS: Database verification completed")
        print("🚀 Schema is compatible - safe to proceed")
    else:
        print("\n⚠️  WARNING: Schema issues found")
        print("🔧 Please review the recommendations above")
    
    print("\n" + "=" * 60)
    input("Press Enter to exit...")
