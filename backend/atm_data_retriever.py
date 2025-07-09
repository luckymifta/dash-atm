"""
ATM Data Retrieval Module

Handles all data retrieval operations including regional data,
terminal status, and terminal details from the ATM monitoring system.
"""

import requests
import json
import logging
import time
import os
import subprocess
import platform
from datetime import datetime
from typing import Optional, Dict, List, Any
from tqdm import tqdm
import pytz
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from atm_config import (
    REPORTS_URL, DASHBOARD_URL, PARAMETER_VALUES, 
    COMMON_HEADERS, DEFAULT_TIMEOUT, DILI_TIMEZONE,
    EXPECTED_TERMINAL_IDS, MAX_RETRIES, RETRY_DELAYS
)

log = logging.getLogger(__name__)

class ATMDataRetriever:
    """Handles data retrieval operations for the ATM monitoring system"""
    
    def __init__(self, authenticator, demo_mode: bool = False, total_atms: int = 14):
        self.authenticator = authenticator
        self.demo_mode = demo_mode
        self.total_atms = total_atms
        self.dili_tz = pytz.timezone(DILI_TIMEZONE)
        
        # Use the same session as authenticator
        self.session = authenticator.session
    
    def check_connectivity(self, host: str = "172.31.1.46") -> bool:
        """
        Check network connectivity to the ATM monitoring system using ping
        
        Args:
            host: Host to ping (default: 172.31.1.46)
            
        Returns:
            bool: True if ping successful, False otherwise
        """
        try:
            # Determine ping command based on OS
            if platform.system().lower() == "windows":
                ping_cmd = ["ping", "-n", "3", host]
            else:
                ping_cmd = ["ping", "-c", "3", host]
            
            # Execute ping command
            result = subprocess.run(
                ping_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            
            if success:
                log.info(f"✅ Ping to {host} successful")
            else:
                log.error(f"❌ Ping to {host} failed")
                log.debug(f"Ping output: {result.stdout}")
                log.debug(f"Ping error: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            log.error(f"❌ Ping to {host} timed out")
            return False
        except Exception as e:
            log.error(f"❌ Error during ping to {host}: {str(e)}")
            return False
    
    def fetch_regional_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch regional ATM data from the reports dashboard
        
        Returns:
            List of regional data or None if failed
        """
        if self.demo_mode:
            log.info("Demo mode: Generating sample regional data")
            return [{
                "hc-key": "TL-DL",
                "state_count": {
                    "AVAILABLE": "85.7",
                    "WARNING": "7.1", 
                    "WOUNDED": "7.1",
                    "ZOMBIE": "0.0",
                    "OUT_OF_SERVICE": "0.0"
                }
            }]
        
        if not self.authenticator.is_authenticated():
            log.error("Not authenticated - cannot fetch regional data")
            return None
        
        try:
            regional_payload = {
                "header": {
                    "logged_user": "Lucky.Saputra", 
                    "user_token": self.authenticator.get_token()
                },
                "body": []
            }
            
            # Using PUT request as required by the API
            response = self.session.put(
                REPORTS_URL,
                json=regional_payload,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            regional_data = response.json()
            
            # Extract fifth_graphic data
            if 'body' in regional_data and 'fifth_graphic' in regional_data['body']:
                fifth_graphic = regional_data['body']['fifth_graphic']
                log.info(f"Successfully fetched regional data: {len(fifth_graphic)} regions")
                return fifth_graphic
            else:
                log.warning("No fifth_graphic data found in regional response")
                return None
                
        except requests.exceptions.RequestException as e:
            log.error(f"Request error fetching regional data: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            log.error(f"JSON decode error in regional data: {str(e)}")
            return None
        except Exception as e:
            log.error(f"Unexpected error fetching regional data: {str(e)}")
            return None
    
    def get_terminals_by_status(self, param_value: str) -> List[Dict[str, Any]]:
        """
        Get terminals with a specific status
        
        Args:
            param_value: Status parameter to search for
            
        Returns:
            List of terminals with the specified status
        """
        if self.demo_mode:
            # Generate demo terminals based on status
            demo_terminals = []
            if param_value == "AVAILABLE":
                demo_terminals = [
                    {"terminalId": "83", "issueStateCode": "AVAILABLE"},
                    {"terminalId": "2603", "issueStateCode": "AVAILABLE"}
                ]
            elif param_value == "WOUNDED":
                demo_terminals = [
                    {"terminalId": "2622", "issueStateCode": "HARD"}
                ]
            
            log.info(f"Demo mode: Generated {len(demo_terminals)} terminals for status {param_value}")
            return demo_terminals
        
        if not self.authenticator.is_authenticated():
            log.error(f"Not authenticated - cannot fetch terminals for status {param_value}")
            return []
        
        try:
            dashboard_url = f"{DASHBOARD_URL}&param_value={param_value}"
            
            dashboard_payload = {
                "header": {
                    "logged_user": "Lucky.Saputra",
                    "user_token": self.authenticator.get_token()
                },
                "body": {}
            }
            
            # Using PUT request as required by the API
            response = self.session.put(
                dashboard_url,
                json=dashboard_payload,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            dashboard_data = response.json()
            
            # Extract terminals from response
            if 'body' in dashboard_data and isinstance(dashboard_data['body'], list):
                terminals = dashboard_data['body']
                log.debug(f"Found {len(terminals)} terminals with status {param_value}")
                return terminals
            else:
                log.debug(f"No terminals found with status {param_value}")
                return []
                
        except requests.exceptions.RequestException as e:
            log.error(f"Request error fetching terminals for status {param_value}: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            log.error(f"JSON decode error for status {param_value}: {str(e)}")
            return []
        except Exception as e:
            log.error(f"Unexpected error fetching terminals for status {param_value}: {str(e)}")
            return []
    
    def fetch_terminal_details(self, terminal_id: str, issue_state_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific terminal
        
        Args:
            terminal_id: Terminal ID to fetch details for
            issue_state_code: Issue state code for the terminal
            
        Returns:
            Terminal detail data or None if failed
        """
        if self.demo_mode:
            log.info(f"Demo mode: Generating sample terminal details for {terminal_id}")
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
        
        if not self.authenticator.is_authenticated():
            log.error(f"Not authenticated - cannot fetch details for terminal {terminal_id}")
            return None
        
        try:
            details_url = f"{DASHBOARD_URL}&terminal_id={terminal_id}&issueStateCode={issue_state_code}"
            
            details_payload = {
                "header": {
                    "logged_user": "Lucky.Saputra",
                    "user_token": self.authenticator.get_token()
                },
                "body": {}
            }
            
            # Enhanced retry logic for Windows
            max_retries = MAX_RETRIES.get("windows" if os.name == 'nt' else "default", 2)
            retry_delay = RETRY_DELAYS.get("windows" if os.name == 'nt' else "default", 1.0)
            
            for attempt in range(max_retries):
                try:
                    # Using PUT request as required by the API
                    response = self.session.put(
                        details_url,
                        json=details_payload,
                        headers=COMMON_HEADERS,
                        verify=False,
                        timeout=DEFAULT_TIMEOUT
                    )
                    response.raise_for_status()
                    
                    terminal_data = response.json()
                    
                    # Update token if provided
                    if 'header' in terminal_data and 'user_token' in terminal_data['header']:
                        self.authenticator.user_token = terminal_data['header']['user_token']
                    
                    log.debug(f"Successfully fetched details for terminal {terminal_id}")
                    return terminal_data
                    
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        log.warning(f"Attempt {attempt + 1} failed for terminal {terminal_id}: {str(e)}")
                        time.sleep(retry_delay)
                        continue
                    else:
                        log.error(f"All attempts failed for terminal {terminal_id}: {str(e)}")
                        return None
                        
        except Exception as e:
            log.error(f"Unexpected error fetching terminal details for {terminal_id}: {str(e)}")
            return None
    
    def comprehensive_terminal_search(self) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Discover all terminals using comprehensive search strategy
        
        Returns:
            Tuple of (all discovered terminals, status counts)
        """
        log.info("🔍 Starting comprehensive terminal search...")
        
        all_terminals = []
        found_terminal_ids = set()
        status_counts = {}
        
        for param_value in tqdm(PARAMETER_VALUES, desc="Searching statuses", unit="status"):
            try:
                terminals = self.get_terminals_by_status(param_value)
                status_counts[param_value] = len(terminals)
                
                if terminals:
                    log.info(f"Found {len(terminals)} terminals with status {param_value}")
                    
                    for terminal in terminals:
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
                status_counts[param_value] = 0
                continue
        
        log.info(f"✅ Terminal search completed: Found {len(found_terminal_ids)} unique terminals")
        log.info(f"Terminal IDs: {sorted(found_terminal_ids)}")
        
        # Log status distribution
        for status, count in status_counts.items():
            log.info(f"Status {status}: {count} terminals")
        
        return all_terminals, status_counts
