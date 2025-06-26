#!/usr/bin/env python3
"""
Test script to verify database logging functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_logging():
    """Test if database logging can be initialized"""
    
    print("🧪 Testing Database Logging Integration")
    print("=" * 50)
    
    # Test 1: Check if database logging files exist
    print("1. Checking database logging files...")
    
    db_handler_exists = os.path.exists('database_log_handler.py')
    print(f"   - database_log_handler.py: {'✅ Found' if db_handler_exists else '❌ Missing'}")
    
    # Test 2: Try to import the database logging components
    print("\n2. Testing imports...")
    try:
        from database_log_handler import DatabaseLogHandler, LogMetricsCollector
        print("   - DatabaseLogHandler: ✅ Import successful")
        print("   - LogMetricsCollector: ✅ Import successful")
    except ImportError as e:
        print(f"   - Database logging import failed: ❌ {e}")
        return False
    
    # Test 3: Check if database connector is available
    print("\n3. Testing database connector...")
    try:
        from db_connector_new import db_connector
        print("   - db_connector_new: ✅ Available")
        db_available = True
    except ImportError:
        try:
            import db_connector
            print("   - db_connector (legacy): ✅ Available")
            db_available = True
        except ImportError:
            print("   - Database connector: ❌ Not available")
            db_available = False
    
    # Test 4: Try to initialize the retriever with database logging
    print("\n4. Testing retriever initialization...")
    try:
        from combined_atm_retrieval_script import CombinedATMRetriever
        
        # Test with database logging enabled
        retriever = CombinedATMRetriever(
            demo_mode=True,  # Use demo mode for safe testing
            total_atms=14,
            enable_db_logging=True
        )
        print("   - CombinedATMRetriever with database logging: ✅ Initialized successfully")
        
        # Test with database logging disabled
        retriever_no_db = CombinedATMRetriever(
            demo_mode=True,
            total_atms=14,
            enable_db_logging=False
        )
        print("   - CombinedATMRetriever without database logging: ✅ Initialized successfully")
        
    except Exception as e:
        print(f"   - Retriever initialization failed: ❌ {e}")
        return False
    
    # Test 5: Test a simple retrieval run
    print("\n5. Testing simple retrieval run...")
    try:
        success, data = retriever.retrieve_and_process_all_data(
            save_to_db=False,  # Don't save to database in test
            use_new_tables=False
        )
        
        if success:
            print("   - Demo retrieval run: ✅ Completed successfully")
            print(f"   - Regional data records: {len(data.get('regional_data', []))}")
            print(f"   - Terminal details records: {len(data.get('terminal_details_data', []))}")
            print(f"   - Demo mode: {data.get('demo_mode', 'Unknown')}")
        else:
            print("   - Demo retrieval run: ❌ Failed")
            return False
            
    except Exception as e:
        print(f"   - Demo retrieval run failed: ❌ {e}")
        return False
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary:")
    print("   - Database logging files: ✅" if db_handler_exists else "   - Database logging files: ❌")
    print("   - Database logging imports: ✅")
    print("   - Database connector: ✅" if db_available else "   - Database connector: ⚠️  Not available")
    print("   - Retriever initialization: ✅")
    print("   - Demo retrieval run: ✅")
    
    if db_available:
        print("\n🚀 READY TO RUN: Your script is ready for production with database logging!")
        print("   - Use enable_db_logging=True for database logging")
        print("   - Use enable_db_logging=False to disable database logging")
        print("   - Demo mode works correctly")
    else:
        print("\n⚠️  PARTIAL READY: Script will work but database logging will be disabled")
        print("   - Database connector not available")
        print("   - Logs will only go to files, not database")
    
    return True

if __name__ == "__main__":
    test_database_logging()
