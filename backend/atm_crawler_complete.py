#!/usr/bin/env python3
# filepath: atm_crawler_complete.py

import requests
import urllib3
import json
import csv
import logging
import sys
import time
from datetime import datetime
from tqdm import tqdm
import os
import argparse

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    ENV_LOADED = True
except ImportError:
    ENV_LOADED = False

# Try to import database connector
try:
    import db_connector  # type: ignore
    DB_AVAILABLE = True
except ImportError:
    db_connector = None  # type: ignore
    DB_AVAILABLE = False

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("atm_crawler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("ATMCrawler")

# --- Disable SSL warnings (self-signed certs) ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Config ---
login_url = "https://172.31.1.46/sigit/user/login?language=EN"
dashboard_url = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"
login_payload = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2024"
}
# Define all the parameter values we want to crawl
parameter_values = ["WOUNDED", "HARD", "CASH", "UNAVAILABLE", "AVAILABLE", "WARNING", "ZOMBIE"]
common_headers = {
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

def check_connectivity(url, timeout=5):
    """Check if we can connect to the target system"""
    try:
        log.info(f"Testing connectivity to {url}")
        response = requests.head(
            url, 
            timeout=timeout, 
            verify=False
        )
        log.info(f"Connectivity test successful: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"Connectivity test failed: {str(e)}")
        return False

def refresh_token(session):
    """Refresh the authentication token if expired"""
    log.info("Attempting to refresh authentication token...")
    
    res = session.post(login_url, json=login_payload, headers=common_headers, verify=False)
    try:
        res.raise_for_status()
    except Exception as ex:
        log.error(f"Token refresh HTTP error: {str(ex)}")
        log.error(f"Response status: {res.status_code}, text: {res.text}")
        return None
        
    try:
        login_json = res.json()
    except Exception:
        log.error("Token refresh response not in JSON format!")
        return None
        
    # Extract the refreshed token
    user_token = None
    for key in ['user_token', 'token']:
        if key in login_json:
            user_token = login_json[key]
            log.info(f"Refreshed user_token extracted with key '{key}'")
            return user_token
            
    # Fallback: check 'header' field
    user_token = login_json.get("header", {}).get("user_token")
    if user_token:
        log.info("Refreshed user_token extracted from 'header' field.")
        return user_token
        
    log.error("Failed to extract refreshed token")
    return None

def get_terminals_by_status(session, user_token, param_value, demo_mode=False):
    """Fetch terminal data for a specific parameter value"""
    if demo_mode:
        log.info(f"DEMO MODE: Generating sample terminals for status {param_value}")
        # Return sample data for demo mode
        sample_terminals = [{
            'terminalId': f"{i+80}",
            'location': f"Sample Location {i}",
            'issueStateName': param_value,
            'fetched_status': param_value,
            'issueStateCode': 'HARD' if param_value == 'WOUNDED' else param_value,
            'brand': 'Nautilus Hyosun',
            'model': 'Monimax 5600'
        } for i in range(3)]  # Generate 3 sample terminals
        return sample_terminals, user_token
    
    dashboard_payload = {
        "header": {
            "logged_user": login_payload["user_name"],
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
    
    # Add retry logic for reliability
    max_retries = 3
    retry_count = 0
    success = False
    terminals = []
    
    while retry_count < max_retries and not success:
        try:
            log.info(f"Requesting terminal dashboard data for {param_value}... (Attempt {retry_count + 1}/{max_retries})")
            dashboard_res = session.put(
                dashboard_url,
                json=dashboard_payload,
                headers=common_headers,
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
                    return [], user_token
                log.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Check if the body field exists in the response
            if "body" not in dashboard_data:
                log.error(f"Dashboard response for {param_value} is missing the 'body' field")
                log.error(f"Response keys: {list(dashboard_data.keys())}")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All attempts failed due to missing 'body' field for {param_value}")
                    return [], user_token
                log.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Check if the body contains terminals
            body_data = dashboard_data.get("body", [])
            if not body_data:
                log.warning(f"No terminals found for status {param_value}")
                success = True  # This is not an error, just no data
                return [], user_token
                
            # Make sure body_data is a list before iterating over it
            if not isinstance(body_data, list):
                log.error(f"Body data for {param_value} is not a list. Type: {type(body_data)}")
                body_data = []
                return [], user_token
                
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
                if new_token != user_token:
                    log.info("Received new token in response, updating...")
                    user_token = new_token
            
        except requests.exceptions.RequestException as ex:
            log.warning(f"Request failed for {param_value} (Attempt {retry_count + 1}): {str(ex)}")
            
            # Check if this might be a token expiration issue (401 Unauthorized)
            if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                log.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                new_token = refresh_token(session)
                
                if new_token:
                    user_token = new_token
                    log.info("Token refreshed successfully, updating payload with new token")
                    # Update the payload with the new token
                    dashboard_payload["header"]["user_token"] = user_token
                    # Don't increment retry count for token refresh
                    log.info("Retrying request with new token...")
                    continue
            
            retry_count += 1
            if retry_count >= max_retries:
                log.error(f"All attempts failed for {param_value}. Skipping this parameter.")
                return [], user_token
            log.info(f"Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
        except ValueError as ex:
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
                return [], user_token
            log.info(f"Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
    return terminals, user_token

def fetch_terminal_details(session, user_token, terminal_id, issue_state_code, demo_mode=False):
    """Fetch detailed information for a specific terminal ID"""
    if demo_mode:
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
                            "location": "DÍLI",
                            "bank": "BRI",
                            "brand": "Nautilus Hyosun",
                            "model": "Monimax 5600",
                            "year": datetime.now().strftime("%Y"),
                            "month": datetime.now().strftime("%b").upper(),
                            "day": datetime.now().strftime("%d"),
                            "externalFaultId": f"PRR2119{terminal_id}",
                            "agentErrorDescription": "MEDIA JAMMED" if issue_state_code == "HARD" else 
                                                    "CASH LOW" if issue_state_code == "CASH" else 
                                                    "DEVICE ERROR"
                        }
                    ]
                }
            ]
        }
        return user_token, terminal_data
    
    details_url = f"{dashboard_url}&terminal_id={terminal_id}"
    
    details_payload = {
        "header": {
            "logged_user": login_payload["user_name"],
            "user_token": user_token
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
            log.info(f"Requesting details for terminal {terminal_id}... (Attempt {retry_count + 1}/{max_retries})")
            details_res = session.put(details_url, json=details_payload, headers=common_headers, verify=False, timeout=30)
            details_res.raise_for_status()
            
            # Try to parse JSON
            details_data = details_res.json()
            
            # Check if the response has the expected structure
            if not isinstance(details_data, dict):
                log.error(f"Details response for terminal {terminal_id} has unexpected format (not a dictionary)")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All attempts failed due to unexpected response format for terminal {terminal_id}")
                    return user_token, None
                log.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Check if the body field exists in the response
            if "body" not in details_data:
                log.error(f"Details response for terminal {terminal_id} is missing the 'body' field")
                log.error(f"Response keys: {list(details_data.keys())}")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error(f"All attempts failed due to missing 'body' field for terminal {terminal_id}")
                    return user_token, None
                log.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            success = True
            terminal_data = details_data
            log.info(f"Details fetch successful for terminal {terminal_id} on attempt {retry_count + 1}")
            
            # Update token if a new one was returned
            if "header" in details_data and "user_token" in details_data["header"]:
                new_token = details_data["header"]["user_token"]
                if new_token != user_token:
                    log.info("Received new token in response, updating...")
                    user_token = new_token
            
        except requests.exceptions.RequestException as ex:
            log.warning(f"Request failed for terminal {terminal_id} (Attempt {retry_count + 1}): {str(ex)}")
            
            # Check if this might be a token expiration issue (401 Unauthorized)
            if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                log.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                new_token = refresh_token(session)
                
                if new_token:
                    user_token = new_token
                    log.info("Token refreshed successfully, updating payload with new token")
                    # Update the payload with the new token
                    details_payload["header"]["user_token"] = user_token
                    # Don't increment retry count for token refresh
                    log.info("Retrying request with new token...")
                    continue
            
            retry_count += 1
            if retry_count >= max_retries:
                log.error(f"All attempts failed for terminal {terminal_id}. Skipping this terminal.")
                return user_token, None
            log.info(f"Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
        except ValueError as ex:
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
                return user_token, None
            log.info(f"Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
    return user_token, terminal_data

def login(session, demo_mode=False):
    """Log in and get the authentication token"""
    if demo_mode:
        log.info("DEMO MODE: Using mock token")
        return "mock-token-for-demo-mode"
        
    log.info("Starting login process...")
    try:
        res = session.post(login_url, json=login_payload, headers=common_headers, verify=False, timeout=30)
        res.raise_for_status()
        
        login_json = res.json()
        user_token = None
        for key in ['user_token', 'token']:
            if key in login_json:
                user_token = login_json[key]
                log.info(f"user_token extracted from login response with key '{key}'")
                break
        if not user_token:
            # Fallback: check 'header' field (some APIs nest here)
            user_token = login_json.get("header", {}).get("user_token")
            if user_token:
                log.info("user_token extracted from 'header' field.")
        if not user_token:
            log.error("Failed to extract user token!")
            return None
        return user_token
    except Exception as e:
        log.error(f"Login failed: {str(e)}")
        return None

def run_and_return_data(use_demo_mode=False):
    """Run the crawler and return the data for further processing (like email transfer)
    
    Parameters:
        use_demo_mode (bool): Whether to use demo mode (no actual requests)
        
    Returns:
        tuple: (terminals_data, terminal_details, regional_data) for further processing
               - terminals_data: List of terminal status data
               - terminal_details: List of detailed terminal information  
               - regional_data: Fifth_graphic regional ATM count data (or None)
    """
    log.info(f"Starting ATM crawler in {'demo' if use_demo_mode else 'live'} mode to collect data")
    
    try:
        # Start session
        session = requests.Session()
        
        # -- Get all terminals --
        all_terminals = []
        
        if use_demo_mode:
            # Generate demo data
            log.info("Generating demo terminal data")
            # Sample parameter values from the main script
            status_values = ['AVAILABLE', 'OUT_OF_SERVICE', 'SUPERVISOR', 'MAINTENANCE']
            
            # Generate sample terminals for each status
            for status in status_values:
                # Generate between 5-20 terminals for each status
                count = min(20, max(5, int(status == 'AVAILABLE') * 15 + 5))
                
                # Create sample terminals
                for i in range(count):
                    terminal_id = f"ATM{i:04d}-{status[:3]}"
                    terminal = {
                        'terminalId': terminal_id,
                        'location': f"Location {i} - {status}",
                        'fetched_status': status,
                        'status': status,
                        'serialNumber': f"SN{i:06d}"
                    }
                    all_terminals.append(terminal)
            
            log.info(f"Generated {len(all_terminals)} demo terminals")
            # Initialize user_token for demo mode
            user_token = "demo-token"
        else:
            # Login to system
            user_token = login(session, False)
            
            if not user_token:
                log.error("Login failed, cannot proceed with data collection")
                return [], []
            
            # Fetch real terminals for each parameter value
            for param_value in parameter_values:
                terminals, user_token = get_terminals_by_status(session, user_token, param_value, False)
                
                if terminals:
                    # Add each terminal to our combined list with the fetched status
                    for terminal in terminals:
                        terminal['fetched_status'] = param_value
                        all_terminals.append(terminal)
                    
                    log.info(f"Added {len(terminals)} terminals with status {param_value}")
                else:
                    log.warning(f"No terminals found with status {param_value}")
        
        if not all_terminals:
            log.warning("No terminal data found")
            return [], []
        
        # -- Get terminal details --
        # Filter out non-AVAILABLE terminals for details
        non_available_terminals = [t for t in all_terminals if t.get('fetched_status') != 'AVAILABLE']
        log.info(f"Found {len(non_available_terminals)} non-AVAILABLE terminals to process for details")
        
        all_terminal_details = []
        
        if use_demo_mode:
            # Generate demo details
            log.info("Generating demo terminal details")
            
            for terminal in tqdm(non_available_terminals, desc="Generating demo details"):
                terminal_id = terminal.get('terminalId')
                status = terminal.get('fetched_status')
                
                # Only generate details for non-available terminals
                if status != 'AVAILABLE':
                    # Create a sample detail record
                    detail = {
                        'terminalId': terminal_id,
                        'location': terminal.get('location', f"Location for {terminal_id}"),
                        'issueStateName': status,
                        'serialNumber': terminal.get('serialNumber', f"SN-{terminal_id}"),
                        'year': datetime.now().year,
                        'month': datetime.now().month,
                        'day': datetime.now().day,
                        'externalFaultId': f"FAULT-{terminal_id}-{status}",
                        'agentErrorDescription': f"Demo fault for {status}: Device error simulation",
                        'fetched_status': status
                    }
                    all_terminal_details.append(detail)
        else:
            # Process each non-AVAILABLE terminal for details
            for terminal in tqdm(non_available_terminals, desc="Fetching terminal details", unit="terminal"):
                terminal_id = terminal.get('terminalId')
                issue_state_code = terminal.get('issueStateCode', 'HARD')  # Default to HARD if not available
                
                if not terminal_id:
                    log.warning(f"Skipping terminal with missing ID")
                    continue
                    
                # Get detailed information for this terminal
                user_token, terminal_data = fetch_terminal_details(
                    session,
                    user_token,
                    terminal_id,
                    issue_state_code,
                    False
                )
                
                if terminal_data:
                    # Process the terminal data
                    terminal_body = terminal_data.get('body', [])
                    
                    if isinstance(terminal_body, list) and terminal_body:
                        for item in terminal_body:
                            # Extract the specific fields we need for this terminal
                            extracted_data = {
                                'terminalId': item.get('terminalId', ''),
                                'location': item.get('location', ''),
                                'issueStateName': item.get('issueStateName', ''),
                                'serialNumber': item.get('serialNumber', '')
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
                            else:
                                # Set default values if no fault information is available
                                extracted_data.update({
                                    'year': '',
                                    'month': '',
                                    'day': '',
                                    'externalFaultId': '',
                                    'agentErrorDescription': ''
                                })
                                
                            # Add the status from the original search
                            extracted_data['fetched_status'] = terminal.get('fetched_status', '')
                            
                            # Add to the combined results
                            all_terminal_details.append(extracted_data)
        
        log.info(f"Collected data for {len(all_terminals)} terminals and {len(all_terminal_details)} fault details")
        
        # Collect fifth_graphic (regional ATM count) data
        regional_data = None
        try:
            log.info("Collecting fifth_graphic regional data...")
            user_token, reports_data = fetch_reports_dashboard(session, user_token, use_demo_mode)
            
            if reports_data and "body" in reports_data and "fifth_graphic" in reports_data["body"]:
                regional_data = reports_data["body"]["fifth_graphic"]
                log.info(f"Successfully collected fifth_graphic data for {len(regional_data)} regions")
            else:
                log.warning("No fifth_graphic data found in reports dashboard response")
                
        except Exception as regional_error:
            log.error(f"Error collecting fifth_graphic data: {str(regional_error)}")
        
        return all_terminals, all_terminal_details, regional_data
        
    except Exception as e:
        log.error(f"Error running crawler: {str(e)}")
        if not use_demo_mode:
            log.info("Attempting to collect data in demo mode as fallback")
            try:
                return run_and_return_data(use_demo_mode=True)
            except Exception as fallback_error:
                log.error(f"Fallback to demo mode also failed: {str(fallback_error)}")
                return [], [], None
        return [], [], None

def fetch_reports_dashboard(session, user_token, demo_mode=False):
    """Fetch reports dashboard data containing fifth_graphic information"""
    if demo_mode:
        log.info("DEMO MODE: Generating sample fifth_graphic data")
        # Return sample data for demo mode
        return user_token, {
            "body": {
                "fifth_graphic": [
                    {
                        "hc-key": "TL-DL",
                        "state_count": {
                            "AVAILABLE": "0.78571427",
                            "WOUNDED": "0.21428572"
                        }
                    }
                ]
            }
        }
    
    reports_url = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=subStatus"
    
    reports_payload = {
        "header": {
            "logged_user": login_payload["user_name"],
            "user_token": user_token
        },
        "body": []  # Empty array as per the API specification
    }
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            log.info(f"Requesting reports dashboard data... (Attempt {retry_count + 1}/{max_retries})")
            response = session.put(
                reports_url,
                json=reports_payload,
                headers=common_headers,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            # Try to parse JSON
            reports_data = response.json()
            
            # Check if the response has the expected structure
            if not isinstance(reports_data, dict):
                log.error("Reports dashboard response has unexpected format (not a dictionary)")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error("All attempts failed due to unexpected response format")
                    return user_token, None
                log.info("Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Check if the body field exists in the response
            if "body" not in reports_data:
                log.error("Reports dashboard response is missing the 'body' field")
                log.error(f"Response keys: {list(reports_data.keys())}")
                retry_count += 1
                if retry_count >= max_retries:
                    log.error("All attempts failed due to missing 'body' field")
                    return user_token, None
                log.info("Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Check if fifth_graphic exists in the body
            body_data = reports_data.get("body", {})
            if "fifth_graphic" not in body_data:
                log.warning("fifth_graphic not found in reports dashboard response")
                log.info("Available body keys: " + str(list(body_data.keys())))
                # This is not necessarily an error, continue without retrying
                return user_token, reports_data
            
            log.info("Reports dashboard fetch successful")
            
            # Update token if a new one was returned
            if "header" in reports_data and "user_token" in reports_data["header"]:
                new_token = reports_data["header"]["user_token"]
                if new_token != user_token:
                    log.info("Received new token in response, updating...")
                    user_token = new_token
            
            return user_token, reports_data
            
        except requests.exceptions.RequestException as ex:
            log.warning(f"Request failed for reports dashboard (Attempt {retry_count + 1}): {str(ex)}")
            
            # Check if this might be a token expiration issue (401 Unauthorized)
            if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                log.warning("Detected possible token expiration (401 Unauthorized). Attempting to refresh token...")
                new_token = refresh_token(session)
                
                if new_token:
                    user_token = new_token
                    log.info("Token refreshed successfully, updating payload with new token")
                    reports_payload["header"]["user_token"] = user_token
                    log.info("Retrying request with new token...")
                    continue
            
            retry_count += 1
            if retry_count >= max_retries:
                log.error("All attempts failed for reports dashboard. Skipping this request.")
                return user_token, None
            log.info("Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
        except ValueError as ex:
            log.error(f"Reports dashboard response not valid JSON! (Attempt {retry_count + 1})")
            retry_count += 1
            if retry_count >= max_retries:
                log.error("All JSON parsing attempts failed for reports dashboard.")
                return user_token, None
            log.info("Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
    return user_token, None

# ...existing code...
def main(use_demo_mode=None, save_to_db=False):
    """Main execution flow combining both ATM status fetching and terminal details retrieval"""
    try:
        log.info("Starting ATM Crawler v1.0...")
        
        # Parse command line arguments when called directly
        if __name__ == "__main__" and (use_demo_mode is None):
            parser = argparse.ArgumentParser(description="ATM Status Crawler")
            parser.add_argument('--demo', action='store_true', help='Run in demo mode')
            parser.add_argument('--db', action='store_true', help='Save data to PostgreSQL database')
            args = parser.parse_args()
            
            use_demo_mode = args.demo
            save_to_db = args.db and DB_AVAILABLE
            
            # Log database availability
            if args.db and not DB_AVAILABLE:
                log.warning("Database integration requested but db_connector module not available")
                log.warning("Data will be saved to CSV files only")
        
        # Test connectivity to the target system
        base_url = "https://172.31.1.46"
        demo_mode = False
        
        # Check if database integration is possible
        db_integration = save_to_db and DB_AVAILABLE
        if db_integration:
            log.info("Database integration enabled - will save data to PostgreSQL")
        
        if use_demo_mode is not None:
            # If demo mode is explicitly set, use that
            demo_mode = use_demo_mode
            if demo_mode:
                log.info("Using demo mode as specified")
        elif not check_connectivity(base_url):
            log.warning("Cannot connect to the target system. Make sure you're connected to the corporate network.")
            log.warning("This script needs access to the internal network (172.31.1.46)")
            
            response = input("Do you want to continue in DEMO mode with sample data? (y/n): ")
            if response.lower() in ('y', 'yes'):
                log.info("Continuing in DEMO mode with sample data")
                demo_mode = True
            else:
                log.error("Exiting due to connectivity issues")
                sys.exit(1)
        
        # Create session and login
        session = requests.Session()
        user_token = login(session, demo_mode)
        
        if not user_token:
            if demo_mode:
                log.warning("Using demo token for demonstration purposes")
                user_token = "demo-token"
            else:
                log.error("Login failed, cannot proceed without authentication")
                sys.exit(2)
        
        # -- PART 1: Fetch ATM Status for All Parameter Values --
        log.info("PHASE 1: Collecting ATM status data for all parameter values...")
        
        # Initialize a list to collect all terminals data
        all_terminals = []
        status_counts = {}
        
        # Process each parameter value with progress bar
        for param_value in tqdm(parameter_values, desc="Fetching ATM status data", unit="status"):
            terminals, user_token = get_terminals_by_status(session, user_token, param_value, demo_mode)
            
            if terminals:
                # Add each terminal to our combined list
                for terminal in terminals:
                    # Add the status we searched for
                    terminal['fetched_status'] = param_value
                    all_terminals.append(terminal)
                
                # Track how many terminals we found for each status
                status_counts[param_value] = len(terminals)
                log.info(f"Added {len(terminals)} terminals with status {param_value}")
            else:
                log.warning(f"No terminals found with status {param_value}")
                status_counts[param_value] = 0
        
        # Phase 1 Reporting
        log.info("\n=== ATM Status Summary ===")
        total_terminals = sum(status_counts.values())
        for status, count in status_counts.items():
            percentage = (count / total_terminals * 100) if total_terminals > 0 else 0
            log.info(f"{status}: {count} terminals ({percentage:.1f}%)")
        log.info(f"Total: {total_terminals} terminals")
        log.info("=========================\n")
        
        # Save all terminals to CSV
        if all_terminals:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_request_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            # Ensure the saved_data directory exists
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_data")
            os.makedirs(save_dir, exist_ok=True)
            status_csv_filename = os.path.join(save_dir, f"atm_status_all_{timestamp}.csv")
            
            # Collect all fields present in at least one terminal
            all_keys = set()
            for terminal in all_terminals:
                terminal['dateRequest'] = date_request_str  # Add dateRequest to each row
                all_keys.update(terminal.keys())
            all_keys = sorted(all_keys)
            
            # Make sure 'fetched_status' is the first column
            if 'fetched_status' in all_keys:
                all_keys.remove('fetched_status')
                all_keys = ['fetched_status'] + all_keys
            
            # Ensure 'dateRequest' is last column
            if 'dateRequest' in all_keys:
                all_keys.remove('dateRequest')
                all_keys = all_keys + ['dateRequest']
            
            with open(status_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=all_keys)
                writer.writeheader()
                for terminal in all_terminals:
                    writer.writerow(terminal)
            log.info(f"Saved all ATM status data to {status_csv_filename} ({len(all_terminals)} rows)")
        else:
            log.error("No terminals found for any status! Cannot proceed.")
            sys.exit(3)
            
        # -- PART 2: Fetch Detailed Information for Non-AVAILABLE Terminals --
        log.info("\nPHASE 2: Collecting detailed information for non-AVAILABLE terminals...")
        
        # Filter out non-AVAILABLE terminals
        non_available_terminals = [t for t in all_terminals if t.get('fetched_status') != 'AVAILABLE']
        log.info(f"Found {len(non_available_terminals)} non-AVAILABLE terminals to process")
        
        # Process each non-AVAILABLE terminal
        all_terminal_details = []
        
        for terminal in tqdm(non_available_terminals, desc="Fetching terminal details", unit="terminal"):
            terminal_id = terminal.get('terminalId')
            issue_state_code = terminal.get('issueStateCode', 'HARD')  # Default to HARD if not available
            
            if not terminal_id:
                log.warning(f"Skipping terminal with missing ID: {terminal}")
                continue
                
            # Get detailed information for this terminal
            user_token, terminal_data = fetch_terminal_details(
                session,
                user_token,
                terminal_id,
                issue_state_code,
                demo_mode
            )
            
            if terminal_data:
                # Process the terminal data
                terminal_body = terminal_data.get('body', [])
                
                if isinstance(terminal_body, list) and terminal_body:
                    for item in terminal_body:
                        # Extract the specific fields we need for this terminal
                        extracted_data = {
                            'terminalId': item.get('terminalId', ''),
                            'location': item.get('location', ''),
                            'issueStateName': item.get('issueStateName', ''),
                            'serialNumber': item.get('serialNumber', '')
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
                        else:
                            # Set default values if no fault information is available
                            extracted_data.update({
                                'year': '',
                                'month': '',
                                'day': '',
                                'externalFaultId': '',
                                'agentErrorDescription': ''
                            })
                            
                        # Add the status from the original search
                        extracted_data['fetched_status'] = terminal.get('fetched_status', '')
                        
                        # Add to the combined results
                        all_terminal_details.append(extracted_data)
                    
                    log.info(f"Added details for terminal {terminal_id}")
                else:
                    log.warning(f"No details found in body for terminal {terminal_id}")
                    
                    # Add placeholder with original data to indicate we tried
                    placeholder = {
                        'terminalId': terminal_id,
                        'location': terminal.get('location', ''),
                        'issueStateName': issue_state_code,
                        'serialNumber': terminal.get('serialNumber', ''),
                        'year': '',
                        'month': '',
                        'day': '',
                        'externalFaultId': '',
                        'agentErrorDescription': '',
                        'fetched_status': terminal.get('fetched_status', ''),
                        'details_status': 'NO_DETAILS_AVAILABLE'
                    }
                    all_terminal_details.append(placeholder)
            else:
                log.warning(f"Failed to fetch details for terminal {terminal_id}")
                
                # Add placeholder with original data to indicate failure
                placeholder = {
                    'terminalId': terminal_id,
                    'location': terminal.get('location', ''),
                    'issueStateName': issue_state_code,
                    'serialNumber': terminal.get('serialNumber', ''),
                    'year': '',
                    'month': '',
                    'day': '',
                    'externalFaultId': '',
                    'agentErrorDescription': '',
                    'fetched_status': terminal.get('fetched_status', ''),
                    'details_status': 'FETCH_FAILED'
                }
                all_terminal_details.append(placeholder)
                
            # Add a small delay between requests to avoid overwhelming the server
            time.sleep(1)
            
        log.info(f"Collected details for {len(all_terminal_details)} terminals")
        
        # Save terminal details to CSV
        if all_terminal_details:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_request_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            # Ensure the saved_data directory exists
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_data")
            os.makedirs(save_dir, exist_ok=True)
            details_csv_filename = os.path.join(save_dir, f"atm_fault_details_{timestamp}.csv")
            
            # Priority fields for better readability
            priority_fields = [
                "terminalId", "location", "issueStateName", "year", "month", "day", 
                "externalFaultId", "agentErrorDescription", "serialNumber", "fetched_status", 
                "details_status"
            ]
            
            # Collect all fields present in at least one terminal detail
            all_keys = set()
            for terminal in all_terminal_details:
                terminal['dateRequest'] = date_request_str  # Add dateRequest to each row
                all_keys.update(terminal.keys())
            
            # Sort fields with priority fields first
            all_keys = sorted(all_keys)
            for field in reversed(priority_fields):
                if field in all_keys:
                    all_keys.remove(field)
                    all_keys = [field] + all_keys
            
            # Ensure 'dateRequest' is last column
            if 'dateRequest' in all_keys:
                all_keys.remove('dateRequest')
                all_keys = all_keys + ['dateRequest']
            
            with open(details_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=all_keys)
                writer.writeheader()
                for entry in all_terminal_details:
                    writer.writerow(entry)
            log.info(f"Saved terminal details to {details_csv_filename} ({len(all_terminal_details)} rows, {len(all_keys)} columns)")
            
            # Generate a summary of fault types
            fault_types = {}
            for terminal in all_terminal_details:
                error_desc = terminal.get('agentErrorDescription', '')
                if error_desc:
                    if error_desc in fault_types:
                        fault_types[error_desc] += 1
                    else:
                        fault_types[error_desc] = 1
            
            log.info("\n=== Fault Summary ===")
            for error_type, count in sorted(fault_types.items(), key=lambda x: x[1], reverse=True):
                if error_type:
                    log.info(f"Error: {error_type} - Count: {count}")
            log.info("=====================")
            
            # Save to database if integration is enabled
            if db_integration and DB_AVAILABLE and db_connector is not None:
                log.info("\n=== Database Integration ===")
                try:
                    # Check database connection
                    conn = db_connector.get_db_connection()
                    if conn:
                        conn.close()
                        log.info("Database connection successful")
                        
                        # Check database tables
                        tables_ok = db_connector.check_db_tables()
                        if tables_ok:
                            log.info("Database tables exist and are ready")
                            
                            # Save data to database
                            log.info(f"Saving {len(all_terminals)} terminals and {len(all_terminal_details)} fault records to database")
                            success = db_connector.save_to_database(all_terminals, all_terminal_details)
                            
                            if success:
                                log.info("Data successfully saved to database")
                            else:
                                log.error("Failed to save data to database")
                        else:
                            log.error("Database tables check failed")
                    else:
                        log.error("Database connection failed")
                except Exception as db_error:
                    log.error(f"Database error: {str(db_error)}")
                    log.debug("Database error details:", exc_info=True)
            
        else:
            log.warning("No terminal details were collected!")
        
        # -- PART 3: Fetch Reports Dashboard Data for Fifth Graphic --
        log.info("\nPHASE 3: Collecting regional ATM count data (fifth_graphic)...")
        
        try:
            user_token, reports_data = fetch_reports_dashboard(session, user_token, demo_mode)
            
            if reports_data and "body" in reports_data and "fifth_graphic" in reports_data["body"]:
                fifth_graphic_data = reports_data["body"]["fifth_graphic"]
                log.info(f"Found fifth_graphic data with {len(fifth_graphic_data)} regions")
                
                # Save fifth_graphic data to database if integration is enabled
                if db_integration and DB_AVAILABLE and db_connector is not None:
                    try:
                        # Ensure regional table exists
                        regional_tables_ok = db_connector.check_regional_atm_counts_table()
                        if regional_tables_ok:
                            log.info("Regional ATM counts table is ready")
                            
                            # Save fifth_graphic data to database
                            log.info(f"Saving fifth_graphic data for {len(fifth_graphic_data)} regions to database")
                            success = db_connector.save_fifth_graphic_to_database(fifth_graphic_data)
                            
                            if success:
                                log.info("Fifth_graphic data successfully saved to database")
                                
                                # Get and display the latest regional data
                                latest_data = db_connector.get_latest_regional_data()
                                if latest_data:
                                    log.info("\n=== Latest Regional ATM Counts ===")
                                    for region in latest_data:
                                        log.info(f"Region {region['region_code']}:")
                                        log.info(f"  Available: {region['count_available']}")
                                        log.info(f"  Warning: {region['count_warning']}")
                                        log.info(f"  Zombie: {region['count_zombie']}")
                                        log.info(f"  Wounded: {region['count_wounded']}")
                                        log.info(f"  Out of Service: {region['count_out_of_service']}")
                                        log.info(f"  Total ATMs: {region['total_atms_in_region']}")
                                        log.info(f"  Date: {region['date_creation']}")
                                    log.info("=====================================")
                            else:
                                log.error("Failed to save fifth_graphic data to database")
                        else:
                            log.error("Regional ATM counts table check failed")
                    except Exception as regional_db_error:
                        log.error(f"Error saving fifth_graphic data to database: {str(regional_db_error)}")
                        log.debug("Regional database error details:", exc_info=True)
                else:
                    log.info("Database integration not enabled, skipping fifth_graphic database save")
                
                # Save fifth_graphic data to JSON file for backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_data")
                os.makedirs(save_dir, exist_ok=True)
                regional_json_filename = os.path.join(save_dir, f"regional_atm_data_{timestamp}.json")
                
                with open(regional_json_filename, "w") as f:
                    json.dump({
                        "timestamp": timestamp,
                        "date_request": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                        "fifth_graphic": fifth_graphic_data,
                        "full_reports_response": reports_data
                    }, f, indent=2)
                log.info(f"Fifth_graphic data saved to {regional_json_filename}")
                
            else:
                log.warning("No fifth_graphic data found in reports dashboard response")
                if reports_data and "body" in reports_data:
                    log.info("Available body keys: " + str(list(reports_data["body"].keys())))
        
        except Exception as reports_error:
            log.error(f"Error fetching reports dashboard data: {str(reports_error)}")
            log.debug("Reports dashboard error details:", exc_info=True)
            
        log.info("\nATM Crawler execution completed successfully!")
        return True  # Return True to indicate successful completion

    except KeyboardInterrupt:
        log.warning("Script interrupted by user, exiting gracefully...")
        return False  # Return False for keyboard interrupt
    except Exception as e:
        log.exception("Unexpected error occurred during execution!")
        return False  # Return False for any other exception

if __name__ == "__main__":
    main()