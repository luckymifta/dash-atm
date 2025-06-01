import requests
import urllib3
import json
import logging
import sys
import time
from datetime import datetime

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("test_login.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("LoginTest")

# --- Disable SSL warnings (self-signed certs) ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Login Configuration (from atm_crawler_complete.py) ---
login_url = "https://172.31.1.46/sigit/user/login?language=EN"
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

def test_connectivity():
    """Test basic connectivity to the host machine"""
    try:
        log.info(f"Testing connectivity to {login_url}")
        response = requests.head(
            login_url, 
            timeout=10, 
            verify=False
        )
        log.info(f"Connectivity test successful: HTTP {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"Connectivity test failed: {str(e)}")
        return False

def test_login():
    """Test login to the host machine using credentials from atm_crawler_complete.py"""
    log.info("="*60)
    log.info("Starting Login Test")
    log.info("="*60)
    
    # First test connectivity
    if not test_connectivity():
        log.error("Cannot connect to the host machine. Please check your network connection.")
        return False
    
    try:
        # Create a session for the login test
        session = requests.Session()
        
        log.info(f"Attempting login to: {login_url}")
        log.info(f"Username: {login_payload['user_name']}")
        log.info("Password: [HIDDEN]")
        
        # Perform login request
        start_time = datetime.now()
        response = session.post(
            login_url,
            json=login_payload,
            headers=common_headers,
            verify=False,
            timeout=30
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        log.info(f"Response received in {response_time:.2f} seconds")
        log.info(f"HTTP Status Code: {response.status_code}")
        
        # Check if the request was successful
        try:
            response.raise_for_status()
            log.info("✅ HTTP request successful")
        except requests.exceptions.HTTPError as e:
            log.error(f"❌ HTTP error: {str(e)}")
            log.error(f"Response text: {response.text[:500]}...")
            return False
        
        # Try to parse JSON response
        try:
            login_json = response.json()
            log.info("✅ Response is valid JSON")
        except ValueError as e:
            log.error(f"❌ Response is not valid JSON: {str(e)}")
            log.error(f"Response text: {response.text[:500]}...")
            return False
        
        # Extract user token (following the same logic as atm_crawler_complete.py)
        user_token = None
        
        # First, try to extract token from main response keys
        for key in ['user_token', 'token']:
            if key in login_json:
                user_token = login_json[key]
                log.info(f"✅ User token extracted with key '{key}': {user_token[:20]}...")
                break
        
        # If not found, check 'header' field as fallback
        if not user_token:
            user_token = login_json.get("header", {}).get("user_token")
            if user_token:
                log.info(f"✅ User token extracted from 'header' field: {user_token[:20]}...")
        
        if user_token:
            log.info("✅ LOGIN SUCCESSFUL!")
            log.info(f"Full token length: {len(user_token)} characters")
            
            # Display response structure for debugging
            log.info("\n--- Response Structure ---")
            if isinstance(login_json, dict):
                for key in login_json.keys():
                    if key.lower() in ['password', 'token', 'user_token']:
                        log.info(f"{key}: [PRESENT - {len(str(login_json[key]))} chars]")
                    else:
                        log.info(f"{key}: {type(login_json[key]).__name__}")
            
            # Test token validity by making a simple authenticated request
            log.info("\n--- Testing Token Validity ---")
            test_dashboard_connectivity(session, user_token)
            
            # Test reports dashboard access
            test_reports_dashboard(session, user_token)
            
            return True
        else:
            log.error("❌ LOGIN FAILED: Unable to extract user token from response")
            log.error("Response keys available:")
            if isinstance(login_json, dict):
                for key in login_json.keys():
                    log.error(f"  - {key}: {type(login_json[key]).__name__}")
            else:
                log.error(f"Response is not a dictionary: {type(login_json)}")
            return False
            
    except requests.exceptions.Timeout:
        log.error("❌ LOGIN FAILED: Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        log.error("❌ LOGIN FAILED: Connection error")
        return False
    except requests.exceptions.RequestException as e:
        log.error(f"❌ LOGIN FAILED: Request error: {str(e)}")
        return False
    except Exception as e:
        log.error(f"❌ LOGIN FAILED: Unexpected error: {str(e)}")
        return False

def test_dashboard_connectivity(session, user_token):
    """Test if we can access the dashboard with the obtained token"""
    dashboard_url = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"
    
    # Simple test payload to verify token works
    test_payload = {
        "header": {
            "logged_user": login_payload["user_name"],
            "user_token": user_token
        },
        "body": {
            "parameters_list": [
                {
                    "parameter_name": "issueStateName",
                    "parameter_values": ["AVAILABLE"]
                }
            ]
        }
    }
    
    try:
        log.info("Testing dashboard access with obtained token...")
        response = session.put(
            dashboard_url,
            json=test_payload,
            headers=common_headers,
            verify=False,
            timeout=15
        )
        
        if response.status_code == 200:
            log.info("✅ Dashboard access successful - Token is valid")
            try:
                dashboard_data = response.json()
                if "body" in dashboard_data:
                    log.info("✅ Dashboard response has expected structure")
                else:
                    log.warning("⚠️  Dashboard response missing 'body' field")
            except ValueError:
                log.warning("⚠️  Dashboard response is not valid JSON")
        else:
            log.warning(f"⚠️  Dashboard access returned HTTP {response.status_code}")
            
    except Exception as e:
        log.warning(f"⚠️  Dashboard test failed: {str(e)}")

def test_reports_dashboard(session, user_token):
    """Test access to the reports dashboard endpoint"""
    reports_url = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status"
    
    # Correct payload format based on your example
    reports_payload = {
        "header": {
            "logged_user": login_payload["user_name"],
            "user_token": user_token
        },
        "body": []  # Empty array, not object
    }
    
    log.info("\n--- Testing Reports Dashboard Access ---")
    log.info(f"Requesting: {reports_url}")
    log.info(f"Payload: {json.dumps(reports_payload, indent=2)}")
    
    try:
        start_time = datetime.now()
        response = session.put(
            reports_url,
            json=reports_payload,
            headers=common_headers,
            verify=False,
            timeout=30
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        log.info(f"Response received in {response_time:.2f} seconds")
        log.info(f"HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            log.info("✅ Reports dashboard access successful!")
            
            try:
                reports_data = response.json()
                log.info("✅ Response is valid JSON")
                
                # Log response structure
                log.info("\n--- Reports Dashboard Response Structure ---")
                if isinstance(reports_data, dict):
                    for key in reports_data.keys():
                        value = reports_data[key]
                        if isinstance(value, list):
                            log.info(f"{key}: List with {len(value)} items")
                        elif isinstance(value, dict):
                            log.info(f"{key}: Dictionary with {len(value)} keys")
                        else:
                            log.info(f"{key}: {type(value).__name__}")
                
                # Log content length
                log.info(f"Response content length: {len(response.text)} characters")
                
                # Save response to file for inspection
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"reports_dashboard_response_{timestamp}.json"
                with open(filename, "w") as f:
                    json.dump(reports_data, f, indent=2)
                log.info(f"✅ Response saved to '{filename}'")
                
                # Process fifth_graphic data if available
                if "body" in reports_data and "fifth_graphic" in reports_data["body"]:
                    log.info("\n--- Processing Fifth Graphic Data ---")
                    processed_data = process_fifth_graphic_data(reports_data["body"]["fifth_graphic"])
                    if processed_data:
                        log.info("✅ Fifth graphic data processed successfully")
                
                return True
                
            except ValueError as e:
                log.error(f"❌ Response is not valid JSON: {str(e)}")
                log.error(f"Response text (first 500 chars): {response.text[:500]}...")
                return False
                
        else:
            log.error(f"❌ Reports dashboard access failed: HTTP {response.status_code}")
            log.error(f"Response text: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        log.error("❌ Reports dashboard request timeout")
        return False
    except requests.exceptions.RequestException as e:
        log.error(f"❌ Reports dashboard request error: {str(e)}")
        return False
    except Exception as e:
        log.error(f"❌ Unexpected error accessing reports dashboard: {str(e)}")
        return False

def process_fifth_graphic_data(fifth_graphic, total_atm_count=14):
    """
    Process fifth_graphic data and convert percentages to actual counts
    
    Args:
        fifth_graphic: The fifth_graphic array from the reports dashboard response
        total_atm_count: Total number of ATMs (default: 14)
    
    Returns:
        list: Processed data with both percentages and counts
    """
    try:
        if not fifth_graphic:
            log.warning("⚠️  No fifth_graphic data found in response")
            return None
        
        log.info(f"Total ATM count: {total_atm_count}")
        
        processed_data = []
        
        for region_data in fifth_graphic:
            region_key = region_data.get("hc-key", "Unknown")
            state_count = region_data.get("state_count", {})
            
            log.info(f"\nRegion: {region_key}")
            
            region_processed = {
                "region": region_key,
                "states": {}
            }
            
            total_percentage = 0
            
            for state, percentage_str in state_count.items():
                try:
                    percentage = float(percentage_str)
                    count = round(percentage * total_atm_count)
                    
                    region_processed["states"][state] = {
                        "percentage": percentage,
                        "percentage_display": f"{percentage:.2%}",
                        "count": count
                    }
                    
                    total_percentage += percentage
                    
                    log.info(f"  {state}:")
                    log.info(f"    Percentage: {percentage:.4f} ({percentage:.2%})")
                    log.info(f"    Count: {count} ATMs")
                    
                except ValueError as e:
                    log.error(f"❌ Error converting percentage for {state}: {percentage_str} - {str(e)}")
                    continue
            
            # Validation
            log.info(f"\nValidation for {region_key}:")
            log.info(f"  Total percentage: {total_percentage:.4f} ({total_percentage:.2%})")
            
            total_calculated_count = sum(state_data["count"] for state_data in region_processed["states"].values())
            log.info(f"  Total calculated count: {total_calculated_count}")
            
            if abs(total_percentage - 1.0) > 0.01:  # Allow 1% tolerance
                log.warning(f"⚠️  Percentages don't sum to 100% for {region_key}: {total_percentage:.2%}")
            
            if total_calculated_count != total_atm_count:
                log.warning(f"⚠️  Calculated count ({total_calculated_count}) doesn't match total ATM count ({total_atm_count})")
            
            processed_data.append(region_processed)
        
        return processed_data
        
    except Exception as e:
        log.error(f"❌ Error processing fifth_graphic data: {str(e)}")
        return None

def main():
    """Main function to run the login test"""
    print("\n" + "="*60)
    print("ATM System Login Test")
    print("="*60)
    
    success = test_login()
    
    print("\n" + "="*60)
    if success:
        print("🎉 LOGIN TEST PASSED!")
        print("✅ Successfully authenticated to the ATM monitoring system")
    else:
        print("❌ LOGIN TEST FAILED!")
        print("❌ Could not authenticate to the ATM monitoring system")
    print("="*60)
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

