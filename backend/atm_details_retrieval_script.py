#!/usr/bin/env python3
"""
ATM Details Retrieval Script for Timor-Leste Banking System

This script retrieves detailed information about individual ATM terminals
including their status, location, and operational details.

It can operate in demo mode (with simulated data) or production mode
connecting to the actual API endpoint.
"""

import os
import sys
import time
import uuid
import json
import logging
import argparse
import random
import pytz
import urllib3
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# Import db_connector or provide a stub if not available
try:
    from db_connector import get_connection  # type: ignore
    DB_AVAILABLE = True
    logging.info("Database connector available")
except ImportError:
    logging.warning("db_connector module not found. Database operations will be disabled.")
    DB_AVAILABLE = False
    def get_connection():
        logging.error("Database operations not available: db_connector module not found")
        return None

# Try to import tabulate, but provide fallback if not available
try:
    from tabulate import tabulate  # type: ignore
except ImportError:
    logging.warning("tabulate module not found. Using simple table formatting.")
    def tabulate(data, headers, tablefmt=None):  # type: ignore
        """Simple tabulate fallback function"""
        result = []
        # Add headers
        result.append(" | ".join(str(h) for h in headers))
        result.append("-" * (sum(len(str(h)) for h in headers) + 3 * len(headers)))
        # Add rows
        for row in data:
            result.append(" | ".join(str(item) for item in row))
        return "\n".join(result)

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.warning("python-dotenv not installed, skipping .env loading")

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
ATM_DETAILS_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"

# Get credentials from environment variables or use defaults
LOGIN_PAYLOAD = {
    "user_name": os.environ.get("ATM_USERNAME", "Lucky.Saputra"),
    "password": os.environ.get("ATM_PASSWORD", "TimlesMon2024")
}

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://172.31.1.46",
    "Referer": "https://172.31.1.46/sigitportal/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Connection": "keep-alive"
}

# Constants for ATM status types (in priority order)
ATM_STATUS_TYPES = [
    "AVAILABLE", 
    "WARNING", 
    "WOUNDED",
    "ZOMBIE",  # Using ZOMBIE as per internal network API
    "OUT_OF_SERVICE"
]

# Status mapping for consistency between API and display
STATUS_MAPPING = {
    "ZOMBIE": "ZOMBIE",  # Keep ZOMBIE as is for internal network
    "OFFLINE": "ZOMBIE"  # Map OFFLINE to ZOMBIE if needed
}

