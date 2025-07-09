#!/usr/bin/env python3
"""
Database Schema Inspector (Extended)

This script checks the existing database schema for ATM-related tables
and compares them with the current insert operations in the code.

It generates a comprehensive report of any discrepancies and provides
recommendations for fixes.
"""

import os
import json
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_schema_check.log'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)

# Load environment variables from .env or .env_fastapi.example
if os.path.exists('.env'):
    load_dotenv('.env')
else:
    load_dotenv('.env_fastapi.example')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Tables to check
TABLES = [
    'terminal_details',
    'regional_atm_counts',
    'atm_cash_info',
    'regional_data',
    'terminal_cash_information',
]

def print_table_schema(conn, table_name):
    """Print the schema for the specified table"""
    with conn.cursor() as cur:
        print(f'\n--- Schema for table: {table_name} ---')
        try:
            cur.execute(sql.SQL("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """), [table_name])
            rows = cur.fetchall()
            if not rows:
                print(f"Table '{table_name}' does not exist or has no columns.")
                return None
            print(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default'}")
            print('-' * 70)
            schema_data = []
            for col, typ, nullable, default in rows:
                print(f"{col:<25} {typ:<20} {nullable:<10} {default}")
                schema_data.append({
                    'column_name': col,
                    'data_type': typ,
                    'is_nullable': nullable,
                    'default': default
                })
            return schema_data
        except Exception as e:
            print(f"Error fetching schema for {table_name}: {e}")
            return None

def get_insert_statements(table_name):
    """Find insert statements for the specified table in the codebase"""
    # This is a simplified implementation - in reality, we would need to parse files
    if table_name == 'terminal_details':
        return """
        INSERT INTO terminal_details 
        (unique_request_id, terminal_id, location, issue_state_name, 
        serial_number, retrieved_date, fetched_status, raw_terminal_data, 
        fault_data, metadata) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    elif table_name == 'regional_atm_counts':
        return """
        INSERT INTO regional_atm_counts 
        (unique_request_id, region_code, count_available, count_warning, 
        count_zombie, count_wounded, count_out_of_service, 
        date_creation, total_atms_in_region, percentage_available, 
        percentage_warning, percentage_zombie, percentage_wounded, 
        percentage_out_of_service) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    elif table_name == 'atm_cash_info':
        return """
        INSERT INTO atm_cash_info 
        (unique_request_id, terminal_id, business_code, technical_code, 
        external_id, retrieval_timestamp, event_date, total_cash_amount, 
        total_currency, cassettes_data, raw_cash_data) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    elif table_name == 'regional_data':
        return """
        INSERT INTO regional_data (
        unique_request_id, region_code, count_available, count_warning,
        count_zombie, count_wounded, count_out_of_service,
        total_atms_in_region, retrieval_timestamp, raw_regional_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    elif table_name == 'terminal_cash_information':
        return """
        INSERT INTO terminal_cash_information (
        unique_request_id, terminal_id, business_code, technical_code,
        external_id, retrieval_timestamp, event_date, total_cash_amount,
        total_currency, cassettes_data, raw_cash_data, cassette_count,
        has_low_cash_warning, has_cash_errors
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    else:
        return "No insert statements found."

def check_script_compatibility(schema_data, insert_statement):
    """Check if the insert statement is compatible with the schema"""
    if not schema_data:
        return "Table does not exist, cannot check compatibility."
    
    # Parse the insert statement to extract columns
    try:
        # Very simple parser - assumes clean formatting
        columns_start = insert_statement.find('(') + 1
        columns_end = insert_statement.find(')')
        columns_str = insert_statement[columns_start:columns_end]
        columns = [col.strip() for col in columns_str.split(',')]
        
        # Check if all columns in the insert exist in the schema
        schema_columns = [col['column_name'] for col in schema_data]
        missing_columns = []
        for col in columns:
            if col not in schema_columns:
                missing_columns.append(col)
        
        if missing_columns:
            return f"The following columns in the insert statement don't exist in the schema: {', '.join(missing_columns)}"
        else:
            return "Insert statement is compatible with the schema."
    except Exception as e:
        return f"Error checking compatibility: {e}"

def generate_report(results):
    """Generate a report of the schema check results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": timestamp,
        "tables": results,
        "recommendations": []
    }
    
    # Generate recommendations
    for table_name, result in results.items():
        if result["schema"] is None:
            report["recommendations"].append(f"Create table '{table_name}' as it doesn't exist in the database.")
        elif "not compatible" in result["compatibility"]:
            report["recommendations"].append(f"Update insert statements for '{table_name}' to match the schema.")
    
    # Save the report to a file
    filename = f"database_schema_analysis_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=4)
    
    log.info(f"Report saved to {filename}")

def main():
    """Main function to check database schema"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        results = {}
        for table in TABLES:
            schema_data = print_table_schema(conn, table)
            insert_statement = get_insert_statements(table)
            compatibility = "N/A" if schema_data is None else check_script_compatibility(schema_data, insert_statement)
            
            results[table] = {
                "schema": schema_data,
                "insert_statement": insert_statement,
                "compatibility": compatibility
            }
        
        conn.close()
        
        # Generate a report
        generate_report(results)
        
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == '__main__':
    main()
