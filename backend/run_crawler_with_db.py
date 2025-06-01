#!/usr/bin/env python3
# run_crawler_with_db.py - Run the ATM crawler with database integration

import os
import sys
import argparse
import logging
import time
import requests
from datetime import datetime
import atm_crawler_complete
import db_connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("crawler_with_db.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("CrawlerRunner")

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    log.info("Environment variables loaded from .env file")
except ImportError:
    log.warning("python-dotenv not installed. Using environment variables directly.")

# Login retry configuration
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGIN_RETRY_DELAY = 900  # 15 minutes in seconds
MAIN_LOOP_DELAY = 3600   # 1 hour in seconds

# Enhanced retry configuration
MAX_LOGIN_RETRIES = 5
LOGIN_RETRY_BASE_DELAY = 60  # Base delay in seconds
LOGIN_RETRY_MAX_DELAY = 900  # Maximum delay in seconds
MAX_CONSECUTIVE_FAILURES = 10  # Maximum consecutive failures before switching to demo mode
DEMO_MODE_FALLBACK_DELAY = 1800  # 30 minutes in seconds

def calculate_retry_delay(retry_count):
    """Calculate exponential backoff delay with jitter"""
    import random
    base_delay = min(LOGIN_RETRY_BASE_DELAY * (2 ** retry_count), LOGIN_RETRY_MAX_DELAY)
    jitter = random.uniform(0.8, 1.2)  # Add 20% jitter
    return int(base_delay * jitter)

def is_login_failure(error_msg):
    """Determine if an error is specifically a login failure"""
    login_error_patterns = [
        "login failed",
        "authentication failed", 
        "invalid credentials",
        "unauthorized",
        "403",
        "401",
        "user_token",
        "login connectivity"
    ]
    return any(pattern.lower() in str(error_msg).lower() for pattern in login_error_patterns)

def test_login_connectivity():
    """Test if we can successfully login to the target system"""
    try:
        log.info(f"Testing login connectivity to {LOGIN_URL}")
        
        # Use the same login credentials and headers as the main crawler
        login_payload = {
            "user_name": "Lucky.Saputra",
            "password": "TimlesMon2024"
        }
        
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
        
        # Create a session and attempt login
        session = requests.Session()
        response = session.post(
            LOGIN_URL,
            json=login_payload,
            headers=common_headers,
            verify=False,
            timeout=30
        )
        
        # Check if login was successful
        response.raise_for_status()
        login_json = response.json()
        
        # Check if we can extract a user token
        user_token = None
        for key in ['user_token', 'token']:
            if key in login_json:
                user_token = login_json[key]
                break
        
        if not user_token:
            # Check 'header' field as fallback
            user_token = login_json.get("header", {}).get("user_token")
        
        if user_token:
            log.info(f"Login test successful - token extracted: {user_token[:20]}...")
            return True
        else:
            log.error("Login test failed - unable to extract user token from response")
            return False
            
    except requests.exceptions.RequestException as e:
        log.error(f"Login connectivity test failed - Network/HTTP error: {str(e)}")
        return False
    except ValueError as e:
        log.error(f"Login connectivity test failed - JSON parsing error: {str(e)}")
        return False
    except Exception as e:
        log.error(f"Login connectivity test failed - Unexpected error: {str(e)}")
        return False

def wait_for_login_connectivity():
    """Wait until login connectivity is restored, retrying every 15 minutes"""
    while True:
        if test_login_connectivity():
            log.info("Login connectivity restored successfully")
            return True
        
        log.warning(f"Failed to login to {LOGIN_URL}")
        log.info(f"Retrying login in {LOGIN_RETRY_DELAY/60:.0f} minutes...")
        time.sleep(LOGIN_RETRY_DELAY)

def run_crawler_with_retry(args, current_failure_count):
    """Run the crawler with comprehensive retry logic for login failures"""
    log.info("=" * 70)
    log.info("Starting ATM Crawler with Enhanced Retry Logic")
    log.info("=" * 70)
    
    # Check login connectivity first if not in demo mode
    if not args.demo:
        log.info("Checking login connectivity before running crawler...")
        if not test_login_connectivity():
            log.warning("Login connectivity test failed - entering retry loop")
            wait_for_login_connectivity()
        else:
            log.info("Login connectivity test successful - proceeding with crawler")
    
    # Run the crawler
    try:
        result = atm_crawler_complete.main(args.demo, not args.no_db)
        # Check if result is explicitly True (successful completion)
        if result is True:
            log.info("Crawler completed successfully")
            return 0, False  # Success: failure_count=0, demo_mode_forced=False
        else:
            # Handle None (old behavior) or False (explicit failure)
            if result is None:
                log.warning("Crawler returned None - treating as success for backwards compatibility")
                return 0, False
            else:
                log.error("Crawler reported failure")
                return current_failure_count + 1, False
            
    except Exception as e:
        error_msg = str(e)
        log.error(f"Crawler execution failed: {error_msg}")
        
        # Check if this is specifically a login failure
        if is_login_failure(error_msg):
            log.warning("Detected login failure - will check connectivity and retry")
            # For login failures, we don't force demo mode immediately
            return current_failure_count + 1, False
        else:
            log.error("Non-login related failure detected")
            return current_failure_count + 1, False

def run_crawler_with_db_check(args):
    """Simple wrapper to run crawler and return success status"""
    try:
        result = atm_crawler_complete.main(args.demo, not args.no_db)
        # Return True if result is explicitly True, or None (backwards compatibility)
        return result is True or result is None
    except Exception as e:
        log.error(f"Crawler execution failed: {str(e)}")
        return False

def main():
    """Run the ATM crawler with database integration every hour until interrupted, with enhanced retry on login/connection failures"""
    parser = argparse.ArgumentParser(description="Run ATM Crawler with Database Integration")
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    parser.add_argument('--no-db', action='store_true', help='Do not save data to database (CSV only)')
    args = parser.parse_args()
    
    consecutive_failures = 0
    last_demo_fallback_time = None
    
    try:
        while True:
            # Check if we should attempt to exit demo mode
            if last_demo_fallback_time and not args.demo:
                time_since_demo = (datetime.now() - last_demo_fallback_time).total_seconds()
                if time_since_demo >= DEMO_MODE_FALLBACK_DELAY:
                    log.info("Attempting to exit demo mode and retry live connection")
                    last_demo_fallback_time = None
            
            try:
                # Database connection check (if not in no-db mode)
                if not args.no_db:
                    log.info("Testing database connection before running crawler...")
                    conn = db_connector.get_db_connection()
                    if conn:
                        log.info(f"Successfully connected to database at {db_connector.DB_CONFIG['host']}:{db_connector.DB_CONFIG['port']}/{db_connector.DB_CONFIG['database']}")
                        conn.close()
                        # Check tables
                        if db_connector.check_db_tables():
                            log.info("Database tables verified - ready to save data")
                        else:
                            log.warning("Database tables not ready - will attempt to create them during crawler run")
                    else:
                        log.error("Failed to connect to database - continuing with CSV output only")
                        log.error("Please check your database connection settings in .env file")
                        args.no_db = True
                
                # Run the crawler with enhanced retry logic
                new_failure_count, demo_mode_forced = run_crawler_with_retry(args, consecutive_failures)
                
                if new_failure_count == 0:
                    # Success - reset failure counter
                    consecutive_failures = 0
                    last_demo_fallback_time = None
                    log.info("Sleeping for 1 hour before next run...")
                    time.sleep(3600)
                else:
                    # Update failure count
                    consecutive_failures = new_failure_count
                    
                    if demo_mode_forced and not args.demo:
                        last_demo_fallback_time = datetime.now()
                        log.warning(f"Forced into demo mode. Will retry live mode in {DEMO_MODE_FALLBACK_DELAY/60:.0f} minutes")
                    
                    # Check if we've hit the maximum consecutive failures
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        log.error(f"Maximum consecutive failures ({MAX_CONSECUTIVE_FAILURES}) reached")
                        
                        if not args.demo:
                            log.warning("Switching to demo mode to maintain service continuity")
                            args.demo = True
                            consecutive_failures = 0  # Reset counter for demo mode
                            last_demo_fallback_time = datetime.now()
                        else:
                            log.error("Already in demo mode and still failing. Using extended retry delay.")
                            extended_delay = DEMO_MODE_FALLBACK_DELAY
                            log.info(f"Will retry in {extended_delay/60:.0f} minutes...")
                            time.sleep(extended_delay)
                            continue
                    
                    # Regular failure retry delay
                    retry_delay = calculate_retry_delay(min(consecutive_failures - 1, 4))  # Cap at 4 for delay calculation
                    log.info(f"Will retry in {retry_delay/60:.1f} minutes due to failure (consecutive failures: {consecutive_failures})...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                consecutive_failures += 1
                log.error(f"Unexpected error in main loop: {e}", exc_info=True)
                
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log.critical("Too many consecutive failures in main loop. Extending retry delay.")
                    time.sleep(DEMO_MODE_FALLBACK_DELAY)
                    consecutive_failures = 0  # Reset after long delay
                else:
                    retry_delay = calculate_retry_delay(consecutive_failures - 1)
                    log.info(f"Will retry in {retry_delay/60:.1f} minutes due to unexpected error...")
                    time.sleep(retry_delay)
                    
    except KeyboardInterrupt:
        log.info("Received external interrupt. Exiting gracefully.")
        log.info(f"Final statistics: consecutive_failures={consecutive_failures}, demo_mode_active={args.demo}")

if __name__ == "__main__":
    main()
