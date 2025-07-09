#!/usr/bin/env python3
"""
Combined ATM Data Retrieval Script (Integrated Version)

A comprehensive script that combines regional ATM data retrieval with terminal-specific
fault information retrieval and cash information processing. This script integrates:
- Regional ATM data retrieval (for regional counts)  
- Terminal details with fault information
- Cash information retrieval and processing (NEW)

Features:
1. Authentication/login to the ATM monitoring system
2. Retrieving regional ATM data (fifth_graphic) from reports dashboard
3. Processing and converting percentage data to actual counts
4. Fetching detailed terminal-specific fault information
5. Cash information retrieval for all terminals (NEW)
6. Comprehensive error handling and retry logic
7. JSON output support for all retrieved data
8. Optional database saving with rollback capability
9. Continuous operation mode with enhanced error handling

Usage:
    python combined_atm_retrieval_script_integrated.py [--demo] [--save-to-db] [--save-json] [--include-cash-info] [--total-atms 14]
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
from collections import defaultdict, deque

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging with enhanced formatting for continuous operation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s:%(lineno)d]: %(message)s",
    handlers=[
        logging.FileHandler("combined_atm_retrieval.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("CombinedATMRetrieval")

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
    from db_connector_new import db_connector
    DB_AVAILABLE = True
except ImportError:
    try:
        import db_connector
        DB_AVAILABLE = True
    except ImportError:
        db_connector = None
        DB_AVAILABLE = False
        log.warning("Database connector not available - database operations will be skipped")

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGOUT_URL = "https://172.31.1.46/sigit/user/logout"
REPORTS_URL = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status"
DASHBOARD_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"
CASH_INFO_URL = "https://172.31.1.46/sigit/terminal/searchTerminal"  # NEW: Cash information URL

# Primary and fallback login credentials
PRIMARY_LOGIN_PAYLOAD = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2025@"
}

FALLBACK_LOGIN_PAYLOAD = {
    "user_name": "Adelaide",
    "password": "Adelaide02052024*"
}

# Active login payload (will be set during authentication)
LOGIN_PAYLOAD = PRIMARY_LOGIN_PAYLOAD.copy()

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
    """Main class for handling combined ATM data retrieval (regional + terminal details + cash information)"""
    
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
                timeout=15  # 15 second timeout for ping
            )
            
            # Check if ping was successful
            if result.returncode == 0:
                log.info(f"✅ Ping successful to {target_host}")
                return True
            else:
                log.error(f"❌ Ping failed to {target_host}")
                log.error(f"Ping output: {result.stdout}")
                log.error(f"Ping errors: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            log.error(f"❌ Ping timeout to {target_host} (15 seconds)")
            return False
        except FileNotFoundError:
            log.error("❌ Ping command not found on this system")
            return False
        except Exception as e:
            log.error(f"❌ Unexpected error during ping: {str(e)}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authenticate with the ATM monitoring system
        Try primary credentials first, then fallback to secondary credentials if primary fails
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Simulating successful authentication")
            self.user_token = "demo_token_" + str(int(time.time()))
            return True
        
        global LOGIN_PAYLOAD  # Make LOGIN_PAYLOAD modifiable
        
        # Try primary credentials first
        log.info("Attempting authentication with primary credentials (Lucky.Saputra)...")
        
        if self._try_authentication(PRIMARY_LOGIN_PAYLOAD):
            LOGIN_PAYLOAD = PRIMARY_LOGIN_PAYLOAD.copy()
            log.info("✅ Authentication successful with primary credentials (Lucky.Saputra)")
            return True
        
        # If primary fails, try fallback credentials
        log.warning("Primary authentication failed, trying fallback credentials (Adelaide)...")
        
        if self._try_authentication(FALLBACK_LOGIN_PAYLOAD):
            LOGIN_PAYLOAD = FALLBACK_LOGIN_PAYLOAD.copy()
            log.info("✅ Authentication successful with fallback credentials (Adelaide)")
            return True
        
        # Both authentication attempts failed
        log.error("❌ Authentication failed with both primary and fallback credentials")
        return False
    
    def _try_authentication(self, credentials: Dict[str, str]) -> bool:
        """
        Try authentication with the provided credentials
        
        Args:
            credentials: Dictionary containing user_name and password
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            response = self.session.post(
                LOGIN_URL,
                json=credentials,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=self.default_timeout
            )
            response.raise_for_status()
            
            login_data = response.json()
            log.debug(f"Login response structure: {list(login_data.keys())}")
            
            # Extract user token from various possible locations in response
            user_token = None
            
            # Method 1: Direct token fields
            for key in ['user_token', 'token']:
                if key in login_data:
                    user_token = login_data[key]
                    break
            
            # Method 2: From header field
            if not user_token and 'header' in login_data:
                user_token = login_data['header'].get('user_token')
            
            if user_token:
                self.user_token = user_token
                log.debug(f"User token extracted successfully for {credentials['user_name']}")
                return True
            else:
                log.warning(f"Authentication failed for {credentials['user_name']}: Unable to extract user token from response")
                log.debug(f"Available keys in response: {list(login_data.keys())}")
                return False
                
        except requests.exceptions.RequestException as e:
            log.warning(f"Authentication request failed for {credentials['user_name']}: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            log.warning(f"Authentication response not valid JSON for {credentials['user_name']}: {str(e)}")
            return False
        except Exception as e:
            log.warning(f"Unexpected error during authentication for {credentials['user_name']}: {str(e)}")
            return False
    
    def refresh_token(self) -> bool:
        """
        Refresh the authentication token by re-authenticating
        
        Returns:
            bool: True if token refresh successful, False otherwise
        """
        log.info("Refreshing authentication token...")
        old_token = self.user_token
        self.user_token = None  # Clear old token
        
        if self.authenticate():
            log.info(f"✅ Token refreshed successfully")
            return True
        else:
            log.error("❌ Token refresh failed")
            self.user_token = old_token  # Restore old token
            return False
    
    def logout(self) -> bool:
        """
        Logout from the system to prevent session lockouts
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Simulating logout")
            return True
        
        if not self.user_token:
            log.warning("No user token available for logout")
            return False
        
        try:
            logout_payload = {
                "header": {
                    "logged_user": LOGIN_PAYLOAD["user_name"],
                    "user_token": self.user_token
                },
                "body": {}
            }
            
            response = self.session.put(
                LOGOUT_URL,
                json=logout_payload,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=self.default_timeout
            )
            response.raise_for_status()
            
            logout_data = response.json()
            
            # Check logout response
            header = logout_data.get('header', {})
            if header.get('result_code') == '000':
                log.info("Successfully logged out")
                self.user_token = None
                return True
            else:
                log.warning(f"Logout returned non-success code: {header.get('result_code')} - {header.get('result_description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            log.error(f"Logout request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            log.error(f"Logout response not valid JSON: {str(e)}")
            return False
        except Exception as e:
            log.error(f"Unexpected error during logout: {str(e)}")
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
            log.error("No authentication token available for regional data retrieval")
            return None
        
        log.info("Fetching regional ATM data from reports dashboard...")
        
        dashboard_payload = {
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
                response = self.session.put(
                    REPORTS_URL,
                    json=dashboard_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=self.default_timeout
                )
                response.raise_for_status()
                
                dashboard_data = response.json()
                
                # Check if fifth_graphic exists in the response
                if 'fifth_graphic' in dashboard_data:
                    fifth_graphic = dashboard_data['fifth_graphic']
                    if isinstance(fifth_graphic, list) and len(fifth_graphic) > 0:
                        log.info(f"✅ Successfully retrieved regional data: {len(fifth_graphic)} regions")
                        return fifth_graphic
                    else:
                        log.warning("fifth_graphic exists but is empty or not a list")
                        return None
                else:
                    log.warning("fifth_graphic not found in dashboard response")
                    log.debug(f"Available keys in response: {list(dashboard_data.keys())}")
                    return None
                    
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Token may have expired, attempting to refresh...")
                    if self.refresh_token():
                        log.info("Token refreshed successfully, retrying...")
                        dashboard_payload["header"]["user_token"] = self.user_token
                        continue
                    else:
                        log.error("Failed to refresh token")
                        return None
                
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"❌ Failed to fetch regional data after {max_retries} attempts")
                    return None
                
                time.sleep(2)  # Wait before retry
                
            except json.JSONDecodeError as ex:
                log.error(f"❌ Dashboard response not valid JSON: {str(ex)}")
                return None
                
            except Exception as ex:
                log.error(f"❌ Unexpected error fetching regional data: {str(ex)}")
                return None
        
        return None

    def get_terminals_by_status(self, param_value: str) -> List[Dict[str, Any]]:
        """
        Get terminals filtered by a specific status parameter
        
        Args:
            param_value: Status parameter to filter by (WOUNDED, AVAILABLE, etc.)
            
        Returns:
            List of terminals matching the status, or empty list if none found
        """
        if self.demo_mode:
            log.info(f"Demo mode: Generating sample terminals for status {param_value}")
            
            # Generate realistic demo data based on status
            demo_terminals = []
            if param_value == "AVAILABLE":
                demo_terminals = [
                    {"terminalId": "83", "issueStateCode": "AVAILABLE"},
                    {"terminalId": "2603", "issueStateCode": "AVAILABLE"},
                    {"terminalId": "88", "issueStateCode": "AVAILABLE"}
                ]
            elif param_value == "WOUNDED":
                demo_terminals = [
                    {"terminalId": "87", "issueStateCode": "HARD"},
                    {"terminalId": "2604", "issueStateCode": "CASH"}
                ]
            elif param_value == "WARNING":
                demo_terminals = [
                    {"terminalId": "49", "issueStateCode": "WARNING"}
                ]
            
            return demo_terminals
        
        if not self.user_token:
            log.error(f"No authentication token available for status {param_value}")
            return []
        
        dashboard_url_with_param = f"{DASHBOARD_URL}&paramValue={param_value}"
        
        dashboard_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": {}
        }
        
        max_retries = 3
        retry_count = 0
        terminals = []
        
        while retry_count < max_retries:
            try:
                log.debug(f"Fetching terminals for status {param_value} (attempt {retry_count + 1})")
                
                response = self.session.put(
                    dashboard_url_with_param,
                    json=dashboard_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=self.default_timeout
                )
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    dashboard_data = response.json()
                except json.JSONDecodeError:
                    log.warning(f"Response for {param_value} is not valid JSON, trying to fix...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        log.error(f"All JSON parsing attempts failed for {param_value}. Skipping this parameter.")
                        return []
                    log.info(f"Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                
                # Check for header and update token if provided
                if "header" in dashboard_data and "user_token" in dashboard_data["header"]:
                    self.user_token = dashboard_data["header"]["user_token"]
                
                # Extract terminals from body
                if "body" in dashboard_data and isinstance(dashboard_data["body"], list):
                    terminals = dashboard_data["body"]
                    log.debug(f"Found {len(terminals)} terminals for status {param_value}")
                    return terminals
                else:
                    log.warning(f"No terminals found in body for status {param_value}")
                    return []
                    
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for status {param_value} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Token may have expired, attempting to refresh...")
                    if self.refresh_token():
                        log.info("Token refreshed successfully, retrying...")
                        dashboard_payload["header"]["user_token"] = self.user_token
                        continue
                    else:
                        log.error("Failed to refresh token")
                        return []
                
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"❌ Failed to fetch terminals for status {param_value} after {max_retries} attempts")
                    return []
                
                time.sleep(2)  # Wait before retry
                continue
        
        return terminals

    def fetch_terminal_details(self, terminal_id: str, issue_state_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific terminal
        Enhanced with Windows production environment optimizations
        
        Args:
            terminal_id: Terminal ID to fetch details for
            issue_state_code: Issue state code for the terminal
            
        Returns:
            Terminal detail data or None if failed
        """
        if self.demo_mode:
            log.info(f"Demo mode: Generating sample terminal details for {terminal_id}")
            
            # Generate realistic demo terminal details
            return {
                "header": {"result_code": "000"},
                "body": [{
                    "terminalId": terminal_id,
                    "location": f"Demo Location for Terminal {terminal_id}",
                    "issueStateName": "AVAILABLE" if issue_state_code == "AVAILABLE" else "WOUNDED",
                    "serialNumber": f"DEMO{terminal_id}",
                    "year": "2025",
                    "month": "07",
                    "day": "07",
                    "externalFaultId": "" if issue_state_code == "AVAILABLE" else f"DEMO_FAULT_{terminal_id}",
                    "agentErrorDescription": "" if issue_state_code == "AVAILABLE" else f"Demo fault for terminal {terminal_id}",
                    "creationDate": "07:07:2025 15:30:00"
                }]
            }
        
        if not self.user_token:
            log.error(f"No authentication token available for terminal {terminal_id}")
            return None
        
        # Construct terminal details URL with parameters
        details_url = f"{DASHBOARD_URL}&terminal_id={terminal_id}&issueStateCode={issue_state_code}"
        
        details_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": {}
        }
        
        # Windows production environment: Enhanced retry logic
        max_retries = 3 if os.name == 'nt' else 2  # More retries on Windows
        retry_delay = 2.0 if os.name == 'nt' else 1.0  # Longer delays on Windows
        retry_count = 0
        success = False
        terminal_data = None
        
        while retry_count < max_retries and not success:
            try:
                log.debug(f"Fetching details for terminal {terminal_id} (attempt {retry_count + 1})")
                
                # Windows: Use longer timeout for better reliability
                timeout = (45, 90) if os.name == 'nt' else self.default_timeout
                
                response = self.session.put(
                    details_url,
                    json=details_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=timeout
                )
                response.raise_for_status()
                
                terminal_data = response.json()
                
                # Validate response structure
                if not isinstance(terminal_data, dict):
                    log.warning(f"Invalid response type for terminal {terminal_id}: {type(terminal_data)}")
                    retry_count += 1
                    continue
                
                # Check for success in header
                header = terminal_data.get('header', {})
                if header.get('result_code') != '000':
                    log.warning(f"API returned error for terminal {terminal_id}: {header.get('result_description', 'Unknown error')}")
                    retry_count += 1
                    continue
                
                # Update token if a new one was returned
                if "user_token" in header:
                    self.user_token = header["user_token"]
                
                success = True
                log.debug(f"✅ Successfully fetched details for terminal {terminal_id}")
                
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for terminal {terminal_id} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Windows-specific error handling
                if os.name == 'nt':
                    error_msg = str(ex)
                    if "WinError" in error_msg:
                        log.warning(f"Windows network error detected for terminal {terminal_id}")
                    elif "timeout" in error_msg.lower():
                        log.warning(f"Windows timeout detected for terminal {terminal_id} - extending retry delay")
                        retry_delay = 3.0  # Extend delay for Windows timeouts
                
                # Check if this might be a token expiration issue
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Token may have expired, attempting to refresh...")
                    if self.refresh_token():
                        log.info("Token refreshed successfully, retrying...")
                        details_payload["header"]["user_token"] = self.user_token
                        continue
                    else:
                        log.error("Failed to refresh token")
                        break
                
                retry_count += 1
                if retry_count < max_retries:
                    log.info(f"Retrying terminal {terminal_id} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                
            except json.JSONDecodeError as ex:
                log.error(f"❌ Terminal details response for {terminal_id} not valid JSON: {str(ex)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(retry_delay)
                continue
                
            except Exception as ex:
                log.error(f"❌ Unexpected error fetching details for terminal {terminal_id}: {str(ex)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(retry_delay)
                continue
                
        return terminal_data

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
            log.warning("No raw regional data provided for processing")
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
            
            log.debug(f"Processing region {region_code} with state_count: {state_count}")
            
            # Initialize counts
            counts = {
                'count_available': 0,
                'count_warning': 0,
                'count_zombie': 0,
                'count_wounded': 0,
                'count_out_of_service': 0
            }
            
            # Convert percentages to actual counts
            for state, percentage_str in state_count.items():
                try:
                    percentage = float(percentage_str)
                    count = round(percentage * self.total_atms)
                    
                    # Map state names to our standardized field names
                    if state in SUPPORTED_STATES:
                        field_name = SUPPORTED_STATES[state]
                        counts[field_name] = count
                        log.debug(f"Region {region_code}: {state} = {percentage:.4f} ({count} ATMs)")
                    else:
                        log.warning(f"Unknown state '{state}' in region {region_code}")
                        
                except (ValueError, TypeError) as e:
                    log.error(f"Error converting percentage for {state} in region {region_code}: {e}")
                    continue
            
            # Calculate total ATMs for this region
            total_atms_in_region = sum(counts.values())
            
            # Calculate percentages (for verification)
            percentages = {}
            for field_name, count in counts.items():
                if total_atms_in_region > 0:
                    percentage = count / total_atms_in_region
                else:
                    percentage = 0.0
                percentages[field_name.replace('count_', 'percentage_')] = percentage
            
            # Create the processed record
            record = {
                'unique_request_id': str(uuid.uuid4()),
                'region_code': region_code,
                'date_creation': current_time,
                'total_atms_in_region': total_atms_in_region,
                **counts,
                **percentages
            }
            
            processed_records.append(record)
            
            log.info(f"✅ Processed region {region_code}: {total_atms_in_region} total ATMs")
            log.info(f"   Available: {counts['count_available']} ({percentages['percentage_available']*100:.1f}%)")
            log.info(f"   Warning: {counts['count_warning']} ({percentages['percentage_warning']*100:.1f}%)")
            log.info(f"   Wounded: {counts['count_wounded']} ({percentages['percentage_wounded']*100:.1f}%)")
            log.info(f"   Zombie: {counts['count_zombie']} ({percentages['percentage_zombie']*100:.1f}%)")
            log.info(f"   Out of Service: {counts['count_out_of_service']} ({percentages['percentage_out_of_service']*100:.1f}%)")
        
        log.info(f"Successfully processed {len(processed_records)} regional records")
        return processed_records

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

    def generate_out_of_service_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate OUT_OF_SERVICE data for all ATMs when connection fails
        
        Returns:
            Tuple of (regional_data, terminal_details_data)
        """
        log.info("Generating OUT_OF_SERVICE data for connection failure mode")
        
        current_time = datetime.now(self.dili_tz)
        
        # Generate regional data showing all ATMs as out of service
        regional_data = [{
            'unique_request_id': str(uuid.uuid4()),
            'region_code': "TL-DL",
            'count_available': 0,
            'count_warning': 0,
            'count_zombie': 0,
            'count_wounded': 0,
            'count_out_of_service': self.total_atms,
            'date_creation': current_time,
            'total_atms_in_region': self.total_atms,
            'percentage_available': 0.0,
            'percentage_warning': 0.0,
            'percentage_zombie': 0.0,
            'percentage_wounded': 0.0,
            'percentage_out_of_service': 1.0
        }]
        
        # Generate terminal details for expected ATMs as OUT_OF_SERVICE
        expected_terminal_ids = ['83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90']
        terminal_details_data = []
        
        for terminal_id in expected_terminal_ids:
            terminal_detail = {
                'unique_request_id': str(uuid.uuid4()),
                'terminalId': terminal_id,
                'location': f"Connection Failed - Terminal {terminal_id}",
                'issueStateName': "OUT_OF_SERVICE",
                'serialNumber': "CONNECTION_FAILED",
                'retrievedDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'year': "",
                'month': "",
                'day': "",
                'externalFaultId': "CONN_FAIL",
                'agentErrorDescription': "Connection failure to monitoring system",
                'creationDate': current_time.strftime('%d:%m:%Y %H:%M:%S'),
                'fetched_status': "OUT_OF_SERVICE"
            }
            terminal_details_data.append(terminal_detail)
        
        log.info(f"Generated OUT_OF_SERVICE data for {len(terminal_details_data)} terminals")
        return regional_data, terminal_details_data

    def generate_auth_failure_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate AUTH_FAILURE data for all ATMs when authentication fails
        
        Returns:
            Tuple of (regional_data, terminal_details_data)
        """
        log.info("Generating AUTH_FAILURE data for authentication failure mode")
        
        current_time = datetime.now(self.dili_tz)
        
        # Generate regional data showing all ATMs as out of service due to auth failure
        regional_data = [{
            'unique_request_id': str(uuid.uuid4()),
            'region_code': "TL-DL",
            'count_available': 0,
            'count_warning': 0,
            'count_zombie': 0,
            'count_wounded': 0,
            'count_out_of_service': self.total_atms,
            'date_creation': current_time,
            'total_atms_in_region': self.total_atms,
            'percentage_available': 0.0,
            'percentage_warning': 0.0,
            'percentage_zombie': 0.0,
            'percentage_wounded': 0.0,
            'percentage_out_of_service': 1.0
        }]
        
        # Generate terminal details for expected ATMs as OUT_OF_SERVICE due to auth failure
        expected_terminal_ids = ['83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90']
        terminal_details_data = []
        
        for terminal_id in expected_terminal_ids:
            terminal_detail = {
                'unique_request_id': str(uuid.uuid4()),
                'terminalId': terminal_id,
                'location': f"Authentication Failed - Terminal {terminal_id}",
                'issueStateName': "OUT_OF_SERVICE",
                'serialNumber': "AUTH_FAILED",
                'retrievedDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'year': "",
                'month': "",
                'day': "",
                'externalFaultId': "AUTH_FAIL",
                'agentErrorDescription': "Authentication failure to monitoring system",
                'creationDate': current_time.strftime('%d:%m:%Y %H:%M:%S'),
                'fetched_status': "OUT_OF_SERVICE"
            }
            terminal_details_data.append(terminal_detail)
        
        log.info(f"Generated AUTH_FAILURE data for {len(terminal_details_data)} terminals")
        return regional_data, terminal_details_data

    def retrieve_and_process_all_data(self, save_to_db: bool = False, use_new_tables: bool = False, include_cash_info: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Complete flow: authenticate, retrieve regional data, terminal details, and cash information
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
            "retrieval_timestamp": datetime.now(self.dili_tz).isoformat(),
            "demo_mode": self.demo_mode,
            "regional_data": [],
            "terminal_details_data": [],
            "cash_information_data": [],  # NEW: Cash information storage
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
                
                # Calculate summary for connection failure
                total_regions = len(regional_data)
                total_terminals = len(terminal_details_data)
                all_data["summary"] = {
                    "total_regions": total_regions,
                    "total_terminals": total_terminals,
                    "total_terminal_details": total_terminals,
                    "failover_activated": True,
                    "connection_status": "FAILED",
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
            phase_times["regional_data"] = time.time() - phase_start
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
                terminal_data = self.fetch_terminal_details(terminal_id, issue_state_code)
                if terminal_data:
                    break
                elif attempt < max_retries - 1:
                    log.warning(f"Retry {attempt + 1} for terminal {terminal_id} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
            
            if terminal_data:
                # Process terminal details from the response
                body = terminal_data.get('body', [])
                if body and isinstance(body, list):
                    items_processed = 0
                    unique_request_id = str(uuid.uuid4())
                    
                    for item in body:
                        if isinstance(item, dict):
                            # Set retrieval metadata
                            item['unique_request_id'] = unique_request_id
                            item['retrievedDate'] = current_retrieval_time.strftime('%Y-%m-%d %H:%M:%S')
                            item['fetched_status'] = terminal.get('fetched_status', 'UNKNOWN')
                            
                            all_terminal_details.append(item)
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
        
        # Step 6: Cash Information Retrieval Phase (NEW)
        if include_cash_info:
            log.info("\n--- PHASE 6: Retrieving Cash Information ---")
            log.info("💰 Phase 6: Cash information retrieval...")
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
        
        # Step 7: Logout Phase
        log.info("🚪 Phase 7: Logout...")
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
                    []
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
                    region_code = raw_item.get("hc-key", "UNKNOWN")
                    raw_data_map[region_code] = raw_item
            
            # Insert records
            for record in processed_data:
                region_code = record['region_code']
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
                    record['unique_request_id'],
                    region_code,
                    record['count_available'],
                    record['count_warning'],
                    record['count_zombie'],
                    record['count_wounded'],
                    record['count_out_of_service'],
                    record['total_atms_in_region'],
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
                        if isinstance(detail['retrievedDate'], str):
                            retrieved_date = datetime.strptime(detail['retrievedDate'], '%Y-%m-%d %H:%M:%S')
                            retrieved_date = self.dili_tz.localize(retrieved_date)
                        else:
                            retrieved_date = detail['retrievedDate']
                    except (ValueError, TypeError) as e:
                        log.warning(f"Error parsing retrievedDate for terminal {detail.get('terminalId')}: {e}")
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
            import psycopg2
            
            # Get database connection parameters
            db_config = {
                "host": os.environ.get("DB_HOST", "localhost"),
                "port": os.environ.get("DB_PORT", "5432"),
                "database": os.environ.get("DB_NAME", "atm_monitor"),
                "user": os.environ.get("DB_USER", "postgres"),
                "password": os.environ.get("DB_PASSWORD", "")
            }
            
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
                        has_cash_errors,
                        is_null_record,
                        null_reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    record['has_cash_errors'],
                    record['is_null_record'],
                    record['null_reason']
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
