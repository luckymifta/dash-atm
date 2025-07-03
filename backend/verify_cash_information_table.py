#!/usr/bin/env python3
"""
Script to verify the terminal_cash_information table structure and data.

This script:
1. Checks if the table exists
2. Validates the table structure/schema
3. Shows sample data (if available)
4. Performs basic integrity checks

Usage:
    python verify_cash_information_table.py [--verbose] [--sample-size N]
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Try to import required packages
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 package is required but not installed.")
    print("Install it using: pip install psycopg2-binary")
    sys.exit(1)

# Set up command line arguments
parser = argparse.ArgumentParser(description="Verify the terminal_cash_information table")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
parser.add_argument("--sample-size", type=int, default=5, help="Number of sample records to display")
args = parser.parse_args()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not args.verbose else logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("verify_cash_table")

# Expected table structure
EXPECTED_COLUMNS = {
    "id": {"type": "integer", "nullable": False},
    "unique_request_id": {"type": "uuid", "nullable": False},
    "terminal_id": {"type": "character varying", "nullable": False},
    "business_code": {"type": "character varying", "nullable": True},
    "technical_code": {"type": "character varying", "nullable": True},
    "external_id": {"type": "character varying", "nullable": True},
    "retrieval_timestamp": {"type": "timestamp with time zone", "nullable": False},
    "event_date": {"type": "timestamp with time zone", "nullable": True},
    "total_cash_amount": {"type": "numeric", "nullable": True},
    "total_currency": {"type": "character varying", "nullable": True},
    "cassettes_data": {"type": "jsonb", "nullable": False},
    "raw_cash_data": {"type": "jsonb", "nullable": True},
    "cassette_count": {"type": "integer", "nullable": True},
    "has_low_cash_warning": {"type": "boolean", "nullable": True},
    "has_cash_errors": {"type": "boolean", "nullable": True},
    "is_null_record": {"type": "boolean", "nullable": True},
    "null_reason": {"type": "text", "nullable": True},
    "created_at": {"type": "timestamp with time zone", "nullable": True}
}

# Expected indexes
EXPECTED_INDEXES = [
    {"name": "idx_terminal_cash_terminal_id", "columns": ["terminal_id"]},
    {"name": "idx_terminal_cash_timestamp", "columns": ["retrieval_timestamp"]}
]

def get_db_connection() -> Optional[psycopg2.extensions.connection]:
    """Get a database connection using environment variables"""
    try:
        db_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": os.environ.get("DB_PORT", "5432"),
            "database": os.environ.get("DB_NAME", "atm_monitor"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", "")
        }
        
        log.debug(f"Connecting to database {db_config['database']} on {db_config['host']}:{db_config['port']}")
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            dbname=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )
        
        return conn
    except Exception as e:
        log.error(f"Failed to connect to database: {str(e)}")
        return None

def check_table_exists(conn: psycopg2.extensions.connection) -> bool:
    """Check if terminal_cash_information table exists"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'terminal_cash_information'
            );
        """)
        result = cursor.fetchone()
        exists = result[0] if result else False
        
        if exists:
            log.info("✅ Table terminal_cash_information exists")
        else:
            log.error("❌ Table terminal_cash_information does not exist")
        
        return exists
    except Exception as e:
        log.error(f"Error checking if table exists: {str(e)}")
        return False
    finally:
        cursor.close()

def get_table_structure(conn: psycopg2.extensions.connection) -> List[Dict[str, Any]]:
    """Get the structure of the terminal_cash_information table"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'terminal_cash_information'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        column_details = []
        for col_name, data_type, is_nullable in columns:
            column_details.append({
                "name": col_name,
                "type": data_type,
                "nullable": is_nullable == "YES"
            })
        
        return column_details
    except Exception as e:
        log.error(f"Error getting table structure: {str(e)}")
        return []
    finally:
        cursor.close()

def get_table_indexes(conn: psycopg2.extensions.connection) -> List[Dict[str, Any]]:
    """Get the indexes on the terminal_cash_information table"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                i.relname as index_name,
                array_agg(a.attname) as column_names
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_attribute a
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND a.attrelid = t.oid
                AND a.attnum = ANY(ix.indkey)
                AND t.relkind = 'r'
                AND t.relname = 'terminal_cash_information'
            GROUP BY
                i.relname
            ORDER BY
                i.relname;
        """)
        indexes = cursor.fetchall()
        
        index_details = []
        for index_name, column_names in indexes:
            # Skip primary key as it's implicit
            if "pkey" not in index_name:
                index_details.append({
                    "name": index_name,
                    "columns": column_names
                })
        
        return index_details
    except Exception as e:
        log.error(f"Error getting table indexes: {str(e)}")
        return []
    finally:
        cursor.close()

