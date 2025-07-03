#!/usr/bin/env python3
"""
Terminal Cash Information Retrieval Script

This script retrieves cash information for ATM terminals using the same authentication
and session management as the main combined_atm_retrieval_script.py. It fetches cash
data from the cash information API and stores it in the terminal_cash_information table.

Features:
1. Uses existing authentication mechanism from main script
2. Retrieves cash information for all discovered terminals
3. Processes and stores cash data in database
4. Saves JSON output for testing and debugging
5. Comprehensive error handling and retry logic
6. Performance optimization for multiple terminals

Usage:
    python terminal_cash_information_retrieval.py [--demo] [--save-to-db] [--save-json] [--terminal-id 2603]
"""

import requests
from requests.adapters import HTTPAdapter
import urllib3
import json
import logging
import sys
import time
import uuid
import subprocess
import platform
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any
import argparse
import pytz
import os
from tqdm import tqdm
import psycopg2

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"cash_retrieval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
log = logging.getLogger("CashInfoRetrieval")

# Try to import database connector and environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    log.info("Environment variables loaded from .env file")
except ImportError:
    log.warning("python-dotenv not installed. Using environment variables directly.")

try:
    from db_connector_new import db_connector
    DB_AVAILABLE = True
    log.info("Database connector available")
except ImportError:
    try:
        import db_connector
        DB_AVAILABLE = True
        log.info("Legacy database connector available")
    except ImportError:
        db_connector = None
        DB_AVAILABLE = False
        log.warning("Database connector not available - database operations will be skipped")

# Configuration - Same as main script
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGOUT_URL = "https://172.31.1.46/sigit/user/logout"
DASHBOARD_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"
CASH_INFO_URL = "https://172.31.1.46/sigit/terminal/searchTerminal"

LOGIN_PAYLOAD = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2025@"
}

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://172.31.1.46",
    "Referer": "https://172.31.1.46/sigitportal/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Connection": "keep-alive"
}

# Parameter values for terminal status retrieval (from main script)
PARAMETER_VALUES = ["WOUNDED", "HARD", "CASH", "UNAVAILABLE", "AVAILABLE", "WARNING", "ZOMBIE", "OUT_OF_SERVICE"]

# Database configuration from environment variables
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "database": os.environ.get("DB_NAME", "atm_monitor"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "")
}


