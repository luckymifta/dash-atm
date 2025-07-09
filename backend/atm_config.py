#!/usr/bin/env python3
"""
ATM Monitoring System Configuration

Contains all configuration constants, URLs, credentials, and settings
for the ATM monitoring and retrieval system.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Endpoints
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGOUT_URL = "https://172.31.1.46/sigit/user/logout"
REPORTS_URL = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status"
DASHBOARD_URL = "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM"
CASH_INFO_URL = "https://172.31.1.46/sigit/terminal/searchTerminal"

# Authentication Credentials
PRIMARY_LOGIN_PAYLOAD = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2025@"
}

FALLBACK_LOGIN_PAYLOAD = {
    "user_name": "Adelaide",
    "password": "Adelaide02052024*"
}

# HTTP Headers
COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://172.31.1.46",
    "Referer": "https://172.31.1.46/sigitportal/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

# Terminal Status Parameters
PARAMETER_VALUES = [
    "AVAILABLE", "WARNING", "WOUNDED", "HARD", 
    "CASH", "UNAVAILABLE", "ZOMBIE"
]

# Expected Terminal IDs (baseline)
EXPECTED_TERMINAL_IDS = [
    '83', '2603', '88', '147', '87', '169', 
    '2605', '2604', '93', '49', '86', '89', '85', '90'
]

# Database Configuration
def get_db_config() -> Dict[str, str]:
    """Get database configuration from environment variables"""
    # Check for both DB_PASSWORD and DB_PASS for compatibility
    password = os.environ.get("DB_PASSWORD") or os.environ.get("DB_PASS", "")
    
    config = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "database": os.environ.get("DB_NAME", "atm_monitor"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": password
    }
    
    # Log configuration (without password) for debugging
    config_debug = {k: v for k, v in config.items() if k != "password"}
    config_debug["password"] = "***" if password else "NOT SET"
    print(f"Database config: {config_debug}")
    
    return config

# Timeout Settings
DEFAULT_TIMEOUT = 30
RETRY_DELAYS = {
    "windows": 2.0,
    "default": 1.0
}

MAX_RETRIES = {
    "windows": 3,
    "default": 2
}

# Timezone Configuration
DILI_TIMEZONE = "Asia/Dili"

# Demo Data Configuration
DEMO_CASSETTES = [
    {
        "cassId": "PCU00",
        "cassLogicNbr": "01",
        "cassPhysNbr": "00",
        "cassTypeValue": "REJECT",
        "cassTypeDescription": "Cassette of Rejected Notes",
        "cassStatusValue": "OK",
        "cassStatusDescription": "Cassete OK",
        "cassStatusColor": "#3cd179",
        "currency": None,
        "notesVal": None,
        "nbrNotes": 14,
        "cassTotal": 0,
        "percentage": 0.0
    },
    {
        "cassId": "PCU01",
        "cassLogicNbr": "02",
        "cassPhysNbr": "01",
        "cassTypeValue": "DISPENSE",
        "cassTypeDescription": "Dispensing Cassette",
        "cassStatusValue": "LOW",
        "cassStatusDescription": "Cassette almost empty",
        "cassStatusColor": "#90EE90",
        "currency": "USD",
        "notesVal": 20,
        "nbrNotes": 542,
        "cassTotal": 10840,
        "percentage": 0.0
    }
]
