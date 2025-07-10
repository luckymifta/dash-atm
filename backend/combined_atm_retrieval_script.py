#!/usr/bin/env python3
"""
ATM Data Retrieval Orchestration Script

This is the main orchestration script that coordinates all ATM data retrieval
operations using the modular components. It replaces the previous monolithic
combined_atm_retrieval_script_integrated.py with a cleaner, more maintainable
architecture.

Features:
- Modular design with separate modules for each responsibility
- Comprehensive error handling and logging
- Support for both demo and production modes
- Cash information retrieval and processing
- Regional and terminal details retrieval
- Database storage with proper transaction handling
- Configurable retry logic and timeout settings
- Continuous operation mode with scheduling support
"""

import argparse
import logging
import sys
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
from collections import deque
import urllib3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress InsecureRequestWarning globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import our modular components
from atm_config import (
    DILI_TIMEZONE, 
    EXPECTED_TERMINAL_IDS,
    PARAMETER_VALUES,
    get_db_config
)
from atm_auth import ATMAuthenticator
from atm_data_retriever import ATMDataRetriever
from atm_cash_processor import ATMCashProcessor
from atm_data_processor import ATMDataProcessor
from atm_database import ATMDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atm_retrieval.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)

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

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    log.info("Received shutdown signal, stopping continuous operation...")
    stop_flag.set()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class ATMOrchestrator:
    """Main orchestrator class that coordinates all ATM data retrieval operations"""
    
    def __init__(self, demo_mode: bool = False, save_to_db: bool = True):
        """
        Initialize the orchestrator
        
        Args:
            demo_mode: Whether to run in demo mode (uses demo data)
            save_to_db: Whether to save data to database
        """
        self.demo_mode = demo_mode
        self.save_to_db = save_to_db
        
        # Initialize components
        self.authenticator = ATMAuthenticator(demo_mode=demo_mode)
        self.data_retriever = ATMDataRetriever(authenticator=self.authenticator, demo_mode=demo_mode)
        self.cash_processor = ATMCashProcessor(authenticator=self.authenticator, demo_mode=demo_mode)
        self.data_processor = ATMDataProcessor()
        self.database_manager = ATMDatabaseManager(demo_mode=demo_mode)
        
        # State tracking
        self.session = None
        self.all_data = {}
        
        log.info(f"ATM Orchestrator initialized - Demo Mode: {demo_mode}, Save to DB: {save_to_db}")
    
    def run_full_retrieval(self, include_cash: bool = True, use_new_tables: bool = False) -> bool:
        """
        Run full ATM data retrieval process
        
        Args:
            include_cash: Whether to include cash information retrieval
            use_new_tables: Whether to use new database tables
            
        Returns:
            bool: True if successful, False otherwise
        """
        log.info("Starting full ATM data retrieval process")
        start_time = time.time()
        
        try:
            # Step 1: Authentication
            log.info("Step 1: Authenticating...")
            auth_success = self.authenticator.authenticate()
            if not auth_success:
                log.error("Authentication failed - cannot proceed")
                return False
            log.info("Authentication successful")
            
            # Step 2: Retrieve regional data
            log.info("Step 2: Retrieving regional data...")
            regional_data = self.data_retriever.fetch_regional_data()
            if not regional_data:
                log.error("ERROR: Failed to retrieve regional data")
                return False
            log.info(f"SUCCESS: Retrieved {len(regional_data)} regional records")
            
            # Step 3: Process regional data
            log.info("Step 3: Processing regional data...")
            processed_regional = self.data_processor.process_regional_data(regional_data)
            
            # Step 4: Retrieve terminal status for comprehensive search
            log.info("Step 4: Performing comprehensive terminal search...")
            all_terminals, status_counts = self.data_retriever.comprehensive_terminal_search()
            log.info(f"SUCCESS: Found {len(all_terminals)} terminals")
            
            # Step 5: Retrieve terminal details for each terminal
            log.info("Step 5: Retrieving terminal details...")
            all_terminal_details = []
            for terminal in all_terminals:
                terminal_id = terminal.get('terminalId')
                issue_state_code = terminal.get('issueStateCode', 'HARD')
                
                if terminal_id:
                    terminal_data = self.data_retriever.fetch_terminal_details(terminal_id, issue_state_code)
                    if terminal_data:
                        details = self.data_processor.process_terminal_details(
                            terminal_data, terminal_id, terminal.get('fetched_status', 'UNKNOWN')
                        )
                        all_terminal_details.extend(details)
            
            log.info(f"SUCCESS: Retrieved {len(all_terminal_details)} terminal details")
            log.info(f"Retrieved {len(all_terminal_details)} terminal details")
            
            # Recalculate regional data based on actual terminal details
            log.info("Recalculating regional data based on actual terminal details...")
            recalculated_regional = self.data_processor.recalculate_regional_data_from_terminals(all_terminal_details)
            
            # Store processed data
            self.all_data = {
                'regional_data': recalculated_regional,  # Use recalculated data instead of API-provided data
                'terminal_details': all_terminal_details,
                'raw_regional_data': regional_data,
                'raw_terminal_data': all_terminals
            }
            
            # Step 6: Retrieve cash information (if requested)
            if include_cash:
                log.info("Step 6: Retrieving cash information...")
                cash_records = self.cash_processor.retrieve_cash_for_terminals(all_terminals)
                self.all_data['cash_info'] = cash_records
                log.info(f"SUCCESS: Retrieved cash information for {len(cash_records)} terminals")
            
            # Step 7: Save to database (if requested)
            if self.save_to_db:
                log.info("Step 7: Saving data to database...")
                save_success = self.database_manager.save_all_data(self.all_data, use_new_tables)
                if not save_success:
                    log.error("ERROR: Failed to save data to database")
                    return False
                log.info("SUCCESS: Data saved to database successfully")
            
            # Step 8: Generate summary
            self.generate_summary()
            
            # Step 9: Save to JSON file
            self.save_to_json()
            
            elapsed_time = time.time() - start_time
            log.info(f"SUCCESS: Full retrieval process completed in {elapsed_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            log.error(f"ERROR: Full retrieval process failed: {e}")
            return False
        finally:
            # Always logout
            if self.authenticator.user_token:
                self.authenticator.logout()
    
    def generate_summary(self):
        """Generate and log a summary of retrieved data"""
        log.info("=== ATM Data Retrieval Summary ===")
        
        if 'regional_data' in self.all_data:
            log.info(f"Regional Data: {len(self.all_data['regional_data'])} regions")
            
        if 'terminal_details' in self.all_data:
            log.info(f"Terminal Details: {len(self.all_data['terminal_details'])} terminals")
            
            # Check for expected terminals
            retrieved_ids = {str(t.get('terminalId')) for t in self.all_data['terminal_details'] if t.get('terminalId')}
            expected_ids = set(EXPECTED_TERMINAL_IDS)
            missing_ids = expected_ids - retrieved_ids
            
            if missing_ids:
                log.warning(f"MISSING expected terminals: {sorted(missing_ids)}")
            else:
                log.info("SUCCESS: All expected terminals retrieved")
        
        if 'cash_info' in self.all_data:
            log.info(f"Cash Information: {len(self.all_data['cash_info'])} cash records")
        
        # Status summary
        if 'terminal_details' in self.all_data:
            status_counts = {}
            for terminal in self.all_data['terminal_details']:
                status = terminal.get('fetched_status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            log.info("Terminal Status Summary:")
            for status, count in sorted(status_counts.items()):
                log.info(f"  {status}: {count}")
        
        log.info("=== End Summary ===")
    
    def save_to_json(self, filename: Optional[str] = None):
        """
        Save all retrieved data to JSON file
        
        Args:
            filename: Optional filename, if not provided will use timestamp
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"atm_data_{timestamp}.json"
        
        try:
            # Convert datetime objects to strings for JSON serialization
            json_data = self._prepare_data_for_json(self.all_data)
            
            filepath = os.path.join(os.getcwd(), filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            log.info(f"SUCCESS: Data saved to JSON file: {filepath}")
            
        except Exception as e:
            log.error(f"ERROR: Failed to save JSON file: {e}")
    
    def _prepare_data_for_json(self, data):
        """
        Prepare data for JSON serialization by converting datetime objects
        
        Args:
            data: Data to prepare
            
        Returns:
            JSON-serializable data
        """
        if isinstance(data, dict):
            return {k: self._prepare_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_data_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def get_terminal_status_only(self) -> Dict[str, Any]:
        """
        Quick method to get just terminal status information
        
        Returns:
            Dict containing terminal status information
        """
        log.info("Getting terminal status information only")
        
        try:
            # Authenticate
            auth_success = self.authenticator.authenticate()
            if not auth_success:
                return {}
            
            # Get basic terminal info
            all_terminals, status_counts = self.data_retriever.comprehensive_terminal_search()
            if not all_terminals:
                log.warning("WARNING: No terminals found")
                return {}
            
            # Process and return status info
            status_info = {
                'total_terminals': len(all_terminals),
                'status_counts': status_counts,
                'timestamp': datetime.now().isoformat(),
                'terminals': [
                    {
                        'terminal_id': t.get('terminalId'),
                        'status': t.get('issueStateName'),
                        'location': t.get('location', '')
                    }
                    for t in all_terminals
                ]
            }
            
            log.info(f"SUCCESS: Retrieved status for {len(all_terminals)} terminals")
            return status_info
            
        except Exception as e:
            log.error(f"ERROR: Failed to get terminal status: {e}")
            return {}
        finally:
            if self.authenticator.user_token:
                self.authenticator.logout()
    
    def continuous_operation(self, interval_minutes: int = 15):
        """
        Run the ATM data retrieval process in continuous mode, with specified interval
        
        Args:
            interval_minutes: Time interval between retrieval cycles (in minutes)
        """
        log.info(f"Starting continuous operation mode - interval: {interval_minutes} minutes")
        execution_stats['start_time'] = datetime.now()
        
        while not stop_flag.is_set():
            log.info("=== Starting new retrieval cycle ===")
            success = self.run_full_retrieval(include_cash=True, use_new_tables=False)
            
            # Update execution statistics
            execution_stats['total_cycles'] += 1
            if success:
                execution_stats['successful_cycles'] += 1
                execution_stats['last_success'] = datetime.now()
                log.info("SUCCESS: Retrieval cycle completed successfully")
            else:
                execution_stats['failed_cycles'] += 1
                log.error("ERROR: Retrieval cycle failed")
            
            # Log execution statistics
            self.log_execution_statistics()
            
            # Sleep until next cycle
            if not stop_flag.is_set():
                log.info(f"Waiting for {interval_minutes} minutes until next cycle")
                time.sleep(interval_minutes * 60)
        
        log.info("Continuous operation stopped by user")

    def log_execution_statistics(self):
        """Log the execution statistics"""
        elapsed_time = datetime.now() - execution_stats['start_time']
        log.info(f"=== Execution Statistics ===")
        log.info(f"Total Cycles: {execution_stats['total_cycles']}")
        log.info(f"Successful Cycles: {execution_stats['successful_cycles']}")
        log.info(f"Failed Cycles: {execution_stats['failed_cycles']}")
        log.info(f"Connection Failures: {execution_stats['connection_failures']}")
        log.info(f"Uptime: {str(elapsed_time).split('.')[0]}")  # Exclude milliseconds
        log.info(f"Last Success: {execution_stats['last_success']}")
        log.info(f"Cycle History (last 50): {list(execution_stats['cycle_history'])}")
        log.info("=============================")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='ATM Data Retrieval Orchestration Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --demo                    # Run in demo mode
  %(prog)s --no-cash                 # Run without cash information
  %(prog)s --no-db                   # Run without database save
  %(prog)s --status-only             # Get just terminal status
  %(prog)s --use-new-tables          # Use new database tables
  %(prog)s --continuous               # Run in continuous operation mode
        """
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (uses demo data instead of real API calls)'
    )
    
    parser.add_argument(
        '--no-cash',
        action='store_true',
        help='Skip cash information retrieval'
    )
    
    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Skip database save operation'
    )
    
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Get terminal status information only (quick mode)'
    )
    
    parser.add_argument(
        '--use-new-tables',
        action='store_true',
        help='Use new database tables with enhanced schema'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output JSON filename (default: auto-generated with timestamp)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run in continuous operation mode'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Interval in minutes for continuous operation (default: 15)'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create orchestrator
    orchestrator = ATMOrchestrator(
        demo_mode=args.demo,
        save_to_db=not args.no_db
    )
    
    # Run appropriate operation
    if args.status_only:
        log.info("Running in status-only mode")
        status_info = orchestrator.get_terminal_status_only()
        if status_info:
            print(json.dumps(status_info, indent=2))
        return 0 if status_info else 1
    elif args.continuous:
        log.info("Running in continuous operation mode")
        orchestrator.continuous_operation(interval_minutes=args.interval)
        return 0
    else:
        log.info("Running full data retrieval")
        success = orchestrator.run_full_retrieval(
            include_cash=not args.no_cash,
            use_new_tables=args.use_new_tables
        )
        
        if success and args.output_file:
            orchestrator.save_to_json(args.output_file)
        
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())