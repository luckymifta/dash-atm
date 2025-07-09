"""
ATM Database Operations Module (Simplified)

Handles all database operations including saving regional data,
terminal details, and cash information to PostgreSQL database.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from atm_config import get_db_config, DILI_TIMEZONE

log = logging.getLogger(__name__)

# Check for database availability
try:
    import psycopg2
    from psycopg2 import sql
    DB_AVAILABLE = True
except ImportError:
    log.warning("psycopg2 not available - database operations will be disabled")
    DB_AVAILABLE = False
    psycopg2 = None

class ATMDatabaseManager:
    """Handles database operations for ATM monitoring data"""
    
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.dili_tz = pytz.timezone(DILI_TIMEZONE)
        self.db_config = get_db_config()
    
    def _get_connection(self):
        """Get database connection with proper parameter handling"""
        if not DB_AVAILABLE or not psycopg2:
            raise ValueError("Database not available")
        
        # Use proper connection parameters - explicit parameter names
        return psycopg2.connect(
            host=self.db_config["host"],
            port=self.db_config["port"], 
            database=self.db_config["database"],
            user=self.db_config["user"],
            password=self.db_config["password"]
        )
    
    def save_all_data(self, all_data: Dict[str, Any], use_new_tables: bool = False) -> bool:
        """
        Save all data to database (regional, terminal details, and cash information)
        
        Args:
            all_data: Dictionary containing all retrieved data
            use_new_tables: Whether to use new database tables with JSONB support
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode active - skipping database save")
            return True
        
        if not DB_AVAILABLE:
            log.warning("Database not available - skipping database save")
            return False
            
        success = True
        
        try:
            # Save regional data
            if 'regional_data' in all_data:
                success &= self.save_regional_data(all_data['regional_data'])
            
            # Save terminal details
            if 'terminal_details' in all_data:
                success &= self.save_terminal_details(all_data['terminal_details'])
            
            # Save cash information
            if 'cash_info' in all_data:
                success &= self.save_cash_info(all_data['cash_info'])
            
            log.info(f"Data save completed {'successfully' if success else 'with errors'}")
            return success
            
        except Exception as e:
            log.error(f"Error saving all data: {e}")
            return False
    
    def save_regional_data(self, regional_data: List[Dict[str, Any]]) -> bool:
        """
        Save regional data to database using the correct schema
        
        Args:
            regional_data: List of regional data dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE:
            log.warning("Database not available - skipping regional data save")
            return False
        
        if not regional_data:
            log.warning("No regional data to save")
            return True
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create table if not exists - using regional_data table with JSONB support
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_data (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    region_code VARCHAR(10) NOT NULL,
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    raw_regional_data JSONB NOT NULL DEFAULT '{}'::jsonb,
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
            
            # Create indexes if they don't exist
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_region_timestamp 
                ON regional_data(region_code, retrieval_timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_raw_jsonb 
                ON regional_data USING GIN(raw_regional_data)
            """)
            
            # Insert data using the updated schema
            for region in regional_data:
                # Prepare raw data as a JSON object
                raw_json_data = json.dumps(region)
                
                cursor.execute("""
                    INSERT INTO regional_data (
                        unique_request_id, region_code, count_available, count_warning,
                        count_zombie, count_wounded, count_out_of_service,
                        total_atms_in_region, retrieval_timestamp, raw_regional_data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    region.get('unique_request_id'),
                    region.get('region_code'),
                    region.get('count_available', 0),
                    region.get('count_warning', 0),
                    region.get('count_zombie', 0),
                    region.get('count_wounded', 0),
                    region.get('count_out_of_service', 0),
                    region.get('total_atms_in_region', 0),
                    datetime.now(self.dili_tz),
                    raw_json_data
                ))
            
            conn.commit()
            log.info(f"Successfully saved {len(regional_data)} regional data records to regional_data table")
            return True
            
        except Exception as e:
            log.error(f"Error saving regional data: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def save_terminal_details(self, terminal_details: List[Dict[str, Any]]) -> bool:
        """
        Save terminal details to database
        
        Args:
            terminal_details: List of terminal detail dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE:
            log.warning("Database not available - skipping terminal details save")
            return False
        
        if not terminal_details:
            log.warning("No terminal details to save")
            return True
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create table if not exists - matching the new terminal_details schema
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
                    metadata JSONB
                )
            """)
            
            # Insert data matching the actual terminal details structure
            for terminal in terminal_details:
                # Prepare fault data
                fault_data = {
                    'year': terminal.get('year', ''),
                    'month': terminal.get('month', ''),
                    'day': terminal.get('day', ''),
                    'externalFaultId': terminal.get('externalFaultId', ''),
                    'agentErrorDescription': terminal.get('agentErrorDescription', ''),
                    'creationDate': terminal.get('creationDate', '')
                }
                
                # Prepare metadata
                metadata = {
                    'retrieval_timestamp': terminal.get('retrievedDate'),
                    'unique_request_id': terminal.get('unique_request_id')
                }
                
                cursor.execute("""
                    INSERT INTO terminal_details 
                    (unique_request_id, terminal_id, location, issue_state_name, 
                     serial_number, retrieved_date, fetched_status, raw_terminal_data, 
                     fault_data, metadata) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    terminal.get('unique_request_id'),
                    terminal.get('terminalId'),
                    terminal.get('location'),
                    terminal.get('issueStateName'),
                    terminal.get('serialNumber'),
                    terminal.get('retrievedDate'),
                    terminal.get('fetched_status'),
                    json.dumps(terminal),  # Store the complete terminal data
                    json.dumps(fault_data),
                    json.dumps(metadata)
                ))
            
            conn.commit()
            log.info(f"Successfully saved {len(terminal_details)} terminal detail records")
            return True
            
        except Exception as e:
            log.error(f"Error saving terminal details: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def save_cash_info(self, cash_info: List[Dict[str, Any]]) -> bool:
        """
        Save cash information to database using terminal_cash_information table
        
        Args:
            cash_info: List of terminal cash information dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE:
            log.warning("Database not available - skipping cash info save")
            return False
        
        if not cash_info:
            log.warning("No cash information to save")
            return True
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create table if not exists - using the terminal_cash_information schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminal_cash_information (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    terminal_id VARCHAR(50) NOT NULL,
                    business_code VARCHAR(20),
                    technical_code VARCHAR(20),
                    external_id VARCHAR(20),
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    event_date TIMESTAMP WITH TIME ZONE,
                    total_cash_amount DECIMAL(15,2) DEFAULT 0.00,
                    total_currency VARCHAR(10),
                    cassettes_data JSONB NOT NULL,
                    raw_cash_data JSONB,
                    cassette_count INTEGER DEFAULT 0,
                    has_low_cash_warning BOOLEAN DEFAULT false,
                    has_cash_errors BOOLEAN DEFAULT false
                )
            """)
            
            # Insert data using the terminal_cash_information schema
            for cash in cash_info:
                # Calculate additional fields for the enhanced schema
                cassettes = cash.get('cassettes_data', [])
                cassette_count = len(cassettes)
                has_low_cash_warning = any(cassette.get('lowCashWarning', False) for cassette in cassettes)
                has_cash_errors = any(cassette.get('error', False) for cassette in cassettes)
                
                cursor.execute("""
                    INSERT INTO terminal_cash_information (
                        unique_request_id,
                        terminal_id,
                        business_code,
                        technical_code,
                        external_id,
                        retrieval_timestamp,
                        event_date,
                        total_cash_amount,
                        total_currency,
                        cassettes_data,
                        raw_cash_data,
                        cassette_count,
                        has_low_cash_warning,
                        has_cash_errors
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    cash.get('unique_request_id'),
                    cash.get('terminal_id'),
                    cash.get('business_code'),
                    cash.get('technical_code'),
                    cash.get('external_id'),
                    cash.get('retrieval_timestamp'),
                    cash.get('event_date'),
                    cash.get('total_cash_amount'),
                    cash.get('total_currency'),
                    json.dumps(cassettes),
                    json.dumps(cash),  # Store complete cash data
                    cassette_count,
                    has_low_cash_warning,
                    has_cash_errors
                ))
            
            conn.commit()
            log.info(f"Successfully saved {len(cash_info)} cash information records to terminal_cash_information")
            return True
            
        except Exception as e:
            log.error(f"Error saving cash information: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_terminal_status_summary(self) -> Dict[str, Any]:
        """
        Get terminal status summary from database
        
        Returns:
            Dict containing status summary
        """
        if not DB_AVAILABLE:
            log.warning("Database not available - returning empty summary")
            return {}
        
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get latest regional data
            cursor.execute("""
                SELECT region_code, region_code as region_name, total_atms_in_region as terminal_count, 
                       json_build_object(
                           'available', count_available,
                           'warning', count_warning,
                           'zombie', count_zombie,
                           'wounded', count_wounded,
                           'out_of_service', count_out_of_service
                       ) as status_summary
                FROM regional_data 
                WHERE retrieval_timestamp = (
                    SELECT MAX(retrieval_timestamp) FROM regional_data
                )
            """)
            
            regions = cursor.fetchall()
            
            summary = {
                'total_regions': len(regions),
                'total_terminals': sum(r[2] for r in regions),
                'regions': [],
                'timestamp': datetime.now().isoformat()
            }
            
            for region in regions:
                summary['regions'].append({
                    'region_id': region[0],
                    'region_name': region[1],
                    'terminal_count': region[2],
                    'status_summary': json.loads(region[3]) if region[3] else {}
                })
            
            return summary
            
        except Exception as e:
            log.error(f"Error getting terminal status summary: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
