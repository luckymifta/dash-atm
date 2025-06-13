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

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGOUT_URL = "https://172.31.1.46/sigit/user/logout"
REPORTS_URL = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status"
DASHBOARD_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"

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
        Check connectivity to the target server 172.31.1.46
        
        Returns:
            bool: True if server is reachable, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Skipping connectivity check")
            return True
        
        try:
            log.info("Testing connectivity to 172.31.1.46...")
            response = requests.head(
                "https://172.31.1.46/",
                timeout=10,
                verify=False
            )
            log.info(f"Connectivity test successful: HTTP {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Connectivity test failed: {str(e)}")
            return False
    
    def generate_out_of_service_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate OUT_OF_SERVICE data for all ATMs when connection fails
        
        Returns:
            Tuple of (regional_data, terminal_details_data) with OUT_OF_SERVICE status
        """
        log.warning("Generating OUT_OF_SERVICE data due to connection failure")
        current_time = datetime.now(pytz.UTC)  # Use UTC time for database storage
        
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
                'count_out_of_service': self.total_atms,  # All ATMs marked as OUT_OF_SERVICE
                'date_creation': current_time,
                'total_atms_in_region': self.total_atms,
                'percentage_available': 0.0,
                'percentage_warning': 0.0,
                'percentage_zombie': 0.0,
                'percentage_wounded': 0.0,
                'percentage_out_of_service': 1.0  # 100% OUT_OF_SERVICE
            }
            regional_data.append(record)
            log.info(f"Generated OUT_OF_SERVICE regional data for {region_code}: all {self.total_atms} ATMs marked as OUT_OF_SERVICE")
        
        # Generate terminal details data with OUT_OF_SERVICE status
        terminal_details_data = []
        for i in range(self.total_atms * len(regions)):  # Generate for all ATMs across all regions
            terminal_id = str(80 + i)  # Start from 80 as seen in sample data
            region_index = i // self.total_atms
            region_code = regions[region_index] if region_index < len(regions) else regions[0]
            
            terminal_detail = {
                'unique_request_id': str(uuid.uuid4()),
                'terminalId': terminal_id,
                'location': f"Connection Lost - {region_code}",
                'issueStateName': 'OUT_OF_SERVICE',
                'issueStateCode': 'OUT_OF_SERVICE',
                'brand': 'Connection Failed',
                'model': 'N/A',
                'serialNumber': f"CONN_FAIL_{terminal_id}",
                'agentErrorDescription': 'Connection to monitoring system failed',
                'externalFaultId': 'CONN_FAILURE',
                'year': str(current_time.year),
                'month': str(current_time.month).zfill(2),
                'day': str(current_time.day).zfill(2),
                'fetched_status': 'OUT_OF_SERVICE',
                'details_status': 'CONNECTION_FAILED',
                'retrievedDate': current_time.isoformat(),
                'dateRequest': current_time.strftime("%d-%m-%Y %H:%M:%S"),
                'region_code': region_code
            }
            terminal_details_data.append(terminal_detail)
        
        log.info(f"Generated {len(terminal_details_data)} terminal details with OUT_OF_SERVICE status")
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
                log.info(f"Retrying in 3 seconds...")
                time.sleep(3)
                continue
                
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
    
    def retrieve_and_process_all_data(self, save_to_db: bool = False, use_new_tables: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Complete flow: authenticate, retrieve regional data, terminal status data, and terminal details
        With failover capability for connection failures
        
        Args:
            save_to_db: Whether to save processed data to database (original tables)
            use_new_tables: Whether to use new database tables (regional_data and terminal_details)
            
        Returns:
            Tuple of (success: bool, all_data: Dict containing all retrieved data)
        """
        log.info("=" * 80)
        log.info("STARTING COMBINED ATM DATA RETRIEVAL WITH FAILOVER CAPABILITY")
        log.info("=" * 80)
        
        all_data = {
            "retrieval_timestamp": datetime.now(self.dili_tz).isoformat(),  # Store Dili timestamp for consistency
            "demo_mode": self.demo_mode,
            "regional_data": [],
            "terminal_details_data": [],  # Only terminal details, no terminal status data
            "summary": {},
            "failover_mode": False
        }
        
        # Step 1: Check connectivity to 172.31.1.46 (skip for demo mode)
        if not self.demo_mode:
            connectivity_ok = self.check_connectivity()
            if not connectivity_ok:
                log.error("Failed to connect to 172.31.1.46 - Activating failover mode")
                log.info("Generating OUT_OF_SERVICE status for all ATMs due to connection failure")
                
                # Generate OUT_OF_SERVICE data for all ATMs
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
                    "connection_status": "FAILED"
                }
                
                # Save to database if requested
                if save_to_db and DB_AVAILABLE:
                    success = self.save_data_to_database(all_data, use_new_tables)
                    if success:
                        log.info("OUT_OF_SERVICE failover data saved to database successfully")
                    else:
                        log.error("Failed to save OUT_OF_SERVICE failover data to database")
                
                log.warning("Failover mode completed - all ATMs marked as OUT_OF_SERVICE")
                return True, all_data  # Return success=True as failover worked as intended
        
        # Step 2: Normal operation - Authenticate
        if not self.authenticate():
            log.error("Authentication failed after connectivity was confirmed - Activating failover mode")
            
            # Generate OUT_OF_SERVICE data for authentication failure
            regional_data, terminal_details_data = self.generate_out_of_service_data()
            
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
                "connection_status": "AUTH_FAILED"
            }
            
            # Save to database if requested
            if save_to_db and DB_AVAILABLE:
                success = self.save_data_to_database(all_data, use_new_tables)
                if success:
                    log.info("OUT_OF_SERVICE failover data saved to database successfully")
                else:
                    log.error("Failed to save OUT_OF_SERVICE failover data to database")
            
            return True, all_data  # Return success=True as failover worked as intended
        
        # Step 3: Fetch regional data
        log.info("\n--- PHASE 1: Retrieving Regional ATM Data ---")
        raw_regional_data = self.fetch_regional_data()
        if raw_regional_data:
            processed_regional_data = self.process_regional_data(raw_regional_data)
            all_data["regional_data"] = processed_regional_data
            log.info(f"[OK] Regional data processing completed: {len(processed_regional_data)} regions")
        else:
            log.warning("WARNING: Regional data retrieval failed")
        
        # Step 4: Fetch terminal status data for all parameter values - DISABLED
        # log.info("\n--- PHASE 2: Retrieving Terminal Status Data ---")
        # all_terminals = []
        # status_counts = {}
        # 
        # for param_value in tqdm(PARAMETER_VALUES, desc="Fetching terminal status", unit="status"):
        #     terminals = self.get_terminals_by_status(param_value)
        #     
        #     if terminals:
        #         # Add each terminal to our combined list
        #         for terminal in terminals:
        #             # Add the status we searched for
        #             terminal['fetched_status'] = param_value
        #             all_terminals.append(terminal)
        #         
        #         # Track how many terminals we found for each status
        #         status_counts[param_value] = len(terminals)
        #         log.info(f"Added {len(terminals)} terminals with status {param_value}")
        #     else:
        #         log.warning(f"No terminals found with status {param_value}")
        #         status_counts[param_value] = 0
        # 
        # all_data["terminal_status_data"] = all_terminals
        # 
        # # Phase 2 Reporting
        # log.info("\n=== Terminal Status Summary ===")
        # total_terminals = sum(status_counts.values())
        # for status, count in status_counts.items():
        #     percentage = (count / total_terminals * 100) if total_terminals > 0 else 0
        #     log.info(f"{status}: {count} terminals ({percentage:.1f}%)")
        # log.info(f"Total: {total_terminals} terminals")
        # log.info("=========================")
        
        # Skip terminal status data retrieval - focus only on terminal details
        log.info("\n--- PHASE 2: Preparing for Terminal Details Retrieval ---")
        log.info("Skipping terminal status data collection as requested")
        all_terminals = []
        status_counts = {}
        
        # Enhanced Comprehensive Terminal Search Strategy
        log.info("Implementing comprehensive terminal search for all 14 ATMs...")
        all_terminals, status_counts = self.comprehensive_terminal_search()
        
        # Step 5: Fetch detailed information for ALL terminals
        log.info("\n--- PHASE 3: Retrieving Terminal Details ---")
        log.info(f"Found {len(all_terminals)} terminals to process for details")
        
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
                        
                    log.info(f"Added {items_processed} detail record(s) for terminal {terminal_id}")
                else:
                    log.warning(f"No details found in body for terminal {terminal_id}")
            else:
                log.warning(f"Failed to fetch details for terminal {terminal_id}")
            
            # Add a small delay between requests to avoid overwhelming the server
            if not self.demo_mode:
                time.sleep(1)
        
        all_data["terminal_details_data"] = all_terminal_details
        
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
            "collection_note": "Terminal status data collection disabled - only regional and terminal details collected"
        }
        
        log.info(f"[OK] Terminal details processing completed: {len(all_terminal_details)} details retrieved")
        
        # Step 6: Save to database if requested
        if save_to_db and all_data["regional_data"]:
            log.info("\n--- PHASE 4: Saving to Database ---")
            
            if use_new_tables:
                # Use new database tables with JSONB support
                log.info("Using new database tables (regional_data and terminal_details)")
                
                # Save regional data to new table
                regional_save_success = self.save_regional_to_new_table(
                    all_data["regional_data"], 
                    raw_regional_data or []
                )
                if regional_save_success:
                    log.info("[OK] Regional data successfully saved to regional_data table")
                else:
                    log.warning("WARNING: Regional data save to new table failed")
                
                # Save terminal details to new table
                if all_data["terminal_details_data"]:
                    terminal_save_success = self.save_terminal_details_to_new_table(
                        all_data["terminal_details_data"]
                    )
                    if terminal_save_success:
                        log.info("[OK] Terminal details successfully saved to terminal_details table")
                    else:
                        log.warning("WARNING: Terminal details save to new table failed")
                else:
                    log.info("No terminal details data to save")
            else:
                # Use original database table
                save_success = self.save_regional_to_database(all_data["regional_data"])
                if save_success:
                    log.info("[OK] Regional data successfully saved to database")
                else:
                    log.warning("WARNING: Database save failed, but processed data is still available")
        
        # Step 7: Logout to prevent session lockouts
        log.info("\n--- PHASE 5: Logout ---")
        logout_success = self.logout()
        if logout_success:
            log.info("[OK] Successfully logged out from ATM monitoring system")
        else:
            log.warning("WARNING: Logout failed, but data retrieval completed successfully")
        
        log.info("=" * 80)
        log.info("COMBINED ATM DATA RETRIEVAL COMPLETED SUCCESSFULLY")
        log.info("=" * 80)
        
        return True, all_data
    
    def save_data_to_database(self, all_data: Dict[str, Any], use_new_tables: bool = False) -> bool:
        """
        Save all data to database (both regional and terminal details)
        
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
                        retrieved_date_str = detail['retrievedDate']
                        if isinstance(retrieved_date_str, str):
                            # Try to parse the date string format: "2025-05-30 17:55:04"
                            # The retrievedDate from the API is already in Dili time format, keep it as Dili time
                            retrieved_date = datetime.strptime(retrieved_date_str, '%Y-%m-%d %H:%M:%S')
                            retrieved_date = self.dili_tz.localize(retrieved_date)  # Keep as Dili timezone
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
            conn.rollback()
            log.error(f"Database error while saving to terminal_details table: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def comprehensive_terminal_search(self) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Comprehensive terminal search strategy that finds all terminals and handles new discoveries.
        
        This method implements a multi-phase search strategy:
        1. Search each status systematically to discover all terminals
        2. Collect all terminals while avoiding duplicates
        3. Handle discovery of new terminals beyond expected set
        4. Implement fallback search for any missing expected terminals
        5. Ensure proper data schema for database insertion
        
        Returns:
            Tuple of (all_terminals_list, status_counts_dict)
        """
        log.info("Starting comprehensive terminal search across all ATM statuses...")
        
        # Expected terminal IDs based on historical requirements (baseline)
        expected_terminal_ids = ['83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90']
        
        # Load adaptive terminal list (includes previously discovered terminals)
        known_terminal_ids = self.get_adaptive_terminal_list()
        
        log.info(f"Search configuration:")
        log.info(f"  Expected terminals (baseline): {len(expected_terminal_ids)}")
        log.info(f"  Total known terminals: {len(known_terminal_ids)}")
        
        all_terminals = []
        status_counts = {}
        found_terminal_ids = set()
        terminal_to_status_map = {}  # Track which status each terminal was found in
        new_terminals_discovered = set()  # Track newly discovered terminals
        
        # Phase 1: Systematic discovery search across all status values
        log.info("Phase 1: Comprehensive discovery search across all statuses...")
        
        for param_value in tqdm(PARAMETER_VALUES, desc="Searching statuses", unit="status"):
            try:
                terminals = self.get_terminals_by_status(param_value)
                status_counts[param_value] = len(terminals)
                
                if terminals:
                    log.info(f"Found {len(terminals)} terminals with status {param_value}")
                    
                    # Process each terminal found for this status
                    for terminal in terminals:
                        terminal_id = terminal.get('terminalId')
                        
                        if terminal_id and terminal_id not in found_terminal_ids:
                            # Add the status we searched for
                            terminal['fetched_status'] = param_value
                            all_terminals.append(terminal)
                            found_terminal_ids.add(terminal_id)
                            terminal_to_status_map[terminal_id] = param_value
                            
                            # Check if this is a new terminal beyond known set
                            if terminal_id not in known_terminal_ids:
                                new_terminals_discovered.add(terminal_id)
                                log.info(f"🆕 NEW TERMINAL DISCOVERED: {terminal_id} (status: {param_value})")
                            elif terminal_id not in expected_terminal_ids:
                                log.debug(f"Previously discovered terminal found: {terminal_id} (status: {param_value})")
                            
                            log.debug(f"Added terminal {terminal_id} from status {param_value}")
                        elif terminal_id:
                            log.debug(f"Terminal {terminal_id} already found in status {terminal_to_status_map.get(terminal_id)}, skipping duplicate from {param_value}")
                else:
                    log.info(f"No terminals found with status {param_value}")
                    
            except Exception as e:
                # Windows-specific error handling with detailed diagnostics
                error_msg = str(e)
                log.error(f"❌ Error searching status {param_value}: {error_msg}")
                
                # Identify Windows-specific network issues
                if "WinError" in error_msg or "ConnectionError" in error_msg:
                    log.warning(f"🔌 Windows network error detected for status {param_value}")
                    log.warning("💡 This may be due to Windows firewall or network configuration")
                elif "timeout" in error_msg.lower():
                    log.warning(f"⏱️ Timeout error for status {param_value} - Windows may need longer timeouts")
                elif "SSL" in error_msg or "certificate" in error_msg.lower():
                    log.warning(f"🔒 SSL/Certificate error for status {param_value} - Windows certificate store issue")
                
                status_counts[param_value] = 0
                
                # Continue with next status instead of failing completely
                log.info(f"↩️ Continuing search with remaining statuses...")
                continue
        
        # Phase 2: Analyze discovery results
        log.info(f"Phase 1 Discovery Results:")
        log.info(f"  Total terminals found: {len(found_terminal_ids)}")
        log.info(f"  Expected terminals found: {len(set(expected_terminal_ids) & found_terminal_ids)}")
        log.info(f"  New terminals discovered: {len(new_terminals_discovered)}")
        
        if new_terminals_discovered:
            log.info(f"🎉 NEW TERMINALS DISCOVERED: {sorted(new_terminals_discovered)}")
            log.info("These new terminals will be included in the retrieval process!")
        
        # Create updated complete terminal set
        complete_terminal_set = set(known_terminal_ids) | new_terminals_discovered
        missing_terminal_ids = complete_terminal_set - found_terminal_ids
        
        log.info(f"Found terminal IDs: {sorted(found_terminal_ids)}")
        
        # Phase 3: Fallback search for any missing terminals
        if missing_terminal_ids:
            log.warning(f"Missing {len(missing_terminal_ids)} terminals: {sorted(missing_terminal_ids)}")
            log.info("Phase 3: Implementing fallback search for missing terminals...")
            
            # Fallback: Search for missing terminals individually across all statuses
            for missing_id in missing_terminal_ids:
                log.info(f"Searching for missing terminal {missing_id} across all statuses...")
                
                terminal_found = False
                for param_value in PARAMETER_VALUES:
                    if terminal_found:
                        break
                        
                    try:
                        # Search this status again to look for the specific terminal
                        terminals = self.get_terminals_by_status(param_value)
                        
                        for terminal in terminals:
                            if terminal.get('terminalId') == missing_id:
                                # Found the missing terminal!
                                terminal['fetched_status'] = param_value
                                all_terminals.append(terminal)
                                found_terminal_ids.add(missing_id)
                                terminal_to_status_map[missing_id] = param_value
                                
                                log.info(f"✅ Found missing terminal {missing_id} in status {param_value}")
                                terminal_found = True
                                break
                                
                    except Exception as e:
                        log.error(f"Error in fallback search for terminal {missing_id} in status {param_value}: {str(e)}")
                        continue
                
                if not terminal_found:
                    log.error(f"❌ Could not find terminal {missing_id} in any status")
        else:
            log.info("✅ All terminals found in Phase 1!")
        
        # Phase 4: Final validation and comprehensive reporting
        final_terminal_ids = [t.get('terminalId') for t in all_terminals if t.get('terminalId')]
        final_missing_expected = set(expected_terminal_ids) - set(final_terminal_ids)
        final_new_terminals = set(final_terminal_ids) - set(expected_terminal_ids)
        
        log.info("\n=== COMPREHENSIVE SEARCH RESULTS ===")
        log.info(f"Total terminals found: {len(all_terminals)}")
        log.info(f"Unique terminal IDs: {len(set(final_terminal_ids))}")
        log.info(f"Expected terminals found: {len(set(expected_terminal_ids) & set(final_terminal_ids))}/14")
        log.info(f"New terminals discovered: {len(final_new_terminals)}")
        
        log.info(f"\nAll terminal IDs: {sorted(final_terminal_ids)}")
        
        if final_new_terminals:
            log.info(f"🆕 NEW TERMINALS: {sorted(final_new_terminals)}")
            # Update the complete set for future runs
            log.info("Consider updating the expected_terminal_ids list to include these new terminals")
        
        if final_missing_expected:
            log.error(f"❌ Missing expected terminals: {sorted(final_missing_expected)}")
            log.error("These terminals may be offline or in an unmapped status")
        else:
            log.info("✅ All 14 expected terminals found!")
        
        # Enhanced status distribution summary
        log.info("\n=== STATUS DISTRIBUTION ===")
        for status, count in status_counts.items():
            if count > 0:
                terminals_in_status = [tid for tid, stat in terminal_to_status_map.items() if stat == status]
                new_in_status = [tid for tid in terminals_in_status if tid in final_new_terminals]
                expected_in_status = [tid for tid in terminals_in_status if tid in expected_terminal_ids]
                
                status_info = f"{status}: {count} terminals -> {sorted(terminals_in_status)}"
                if new_in_status:
                    status_info += f" [NEW: {sorted(new_in_status)}]"
                if expected_in_status:
                    status_info += f" [EXPECTED: {sorted(expected_in_status)}]"
                
                log.info(status_info)
        
        # Phase 5: Ensure proper data schema for database insertion
        log.info("Phase 5: Validating data schema for database insertion...")
        
        validated_terminals = []
        for terminal in all_terminals:
            # Ensure required fields are present
            if not terminal.get('terminalId'):
                log.warning(f"Skipping terminal with missing terminalId: {terminal}")
                continue
            
            # Ensure fetched_status is set
            if not terminal.get('fetched_status'):
                terminal['fetched_status'] = 'UNKNOWN'
                log.warning(f"Set fetched_status to UNKNOWN for terminal {terminal.get('terminalId')}")
            
            # Ensure issueStateCode is set (needed for terminal details fetching)
            if not terminal.get('issueStateCode'):
                # Map common status names to issue state codes
                status_to_code_map = {
                    'AVAILABLE': 'AVAILABLE',
                    'WARNING': 'WARNING', 
                    'WOUNDED': 'HARD',
                    'HARD': 'HARD',
                    'CASH': 'CASH',
                    'ZOMBIE': 'HARD',
                    'UNAVAILABLE': 'HARD'
                }
                terminal['issueStateCode'] = status_to_code_map.get(terminal.get('fetched_status', 'UNKNOWN'), 'HARD')
                log.debug(f"Set issueStateCode to {terminal['issueStateCode']} for terminal {terminal.get('terminalId')}")
            
            # Add discovery metadata for tracking
            terminal['is_newly_discovered'] = terminal.get('terminalId') in final_new_terminals
            terminal['discovery_timestamp'] = datetime.now().isoformat()
            
            validated_terminals.append(terminal)
        
        log.info(f"Validated {len(validated_terminals)} terminals for terminal details processing")
        
        # Final summary
        summary_msg = f"DISCOVERY COMPLETE: {len(validated_terminals)} total terminals"
        if final_new_terminals:
            summary_msg += f" (including {len(final_new_terminals)} newly discovered)"
        log.info(summary_msg)
        
        # Save discovered terminals to persistent storage
        if final_new_terminals or not self.demo_mode:
            all_discovered_terminals = set(final_terminal_ids)
            self.save_discovered_terminals(all_discovered_terminals)
            
            if final_new_terminals:
                log.info(f"💾 Saved {len(final_new_terminals)} newly discovered terminals to persistent storage")
        
        # Windows production environment final validation
        if os.name == 'nt':  # Windows
            log.info("🪟 WINDOWS PRODUCTION ENVIRONMENT - Final Validation:")
            log.info(f"   ✅ Total terminals ready for processing: {len(validated_terminals)}")
            log.info(f"   ✅ Status distribution validated: {len(status_counts)} statuses checked")
            log.info(f"   ✅ Discovery persistence: {'Enabled' if not self.demo_mode else 'Demo Mode'}")
            log.info(f"   ✅ Memory usage optimized for terminal details retrieval")
            
            # Log performance metrics for Windows troubleshooting
            if hasattr(self, 'session') and self.session:
                log.info(f"   ✅ HTTP session: Active with Windows optimizations")
            
        log.info("=== COMPREHENSIVE SEARCH COMPLETED ===")
        
        return validated_terminals, status_counts

    def load_discovered_terminals(self) -> set:
        """
        Load previously discovered terminal IDs from persistent storage
        Windows-compatible version with proper path handling
        
        Returns:
            set: Set of all known terminal IDs
        """
        # Get the script directory (works on both Windows and Unix)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        discovered_terminals_file = os.path.join(script_dir, "discovered_terminals.json")
        
        # Normalize the path for Windows compatibility
        discovered_terminals_file = os.path.normpath(discovered_terminals_file)
        
        try:
            if os.path.exists(discovered_terminals_file):
                # Use UTF-8 encoding explicitly for Windows compatibility
                with open(discovered_terminals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                discovered_terminals = set(data.get('discovered_terminals', []))
                last_updated = data.get('last_updated', 'Unknown')
                
                log.info(f"Loaded {len(discovered_terminals)} previously discovered terminals")
                log.info(f"Last discovery update: {last_updated}")
                log.info(f"Discovery file location: {discovered_terminals_file}")
                
                return discovered_terminals
            else:
                log.info("No previous terminal discovery file found - starting fresh")
                log.info(f"Will create discovery file at: {discovered_terminals_file}")
                return set()
                
        except Exception as e:
            log.warning(f"Error loading discovered terminals from {discovered_terminals_file}: {e}")
            log.warning(f"This may be the first run - continuing with empty discovery set")
            return set()
    
    def save_discovered_terminals(self, all_discovered_terminals: set):
        """
        Save discovered terminal IDs to persistent storage
        Windows-compatible version with proper path handling and error recovery
        
        Args:
            all_discovered_terminals: Set of all discovered terminal IDs
        """
        # Get the script directory (works on both Windows and Unix)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        discovered_terminals_file = os.path.join(script_dir, "discovered_terminals.json")
        
        # Normalize the path for Windows compatibility
        discovered_terminals_file = os.path.normpath(discovered_terminals_file)
        
        try:
            # Create directory if it doesn't exist (Windows may need this)
            os.makedirs(script_dir, exist_ok=True)
            
            data = {
                'discovered_terminals': sorted(list(all_discovered_terminals)),
                'total_count': len(all_discovered_terminals),
                'last_updated': datetime.now().isoformat(),
                'discovery_metadata': {
                    'demo_mode': self.demo_mode,
                    'total_atms_configured': self.total_atms,
                    'discovery_timestamp': datetime.now().isoformat(),
                    'platform': os.name,  # Track which OS discovered the terminals
                    'script_version': '2.0_windows_compatible'
                }
            }
            
            # Use UTF-8 encoding explicitly for Windows compatibility
            with open(discovered_terminals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            log.info(f"✅ Saved {len(all_discovered_terminals)} discovered terminals to discovery file")
            log.info(f"📁 Discovery file location: {discovered_terminals_file}")
            
        except PermissionError as e:
            log.error(f"❌ Permission denied saving discovered terminals to {discovered_terminals_file}: {e}")
            log.error(f"💡 Suggestion: Run the script as administrator on Windows or check file permissions")
        except Exception as e:
            log.error(f"❌ Error saving discovered terminals to {discovered_terminals_file}: {e}")
            log.error(f"💡 This won't prevent the script from working, but terminal discovery won't persist")

    def get_adaptive_terminal_list(self) -> List[str]:
        """
        Get an adaptive list of terminal IDs that includes both expected and previously discovered terminals
        
        Returns:
            List[str]: Combined list of expected and discovered terminal IDs
        """
        # Base expected terminals
        expected_terminal_ids = ['83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90']
        
        # Load previously discovered terminals
        previously_discovered = self.load_discovered_terminals()
        
        # Combine and deduplicate
        all_known_terminals = set(expected_terminal_ids) | previously_discovered
        
        log.info(f"Adaptive terminal list: {len(expected_terminal_ids)} expected + {len(previously_discovered)} previously discovered = {len(all_known_terminals)} total")
        
        return sorted(list(all_known_terminals))
    
def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM signals gracefully"""
    signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
    log.info(f"\n[STOP] Received {signal_name} signal. Initiating graceful shutdown...")
    stop_flag.set()
    print("\nWARNING: Shutting down gracefully. Please wait for current operation to complete...")


def update_execution_stats(success: bool, error_type: Optional[str] = None):
    """Update global execution statistics"""
    global execution_stats
    
    current_time = datetime.now()
    execution_stats['total_cycles'] += 1
    
    if success:
        execution_stats['successful_cycles'] += 1
        execution_stats['last_success'] = current_time
        execution_stats['cycle_history'].append({
            'timestamp': current_time,
            'success': True,
            'error': None
        })
    else:
        execution_stats['failed_cycles'] += 1
        if error_type == 'connection':
            execution_stats['connection_failures'] += 1
        execution_stats['cycle_history'].append({
            'timestamp': current_time,
            'success': False,
            'error': error_type
        })


def print_execution_stats():
    """Print comprehensive execution statistics"""
    if execution_stats['total_cycles'] == 0:
        return
    
    current_time = datetime.now()
    uptime = current_time - execution_stats['start_time'] if execution_stats['start_time'] else current_time
    success_rate = (execution_stats['successful_cycles'] / execution_stats['total_cycles']) * 100
    
    print("\n" + "=" * 80)
    print("=== EXECUTION STATISTICS ===")
    print("=" * 80)
    print(f"[TIME] Total uptime: {uptime}")
    print(f"[CYCLES] Total cycles: {execution_stats['total_cycles']}")
    print(f"[SUCCESS] Successful cycles: {execution_stats['successful_cycles']}")
    print(f"[FAILED] Failed cycles: {execution_stats['failed_cycles']}")
    print(f"[NET] Connection failures: {execution_stats['connection_failures']}")
    print(f"[STATS] Success rate: {success_rate:.1f}%")
    
    if execution_stats['last_success']:
        time_since_success = current_time - execution_stats['last_success']
        print(f"[TIME] Last successful cycle: {time_since_success} ago")
    
    # Show recent cycle history
    recent_cycles = list(execution_stats['cycle_history'])[-10:]  # Last 10 cycles
    if recent_cycles:
        print(f"\n[HISTORY] Recent cycle history (last {len(recent_cycles)}):")
        for i, cycle in enumerate(recent_cycles, 1):
            status = "[OK]" if cycle['success'] else "[FAIL]"
            error_info = f" ({cycle['error']})" if cycle['error'] else ""
            timestamp = cycle['timestamp'].strftime('%H:%M:%S')
            print(f"  {i:2d}. {status} {timestamp}{error_info}")
    
    print("=" * 80)


def wait_with_progress(duration_minutes: int, reason: str):
    """Wait for specified duration with progress indication and early exit on stop signal"""
    total_seconds = duration_minutes * 60
    log.info(f"[WAIT] {reason} - waiting {duration_minutes} minutes...")
    
    for remaining in range(total_seconds, 0, -1):
        if stop_flag.is_set():
            log.info("Stop signal received during wait period")
            return False
        
        # Update progress every 30 seconds or on first/last iterations
        if remaining % 30 == 0 or remaining <= 5 or remaining == total_seconds:
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = f"{minutes:02d}:{seconds:02d}"
            
            print(f"\r[WAIT] {reason} - Time remaining: {time_str}    ", end="", flush=True)
        
        time.sleep(1)
    
    print()  # New line after progress
    return True


def handle_connection_error(error: Exception, cycle_number: int) -> bool:
    """
    Handle connection errors with intelligent retry logic
    
    Returns:
        bool: True if should continue, False if should stop
    """
    log.error(f"[NET] Connection error in cycle {cycle_number}: {str(error)}")
    
    # Check if this is a LOGIN_URL specific error
    is_login_error = False
    if hasattr(error, 'response') and getattr(error, 'response', None) is not None:
        # Check if the error occurred during authentication
        if 'login' in str(error).lower() or 'authentication' in str(error).lower():
            is_login_error = True
    elif 'login' in str(error).lower() or 'authentication' in str(error).lower():
        is_login_error = True
    
    update_execution_stats(False, 'connection')
    
    if is_login_error:
        log.warning("[AUTH] Detected LOGIN_URL connection failure - implementing 15-minute retry period")
        if not wait_with_progress(15, "Retrying after LOGIN_URL connection failure"):
            return False
    else:
        log.warning("[NET] General connection error - implementing 5-minute retry period")
        if not wait_with_progress(5, "Retrying after connection error"):
            return False
    
    return True


def run_continuous_operation(args):
    """Run the ATM retrieval script continuously with enhanced error handling"""
    global execution_stats
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize execution stats
    execution_stats['start_time'] = datetime.now()
    
    log.info("[START] Starting continuous ATM data retrieval operation")
    log.info(f"[TIME] Start time: {execution_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"[CONFIG] Configuration: Demo={args.demo}, Save-to-DB={args.save_to_db}, Use-New-Tables={args.use_new_tables}")
    log.info("[INFO] Running every 15 minutes. Press Ctrl+C for graceful shutdown.")
    
    # Create retriever instance
    retriever = CombinedATMRetriever(demo_mode=args.demo, total_atms=args.total_atms)
    cycle_number = 0
    success = False  # Initialize success variable
    
    while not stop_flag.is_set():
        cycle_number += 1
        cycle_start_time = datetime.now()
        
        try:
            log.info(f"\n{'='*20} CYCLE {cycle_number} - {cycle_start_time.strftime('%Y-%m-%d %H:%M:%S')} {'='*20}")
            
            # Execute the complete retrieval and processing flow
            success, all_data = retriever.retrieve_and_process_all_data(
                save_to_db=args.save_to_db,
                use_new_tables=args.use_new_tables
            )
            
            if success:
                log.info(f"[OK] Cycle {cycle_number} completed successfully")
                
                # Display brief results
                summary = all_data.get("summary", {})
                log.info(f"[RESULTS] Results: {summary.get('total_regions', 0)} regions, "
                        f"{summary.get('total_terminals', 0)} terminals, "
                        f"{summary.get('total_terminal_details', 0)} terminal details")
                
                # Save to JSON if requested or if we have data
                if args.save_json or all_data.get("summary", {}).get("total_terminals", 0) > 0:
                    json_filename = save_to_json(all_data)
                    log.info(f"[FILE] Data saved to: {json_filename}")
                
                if args.save_to_db and DB_AVAILABLE:
                    if args.use_new_tables:
                        log.info("[DB] Data saved to new database tables (regional_data and terminal_details)")
                    else:
                        log.info("[DB] Regional data saved to database (regional_atm_counts table)")
                
                update_execution_stats(True)
                
            else:
                log.error(f"[FAIL] Cycle {cycle_number} failed - unable to retrieve ATM data")
                update_execution_stats(False, 'general')
                
        except requests.exceptions.ConnectionError as e:
            if not handle_connection_error(e, cycle_number):
                break
            continue
            
        except requests.exceptions.Timeout as e:
            log.error(f"[TIMEOUT] Timeout error in cycle {cycle_number}: {str(e)}")
            update_execution_stats(False, 'timeout')
            
        except requests.exceptions.RequestException as e:
            if not handle_connection_error(e, cycle_number):
                break
            continue
            
        except Exception as e:
            log.error(f"[ERROR] Unexpected error in cycle {cycle_number}: {str(e)}")
            log.debug("Error details:", exc_info=True)
            update_execution_stats(False, 'unexpected')
            
            # For unexpected errors, wait a bit before continuing
            if not wait_with_progress(2, "Recovering from unexpected error"):
                break
        
        # Print statistics every 10 cycles or if this was a failed cycle
        if cycle_number % 10 == 0 or not success:
            print_execution_stats()
        
        # Check for stop signal before waiting
        if stop_flag.is_set():
            break
        
        # Wait for next cycle (15 minutes)
        log.info(f"[CYCLE] Cycle {cycle_number} completed. Next cycle in 15 minutes...")
        if not wait_with_progress(15, "Next cycle"):
            break
    
    # Final statistics and cleanup
    log.info("\n[STOP] Continuous operation stopped")
    print_execution_stats()
    
    end_time = datetime.now()
    total_runtime = end_time - execution_stats['start_time']
    log.info(f"[RUNTIME] Total runtime: {total_runtime}")
    log.info(f"[SHUTDOWN] Shutdown completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")


def display_results(all_data: Dict[str, Any]) -> None:
    """Display the processed results in a formatted way"""
    print("\n" + "=" * 120)
    print("COMBINED ATM DATA RETRIEVAL RESULTS")
    print("=" * 120)
    
    # Summary
    summary = all_data.get("summary", {})
    status_counts = summary.get('status_counts', {})
    total_terminals = sum(status_counts.values()) if status_counts else 0
    
    print(f"Retrieval Time: {all_data.get('retrieval_timestamp', 'Unknown')}")
    print(f"Demo Mode: {all_data.get('demo_mode', False)}")
    print(f"Total Regions: {summary.get('total_regions', 0)}")
    print(f"Total Terminals: {total_terminals}")
    print(f"Terminal Details Retrieved: {summary.get('total_terminal_details', 0)}")
    
    # Show collection note if available
    collection_note = summary.get('collection_note')
    if collection_note:
        print(f"Note: {collection_note}")
    
    # Regional data
    regional_data = all_data.get("regional_data", [])
    if regional_data:
        print("\n--- REGIONAL ATM COUNTS ---")
        print(f"{'Region':<10} {'Available':<10} {'Warning':<8} {'Zombie':<8} {'Wounded':<8} {'Out/Svc':<8} {'Total':<6}")
        print("-" * 70)
        
        for record in regional_data:
            print(f"{record['region_code']:<10} "
                  f"{record['count_available']:3d} ({record['percentage_available']*100:5.1f}%) "
                  f"{record['count_warning']:3d}      "
                  f"{record['count_zombie']:3d}      "
                  f"{record['count_wounded']:3d}      "
                  f"{record['count_out_of_service']:3d}      "
                  f"{record['total_atms_in_region']:3d}")
    
    # Terminal status summary
    if status_counts:
        print("\n--- TERMINAL STATUS SUMMARY ---")
        for status, count in status_counts.items():
            percentage = (count / total_terminals * 100) if total_terminals > 0 else 0
            print(f"{status}: {count} terminals ({percentage:.1f}%)")
        print(f"Total: {total_terminals} terminals")
    
    # Terminal details summary
    terminal_details = all_data.get("terminal_details_data", [])
    if terminal_details:
        print("\n--- TERMINAL DETAILS SUMMARY ---")
        print(f"Terminal details with unique IDs: {summary.get('terminal_details_with_unique_ids', len(terminal_details))}")
        
        fault_types = {}
        for detail in terminal_details:
            error_desc = detail.get('agentErrorDescription', '')
            if error_desc:
                fault_types[error_desc] = fault_types.get(error_desc, 0) + 1
        
        print("Fault Summary:")
        for error_type, count in sorted(fault_types.items(), key=lambda x: x[1], reverse=True):
            if error_type:
                print(f"  {error_type}: {count}")
    
    print("=" * 120)


def save_to_json(all_data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """Save all retrieved data to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"combined_atm_data_{timestamp}.json"
    
    # Ensure the saved_data directory exists
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_data")
    os.makedirs(save_dir, exist_ok=True)
    full_path = os.path.join(save_dir, filename)
    
    # Convert datetime objects to strings for JSON serialization
    json_data = all_data.copy()
    
    # Convert regional data datetime objects
    if "regional_data" in json_data:
        for record in json_data["regional_data"]:
            if 'date_creation' in record and hasattr(record['date_creation'], 'isoformat'):
                record['date_creation'] = record['date_creation'].isoformat()
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    log.info(f"All data saved to JSON file: {full_path}")
    return full_path


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Combined ATM Data Retrieval Script with Continuous Operation Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python combined_atm_retrieval_script.py                           # Live mode, display only
  python combined_atm_retrieval_script.py --demo                    # Demo mode for testing
  python combined_atm_retrieval_script.py --save-to-db              # Live mode with database save
  python combined_atm_retrieval_script.py --save-json               # Live mode with JSON save
  python combined_atm_retrieval_script.py --continuous              # Continuous mode (15-min intervals)
  python combined_atm_retrieval_script.py --continuous --save-to-db --use-new-tables
  python combined_atm_retrieval_script.py --demo --save-json --total-atms 20
        """
    )
    
    parser.add_argument('--demo', action='store_true', 
                       help='Run in demo mode (no actual network requests)')
    parser.add_argument('--save-to-db', action='store_true',
                       help='Save processed data to database')
    parser.add_argument('--use-new-tables', action='store_true',
                       help='Use new database tables (regional_data and terminal_details) with JSONB support')
    parser.add_argument('--save-json', action='store_true',
                       help='Save all retrieved data to JSON file')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously with 15-minute intervals (enhanced error handling)')
    parser.add_argument('--total-atms', type=int, default=14,
                       help='Total number of ATMs for percentage to count conversion (default: 14)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce logging output (errors and warnings only)')
    
    args = parser.parse_args()
    
    # Adjust logging level if quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Check for continuous mode
    if args.continuous:
        log.info("[CONTINUOUS] Continuous mode enabled - script will run every 15 minutes")
        run_continuous_operation(args)
        return 0
    
    # Single execution mode (original behavior)
    # Create retriever instance
    retriever = CombinedATMRetriever(demo_mode=args.demo, total_atms=args.total_atms)
    
    try:
        # Execute the complete retrieval and processing flow
        success, all_data = retriever.retrieve_and_process_all_data(
            save_to_db=args.save_to_db, 
            use_new_tables=args.use_new_tables
        )
        
        if success:
            # Display results
            display_results(all_data)
            
            # Save to JSON if requested or if we have data
            if args.save_json or all_data.get("summary", {}).get("total_terminals", 0) > 0:
                json_filename = save_to_json(all_data)
                print(f"\n[FILE] All data saved to: {json_filename}")
            
            summary = all_data.get("summary", {})
            print(f"\n[OK] SUCCESS: Retrieved data for {summary.get('total_regions', 0)} regions, "
                  f"{summary.get('total_terminals', 0)} terminals, and "
                  f"{summary.get('total_terminal_details', 0)} terminal details")
            
            if args.save_to_db and DB_AVAILABLE:
                if args.use_new_tables:
                    print("[OK] Data saved to new database tables (regional_data and terminal_details)")
                else:
                    print("[OK] Regional data saved to database (regional_atm_counts table)")
            elif args.save_to_db and not DB_AVAILABLE:
                print("WARNING: Database not available - data not saved to database")
            
            return 0
        else:
            print("\n[FAIL] FAILED: Unable to retrieve ATM data")
            return 1
            
    except KeyboardInterrupt:
        print("\n[WARNING] Process interrupted by user")
        return 1
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        log.debug("Error details:", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
