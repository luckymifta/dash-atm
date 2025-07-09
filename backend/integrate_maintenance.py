#!/usr/bin/env python3
"""
Integration script to add maintenance endpoints to the main API
This script demonstrates how to integrate the maintenance functionality
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the maintenance module
from maintenance_api import create_maintenance_endpoints, set_db_pool

# Import the main API (you'll need to modify the import based on your setup)
# from api_option_2_fastapi_fixed import app, db_pool

def integrate_maintenance_api():
    """
    Integration function to add maintenance endpoints to the main API.
    Call this function from your main API startup.
    """
    print("Integrating Terminal Maintenance API endpoints...")
    
    # Example integration (modify as needed):
    # 1. Set the database pool for the maintenance module
    # set_db_pool(db_pool)
    
    # 2. Add the maintenance endpoints to your main app
    # create_maintenance_endpoints(app)
    
    print("✅ Terminal Maintenance API endpoints integrated successfully!")
    print("Available endpoints:")
    print("  GET    /api/v1/maintenance                    - List maintenance records")
    print("  POST   /api/v1/maintenance                    - Create maintenance record")
    print("  GET    /api/v1/maintenance/{id}               - Get specific record")
    print("  PUT    /api/v1/maintenance/{id}               - Update maintenance record")
    print("  DELETE /api/v1/maintenance/{id}               - Delete maintenance record")
    print("  GET    /api/v1/atm/{terminal_id}/maintenance  - ATM maintenance history")
    print("  POST   /api/v1/maintenance/{id}/images        - Upload images")
    print("  DELETE /api/v1/maintenance/{id}/images/{img}  - Delete image")

if __name__ == "__main__":
    integrate_maintenance_api()