class ATMDetailsRetriever:
    """Main class for handling ATM details retrieval"""
    
    def __init__(self, demo_mode: bool = False, status_types: Optional[List[str]] = None):
        """
        Initialize the retriever
        
        Args:
            demo_mode: Whether to use demo mode (no actual network requests)
            status_types: List of status types to retrieve (default: all status types)
        """
        self.demo_mode = demo_mode
        self.status_types = status_types if status_types else ATM_STATUS_TYPES
        self.session = requests.Session()
        self.user_token = None
        
        # Log timezone info for clarity
        dili_tz = pytz.timezone('Asia/Dili')  # UTC+9
        current_time = datetime.now(dili_tz)
        
        logging.info(f"Initialized ATMDetailsRetriever - Demo: {demo_mode}")
        logging.info(f"Using Dili timezone (UTC+9) for timestamps: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        logging.info(f"Status types to retrieve: {', '.join(self.status_types)}")
    
    def check_connectivity(self, timeout: int = 10) -> bool:
        """Check connectivity to the target system"""
        if self.demo_mode:
            logging.info("Demo mode: Skipping connectivity check")
            return True
            
        try:
            logging.info(f"Testing connectivity to {LOGIN_URL}")
            response = requests.head(LOGIN_URL, timeout=timeout, verify=False)
            logging.info(f"Connectivity successful: HTTP {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Connectivity test failed: {str(e)}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authenticate with the ATM monitoring system
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if self.demo_mode:
            logging.info("Demo mode: Using mock authentication")
            self.user_token = "demo_token_" + str(int(time.time()))
            return True
        
        logging.info("Attempting authentication...")
        
        try:
            response = self.session.post(
                LOGIN_URL,
                json=LOGIN_PAYLOAD,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            login_data = response.json()
            
            # Extract user token using multiple fallback methods
            user_token = None
            
            # Method 1: Direct keys
            for key in ['user_token', 'token']:
                if key in login_data:
                    user_token = login_data[key]
                    logging.info(f"User token extracted with key '{key}'")
                    break
            
            # Method 2: From header field
            if not user_token and 'header' in login_data:
                user_token = login_data['header'].get('user_token')
                if user_token:
                    logging.info("User token extracted from 'header' field")
            
            if user_token:
                self.user_token = user_token
                logging.info(f"Authentication successful - Token length: {len(user_token)} characters")
                return True
            else:
                logging.error("Authentication failed: Unable to extract user token from response")
                logging.debug(f"Available keys in response: {list(login_data.keys())}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Authentication request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            logging.error(f"Authentication response not valid JSON: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during authentication: {str(e)}")
            return False
    
    def refresh_token(self) -> bool:
        """Refresh the authentication token if expired"""
        logging.info("Attempting to refresh authentication token...")
        return self.authenticate()
    
    def fetch_atm_details_for_status(self, status: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch ATM details for a specific status type using the working logic from atm_crawler_complete.py
        
        Args:
            status: ATM status type (e.g., AVAILABLE, WARNING, etc.)
            
        Returns:
            List of terminal dictionaries or None if failed
        """
        if self.demo_mode:
            logging.info(f"Demo mode: Generating sample ATM data for status {status}")
            
            # Return sample data for demo mode
            sample_terminals = [{
                'terminalId': f"{i+80}",
                'location': f"Sample Location {i}",
                'issueStateName': status,
                'fetched_status': status,
                'issueStateCode': 'HARD' if status == 'WOUNDED' else status,
                'brand': 'Nautilus Hyosun',
                'model': 'Monimax 5600'
            } for i in range(3)]  # Generate 3 sample terminals
            return sample_terminals
        
        if not self.user_token:
            logging.error("No authentication token available - please authenticate first")
            return None
        
        dashboard_payload = {
            "header": {
                "logged_user": LOGIN_PAYLOAD["user_name"],
                "user_token": self.user_token
            },
            "body": {
                "parameters_list": [
                    {
                        "parameter_name": "issueStateName",
                        "parameter_values": [status]
                    }
                ]
            }
        }
        
        # Add retry logic for reliability
        max_retries = 3
        retry_count = 0
        success = False
        terminals = []
        
        while retry_count < max_retries and not success:
            try:
                logging.info(f"Requesting terminal dashboard data for {status}... (Attempt {retry_count + 1}/{max_retries})")
                dashboard_res = self.session.put(
                    ATM_DETAILS_URL,
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
                    logging.error(f"Dashboard response for {status} has unexpected format (not a dictionary)")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.error(f"All attempts failed due to unexpected response format for {status}")
                        return None
                    logging.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                # Check if the body field exists in the response
                if "body" not in dashboard_data:
                    logging.error(f"Dashboard response for {status} is missing the 'body' field")
                    logging.error(f"Response keys: {list(dashboard_data.keys())}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.error(f"All attempts failed due to missing 'body' field for {status}")
                        return None
                    logging.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                # Check if the body contains terminals
                body_data = dashboard_data.get("body", [])
                if not body_data:
                    logging.warning(f"No terminals found for status {status}")
                    success = True  # This is not an error, just no data
                    return []
                    
                # Make sure body_data is a list before iterating over it
                if not isinstance(body_data, list):
                    logging.error(f"Body data for {status} is not a list. Type: {type(body_data)}")
                    body_data = []
                    return []
                    
                # Process the terminal data
                for terminal in body_data:
                    # Add the parameter value we searched for
                    terminal['fetched_status'] = status
                    terminals.append(terminal)
                    
                logging.info(f"Found {len(terminals)} terminals with status {status}")
                
                # Step 2: For WARNING and WOUNDED terminals, fetch individual details to get fault data
                if status in ['WARNING', 'WOUNDED'] and terminals:
                    logging.info(f"Fetching detailed fault data for {len(terminals)} {status} terminals...")
                    enhanced_terminals = []
                    
                    for terminal in terminals:
                        terminal_id = terminal.get('terminalId')
                        issue_state_code = terminal.get('issueStateCode', 'HARD')
                        
                        if not terminal_id:
                            logging.warning(f"Skipping terminal with missing ID: {terminal}")
                            enhanced_terminals.append(terminal)
                            continue
                        
                        # Fetch detailed information for this terminal
                        terminal_details = self.fetch_terminal_details(terminal_id, issue_state_code)
                        
                        if terminal_details and 'body' in terminal_details:
                            # Merge the detailed fault data with the original terminal data
                            detail_body = terminal_details['body']
                            if isinstance(detail_body, list) and detail_body:
                                # Use the first item from the details response
                                detailed_info = detail_body[0]
                                
                                # Merge fault information into the original terminal data
                                if 'faultList' in detailed_info:
                                    terminal['faultList'] = detailed_info['faultList']
                                    logging.info(f"Enhanced terminal {terminal_id} with {len(detailed_info['faultList'])} fault records")
                                else:
                                    logging.info(f"No fault data found in details for terminal {terminal_id}")
                                
                                # Merge any other useful fields from detailed response
                                for key, value in detailed_info.items():
                                    if key not in terminal or terminal[key] in [None, '']:
                                        terminal[key] = value
                            else:
                                logging.warning(f"No detail body found for terminal {terminal_id}")
                        else:
                            logging.warning(f"Failed to fetch details for terminal {terminal_id}")
                        
                        enhanced_terminals.append(terminal)
                        # Add a small delay between requests to avoid overwhelming the server
                        time.sleep(0.5)
                    
                    terminals = enhanced_terminals
                    logging.info(f"Enhanced {len(terminals)} {status} terminals with detailed fault data")
                
                success = True
                
                # Update token if a new one was returned
                if "header" in dashboard_data and "user_token" in dashboard_data["header"]:
                    new_token = dashboard_data["header"]["user_token"]
                    if new_token != self.user_token:
                        logging.info("Received new token in response, updating...")
                        self.user_token = new_token
                
            except requests.exceptions.RequestException as ex:
                logging.warning(f"Request failed for {status} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue (401 Unauthorized)
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    logging.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                    if self.refresh_token():
                        self.user_token = self.user_token
                        logging.info("Token refreshed successfully, updating payload with new token")
                        # Update the payload with the new token
                        dashboard_payload["header"]["user_token"] = self.user_token
                        # Don't increment retry count for token refresh
                        logging.info("Retrying request with new token...")
                        continue
                
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error(f"All attempts failed for {status}. Skipping this parameter.")
                    return None
                logging.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
                
            except json.JSONDecodeError as ex:
                logging.error(f"Dashboard response for {status} not valid JSON! (Attempt {retry_count + 1})")
                # Only show raw response if dashboard_res was successfully created
                dashboard_res_text = getattr(locals().get('dashboard_res'), 'text', 'Response object not available')
                if dashboard_res_text != 'Response object not available':
                    logging.error(f"Raw response: {dashboard_res_text[:200]}...")
                else:
                    logging.error("Response object not available for debugging")
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error(f"All JSON parsing attempts failed for {status}. Skipping this parameter.")
                    return None
                logging.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
                
        return terminals
    
    def fetch_terminal_details(self, terminal_id: str, issue_state_code: str = "HARD") -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific terminal ID with fault data
        This implements the two-step approach from the working atm_crawler_complete.py
        
        Args:
            terminal_id: The terminal ID to fetch details for
            issue_state_code: The issue state code (default: HARD)
            
        Returns:
            Terminal data dictionary with fault information or None if failed
        """
        if self.demo_mode:
            logging.info(f"Demo mode: Generating sample terminal details for {terminal_id}")
            # Generate demo fault data
            sample_fault_data = {
                "body": [
                    {
                        "terminalId": terminal_id,
                        "location": f"Sample location for {terminal_id}",
                        "issueStateName": issue_state_code,
                        "serialNumber": f"SN-{terminal_id}",
                        "faultList": [
                            {
                                "creationDate": int(time.time() * 1000),
                                "faultTypeCode": "HARDWARE",
                                "externalFaultId": f"ERR_{terminal_id}",
                                "agentErrorDescription": f"Demo fault for {terminal_id}: Hardware malfunction",
                                "year": str(datetime.now().year),
                                "month": datetime.now().strftime("%m"),
                                "date": datetime.now().strftime("%d")
                            }
                        ]
                    }
                ]
            }
            return sample_fault_data
        
        if not self.user_token:
            logging.error("No authentication token available - please authenticate first")
            return None
        
        # Use the same URL pattern as the working reference implementation
        details_url = f"{ATM_DETAILS_URL}&terminal_id={terminal_id}"
        
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
        max_retries = 3
        retry_count = 0
        success = False
        terminal_data = None
        
        while retry_count < max_retries and not success:
            try:
                logging.info(f"Requesting details for terminal {terminal_id}... (Attempt {retry_count + 1}/{max_retries})")
                details_res = self.session.put(
                    details_url, 
                    json=details_payload, 
                    headers=COMMON_HEADERS, 
                    verify=False, 
                    timeout=30
                )
                details_res.raise_for_status()
                
                # Try to parse JSON
                details_data = details_res.json()
                
                # Check if the response has the expected structure
                if not isinstance(details_data, dict):
                    logging.error(f"Details response for terminal {terminal_id} has unexpected format (not a dictionary)")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.error(f"All attempts failed due to unexpected response format for terminal {terminal_id}")
                        return None
                    logging.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                # Check if the body field exists in the response
                if "body" not in details_data:
                    logging.error(f"Details response for terminal {terminal_id} is missing the 'body' field")
                    logging.error(f"Response keys: {list(details_data.keys())}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.error(f"All attempts failed due to missing 'body' field for terminal {terminal_id}")
                        return None
                    logging.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                success = True
                terminal_data = details_data
                logging.info(f"Details fetch successful for terminal {terminal_id} on attempt {retry_count + 1}")
                
                # Update token if a new one was returned
                if "header" in details_data and "user_token" in details_data["header"]:
                    new_token = details_data["header"]["user_token"]
                    if new_token != self.user_token:
                        logging.info("Received new token in response, updating...")
                        self.user_token = new_token
                
            except requests.exceptions.RequestException as ex:
                logging.warning(f"Request failed for terminal {terminal_id} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue (401 Unauthorized)
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    logging.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                    if self.refresh_token():
                        logging.info("Token refreshed successfully, updating payload with new token")
                        # Update the payload with the new token
                        details_payload["header"]["user_token"] = self.user_token
                        # Don't increment retry count for token refresh
                        logging.info("Retrying request with new token...")
                        continue
                
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error(f"All attempts failed for terminal {terminal_id}. Skipping this terminal.")
                    return None
                logging.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
                
            except json.JSONDecodeError as ex:
                logging.error(f"Details response for terminal {terminal_id} not valid JSON! (Attempt {retry_count + 1})")
                # Only show raw response if details_res was successfully created
                details_res_text = getattr(locals().get('details_res'), 'text', 'Response object not available')
                if details_res_text != 'Response object not available':
                    logging.error(f"Raw response: {details_res_text[:200]}...")
                else:
                    logging.error("Response object not available for debugging")
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error(f"All JSON parsing attempts failed for terminal {terminal_id}. Skipping this terminal.")
                    return None
                logging.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
                
        return terminal_data
    
    def process_atm_data(self, raw_terminals: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
        """
        Process raw ATM details data into structured format
        
        Args:
            raw_terminals: List of terminal dictionaries from API response
            status: The status type for this data
            
        Returns:
            List of processed ATM records
        """
        processed_records = []
        dili_tz = pytz.timezone('Asia/Dili')  # Asia/Dili is UTC+9 for Timor-Leste
        current_time = datetime.now(dili_tz)
        
        if not raw_terminals:
            logging.warning(f"No raw terminals provided for processing for status {status}")
            return []
        
        logging.info(f"Processing {len(raw_terminals)} ATMs with status {status}")
        
        for terminal in raw_terminals:
            atm_id = terminal.get("terminalId", "Unknown")
            
            # Convert timestamps to readable format if available
            last_comm_date = None
            if "statusDate" in terminal and terminal["statusDate"]:
                try:
                    # Convert milliseconds timestamp to datetime
                    last_comm_date = datetime.fromtimestamp(terminal["statusDate"] / 1000.0)
                    last_comm_date = last_comm_date.astimezone(dili_tz)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Failed to parse timestamp for ATM {atm_id}: {e}")
            
            # Process fault list data if available
            fault_data = []
            if terminal.get("faultList") and isinstance(terminal["faultList"], list):
                for fault in terminal["faultList"]:
                    fault_info = {}
                    
                    # Extract and convert creation date from unix timestamp to Dili time (UTC+9)
                    if fault.get("creationDate"):
                        try:
                            # Convert unix timestamp (milliseconds) to datetime
                            creation_timestamp = fault["creationDate"] / 1000.0  # Convert from milliseconds
                            creation_utc = datetime.fromtimestamp(creation_timestamp, tz=pytz.UTC)
                            creation_dili = creation_utc.astimezone(dili_tz)
                            fault_info["creation_date"] = creation_dili.isoformat()
                            fault_info["creation_date_timestamp"] = creation_dili
                        except Exception as e:
                            logging.warning(f"Failed to parse fault creation date: {fault.get('creationDate')} - {str(e)}")
                            fault_info["creation_date"] = None
                            fault_info["creation_date_timestamp"] = None
                    else:
                        fault_info["creation_date"] = None
                        fault_info["creation_date_timestamp"] = None
                    
                    # Extract external fault ID (error code)
                    fault_info["external_fault_id"] = fault.get("externalFaultId", "")
                    
                    # Extract agent error description
                    fault_info["agent_error_description"] = fault.get("agentErrorDescription", "")
                    
                    # Keep other fault data for reference
                    fault_info["raw_fault_data"] = fault
                    
                    fault_data.append(fault_info)
            
            # Process each ATM data
            record = {
                'unique_request_id': str(uuid.uuid4()),
                'request_timestamp': current_time,
                'terminal_id': atm_id,
                'external_id': terminal.get("externalId", ""),
                'terminal_name': f"{terminal.get('brand', '')} {terminal.get('model', '')}".strip(),
                'location': terminal.get("location", ""),
                'city': terminal.get("cityName", ""),
                'region': terminal.get("geoLocation", ""),
                'status': terminal.get("issueStateName", status),
                'status_code': terminal.get("issueStateCode", ""),
                'bank': terminal.get("bank", ""),
                'last_updated': last_comm_date.isoformat() if last_comm_date else "",
                'last_updated_timestamp': last_comm_date,  # Keep datetime object for database operations
                'serial_number': terminal.get("serialNumber", ""),
                'business_id': terminal.get("businessId", ""),
                'free_disk_space': terminal.get("freeDiskSpace", ""),
                'location_type': terminal.get("locationType", ""),
                'has_advertising': terminal.get("hasAdvertising", False),
                'issue_type': terminal.get("issueTypeName", ""),
                'issue_state': terminal.get("issueStateName", ""),
                'contact_name': terminal.get("contactDisplayName", ""),
                # Add fault list information
                'fault_list': fault_data,
                'fault_count': len(fault_data),
                'raw_data': terminal  # Keep raw data for reference
            }
            
            processed_records.append(record)
            logging.debug(f"Processed ATM {atm_id}: {record['terminal_name']} ({record['status']})")
        
        logging.info(f"Successfully processed {len(processed_records)} ATM records with status {status}")
        return processed_records
    
    def save_to_database(self, processed_data: List[Dict[str, Any]]) -> bool:
        """
        Save processed ATM details data to database
        
        Args:
            processed_data: List of processed ATM records
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not DB_AVAILABLE:
            logging.warning("Database not available - skipping database save")
            return False
        
        if not processed_data:
            logging.warning("No processed data to save")
            return False
        
        logging.info(f"Saving {len(processed_data)} ATM records to database...")
        
        try:
            db_connection = get_connection()
            if not db_connection:
                logging.error("Failed to get database connection")
                return False
                
            # Use store_atm_data_in_db function to store in database
            terminals_added, terminals_updated, status_records_added = store_atm_data_in_db(
                db_connection, processed_data
            )
            
            db_connection.close()
            
            logging.info(f"Database updated: {terminals_added} terminals added, "
                        f"{terminals_updated} terminals updated, "
                        f"{status_records_added} status records added")
            return True
            
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return False
    
    def retrieve_all_atm_details(self, save_to_db: bool = False) -> Tuple[bool, Dict[str, List[Dict[str, Any]]]]:
        """
        Retrieve ATM details for all specified status types
        
        Args:
            save_to_db: Whether to save processed data to database
            
        Returns:
            Tuple of (success: bool, dict of status type to list of ATM records)
        """
        logging.info("=" * 80)
        logging.info("STARTING ATM DETAILS RETRIEVAL")
        logging.info("=" * 80)
        
        # Step 1: Check connectivity (unless demo mode)
        if not self.demo_mode:
            if not self.check_connectivity():
                logging.error("Connectivity check failed - aborting")
                return False, {}
        
        # Step 2: Authenticate
        if not self.authenticate():
            logging.error("Authentication failed - aborting")
            return False, {}
        
        # Step 3: Fetch and process ATM details for each status type
        all_atm_data = {}
        success_count = 0
        
        for status in self.status_types:
            logging.info(f"Retrieving ATM details for status: {status}")
            
            # Fetch raw data
            raw_terminals = self.fetch_atm_details_for_status(status)
            if not raw_terminals:
                logging.error(f"Failed to retrieve ATM details for status {status}")
                continue
            
            # Process the data (raw_terminals is already a list)
            processed_data = self.process_atm_data(raw_terminals, status)
            if processed_data:
                all_atm_data[status] = processed_data
                success_count += 1
                
                # Save to database if requested
                if save_to_db:
                    save_success = self.save_to_database(processed_data)
                    if save_success:
                        logging.info(f"Data for status {status} successfully saved to database")
                    else:
                        logging.warning(f"Database save failed for status {status}")
        
        # Check if we got any data at all
        if not all_atm_data:
            logging.error("Failed to retrieve any ATM details")
            return False, {}
        
        logging.info("=" * 80)
        logging.info(f"ATM DETAILS RETRIEVAL COMPLETED: {success_count}/{len(self.status_types)} status types successful")
        logging.info("=" * 80)
        
        return True, all_atm_data


def create_tables_if_not_exist(cursor):
    """Create necessary tables if they don't exist"""
    
    # Create terminals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atm_terminals (
        terminal_id VARCHAR(20) PRIMARY KEY,
        terminal_name VARCHAR(255),
        region VARCHAR(100),
        city VARCHAR(100),
        latitude DECIMAL(10, 6),
        longitude DECIMAL(10, 6),
        last_status VARCHAR(50),
        last_updated TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create status updates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atm_status_updates (
        update_id SERIAL PRIMARY KEY,
        terminal_id VARCHAR(20) REFERENCES atm_terminals(terminal_id),
        status VARCHAR(50),
        issue_type VARCHAR(100),
        issue_state_name VARCHAR(100),
        contact_name VARCHAR(255),
        updated_at TIMESTAMP WITH TIME ZONE,
        recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create indexes for performance
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_atm_terminals_region 
    ON atm_terminals(region)
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_atm_status_updates_terminal 
    ON atm_status_updates(terminal_id)
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_atm_status_updates_status 
    ON atm_status_updates(status)
    """)


def upsert_terminal_record(cursor, atm):
    """Insert or update a terminal record"""
    terminal_id = atm.get('terminal_id')
    terminal_name = atm.get('terminal_name')
    region = atm.get('region')
    city = atm.get('city', region)  # Use region as fallback if city not available
    status = atm.get('status')
    last_updated = atm.get('last_updated_timestamp')
    
    # Extract location data
    lat = None
    long = None
    if 'location' in atm and atm['location']:
        lat = atm['location'].get('latitude')
        long = atm['location'].get('longitude')
    
    # Check if terminal already exists
    cursor.execute(
        "SELECT terminal_id FROM atm_terminals WHERE terminal_id = %s",
        (terminal_id,)
    )
    terminal_exists = cursor.fetchone() is not None
    
    if terminal_exists:
        # Update existing terminal
        cursor.execute("""
        UPDATE atm_terminals 
        SET terminal_name = %s,
            region = %s,
            city = %s,
            latitude = %s,
            longitude = %s,
            last_status = %s,
            last_updated = %s
        WHERE terminal_id = %s
        """, (
            terminal_name, region, city, lat, long, 
            status, last_updated, terminal_id
        ))
        return 0, 1  # 0 added, 1 updated
    else:
        # Insert new terminal
        cursor.execute("""
        INSERT INTO atm_terminals (
            terminal_id, terminal_name, region, city,
            latitude, longitude, last_status, last_updated
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            terminal_id, terminal_name, region, city,
            lat, long, status, last_updated
        ))
        return 1, 0  # 1 added, 0 updated


def add_status_update_record(cursor, atm):
    """Add a status update record"""
    terminal_id = atm.get('terminal_id')
    status = atm.get('status')
    issue_type = atm.get('issue_type')
    issue_state = atm.get('issue_state')
    contact_name = atm.get('contact_name')
    updated_at = atm.get('last_updated_timestamp')
    
    # Skip if no status or timestamp
    if not status or not updated_at:
        return False
        
    # Insert status update record
    cursor.execute("""
    INSERT INTO atm_status_updates (
        terminal_id, status, issue_type, issue_state_name,
        contact_name, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        terminal_id, status, issue_type, issue_state,
        contact_name, updated_at
    ))
    
    return True


def store_atm_data_in_db(db_connection, atm_data):
    """
    Store ATM details in the database according to our schema
    
    Args:
        db_connection: Database connection object
        atm_data: List of processed ATM data objects
        
    Returns:
        Tuple of (terminals_added, terminals_updated, status_records_added)
    """
    if not atm_data:
        logging.warning("No ATM data to store in database")
        return 0, 0, 0
    
    cursor = db_connection.cursor()
    
    terminals_added = 0
    terminals_updated = 0
    status_records_added = 0
    
    try:
        # First ensure tables exist (idempotent operation)
        create_tables_if_not_exist(cursor)
        
        # Process each ATM terminal
        for atm in atm_data:
            terminal_id = atm.get('terminal_id')
            if not terminal_id:
                logging.warning(f"Skipping ATM record without terminal_id: {atm}")
                continue
                
            # Attempt to insert or update terminal record
            added, updated = upsert_terminal_record(cursor, atm)
            terminals_added += added
            terminals_updated += updated
            
            # Add status update record
            if add_status_update_record(cursor, atm):
                status_records_added += 1
        
        # Commit the transaction
        db_connection.commit()
        
        logging.info(f"Database updated: {terminals_added} terminals added, "
                    f"{terminals_updated} terminals updated, "
                    f"{status_records_added} status records added")
        
        return terminals_added, terminals_updated, status_records_added
        
    except Exception as e:
        db_connection.rollback()
        logging.error(f"Database error: {str(e)}")
        return 0, 0, 0


def display_atm_data(all_atm_data):
    """Display the processed results in a formatted way"""
    if not all_atm_data:
        print("No data to display")
        return
    
    total_atms = sum(len(atms) for atms in all_atm_data.values())
    
    print("\n" + "=" * 110)
    print("ATM DETAILS DATA")
    print("=" * 110)
    
    for status, atm_list in all_atm_data.items():
        print(f"\n🔹 STATUS: {status} - {len(atm_list)} ATMs")
        print("-" * 110)
        
        if not atm_list:
            print("  No ATMs with this status")
            continue
        
        print(f"{'ATM ID':<8} {'External':<8} {'Bank':<8} {'Model':<20} {'Location':<30} {'City':<15} {'Region':<6} {'Last Comm':<20} {'Faults':<8}")
        print("-" * 120)
        
        for atm in atm_list[:5]:  # Show first 5 ATMs for each status to keep output manageable
            fault_count = atm.get('fault_count', 0)
            fault_display = f"{fault_count}" if fault_count > 0 else "-"
            
            print(f"{atm['terminal_id']:<8} {atm.get('external_id', '')[:6]:<8} {atm.get('bank', '')[:6]:<8} {atm.get('terminal_name', '')[:18]:<20} "
                  f"{atm.get('location_str', atm.get('location', ''))[:28]:<30} {atm.get('city', '')[:13]:<15} {atm.get('region', ''):<6} "
                  f"{atm.get('last_updated', '')[:19] if atm.get('last_updated') else 'N/A':<20} {fault_display:<8}")
            
            # Show fault details if available
            if atm.get('fault_list') and isinstance(atm['fault_list'], list):
                for idx, fault in enumerate(atm['fault_list'][:2]):  # Show up to 2 faults per ATM
                    fault_desc = fault.get('agent_error_description', 'No description')[:50]
                    fault_id = fault.get('external_fault_id', 'N/A')
                    fault_date = fault.get('creation_date', 'N/A')[:19] if fault.get('creation_date') else 'N/A'
                    print(f"          └─ Fault {idx+1}: [{fault_id}] {fault_desc} ({fault_date})")
        
        if len(atm_list) > 5:
            print(f"... and {len(atm_list) - 5} more ATMs with status {status}")
    
    print("\n" + "-" * 120)
    print(f"Total ATMs processed: {total_atms}")
    print(f"Status types: {', '.join(sorted(all_atm_data.keys()))}")


def save_to_json(all_atm_data, filename=None):
    """Save processed ATM details to JSON file"""
    if isinstance(all_atm_data, list):
        # Called with a simple list of ATM data, not grouped by status
        return save_atm_list_to_json(all_atm_data, filename)
        
    dili_tz = pytz.timezone('Asia/Dili')  # Asia/Dili is UTC+9 for Timor-Leste
    current_time = datetime.now(dili_tz)
    if not filename:
        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        filename = f"atm_details_{timestamp}.json"
    
    # Prepare data for JSON serialization
    total_atms = sum(len(atms) for atms in all_atm_data.values())
    
    # Convert datetime objects to strings
    json_data = {}
    for status, atm_list in all_atm_data.items():
        json_data[status] = []
        for atm in atm_list:
            atm_copy = {}
            for key, value in atm.items():
                if key == 'raw_data' or key == 'last_updated_timestamp':
                    continue  # Skip these fields
                elif isinstance(value, datetime):
                    atm_copy[key] = value.isoformat()
                else:
                    atm_copy[key] = value
            json_data[status].append(atm_copy)
    
    # Create the full JSON structure
    output_data = {
        "retrieval_timestamp": current_time.isoformat(),
        "total_atms": total_atms,
        "status_summary": {status: len(atms) for status, atms in all_atm_data.items()},
        "atm_data": json_data
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logging.info(f"Data saved to JSON file: {filename}")
    return filename


def save_comprehensive_response_to_json(comprehensive_response, output_path=None):
    """
    Save comprehensive ATM response data to JSON file with proper structure
    
    Args:
        comprehensive_response: Full response dict from fetch_atm_details_for_status
        output_path: Optional custom output path
        
    Returns:
        Path to saved JSON file
    """
    try:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"atm_comprehensive_response_{timestamp}.json"
        
        # Ensure we're in the correct directory
        if not os.path.isabs(output_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(script_dir, output_path)
        
        # Create enhanced structure for comprehensive response
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now(pytz.timezone('Asia/Dili')).isoformat(),
                "data_source": "ATM Management System (172.31.1.46)",
                "export_type": "comprehensive_response",
                "data_retrieval_timestamp": comprehensive_response.get("retrieval_timestamp"),
                "total_atms_retrieved": comprehensive_response.get("total_atms", 0),
                "status_types_processed": comprehensive_response.get("processing_order", []),
                "requested_statuses": comprehensive_response.get("requested_statuses", [])
            },
            "summary": {
                "status_counts": comprehensive_response.get("status_summary", {}),
                "total_atms": comprehensive_response.get("total_atms", 0),
                "processing_notes": comprehensive_response.get("response_metadata", {}).get("processing_notes", [])
            },
            "atm_data_by_status": comprehensive_response.get("atm_data", {}),
            "response_metadata": comprehensive_response.get("response_metadata", {})
        }
        
        # Save to JSON file with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        logging.info(f"Comprehensive ATM response data saved to {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"Failed to save comprehensive response to JSON: {str(e)}")
        return None


def save_atm_list_to_json(atm_data, output_path=None):
    """
    Save a list of ATM data to JSON file
    
    Args:
        atm_data: List of processed ATM data objects
        output_path: Optional path to save to, otherwise uses default with timestamp
        
    Returns:
        Path to the saved JSON file
    """
    if not atm_data:
        logging.warning("No ATM data to save to JSON")
        return None
        
    # Create a serializable version (remove datetime objects)
    serializable_data = []
    for atm in atm_data:
        # Create a copy without the raw_data field to make the output more readable
        atm_copy = {k: v for k, v in atm.items() if k != 'raw_data' and k != 'last_updated_timestamp'}
        
        # Convert datetime objects to ISO format strings
        for key, value in atm_copy.items():
            if isinstance(value, datetime):
                atm_copy[key] = value.isoformat()
                
        serializable_data.append(atm_copy)
    
    # Generate filename with timestamp if not provided
    if not output_path:
        dili_tz = pytz.timezone('Asia/Dili')
        timestamp = datetime.now(dili_tz).strftime("%Y%m%d_%H%M%S")
        output_path = f"atm_details_{timestamp}.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                {"atm_data": serializable_data, 
                 "timestamp": datetime.now(pytz.timezone('Asia/Dili')).isoformat(),
                 "count": len(serializable_data)
                }, 
                f, 
                indent=2,
                default=str
            )
        logging.info(f"ATM data saved to {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Failed to save JSON: {str(e)}")
        return None


def get_demo_data(status_types=None):
    """
    Generate demo data for testing without API access
    
    Args:
        status_types: List of status types to include or None for all
        
    Returns:
        List of simulated ATM details
    """
    dili_tz = pytz.timezone('Asia/Dili')
    current_time = datetime.now(dili_tz)
    
    # Define possible statuses with their properties (in correct order)
    status_options = {
        "AVAILABLE": {
            "issueTypeName": None,
            "issueStateName": "AVAILABLE",
            "issueStateCode": "NORMAL"
        },
        "WARNING": {
            "issueTypeName": "SERVICE_NEEDED",
            "issueStateName": "WARNING",
            "issueStateCode": "WARN"
        },
        "WOUNDED": {
            "issueTypeName": "HARDWARE_ISSUE",
            "issueStateName": "WOUNDED",
            "issueStateCode": "HARD"
        },
        "ZOMBIE": {  # Using ZOMBIE for internal network compatibility
            "issueTypeName": "NETWORK_ISSUE",
            "issueStateName": "ZOMBIE",
            "issueStateCode": "ZOMBIE"
        },
        "OUT_OF_SERVICE": {
            "issueTypeName": "POWER_ISSUE",
            "issueStateName": "OUT_OF_SERVICE",
            "issueStateCode": "CASH"
        }
    }
    
    # Use requested statuses or all if none specified
    if status_types:
        # Filter to only include requested status types
        status_options = {k: v for k, v in status_options.items() if k in status_types}
    
    # Generate random ATM data
    atm_data = []
    regions = ["Dili", "Baucau", "Bobonaro", "Covalima", "Lautem", "Liquiçá"]
    banks = ["BNCTL", "BNU", "BRI", "Mandiri"]
    models = ["Nautilus Hyosun", "NCR SelfServ", "Diebold 4900", "Wincor ProCash"]
    
    # Generate 5 ATMs for each status
    for status, properties in status_options.items():
        for i in range(1, 6):
            region = random.choice(regions)
            bank = random.choice(banks)
            model = random.choice(models)
            terminal_id = f"ATM{random.randint(1000, 9999)}"
            external_id = f"TL{random.randint(100, 999)}"
            
            # Generate lat/long within Timor-Leste bounds approximately
            lat = random.uniform(-9.5, -8.1) 
            long = random.uniform(124.0, 127.3)
            
            # Random time in the last 24 hours
            update_time = current_time - timedelta(hours=random.randint(0, 24))
            
            # Generate sample fault list for demo (only for non-AVAILABLE statuses)
            fault_list = []
            if status != "AVAILABLE" and random.choice([True, False]):  # 50% chance of having faults
                for fault_idx in range(random.randint(1, 3)):  # 1-3 faults
                    fault_creation_time = update_time - timedelta(minutes=random.randint(0, 120))
                    fault_creation_timestamp = int(fault_creation_time.timestamp() * 1000)  # Unix timestamp in milliseconds
                    
                    # Sample fault types and component types
                    fault_types = ["HARDWARE", "SOFTWARE", "NETWORK", "CASH", "RECEIPT", "CARD_READER"]
                    component_types = ["DISPENSER", "READER", "PRINTER", "NETWORK_MODULE", "DEPOSIT_MODULE", "SENSOR"]
                    issue_states = ["ERROR", "WARNING", "CRITICAL", "MAINTENANCE"]
                    
                    fault_list.append({
                        "creationDate": fault_creation_timestamp,
                        "faultTypeCode": random.choice(fault_types),
                        "componentTypeCode": random.choice(component_types),  # Fixed field name to match API
                        "issueStateName": random.choice(issue_states),
                        "year": str(fault_creation_time.year),
                        "month": str(fault_creation_time.month).zfill(2),
                        "date": str(fault_creation_time.day).zfill(2)
                    })
            
            atm = {
                "terminalId": terminal_id,
                "externalId": external_id,
                "terminalCode": external_id,
                "terminalName": f"{model} {region} {i}",
                "bank": bank,
                "cityName": region,
                "city": region,
                "geoLocation": region,
                "location": f"{region} MAIN ROAD, {random.randint(1, 100)}",
                "status": status,
                "issueStateName": properties["issueStateName"],
                "issueStateCode": properties["issueStateCode"],
                "lastUpdate": update_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "geolocation": {
                    "latitude": str(lat),
                    "longitude": str(long)
                },
                "issueTypeName": properties["issueTypeName"],
                "contactDisplayName": "ATM Service" if properties["issueTypeName"] else None,
                "serialNumber": f"SN{random.randint(10000, 99999)}",
                "businessId": f"BIZ{random.randint(100, 999)}",
                "faultList": fault_list  # Add fault list to demo data
            }
            
            atm_data.append(atm)
    
    logging.info(f"Generated {len(atm_data)} demo ATM records")
    return atm_data


def process_atm_data(raw_data):
    """
    Process raw ATM data into a structured format
    
    Args:
        raw_data: List of ATM data objects from the API
        
    Returns:
        List of processed ATM objects
    """
    processed_data = []
    dili_tz = pytz.timezone('Asia/Dili')  # UTC+9
    
    for atm in raw_data:
        # Process timestamps if available
        last_updated = None
        if atm.get("lastUpdate"):
            # Convert timestamp to Dili timezone (UTC+9)
            try:
                # Parse timestamp (assuming UTC format from API)
                last_updated_utc = datetime.strptime(
                    atm["lastUpdate"], "%Y-%m-%dT%H:%M:%S.%fZ"
                ).replace(tzinfo=pytz.UTC)
                
                # Convert to Dili timezone
                last_updated = last_updated_utc.astimezone(dili_tz)
            except Exception as e:
                logging.warning(f"Failed to parse timestamp: {atm.get('lastUpdate')} - {str(e)}")
        
        # Extract location data if available
        location = {}
        if atm.get("city"):
            location["city"] = atm["city"]
        if atm.get("geolocation"):
            try:
                geo = atm["geolocation"]
                location["latitude"] = float(geo["latitude"])
                location["longitude"] = float(geo["longitude"])
            except Exception as e:
                logging.warning(f"Failed to parse geolocation for ATM {atm.get('terminalId') or atm.get('terminalCode')}: {str(e)}")
        
        # Process fault list data if available
        fault_data = []
        if atm.get("faultList") and isinstance(atm["faultList"], list):
            for fault in atm["faultList"]:
                fault_info = {}
                
                # Extract and convert creation date from unix timestamp to Dili time (UTC+9)
                creation_dili = None
                if fault.get("creationDate"):
                    try:
                        # Convert unix timestamp (milliseconds) to datetime
                        creation_timestamp = fault["creationDate"] / 1000.0  # Convert from milliseconds
                        creation_utc = datetime.fromtimestamp(creation_timestamp, tz=pytz.UTC)
                        creation_dili = creation_utc.astimezone(dili_tz)
                        fault_info["creation_date"] = creation_dili.isoformat()
                        fault_info["creation_date_timestamp"] = creation_dili
                    except Exception as e:
                        logging.warning(f"Failed to parse fault creation date: {fault.get('creationDate')} - {str(e)}")
                        fault_info["creation_date"] = None
                        fault_info["creation_date_timestamp"] = None
                else:
                    fault_info["creation_date"] = None
                    fault_info["creation_date_timestamp"] = None
                
                # Extract fault type code
                fault_info["fault_type_code"] = fault.get("faultTypeCode", "")
                
                # Extract component type code (using correct field name from API)
                fault_info["component_type_code"] = fault.get("componentTypeCode", "")
                
                # Extract issue state name
                fault_info["issue_state_name"] = fault.get("issueStateName", "")
                
                # Extract year, month, date from API response or from parsed creation date
                if fault.get("year") and fault.get("month") and fault.get("day"):
                    # Use data directly from API response
                    fault_info["year"] = str(fault.get("year", ""))
                    fault_info["month"] = str(fault.get("month", "")).zfill(2) if str(fault.get("month", "")).isdigit() else str(fault.get("month", ""))
                    fault_info["date"] = str(fault.get("day", "")).zfill(2) if str(fault.get("day", "")).isdigit() else str(fault.get("day", ""))
                elif creation_dili:
                    # Extract from parsed creation date if API data not available
                    fault_info["year"] = str(creation_dili.year)
                    fault_info["month"] = str(creation_dili.month).zfill(2)  # Zero-pad to 2 digits
                    fault_info["date"] = str(creation_dili.day).zfill(2)    # Zero-pad to 2 digits
                else:
                    fault_info["year"] = ""
                    fault_info["month"] = ""
                    fault_info["date"] = ""
                
                # Extract external fault ID (error code)
                fault_info["external_fault_id"] = fault.get("externalFaultId", "")
                
                # Extract agent error description
                fault_info["agent_error_description"] = fault.get("agentErrorDescription", "")
                
                # Extract additional fields from the API response
                fault_info["fault_id"] = fault.get("faultId", "")
                fault_info["service_request_id"] = fault.get("serviceRequestId", "")
                fault_info["fault_state"] = fault.get("faultState", "")
                fault_info["business_code"] = fault.get("businessCode", "")
                fault_info["technical_code"] = fault.get("technicalCode", "")
                fault_info["fault_origin"] = fault.get("faultOrigin", "")
                fault_info["terminal_model_name"] = fault.get("terminalModelName", "")
                
                # Keep other fault data for reference
                fault_info["raw_fault_data"] = fault
                
                fault_data.append(fault_info)
        
        # Create structured ATM object
        processed_atm = {
            "terminal_id": atm.get("terminalId") or atm.get("terminalCode"),
            "terminal_name": atm.get("terminalName"),
            "external_id": atm.get("externalId", ""),
            "bank": atm.get("bank", ""),
            "region": atm.get("city") or atm.get("geoLocation") or "",
            "city": atm.get("cityName") or atm.get("city") or "",
            "location": location,
            "location_str": atm.get("location", ""),
            "status": atm.get("status") or atm.get("issueStateName", ""),
            "status_code": atm.get("issueStateCode", ""),
            "last_updated": last_updated.isoformat() if last_updated else None,
            "last_updated_timestamp": last_updated,  # Keep datetime object for database operations
            "issue_type": atm.get("issueTypeName"),
            "issue_state": atm.get("issueStateName") or atm.get("status"),
            "contact_name": atm.get("contactDisplayName"),
            "serial_number": atm.get("serialNumber", ""),
            "business_id": atm.get("businessId", ""),
            # Add fault list information
            "fault_list": fault_data,
            "fault_count": len(fault_data),
            # Include additional fields as needed
            "raw_data": atm  # Keep raw data for reference
        }
        
        processed_data.append(processed_atm)
    
    return processed_data





def fetch_atm_details_for_status(session, status_types=None):
    """
    Fetch ATM details for specified status types or all if none specified
    Returns data in the correct order with comprehensive response information
    
    Args:
        session: Requests session with authentication
        status_types: List of status types (e.g., ["AVAILABLE", "WOUNDED"]) or None for all
    
    Returns:
        Dict containing ordered ATM details by status with full response metadata
    """
    logging.info(f"Fetching ATM details for status(es): {status_types or 'ALL'}")
    
    # Get user_token from session (should be stored after authentication)
    if not hasattr(session, 'user_token'):
        logging.error("No user_token found in session. Authentication may have failed.")
        return {}
    
    user_token = session.user_token
    
    # Define the correct order of status types to process
    ordered_status_types = ATM_STATUS_TYPES.copy()
    
    # If specific status types requested, filter and maintain order
    if status_types:
        # Maintain the original order of ATM_STATUS_TYPES but only include requested ones
        ordered_status_types = [status for status in ordered_status_types if status in status_types]
        logging.info(f"Processing status types in order: {ordered_status_types}")
    else:
        logging.info(f"Processing all status types in order: {ordered_status_types}")
    
    # Comprehensive response structure
    comprehensive_response = {
        "retrieval_timestamp": datetime.now(pytz.timezone('Asia/Dili')).isoformat(),
        "requested_statuses": status_types or ordered_status_types,
        "processing_order": ordered_status_types,
        "total_atms": 0,
        "status_summary": {},
        "atm_data": {},
        "response_metadata": {
            "source": "172.31.1.46",
            "api_endpoint": ATM_DETAILS_URL,
            "authentication_user": LOGIN_PAYLOAD["user_name"],
            "processing_notes": []
        }
    }
    
    # Process each status type in the correct order
    for status in ordered_status_types:
        logging.info(f"Processing status: {status}")
        
        # Use status as-is for internal network (ZOMBIE should work directly)
        api_status = STATUS_MAPPING.get(status, status)
        
        terminals = fetch_terminals_for_single_status(session, user_token, api_status)
        
        if terminals:
            # Add the fetched status to each terminal record
            for terminal in terminals:
                terminal['fetched_status'] = status
                terminal['api_status_used'] = api_status
                terminal['processing_order'] = ordered_status_types.index(status) + 1
            
            comprehensive_response["atm_data"][status] = terminals
            comprehensive_response["status_summary"][status] = len(terminals)
            comprehensive_response["total_atms"] += len(terminals)
            
            logging.info(f"Added {len(terminals)} terminals with status {status}")
            comprehensive_response["response_metadata"]["processing_notes"].append(
                f"Status {status}: {len(terminals)} terminals retrieved successfully"
            )
        else:
            # Include empty result in response for completeness
            comprehensive_response["atm_data"][status] = []
            comprehensive_response["status_summary"][status] = 0
            
            logging.warning(f"No terminals found with status {status}")
            comprehensive_response["response_metadata"]["processing_notes"].append(
                f"Status {status}: No terminals found or retrieval failed"
            )
    
    # Add final processing summary
    comprehensive_response["response_metadata"]["processing_notes"].append(
        f"Total processing completed: {comprehensive_response['total_atms']} terminals across {len(ordered_status_types)} status types"
    )
    
    # Log comprehensive summary
    logging.info("=" * 80)
    logging.info("ATM DETAILS RETRIEVAL SUMMARY")
    logging.info("=" * 80)
    logging.info(f"Total ATMs retrieved: {comprehensive_response['total_atms']}")
    for status, count in comprehensive_response["status_summary"].items():
        logging.info(f"  {status}: {count} ATMs")
    logging.info("=" * 80)
    
    return comprehensive_response


def fetch_terminals_for_single_status(session, user_token, param_value):
    """
    Fetch terminals for a single status using the working crawler payload structure
    """
    # Use the exact payload structure from working crawler
    payload = {
        "header": {
            "logged_user": LOGIN_PAYLOAD["user_name"],
            "user_token": user_token
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
    
    # Use the working crawler approach with retry logic
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Making dashboard request for {param_value} (attempt {attempt + 1}/{max_retries})")
            logging.info(f"Request URL: {ATM_DETAILS_URL}")
            logging.info(f"Request headers: {COMMON_HEADERS}")
            
            # Log payload in formatted JSON for debugging
            import json as json_module
            formatted_payload = json_module.dumps(payload, indent=2, ensure_ascii=False)
            logging.info(f"=== REQUEST PAYLOAD FOR {param_value} ===")
            logging.info(formatted_payload)
            logging.info("=== END REQUEST PAYLOAD ===")
            
            # Use PUT method and ATM_DETAILS_URL like the working crawler
            response = session.put(
                ATM_DETAILS_URL,
                json=payload,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=30
            )
            
            logging.info(f"Dashboard response status: {response.status_code}")
            logging.info(f"Response headers: {dict(response.headers)}")
            
            # Handle different status codes with detailed logging
            if response.status_code == 401:
                logging.warning("Unauthorized response - token may have expired")
                logging.warning(f"Response body: {response.text[:500]}")
                if attempt < max_retries - 1:
                    logging.info("Attempting to refresh authentication...")
                    # Re-authenticate and get new token
                    auth_result = authenticate(session)
                    if auth_result:
                        session.user_token = auth_result
                        # Update payload with new token
                        payload["header"]["user_token"] = auth_result
                        logging.info("Re-authentication successful, retrying request...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logging.error("Failed to re-authenticate")
                        continue
                else:
                    logging.error("Failed to authenticate after all retries")
                    return []
            
            elif response.status_code == 400:
                logging.error(f"Bad Request (400) for {param_value}")
                logging.error(f"Response body: {response.text}")
                
                # Try to parse error message
                try:
                    error_data = response.json()
                    formatted_error = json_module.dumps(error_data, indent=2, ensure_ascii=False)
                    logging.error(f"=== ERROR RESPONSE JSON ===")
                    logging.error(formatted_error)
                    logging.error("=== END ERROR RESPONSE ===")
                except:
                    logging.error("Could not parse error response as JSON")
                
                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return []
            
            elif response.status_code == 405:
                logging.error(f"Method Not Allowed (405) for {param_value}")
                logging.error(f"Response body: {response.text}")
                logging.error("This suggests the API endpoint doesn't accept PUT requests")
                
                # Save detailed error info
                error_info = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "request_method": "PUT",
                    "request_url": ATM_DETAILS_URL,
                    "request_payload": payload
                }
                
                error_filename = f"method_error_{param_value}_{int(time.time())}.json"
                try:
                    with open(error_filename, 'w', encoding='utf-8') as f:
                        json_module.dump(error_info, f, indent=2, ensure_ascii=False)
                    logging.error(f"Detailed error info saved to: {error_filename}")
                except Exception as save_error:
                    logging.error(f"Failed to save error info: {save_error}")
                
                return []
            
            elif response.status_code != 200:
                logging.error(f"Unexpected status code {response.status_code} for {param_value}")
                logging.error(f"Response body: {response.text[:500]}")
                
                # Save response for analysis
                error_filename = f"status_{response.status_code}_{param_value}_{int(time.time())}.txt"
                try:
                    with open(error_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Status Code: {response.status_code}\n")
                        f.write(f"Headers: {dict(response.headers)}\n")
                        f.write(f"Body: {response.text}")
                    logging.error(f"Response saved to: {error_filename}")
                except Exception as save_error:
                    logging.error(f"Failed to save response: {save_error}")
                
                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return []
            
            # Enhanced response handling with robust error logging
            # Log raw response details for debugging
            logging.info(f"Raw response status: {response.status_code}")
            logging.info(f"Raw response headers: {dict(response.headers)}")
            
            # Get raw response text for debugging
            raw_response_text = response.text
            logging.info(f"Raw response length: {len(raw_response_text)} characters")
            
            # Try to parse as JSON with enhanced error handling
            try:
                dashboard_data = response.json()
                
                # Log the full response in formatted JSON for review
                import json as json_module
                formatted_response = json_module.dumps(dashboard_data, indent=2, ensure_ascii=False)
                logging.info(f"=== FORMATTED JSON RESPONSE FOR {param_value} ===")
                logging.info(formatted_response)
                logging.info("=== END FORMATTED JSON RESPONSE ===")
                
                # Validate response structure
                if not isinstance(dashboard_data, dict):
                    logging.error(f"Response is not a dictionary for {param_value}. Type: {type(dashboard_data)}")
                    logging.error(f"Raw response preview: {raw_response_text[:500]}...")
                    return []
                
                logging.info(f"Dashboard data keys: {list(dashboard_data.keys())}")
                
                # Extract body data as list (like working crawler)
                body_data = dashboard_data.get("body", [])
                
                if not isinstance(body_data, list):
                    logging.error(f"Expected body to be a list for {param_value}, got: {type(body_data)}")
                    logging.error(f"Body data content: {body_data}")
                    return []
                
                logging.info(f"Retrieved {len(body_data)} terminals for status {param_value}")
                
                # Log sample terminal data if available
                if body_data and len(body_data) > 0:
                    sample_terminal = body_data[0]
                    logging.info(f"Sample terminal keys: {list(sample_terminal.keys()) if isinstance(sample_terminal, dict) else 'Not a dict'}")
                
                # Update token if a new one was returned (like working crawler)
                if "header" in dashboard_data and "user_token" in dashboard_data["header"]:
                    new_token = dashboard_data["header"]["user_token"]
                    if new_token != user_token:
                        logging.info("Received new token in response, updating...")
                        session.user_token = new_token
                
                return body_data
                
            except json_module.JSONDecodeError as json_error:
                logging.error(f"JSON parsing failed for {param_value}: {str(json_error)}")
                logging.error(f"Raw response text (first 1000 chars): {raw_response_text[:1000]}")
                
                # Try to identify the response type
                if raw_response_text.strip().startswith('<'):
                    logging.error("Response appears to be HTML/XML, not JSON")
                elif raw_response_text.strip() == '':
                    logging.error("Response is empty")
                else:
                    logging.error("Response is not valid JSON format")
                
                # Save raw response to file for detailed analysis
                error_filename = f"error_response_{param_value}_{int(time.time())}.txt"
                try:
                    with open(error_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Status Code: {response.status_code}\n")
                        f.write(f"Headers: {dict(response.headers)}\n")
                        f.write(f"Raw Response:\n{raw_response_text}")
                    logging.error(f"Raw response saved to: {error_filename}")
                except Exception as save_error:
                    logging.error(f"Failed to save error response details: {save_error}")
            
            except Exception as parse_error:
                logging.error(f"Unexpected error while processing response for {param_value}: {str(parse_error)}")
                logging.error(f"Response status: {response.status_code}")
                logging.error(f"Response headers: {dict(response.headers)}")
                
                # Try to get raw response safely
                try:
                    raw_text = response.text
                    logging.error(f"Raw response (first 500 chars): {raw_text[:500]}")
                except Exception as text_error:
                    logging.error(f"Could not get response text: {text_error}")
            
        except requests.exceptions.RequestException as ex:
            logging.warning(f"Request failed for {param_value} (Attempt {attempt + 1}): {str(ex)}")
            
        if attempt < max_retries - 1:
            logging.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2
            continue
        return []
            
    return []  # All attempts failed





def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Retrieve ATM details from management system'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode with simulated data'
    )
    
    parser.add_argument(
        '--status',
        nargs='+',
        choices=['AVAILABLE', 'WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE'],  # Updated for internal network
        help='Filter by status (multiple allowed). Status types will be processed in priority order.'
    )
    
    parser.add_argument(
        '--save-json',
        action='store_true',
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--save-db',
        action='store_true',
               help='Save results to database'
    )
    
    parser.add_argument(
        '--class-mode',
        action='store_true',
        help='Use class-based implementation instead of functional'
    )
    
    args = parser.parse_args()
    
    # Log execution mode
    if args.demo:
        logging.info("Running in DEMO mode with simulated data")
    else:
        logging.info("Running in PRODUCTION mode connecting to actual API")
    
    if args.status:
        logging.info(f"Filtering by status: {', '.join(args.status)}")
    
    try:
        # Use class-based implementation if requested
        if args.class_mode:
            retriever = ATMDetailsRetriever(
                demo_mode=args.demo,
                status_types=args.status
            )
            
            success, all_atm_data = retriever.retrieve_all_atm_details(
                save_to_db=args.save_db
            )
            
            if not success:
                logging.error("Failed to retrieve ATM details")
                return 1
                
            # Display the results
            display_atm_data(all_atm_data)
            
            # Save to JSON if requested
            if args.save_json:
                json_path = save_to_json(all_atm_data)
                print(f"\nData saved to: {json_path}")
                
            return 0
        else:
            # Use functional implementation
            # Get ATM data (demo or production)
            if args.demo:
                # Get demo data in comprehensive format
                demo_data = get_demo_data(args.status)
                if not demo_data:
                    logging.error("Failed to generate demo data")
                    return 1
                
                # Convert demo data to comprehensive response format
                comprehensive_response = {
                    "retrieval_timestamp": datetime.now(pytz.timezone('Asia/Dili')).isoformat(),
                    "requested_statuses": args.status or ATM_STATUS_TYPES,
                    "processing_order": args.status or ATM_STATUS_TYPES,
                    "total_atms": len(demo_data),
                    "status_summary": {},
                    "atm_data": {},
                    "response_metadata": {
                        "source": "DEMO_MODE",
                        "api_endpoint": "SIMULATED",
                        "authentication_user": "DEMO_USER",
                        "processing_notes": [f"Generated {len(demo_data)} demo ATM records"]
                    }
                }
                
                # Group demo data by status in correct order
                ordered_statuses = args.status or ATM_STATUS_TYPES
                for status in ordered_statuses:
                    status_data = [atm for atm in demo_data if atm.get('issueStateName') == status or 
                                 (status == 'AVAILABLE' and atm.get('issueStateName') is None)]
                    comprehensive_response["atm_data"][status] = status_data
                    comprehensive_response["status_summary"][status] = len(status_data)
                
                logging.info(f"Generated comprehensive demo response with {len(demo_data)} ATM records")
            else:
                # Create session for API calls
                session = requests.Session()
                
                # Authenticate
                auth_token = authenticate(session)
                if not auth_token:
                    logging.error("Authentication failed, exiting")
                    return 1
                    
                # Fetch ATM details in comprehensive format
                comprehensive_response = fetch_atm_details_for_status(session, args.status)
                if not comprehensive_response or comprehensive_response.get("total_atms", 0) == 0:
                    logging.error("Failed to retrieve ATM data or no data available, exiting")
                    return 1
            
            # Process the comprehensive response for database and display
            all_atm_data = []
            for status in comprehensive_response.get("processing_order", []):
                status_data = comprehensive_response.get("atm_data", {}).get(status, [])
                if status_data:
                    # Process each status group
                    processed_status_data = process_atm_data(status_data)
                    all_atm_data.extend(processed_status_data)
            
            logging.info(f"Processed {len(all_atm_data)} ATM records from comprehensive response")
            
            # Save comprehensive response to JSON if requested
            if args.save_json:
                json_path = save_comprehensive_response_to_json(comprehensive_response)
                if json_path:
                    print(f"\nComprehensive response saved to: {json_path}")
                
                # Also save processed data for backwards compatibility
                processed_json_path = save_atm_list_to_json(all_atm_data)
                if processed_json_path:
                    print(f"Processed ATM data saved to: {processed_json_path}")
            
            # # Group processed data by status for display (maintaining order)
            grouped_data = {}
            for status in comprehensive_response.get("processing_order", []):
                grouped_data[status] = []
            
            for atm in all_atm_data:
                status = atm.get('status')
                if status in grouped_data:
                    grouped_data[status].append(atm)
                else:
                    # Handle any unexpected statuses
                    if status not in grouped_data:
                        grouped_data[status] = []
                    grouped_data[status].append(atm)
            
            # Save to database if requested
            if args.save_db and DB_AVAILABLE:
                db_connection = get_connection()
                if db_connection:
                    store_atm_data_in_db(db_connection, all_atm_data)
                    db_connection.close()
                else:
                    logging.error("Failed to connect to database")
            
            # Display comprehensive results
            print("\n" + "=" * 80)
            print("COMPREHENSIVE ATM DETAILS RETRIEVAL RESULTS")
            print("=" * 80)
            
            if not comprehensive_response.get("atm_data"):
                print("No ATM data retrieved.")
                return 1
            
            # Display metadata
            print(f"\nRetrieval Information:")
            print(f"- Timestamp: {comprehensive_response.get('retrieval_timestamp', 'Unknown')}")
            print(f"- Source: {comprehensive_response.get('response_metadata', {}).get('source', 'Unknown')}")
            print(f"- Total ATMs: {comprehensive_response.get('total_atms', 0)}")
            print(f"- Status types processed: {', '.join(comprehensive_response.get('processing_order', []))}")
            
            # Display summary by status (in correct order)
            print(f"\nStatus Summary (in processing order):")
            for status in comprehensive_response.get("processing_order", []):
                count = comprehensive_response.get("status_summary", {}).get(status, 0)
                percentage = (count / comprehensive_response.get('total_atms', 1)) * 100 if comprehensive_response.get('total_atms', 0) > 0 else 0
                print(f"- {status}: {count} ATMs ({percentage:.1f}%)")
            
            # Display detailed data by status (in correct order)
            print(f"\nDetailed Data by Status:")
            for status in comprehensive_response.get("processing_order", []):
                status_atms = grouped_data.get(status, [])
                if status_atms:
                    print(f"\n{'=' * 60}")
                    print(f"STATUS: {status} ({len(status_atms)} ATMs)")
                    print(f"{'=' * 60}")
                    
                    # Display table for this status
                    display_table = []
                    for atm in status_atms[:10]:  # Show up to 10 ATMs per status
                        display_table.append([
                            atm.get('terminal_id', 'Unknown'),
                            atm.get('external_id', 'N/A'),
                            atm.get('bank', 'N/A'),
                            (atm.get('terminal_name', 'Unknown') or 'Unknown')[:20],
                            (atm.get('location_str') or atm.get('city') or 'Unknown')[:25],
                            (atm.get('last_updated', 'Unknown')[:19] if atm.get('last_updated') else 'Unknown')
                        ])
                    
                    headers = ["Terminal ID", "External ID", "Bank", "Name", "Location", "Last Updated"]
                    print(tabulate(display_table, headers=headers, tablefmt="simple"))
                    
                    if len(status_atms) > 10:
                        print(f"... and {len(status_atms) - 10} more records")
                else:
                    print(f"\n{status}: No ATMs found")
            
            # Display processing notes
            processing_notes = comprehensive_response.get("response_metadata", {}).get("processing_notes", [])
            if processing_notes:
                print(f"\nProcessing Notes:")
                for note in processing_notes:
                    print(f"- {note}")
            
            print(f"\n{'=' * 80}")
            print(f"TOTAL PROCESSED: {len(all_atm_data)} ATMs across {len(comprehensive_response.get('processing_order', []))} status types")
            print(f"{'=' * 80}")
            
            return 0
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return 1

def authenticate(session):
    """Authenticate to the ATM management system and return session token"""
    logging.info(f"Authenticating to {LOGIN_URL}")
    
    try:
        # Disable SSL warnings - for development only!
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Make login request
        response = session.post(
            LOGIN_URL,
            json=LOGIN_PAYLOAD,
            headers=COMMON_HEADERS,
            verify=False  # Skip SSL verification - not recommended for production
        )
        
        if response.status_code != 200:
            logging.error(f"Authentication failed with status code: {response.status_code}")
            logging.error(f"Response: {response.text}")
            return None
        
        # Parse auth token from response using working crawler logic
        auth_data = response.json()
        
        # Extract token using the same method as working crawler
        user_token = None
        for key in ['user_token', 'token']:
            if key in auth_data:
                user_token = auth_data[key]
                logging.info(f"User token extracted with key '{key}'")
                break
                
        if not user_token:
            # Fallback: check 'header' field like working crawler
            user_token = auth_data.get("header", {}).get("user_token")
            if user_token:
                logging.info("User token extracted from 'header' field")
        
        if not user_token:
            logging.error(f"No auth token found in response: {list(auth_data.keys())}")
            return None
            
        # Store token in session for later use
        session.user_token = user_token
        
        logging.info("Authentication successful")
        return user_token
        
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return None


if __name__ == "__main__":
    sys.exit(main())
