#!/usr/bin/env python3
"""
Database Schema Test Script

This script tests if the database tables have been updated correctly
and confirms that the schema changes in atm_database.py will work.
"""

import logging
import sys
import json
import os
from datetime import datetime
import pytz
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env'):
    load_dotenv('.env')
else:
    load_dotenv('.env_fastapi.example')

# Import the modified database manager
from atm_database import ATMDatabaseManager
from atm_config import DILI_TIMEZONE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_db_tables.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)

def test_regional_data():
    """Test saving to regional_data table"""
    db_manager = ATMDatabaseManager(demo_mode=False)
    
    # Create sample regional data
    sample_data = [
        {
            'unique_request_id': str(uuid4()),
            'region_code': 'TL-DL',
            'count_available': 5,
            'count_warning': 1,
            'count_zombie': 0,
            'count_wounded': 2,
            'count_out_of_service': 3,
            'total_atms_in_region': 11,
            'date_creation': datetime.now(pytz.timezone(DILI_TIMEZONE)),
            'percentage_available': 45.45,
            'percentage_warning': 9.09,
            'percentage_zombie': 0.00,
            'percentage_wounded': 18.18,
            'percentage_out_of_service': 27.27
        }
    ]
    
    log.info("Testing save_regional_data with sample data")
    success = db_manager.save_regional_data(sample_data)
    log.info(f"Save to regional_data result: {success}")
    return success

def test_cash_information():
    """Test saving to terminal_cash_information table"""
    db_manager = ATMDatabaseManager(demo_mode=False)
    
    # Create sample cash information data
    sample_cash_data = [
        {
            'unique_request_id': str(uuid4()),
            'terminal_id': 'ATM001',
            'business_code': 'BUS123',
            'technical_code': 'TECH456',
            'external_id': 'EXT789',
            'retrieval_timestamp': datetime.now(pytz.timezone(DILI_TIMEZONE)),
            'event_date': datetime.now(pytz.timezone(DILI_TIMEZONE)),
            'total_cash_amount': 15000.00,
            'total_currency': 'USD',
            'cassettes_data': [
                {
                    'id': '1',
                    'currency': 'USD',
                    'denomination': 100,
                    'count': 50,
                    'lowCashWarning': False,
                    'error': False
                },
                {
                    'id': '2',
                    'currency': 'USD',
                    'denomination': 50,
                    'count': 200,
                    'lowCashWarning': True,
                    'error': False
                }
            ],
            'raw_cash_data': {
                'timestamp': datetime.now(pytz.timezone(DILI_TIMEZONE)).isoformat(),
                'status': 'OK'
            }
        }
    ]
    
    log.info("Testing save_cash_info with sample data")
    success = db_manager.save_cash_info(sample_cash_data)
    log.info(f"Save to terminal_cash_information result: {success}")
    return success

def main():
    """Run all tests"""
    log.info("Starting database schema tests")
    
    regional_success = test_regional_data()
    cash_success = test_cash_information()
    
    if regional_success and cash_success:
        log.info("All tests passed successfully!")
    else:
        log.error("Some tests failed. Please check the logs for details.")
        
    log.info("Tests completed.")

if __name__ == "__main__":
    main()
