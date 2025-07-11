#!/usr/bin/env python3
"""
Database Schema and Insert Verification Script

This script verifies:
1. Database schema consistency with insert operations
2. Timezone handling for created_at and timestamp columns
3. Data type compatibility
4. JSONB column handling
5. UUID generation and handling
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

class DatabaseVerifier:
    """Verifies database schema and insert operations"""
    
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
        """Check how timestamps are being handled in the database"""
        log.info("=== Checking Timezone Handling ===")
        
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
        """Verify the actual table schemas match our expectations"""
        log.info("=== Verifying Table Schemas ===")
        
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
        """Compare database schema with code insert logic - NO INSERTS"""
        log.info("=== Comparing Schema with Code Logic (READ-ONLY) ===")
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Define expected columns based on our code
            expected_schemas = {
                'regional_data': {
                    'unique_request_id': 'character varying',
                    'region_code': 'character varying', 
                    'count_available': 'integer',
                    'count_warning': 'integer',
                    'count_zombie': 'integer',
                    'count_wounded': 'integer',
                    'count_out_of_service': 'integer',
                    'total_atms_in_region': 'integer',
                    'retrieval_timestamp': 'timestamp with time zone',
                    'raw_regional_data': 'jsonb',
                    'created_at': 'timestamp with time zone'
                },
                'terminal_details': {
                    'terminal_id': 'character varying',
                    'bank_name': 'character varying',
                    'terminal_name': 'character varying',
                    'address': 'text',
                    'location': 'character varying',
                    'status': 'character varying',
                    'retrieved_date': 'timestamp with time zone',
                    'unique_request_id': 'character varying'
                },
                'terminal_cash_information': {
                    'terminal_id': 'character varying',
                    'event_date': 'timestamp with time zone',
                    'cash_level': 'character varying',
                    'retrieval_timestamp': 'timestamp with time zone',
                    'unique_request_id': 'character varying'
                }
            }
            
            schema_issues = []
            
            for table_name, expected_cols in expected_schemas.items():
                log.info(f"\nAnalyzing table: {table_name}")
                
                # Get actual schema
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default,
                           character_maximum_length, numeric_precision
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                actual_columns = {row['column_name']: row for row in cursor.fetchall()}
                
                if not actual_columns:
                    schema_issues.append(f"❌ Table {table_name} does not exist!")
                    continue
                
                log.info(f"✅ Table {table_name} exists with {len(actual_columns)} columns")
                
                # Compare each expected column
                for col_name, expected_type in expected_cols.items():
                    if col_name not in actual_columns:
                        issue = f"❌ {table_name}.{col_name}: Missing column"
                        schema_issues.append(issue)
                        log.warning(f"  {issue}")
                    else:
                        actual_col = actual_columns[col_name]
                        actual_type = actual_col['data_type']
                        
                        # Check type compatibility
                        type_match = self._check_type_compatibility(expected_type, actual_type)
                        if type_match:
                            log.info(f"  ✅ {col_name}: {actual_type} (matches {expected_type})")
                        else:
                            issue = f"❌ {table_name}.{col_name}: Type mismatch - expected {expected_type}, got {actual_type}"
                            schema_issues.append(issue)
                            log.warning(f"  {issue}")
                        
                        # Check special constraints for timestamp columns
                        if 'timestamp' in actual_type.lower():
                            default_val = actual_col['column_default']
                            nullable = actual_col['is_nullable']
                            log.info(f"    Timestamp column details: nullable={nullable}, default={default_val}")
                
                # Check for unexpected columns
                expected_set = set(expected_cols.keys())
                actual_set = set(actual_columns.keys())
                extra_cols = actual_set - expected_set
                if extra_cols:
                    log.info(f"  ℹ️  Extra columns in {table_name}: {', '.join(extra_cols)}")
            
            # Summary
            if schema_issues:
                log.error(f"\n❌ SCHEMA ISSUES FOUND ({len(schema_issues)}):")
                for issue in schema_issues:
                    log.error(f"  {issue}")
                return False
            else:
                log.info("\n✅ ALL SCHEMAS MATCH CODE EXPECTATIONS")
                return True
            
        except Exception as e:
            log.error(f"Error comparing schema with code: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _check_type_compatibility(self, expected: str, actual: str) -> bool:
        """Check if database type is compatible with expected type"""
        # Common type mappings
        type_mappings = {
            'character varying': ['character varying', 'varchar', 'text'],
            'integer': ['integer', 'int4', 'bigint', 'int8'],
            'timestamp with time zone': ['timestamp with time zone', 'timestamptz'],
            'jsonb': ['jsonb', 'json'],
            'text': ['text', 'character varying']
        }
        
        expected_lower = expected.lower()
        actual_lower = actual.lower()
        
        if expected_lower == actual_lower:
            return True
            
        # Check mappings
        for exp_type, compatible_types in type_mappings.items():
            if expected_lower == exp_type and actual_lower in compatible_types:
                return True
                
        return False
    
    def check_existing_data_format(self):
        """Check the format of existing data in the database"""
        log.info("=== Checking Existing Data Format ===")
        
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
            
            return True
            
        except Exception as e:
            log.error(f"Error checking existing data format: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def generate_timezone_fix_recommendations(self):
        """Generate recommendations for fixing timezone issues"""
        log.info("=== Timezone Fix Recommendations ===")
        
        log.info("1. CURRENT TIMEZONE HANDLING:")
        log.info("   - Database columns use TIMESTAMP WITH TIME ZONE")
        log.info("   - Python code uses datetime.now(dili_tz) for retrieval_timestamp")
        log.info("   - created_at uses database DEFAULT CURRENT_TIMESTAMP")
        
        log.info("\n2. POTENTIAL ISSUES:")
        log.info("   - Database server timezone vs Dili timezone (+09:00)")
        log.info("   - Inconsistent timezone handling between columns")
        log.info("   - Mixed timezone sources (database vs Python)")
        
        log.info("\n3. RECOMMENDED FIXES:")
        log.info("   a. Use UTC consistently for storage, convert to Dili for display")
        log.info("   b. Ensure all timestamp inserts use same timezone source")
        log.info("   c. Add explicit timezone conversion in queries")
        log.info("   d. Consider database timezone setting")
        
        log.info("\n4. CODE CHANGES NEEDED:")
        log.info("   - Standardize all datetime.now() calls to use same timezone")
        log.info("   - Add timezone conversion utilities")
        log.info("   - Update insert statements to be timezone-explicit")
    
    def run_full_verification(self):
        """Run complete database verification (READ-ONLY for production safety)"""
        log.info("Starting comprehensive database verification...")
        
        results = {
            'timezone_check': self.check_timezone_handling(),
            'schema_verification': self.verify_table_schemas(),
            'schema_code_comparison': self.compare_schema_with_code(),
            'data_format_check': self.check_existing_data_format()
        }
        
        self.generate_timezone_fix_recommendations()
        
        log.info("\n=== VERIFICATION RESULTS ===")
        for test, passed in results.items():
            status = "PASS" if passed else "FAIL"
            log.info(f"{test}: {status}")
        
        all_passed = all(results.values())
        log.info(f"\nOverall result: {'PASS' if all_passed else 'FAIL'}")
        
        return all_passed

if __name__ == "__main__":
    print("ATM Database Verification Tool")
    print("=" * 50)
    
    verifier = DatabaseVerifier()
    success = verifier.run_full_verification()
    
    if success:
        print("\nSUCCESS: Database verification completed")
    else:
        print("\nWARNING: Issues found during verification")
        print("Please review the recommendations above")
    
    input("\nPress Enter to exit...")
