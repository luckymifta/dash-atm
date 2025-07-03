#!/usr/bin/env python3
"""
Combined ATM Data Retrieval Script

A comprehensive script that combines regional ATM data retrieval with terminal-specific
fault information retrieval. This script integrates the functionality from:
- regional_atm_retrieval_script.py (for regional counts)  
- atm_crawler_complete.py (for terminal details with fetch_terminal_details function)

Features:
1. Authentication/login to the ATM monitoring system
2. Retrieving regional ATM data (fifth_graphic) from reports dashboard
3. Processing and converting percentage data to actual counts
4. Fetching detailed terminal-specific fault information
5. Comprehensive error handling and retry logic
6. JSON output support for all retrieved data
7. Optional database saving with rollback capability

Usage:
    python combined_atm_retrieval_script.py [--demo] [--save-to-db] [--save-json] [--total-atms 14]
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
import random
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any
import argparse
import pytz
import os
from tqdm import tqdm
import signal
import threading
from collections import deque

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.warning("python-dotenv not installed. Environment variables will not be loaded from .env file.")

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Enhanced logging setup with rotation and better error handling
def setup_enhanced_logging():
    """Setup enhanced logging with rotation and comprehensive coverage"""
    from logging.handlers import RotatingFileHandler
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate timestamped log filename for easier identification
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"combined_atm_retrieval_{current_timestamp}.log"
    log_filepath = os.path.join(logs_dir, log_filename)
    
    # Create separate error log file for critical issues
    error_log_filename = f"combined_atm_retrieval_errors_{current_timestamp}.log"
    error_log_filepath = os.path.join(logs_dir, error_log_filename)
    
    # Clear any existing logging configuration
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s:%(funcName)s:%(lineno)d]: %(message)s",
        handlers=[
            # Main log file with rotation (max 10MB, keep 5 files)
            RotatingFileHandler(
                log_filepath, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            ),
            # Console output with INFO level
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create specialized logger for this script
    log = logging.getLogger("CombinedATMRetrieval")
    log.setLevel(logging.INFO)
    
    # Add separate error file handler for ERROR and CRITICAL levels only
    error_handler = RotatingFileHandler(
        error_log_filepath,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s:%(funcName)s:%(lineno)d]: %(message)s")
    )
    log.addHandler(error_handler)
    
    # Set console handler to INFO level (reduce noise)
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.INFO)
    
    # Log setup information
    log.info("=" * 80)
    log.info("� COMBINED ATM RETRIEVAL SCRIPT STARTED")
    log.info("=" * 80)
    log.info(f"�📝 Main log file: {log_filepath}")
    log.info(f"🚨 Error log file: {error_log_filepath}")
    log.info(f"📁 Logs directory: {logs_dir}")
    log.info(f"⚙️  Log rotation enabled: 10MB max size, 5 backup files")
    log.info(f"🔧 Python version: {sys.version}")
    log.info(f"💻 Platform: {platform.system()} {platform.release()}")
    log.info(f"📍 Script location: {os.path.abspath(__file__)}")
    log.info(f"📍 Working directory: {os.getcwd()}")
    log.info("=" * 80)
    
    return log, logs_dir, log_filepath, error_log_filepath

# Initialize enhanced logging
log, logs_dir, log_filepath, error_log_filepath = setup_enhanced_logging()

# Global variables for continuous operation
stop_flag = threading.Event()
execution_stats = {
    'total_cycles': 0,
    'successful_cycles': 0,
    'failed_cycles': 0,
    'connection_failures': 0,
    'start_time': None,
    'last_success': None,
    'cycle_history': deque(maxlen=50)  # Keep last 50 cycle results
}

# Try to import database connector if available
try:
    # First try to use the original db_connector which uses environment variables properly
    import db_connector
    DB_AVAILABLE = True
    log.info("Legacy database connector available (using environment variables)")
except ImportError:
    try:
        # Fall back to db_connector_new only if original not available
        from db_connector_new import db_connector
        DB_AVAILABLE = True
        log.warning("Using new database connector with hardcoded credentials - consider switching to environment variables")
    except ImportError:
        db_connector = None
        DB_AVAILABLE = False
        log.warning("Database connector not available - database operations will be skipped")

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGOUT_URL = "https://172.31.1.46/sigit/user/logout"
REPORTS_URL = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status"
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

# Constants for table structure mapping
SUPPORTED_STATES = {
    'AVAILABLE': 'count_available',
    'WARNING': 'count_warning',
    'ZOMBIE': 'count_zombie',
    'WOUNDED': 'count_wounded',
    'OUT_OF_SERVICE': 'count_out_of_service'
}

# Parameter values for terminal status retrieval
PARAMETER_VALUES = ["WOUNDED", "HARD", "CASH", "UNAVAILABLE", "AVAILABLE", "WARNING", "ZOMBIE", "OUT_OF_SERVICE"]


class CombinedATMRetriever:
    """Main class for handling combined ATM data retrieval (regional + terminal details)"""
    
    def __init__(self, demo_mode: bool = False, total_atms: int = 14):
        """
        Initialize the retriever with Windows production environment optimizations
        
        Args:
            demo_mode: Whether to use demo mode (no actual network requests)
            total_atms: Total number of ATMs for percentage to count conversion
        """
        self.demo_mode = demo_mode
        self.total_atms = total_atms
        
        # Initialize session with Windows-compatible settings
        self.session = requests.Session()
        
        # Windows-specific session configuration for better reliability
        self.session.mount('https://', HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        ))
        
        # Note: Session-level timeout is not supported, will use per-request timeouts
        self.default_timeout = (30, 60)  # (connection_timeout, read_timeout)
        
        self.user_token = None
        
        # Log timezone info for clarity
        self.dili_tz = pytz.timezone('Asia/Dili')  # UTC+9
        current_time = datetime.now(self.dili_tz)
        
        # Log system information for Windows troubleshooting
        log.info(f"🚀 Initialized CombinedATMRetriever - Demo: {demo_mode}, Total ATMs: {total_atms}")
        log.info(f"🕒 Using Dili timezone (UTC+9) for timestamps: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        log.info(f"💻 Platform: {os.name} - Script optimized for Windows production")
        
        # Log current working directory for Windows debugging
        log.info(f"📁 Working directory: {os.getcwd()}")
        log.info(f"📄 Script location: {os.path.abspath(__file__)}")
    
    # Removed check_connectivity - authentication will catch connectivity issues
    
    def check_connectivity(self) -> bool:
        """
        Check connectivity to the target server 172.31.1.46 using ping
        
        Returns:
            bool: True if server is reachable via ping, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Skipping connectivity check")
            return True
        
        target_host = "172.31.1.46"
        log.info(f"Testing connectivity to {target_host} using ping...")
        
        try:
            # Determine ping command based on operating system
            if platform.system().lower() == "windows":
                # Windows ping command
                ping_cmd = ["ping", "-n", "3", target_host]
            else:
                # Unix/Linux/macOS ping command
                ping_cmd = ["ping", "-c", "3", target_host]
            
            # Execute ping command
            result = subprocess.run(
                ping_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log.info(f"✅ Ping successful to {target_host}")
                log.debug(f"Ping output: {result.stdout.strip()}")
                return True
            else:
                log.error(f"❌ Ping failed to {target_host}")
                log.debug(f"Ping error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            log.error(f"❌ Ping timeout to {target_host} (10 seconds)")
            return False
        except FileNotFoundError:
            log.error("❌ Ping command not found on system - falling back to HTTP check")
            # Fallback to original HTTP-based connectivity check
            return self._fallback_http_connectivity_check()
        except Exception as e:
            log.error(f"❌ Ping command failed: {str(e)} - falling back to HTTP check")
            # Fallback to original HTTP-based connectivity check
            return self._fallback_http_connectivity_check()
    
    def _fallback_http_connectivity_check(self) -> bool:
        """
        Fallback HTTP-based connectivity check (original implementation)
        
        Returns:
            bool: True if server is reachable via HTTP, False otherwise
        """
        try:
            log.info("Testing connectivity to 172.31.1.46 via HTTP...")
            response = requests.head(
                "https://172.31.1.46/",
                timeout=10,
                verify=False
            )
            log.info(f"HTTP connectivity test successful: HTTP {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"HTTP connectivity test failed: {str(e)}")
            return False
    
    def generate_out_of_service_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate OUT_OF_SERVICE data for all ATMs when connection fails
        Uses real terminal IDs and actual locations from database
        
        Returns:
            Tuple of (regional_data, terminal_details_data) with OUT_OF_SERVICE status
        """
        log.warning("Generating OUT_OF_SERVICE data due to connection failure")
        current_time = datetime.now(self.dili_tz)  # Use Dili time for database consistency (same as normal operation)
        
        # Real terminal IDs and their actual locations from database
        REAL_TERMINAL_DATA = {
            "83": "RUA NICOLAU DOS REIS LOBATO",
            "2603": "BRI - CENTRAL OFFICE COLMERA 02", 
            "87": "PERTAMINA INT. BEBORRA RUA. DOS MARTIRES DA PATRIA",
            "88": "AERO PORTO NICOLAU LOBATU,DILI",
            "2604": "BRI - SUB-BRANCH AUDIAN",
            "85": "ESTRADA DE BALIDE, BALIDE",
            "147": "CENTRO SUPERMERCADO PANTAI KELAPA",
            "49": "AV. ALM. AMERICO TOMAS",
            "86": "FATU AHI", 
            "2605": "BRI - SUB BRANCH HUDILARAN",
            "169": "BRI SUB-BRANCH FATUHADA",
            "90": "NOVO TURISMO, BIDAU LECIDERE",
            "89": "UNTL, RUA JACINTO CANDIDO",
            "93": "TIMOR PLAZA COMORO"
        }
        
        # Verify we have all required terminals
        total_real_terminals = len(REAL_TERMINAL_DATA)
        log.info(f"Using {total_real_terminals} real ATM terminals with actual locations")
        
        # Generate regional data with OUT_OF_SERVICE status for TL-DL region only
        regional_data = []
        regions = ["TL-DL"]  # Only TL-DL region to avoid connection failures
        
        for region_code in regions:
            record = {
                'unique_request_id': str(uuid.uuid4()),
                'region_code': region_code,
                'count_available': 0,
                'count_warning': 0,
                'count_zombie': 0,
                'count_wounded': 0,
                'count_out_of_service': total_real_terminals,  # All real ATMs marked as OUT_OF_SERVICE
                'date_creation': current_time,
                'total_atms_in_region': total_real_terminals,
                'percentage_available': 0.0,
                'percentage_warning': 0.0,
                'percentage_zombie': 0.0,
                'percentage_wounded': 0.0,
                'percentage_out_of_service': 1.0  # 100% OUT_OF_SERVICE
            }
            regional_data.append(record)
            log.info(f"Generated OUT_OF_SERVICE regional data for {region_code}: all {total_real_terminals} real ATMs marked as OUT_OF_SERVICE")
        
        # Generate terminal details data with OUT_OF_SERVICE status using real terminal data
        terminal_details_data = []
        for terminal_id, actual_location in REAL_TERMINAL_DATA.items():
            terminal_detail = {
                'unique_request_id': str(uuid.uuid4()),
                'terminalId': terminal_id,
                'location': actual_location,  # Use real location from database
                'issueStateName': 'OUT_OF_SERVICE',
                'issueStateCode': 'OUT_OF_SERVICE',
                'brand': 'CONNECTION_FAILED',  # Indicate this is due to connection failure
                'model': 'N/A',
                'serialNumber': f"CONN_FAIL_{terminal_id}",
                'agentErrorDescription': f'Connection to monitoring system failed - Terminal {terminal_id} at {actual_location}',
                'externalFaultId': 'CONN_FAILURE',
                'year': str(current_time.year),
                'month': str(current_time.month).zfill(2),
                'day': str(current_time.day).zfill(2),
                'fetched_status': 'OUT_OF_SERVICE',
                'details_status': 'CONNECTION_FAILED',
                'retrievedDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),  # Use consistent format with normal operation
                'dateRequest': current_time.strftime("%d-%m-%Y %H:%M:%S"),
                'region_code': 'TL-DL'  # All terminals in TL-DL region
            }
            terminal_details_data.append(terminal_detail)
            log.debug(f"Generated OUT_OF_SERVICE data for terminal {terminal_id} at {actual_location}")
        
        log.info(f"Generated {len(terminal_details_data)} terminal details with OUT_OF_SERVICE status using real terminal data")
        log.info(f"Real terminals included: {', '.join(sorted(REAL_TERMINAL_DATA.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')))}")
        return regional_data, terminal_details_data

    def generate_auth_failure_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate OUT_OF_SERVICE data for all ATMs when authentication fails but ping succeeds
        Uses real terminal IDs and actual locations with special identifiers for auth failure
        
        Returns:
            Tuple of (regional_data, terminal_details_data) with AUTH_FAILURE status
        """
        log.warning("Generating AUTH_FAILURE data - connection available but authentication failed")
        current_time = datetime.now(self.dili_tz)  # Use Dili time for database consistency
        
        # Real terminal IDs and their actual locations from database
        REAL_TERMINAL_DATA = {
            "83": "RUA NICOLAU DOS REIS LOBATO",
            "2603": "BRI - CENTRAL OFFICE COLMERA 02", 
            "87": "PERTAMINA INT. BEBORRA RUA. DOS MARTIRES DA PATRIA",
            "88": "AERO PORTO NICOLAU LOBATU,DILI",
            "2604": "BRI - SUB-BRANCH AUDIAN",
            "85": "ESTRADA DE BALIDE, BALIDE",
            "147": "CENTRO SUPERMERCADO PANTAI KELAPA",
            "49": "AV. ALM. AMERICO TOMAS",
            "86": "FATU AHI", 
            "2605": "BRI - SUB BRANCH HUDILARAN",
            "169": "BRI SUB-BRANCH FATUHADA",
            "90": "NOVO TURISMO, BIDAU LECIDERE",
            "89": "UNTL, RUA JACINTO CANDIDO",
            "93": "TIMOR PLAZA COMORO"
        }
        
        total_real_terminals = len(REAL_TERMINAL_DATA)
        log.info(f"Generating AUTH_FAILURE data for {total_real_terminals} real ATM terminals")
        
        # Generate regional data with OUT_OF_SERVICE status for TL-DL region only
        regional_data = []
        regions = ["TL-DL"]  # Only TL-DL region to avoid connection failures
        
        for region_code in regions:
            record = {
                'unique_request_id': str(uuid.uuid4()),
                'region_code': region_code,
                'count_available': 0,
                'count_warning': 0,
                'count_zombie': 0,
                'count_wounded': 0,
                'count_out_of_service': total_real_terminals,  # All real ATMs marked as OUT_OF_SERVICE
                'date_creation': current_time,
                'total_atms_in_region': total_real_terminals,
                'percentage_available': 0.0,
                'percentage_warning': 0.0,
                'percentage_zombie': 0.0,
                'percentage_wounded': 0.0,
                'percentage_out_of_service': 1.0  # 100% OUT_OF_SERVICE
            }
            regional_data.append(record)
            log.info(f"Generated AUTH_FAILURE regional data for {region_code}: all {total_real_terminals} real ATMs marked as OUT_OF_SERVICE")
        
        # Generate terminal details data with AUTH_FAILURE status using real terminal data
        terminal_details_data = []
        for terminal_id, actual_location in REAL_TERMINAL_DATA.items():
            terminal_detail = {
                'unique_request_id': str(uuid.uuid4()),
                'terminalId': terminal_id,
                'location': actual_location,  # Use real location from database
                'issueStateName': 'OUT_OF_SERVICE',
                'issueStateCode': 'OUT_OF_SERVICE',
                'brand': 'AUTH_FAILED',  # Indicate this is due to authentication failure
                'model': 'LOGIN_ERROR',
                'serialNumber': f"AUTH_FAIL_{terminal_id}",
                'agentErrorDescription': f'Authentication failed - Unable to login to monitoring system for Terminal {terminal_id} at {actual_location}',
                'externalFaultId': 'AUTH_FAILURE',
                'year': str(current_time.year),
                'month': str(current_time.month).zfill(2),
                'day': str(current_time.day).zfill(2),
                'fetched_status': 'OUT_OF_SERVICE',
                'details_status': 'AUTH_FAILED',
                'retrievedDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'dateRequest': current_time.strftime("%d-%m-%Y %H:%M:%S"),
                'region_code': 'TL-DL'  # All terminals in TL-DL region
            }
            terminal_details_data.append(terminal_detail)
            log.debug(f"Generated AUTH_FAILURE data for terminal {terminal_id} at {actual_location}")
        
        log.info(f"Generated {len(terminal_details_data)} terminal details with AUTH_FAILURE status")
        log.info(f"Auth failure terminals: {', '.join(sorted(REAL_TERMINAL_DATA.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')))}")
        return regional_data, terminal_details_data

    def authenticate(self) -> bool:
        """
        Authenticate with the ATM monitoring system
        
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
                    # Reduced logging verbosity for performance
                    break
            
            # Method 2: From header field
            if not user_token and 'header' in login_data:
                user_token = login_data['header'].get('user_token')
                if user_token:
                    # Reduced logging verbosity for performance
                    pass
            
            if user_token:
                self.user_token = user_token
                log.info("Authentication successful")
                return True
            else:
                log.error("Authentication failed: Unable to extract user token from response")
                log.debug(f"Available keys in response: {list(login_data.keys())}")
                return False
                
        except requests.exceptions.RequestException as e:
            log.error(f"Authentication request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            log.error(f"Authentication response not valid JSON: {str(e)}")
            return False
        except Exception as e:
            log.error(f"Unexpected error during authentication: {str(e)}")
            return False
    
    def refresh_token(self) -> bool:
        """Refresh the authentication token if expired"""
        log.info("Attempting to refresh authentication token...")
        return self.authenticate()
    
    def logout(self) -> bool:
        """
        Logout from the ATM monitoring system to prevent session lockouts
        
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
                result_code = logout_data["header"].get("result_code", "")
                result_description = logout_data["header"].get("result_description", "")
                
                if result_code == "000":
                    log.info(f"Logout successful: {result_description}")
                    self.user_token = None
                    return True
                else:
                    log.warning(f"Logout returned non-success code: {result_code} - {result_description}")
                    self.user_token = None  # Clear token anyway
                    return False
            else:
                log.warning("Logout response missing header field")
                self.user_token = None  # Clear token anyway
                return False
                
        except requests.exceptions.RequestException as e:
            log.error(f"Logout request failed: {str(e)}")
            self.user_token = None  # Clear token anyway to prevent reuse
            return False
        except json.JSONDecodeError as e:
            log.error(f"Logout response not valid JSON: {str(e)}")
            self.user_token = None  # Clear token anyway
            return False
        except Exception as e:
            log.error(f"Unexpected error during logout: {str(e)}")
            self.user_token = None  # Clear token anyway
            return False
    
    def fetch_regional_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch regional ATM data from the reports dashboard
        
        Returns:
            List containing fifth_graphic data or None if failed
        """
        if self.demo_mode:
            log.info("Demo mode: Generating sample regional data for TL-DL only")
            return [
                {
                    "hc-key": "TL-DL",
                    "state_count": {
                        "AVAILABLE": "0.78571427",
                        "WOUNDED": "0.14285714",
                        "WARNING": "0.07142857"
                    }
                }
            ]
        
        if not self.user_token:
            log.error("No authentication token available - please authenticate first")
            return None
        
        reports_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": []
        }
        
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Reduced logging verbosity for performance
                response = self.session.put(
                    REPORTS_URL,
                    json=reports_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=self.default_timeout
                )
                response.raise_for_status()
                
                reports_data = response.json()
                
                # Validate response structure
                if not isinstance(reports_data, dict):
                    log.error("Response has unexpected format (not a dictionary)")
                    retry_count += 1
                    continue
                
                if "body" not in reports_data:
                    log.error("Response missing 'body' field")
                    retry_count += 1
                    continue
                
                body_data = reports_data.get("body", {})
                if "fifth_graphic" not in body_data:
                    log.warning("fifth_graphic not found in response body")
                    log.info(f"Available body keys: {list(body_data.keys())}")
                    return None
                
                fifth_graphic_data = body_data["fifth_graphic"]
                log.info(f"Successfully retrieved regional data for {len(fifth_graphic_data)} regions")
                
                # Update token if a new one was provided
                if "header" in reports_data and "user_token" in reports_data["header"]:
                    new_token = reports_data["header"]["user_token"]
                    if new_token != self.user_token:
                        log.info("Received updated token in response")
                        self.user_token = new_token
                
                return fifth_graphic_data
                
            except requests.exceptions.RequestException as e:
                log.warning(f"Request failed (Attempt {retry_count + 1}): {str(e)}")
                
                # Check for token expiration
                if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
                    log.warning("Detected possible token expiration (401 Unauthorized)")
                    if self.refresh_token():
                        reports_payload["header"]["user_token"] = self.user_token
                        log.info("Token refreshed, retrying request...")
                        continue
                
                retry_count += 1
                if retry_count < max_retries:
                    log.info("Retrying in 3 seconds...")
                    time.sleep(3)
                
            except json.JSONDecodeError as e:
                log.error(f"Response not valid JSON (Attempt {retry_count + 1}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(3)
        
        log.error("All attempts failed to retrieve regional data")
        return None
    
    def get_terminals_by_status(self, param_value: str) -> List[Dict[str, Any]]:
        """
        Fetch terminal data for a specific parameter value
        Extracted and adapted from atm_crawler_complete.py
        """
        if self.demo_mode:
            log.info(f"DEMO MODE: Generating sample terminals for status {param_value}")
            
            # Define realistic terminal distribution based on real data
            # All 14 terminals as requested: 83, 2603, 88, 147, 87, 169, 2605, 2604, 93, 49, 86, 89, 85, 90
            status_terminal_map = {
                'AVAILABLE': ['147', '169', '2603', '2604', '2605', '49', '83', '87', '88', '93'],  # 10 terminals
                'WARNING': ['85', '90', '86'],  # 3 terminals (added 86)  
                'WOUNDED': ['89'],  # 1 terminal
                'HARD': [],  # No terminals (mapped to WOUNDED)
                'CASH': [],  # No terminals (mapped to WOUNDED)
                'ZOMBIE': [],  # No terminals
                'UNAVAILABLE': [],  # No terminals (mapped to OUT_OF_SERVICE)
                'OUT_OF_SERVICE': []  # No terminals (for consistency with terminal status summary)
            }
            
            # Get terminal IDs for this status
            terminal_ids = status_terminal_map.get(param_value, [])
            
            # Generate sample terminals based on realistic data
            sample_terminals = []
            for terminal_id in terminal_ids:
                sample_terminals.append({
                    'terminalId': terminal_id,
                    'location': f"Sample Location for {terminal_id}",
                    'issueStateName': param_value,
                    'fetched_status': param_value,
                    'issueStateCode': 'HARD' if param_value == 'WOUNDED' else param_value,
                    'brand': 'Nautilus Hyosun',
                    'model': 'Monimax 5600'
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
        
        # Add retry logic for reliability
        max_retries = 2
        retry_count = 0
        success = False
        terminals = []
        
        while retry_count < max_retries and not success:
            try:
                # Reduced logging verbosity for performance
                dashboard_res = self.session.put(
                    DASHBOARD_URL,
                    json=dashboard_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=30
                )
                dashboard_res.raise_for_status()
                
                # Try to parse JSON
                dashboard_data = dashboard_res.json()
                
                # Check if the response has the expected structure
                if not isinstance(dashboard_data, dict):
                    log.error(f"Dashboard response for {param_value} has unexpected format (not a dictionary)")
                    retry_count += 1
                    if retry_count >= max_retries:
                        log.error(f"All attempts failed due to unexpected response format for {param_value}")
                        return []
                    log.info(f"Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                
                # Check if the body field exists in the response
                if "body" not in dashboard_data:
                    log.error(f"Dashboard response for {param_value} is missing the 'body' field")
                    log.error(f"Response keys: {list(dashboard_data.keys())}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        log.error(f"All attempts failed due to missing 'body' field for {param_value}")
                        return []
                    log.info(f"Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                
                # Check if the body contains terminals
                body_data = dashboard_data.get("body", [])
                if not body_data:
                    log.warning(f"No terminals found for status {param_value}")
                    success = True  # This is not an error, just no data
                    return []
                    
                # Make sure body_data is a list before iterating over it
                if not isinstance(body_data, list):
                    log.error(f"Body data for {param_value} is not a list. Type: {type(body_data)}")
                    body_data = []
                    return []
                    
                # Process the terminal data
                for terminal in body_data:
                    # Add the parameter value we searched for
                    terminal['fetched_status'] = param_value
                    terminals.append(terminal)
                    
                log.info(f"Found {len(terminals)} terminals with status {param_value}")
                success = True
                
                # Update token if a new one was returned
                if "header" in dashboard_data and "user_token" in dashboard_data["header"]:
                    new_token = dashboard_data["header"]["user_token"]
                    if new_token != self.user_token:
                        log.info("Received new token in response, updating...")
                        self.user_token = new_token
                
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for {param_value} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue (401 Unauthorized)
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                    if self.refresh_token():
                        log.info("Token refreshed successfully, updating payload with new token")
                        # Update the payload with the new token
                        dashboard_payload["header"]["user_token"] = self.user_token
                        # Don't increment retry count for token refresh
                        log.info("Retrying request with new token...")
                        continue
                
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All attempts failed for {param_value}. Skipping this parameter.")
                    return []
                log.info(f"Retrying in 3 seconds...")
                time.sleep(3)
                continue
                
            except json.JSONDecodeError as ex:
                log.error(f"Dashboard response for {param_value} not valid JSON! (Attempt {retry_count + 1})")
                # Only show raw response if dashboard_res was successfully created
                dashboard_res_text = getattr(locals().get('dashboard_res'), 'text', 'Response object not available')
                if dashboard_res_text != 'Response object not available':
                    log.error(f"Raw response: {dashboard_res_text[:200]}...")
                else:
                    log.error("Response object not available for debugging")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All JSON parsing attempts failed for {param_value}. Skipping this parameter.")
                    return []
        
        return terminals
    
    def fetch_terminal_details(self, terminal_id: str, issue_state_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific terminal ID
        Extracted from atm_crawler_complete.py fetch_terminal_details function
        """
        if self.demo_mode:
            log.info(f"DEMO MODE: Generating sample data for terminal {terminal_id}")
            
            # Create a mock response based on the sample you provided
            terminal_data = {
                "body": [
                    {
                        "terminalId": terminal_id,
                        "networkId": "P24",
                        "externalId": f"4520{terminal_id[-1]}",
                        "brand": "Nautilus Hyosun",
                        "model": "Monimax 5600",
                        "supplier": "BRI",
                        "location": f"Sample location for {terminal_id}",
                        "geoLocation": "TL-DL",
                        "terminalType": "ATM",
                        "osVersion": "00130035",
                        "issueStateName": issue_state_code,
                        "creationDate": int(datetime.now().timestamp() * 1000),
                        "statusDate": int(datetime.now().timestamp() * 1000),
                        "bank": "BRI",
                        "serialNumber": f"YB7620{terminal_id}",
                        "faultList": [
                            {
                                "faultId": f"1379{terminal_id}",
                                "faultTypeCode": issue_state_code,
                                "componentTypeCode": "PRR",
                                "issueStateName": issue_state_code,
                                "terminalId": int(terminal_id),
                                "serviceRequestId": 63173,
                                "location": "DILI",
                                "bank": "BRI",
                                "brand": "Nautilus Hyosun",
                                "model": "Monimax 5600",
                                "year": datetime.now().strftime("%Y"),
                                "month": datetime.now().strftime("%b").upper(),
                                "day": datetime.now().strftime("%d"),
                                "externalFaultId": f"PRR2119{terminal_id}",
                                "agentErrorDescription": "MEDIA JAMMED" if issue_state_code == "HARD" else 
                                                        "CASH LOW" if issue_state_code == "CASH" else 
                                                        "DEVICE ERROR",
                                "creationDate": int(datetime.now().timestamp() * 1000)  # Unix timestamp in milliseconds
                            }
                        ]
                    }
                ]
            }
            return terminal_data
        
        details_url = f"{DASHBOARD_URL}&terminal_id={terminal_id}"
        
        details_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": {
                "parameters_list": [
                    {
                        "parameter_name": "issueStateCode",
                        "parameter_values": [issue_state_code]
                    }
                ]
            }
        }
        
        # Add retry logic for reliability
        max_retries = 2
        retry_count = 0
        success = False
        terminal_data = None
        
        while retry_count < max_retries and not success:
            try:
                # Reduced logging verbosity for performance
                details_res = self.session.put(details_url, json=details_payload, headers=COMMON_HEADERS, verify=False, timeout=30)
                details_res.raise_for_status()
                
                # Try to parse JSON
                details_data = details_res.json()
                
                # Check if the response has the expected structure
                if not isinstance(details_data, dict):
                    log.error(f"Details response for terminal {terminal_id} has unexpected format (not a dictionary)")
                    retry_count += 1
                    if retry_count >= max_retries:
                        log.error(f"All attempts failed due to unexpected response format for terminal {terminal_id}")
                        return None
                    log.info(f"Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                
                # Check if the body field exists in the response
                if "body" not in details_data:
                    log.error(f"Details response for terminal {terminal_id} is missing the 'body' field")
                    log.error(f"Response keys: {list(details_data.keys())}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        log.error(f"All attempts failed due to missing 'body' field for terminal {terminal_id}")
                        return None
                    log.info(f"Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                
                success = True
                terminal_data = details_data
                # Removed verbose success logging for performance
                
                # Update token if a new one was returned
                if "header" in details_data and "user_token" in details_data["header"]:
                    new_token = details_data["header"]["user_token"]
                    if new_token != self.user_token:
                        log.info("Received new token in response, updating...")
                        self.user_token = new_token
                
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for terminal {terminal_id} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue (401 Unauthorized)
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                    if self.refresh_token():
                        log.info("Token refreshed successfully, updating payload with new token")
                        # Update the payload with the new token
                        details_payload["header"]["user_token"] = self.user_token
                        # Don't increment retry count for token refresh
                        log.info("Retrying request with new token...")
                        continue
                
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All attempts failed for terminal {terminal_id}. Skipping this terminal.")
                    return None
                log.info(f"Retrying in 3 seconds...")
                time.sleep(3)
                continue
                
            except json.JSONDecodeError as ex:
                log.error(f"Details response for terminal {terminal_id} not valid JSON! (Attempt {retry_count + 1})")
                # Only show raw response if details_res was successfully created
                details_res_text = getattr(locals().get('details_res'), 'text', 'Response object not available')
                if details_res_text != 'Response object not available':
                    log.error(f"Raw response: {details_res_text[:200]}...")
                else:
                    log.error("Response object not available for debugging")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All JSON parsing attempts failed for terminal {terminal_id}. Skipping this terminal.")
                    return None
                log.info(f"Retrying in 3 seconds...")
                time.sleep(3)
                continue
                
        return terminal_data

    def process_regional_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process raw fifth_graphic data and convert to regional_atm_counts table structure
        Only processes TL-DL region to avoid connection failures.
        
        Args:
            raw_data: Raw fifth_graphic data from API response
            
        Returns:
            List of processed records matching regional_atm_counts table structure
        """
        if not raw_data:
            log.warning("No raw data provided for processing")
            return []
        
        processed_records = []
        current_time = datetime.now(self.dili_tz)  # Use Dili time for database consistency
        
        # Filter to only process TL-DL region
        tl_dl_data = [region for region in raw_data if region.get("hc-key") == "TL-DL"]
        
        log.info(f"Processing regional data for TL-DL region only (filtered from {len(raw_data)} regions)")
        log.info(f"Using Dili time for database storage: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        
        for region_data in tl_dl_data:
            region_code = region_data.get("hc-key", "UNKNOWN")
            state_count = region_data.get("state_count", {})
            
            if region_code != "TL-DL":
                log.info(f"Skipping region {region_code} - only processing TL-DL")
                continue
            
            if not state_count:
                log.warning(f"No state_count data found for region {region_code}")
                continue
            
            # Initialize the record structure matching regional_atm_counts table
            record = {
                'unique_request_id': str(uuid.uuid4()),
                'region_code': region_code,
                'count_available': 0,
                'count_warning': 0,
                'count_zombie': 0,
                'count_wounded': 0,
                'count_out_of_service': 0,
                'date_creation': current_time,
                'total_atms_in_region': self.total_atms,
                'percentage_available': 0.0,
                'percentage_warning': 0.0,
                'percentage_zombie': 0.0,
                'percentage_wounded': 0.0,
                'percentage_out_of_service': 0.0
            }
            
            total_percentage = 0.0
            
            # Process each state in the region
            for state_type, percentage_str in state_count.items():
                try:
                    percentage_value = float(percentage_str)
                    count_value = round(percentage_value * self.total_atms)
                    
                    # Map state types to database columns
                    state_upper = state_type.upper()
                    if state_upper in SUPPORTED_STATES:
                        count_column = SUPPORTED_STATES[state_upper]
                        percentage_column = f"percentage_{count_column.split('_', 1)[1]}"
                        
                        record[count_column] = count_value
                        record[percentage_column] = round(percentage_value, 8)  # Match DECIMAL(10,8)
                        
                        total_percentage += percentage_value
                        
                        log.debug(f"Region {region_code} - {state_type}: {percentage_value:.4f} ({count_value} ATMs)")
                    else:
                        log.warning(f"Unknown state type: {state_type} for region {region_code}")
                        
                except (ValueError, TypeError) as e:
                    log.error(f"Error processing state {state_type} for region {region_code}: {e}")
                    continue
            
            # Validation
            if abs(total_percentage - 1.0) > 0.01:  # Allow 1% tolerance
                log.warning(f"Percentages don't sum to 100% for {region_code}: {total_percentage:.2%}")
            
            total_calculated_count = (record['count_available'] + record['count_warning'] + 
                                    record['count_zombie'] + record['count_wounded'] + 
                                    record['count_out_of_service'])
            
            if total_calculated_count != self.total_atms:
                log.warning(f"Calculated count ({total_calculated_count}) doesn't match total ATMs ({self.total_atms}) for {region_code}")
            
            processed_records.append(record)
            
            log.info(f"Processed region {region_code}: "
                    f"Available={record['count_available']}, "
                    f"Warning={record['count_warning']}, "
                    f"Zombie={record['count_zombie']}, "
                    f"Wounded={record['count_wounded']}, "
                    f"Out_of_Service={record['count_out_of_service']}")
        
        log.info(f"Successfully processed {len(processed_records)} regional records")
        return processed_records
    
    def retrieve_and_process_all_data(self, save_to_db: bool = False, use_new_tables: bool = False, include_cash_info: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Complete flow: authenticate, retrieve regional data and terminal details
        With failover capability for connection failures
        
        Args:
            save_to_db: Whether to save processed data to database (original tables)
            use_new_tables: Whether to use new database tables (regional_data and terminal_details)
            include_cash_info: Whether to also retrieve cash information for all terminals
            
        Returns:
            Tuple of (success: bool, all_data: Dict containing all retrieved data)
        """
        log.info("=" * 80)
        log.info("🚀 STARTING COMBINED ATM DATA RETRIEVAL")
        log.info("=" * 80)
        log.info(f"📊 Retrieval mode: {'DEMO' if self.demo_mode else 'LIVE'}")
        log.info(f"💾 Database save: {'Enabled' if save_to_db else 'Disabled'}")
        log.info(f"🆕 New tables: {'Enabled' if use_new_tables else 'Disabled'}")
        log.info(f"💰 Cash info retrieval: {'Enabled' if include_cash_info else 'Disabled'}")
        log.info(f"🏧 Total ATMs configured: {self.total_atms}")
        log.info(f"⏰ Retrieval timestamp: {datetime.now(self.dili_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        log.info("=" * 80)
        
        # Initialize performance tracking
        start_time = time.time()
        phase_times = {}
        
        all_data = {
            "retrieval_timestamp": datetime.now(self.dili_tz).isoformat(),  # Store Dili timestamp for consistency
            "demo_mode": self.demo_mode,
            "regional_data": [],
            "terminal_details_data": [],  # Only terminal details, no terminal status data
            "cash_information_data": [],  # Cash information for terminals
            "summary": {},
            "failover_mode": False,
            "performance_metrics": {}
        }
        
        # Step 1: Check connectivity to 172.31.1.46 using ping (skip for demo mode)
        log.info("📡 Phase 1: Network connectivity check...")
        phase_start = time.time()
        if not self.demo_mode:
            connectivity_ok = self.check_connectivity()
            if not connectivity_ok:
                log.error("❌ Ping failed to 172.31.1.46 - Activating connection failure mode")
                log.info("🔄 Generating OUT_OF_SERVICE status for all ATMs due to network connectivity failure")
                
                # Generate OUT_OF_SERVICE data for all ATMs due to connection failure
                regional_data, terminal_details_data = self.generate_out_of_service_data()
                all_data["regional_data"] = regional_data
                all_data["terminal_details_data"] = terminal_details_data
                all_data["failover_mode"] = True
                
                # Calculate summary for failover mode
                total_regions = len(regional_data)
                total_terminals = len(terminal_details_data)
                all_data["summary"] = {
                    "total_regions": total_regions,
                    "total_terminals": total_terminals,
                    "total_terminal_details": total_terminals,
                    "failover_activated": True,
                    "connection_status": "PING_FAILED",
                    "failure_type": "NETWORK_CONNECTIVITY_FAILURE"
                }
                
                phase_times["connectivity_check"] = time.time() - phase_start
                phase_times["total_execution"] = time.time() - start_time
                all_data["performance_metrics"] = phase_times
                
                log.warning(f"⚡ Failover mode completed in {phase_times['total_execution']:.2f} seconds")
                
                # Save to database if requested
                if save_to_db and DB_AVAILABLE:
                    log.info("💾 Saving connection failure data to database...")
                    success = self.save_data_to_database(all_data, use_new_tables)
                    if success:
                        log.info("✅ Connection failure data saved to database successfully")
                    else:
                        log.error("Failed to save connection failure data to database")
                
                log.warning("Connection failure mode completed - all ATMs marked as OUT_OF_SERVICE due to ping failure")
                return True, all_data  # Return success=True as failover worked as intended
            else:
                phase_times["connectivity_check"] = time.time() - phase_start
                log.info(f"✅ Connectivity check passed in {phase_times['connectivity_check']:.2f} seconds")
        else:
            phase_times["connectivity_check"] = 0.0  # Demo mode skips connectivity check
            log.info("🎭 Demo mode: Skipping connectivity check")
        
        # Step 2: Authentication Phase
        log.info("🔐 Phase 2: Authentication...")
        phase_start = time.time()
        
        if not self.authenticate():
            log.error("❌ Authentication failed after connectivity was confirmed - Activating authentication failure mode")
            
            # Generate AUTH_FAILURE data for authentication failure (ping succeeded but login failed)
            regional_data, terminal_details_data = self.generate_auth_failure_data()
            
            all_data["regional_data"] = regional_data
            all_data["terminal_details_data"] = terminal_details_data
            all_data["failover_mode"] = True
            
            # Calculate summary for authentication failure
            total_regions = len(regional_data)
            total_terminals = len(terminal_details_data)
            all_data["summary"] = {
                "total_regions": total_regions,
                "total_terminals": total_terminals,
                "total_terminal_details": total_terminals,
                "failover_activated": True,
                "connection_status": "AUTH_FAILED",
                "failure_type": "AUTHENTICATION_FAILURE"
            }
            
            phase_times["authentication"] = time.time() - phase_start
            phase_times["total_execution"] = time.time() - start_time
            all_data["performance_metrics"] = phase_times
            
            log.warning(f"⚡ Authentication failure mode completed in {phase_times['total_execution']:.2f} seconds")
            
            # Save to database if requested
            if save_to_db and DB_AVAILABLE:
                log.info("💾 Saving authentication failure data to database...")
                success = self.save_data_to_database(all_data, use_new_tables)
                if success:
                    log.info("✅ AUTH_FAILURE data saved to database successfully")
                else:
                    log.error("❌ Failed to save AUTH_FAILURE data to database")
            
            log.warning("🔄 Authentication failure mode completed - all ATMs marked as OUT_OF_SERVICE due to login failure")
            return True, all_data  # Return success=True as failover worked as intended
        
        phase_times["authentication"] = time.time() - phase_start
        log.info(f"✅ Authentication successful in {phase_times['authentication']:.2f} seconds")
        
        # Step 3: Regional Data Retrieval Phase
        log.info("\n--- PHASE 1: Retrieving Regional ATM Data ---")
        log.info("📊 Phase 3: Regional data retrieval...")
        phase_start = time.time()
        
        raw_regional_data = self.fetch_regional_data()
        if raw_regional_data:
            processed_regional_data = self.process_regional_data(raw_regional_data)
            all_data["regional_data"] = processed_regional_data
            phase_times["regional_data"] = time.time() - phase_start
            log.info(f"✅ Regional data processing completed: {len(processed_regional_data)} regions in {phase_times['regional_data']:.2f} seconds")
        else:
            phase_times["regional_data"] = time.time()
            log.warning(f"⚠️ Regional data retrieval failed after {phase_times['regional_data']:.2f} seconds")
        
        # Skip terminal status data retrieval - focus only on terminal details
        log.info("📋 Phase 4: Preparing for terminal details retrieval...")
        log.info("Skipping terminal status data collection as requested")
        all_terminals = []
        status_counts = {}
        
        # Enhanced Comprehensive Terminal Search Strategy
        phase_start = time.time()
        log.info("🔍 Implementing comprehensive terminal search for all 14 ATMs...")
        all_terminals, status_counts = self.comprehensive_terminal_search()
        phase_times["terminal_search"] = time.time() - phase_start
        log.info(f"✅ Terminal search completed: Found {len(all_terminals)} terminals in {phase_times['terminal_search']:.2f} seconds")
        
        # Step 5: Fetch detailed information for ALL terminals
        log.info("🔧 Phase 5: Retrieving terminal details...")
        phase_start = time.time()
        log.info(f"Processing {len(all_terminals)} terminals for detailed information...")
        
        all_terminal_details = []
        current_retrieval_time = datetime.now(self.dili_tz)  # Use Dili time for database consistency
        
        for terminal in tqdm(all_terminals, desc="Fetching terminal details", unit="terminal"):
            terminal_id = terminal.get('terminalId')
            issue_state_code = terminal.get('issueStateCode', 'HARD')  # Default to HARD if not available
            
            if not terminal_id:
                log.warning(f"Skipping terminal with missing ID: {terminal}")
                continue
            
            # Windows production environment: Add retry logic for terminal details
            max_retries = 3 if os.name == 'nt' else 2  # More retries on Windows
            retry_delay = 2.0 if os.name == 'nt' else 1.0  # Longer delays on Windows
            
            terminal_data = None
            for attempt in range(max_retries):
                try:
                    # Get detailed information for this terminal
                    terminal_data = self.fetch_terminal_details(terminal_id, issue_state_code)
                    if terminal_data:
                        break  # Success, exit retry loop
                        
                except Exception as e:
                    error_msg = str(e)
                    if attempt < max_retries - 1:  # Not the last attempt
                        if os.name == 'nt':  # Windows-specific logging
                            log.warning(f"🪟 Windows retry {attempt + 1}/{max_retries} for terminal {terminal_id}: {error_msg}")
                        else:
                            log.warning(f"Retry {attempt + 1}/{max_retries} for terminal {terminal_id}: {error_msg}")
                        time.sleep(retry_delay)
                    else:
                        log.error(f"❌ Failed to fetch terminal {terminal_id} after {max_retries} attempts: {error_msg}")
            
            if terminal_data:
                # Process the terminal data
                terminal_body = terminal_data.get('body', [])
                items_processed = 0
                
                if isinstance(terminal_body, list) and terminal_body:
                    for item in terminal_body:
                        # Generate unique request ID for this specific ATM status record
                        unique_request_id = str(uuid.uuid4())
                        
                        # Extract the specific fields we need for this terminal
                        extracted_data = {
                            'unique_request_id': unique_request_id,  # Unique ID for each ATM status
                            'terminalId': item.get('terminalId', ''),
                            'location': item.get('location', ''),
                            'issueStateName': item.get('issueStateName', ''),
                            'serialNumber': item.get('serialNumber', ''),
                            'retrievedDate': current_retrieval_time.strftime('%Y-%m-%d %H:%M:%S')  # Current request retrieved date
                        }
                        
                        # Extract fault details if available
                        fault_list = item.get('faultList', [])
                        if fault_list and isinstance(fault_list, list) and len(fault_list) > 0:
                            # Get the first fault in the list (most recent)
                            fault = fault_list[0]
                            extracted_data.update({
                                'year': fault.get('year', ''),
                                'month': fault.get('month', ''),
                                'day': fault.get('day', ''),
                                'externalFaultId': fault.get('externalFaultId', ''),
                                'agentErrorDescription': fault.get('agentErrorDescription', '')
                            })
                            
                            # Add creationDate from faultList with proper formatting
                            creation_timestamp = fault.get('creationDate', None)
                            if creation_timestamp:
                                try:
                                    # Convert Unix timestamp (milliseconds) to datetime
                                    creation_dt = datetime.fromtimestamp(creation_timestamp / 1000, tz=self.dili_tz)
                                    # Format as dd:mm:YYYY hh:mm:ss
                                    extracted_data['creationDate'] = creation_dt.strftime('%d:%m:%Y %H:%M:%S')
                                except (ValueError, TypeError) as e:
                                    log.warning(f"Error converting creationDate for terminal {terminal_id}: {e}")
                                    extracted_data['creationDate'] = ''
                            else:
                                extracted_data['creationDate'] = ''
                        else:
                            # Set default values if no fault information is available
                            extracted_data.update({
                                'year': '',
                                'month': '',
                                'day': '',
                                'externalFaultId': '',
                                'agentErrorDescription': '',
                                'creationDate': ''
                            })
                            
                        # Add the status from the original search
                        extracted_data['fetched_status'] = terminal.get('fetched_status', '')
                        
                        # Add to the combined results
                        all_terminal_details.append(extracted_data)
                        items_processed += 1
                        
                        log.debug(f"Processed item {items_processed} for terminal {terminal_id} with unique_request_id: {unique_request_id}")
                        
                    log.info(f"✅ Added {items_processed} detail record(s) for terminal {terminal_id}")
                else:
                    log.warning(f"⚠️ No details found in body for terminal {terminal_id}")
            else:
                log.warning(f"❌ Failed to fetch details for terminal {terminal_id}")
            
            # Add a small delay between requests to avoid overwhelming the server
            if not self.demo_mode:
                time.sleep(1)
        
        all_data["terminal_details_data"] = all_terminal_details
        phase_times["terminal_details"] = time.time() - phase_start
        log.info(f"✅ Terminal details processing completed: {len(all_terminal_details)} details retrieved in {phase_times['terminal_details']:.2f} seconds")
        
        # Map parameter values to proper status names for summary
        status_name_mapping = {
            "WOUNDED": "WOUNDED",
            "HARD": "WOUNDED",  # HARD is a type of WOUNDED status
            "CASH": "WOUNDED",  # CASH is a type of WOUNDED status  
            "UNAVAILABLE": "OUT_OF_SERVICE",
            "AVAILABLE": "AVAILABLE",
            "WARNING": "WARNING",
            "ZOMBIE": "ZOMBIE"
        }
        
        # Create proper status counts for summary
        summary_status_counts = {
            "AVAILABLE": 0,
            "WARNING": 0,
            "WOUNDED": 0,
            "ZOMBIE": 0,
            "OUT_OF_SERVICE": 0
        }
        
        # Count terminals by proper status names
        for param_value, count in status_counts.items():
            proper_status = status_name_mapping.get(param_value, param_value)
            if proper_status in summary_status_counts:
                summary_status_counts[proper_status] += count
        
        # Create summary
        all_data["summary"] = {
            "total_regions": len(all_data["regional_data"]),
            "total_terminal_details": len(all_data["terminal_details_data"]),
            "terminal_details_with_unique_ids": len(all_terminal_details),
            "status_counts": summary_status_counts,
            "collection_note": "Enhanced retrieval: regional data and terminal details collected"
        }
        
        # Terminal details phase completion
        phase_times["terminal_details"] = time.time() - phase_start
        log.info(f"✅ Terminal details processing completed: {len(all_terminal_details)} details retrieved in {phase_times['terminal_details']:.2f} seconds")
        
        # Step 6: Logout to prevent session lockouts
        # Retrieve cash information if requested
        if include_cash_info:
            log.info("\n--- PHASE 8: Retrieving Cash Information ---")
            log.info("💰 Phase 8: Cash information retrieval...")
            phase_start = time.time()
            
            # Only retrieve cash information if we've successfully retrieved terminals
            if all_terminals:
                cash_records = []
                log.info(f"Retrieving cash information for {len(all_terminals)} terminals...")
                
                # Use a progress bar for cash information retrieval
                for terminal in tqdm(all_terminals, desc="Fetching cash information", unit="terminal"):
                    terminal_id = terminal.get('terminalId')
                    
                    if not terminal_id:
                        log.warning(f"Skipping cash info for terminal with missing ID: {terminal}")
                        continue
                    
                    # Fetch cash information for this terminal
                    cash_data = self.fetch_cash_information(terminal_id)
                    
                    if cash_data:
                        # Process the cash data into our structured format
                        processed_cash_record = self.process_cash_information(terminal_id, cash_data)
                        if processed_cash_record:
                            cash_records.append(processed_cash_record)
                    else:
                        # Create a null record for terminals without cash data
                        current_time = datetime.now(self.dili_tz)
                        null_record = self._create_null_cash_record(
                            terminal_id, current_time, {}, "Failed to fetch cash information"
                        )
                        cash_records.append(null_record)
                    
                    # Add a small delay between requests
                    if not self.demo_mode:
                        time.sleep(0.5)
                
                # Add cash records to the all_data dictionary
                all_data["cash_information_data"] = cash_records
                
                log.info(f"✅ Cash information retrieved for {len(cash_records)} terminals")
                
                # Save cash information to database if requested
                if save_to_db and DB_AVAILABLE and cash_records:
                    log.info("💾 Saving cash information to database...")
                    cash_save_success = self.save_cash_information_to_database(cash_records)
                    if cash_save_success:
                        log.info("✅ Cash information saved to database successfully")
                    else:
                        log.warning("⚠️ Failed to save cash information to database")
            else:
                log.warning("⚠️ No terminals available for cash information retrieval")
                all_data["cash_information_data"] = []
            
            phase_times["cash_information"] = time.time() - phase_start
            log.info(f"Cash information phase completed in {phase_times['cash_information']:.2f} seconds")
        
        # Step 9: Logout Phase
        log.info("🚪 Phase 9: Logout...")
        phase_start = time.time()
        logout_success = self.logout()
        phase_times["logout"] = time.time() - phase_start
        
        if logout_success:
            log.info(f"✅ Successfully logged out in {phase_times['logout']:.2f} seconds")
        else:
            log.warning(f"⚠️ Logout failed after {phase_times['logout']:.2f} seconds, but data retrieval completed successfully")
        
        # Final Performance Summary
        phase_times["total_execution"] = time.time() - start_time
        all_data["performance_metrics"] = phase_times
        
        log.info("=" * 80)
        log.info("🎉 COMBINED ATM DATA RETRIEVAL COMPLETED SUCCESSFULLY")
        log.info("=" * 80)
        log.info("📊 PERFORMANCE METRICS:")
        log.info(f"   • Total execution time: {phase_times['total_execution']:.2f} seconds")
        log.info(f"   • Connectivity check: {phase_times.get('connectivity_check', 0):.2f} seconds")
        log.info(f"   • Authentication: {phase_times.get('authentication', 0):.2f} seconds")
        log.info(f"   • Regional data: {phase_times.get('regional_data', 0):.2f} seconds")
        log.info(f"   • Terminal search: {phase_times.get('terminal_search', 0):.2f} seconds")
        log.info(f"   • Terminal details: {phase_times.get('terminal_details', 0):.2f} seconds")
        if include_cash_info:
            log.info(f"   • Cash information: {phase_times.get('cash_information', 0):.2f} seconds")
        log.info(f"   • Database save: {phase_times.get('database_save', 0):.2f} seconds")
        log.info(f"   • Logout: {phase_times.get('logout', 0):.2f} seconds")
        
        # Data Summary
        summary = all_data.get("summary", {})
        log.info("📈 DATA SUMMARY:")
        log.info(f"   • Regions processed: {summary.get('total_regions', 0)}")
        log.info(f"   • Terminals found: {summary.get('total_terminals', 0)}")
        log.info(f"   • Terminal details: {summary.get('total_terminal_details', 0)}")
        if include_cash_info:
            log.info(f"   • Cash records: {len(all_data.get('cash_information_data', []))}")
        if summary.get('failover_activated'):
            log.info(f"   • Failover mode: {summary.get('failure_type', 'UNKNOWN')}")
        log.info("=" * 80)
        
        return True, all_data
    
    def save_data_to_database(self, all_data: Dict[str, Any], use_new_tables: bool = False) -> bool:
        """
        Save all data to database (regional and terminal details)
        
        Args:
            all_data: Dictionary containing all retrieved data
            use_new_tables: Whether to use new database tables
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Prevent demo mode data from being saved to database
        if self.demo_mode:
            log.info("Demo mode active - skipping database save (demo data will not be saved)")
            return True  # Return True to indicate operation completed as expected
        
        if not DB_AVAILABLE or db_connector is None:
            log.warning("Database not available - skipping database save")
            return False
        
        success = True
        
        # Save regional data
        if all_data.get("regional_data"):
            log.info("Saving regional data to database...")
            if use_new_tables:
                regional_success = self.save_regional_to_new_table(
                    all_data["regional_data"], 
                    []  # No raw data for failover mode
                )
            else:
                regional_success = self.save_regional_to_database(all_data["regional_data"])
            
            if regional_success:
                log.info("Regional data saved successfully")
            else:
                log.error("Failed to save regional data")
                success = False
        
        # Save terminal details data
        if all_data.get("terminal_details_data"):
            log.info("Saving terminal details data to database...")
            if use_new_tables:
                terminal_success = self.save_terminal_details_to_new_table(
                    all_data["terminal_details_data"]
                )
            else:
                # For old tables, we would need to save using the old format
                # For now, just log that terminal details aren't saved to old tables
                log.info("Terminal details saving to old database tables not implemented")
                terminal_success = True
            
            if terminal_success:
                log.info("Terminal details data saved successfully")
            else:
                log.error("Failed to save terminal details data")
                success = False
        
        # Save cash information data if available
        if all_data.get("cash_information_data"):
            log.info("Saving cash information data to database...")
            cash_success = self.save_cash_information_to_database(all_data["cash_information_data"])
            if cash_success:
                log.info("Cash information data saved successfully")
            else:
                log.error("Failed to save cash information data")
                success = False
        
        # Save data - only if it was successfully retrieved
        
        return success

    def save_regional_to_database(self, processed_data: List[Dict[str, Any]]) -> bool:
        """
        Save processed regional data to the regional_atm_counts database table
        
        Args:
            processed_data: List of processed records
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE or db_connector is None:
            log.warning("Database not available - skipping database save")
            return False
        
        if not processed_data:
            log.warning("No processed data to save")
            return False
        
        log.info(f"Saving {len(processed_data)} records to database...")
        
        # Ensure table exists
        if not db_connector.check_regional_atm_counts_table():
            log.error("Failed to ensure regional_atm_counts table exists")
            return False
        
        conn = db_connector.get_db_connection()
        if not conn:
            log.error("Failed to connect to database")
            return False
        
        cursor = conn.cursor()
        
        try:
            for record in processed_data:
                cursor.execute("""
                    INSERT INTO regional_atm_counts (
                        unique_request_id,
                        region_code,
                        count_available,
                        count_warning,
                        count_zombie,
                        count_wounded,
                        count_out_of_service,
                        date_creation,
                        total_atms_in_region,
                        percentage_available,
                        percentage_warning,
                        percentage_zombie,
                        percentage_wounded,
                        percentage_out_of_service
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record['unique_request_id'],
                    record['region_code'],
                    record['count_available'],
                    record['count_warning'],
                    record['count_zombie'],
                    record['count_wounded'],
                    record['count_out_of_service'],
                    record['date_creation'],
                    record['total_atms_in_region'],
                    record['percentage_available'],
                    record['percentage_warning'],
                    record['percentage_zombie'],
                    record['percentage_wounded'],
                    record['percentage_out_of_service']
                ))
            
            conn.commit()
            log.info(f"Successfully saved {len(processed_data)} records to database")
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Database error while saving data: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def save_regional_to_new_table(self, processed_data: List[Dict[str, Any]], raw_data: List[Dict[str, Any]]) -> bool:
        """
        Save processed regional data to the new regional_data table with JSONB support
        
        Args:
            processed_data: List of processed regional records
            raw_data: Original raw data from API for JSONB storage
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE or db_connector is None:
            log.warning("Database not available - skipping regional_data table save")
            return False
        
        if not processed_data:
            log.warning("No processed regional data to save")
            return False
        
        log.info(f"Saving {len(processed_data)} records to regional_data table...")
        
        conn = db_connector.get_db_connection()
        if not conn:
            log.error("Failed to connect to database for regional_data table")
            return False
        
        cursor = conn.cursor()
        
        try:
            # Ensure regional_data table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_data (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    region_code VARCHAR(10) NOT NULL,
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    raw_regional_data JSONB NOT NULL,
                    count_available INTEGER,
                    count_warning INTEGER,
                    count_zombie INTEGER,
                    count_wounded INTEGER,
                    count_out_of_service INTEGER,
                    total_atms_in_region INTEGER
                )
            """)
            
            # Create index on region_code and retrieval_timestamp for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_region_timestamp 
                ON regional_data(region_code, retrieval_timestamp DESC)
            """)
            
            # Create JSONB index for raw_regional_data
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regional_data_raw_jsonb 
                ON regional_data USING GIN(raw_regional_data)
            """)
            
            # Create a mapping from processed data back to raw data
            raw_data_map = {}
            if raw_data:
                for raw_item in raw_data:
                    region_code = raw_item.get('regionCode')
                    if region_code:
                        raw_data_map[region_code] = raw_item
            
            # Generate a unique request ID for this batch
            batch_request_id = str(uuid.uuid4())
            
            # Insert processed data for each region
            for record in processed_data:
                region_code = record.get('region_code', 'UNKNOWN')
                raw_json_data = raw_data_map.get(region_code, {})
                
                cursor.execute("""
                    INSERT INTO regional_data (
                        unique_request_id,
                        region_code,
                        count_available,
                        count_warning,
                        count_zombie,
                        count_wounded,
                        count_out_of_service,
                        total_atms_in_region,
                        retrieval_timestamp,
                        raw_regional_data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record.get('unique_request_id', batch_request_id),  # Use record's ID or batch ID
                    region_code,
                    record.get('count_available', 0),
                    record.get('count_warning', 0),
                    record.get('count_zombie', 0),
                    record.get('count_wounded', 0),
                    record.get('count_out_of_service', 0),
                    record.get('total_atms_in_region', 0),
                    datetime.now(self.dili_tz),  # Use Dili time for consistency
                    json.dumps(raw_json_data)
                ))
            
            conn.commit()
            log.info(f"Successfully saved {len(processed_data)} records to regional_data table")
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Database error while saving to regional_data table: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def save_terminal_details_to_new_table(self, terminal_details: List[Dict[str, Any]]) -> bool:
        """
        Save terminal details data to the new terminal_details table with JSONB support
        
        Args:
            terminal_details: List of terminal detail records
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE or db_connector is None:
            log.warning("Database not available - skipping terminal_details table save")
            return False
        
        if not terminal_details:
            log.warning("No terminal details data to save")
            return False
        
        log.info(f"Saving {len(terminal_details)} records to terminal_details table...")
        
        conn = db_connector.get_db_connection()
        if not conn:
            log.error("Failed to connect to database for terminal_details table")
            return False
        
        cursor = conn.cursor()
        
        try:
            # Ensure terminal_details table exists
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
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_terminal_id 
                ON terminal_details(terminal_id, retrieved_date DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_details_fetched_status 
                ON terminal_details(fetched_status)
            """)
            
            # Create JSONB indexes
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
            
            # Insert records
            for detail in terminal_details:
                # Extract the unique request ID if available, or use the one from the detail
                unique_request_id = detail.get('unique_request_id', str(uuid.uuid4()))
                
                # Parse retrieved_date if it's a string
                retrieved_date = None
                if detail.get('retrievedDate'):
                    try:
                        retrieved_date_str = detail['retrievedDate']
                        if isinstance(retrieved_date_str, str):
                            # Try multiple datetime formats to handle both API and generated data
                            formats_to_try = [
                                '%Y-%m-%d %H:%M:%S',  # Original format: "2025-05-30 17:55:04"
                                '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with Z: "2025-06-17T02:13:18.640254Z"
                                '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO format with timezone: "2025-06-17T02:13:18.640254+00:00"
                                '%Y-%m-%dT%H:%M:%S%z',  # ISO format without microseconds: "2025-06-17T02:13:18+00:00"
                                '%Y-%m-%dT%H:%M:%S',  # ISO format simple: "2025-06-17T02:13:18"
                            ]
                            
                            retrieved_date = None
                            for fmt in formats_to_try:
                                try:
                                    if fmt.endswith('%z'):
                                        # Parse with timezone info and convert to Dili time
                                        retrieved_date = datetime.strptime(retrieved_date_str, fmt)
                                        retrieved_date = retrieved_date.astimezone(self.dili_tz)
                                    elif fmt.endswith('Z'):
                                        # Handle UTC format with Z
                                        retrieved_date = datetime.strptime(retrieved_date_str, fmt)
                                        retrieved_date = pytz.UTC.localize(retrieved_date).astimezone(self.dili_tz)
                                    else:
                                        # Parse without timezone and assume Dili time
                                        retrieved_date = datetime.strptime(retrieved_date_str, fmt)
                                        retrieved_date = self.dili_tz.localize(retrieved_date)
                                    break  # Successfully parsed, exit loop
                                except ValueError:
                                    continue  # Try next format
                                    
                            if not retrieved_date:
                                raise ValueError(f"Could not parse datetime format: {retrieved_date_str}")
                                
                    except (ValueError, TypeError) as e:
                        log.warning(f"Could not parse retrievedDate '{detail.get('retrievedDate')}': {e}")
                        retrieved_date = datetime.now(self.dili_tz)  # Use Dili time for fallback
                
                if not retrieved_date:
                    retrieved_date = datetime.now(self.dili_tz)  # Use Dili timezone for database consistency
                
                # Prepare JSONB data
                raw_terminal_data = {
                    "terminalId": detail.get('terminalId'),
                    "location": detail.get('location'),
                    "issueStateName": detail.get('issueStateName'),
                    "serialNumber": detail.get('serialNumber'),
                    "fetched_status": detail.get('fetched_status'),
                    "original_data": detail
                }
                
                fault_data = {
                    "year": detail.get('year'),
                    "month": detail.get('month'),
                    "day": detail.get('day'),
                    "externalFaultId": detail.get('externalFaultId'),
                    "agentErrorDescription": detail.get('agentErrorDescription'),
                    "creationDate": detail.get('creationDate')
                }
                
                metadata = {
                    "retrieval_timestamp": datetime.now(self.dili_tz).isoformat(),  # Store Dili timestamp for consistency
                    "demo_mode": self.demo_mode,
                    "unique_request_id": unique_request_id,
                    "processing_info": {
                        "has_fault_data": bool(detail.get('externalFaultId')),
                        "has_location": bool(detail.get('location')),
                        "status_at_retrieval": detail.get('fetched_status')
                    }
                }
                
                cursor.execute("""
                    INSERT INTO terminal_details (
                        unique_request_id,
                        terminal_id,
                        location,
                        issue_state_name,
                        serial_number,
                        retrieved_date,
                        fetched_status,
                        raw_terminal_data,
                        fault_data,
                        metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    unique_request_id,
                    detail.get('terminalId', ''),
                    detail.get('location', ''),
                    detail.get('issueStateName', ''),
                    detail.get('serialNumber', ''),
                    retrieved_date,
                    detail.get('fetched_status', 'UNKNOWN'),
                    json.dumps(raw_terminal_data),
                    json.dumps(fault_data),
                    json.dumps(metadata)
                ))
            
            conn.commit()
            log.info(f"Successfully saved {len(terminal_details)} records to terminal_details table")
            return True
            
        except Exception as e:
            # Safe rollback if connection exists
            conn_var = locals().get('conn')
            if conn_var is not None:
                try:
                    conn_var.rollback()
                except Exception:
                    pass
            log.error(f"Database error while saving to terminal_details table: {str(e)}")
            return False
        finally:
            # Safe resource cleanup
            cursor_var = locals().get('cursor')
            if cursor_var is not None:
                try:
                    cursor_var.close()
                except Exception:
                    pass
                    
            conn_var = locals().get('conn')
            if conn_var is not None:
                try:
                    conn_var.close()
                except Exception:
                    pass

    def fetch_cash_information(self, terminal_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cash information for a specific terminal (adapted from terminal_cash_information_retrieval.py)
        
        Args:
            terminal_id: Terminal ID to fetch cash information for
            
        Returns:
            Cash information data or None if failed
        """
        if self.demo_mode:
            log.info(f"DEMO MODE: Generating sample cash data for terminal {terminal_id}")
            
            # Generate realistic demo cash data
            demo_cassettes = [
                {
                    "cassId": "PCU00",
                    "cassLogicNbr": "01",
                    "cassPhysNbr": "00",
                    "cassTypeValue": "REJECT",
                    "cassTypeDescription": "Cassette of Rejected Notes",
                    "cassStatusValue": "OK",
                    "cassStatusDescription": "Cassete OK",
                    "cassStatusColor": "#3cd179",
                    "currency": None,
                    "notesVal": None,
                    "nbrNotes": 14,
                    "cassTotal": 0,
                    "percentage": 0.0
                },
                {
                    "cassId": "PCU01",
                    "cassLogicNbr": "02",
                    "cassPhysNbr": "01",
                    "cassTypeValue": "DISPENSE",
                    "cassTypeDescription": "Dispensing Cassette",
                    "cassStatusValue": "LOW",
                    "cassStatusDescription": "Cassette almost empty",
                    "cassStatusColor": "#90EE90",
                    "currency": "USD",
                    "notesVal": 20,
                    "nbrNotes": 542,
                    "cassTotal": 10840,
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
            log.error("No authentication token available for cash information retrieval")
            return None
        
        # Construct cash information URL with parameters
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
        Process raw cash information data into database format (adapted from terminal_cash_information_retrieval.py)
        
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
    
    def save_cash_information_to_database(self, cash_records: List[Dict[str, Any]]) -> bool:
        """
        Save cash information records to the database
        
        Args:
            cash_records: List of processed cash information records
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Skipping database save for cash information")
            return True
        
        if not cash_records:
            log.warning("No cash records to save")
            return False
        
        if not DB_AVAILABLE:
            log.error("Database not available for cash information save")
            return False
        
        try:
            # Use the db_connector module that handles environment variables properly
            if db_connector:
                conn = db_connector.get_db_connection()
                if not conn:
                    log.error("Failed to get database connection from db_connector")
                    return False
            else:
                import psycopg2
                
                # Get database connection parameters from environment variables
                db_config = {
                    "host": os.environ.get("DB_HOST", "localhost"),
                    "port": os.environ.get("DB_PORT", "5432"),
                    "database": os.environ.get("DB_NAME", "atm_monitor"),
                    "user": os.environ.get("DB_USER", "postgres"),
                    "password": os.environ.get("DB_PASSWORD", "")
                }
                
                # Log the actual host being used
                log.info(f"Connecting to database at {db_config['host']}:{db_config['port']} for cash information storage")
                
                conn = psycopg2.connect(
                    host=db_config["host"],
                    port=db_config["port"],
                    dbname=db_config["database"],
                    user=db_config["user"],
                    password=db_config["password"]
                )
            
            cursor = conn.cursor()
            
            # Ensure the terminal_cash_information table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminal_cash_information (
                    id SERIAL PRIMARY KEY,
                    unique_request_id UUID NOT NULL,
                    terminal_id VARCHAR(50) NOT NULL,
                    business_code VARCHAR(50),
                    technical_code VARCHAR(50),
                    external_id VARCHAR(50),
                    retrieval_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    event_date TIMESTAMP WITH TIME ZONE,
                    total_cash_amount DECIMAL(15, 2),
                    total_currency VARCHAR(10),
                    cassettes_data JSONB NOT NULL DEFAULT '[]'::jsonb,
                    raw_cash_data JSONB,
                    cassette_count INTEGER DEFAULT 0,
                    has_low_cash_warning BOOLEAN DEFAULT FALSE,
                    has_cash_errors BOOLEAN DEFAULT FALSE,
                    is_null_record BOOLEAN DEFAULT FALSE,
                    null_reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_cash_terminal_id 
                ON terminal_cash_information(terminal_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_cash_timestamp 
                ON terminal_cash_information(retrieval_timestamp DESC)
            """)
            
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
            # Safe rollback if connection exists
            conn_var = locals().get('conn')
            if conn_var is not None:
                try:
                    conn_var.rollback()
                except Exception:
                    pass
            log.error(f"❌ Database error while saving cash information: {str(e)}")
            return False
        finally:
            # Safe resource cleanup
            cursor_var = locals().get('cursor')
            if cursor_var is not None:
                try:
                    cursor_var.close()
                except Exception:
                    pass
                    
            conn_var = locals().get('conn')
            if conn_var is not None:
                try:
                    conn_var.close()
                except Exception:
                    pass

    def comprehensive_terminal_search(self) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Discover all terminals using comprehensive search strategy
        
        Returns:
            Tuple of (all discovered terminals, status counts)
        """
        log.info("🔍 Starting comprehensive terminal search...")
        
        all_terminals = []
        found_terminal_ids = set()
        status_counts = {}  # Track terminal counts by status
        
        for param_value in tqdm(PARAMETER_VALUES, desc="Searching statuses", unit="status"):
            try:
                terminals = self.get_terminals_by_status(param_value)
                
                # Track status count
                status_counts[param_value] = len(terminals)
                
                if terminals:
                    log.info(f"Found {len(terminals)} terminals with status {param_value}")
                    
                    for terminal in terminals:
                        # Mark the status we retrieved this terminal from
                        terminal['fetched_status'] = param_value
                        
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
        
        # Terminal count by status
        for status, count in status_counts.items():
            log.info(f"Status {status}: {count} terminals")
        
        return all_terminals, status_counts

# Main execution point of the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combined ATM Data Retrieval Script")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode without actual API calls")
    parser.add_argument("--save-to-db", action="store_true", help="Save the retrieved data to the database")
    parser.add_argument("--save-json", action="store_true", help="Save the retrieved data as JSON files")
    parser.add_argument("--use-new-tables", action="store_true", help="Use new database tables with JSONB support")
    parser.add_argument("--total-atms", type=int, default=14, help="Total number of ATMs for percentage calculation")
    parser.add_argument("--include-cash-info", action="store_true", help="Include cash information retrieval")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous operation mode")
    parser.add_argument("--interval", type=int, default=900, help="Interval between runs in seconds (default: 900 / 15 minutes)")
    parser.add_argument("--output-dir", type=str, default="./cash_output", help="Directory for JSON output files")
    args = parser.parse_args()
    
    # Ensure output directory exists if saving JSON
    if args.save_json:
        os.makedirs(args.output_dir, exist_ok=True)
        
    # Run counter and shutdown flag for continuous mode
    run_count = 0
    
    # Use a list to allow modification inside the signal handler
    # (Avoids nonlocal variables issue)
    running_state = [True]
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        log.warning("\n⚠️ Received shutdown signal, completing current run and exiting...")
        running_state[0] = False
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while running_state[0]:
            run_start_time = time.time()
            if args.continuous:
                run_count += 1
                log.info("=" * 80)
                log.info(f"🔄 CONTINUOUS MODE: Starting run #{run_count}")
                log.info(f"⏰ Run start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                log.info("=" * 80)
            
            # Initialize retriever with command line arguments
            retriever = CombinedATMRetriever(demo_mode=args.demo, total_atms=args.total_atms)
            
            # Run the combined data retrieval process
            success, data = retriever.retrieve_and_process_all_data(
                save_to_db=args.save_to_db,
                use_new_tables=args.use_new_tables,
                include_cash_info=args.include_cash_info
            )
            
            # Save JSON output if requested
            if args.save_json:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename_prefix = "combined_atm_data"
                if args.include_cash_info:
                    filename_prefix = "combined_atm_cash_data"
                
                output_filename = f"{args.output_dir}/{filename_prefix}_{timestamp}.json"
                try:
                    with open(output_filename, "w") as f:
                        json.dump(data, f, default=str, indent=2)
                    log.info(f"✅ Data saved to {output_filename}")
                except Exception as e:
                    log.error(f"❌ Error saving JSON output: {str(e)}")
            
            if success:
                if args.continuous:
                    run_duration = time.time() - run_start_time
                    log.info(f"✅ Run #{run_count} completed successfully in {run_duration:.2f} seconds")
                else:
                    log.info("🎉 Script completed successfully!")
                    sys.exit(0)
            else:
                if args.continuous:
                    log.warning(f"⚠️ Run #{run_count} completed with errors")
                else:
                    log.error("⚠️ Script completed with errors.")
                    sys.exit(1)
            
            # If not in continuous mode or shutdown requested, exit the loop
            if not args.continuous or not running_state[0]:
                break
                
            # Calculate sleep time for next run
            run_duration = time.time() - run_start_time
            sleep_time = max(0, args.interval - run_duration)
            
            if sleep_time > 0:
                log.info(f"💤 Sleeping for {sleep_time:.2f} seconds until next run...")
                # Use a smaller sleep increment to allow for faster response to signals
                sleep_increment = 1.0
                sleep_count = 0
                while sleep_count < sleep_time and running_state[0]:
                    time.sleep(min(sleep_increment, sleep_time - sleep_count))
                    sleep_count += sleep_increment
            else:
                log.warning(f"⚠️ Run took longer ({run_duration:.2f}s) than the requested interval ({args.interval}s), starting next run immediately")
                
        # Final message for continuous mode when exiting
        if args.continuous:
            log.info("=" * 80)
            log.info(f"👋 Continuous operation completed after {run_count} runs")
            log.info("=" * 80)
            
    except KeyboardInterrupt:
        # This should be caught by signal handler now
        log.warning("\n⚠️ Script interrupted by user")
        sys.exit(130)  # Standard SIGINT exit code
    except Exception as e:
        log.error(f"❌ Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
