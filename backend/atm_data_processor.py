"""
ATM Data Processing Module

Handles processing of raw ATM data into structured formats
suitable for database storage and analysis.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any
import pytz

from atm_config import DILI_TIMEZONE, EXPECTED_TERMINAL_IDS

log = logging.getLogger(__name__)

class ATMDataProcessor:
    """Processes raw ATM data into structured formats"""
    
    def __init__(self, total_atms: int = 14):
        self.total_atms = total_atms
        self.dili_tz = pytz.timezone(DILI_TIMEZONE)
    
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
        current_time = datetime.now(self.dili_tz)
        
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
                    # Check if percentage is already in decimal form (less than 1)
                    percentage_val = float(percentage_str)
                    if percentage_val > 1.0:
                        # Value is in percent form (e.g., 85.7)
                        percentage = percentage_val / 100.0  
                    else:
                        # Value is already in decimal form (e.g., 0.857)
                        percentage = percentage_val
                    
                    count = int(round(percentage * self.total_atms))
                    
                    # Map state names to count fields
                    if state == "AVAILABLE":
                        counts['count_available'] = count
                    elif state == "WARNING":
                        counts['count_warning'] = count
                    elif state in ["WOUNDED", "HARD", "CASH"]:
                        counts['count_wounded'] += count
                    elif state == "ZOMBIE":
                        counts['count_zombie'] = count
                    elif state in ["OUT_OF_SERVICE", "UNAVAILABLE"]:
                        counts['count_out_of_service'] += count
                    
                    log.debug(f"  {state}: {percentage * 100:.1f}% = {count} ATMs")
                        
                except (ValueError, TypeError) as e:
                    log.warning(f"Error converting percentage for {state}: {percentage_str} - {str(e)}")
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
    
    def process_terminal_details(self, terminal_data: Dict[str, Any], 
                                terminal_id: str, fetched_status: str) -> List[Dict[str, Any]]:
        """
        Process terminal details data from API response
        
        Args:
            terminal_data: Raw terminal data from API
            terminal_id: Terminal ID being processed
            fetched_status: Status this terminal was fetched under
            
        Returns:
            List of processed terminal detail records
        """
        processed_details = []
        current_time = datetime.now(self.dili_tz)
        unique_request_id = str(uuid.uuid4())
        
        # Extract details from response body
        body = terminal_data.get('body', [])
        if not body or not isinstance(body, list):
            log.warning(f"No body data found for terminal {terminal_id}")
            return processed_details
        
        for item in body:
            if not isinstance(item, dict):
                continue
            
            # Get the actual status from the API response (issueStateName)
            actual_status = item.get('issueStateName', '')
            
            # Use the actual status from the API as the authoritative status
            # If it's empty, fall back to the fetched_status
            final_status = actual_status if actual_status else fetched_status
            
            # Create processed terminal detail record
            detail_record = {
                'unique_request_id': unique_request_id,
                'terminalId': item.get('terminalId', terminal_id),
                'location': item.get('location', ''),
                'issueStateName': actual_status,
                'serialNumber': item.get('serialNumber', ''),
                'retrievedDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'year': item.get('year', ''),
                'month': item.get('month', ''),
                'day': item.get('day', ''),
                'externalFaultId': item.get('externalFaultId', ''),
                'agentErrorDescription': item.get('agentErrorDescription', ''),
                'creationDate': item.get('creationDate', ''),
                'fetched_status': final_status  # Set fetched_status to match issueStateName
            }
            
            processed_details.append(detail_record)
        
        return processed_details
    
    def generate_failure_data(self, failure_type: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate failure data for all ATMs when system failures occur
        
        Args:
            failure_type: Type of failure ('NETWORK_CONNECTIVITY_FAILURE' or 'AUTHENTICATION_FAILURE')
            
        Returns:
            Tuple of (regional_data, terminal_details_data)
        """
        log.info(f"Generating {failure_type} data for failover mode")
        
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
        terminal_details_data = []
        
        for terminal_id in EXPECTED_TERMINAL_IDS:
            # Determine error details based on failure type
            if failure_type == "NETWORK_CONNECTIVITY_FAILURE":
                location = f"Connection Failed - Terminal {terminal_id}"
                serial_number = "CONNECTION_FAILED"
                fault_id = "CONN_FAIL"
                error_description = "Connection failure to monitoring system"
            else:  # AUTHENTICATION_FAILURE
                location = f"Authentication Failed - Terminal {terminal_id}"
                serial_number = "AUTH_FAILED"
                fault_id = "AUTH_FAIL"
                error_description = "Authentication failure to monitoring system"
            
            terminal_detail = {
                'unique_request_id': str(uuid.uuid4()),
                'terminalId': terminal_id,
                'location': location,
                'issueStateName': "OUT_OF_SERVICE",
                'serialNumber': serial_number,
                'retrievedDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'year': "",
                'month': "",
                'day': "",
                'externalFaultId': fault_id,
                'agentErrorDescription': error_description,
                'creationDate': current_time.strftime('%d:%m:%Y %H:%M:%S'),
                'fetched_status': "OUT_OF_SERVICE"
            }
            terminal_details_data.append(terminal_detail)
        
        log.info(f"Generated {failure_type} data for {len(terminal_details_data)} terminals")
        return regional_data, terminal_details_data
    
    def create_summary(self, all_data: Dict[str, Any], status_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Create summary data for the retrieval results
        
        Args:
            all_data: All retrieved data
            status_counts: Terminal status counts
            
        Returns:
            Summary dictionary
        """
        # Map parameter values to proper status names for summary
        status_name_mapping = {
            "WOUNDED": "WOUNDED",
            "HARD": "WOUNDED",
            "CASH": "WOUNDED",
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
        summary = {
            "total_regions": len(all_data.get("regional_data", [])),
            "total_terminals": sum(status_counts.values()) if status_counts else 0,
            "total_terminal_details": len(all_data.get("terminal_details_data", [])),
            "status_counts": summary_status_counts,
            "collection_note": "Enhanced retrieval: regional data, terminal details, and cash information collected"
        }
        
        # Add cash information count if available
        if "cash_information_data" in all_data:
            summary["total_cash_records"] = len(all_data["cash_information_data"])
        
        return summary
    
    def recalculate_regional_data_from_terminals(self, terminal_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Recalculate regional data based on actual terminal details
        
        Args:
            terminal_details: List of processed terminal details
            
        Returns:
            Updated regional data with accurate counts and percentages
        """
        if not terminal_details:
            log.warning("No terminal details provided for regional data recalculation")
            return []
        
        # Count terminals by status
        counts = {
            'count_available': 0,
            'count_warning': 0,
            'count_zombie': 0,
            'count_wounded': 0,
            'count_out_of_service': 0
        }
        
        # Count terminals by status
        for terminal in terminal_details:
            # Use fetched_status as the source of truth (it's now consistent with issueStateName)
            status = terminal.get('fetched_status', 'UNKNOWN')
            
            # Map the status to the appropriate counter
            if status == "AVAILABLE":
                counts['count_available'] += 1
            elif status == "WARNING":
                counts['count_warning'] += 1
            elif status in ["WOUNDED", "HARD", "CASH"]:
                counts['count_wounded'] += 1
            elif status == "ZOMBIE":
                counts['count_zombie'] += 1
            elif status in ["OUT_OF_SERVICE", "UNAVAILABLE"]:
                counts['count_out_of_service'] += 1
            else:
                log.warning(f"Unknown status: {status} for terminal {terminal.get('terminalId')}")
                # Default to wounded for unknown statuses
                counts['count_wounded'] += 1
        
        # Calculate total terminals
        total_terminals = sum(counts.values())
        
        # Calculate percentages
        percentages = {}
        for status_key, count in counts.items():
            percentage_key = status_key.replace('count_', 'percentage_')
            percentages[percentage_key] = round(count / total_terminals * 100, 1) if total_terminals > 0 else 0.0
        
        # Create regional record
        current_time = datetime.now(self.dili_tz)
        
        regional_record = {
            'unique_request_id': str(uuid.uuid4()),
            'region_code': 'TL-DL',
            'date_creation': current_time.isoformat(),
            'total_atms_in_region': total_terminals,
            **counts,
            **percentages
        }
        
        log.info(f"✅ Recalculated regional data based on {total_terminals} terminals:")
        log.info(f"  Available: {counts['count_available']} ({percentages['percentage_available']}%)")
        log.info(f"  Warning: {counts['count_warning']} ({percentages['percentage_warning']}%)")
        log.info(f"  Wounded: {counts['count_wounded']} ({percentages['percentage_wounded']}%)")
        log.info(f"  Zombie: {counts['count_zombie']} ({percentages['percentage_zombie']}%)")
        log.info(f"  Out of Service: {counts['count_out_of_service']} ({percentages['percentage_out_of_service']}%)")
        
        # Add extra log with terminal statuses for verification
        log.info("Terminal status breakdown:")
        status_breakdown = {}
        for terminal in terminal_details:
            terminal_id = terminal.get('terminalId', 'UNKNOWN')
            status = terminal.get('fetched_status', 'UNKNOWN')
            log.debug(f"  Terminal {terminal_id}: {status}")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        for status, count in sorted(status_breakdown.items()):
            log.info(f"  {status}: {count} terminals")
        
        return [regional_record]