def validate_table_structure(conn: psycopg2.extensions.connection) -> bool:
    """Validate the structure of the terminal_cash_information table"""
    columns = get_table_structure(conn)
    
    if not columns:
        return False
    
    log.info(f"Table has {len(columns)} columns")
    
    # Check each expected column
    all_valid = True
    for col_name, expected in EXPECTED_COLUMNS.items():
        found = False
        for col in columns:
            if col["name"] == col_name:
                found = True
                if expected["type"] not in col["type"]:
                    log.error(f"❌ Column {col_name} has wrong type: {col['type']} (expected: {expected['type']})")
                    all_valid = False
                if expected["nullable"] != col["nullable"]:
                    log.error(f"❌ Column {col_name} has wrong nullable setting: {col['nullable']} (expected: {expected['nullable']})")
                    all_valid = False
                break
                
        if not found:
            log.error(f"❌ Missing required column: {col_name}")
            all_valid = False
    
    # Check for unexpected columns
    column_names = set(c["name"] for c in columns)
    expected_names = set(EXPECTED_COLUMNS.keys())
    unexpected = column_names - expected_names
    
    if unexpected:
        log.warning(f"⚠️ Found unexpected columns: {', '.join(unexpected)}")
    
    # Check indexes
    indexes = get_table_indexes(conn)
    log.info(f"Table has {len(indexes)} custom indexes")
    
    for expected_index in EXPECTED_INDEXES:
        found = False
        for idx in indexes:
            if expected_index["name"] == idx["name"]:
                found = True
                if set(expected_index["columns"]) != set(idx["columns"]):
                    log.warning(f"⚠️ Index {idx['name']} has different columns: {idx['columns']} (expected: {expected_index['columns']})")
                break
                
        if not found:
            log.warning(f"⚠️ Missing recommended index: {expected_index['name']} on {expected_index['columns']}")
    
    if all_valid:
        log.info("✅ Table structure is valid")
    
    return all_valid

def get_sample_data(conn: psycopg2.extensions.connection, limit: int = 5) -> List[Dict[str, Any]]:
    """Get sample data from the terminal_cash_information table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            SELECT 
                id, unique_request_id, terminal_id, business_code, 
                retrieval_timestamp, total_cash_amount, total_currency,
                cassettes_data, cassette_count, has_low_cash_warning, has_cash_errors,
                is_null_record, null_reason
            FROM terminal_cash_information
            ORDER BY retrieval_timestamp DESC
            LIMIT {limit};
        """)
        rows = cursor.fetchall()
        
        # Get column names
        if cursor.description is None:
            log.error("No columns returned in query result")
            return []
            
        colnames = [desc[0] for desc in cursor.description]
        
        result = []
        for row in rows:
            record = {}
            for i, col in enumerate(colnames):
                if col == 'cassettes_data':
                    try:
                        # Format cassette data for better display
                        cassettes = row[i]
                        if cassettes:
                            record[col] = f"[{len(cassettes)} cassettes]"
                        else:
                            record[col] = "[]"
                    except Exception as e:
                        record[col] = str(row[i]) if row[i] is not None else "None"
                elif col == 'retrieval_timestamp':
                    # Format timestamp for better display
                    record[col] = row[i].strftime("%Y-%m-%d %H:%M:%S") if row[i] else None
                else:
                    record[col] = row[i]
            
            result.append(record)
        
        return result
    except Exception as e:
        log.error(f"Error getting sample data: {str(e)}")
        return []
    finally:
        cursor.close()

