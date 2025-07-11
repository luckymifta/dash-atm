"""
ATM Cash Information Module

Handles cash information retrieval and processing for ATM terminals.
"""

import requests
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from tqdm import tqdm
import pytz
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from atm_config import (
    CASH_INFO_URL, COMMON_HEADERS, DEFAULT_TIMEOUT, 
    DILI_TIMEZONE, DEMO_CASSETTES
)

log = logging.getLogger(__name__)

class ATMCashProcessor:
    """Handles cash information operations for ATM terminals"""
    
    def __init__(self, authenticator, demo_mode: bool = False):
        self.authenticator = authenticator
        self.demo_mode = demo_mode
        self.dili_tz = pytz.timezone(DILI_TIMEZONE)
        
        # Use the same session as authenticator
        self.session = authenticator.session
    
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
            
            return {
                "header": {"result_code": "000", "result_description": "Success."},
                "body": [{
                    "terminalId": terminal_id,
                    "businessId": "00610",
                    "technicalCode": "00600610",
                    "externalId": "45210",
                    "terminalCashInfo": {
                        "cashInfo": DEMO_CASSETTES,
                        "total": 10840
                    }
                }]
            }
        
        if not self.authenticator.is_authenticated():
            log.error("No authentication token available for cash information retrieval")
            return None
        
        # Construct cash information URL with parameters
        cash_url = f"{CASH_INFO_URL}?number_of_occurrences=30&terminal_type=ATM&terminal_id={terminal_id}&language=EN"
        
        cash_payload = {
            "header": {
                "logged_user": "Lucky.Saputra",
                "user_token": self.authenticator.get_token()
            },
            "body": {}
        }
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                log.debug(f"Fetching cash information for terminal {terminal_id} (attempt {retry_count + 1})")
                
                # Using PUT request as required by the API
                response = self.session.put(
                    cash_url,
                    json=cash_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=DEFAULT_TIMEOUT
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
                    self.authenticator.user_token = header["user_token"]
                
                log.debug(f"✅ Successfully fetched cash information for terminal {terminal_id}")
                return cash_data
                
            except requests.exceptions.RequestException as ex:
                log.warning(f"Request failed for terminal {terminal_id} (Attempt {retry_count + 1}): {str(ex)}")
                
                # Check if this might be a token expiration issue
                if hasattr(ex, 'response') and ex.response is not None and ex.response.status_code == 401:
                    log.warning("Token may have expired, attempting to refresh...")
                    if self.authenticator.refresh_token():
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
            
            # Create final record (removed unique_request_id as DB auto-generates)
            record = {
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
                'cassette_count': len(processed_cassettes),
                'has_low_cash_warning': has_low_cash_warning,
                'has_cash_errors': has_cash_errors,
                'is_null_record': False,
                'null_reason': None
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
    
    def retrieve_cash_for_terminals(self, terminals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve cash information for a list of terminals
        
        Args:
            terminals: List of terminal dictionaries
            
        Returns:
            List of processed cash information records
        """
        cash_records = []
        
        if not terminals:
            log.warning("No terminals provided for cash information retrieval")
            return cash_records
        
        log.info(f"Retrieving cash information for {len(terminals)} terminals...")
        
        # Use a progress bar for cash information retrieval
        for terminal in tqdm(terminals, desc="Fetching cash information", unit="terminal"):
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
        
        log.info(f"✅ Cash information retrieved for {len(cash_records)} terminals")
        return cash_records
