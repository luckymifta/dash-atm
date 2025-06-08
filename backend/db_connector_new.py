#!/usr/bin/env python3
"""
Database Connector for ATM Data Retrieval System
Supports PostgreSQL with new credentials for development_db
"""

import psycopg2
import psycopg2.extras
import psycopg2.extensions
import logging
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("DatabaseConnector")

# Database configuration
DB_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

class DatabaseConnector:
    """Database connector for ATM data storage and retrieval"""
    
    def __init__(self):
        """Initialize the database connector"""
        self.config = DB_CONFIG
        
    def get_db_connection(self) -> Optional[psycopg2.extensions.connection]:
        """
        Get a database connection
        
        Returns:
            psycopg2 connection object or None if connection fails
        """
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            conn.autocommit = False
            log.info("Successfully connected to PostgreSQL database")
            return conn
        except psycopg2.Error as e:
            log.error(f"Error connecting to PostgreSQL database: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the database connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                if version:
                    log.info(f"PostgreSQL version: {version[0]}")
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                log.error(f"Error testing connection: {e}")
                if conn:
                    conn.close()
                return False
        return False
    
    def create_tables(self) -> bool:
        """
        Create all required tables for ATM data storage
        
        Returns:
            bool: True if successful, False otherwise
        """
        conn = self.get_db_connection()
        if not conn:
            log.error("Failed to connect to database for table creation")
            return False
        
        cursor = conn.cursor()
        
        try:
            # Create regional_data table
            log.info("Creating regional_data table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_data (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    region_code VARCHAR(10) NOT NULL,
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    raw_regional_data JSONB NOT NULL,
                    count_available INTEGER DEFAULT 0,
                    count_warning INTEGER DEFAULT 0,
                    count_zombie INTEGER DEFAULT 0,
                    count_wounded INTEGER DEFAULT 0,
                    count_out_of_service INTEGER DEFAULT 0,
                    total_atms_in_region INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for regional_data
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_region_timestamp 
                ON regional_data(region_code, retrieval_timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_raw_jsonb 
                ON regional_data USING GIN(raw_regional_data)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_unique_request 
                ON regional_data(unique_request_id)
            """)
            
            # Create terminal_details table
            log.info("Creating terminal_details table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminal_details (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    terminal_id VARCHAR(50) NOT NULL,
                    location TEXT,
                    issue_state_name VARCHAR(50),
                    serial_number VARCHAR(50),
                    retrieved_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    fetched_status VARCHAR(50) NOT NULL,
                    raw_terminal_data JSONB NOT NULL,
                    fault_data JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for terminal_details
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_terminal_id 
                ON terminal_details(terminal_id, retrieved_date DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_fetched_status 
                ON terminal_details(fetched_status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_raw_jsonb 
                ON terminal_details USING GIN(raw_terminal_data)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_fault_jsonb 
                ON terminal_details USING GIN(fault_data)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_metadata_jsonb 
                ON terminal_details USING GIN(metadata)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_unique_request 
                ON terminal_details(unique_request_id)
            """)
            
            # Create legacy table for compatibility (optional)
            log.info("Creating legacy regional_atm_counts table for compatibility...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_atm_counts (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    region_code VARCHAR(10) NOT NULL,
                    count_available INTEGER DEFAULT 0,
                    count_warning INTEGER DEFAULT 0,
                    count_zombie INTEGER DEFAULT 0,
                    count_wounded INTEGER DEFAULT 0,
                    count_out_of_service INTEGER DEFAULT 0,
                    date_creation TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    total_atms_in_region INTEGER DEFAULT 0,
                    percentage_available DECIMAL(10,8) DEFAULT 0.0,
                    percentage_warning DECIMAL(10,8) DEFAULT 0.0,
                    percentage_zombie DECIMAL(10,8) DEFAULT 0.0,
                    percentage_wounded DECIMAL(10,8) DEFAULT 0.0,
                    percentage_out_of_service DECIMAL(10,8) DEFAULT 0.0
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_atm_counts_region_date 
                ON regional_atm_counts(region_code, date_creation DESC)
            """)
            
            # Create update timestamp triggers
            log.info("Creating update timestamp triggers...")
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_regional_data_updated_at ON regional_data;
                CREATE TRIGGER update_regional_data_updated_at 
                    BEFORE UPDATE ON regional_data 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_terminal_details_updated_at ON terminal_details;
                CREATE TRIGGER update_terminal_details_updated_at 
                    BEFORE UPDATE ON terminal_details 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
            
            conn.commit()
            log.info("All tables and indexes created successfully")
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Error creating tables: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def check_regional_atm_counts_table(self) -> bool:
        """
        Check if regional_atm_counts table exists (for legacy compatibility)
        
        Returns:
            bool: True if table exists, False otherwise
        """
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'regional_atm_counts'
                );
            """)
            result = cursor.fetchone()
            exists = result[0] if result else False
            log.info(f"regional_atm_counts table exists: {exists}")
            return exists
        except Exception as e:
            log.error(f"Error checking table existence: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about existing tables
        
        Returns:
            Dict with table information
        """
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor()
        table_info = {}
        
        try:
            # Get table names
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            table_info['tables'] = tables
            
            # Get row counts for each table
            table_info['row_counts'] = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    table_info['row_counts'][table] = count
                except Exception as e:
                    table_info['row_counts'][table] = f"Error: {e}"
            
            return table_info
            
        except Exception as e:
            log.error(f"Error getting table info: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()


# Global instance for compatibility with existing code
db_connector = DatabaseConnector()

def get_db_connection():
    """Global function for compatibility"""
    return db_connector.get_db_connection()

def check_regional_atm_counts_table():
    """Global function for compatibility"""
    return db_connector.check_regional_atm_counts_table()

if __name__ == "__main__":
    # Test the connection and create tables
    connector = DatabaseConnector()
    
    print("Testing database connection...")
    if connector.test_connection():
        print("✅ Database connection successful!")
        
        print("\nCreating tables...")
        if connector.create_tables():
            print("✅ Tables created successfully!")
            
            print("\nTable information:")
            info = connector.get_table_info()
            for table in info.get('tables', []):
                count = info.get('row_counts', {}).get(table, 'Unknown')
                print(f"  {table}: {count} rows")
        else:
            print("❌ Failed to create tables")
    else:
        print("❌ Database connection failed")
