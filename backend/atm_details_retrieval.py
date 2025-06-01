#!/usr/bin/env python3
"""
ATM Details Retrieval Script
============================

A robust script for retrieving detailed ATM fault information using the proven
logic from atm_crawler_complete.py. This script focuses specifically on fetching
terminal details with comprehensive error handling and retry mechanisms.

Features:
- Robust authentication with token refresh
- Comprehensive error handling and retry logic
- Support for demo mode for testing
- Detailed logging and debugging information
- JSON output with structured fault data
- Terminal-specific fault information retrieval

Author: ATM Monitoring System
Created: May 30, 2025
"""

import requests
import urllib3
import json
import logging
import sys
import time
import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    ENV_LOADED = True
    logging.info("Environment variables loaded from .env file")
except ImportError:
    ENV_LOADED = False
    logging.warning("dotenv not available, using system environment variables")

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("atm_details_retrieval.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("ATMDetailsRetrieval")

# --- Disable SSL warnings (self-signed certs) ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
DASHBOARD_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"

LOGIN_PAYLOAD = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2024"
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

# Default terminals to fetch details for (can be overridden via command line)
DEFAULT_TERMINALS = [
    {"terminal_id": "83", "issue_state_code": "HARD"},
    {"terminal_id": "84", "issue_state_code": "HARD"},
    {"terminal_id": "85", "issue_state_code": "CASH"}
]


class ATMDetailsRetriever:
    """
    Main class for retrieving ATM terminal details with robust error handling
    """
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize the ATM Details Retriever
        
        Args:
            demo_mode: Whether to run in demo mode (generates mock data)
        """
        self.demo_mode = demo_mode
        self.session = requests.Session()
        self.user_token = None
        self.retrieval_stats = {
            "total_requested": 0,
            "successful_retrievals": 0,
            "failed_retrievals": 0,
            "token_refreshes": 0,
            "retries_performed": 0
        }
        
        log.info(f"Initialized ATMDetailsRetriever - Demo Mode: {demo_mode}")
    
    def check_connectivity(self, timeout: int = 5) -> bool:
        """
        Check if we can connect to the target system
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connectivity is successful, False otherwise
        """
        try:
            log.info(f"Testing connectivity to {LOGIN_URL}")
            response = requests.head(LOGIN_URL, timeout=timeout, verify=False)
            log.info(f"Connectivity test successful: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Connectivity test failed: {str(e)}")
            return False
    
    def login(self) -> bool:
        """
        Authenticate and get the user token
        
        Returns:
            True if login successful, False otherwise
        """
        if self.demo_mode:
            log.info("DEMO MODE: Using mock authentication token")
            self.user_token = "mock-token-for-demo-mode"
            return True
        
        log.info("Starting authentication process...")
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                log.info(f"Login attempt {attempt + 1}/{max_retries}")
                
                response = self.session.post(
                    LOGIN_URL, 
                    json=LOGIN_PAYLOAD, 
                    headers=COMMON_HEADERS, 
                    verify=False, 
                    timeout=30
                )
                response.raise_for_status()
                
                login_data = response.json()
                log.info("Login response received successfully")
                
                # Extract user token with multiple fallback strategies
                user_token = None
                
                # Strategy 1: Direct token keys
                for key in ['user_token', 'token']:
                    if key in login_data:
                        user_token = login_data[key]
                        log.info(f"User token extracted with key '{key}'")
                        break
                
                # Strategy 2: Nested in header field
                if not user_token:
                    user_token = login_data.get("header", {}).get("user_token")
                    if user_token:
                        log.info("User token extracted from 'header' field")
                
                # Strategy 3: Search in response body
                if not user_token and "body" in login_data:
                    body = login_data["body"]
                    if isinstance(body, dict) and "user_token" in body:
                        user_token = body["user_token"]
                        log.info("User token extracted from 'body' field")
                
                if user_token:
                    self.user_token = user_token
                    log.info("Authentication successful")
                    return True
                else:
                    log.error("Failed to extract user token from login response")
                    log.error(f"Login response structure: {list(login_data.keys())}")
                    
                    if attempt < max_retries - 1:
                        log.info(f"Retrying authentication in 3 seconds...")
                        time.sleep(3)
                        continue
                    
            except requests.exceptions.HTTPError as e:
                log.error(f"HTTP error during authentication: {e}")
                log.error(f"Response status: {e.response.status_code if e.response else 'N/A'}")
                log.error(f"Response text: {e.response.text if e.response else 'N/A'}")
            
            except requests.exceptions.RequestException as e:
                log.error(f"Network error during authentication: {e}")
            
            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON response during authentication: {e}")
            
            except Exception as e:
                log.error(f"Unexpected error during authentication: {e}")
            
            if attempt < max_retries - 1:
                log.info(f"Authentication failed, retrying in 5 seconds...")
                time.sleep(5)
        
        log.error("All authentication attempts failed")
        return False
    
    def refresh_token(self) -> bool:
        """
        Refresh the authentication token if expired
        
        Returns:
            True if token refresh successful, False otherwise
        """
        log.info("Attempting to refresh authentication token...")
        self.retrieval_stats["token_refreshes"] += 1
        
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
            
            # Extract the refreshed token using the same strategies as login
            user_token = None
            for key in ['user_token', 'token']:
                if key in login_data:
                    user_token = login_data[key]
                    log.info(f"Refreshed token extracted with key '{key}'")
                    break
            
            if not user_token:
                user_token = login_data.get("header", {}).get("user_token")
                if user_token:
                    log.info("Refreshed token extracted from 'header' field")
            
            if user_token:
                self.user_token = user_token
                log.info("Token refresh successful")
                return True
            else:
                log.error("Failed to extract refreshed token")
                return False
                
        except Exception as e:
            log.error(f"Token refresh failed: {e}")
            return False
    
    def fetch_terminal_details(self, terminal_id: str, issue_state_code: str = "HARD") -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific terminal ID with robust error handling
        
        Args:
            terminal_id: The terminal ID to fetch details for
            issue_state_code: The issue state code (default: HARD)
            
        Returns:
            Terminal details dictionary or None if failed
        """
        self.retrieval_stats["total_requested"] += 1
        
        if self.demo_mode:
            log.info(f"DEMO MODE: Generating sample fault data for terminal {terminal_id}")
            return self._generate_demo_terminal_data(terminal_id, issue_state_code)
        
        if not self.user_token:
            log.error("No authentication token available. Please login first.")
            self.retrieval_stats["failed_retrievals"] += 1
            return None
        
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
        
        # Retry logic with comprehensive error handling
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                log.info(f"Fetching details for terminal {terminal_id} (attempt {retry_count + 1}/{max_retries})")
                log.info(f"Using issue state code: {issue_state_code}")
                
                # Log request details for debugging
                log.debug(f"Request URL: {details_url}")
                log.debug(f"Request payload: {json.dumps(details_payload, indent=2)}")
                
                response = self.session.put(
                    details_url,
                    json=details_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=30
                )
                
                log.info(f"Response status code: {response.status_code}")
                response.raise_for_status()
                
                # Parse and validate response
                details_data = response.json()
                log.info("Response successfully parsed as JSON")
                
                # Validate response structure
                if not isinstance(details_data, dict):
                    log.error(f"Unexpected response format for terminal {terminal_id} (not a dictionary)")
                    log.error(f"Response type: {type(details_data)}")
                    raise ValueError("Response is not a dictionary")
                
                # Check for required body field
                if "body" not in details_data:
                    log.error(f"Response missing 'body' field for terminal {terminal_id}")
                    log.error(f"Available response keys: {list(details_data.keys())}")
                    raise ValueError("Response missing 'body' field")
                
                # Extract and validate body data
                body_data = details_data["body"]
                if not isinstance(body_data, list):
                    log.warning(f"Body data is not a list for terminal {terminal_id}: {type(body_data)}")
                    if body_data is None:
                        log.info(f"No fault data found for terminal {terminal_id}")
                        body_data = []
                    else:
                        # Try to convert to list if possible
                        try:
                            body_data = [body_data] if body_data else []
                        except:
                            log.error(f"Cannot convert body data to list: {body_data}")
                            raise ValueError("Invalid body data format")
                
                # Update token if a new one was returned
                if "header" in details_data and "user_token" in details_data["header"]:
                    new_token = details_data["header"]["user_token"]
                    if new_token != self.user_token:
                        log.info("Received updated token in response")
                        self.user_token = new_token
                
                # Enhance response with metadata
                enhanced_response = {
                    "terminal_id": terminal_id,
                    "issue_state_code": issue_state_code,
                    "retrieval_timestamp": datetime.now().isoformat(),
                    "response_status": "success",
                    "body": body_data,
                    "fault_count": len(body_data) if body_data else 0,
                    "raw_response": details_data  # Include full response for debugging
                }
                
                log.info(f"Successfully retrieved details for terminal {terminal_id}")
                log.info(f"Found {len(body_data)} fault records")
                self.retrieval_stats["successful_retrievals"] += 1
                
                return enhanced_response
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                log.warning(f"HTTP error fetching terminal {terminal_id}: {e} (Status: {status_code})")
                
                # Handle specific HTTP status codes
                if status_code == 401:
                    log.warning("Unauthorized (401) - attempting token refresh...")
                    if self.refresh_token():
                        # Update payload with new token and retry
                        details_payload["header"]["user_token"] = self.user_token
                        log.info("Token refreshed, retrying request...")
                        self.retrieval_stats["retries_performed"] += 1
                        continue
                    else:
                        log.error("Token refresh failed, cannot continue")
                        break
                
                elif status_code == 404:
                    log.error(f"Terminal {terminal_id} not found (404)")
                    break  # Don't retry for 404 errors
                
                elif status_code == 500:
                    log.warning(f"Server error (500) for terminal {terminal_id}")
                    # Continue with retries for server errors
                
                # Log response details for debugging
                if e.response:
                    log.error(f"Response text: {e.response.text[:500]}...")
            
            except requests.exceptions.Timeout:
                log.warning(f"Timeout fetching details for terminal {terminal_id}")
            
            except requests.exceptions.RequestException as e:
                log.warning(f"Network error fetching terminal {terminal_id}: {e}")
            
            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON response for terminal {terminal_id}: {e}")
                # Log raw response for debugging
                try:
                    raw_response = response.text if 'response' in locals() else "Response not available"
                    log.error(f"Raw response (first 500 chars): {raw_response[:500]}")
                except:
                    log.error("Could not log raw response")
            
            except ValueError as e:
                log.error(f"Data validation error for terminal {terminal_id}: {e}")
            
            except Exception as e:
                log.error(f"Unexpected error fetching terminal {terminal_id}: {e}")
            
            # Increment retry count and wait before retrying
            retry_count += 1
            self.retrieval_stats["retries_performed"] += 1
            
            if retry_count < max_retries:
                wait_time = min(5 * retry_count, 15)  # Progressive backoff, max 15 seconds
                log.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # All retries exhausted
        log.error(f"All attempts failed for terminal {terminal_id}")
        self.retrieval_stats["failed_retrievals"] += 1
        
        # Return failure response with metadata
        return {
            "terminal_id": terminal_id,
            "issue_state_code": issue_state_code,
            "retrieval_timestamp": datetime.now().isoformat(),
            "response_status": "failed",
            "error": "Maximum retries exceeded",
            "body": [],
            "fault_count": 0
        }
    
    def _generate_demo_terminal_data(self, terminal_id: str, issue_state_code: str) -> Dict[str, Any]:
        """
        Generate demo terminal data for testing purposes
        
        Args:
            terminal_id: The terminal ID
            issue_state_code: The issue state code
            
        Returns:
            Mock terminal data dictionary
        """
        current_time = datetime.now()
        
        demo_data = {
            "terminal_id": terminal_id,
            "issue_state_code": issue_state_code,
            "retrieval_timestamp": current_time.isoformat(),
            "response_status": "demo",
            "body": [
                {
                    "terminalId": terminal_id,
                    "networkId": "P24",
                    "externalId": f"4520{terminal_id[-1] if terminal_id else '0'}",
                    "brand": "Nautilus Hyosun",
                    "model": "Monimax 5600",
                    "supplier": "BRI",
                    "location": f"DEMO Location for Terminal {terminal_id}",
                    "geoLocation": "TL-DL",
                    "terminalType": "ATM",
                    "osVersion": "00130035",
                    "issueStateName": issue_state_code,
                    "creationDate": int(current_time.timestamp() * 1000),
                    "statusDate": int(current_time.timestamp() * 1000),
                    "bank": "BRI",
                    "serialNumber": f"YB7620{terminal_id}",
                    "faultList": [
                        {
                            "faultId": f"1379{terminal_id}",
                            "faultTypeCode": issue_state_code,
                            "componentTypeCode": "PRR",
                            "issueStateName": issue_state_code,
                            "terminalId": int(terminal_id) if terminal_id.isdigit() else 999,
                            "serviceRequestId": 63173,
                            "location": "DÍLI",
                            "bank": "BRI",
                            "brand": "Nautilus Hyosun",
                            "model": "Monimax 5600",
                            "year": current_time.strftime("%Y"),
                            "month": current_time.strftime("%b").upper(),
                            "day": current_time.strftime("%d"),
                            "externalFaultId": f"PRR2119{terminal_id}",
                            "agentErrorDescription": {
                                "HARD": "MEDIA JAMMED - DEMO FAULT",
                                "CASH": "CASH LOW - DEMO FAULT",
                                "WARNING": "DEVICE WARNING - DEMO FAULT"
                            }.get(issue_state_code, "DEVICE ERROR - DEMO FAULT")
                        }
                    ]
                }
            ],
            "fault_count": 1
        }
        
        return demo_data
    
    def fetch_multiple_terminals(self, terminals: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Fetch details for multiple terminals
        
        Args:
            terminals: List of terminal dictionaries with 'terminal_id' and 'issue_state_code'
            
        Returns:
            List of terminal details responses
        """
        results = []
        
        log.info(f"Starting batch retrieval for {len(terminals)} terminals")
        
        for i, terminal_info in enumerate(terminals, 1):
            terminal_id = terminal_info.get("terminal_id")
            issue_state_code = terminal_info.get("issue_state_code", "HARD")
            
            log.info(f"Processing terminal {i}/{len(terminals)}: {terminal_id}")
            
            if not terminal_id:
                log.warning(f"Skipping terminal {i} - missing terminal_id")
                continue
            
            result = self.fetch_terminal_details(terminal_id, issue_state_code)
            if result:
                results.append(result)
            
            # Add delay between requests to avoid overwhelming the server
            if i < len(terminals) and not self.demo_mode:
                time.sleep(1)
        
        log.info(f"Batch retrieval completed: {len(results)} successful out of {len(terminals)} requested")
        return results
    
    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """
        Get retrieval statistics
        
        Returns:
            Dictionary containing retrieval statistics
        """
        stats = self.retrieval_stats.copy()
        stats["success_rate"] = (
            (stats["successful_retrievals"] / stats["total_requested"] * 100) 
            if stats["total_requested"] > 0 else 0
        )
        return stats
    
    def save_results_to_file(self, results: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Save results to a JSON file
        
        Args:
            results: List of terminal details results
            filename: Optional custom filename
            
        Returns:
            The filename where results were saved
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"atm_terminal_details_{timestamp}.json"
        
        # Ensure the filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Create comprehensive output structure
        output_data = {
            "retrieval_metadata": {
                "timestamp": datetime.now().isoformat(),
                "demo_mode": self.demo_mode,
                "total_terminals": len(results),
                "statistics": self.get_retrieval_statistics()
            },
            "terminal_details": results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            log.info(f"Results saved to: {filename}")
            log.info(f"Total terminals: {len(results)}")
            return filename
            
        except Exception as e:
            log.error(f"Failed to save results to {filename}: {e}")
            raise


def main():
    """
    Main execution function
    """
    parser = argparse.ArgumentParser(
        description='Retrieve detailed ATM fault information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --demo                                    # Run in demo mode
  %(prog)s --terminal 83 --state HARD              # Get details for terminal 83
  %(prog)s --terminals 83,84,85                    # Get details for multiple terminals
  %(prog)s --file terminals.json                   # Load terminals from JSON file
  %(prog)s --connectivity-check                    # Test network connectivity only
        """
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (generates mock data for testing)'
    )
    
    parser.add_argument(
        '--terminal',
        type=str,
        help='Single terminal ID to fetch details for'
    )
    
    parser.add_argument(
        '--state',
        type=str,
        default='HARD',
        choices=['HARD', 'CASH', 'WARNING', 'WOUNDED'],
        help='Issue state code (default: HARD)'
    )
    
    parser.add_argument(
        '--terminals',
        type=str,
        help='Comma-separated list of terminal IDs'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='JSON file containing terminal configurations'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output filename for results (default: auto-generated)'
    )
    
    parser.add_argument(
        '--connectivity-check',
        action='store_true',
        help='Test connectivity and exit'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        log.info("Verbose logging enabled")
    
    # Initialize retriever
    retriever = ATMDetailsRetriever(demo_mode=args.demo)
    
    # Connectivity check
    if args.connectivity_check:
        log.info("Performing connectivity check...")
        if retriever.check_connectivity():
            log.info("✅ Connectivity check passed")
            return 0
        else:
            log.error("❌ Connectivity check failed")
            return 1
    
    # Determine terminals to process
    terminals_to_process = []
    
    if args.file:
        # Load terminals from JSON file
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
            if isinstance(file_data, list):
                terminals_to_process = file_data
            elif isinstance(file_data, dict) and 'terminals' in file_data:
                terminals_to_process = file_data['terminals']
            else:
                log.error("Invalid file format. Expected list or dict with 'terminals' key")
                return 1
                
            log.info(f"Loaded {len(terminals_to_process)} terminals from {args.file}")
            
        except FileNotFoundError:
            log.error(f"File not found: {args.file}")
            return 1
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in file {args.file}: {e}")
            return 1
    
    elif args.terminals:
        # Parse comma-separated terminal IDs
        terminal_ids = [tid.strip() for tid in args.terminals.split(',')]
        terminals_to_process = [
            {"terminal_id": tid, "issue_state_code": args.state} 
            for tid in terminal_ids
        ]
        log.info(f"Processing {len(terminals_to_process)} terminals from command line")
    
    elif args.terminal:
        # Single terminal
        terminals_to_process = [{"terminal_id": args.terminal, "issue_state_code": args.state}]
        log.info(f"Processing single terminal: {args.terminal}")
    
    else:
        # Use default terminals
        terminals_to_process = DEFAULT_TERMINALS
        log.info(f"Using default terminals: {len(terminals_to_process)} terminals")
    
    # Authenticate if not in demo mode
    if not args.demo:
        log.info("Authenticating...")
        if not retriever.login():
            log.error("Authentication failed. Cannot proceed.")
            return 1
        log.info("Authentication successful")
    
    # Process terminals
    log.info(f"Starting terminal details retrieval...")
    log.info("=" * 60)
    
    results = retriever.fetch_multiple_terminals(terminals_to_process)
    
    # Display summary
    stats = retriever.get_retrieval_statistics()
    log.info("=" * 60)
    log.info("RETRIEVAL SUMMARY")
    log.info("=" * 60)
    log.info(f"Total requested: {stats['total_requested']}")
    log.info(f"Successful: {stats['successful_retrievals']}")
    log.info(f"Failed: {stats['failed_retrievals']}")
    log.info(f"Success rate: {stats['success_rate']:.1f}%")
    log.info(f"Token refreshes: {stats['token_refreshes']}")
    log.info(f"Retries performed: {stats['retries_performed']}")
    
    # Save results
    if results:
        try:
            filename = retriever.save_results_to_file(results, args.output)
            log.info(f"✅ Results saved to: {filename}")
        except Exception as e:
            log.error(f"❌ Failed to save results: {e}")
            return 1
    else:
        log.warning("No results to save")
    
    # Display sample fault data
    if results:
        log.info("\nSample fault data:")
        for result in results[:3]:  # Show first 3 results
            terminal_id = result.get('terminal_id', 'Unknown')
            fault_count = result.get('fault_count', 0)
            status = result.get('response_status', 'Unknown')
            
            log.info(f"  Terminal {terminal_id}: {fault_count} faults (Status: {status})")
            
            # Show first fault if available
            body = result.get('body', [])
            if body and len(body) > 0:
                first_item = body[0]
                fault_list = first_item.get('faultList', [])
                if fault_list and len(fault_list) > 0:
                    first_fault = fault_list[0]
                    error_desc = first_fault.get('agentErrorDescription', 'No description')
                    log.info(f"    First fault: {error_desc}")
    
    log.info("Terminal details retrieval completed")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        sys.exit(1)
