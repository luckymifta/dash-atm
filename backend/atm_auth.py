"""
ATM Authentication Module

Handles all authentication-related operations including login, logout,
token management, and session handling.
"""

import requests
from requests.adapters import HTTPAdapter
import json
import logging
import time
from typing import Optional, Dict, Any
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from atm_config import (
    LOGIN_URL, LOGOUT_URL, PRIMARY_LOGIN_PAYLOAD, 
    FALLBACK_LOGIN_PAYLOAD, COMMON_HEADERS, DEFAULT_TIMEOUT
)

log = logging.getLogger(__name__)

class ATMAuthenticator:
    """Handles authentication operations for the ATM monitoring system"""
    
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.user_token: Optional[str] = None
        self.username: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = False
        
        # Set up session with retry strategy
        adapter = HTTPAdapter(max_retries=3)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def authenticate(self) -> bool:
        """
        Authenticate with the ATM monitoring system
        Try primary credentials first, then fallback to secondary credentials if primary fails
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Skipping actual authentication")
            self.user_token = "demo_token_" + str(int(time.time()))
            self.username = "demo_user"
            return True
        
        # Try primary credentials first
        log.info("Attempting authentication with primary credentials...")
        
        if self._try_authentication(PRIMARY_LOGIN_PAYLOAD):
            log.info("✅ Authentication successful with primary credentials")
            return True
        
        # If primary fails, try fallback credentials
        log.warning("Primary authentication failed, trying fallback credentials...")
        
        if self._try_authentication(FALLBACK_LOGIN_PAYLOAD):
            log.info("✅ Authentication successful with fallback credentials")
            return True
        
        # Both authentication attempts failed
        log.error("❌ Authentication failed with both primary and fallback credentials")
        return False
    
    def _try_authentication(self, credentials: Dict[str, str]) -> bool:
        """
        Try authentication with the provided credentials
        
        Args:
            credentials: Dictionary containing user_name and password
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            response = self.session.post(
                LOGIN_URL,
                json=credentials,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            login_data = response.json()
            user_token = None
            
            # Method 1: Direct token extraction
            for key in ['user_token', 'token']:
                if key in login_data:
                    user_token = login_data[key]
                    break
            
            # Method 2: From header field
            if not user_token and 'header' in login_data:
                user_token = login_data['header'].get('user_token')
            
            if user_token:
                self.user_token = user_token
                self.username = credentials['user_name']
                log.debug(f"User token extracted successfully for {credentials['user_name']}")
                return True
            else:
                log.warning(f"Authentication failed for {credentials['user_name']}: Unable to extract user token")
                return False
                
        except requests.exceptions.RequestException as e:
            log.warning(f"Authentication request failed for {credentials['user_name']}: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            log.warning(f"Authentication response not valid JSON for {credentials['user_name']}: {str(e)}")
            return False
        except Exception as e:
            log.warning(f"Unexpected error during authentication for {credentials['user_name']}: {str(e)}")
            return False
    
    def refresh_token(self) -> bool:
        """
        Refresh the authentication token
        
        Returns:
            bool: True if token refresh successful, False otherwise
        """
        log.info("Attempting to refresh authentication token...")
        return self.authenticate()
    
    def logout(self) -> bool:
        """
        Logout from the ATM monitoring system
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        if self.demo_mode:
            log.info("Demo mode: Simulating logout")
            self.user_token = None
            return True
        
        if not self.user_token:
            log.warning("No active session to logout from")
            return True
        
        try:
            logout_payload = {
                "header": {
                    "logged_user": "Lucky.Saputra",
                    "user_token": self.user_token
                },
                "body": {}
            }
            
            # Using PUT request as required by the API
            response = self.session.put(
                LOGOUT_URL,
                json=logout_payload,
                headers=COMMON_HEADERS,
                verify=False,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            self.user_token = None
            log.info("Successfully logged out")
            return True
            
        except requests.exceptions.RequestException as e:
            log.warning(f"Logout request failed: {str(e)}")
            return False
        except Exception as e:
            log.warning(f"Unexpected error during logout: {str(e)}")
            return False
    
    def get_token(self) -> Optional[str]:
        """Get the current authentication token"""
        return self.user_token
    
    def get_username(self) -> Optional[str]:
        """Get the current authenticated username"""
        return self.username
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return self.user_token is not None
