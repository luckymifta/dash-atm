#!/usr/bin/env python3
"""
Test script for the Regional ATM Data Retrieval Script

This script validates the complete functionality of the regional_atm_retrieval_script.py
including authentication, data retrieval, processing, and database operations.
"""

import sys
import os
import logging
import json
from datetime import datetime
import argparse

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    import regional_atm_retrieval_script as retrieval_script
    import db_connector
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    DB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s"
)
log = logging.getLogger("RegionalATMTest")

def test_demo_mode():
    """Test the regional data retrieval in demo mode"""
    print("\n" + "=" * 80)
    print("🧪 TESTING DEMO MODE FUNCTIONALITY")
    print("=" * 80)
    
    try:
        # Create retriever in demo mode
        retriever = retrieval_script.RegionalATMRetriever(demo_mode=True, total_atms=14)
        
        # Test authentication
        print("1. Testing demo authentication...")
        auth_success = retriever.authenticate()
        if auth_success:
            print("   ✅ Demo authentication successful")
            print(f"   📝 Token: {retriever.user_token[:20]}...")
        else:
            print("   ❌ Demo authentication failed")
            return False
        
        # Test data retrieval
        print("2. Testing demo data retrieval...")
        raw_data = retriever.fetch_regional_data()
        if raw_data and len(raw_data) > 0:
            print(f"   ✅ Demo data retrieval successful ({len(raw_data)} regions)")
            for region in raw_data:
                print(f"      Region: {region.get('hc-key', 'Unknown')}")
                states = region.get('state_count', {})
                print(f"      States: {list(states.keys())}")
        else:
            print("   ❌ Demo data retrieval failed")
            return False
        
        # Test data processing
        print("3. Testing data processing...")
        processed_data = retriever.process_regional_data(raw_data)
        if processed_data and len(processed_data) > 0:
            print(f"   ✅ Data processing successful ({len(processed_data)} records)")
            
            # Validate structure
            first_record = processed_data[0]
            required_fields = [
                'unique_request_id', 'region_code', 'count_available', 'count_warning',
                'count_zombie', 'count_wounded', 'count_out_of_service', 'date_creation',
                'total_atms_in_region', 'percentage_available', 'percentage_warning',
                'percentage_zombie', 'percentage_wounded', 'percentage_out_of_service'
            ]
            
            missing_fields = [field for field in required_fields if field not in first_record]
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
            else:
                print("   ✅ All required fields present in processed data")
                
                # Display sample record
                sample = processed_data[0]
                print(f"   📊 Sample record for {sample['region_code']}:")
                print(f"      Available: {sample['count_available']} ({sample['percentage_available']*100:.1f}%)")
                print(f"      Warning: {sample['count_warning']} ({sample['percentage_warning']*100:.1f}%)")
                print(f"      Total ATMs: {sample['total_atms_in_region']}")
        else:
            print("   ❌ Data processing failed")
            return False
        
        print("✅ Demo mode test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Demo mode test failed: {str(e)}")
        return False

def test_complete_flow_demo():
    """Test the complete flow using the main method in demo mode"""
    print("\n" + "=" * 80)
    print("🔄 TESTING COMPLETE FLOW (DEMO MODE)")
    print("=" * 80)
    
    try:
        retriever = retrieval_script.RegionalATMRetriever(demo_mode=True, total_atms=14)
        
        # Test complete flow without database save
        print("1. Testing complete flow without database...")
        success, processed_data = retriever.retrieve_and_process(save_to_db=False)
        
        if success and processed_data:
            print("   ✅ Complete flow successful")
            print(f"   📊 Retrieved {len(processed_data)} regional records")
            
            # Test with database save if available
            if DB_AVAILABLE:
                print("2. Testing complete flow with database save...")
                success_db, processed_data_db = retriever.retrieve_and_process(save_to_db=True)
                
                if success_db:
                    print("   ✅ Complete flow with database save successful")
                    
                    # Verify data was saved by querying latest data
                    latest_data = db_connector.get_latest_regional_data()
                    if latest_data:
                        print(f"   ✅ Database verification successful ({len(latest_data)} records found)")
                        for region in latest_data:
                            print(f"      {region['region_code']}: {region['count_available']}/{region['total_atms_in_region']} available")
                    else:
                        print("   ⚠️  No data found in database (may be expected)")
                else:
                    print("   ❌ Complete flow with database save failed")
                    return False
            else:
                print("2. Database not available - skipping database test")
            
            return True
        else:
            print("   ❌ Complete flow failed")
            return False
            
    except Exception as e:
        print(f"❌ Complete flow test failed: {str(e)}")
        return False