class CashInformationRetriever:
    """Main class for handling terminal cash information retrieval"""
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize the cash information retriever
        
        Args:
            demo_mode: Whether to use demo mode (no actual network requests)
        """
        self.demo_mode = demo_mode
        
        # Initialize session with same configuration as main script
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        ))
        
        self.default_timeout = (30, 60)  # (connection_timeout, read_timeout)
        self.user_token = None
        
        # Use Dili timezone for consistency
        self.dili_tz = pytz.timezone('Asia/Dili')  # UTC+9
        current_time = datetime.now(self.dili_tz)
        
        log.info(f"🚀 Initialized CashInformationRetriever - Demo: {demo_mode}")
        log.info(f"🕒 Using Dili timezone (UTC+9): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        log.info(f"💻 Platform: {os.name}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with the ATM monitoring system (same as main script)
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Using mock authentication")
            self.user_token = "demo_token_" + str(int(time.time()))
            return True
        
        log.info("Attempting authentication...")
        
        try:
            response = self.session.post(
                LOGIN_URL,
                json=LOGIN_PAYLOAD,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=self.default_timeout
            )
            response.raise_for_status()
            
            login_data = response.json()
            
            # Extract user token using multiple fallback methods
            user_token = None
            
            # Method 1: Direct keys
            for key in ['user_token', 'token']:
                if key in login_data:
                    user_token = login_data[key]
                    break
            
            # Method 2: From header field
            if not user_token and 'header' in login_data:
                user_token = login_data['header'].get('user_token')
            
            if user_token:
                self.user_token = user_token
                log.info("✅ Authentication successful")
                return True
            else:
                log.error("❌ Authentication failed: Unable to extract user token from response")
                log.debug(f"Available keys in response: {list(login_data.keys())}")
                return False
                
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Authentication request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            log.error(f"❌ Authentication response not valid JSON: {str(e)}")
            return False
        except Exception as e:
            log.error(f"❌ Unexpected error during authentication: {str(e)}")
            return False
    
    def logout(self) -> bool:
        """
        Logout from the ATM monitoring system (same as main script)
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Using mock logout")
            self.user_token = None
            return True
        
        if not self.user_token:
            log.warning("No user token available - already logged out or never authenticated")
            return True
        
        log.info("Attempting logout...")
        
        logout_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            }
        }
        
        try:
            response = self.session.put(
                LOGOUT_URL,
                json=logout_payload,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=self.default_timeout
            )
            response.raise_for_status()
            
            logout_data = response.json()
            
            # Check for successful logout
            if "header" in logout_data:
                log.info("✅ Successfully logged out")
                self.user_token = None
                return True
            else:
                log.warning("⚠️ Logout response unclear, clearing token anyway")
                self.user_token = None
                return True
                
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Logout request failed: {str(e)}")
            self.user_token = None  # Clear token anyway to prevent reuse
            return False
        except json.JSONDecodeError as e:
            log.error(f"❌ Logout response not valid JSON: {str(e)}")
            self.user_token = None  # Clear token anyway
            return False
        except Exception as e:
            log.error(f"❌ Unexpected error during logout: {str(e)}")
            self.user_token = None  # Clear token anyway
            return False
    
    def get_terminals_by_status(self, param_value: str) -> List[Dict[str, Any]]:
        """
        Fetch terminal data for a specific parameter value (from main script)
        """
        if self.demo_mode:
            log.info(f"DEMO MODE: Generating sample terminals for status {param_value}")
            # Real terminal data for demo
            status_terminal_map = {
                'AVAILABLE': ['147', '169', '2603', '2604', '2605', '49', '83', '87', '88', '93'],
                'WARNING': ['85', '90', '86'],
                'WOUNDED': ['89'],
                'HARD': [],
                'CASH': [],
                'ZOMBIE': [],
                'UNAVAILABLE': [],
                'OUT_OF_SERVICE': []
            }
            
            terminal_ids = status_terminal_map.get(param_value, [])
            sample_terminals = []
            for terminal_id in terminal_ids:
                sample_terminals.append({
                    'terminalId': terminal_id,
                    'issueStateCode': param_value,
                    'fetched_status': param_value
                })
            return sample_terminals
        
        dashboard_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": {
                "parameters_list": [
                    {
                        "parameter_name": "issueStateName",
                        "parameter_values": [param_value]
                    }
                ]
            }
        }
        
        max_retries = 2
        retry_count = 0
        success = False
        terminals = []
        
        while retry_count < max_retries and not success:
            try:
                dashboard_res = self.session.put(
                    DASHBOARD_URL, 
                    json=dashboard_payload, 
                    headers=COMMON_HEADERS, 
                    verify=False, 
                    timeout=self.default_timeout
                )
                dashboard_res.raise_for_status()
                
                dashboard_data = dashboard_res.json()
                body_data = dashboard_data.get('body', [])
                
                if not body_data:
                    log.info(f"No data returned for status {param_value}")
                    return []
                
                if not isinstance(body_data, list):
                    log.warning(f"Unexpected body data type for {param_value}: {type(body_data)}")
                    return []
                
                for terminal in body_data:
                    terminal['fetched_status'] = param_value
                    terminals.append(terminal)
                
                log.info(f"Found {len(terminals)} terminals with status {param_value}")
                success = True
                
                # Update token if a new one was returned
                if "header" in dashboard_data and "user_token" in dashboard_data["header"]:
                    self.user_token = dashboard_data["header"]["user_token"]
                
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for {param_value} (Attempt {retry_count + 1}): {str(ex)}")
                
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Token may have expired, attempting to refresh...")
                    if self.authenticate():
                        log.info("Token refreshed successfully, retrying...")
                    else:
                        log.error("Failed to refresh token")
                        break
                
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All retry attempts failed for status {param_value}")
                    break
                log.info(f"Retrying in 3 seconds...")
                time.sleep(3)
                continue
                
        return terminals
    
    def comprehensive_terminal_search(self) -> List[Dict[str, Any]]:
        """
        Discover all terminals using comprehensive search strategy (from main script)
        
        Returns:
            List of all discovered terminals
        """
        log.info("🔍 Starting comprehensive terminal search for cash information retrieval...")
        
        all_terminals = []
        found_terminal_ids = set()
        
        for param_value in tqdm(PARAMETER_VALUES, desc="Searching statuses", unit="status"):
            try:
                terminals = self.get_terminals_by_status(param_value)
                
                if terminals:
                    log.info(f"Found {len(terminals)} terminals with status {param_value}")
                    
                    for terminal in terminals:
                        terminal_id = terminal.get('terminalId')
                        
                        if terminal_id and terminal_id not in found_terminal_ids:
                            all_terminals.append(terminal)
                            found_terminal_ids.add(terminal_id)
                            log.debug(f"Added terminal {terminal_id} from status {param_value}")
                        elif terminal_id:
                            log.debug(f"Terminal {terminal_id} already found, skipping duplicate")
                else:
                    log.info(f"No terminals found with status {param_value}")
                    
            except Exception as e:
                log.error(f"❌ Error searching status {param_value}: {str(e)}")
                continue
        
        log.info(f"✅ Terminal search completed: Found {len(found_terminal_ids)} unique terminals")
        log.info(f"Terminal IDs: {sorted(found_terminal_ids)}")
        
        return all_terminals
    
    def fetch_cash_information(self, terminal_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cash information for a specific terminal
        
        Args:
            terminal_id: Terminal ID to fetch cash information for
            
        Returns:
            Cash information data or None if failed
        """
        if self.demo_mode:
            log.info(f"DEMO MODE: Generating sample cash data for terminal {terminal_id}")
            
            # Generate realistic demo cash data based on the API response sample
            demo_cassettes = [
                {
                    "cassette_id": "PCU00",
                    "logical_number": "01",
                    "physical_number": "00",
                    "type": "REJECT",
                    "type_description": "Cassette of Rejected Notes",
                    "status": "OK",
                    "status_description": "Cassete OK",
                    "status_color": "#3cd179",
                    "currency": None,
                    "denomination": None,
                    "note_count": 14,
                    "total_value": 0,
                    "percentage": 0.0
                },
                {
                    "cassette_id": "PCU01",
                    "logical_number": "02",
                    "physical_number": "01",
                    "type": "DISPENSE",
                    "type_description": "Dispensing Cassette",
                    "status": "LOW",
                    "status_description": "Cassette almost empty",
                    "status_color": "#90EE90",
                    "currency": "USD",
                    "denomination": 20,
                    "note_count": 542,
                    "total_value": 10840,
                    "percentage": 0.0
                }
            ]
            
            return {
                "header": {"result_code": "000", "result_description": "Success."},
                "body": [{
                    "terminalId": terminal_id,
                    "businessId": "00610",
                    "technicalCode": "00600610",
                    "externalId": "45210",
                    "terminalCashInfo": {
                        "cashInfo": demo_cassettes,
                        "total": 10840
                    }
                }]
            }
        
        if not self.user_token:
            log.error("No authentication token available")
            return None
        
        # Construct cash information URL with parameters (based on the API sample)
        cash_url = f"{CASH_INFO_URL}?number_of_occurrences=30&terminal_type=ATM&terminal_id={terminal_id}&language=EN"
        
        cash_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": {}
        }
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                log.debug(f"Fetching cash information for terminal {terminal_id} (attempt {retry_count + 1})")
                
                response = self.session.put(
                    cash_url,
                    json=cash_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=self.default_timeout
                )
                response.raise_for_status()
                
                cash_data = response.json()
                
                # Check if the response has the expected structure
                if not isinstance(cash_data, dict):
                    log.warning(f"Unexpected response type for terminal {terminal_id}: {type(cash_data)}")
                    return None
                
                # Check for success in header
                header = cash_data.get('header', {})
                if header.get('result_code') != '000':
                    log.warning(f"API returned error for terminal {terminal_id}: {header.get('result_description', 'Unknown error')}")
                    return None
                
                # Update token if a new one was returned
                if "user_token" in header:
                    self.user_token = header["user_token"]
                
                log.debug(f"✅ Successfully fetched cash information for terminal {terminal_id}")
                return cash_data
                
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for terminal {terminal_id} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Token may have expired, attempting to refresh...")
                    if self.authenticate():
                        log.info("Token refreshed successfully, retrying...")
                        continue
                    else:
                        log.error("Failed to refresh token")
                        return None
                
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"❌ Failed to fetch cash info for terminal {terminal_id} after {max_retries} attempts")
                    return None
                
                time.sleep(2)  # Wait before retry
                
            except json.JSONDecodeError as ex:
                log.error(f"❌ Cash info response for terminal {terminal_id} not valid JSON: {str(ex)}")
                return None
                
            except Exception as ex:
                log.error(f"❌ Unexpected error fetching cash info for terminal {terminal_id}: {str(ex)}")
                return None
        
        return None
    
    def process_cash_information(self, terminal_id: str, cash_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process raw cash information data into database format
        
        Args:
            terminal_id: Terminal ID
            cash_data: Raw cash data from API
            
        Returns:
            Processed cash information record or None if failed
        """
        try:
            current_time = datetime.now(self.dili_tz)
            body = cash_data.get('body', [])
            
            if not body or not isinstance(body, list):
                log.warning(f"No body data found for terminal {terminal_id} - returning null record")
                return self._create_null_cash_record(terminal_id, current_time, cash_data, "No body data")
            
            terminal_info = body[0]  # Get first (and usually only) terminal info
            cash_info = terminal_info.get('terminalCashInfo', {})
            
            if not cash_info:
                log.warning(f"No terminalCashInfo found for terminal {terminal_id} - returning null record")
                return self._create_null_cash_record(terminal_id, current_time, cash_data, "No cash info", terminal_info)
            
            # Extract cash information
            cassettes_raw = cash_info.get('cashInfo', [])
            total_cash = cash_info.get('total', 0)
            
            # Check if cassettes data is empty or null
            if not cassettes_raw or not isinstance(cassettes_raw, list):
                log.warning(f"No cassette data found for terminal {terminal_id} - returning null record")
                return self._create_null_cash_record(terminal_id, current_time, cash_data, "No cassette data", terminal_info)
            
            # Process cassettes data
            processed_cassettes = []
            cassette_count = len(cassettes_raw)
            has_low_cash_warning = False
            has_cash_errors = False
            
            for cassette in cassettes_raw:
                # Skip cassettes with no meaningful data
                if not isinstance(cassette, dict):
                    log.debug(f"Skipping invalid cassette data for terminal {terminal_id}")
                    continue
                    
                processed_cassette = {
                    "cassette_id": cassette.get('cassId', ''),
                    "logical_number": cassette.get('cassLogicNbr', ''),
                    "physical_number": cassette.get('cassPhysNbr', ''),
                    "type": cassette.get('cassTypeValue', ''),
                    "type_description": cassette.get('cassTypeDescription', ''),
                    "status": cassette.get('cassStatusValue', ''),
                    "status_description": cassette.get('cassStatusDescription', ''),
                    "status_color": cassette.get('cassStatusColor', ''),
                    "currency": cassette.get('currency'),
                    "denomination": int(cassette.get('notesVal', 0)) if cassette.get('notesVal') else None,
                    "note_count": int(cassette.get('nbrNotes', 0)) if cassette.get('nbrNotes') else 0,
                    "total_value": cassette.get('cassTotal', 0),
                    "percentage": cassette.get('percentage', 0.0),
                    "instance_id": cassette.get('instanceId', '')
                }
                processed_cassettes.append(processed_cassette)
                
                # Check for warnings and errors
                status = cassette.get('cassStatusValue', '').upper()
                if status == 'LOW':
                    has_low_cash_warning = True
                elif status in ['ERROR', 'FAULT', 'FAILED']:
                    has_cash_errors = True
            
            # If all cassettes were invalid, return null record
            if not processed_cassettes:
                log.warning(f"All cassette data invalid for terminal {terminal_id} - returning null record")
                return self._create_null_cash_record(terminal_id, current_time, cash_data, "Invalid cassette data", terminal_info)
            
            # Create final record
            record = {
                'unique_request_id': str(uuid.uuid4()),
                'terminal_id': str(terminal_id),
                'business_code': terminal_info.get('businessId', ''),
                'technical_code': terminal_info.get('technicalCode', ''),
                'external_id': terminal_info.get('externalId', ''),
                'retrieval_timestamp': current_time,
                'event_date': datetime.fromtimestamp(cassettes_raw[0].get('eventDate', 0) / 1000, tz=self.dili_tz) if cassettes_raw and cassettes_raw[0].get('eventDate') else current_time,
                'total_cash_amount': float(total_cash) if total_cash is not None else 0.0,
                'total_currency': 'USD',  # Default currency
                'cassettes_data': processed_cassettes,
                'raw_cash_data': cash_data,
                'cassette_count': len(processed_cassettes),  # Use actual processed count
                'has_low_cash_warning': has_low_cash_warning,
                'has_cash_errors': has_cash_errors,
                'is_null_record': False,    # This is a valid record
                'null_reason': None         # No null reason
            }
            
            log.debug(f"Processed cash info for terminal {terminal_id}: ${total_cash:,} ({len(processed_cassettes)} cassettes)")
            return record
            
        except Exception as e:
            log.error(f"❌ Error processing cash information for terminal {terminal_id}: {str(e)}")
            current_time = datetime.now(self.dili_tz)
            return self._create_null_cash_record(terminal_id, current_time, cash_data, f"Processing error: {str(e)}")
    
    def _create_null_cash_record(self, terminal_id: str, current_time: datetime, 
                                cash_data: Dict[str, Any], reason: str, 
                                terminal_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a null cash record for terminals with missing or invalid cash information
        
        Args:
            terminal_id: Terminal ID
            current_time: Current timestamp
            cash_data: Raw cash data (for debugging)
            reason: Reason why cash info is null
            terminal_info: Optional terminal info from API response
            
        Returns:
            Null cash record with metadata
        """
        log.info(f"📭 Creating null cash record for terminal {terminal_id}: {reason}")
        
        return {
            'unique_request_id': str(uuid.uuid4()),
            'terminal_id': str(terminal_id),
            'business_code': terminal_info.get('businessId', '') if terminal_info else '',
            'technical_code': terminal_info.get('technicalCode', '') if terminal_info else '',
            'external_id': terminal_info.get('externalId', '') if terminal_info else '',
            'retrieval_timestamp': current_time,
            'event_date': current_time,  # Use current time as fallback
            'total_cash_amount': None,  # Explicitly null
            'total_currency': None,     # Explicitly null
            'cassettes_data': [],       # Empty array
            'raw_cash_data': cash_data, # Keep raw data for debugging
            'cassette_count': 0,
            'has_low_cash_warning': False,
            'has_cash_errors': False,
            'is_null_record': True,     # Flag to identify null records
            'null_reason': reason       # Reason for null record
        }
    
    def get_db_connection(self):
        """Create a database connection"""
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                dbname=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )
            return conn
        except Exception as e:
            log.error(f"Database connection error: {str(e)}")
            return None
    
    def save_cash_information_to_database(self, cash_records: List[Dict[str, Any]]) -> bool:
        """
        Save cash information records to the database
        
        Args:
            cash_records: List of processed cash information records
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Skipping database save")
            return True
        
        if not cash_records:
            log.warning("No cash records to save")
            return False
        
        conn = self.get_db_connection()
        if not conn:
            log.error("Failed to connect to database")
            return False
        
        cursor = conn.cursor()
        
        try:
            log.info(f"💾 Saving {len(cash_records)} cash information records to database...")
            
            for record in cash_records:
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
                    record['unique_request_id'],
                    record['terminal_id'],
                    record['business_code'],
                    record['technical_code'],
                    record['external_id'],
                    record['retrieval_timestamp'],
                    record['event_date'],
                    record['total_cash_amount'],
                    record['total_currency'],
                    json.dumps(record['cassettes_data']),
                    json.dumps(record['raw_cash_data']),
                    record['cassette_count'],
                    record['has_low_cash_warning'],
                    record['has_cash_errors']
                ))
            
            conn.commit()
            log.info(f"✅ Successfully saved {len(cash_records)} cash information records to database")
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"❌ Database error while saving cash information: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def save_json_output(self, cash_records: List[Dict[str, Any]], filename: Optional[str] = None) -> bool:
        """
        Save cash information to JSON file for testing
        
        Args:
            cash_records: List of processed cash information records
            filename: Optional custom filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cash_information_{timestamp}.json"
            
            # Create output directory if it doesn't exist
            output_dir = "cash_output"
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            # Prepare data for JSON serialization
            json_data = {
                "retrieval_timestamp": datetime.now(self.dili_tz).isoformat(),
                "total_terminals": len(cash_records),
                "cash_information": []
            }
            
            for record in cash_records:
                json_record = record.copy()
                # Convert datetime objects to ISO strings
                if isinstance(json_record.get('retrieval_timestamp'), datetime):
                    json_record['retrieval_timestamp'] = json_record['retrieval_timestamp'].isoformat()
                if isinstance(json_record.get('event_date'), datetime):
                    json_record['event_date'] = json_record['event_date'].isoformat()
                
                json_data["cash_information"].append(json_record)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
            
            log.info(f"✅ Cash information saved to JSON file: {filepath}")
            log.info(f"📊 File contains {len(cash_records)} terminal cash records")
            return True
            
        except Exception as e:
            log.error(f"❌ Error saving JSON output: {str(e)}")
            return False
    
    def retrieve_all_cash_information(self, save_to_db: bool = False, save_json: bool = False, specific_terminal_id: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Main method to retrieve cash information for all terminals
        
        Args:
            save_to_db: Whether to save to database
            save_json: Whether to save JSON output
            specific_terminal_id: If provided, only retrieve for this terminal
            
        Returns:
            Tuple of (success: bool, cash_records: List)
        """
        log.info("=" * 80)
        log.info("💰 STARTING TERMINAL CASH INFORMATION RETRIEVAL")
        log.info("=" * 80)
        log.info(f"📊 Mode: {'DEMO' if self.demo_mode else 'LIVE'}")
        log.info(f"💾 Database save: {'Enabled' if save_to_db else 'Disabled'}")
        log.info(f"📄 JSON save: {'Enabled' if save_json else 'Disabled'}")
        if specific_terminal_id:
            log.info(f"🎯 Target terminal: {specific_terminal_id}")
        log.info(f"⏰ Started at: {datetime.now(self.dili_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        log.info("=" * 80)
        
        start_time = time.time()
        all_cash_records = []
        
        try:
            # Step 1: Authentication
            log.info("🔐 Step 1: Authentication...")
            if not self.authenticate():
                log.error("❌ Authentication failed!")
                return False, []
            
            # Step 2: Get terminals to process
            if specific_terminal_id:
                log.info(f"🎯 Step 2: Processing specific terminal {specific_terminal_id}...")
                terminals_to_process = [{'terminalId': specific_terminal_id}]
            else:
                log.info("🔍 Step 2: Discovering terminals...")
                terminals_to_process = self.comprehensive_terminal_search()
            
            if not terminals_to_process:
                log.warning("⚠️ No terminals found to process")
                return False, []
            
            log.info(f"📋 Found {len(terminals_to_process)} terminals to process")
            
            # Step 3: Retrieve cash information for each terminal
            log.info("💰 Step 3: Retrieving cash information...")
            
            successful_retrievals = 0
            failed_retrievals = 0
            
            for terminal in tqdm(terminals_to_process, desc="Retrieving cash info", unit="terminal"):
                terminal_id = terminal.get('terminalId')
                if not terminal_id:
                    log.warning("Skipping terminal with missing ID")
                    failed_retrievals += 1
                    continue
                
                try:
                    # Fetch cash information
                    cash_data = self.fetch_cash_information(terminal_id)
                    
                    if cash_data:
                        # Process cash information
                        processed_record = self.process_cash_information(terminal_id, cash_data)
                        
                        if processed_record:
                            all_cash_records.append(processed_record)
                            
                            # Check if this is a null record
                            if processed_record.get('is_null_record', False):
                                log.warning(f"📭 Terminal {terminal_id}: No cash data - {processed_record.get('null_reason', 'Unknown reason')}")
                                failed_retrievals += 1  # Count as failed for statistics
                            else:
                                # Valid cash record
                                cash_amount = processed_record.get('total_cash_amount', 0)
                                cassette_count = processed_record.get('cassette_count', 0)
                                
                                if cash_amount is not None:
                                    log.info(f"✅ Terminal {terminal_id}: ${cash_amount:,.2f} ({cassette_count} cassettes)")
                                    successful_retrievals += 1
                                else:
                                    log.warning(f"📭 Terminal {terminal_id}: Null cash amount")
                                    failed_retrievals += 1
                        else:
                            log.warning(f"⚠️ Failed to process cash data for terminal {terminal_id}")
                            failed_retrievals += 1
                    else:
                        log.warning(f"⚠️ Failed to fetch cash data for terminal {terminal_id}")
                        failed_retrievals += 1
                    
                    # Small delay to avoid overwhelming the server
                    if not self.demo_mode:
                        time.sleep(1)
                        
                except Exception as e:
                    log.error(f"❌ Error processing terminal {terminal_id}: {str(e)}")
                    failed_retrievals += 1
                    continue
            
            # Step 4: Save to database if requested
            if save_to_db and all_cash_records:
                log.info("💾 Step 4: Saving to database...")
                db_success = self.save_cash_information_to_database(all_cash_records)
                if not db_success:
                    log.warning("⚠️ Database save failed, but cash data retrieved successfully")
            
            # Step 5: Save JSON output if requested
            if save_json and all_cash_records:
                log.info("📄 Step 5: Saving JSON output...")
                json_success = self.save_json_output(all_cash_records)
                if not json_success:
                    log.warning("⚠️ JSON save failed, but cash data retrieved successfully")
            
            # Step 6: Logout
            log.info("🚪 Step 6: Logout...")
            logout_success = self.logout()
            if not logout_success:
                log.warning("⚠️ Logout failed, but cash retrieval completed")
            
            # Final summary
            execution_time = time.time() - start_time
            
            log.info("=" * 80)
            log.info("🎉 CASH INFORMATION RETRIEVAL COMPLETED")
            log.info("=" * 80)
            log.info(f"📊 SUMMARY:")
            log.info(f"   • Total terminals processed: {len(terminals_to_process)}")
            log.info(f"   • Successful retrievals: {successful_retrievals}")
            log.info(f"   • Failed retrievals: {failed_retrievals}")
            log.info(f"   • Total cash records: {len(all_cash_records)}")
            log.info(f"   • Execution time: {execution_time:.2f} seconds")
            
            if all_cash_records:
                # Calculate statistics, handling null records
                valid_records = [record for record in all_cash_records if not record.get('is_null_record', False)]
                null_records = [record for record in all_cash_records if record.get('is_null_record', False)]
                
                log.info(f"   • Valid cash records: {len(valid_records)}")
                log.info(f"   • Null cash records: {len(null_records)}")
                
                if valid_records:
                    total_cash = sum(record.get('total_cash_amount', 0) or 0 for record in valid_records)
                    log.info(f"   • Total cash amount: ${total_cash:,.2f}")
                    
                    low_cash_count = sum(1 for record in valid_records if record.get('has_low_cash_warning', False))
                    if low_cash_count > 0:
                        log.info(f"   ⚠️ Terminals with low cash warnings: {low_cash_count}")
                
                if null_records:
                    log.info("   📭 Null record reasons:")
                    null_reasons = {}
                    for record in null_records:
                        reason = record.get('null_reason', 'Unknown')
                        null_reasons[reason] = null_reasons.get(reason, 0) + 1
                    
                    for reason, count in null_reasons.items():
                        log.info(f"      • {reason}: {count} terminals")
            
            log.info("=" * 80)
            
            return len(all_cash_records) > 0, all_cash_records
            
        except KeyboardInterrupt:
            log.info("⚠️ Operation cancelled by user")
            return False, all_cash_records
        except Exception as e:
            log.error(f"❌ Unexpected error during cash retrieval: {str(e)}")
            return False, all_cash_records


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Terminal Cash Information Retrieval Script')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode (no actual API calls)')
    parser.add_argument('--save-to-db', action='store_true', help='Save retrieved data to database')
    parser.add_argument('--save-json', action='store_true', help='Save retrieved data to JSON file')
    parser.add_argument('--terminal-id', type=str, help='Retrieve cash info for specific terminal only')
    
    args = parser.parse_args()
    
    # Create retriever instance
    retriever = CashInformationRetriever(demo_mode=args.demo)
    
    try:
        # Retrieve cash information
        success, cash_records = retriever.retrieve_all_cash_information(
            save_to_db=args.save_to_db,
            save_json=args.save_json,
            specific_terminal_id=args.terminal_id
        )
        
        if success:
            log.info("✅ Cash information retrieval completed successfully!")
            sys.exit(0)
        else:
            log.error("❌ Cash information retrieval failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        log.info("⚠️ Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
