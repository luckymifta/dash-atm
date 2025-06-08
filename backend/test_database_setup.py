#!/usr/bin/env python3
"""
Test Script for ATM Data Retrieval System Database
This script tests the database connection and table creation
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test basic database connectivity"""
    print("Testing database connection...")
    
    try:
        from db_connector_new import DatabaseConnector
        connector = DatabaseConnector()
        
        if connector.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except ImportError as e:
        print(f"❌ Cannot import database connector: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_table_creation():
    """Test table creation and schema"""
    print("Testing table creation...")
    
    try:
        from db_connector_new import DatabaseConnector
        connector = DatabaseConnector()
        
        if connector.create_tables():
            print("✅ Tables created successfully")
            
            # Get table info
            info = connector.get_table_info()
            tables = info.get('tables', [])
            
            expected_tables = ['regional_data', 'terminal_details', 'regional_atm_counts']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                print(f"✅ All expected tables found: {expected_tables}")
                return True
        else:
            print("❌ Table creation failed")
            return False
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def test_combined_script_import():
    """Test if the combined ATM script can import the new database connector"""
    print("Testing combined script compatibility...")
    
    try:
        # Try to import the updated script
        import combined_atm_retrieval_script
        print("✅ Combined ATM script imported successfully")
        
        # Check if DB_AVAILABLE is True
        if hasattr(combined_atm_retrieval_script, 'DB_AVAILABLE'):
            if combined_atm_retrieval_script.DB_AVAILABLE:
                print("✅ Database connector is available in combined script")
                return True
            else:
                print("❌ Database connector not available in combined script")
                return False
        else:
            print("❌ DB_AVAILABLE attribute not found in combined script")
            return False
    except ImportError as e:
        print(f"❌ Cannot import combined script: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_demo_run():
    """Test running the combined script in demo mode"""
    print("Testing demo run...")
    
    try:
        from combined_atm_retrieval_script import CombinedATMRetriever
        
        # Create retriever in demo mode
        retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
        print("✅ CombinedATMRetriever created successfully")
        
        # Test data retrieval and processing (demo mode - no network calls)
        success, all_data = retriever.retrieve_and_process_all_data(
            save_to_db=True, 
            use_new_tables=True
        )
        
        if success:
            print("✅ Demo run completed successfully")
            print(f"   - Regional data: {len(all_data.get('regional_data', []))} records")
            print(f"   - Terminal details: {len(all_data.get('terminal_details_data', []))} records")
            return True
        else:
            print("❌ Demo run failed")
            return False
    except Exception as e:
        print(f"❌ Demo run error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("ATM DATA RETRIEVAL SYSTEM - DATABASE TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Table Creation", test_table_creation),
        ("Script Import", test_combined_script_import),
        ("Demo Run", test_demo_run)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
        print()
    
    print("=" * 80)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your database setup is ready.")
        print()
        print("Next steps:")
        print("1. Run: python combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables")
        print("2. Test with live data (remove --demo flag)")
        print("3. Set up continuous monitoring with --continuous flag")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