def test_data_structure_validation():
    """Test that the processed data matches the regional_atm_counts table structure"""
    print("\n" + "=" * 80)
    print("🗄️  TESTING DATA STRUCTURE VALIDATION")
    print("=" * 80)
    
    try:
        retriever = retrieval_script.RegionalATMRetriever(demo_mode=True, total_atms=14)
        
        # Get demo data
        raw_data = retriever.fetch_regional_data()
        processed_data = retriever.process_regional_data(raw_data)
        
        if not processed_data:
            print("❌ No processed data available for validation")
            return False
        
        print(f"Validating structure for {len(processed_data)} records...")
        
        # Expected data types and constraints for regional_atm_counts table
        field_validations = {
            'unique_request_id': (str, "UUID string"),
            'region_code': (str, "VARCHAR region identifier"),
            'count_available': (int, "INTEGER >= 0"),
            'count_warning': (int, "INTEGER >= 0"),
            'count_zombie': (int, "INTEGER >= 0"),
            'count_wounded': (int, "INTEGER >= 0"),
            'count_out_of_service': (int, "INTEGER >= 0"),
            'date_creation': (datetime, "TIMESTAMP WITH TIME ZONE"),
            'total_atms_in_region': (int, "INTEGER > 0"),
            'percentage_available': (float, "DECIMAL(10,8) [0.0-1.0]"),
            'percentage_warning': (float, "DECIMAL(10,8) [0.0-1.0]"),
            'percentage_zombie': (float, "DECIMAL(10,8) [0.0-1.0]"),
            'percentage_wounded': (float, "DECIMAL(10,8) [0.0-1.0]"),
            'percentage_out_of_service': (float, "DECIMAL(10,8) [0.0-1.0]")
        }
        
        validation_passed = True
        
        for i, record in enumerate(processed_data):
            print(f"\nValidating record {i+1} (Region: {record.get('region_code', 'Unknown')}):")
            
            # Check all required fields are present
            for field_name, (expected_type, description) in field_validations.items():
                if field_name not in record:
                    print(f"   ❌ Missing field: {field_name}")
                    validation_passed = False
                    continue
                
                value = record[field_name]
                
                # Type validation
                if not isinstance(value, expected_type):
                    print(f"   ❌ Field {field_name}: Expected {expected_type.__name__}, got {type(value).__name__}")
                    validation_passed = False
                    continue
                
                # Value validation
                if 'count_' in field_name and value < 0:
                    print(f"   ❌ Field {field_name}: Count cannot be negative ({value})")
                    validation_passed = False
                elif 'percentage_' in field_name and not (0.0 <= value <= 1.0):
                    print(f"   ❌ Field {field_name}: Percentage out of range [0.0-1.0] ({value})")
                    validation_passed = False
                elif field_name == 'total_atms_in_region' and value <= 0:
                    print(f"   ❌ Field {field_name}: Total ATMs must be positive ({value})")
                    validation_passed = False
                else:
                    print(f"   ✅ Field {field_name}: Valid {description}")
            
            # Cross-field validations
            count_sum = (record.get('count_available', 0) + record.get('count_warning', 0) + 
                        record.get('count_zombie', 0) + record.get('count_wounded', 0) + 
                        record.get('count_out_of_service', 0))
            
            if count_sum != record.get('total_atms_in_region', 0):
                print(f"   ⚠️  Count sum ({count_sum}) doesn't match total ATMs ({record.get('total_atms_in_region', 0)})")
            else:
                print(f"   ✅ Count validation: Sum matches total ATMs")
            
            percentage_sum = (record.get('percentage_available', 0) + record.get('percentage_warning', 0) + 
                            record.get('percentage_zombie', 0) + record.get('percentage_wounded', 0) + 
                            record.get('percentage_out_of_service', 0))
            
            if abs(percentage_sum - 1.0) > 0.01:  # Allow 1% tolerance
                print(f"   ⚠️  Percentage sum ({percentage_sum:.4f}) doesn't equal 1.0")
            else:
                print(f"   ✅ Percentage validation: Sum equals 1.0")
        
        if validation_passed:
            print(f"\n✅ All {len(processed_data)} records passed structure validation")
            print("✅ Data structure matches regional_atm_counts table requirements")
        else:
            print(f"\n❌ Some records failed validation")
        
        return validation_passed
        
    except Exception as e:
        print(f"❌ Data structure validation failed: {str(e)}")
        return False

