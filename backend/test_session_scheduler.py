#!/usr/bin/env python3
"""
Test script to verify session scheduler database connectivity
"""

import sys
import os
sys.path.append('/Users/luckymifta/Documents/2. AREA/dash-atm/backend')

from session_scheduler import SessionScheduler
import logging

# Configure logging for test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and basic operations"""
    print("Testing Session Scheduler Database Connection...")
    print("=" * 50)
    
    try:
        # Create scheduler instance
        scheduler = SessionScheduler()
        
        # Test database connection
        print("1. Testing database connection...")
        conn = scheduler.get_db_connection()
        if conn:
            print("✅ Database connection successful!")
            conn.close()
        else:
            print("❌ Database connection failed!")
            return False
        
        # Test session health check
        print("\n2. Testing session health check...")
        scheduler.session_health_check()
        print("✅ Session health check completed!")
        
        # Test expired session cleanup
        print("\n3. Testing expired session cleanup...")
        scheduler.cleanup_expired_sessions()
        print("✅ Expired session cleanup completed!")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Session scheduler is ready to use.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
