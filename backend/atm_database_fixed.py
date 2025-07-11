#!/usr/bin/env python3
"""
Database Timezone Fix for ATM System

This script fixes timezone handling inconsistencies in database operations.
It ensures all timestamps are handled consistently with Dili timezone (+09:00).
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from atm_config import get_db_config, DILI_TIMEZONE

log = logging.getLogger(__name__)

# Check for database availability
try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import sql
    DB_AVAILABLE = True
except ImportError:
    log.warning("psycopg2 not available - database operations will be disabled")
    DB_AVAILABLE = False
    psycopg2 = None

class FixedATMDatabaseManager:
    """Enhanced database manager with proper timezone handling"""
    
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.dili_tz = pytz.timezone(DILI_TIMEZONE)
        self.utc_tz = pytz.UTC
        self.db_config = get_db_config()
        
        log.info(f"Database Manager initialized with Dili timezone: {DILI_TIMEZONE}")
    
    def _get_connection(self):
        """Get database connection with proper parameter handling"""
        if not DB_AVAILABLE or not psycopg2:
            raise ValueError("Database not available")
        
        return psycopg2.connect(
            host=self.db_config["host"],
            port=self.db_config["port"], 
            database=self.db_config["database"],
            user=self.db_config["user"],
            password=self.db_config["password"]
        )
    
    def _get_dili_timestamp(self) -> datetime:
        """Get current timestamp in Dili timezone"""
        return datetime.now(self.dili_tz)
    
    def _convert_to_dili_tz(self, dt: datetime) -> datetime:
        """Convert datetime to Dili timezone if not already timezone-aware"""
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = self.utc_tz.localize(dt)
        
        return dt.astimezone(self.dili_tz)
    
    def save_all_data(self, all_data: Dict[str, Any], use_new_tables: bool = False) -> bool:
        """
        Save all data to database with proper timezone handling
        
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
                success &= self.save_regional_data_fixed(all_data['regional_data'])
            
            # Save terminal details
            if 'terminal_details' in all_data:
                success &= self.save_terminal_details_fixed(all_data['terminal_details'])
            
            # Save cash information
            if 'cash_info' in all_data:
                success &= self.save_cash_info_fixed(all_data['cash_info'])
            
            log.info(f"Data save completed {'successfully' if success else 'with errors'}")
            return success
            
        except Exception as e:
            log.error(f"ERROR: Failed to save all data: {e}")
            return False
    
    def save_regional_data_fixed(self, regional_data: List[Dict[str, Any]]) -> bool:
        """
        Save regional data with fixed timezone handling
        
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
            
            # Create table if not exists with proper timezone columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_data (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    region_code VARCHAR(10) NOT NULL,
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
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
            
            # Get current Dili timestamp for all records
            current_dili_time = self._get_dili_timestamp()
            
            # Insert data with consistent timezone handling
            for region in regional_data:
                # Use current Dili time for retrieval_timestamp
                # Use JSON dumps for JSONB data to avoid psycopg2.extras dependency
                raw_data_json = json.dumps(region) if region else '{}'
                
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
                    current_dili_time,  # Consistent Dili timestamp
                    raw_data_json  # JSON string for JSONB column
                ))
            
            conn.commit()
            log.info(f"SUCCESS: Saved {len(regional_data)} regional data records with Dili timezone")
            return True
            
        except Exception as e:
            log.error(f"ERROR: Failed to save regional data: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def save_terminal_details_fixed(self, terminal_details: List[Dict[str, Any]]) -> bool:
        """
        Save terminal details with fixed timezone handling
        
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
            
            # Create table if not exists with proper timezone handling
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
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get current Dili timestamp
            current_dili_time = self._get_dili_timestamp()
            
            # Insert data with proper timezone handling
            for terminal in terminal_details:
                # Convert retrieved_date to Dili timezone if present, otherwise use current time
                retrieved_date = terminal.get('retrievedDate')
                if isinstance(retrieved_date, str):
                    try:
                        # Try to parse the date string and convert to Dili timezone
                        retrieved_date = datetime.fromisoformat(retrieved_date.replace('Z', '+00:00'))
                        retrieved_date = self._convert_to_dili_tz(retrieved_date)
                    except:
                        retrieved_date = current_dili_time
                elif isinstance(retrieved_date, datetime):
                    retrieved_date = self._convert_to_dili_tz(retrieved_date)
                else:
                    retrieved_date = current_dili_time
                
                # Prepare fault data with proper structure
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
                    'retrieval_timestamp': current_dili_time.isoformat(),
                    'unique_request_id': terminal.get('unique_request_id'),
                    'timezone': DILI_TIMEZONE
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
                    retrieved_date,  # Properly converted timestamp
                    terminal.get('fetched_status'),
                    json.dumps(terminal),  # JSON string for JSONB column
                    json.dumps(fault_data),  # JSON string for JSONB column
                    json.dumps(metadata)  # JSON string for JSONB column
                ))
            
            conn.commit()
            log.info(f"SUCCESS: Saved {len(terminal_details)} terminal detail records with proper timezone handling")
            return True
            
        except Exception as e:
            log.error(f"ERROR: Failed to save terminal details: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def save_cash_info_fixed(self, cash_info: List[Dict[str, Any]]) -> bool:
        """
        Save cash information with fixed timezone handling
        
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
            
            # Create table if not exists with proper timezone handling
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminal_cash_information (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    terminal_id VARCHAR(50) NOT NULL,
                    business_code VARCHAR(20),
                    technical_code VARCHAR(20),
                    external_id VARCHAR(20),
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    event_date TIMESTAMP WITH TIME ZONE,
                    total_cash_amount DECIMAL(15,2) DEFAULT 0.00,
                    total_currency VARCHAR(10),
                    cassettes_data JSONB NOT NULL,
                    raw_cash_data JSONB,
                    cassette_count INTEGER DEFAULT 0,
                    has_low_cash_warning BOOLEAN DEFAULT false,
                    has_cash_errors BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get current Dili timestamp
            current_dili_time = self._get_dili_timestamp()
            
            # Insert data with proper timezone handling
            for cash in cash_info:
                # Handle event_date timezone conversion
                event_date = cash.get('event_date')
                if event_date and isinstance(event_date, (str, datetime)):
                    if isinstance(event_date, str):
                        try:
                            event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                        except:
                            event_date = None
                    if event_date:
                        event_date = self._convert_to_dili_tz(event_date)
                
                # Handle retrieval_timestamp
                retrieval_timestamp = cash.get('retrieval_timestamp', current_dili_time)
                if isinstance(retrieval_timestamp, str):
                    try:
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp.replace('Z', '+00:00'))
                        retrieval_timestamp = self._convert_to_dili_tz(retrieval_timestamp)
                    except:
                        retrieval_timestamp = current_dili_time
                elif isinstance(retrieval_timestamp, datetime):
                    retrieval_timestamp = self._convert_to_dili_tz(retrieval_timestamp)
                else:
                    retrieval_timestamp = current_dili_time
                
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
                    retrieval_timestamp,  # Properly converted timestamp
                    event_date,  # Properly converted timestamp
                    cash.get('total_cash_amount'),
                    cash.get('total_currency'),
                    json.dumps(cassettes),  # JSON string for JSONB column
                    json.dumps(cash),  # Store complete cash data as JSON string
                    cassette_count,
                    has_low_cash_warning,
                    has_cash_errors
                ))
            
            conn.commit()
            log.info(f"SUCCESS: Saved {len(cash_info)} cash information records with proper timezone handling")
            return True
            
        except Exception as e:
            log.error(f"ERROR: Failed to save cash information: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