def test_database_integration():
    """Test database integration if available"""
    print("\n" + "=" * 80)
    print("🗄️  TESTING DATABASE INTEGRATION")
    print("=" * 80)
    
    if not DB_AVAILABLE:
        print("❌ Database not available - skipping database integration test")
        return True  # Not a failure, just not available
    
    try:
        # Test database connection
        print("1. Testing database connection...")
        conn = db_connector.get_db_connection()
        if conn:
            print("   ✅ Database connection successful")
            conn.close()
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Test table existence/creation
        print("2. Testing regional_atm_counts table...")
        table_ok = db_connector.check_regional_atm_counts_table()
        if table_ok:
            print("   ✅ regional_atm_counts table ready")
        else:
            print("   ❌ regional_atm_counts table check failed")
            return False
        
        # Test data insertion with demo data
        print("3. Testing data insertion...")
        retriever = retrieval_script.RegionalATMRetriever(demo_mode=True, total_atms=14)
        raw_data = retriever.fetch_regional_data()
        processed_data = retriever.process_regional_data(raw_data)
        
        if processed_data:
            save_success = retriever.save_to_database(processed_data)
            if save_success:
                print(f"   ✅ Successfully saved {len(processed_data)} records to database")
                
                # Verify data was saved
                latest_data = db_connector.get_latest_regional_data()
                if latest_data:
                    print(f"   ✅ Data verification successful ({len(latest_data)} records retrieved)")
                else:
                    print("   ⚠️  No data retrieved after save (may indicate issue)")
            else:
                print("   ❌ Database save failed")
                return False
        else:
            print("   ❌ No processed data available for database test")
            return False
        
        print("✅ Database integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "=" * 80)
    print("🛠️  TESTING ERROR HANDLING")
    print("=" * 80)
    
    try:
        # Test with invalid data
        print("1. Testing invalid data handling...")
        retriever = retrieval_script.RegionalATMRetriever(demo_mode=True, total_atms=14)
        
        # Test with None data
        processed = retriever.process_regional_data(None)
        if processed == []:
            print("   ✅ Correctly handled None input")
        else:
            print("   ❌ Failed to handle None input properly")
            return False
        
        # Test with empty data
        processed = retriever.process_regional_data([])
        if processed == []:
            print("   ✅ Correctly handled empty input")
        else:
            print("   ❌ Failed to handle empty input properly")
            return False
        
        # Test with malformed data
        malformed_data = [{"hc-key": "TEST", "state_count": {}}]
        processed = retriever.process_regional_data(malformed_data)
        if isinstance(processed, list):
            print("   ✅ Correctly handled malformed input")
        else:
            print("   ❌ Failed to handle malformed input properly")
            return False
        
        print("2. Testing authentication without token...")
        retriever_no_auth = retrieval_script.RegionalATMRetriever(demo_mode=False, total_atms=14)
        # Don't authenticate, try to fetch data
        if retriever_no_auth.user_token is None:
            data = retriever_no_auth.fetch_regional_data()
            if data is None:
                print("   ✅ Correctly handled missing authentication")
            else:
                print("   ❌ Should have failed without authentication")
                return False
        
        print("✅ Error handling test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and return overall success status"""
    print("🚀 STARTING COMPREHENSIVE TESTS FOR REGIONAL ATM RETRIEVAL SCRIPT")
    print("=" * 100)
    
    tests = [
        ("Demo Mode Functionality", test_demo_mode),
        ("Complete Flow", test_complete_flow_demo),
        ("Data Structure Validation", test_data_structure_validation),
        ("Database Integration", test_database_integration),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    overall_success = True
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = success
            if not success:
                overall_success = False
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False
            overall_success = False
    
    # Summary
    print("\n" + "=" * 100)
    print("📊 TEST SUMMARY")
    print("=" * 100)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    overall_status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"
    print(f"\nOverall Result: {overall_status}")
    
    if overall_success:
        print("\n🎉 The Regional ATM Retrieval Script is ready for use!")
        print("\nNext steps:")
        print("1. Run in demo mode: python regional_atm_retrieval_script.py --demo")
        print("2. Run with database save: python regional_atm_retrieval_script.py --demo --save-to-db")
        print("3. Run in live mode (when network is available): python regional_atm_retrieval_script.py --save-to-db")
    else:
        print("\n⚠️  Please address the failed tests before using the script in production.")
    
    return overall_success

def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(description="Test Regional ATM Retrieval Script")
    parser.add_argument('--quick', action='store_true', help='Run only essential tests')
    parser.add_argument('--demo-only', action='store_true', help='Run only demo mode tests')
    parser.add_argument('--db-only', action='store_true', help='Run only database tests')
    
    args = parser.parse_args()
    
    if args.quick:
        print("🏃 Running quick tests only...")
        success = test_demo_mode() and test_data_structure_validation()
    elif args.demo_only:
        print("🧪 Running demo tests only...")
        success = test_demo_mode() and test_complete_flow_demo()
    elif args.db_only:
        print("🗄️  Running database tests only...")
        success = test_database_integration()
    else:
        success = run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
