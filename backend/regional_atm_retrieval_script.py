#!/usr/bin/env python3
"""
Regional ATM Data Retrieval Script

A complete script to retrieve ATM regional data from login until retrieving the response 
with the same structure as the `regional_atm_counts` database table.

This script handles:
1. Authentication/login to the ATM monitoring system
2. Retrieving fifth_graphic regional data from the reports dashboard
3. Processing and converting percentage data to actual counts
4. Formatting data to match the regional_atm_counts table structure
5. Optional database saving with rollback capability
6. Comprehensive error handling and retry logic

Usage:
    python regional_atm_retrieval_script.py [--demo] [--save-to-db] [--total-atms 14]
"""

import requests
import urllib3
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
import argparse
import pytz

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s",
    handlers=[
        logging.FileHandler("regional_atm_retrieval.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("RegionalATMRetrieval")

# Try to import database connector if available
try:
    import db_connector
    DB_AVAILABLE = True
    log.info("Database connector available")
except ImportError:
    db_connector = None
    DB_AVAILABLE = False
    log.warning("Database connector not available - database operations will be skipped")

# Configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
REPORTS_URL = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status"

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

# Constants for table structure mapping
SUPPORTED_STATES = {
    'AVAILABLE': 'count_available',
    'WARNING': 'count_warning',
    'ZOMBIE': 'count_zombie',
    'WOUNDED': 'count_wounded',
    'OUT_OF_SERVICE': 'count_out_of_service'
}

class RegionalATMRetriever:
    """Main class for handling regional ATM data retrieval"""
    
    def __init__(self, demo_mode: bool = False, total_atms: int = 14):
        """
        Initialize the retriever
        
        Args:
            demo_mode: Whether to use demo mode (no actual network requests)
            total_atms: Total number of ATMs for percentage to count conversion
        """
        self.demo_mode = demo_mode
        self.total_atms = total_atms
        self.session = requests.Session()
        self.user_token = None
        
        # Log timezone info for clarity
        dili_tz = pytz.timezone('Asia/Dili')  # UTC+9
        current_time = datetime.now(dili_tz)
        log.info(f"Initialized RegionalATMRetriever - Demo: {demo_mode}, Total ATMs: {total_atms}")
        log.info(f"Using Dili timezone (UTC+9) for timestamps: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    
    def check_connectivity(self, timeout: int = 10) -> bool:
        """Check connectivity to the target system"""
        if self.demo_mode:
            log.info("Demo mode: Skipping connectivity check")
            return True
            
        try:
            log.info(f"Testing connectivity to {LOGIN_URL}")
            response = requests.head(LOGIN_URL, timeout=timeout, verify=False)
            log.info(f"Connectivity successful: HTTP {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Connectivity test failed: {str(e)}")
            return False
    
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
                    log.info(f"User token extracted with key '{key}'")
                    break
            
            # Method 2: From header field
            if not user_token and 'header' in login_data:
                user_token = login_data['header'].get('user_token')
                if user_token:
                    log.info("User token extracted from 'header' field")
            
            if user_token:
                self.user_token = user_token
                log.info(f"Authentication successful - Token length: {len(user_token)} characters")
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
    
    def fetch_regional_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch regional ATM data from the reports dashboard
        
        Returns:
            List containing fifth_graphic data or None if failed
        """
        if self.demo_mode:
            log.info("Demo mode: Generating sample regional data")
            return [
                {
                    "hc-key": "TL-DL",
                    "state_count": {
                        "AVAILABLE": "0.78571427",
                        "WOUNDED": "0.14285714",
                        "WARNING": "0.07142857"
                    }
                },
                {
                    "hc-key": "TL-AN",
                    "state_count": {
                        "AVAILABLE": "0.85714286",
                        "OUT_OF_SERVICE": "0.07142857",
                        "ZOMBIE": "0.07142857"
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
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                log.info(f"Requesting regional data... (Attempt {retry_count + 1}/{max_retries})")
                response = self.session.put(
                    REPORTS_URL,
                    json=reports_payload,
                    headers=COMMON_HEADERS,
                    verify=False,
                    timeout=30
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
                    log.info("Retrying in 5 seconds...")
                    time.sleep(5)
                
            except json.JSONDecodeError as e:
                log.error(f"Response not valid JSON (Attempt {retry_count + 1}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
        
        log.error("All attempts failed to retrieve regional data")
        return None
    
    def process_regional_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process raw fifth_graphic data and convert to regional_atm_counts table structure
        
        Args:
            raw_data: Raw fifth_graphic data from API response
            
        Returns:
            List of processed records matching regional_atm_counts table structure
        """
        if not raw_data:
            log.warning("No raw data provided for processing")
            return []
        
        processed_records = []
        dili_tz = pytz.timezone('Asia/Dili')  # Use Dili time for database storage
        current_time = datetime.now(dili_tz)
        
        log.info(f"Processing regional data for {len(raw_data)} regions")
        log.info(f"Using Dili time for database storage: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        
        for region_data in raw_data:
            region_code = region_data.get("hc-key", "UNKNOWN")
            state_count = region_data.get("state_count", {})
            
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
    
    def save_to_database(self, processed_data: List[Dict[str, Any]]) -> bool:
        """
        Save processed data to the regional_atm_counts database table
        
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
    
    def retrieve_and_process(self, save_to_db: bool = False) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
        """
        Complete flow: authenticate, retrieve, and process regional ATM data
        
        Args:
            save_to_db: Whether to save processed data to database
            
        Returns:
            Tuple of (success: bool, processed_data: List or None)
        """
        log.info("=" * 80)
        log.info("STARTING REGIONAL ATM DATA RETRIEVAL")
        log.info("=" * 80)
        
        # Step 1: Check connectivity (unless demo mode)
        if not self.demo_mode:
            if not self.check_connectivity():
                log.error("Connectivity check failed - aborting")
                return False, None
        
        # Step 2: Authenticate
        if not self.authenticate():
            log.error("Authentication failed - aborting")
            return False, None
        
        # Step 3: Fetch regional data
        raw_data = self.fetch_regional_data()
        if not raw_data:
            log.error("Failed to retrieve regional data - aborting")
            return False, None
        
        # Step 4: Process the data
        processed_data = self.process_regional_data(raw_data)
        if not processed_data:
            log.error("Failed to process regional data - aborting")
            return False, None
        
        # Step 5: Save to database if requested
        if save_to_db:
            save_success = self.save_to_database(processed_data)
            if save_success:
                log.info("Data successfully saved to database")
            else:
                log.warning("Database save failed, but processed data is still available")
        
        log.info("=" * 80)
        log.info("REGIONAL ATM DATA RETRIEVAL COMPLETED SUCCESSFULLY")
        log.info("=" * 80)
        
        return True, processed_data


def display_results(processed_data: List[Dict[str, Any]]) -> None:
    """Display the processed results in a formatted way"""
    if not processed_data:
        print("No data to display")
        return
    
    print("\n" + "=" * 100)
    print("REGIONAL ATM COUNTS DATA (matching regional_atm_counts table structure)")
    print("=" * 100)
    
    print(f"{'Region':<10} {'Available':<10} {'Warning':<8} {'Zombie':<8} {'Wounded':<8} {'Out/Svc':<8} {'Total':<6} {'Timestamp (UTC+9)':<25}")
    print("-" * 105)
    
    for record in processed_data:
        timestamp_str = record['date_creation'].strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"{record['region_code']:<10} "
              f"{record['count_available']:3d} ({record['percentage_available']*100:5.1f}%) "
              f"{record['count_warning']:3d}      "
              f"{record['count_zombie']:3d}      "
              f"{record['count_wounded']:3d}      "
              f"{record['count_out_of_service']:3d}      "
              f"{record['total_atms_in_region']:3d}    "
              f"{timestamp_str}")
    
    print("-" * 100)
    print(f"Total regions processed: {len(processed_data)}")


def save_to_json(processed_data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
    """Save processed data to JSON file"""
    dili_tz = pytz.timezone('Asia/Dili')  # Asia/Dili is UTC+9 for Timor-Leste
    current_time = datetime.now(dili_tz)
    
    if filename is None:
        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        filename = f"regional_atm_data_{timestamp}.json"
    
    # Convert datetime objects to strings for JSON serialization
    json_data = []
    for record in processed_data:
        json_record = record.copy()
        json_record['date_creation'] = json_record['date_creation'].isoformat()
        json_data.append(json_record)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "retrieval_timestamp": current_time.isoformat(),
            "total_regions": len(json_data),
            "regional_data": json_data
        }, f, indent=2)
    
    log.info(f"Data saved to JSON file: {filename}")
    return filename


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Regional ATM Data Retrieval Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python regional_atm_retrieval_script.py                    # Live mode, display only
  python regional_atm_retrieval_script.py --demo             # Demo mode for testing
  python regional_atm_retrieval_script.py --save-to-db       # Live mode with database save
  python regional_atm_retrieval_script.py --demo --save-to-db --total-atms 20
        """
    )
    
    parser.add_argument('--demo', action='store_true', 
                       help='Run in demo mode (no actual network requests)')
    parser.add_argument('--save-to-db', action='store_true',
                       help='Save processed data to database')
    parser.add_argument('--total-atms', type=int, default=14,
                       help='Total number of ATMs for percentage to count conversion (default: 14)')
    parser.add_argument('--save-json', action='store_true',
                       help='Save processed data to JSON file')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce logging output (errors and warnings only)')
    
    args = parser.parse_args()
    
    # Adjust logging level if quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Create retriever instance
    retriever = RegionalATMRetriever(demo_mode=args.demo, total_atms=args.total_atms)
    
    try:
        # Execute the complete retrieval and processing flow
        success, processed_data = retriever.retrieve_and_process(save_to_db=args.save_to_db)
        
        if success and processed_data:
            # Display results
            display_results(processed_data)
            
            # Save to JSON if requested
            if args.save_json:
                json_filename = save_to_json(processed_data)
                print(f"\nData saved to: {json_filename}")
            
            print(f"\n✅ SUCCESS: Retrieved and processed data for {len(processed_data)} regions")
            
            if args.save_to_db and DB_AVAILABLE:
                print("✅ Data saved to database (regional_atm_counts table)")
            elif args.save_to_db and not DB_AVAILABLE:
                print("⚠️  Database not available - data not saved to database")
            
            return 0
        else:
            print("\n❌ FAILED: Unable to retrieve or process regional data")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        log.debug("Error details:", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
