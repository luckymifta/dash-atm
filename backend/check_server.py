#!/usr/bin/env python3

import requests
import sys

def check_server():
    """Check if the API server is running"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy!")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {str(e)}")
        return False

if __name__ == "__main__":
    if check_server():
        sys.exit(0)
    else:
        sys.exit(1)