def get_table_stats(conn: psycopg2.extensions.connection) -> Dict[str, Any]:
    """Get statistics about the terminal_cash_information table"""
    cursor = conn.cursor()
    stats = {}
    
    try:
        # Total count
        cursor.execute("SELECT COUNT(*) FROM terminal_cash_information")
        result = cursor.fetchone()
        stats["total_records"] = result[0] if result else 0
        
        # Count by terminal
        cursor.execute("""
            SELECT terminal_id, COUNT(*) as count 
            FROM terminal_cash_information 
            GROUP BY terminal_id 
            ORDER BY count DESC
        """)
        result = cursor.fetchall()
        stats["records_by_terminal"] = dict(result) if result else {}
        
        # Count by date (last 7 days)
        cursor.execute("""
            SELECT 
                DATE(retrieval_timestamp) as date, 
                COUNT(*) as count 
            FROM terminal_cash_information 
            WHERE retrieval_timestamp > CURRENT_DATE - INTERVAL '7 days' 
            GROUP BY DATE(retrieval_timestamp) 
            ORDER BY date DESC
        """)
        results = cursor.fetchall()
        stats["records_by_date"] = {row[0].strftime("%Y-%m-%d"): row[1] for row in results} if results else {}
        
        # Cash warnings
        cursor.execute("SELECT COUNT(*) FROM terminal_cash_information WHERE has_low_cash_warning = TRUE")
        result = cursor.fetchone()
        stats["low_cash_warnings"] = result[0] if result else 0
        
        # Cash errors
        cursor.execute("SELECT COUNT(*) FROM terminal_cash_information WHERE has_cash_errors = TRUE")
        result = cursor.fetchone()
        stats["cash_errors"] = result[0] if result else 0
        
        # Null records
        cursor.execute("SELECT COUNT(*) FROM terminal_cash_information WHERE is_null_record = TRUE")
        result = cursor.fetchone()
        stats["null_records"] = result[0] if result else 0
        
        # Date range
        cursor.execute("""
            SELECT 
                MIN(retrieval_timestamp),
                MAX(retrieval_timestamp)
            FROM terminal_cash_information
        """)
        result = cursor.fetchone()
        if result:
            min_date, max_date = result
            if min_date and max_date:
                stats["first_record"] = min_date.strftime("%Y-%m-%d %H:%M:%S")
                stats["last_record"] = max_date.strftime("%Y-%m-%d %H:%M:%S")
                stats["date_span_days"] = (max_date - min_date).days
        
        return stats
    except Exception as e:
        log.error(f"Error getting table statistics: {str(e)}")
        return stats
    finally:
        cursor.close()

def main():
    """Main function to verify the terminal_cash_information table"""
    log.info("Starting terminal_cash_information table verification")
    
    # Connect to the database
    conn = get_db_connection()
    if not conn:
        log.error("Unable to connect to database. Please check your environment variables.")
        sys.exit(1)
    
    try:
        # Check if table exists
        if not check_table_exists(conn):
            log.error("The terminal_cash_information table does not exist. Please run the combined script to create it.")
            sys.exit(1)
        
        # Validate table structure
        validate_table_structure(conn)
        
        # Get table statistics
        stats = get_table_stats(conn)
        if stats:
            log.info("\n📊 TABLE STATISTICS:")
            log.info(f"  • Total records: {stats.get('total_records', 0):,}")
            
            if 'first_record' in stats and 'last_record' in stats:
                log.info(f"  • Date range: {stats.get('first_record')} to {stats.get('last_record')}")
                log.info(f"  • Span: {stats.get('date_span_days', 0)} days")
                
            log.info(f"  • Low cash warnings: {stats.get('low_cash_warnings', 0):,}")
            log.info(f"  • Cash errors: {stats.get('cash_errors', 0):,}")
            log.info(f"  • Null records: {stats.get('null_records', 0):,}")
            
            # Terminal counts
            terminal_counts = stats.get('records_by_terminal', {})
            if terminal_counts:
                log.info("\n  RECORDS PER TERMINAL:")
                for terminal, count in sorted(terminal_counts.items(), key=lambda x: x[1], reverse=True)[:10]:  # Top 10
                    log.info(f"  • {terminal}: {count:,}")
                
                if len(terminal_counts) > 10:
                    log.info(f"  • ... and {len(terminal_counts) - 10} more terminals")
            
            # Date counts
            date_counts = stats.get('records_by_date', {})
            if date_counts:
                log.info("\n  RECORDS PER DATE (last 7 days):")
                for date, count in sorted(date_counts.items(), reverse=True):
                    log.info(f"  • {date}: {count:,}")
        
        # Get sample data
        samples = get_sample_data(conn, args.sample_size)
        if samples:
            log.info(f"\n📋 SAMPLE DATA ({min(len(samples), args.sample_size)} records):")
            for i, sample in enumerate(samples):
                log.info(f"\n  Record #{i+1}:")
                for key, value in sample.items():
                    log.info(f"  • {key}: {value}")
        else:
            log.warning("No sample data available - table might be empty")
        
        log.info("\n✅ Terminal cash information table verification complete")
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
