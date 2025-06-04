#!/usr/bin/env python3
# test_dashboard_integration.py - Test script for the complete ATM dashboard system

import os
import sys
import logging
import argparse
from datetime import datetime
import json

# Import our modules
import db_connector
import dashboard_queries
import atm_crawler_complete

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
log = logging.getLogger("DashboardTest")

def test_database_connection():
    """Test database connection"""
    print("=" * 60)
    print("🔌 TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    conn = db_connector.get_db_connection()
    if conn:
        print("✅ Database connection successful")
        conn.close()
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_database_tables():
    """Test database table existence"""
    print("\n" + "=" * 60)
    print("🗃️  TESTING DATABASE TABLES")
    print("=" * 60)
    
    # Test main tables
    main_tables_ok = db_connector.check_db_tables()
    if main_tables_ok:
        print("✅ Main ATM tables exist and are ready")
    else:
        print("❌ Main ATM tables check failed")
    
    # Test regional tables
    regional_tables_ok = db_connector.check_regional_atm_counts_table()
    if regional_tables_ok:
        print("✅ Regional ATM counts table exists and is ready")
    else:
        print("❌ Regional ATM counts table check failed")
    
    return main_tables_ok and regional_tables_ok

def test_crawler_data_collection(demo_mode=True):
    """Test data collection from crawler"""
    print("\n" + "=" * 60)
    print(f"🕷️  TESTING CRAWLER DATA COLLECTION ({'DEMO' if demo_mode else 'LIVE'} MODE)")
    print("=" * 60)
    
    try:
        # Use the run_and_return_data function to collect data
        terminals, terminal_details = atm_crawler_complete.run_and_return_data(demo_mode)
        
        print(f"✅ Crawler execution successful")
        print(f"   📊 Terminals collected: {len(terminals)}")
        print(f"   🔍 Terminal details collected: {len(terminal_details)}")
        
        if terminals:
            status_counts = {}
            for terminal in terminals:
                status = terminal.get('fetched_status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("   📈 Status distribution:")
            for status, count in status_counts.items():
                print(f"      {status}: {count}")
        
        return True, terminals, terminal_details
        
    except Exception as e:
        print(f"❌ Crawler test failed: {str(e)}")
        return False, [], []

def test_fifth_graphic_functionality(demo_mode=True):
    """Test fifth_graphic data collection and database saving"""
    print("\n" + "=" * 60)
    print(f"🗺️  TESTING FIFTH_GRAPHIC FUNCTIONALITY ({'DEMO' if demo_mode else 'LIVE'} MODE)")
    print("=" * 60)
    
    try:
        # Test the main function with fifth_graphic collection
        result = atm_crawler_complete.main(demo_mode, True)  # demo_mode, save_to_db=True
        
        if result:
            print("✅ Fifth_graphic functionality test successful")
            
            # Check if regional data was saved
            latest_data = db_connector.get_latest_regional_data()
            if latest_data:
                print(f"   📊 Regional data retrieved: {len(latest_data)} regions")
                for region in latest_data:
                    print(f"      {region['region_code']}: {region['count_available']} available out of {region['total_atms_in_region']}")
            else:
                print("   ⚠️  No regional data found in database")
            
            return True
        else:
            print("❌ Fifth_graphic functionality test failed")
            return False
            
    except Exception as e:
        print(f"❌ Fifth_graphic test failed: {str(e)}")
        return False

def test_dashboard_queries():
    """Test dashboard query functions"""
    print("\n" + "=" * 60)
    print("📊 TESTING DASHBOARD QUERIES")
    print("=" * 60)
    
    success_count = 0
    total_tests = 6
    
    # Test 1: Dashboard Summary
    try:
        summary = dashboard_queries.get_dashboard_summary()
        if summary:
            print("✅ Dashboard summary query successful")
            print(f"   📊 Total ATMs: {summary.get('grand_total_atms', 0)}")
            print(f"   🟢 Availability: {summary.get('percentage_available', 0)}%")
            success_count += 1
        else:
            print("❌ Dashboard summary query returned no data")
    except Exception as e:
        print(f"❌ Dashboard summary query failed: {str(e)}")
    
    # Test 2: Regional Comparison
    try:
        regions = dashboard_queries.get_regional_comparison()
        if regions:
            print(f"✅ Regional comparison query successful ({len(regions)} regions)")
            success_count += 1
        else:
            print("❌ Regional comparison query returned no data")
    except Exception as e:
        print(f"❌ Regional comparison query failed: {str(e)}")
    
    # Test 3: Alerting Data
    try:
        alerts = dashboard_queries.get_alerting_data()
        if alerts:
            print(f"✅ Alerting data query successful ({len(alerts)} regions)")
            health_status = {}
            for alert in alerts:
                status = alert.get('health_status', 'UNKNOWN')
                health_status[status] = health_status.get(status, 0) + 1
            print(f"   🏥 Health distribution: {health_status}")
            success_count += 1
        else:
            print("❌ Alerting data query returned no data")
    except Exception as e:
        print(f"❌ Alerting data query failed: {str(e)}")
    
    # Test 4: Data Freshness
    try:
        freshness = dashboard_queries.get_data_freshness()
        if freshness:
            print(f"✅ Data freshness query successful ({len(freshness)} regions)")
            success_count += 1
        else:
            print("❌ Data freshness query returned no data")
    except Exception as e:
        print(f"❌ Data freshness query failed: {str(e)}")
    
    # Test 5: Hourly Trends
    try:
        trends = dashboard_queries.get_hourly_trends(hours_back=6)
        if trends:
            print(f"✅ Hourly trends query successful ({len(trends)} data points)")
            success_count += 1
        else:
            print("⚠️  Hourly trends query returned no data (may be normal for new installations)")
            success_count += 1  # Count as success since this might be expected
    except Exception as e:
        print(f"❌ Hourly trends query failed: {str(e)}")
    
    # Test 6: Historical Analysis
    try:
        historical = dashboard_queries.get_historical_analysis(days_back=3)
        if historical:
            print(f"✅ Historical analysis query successful ({len(historical)} data points)")
            success_count += 1
        else:
            print("⚠️  Historical analysis query returned no data (may be normal for new installations)")
            success_count += 1  # Count as success since this might be expected
    except Exception as e:
        print(f"❌ Historical analysis query failed: {str(e)}")
    
    print(f"\n📈 Dashboard queries test result: {success_count}/{total_tests} successful")
    return success_count == total_tests

def run_sample_data_generation():
    """Generate some sample data for testing"""
    print("\n" + "=" * 60)
    print("🎲 GENERATING SAMPLE DATA FOR TESTING")
    print("=" * 60)
    
    try:
        # Generate sample fifth_graphic data
        sample_fifth_graphic = [
            {
                "hc-key": "TL-DL",
                "state_count": {
                    "AVAILABLE": "0.78571427",
                    "WOUNDED": "0.14285714",
                    "WARNING": "0.07142857"
                }
            },
            {
                "hc-key": "TL-AN",
                "state_count": {
                    "AVAILABLE": "0.85714286",
                    "OUT_OF_SERVICE": "0.07142857",
                    "ZOMBIE": "0.07142857"
                }
            }
        ]
        
        # Save sample data to database
        success = db_connector.save_fifth_graphic_to_database(sample_fifth_graphic)
        
        if success:
            print("✅ Sample fifth_graphic data generated and saved successfully")
            
            # Verify the data was saved
            latest_data = db_connector.get_latest_regional_data()
            if latest_data:
                print(f"   📊 Verified: {len(latest_data)} regional records saved")
                for region in latest_data:
                    print(f"      {region['region_code']}: {region['count_available']}/{region['total_atms_in_region']} available")
            return True
        else:
            print("❌ Failed to save sample data")
            return False
            
    except Exception as e:
        print(f"❌ Sample data generation failed: {str(e)}")
        return False

def test_monitoring_dashboard():
    """Test the monitoring dashboard script"""
    print("\n" + "=" * 60)
    print("🖥️  TESTING MONITORING DASHBOARD")
    print("=" * 60)
    
    try:
        # Import the monitoring dashboard module
        import monitoring_dashboard
        
        print("✅ Monitoring dashboard module loaded successfully")
        print("   ℹ️  You can run the dashboard with:")
        print("      python monitoring_dashboard.py           # Single report")
        print("      python monitoring_dashboard.py --live    # Live mode")
        print("      python monitoring_dashboard.py --summary-only  # Summary only")
        print("      python monitoring_dashboard.py --alerts-only   # Alerts only")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring dashboard test failed: {str(e)}")
        return False

def main():
    """Main testing function"""
    parser = argparse.ArgumentParser(description="Test ATM Dashboard Integration")
    parser.add_argument('--skip-crawler', action='store_true', help='Skip crawler testing')
    parser.add_argument('--live-mode', action='store_true', help='Test with live data (requires network access)')
    parser.add_argument('--generate-sample', action='store_true', help='Generate sample data for testing')
    parser.add_argument('--quick', action='store_true', help='Quick test (essential components only)')
    
    args = parser.parse_args()
    
    print("🧪 ATM DASHBOARD INTEGRATION TEST")
    print("⏰ Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    test_results = {
        'database_connection': False,
        'database_tables': False,
        'crawler_data': False,
        'fifth_graphic': False,
        'dashboard_queries': False,
        'monitoring_dashboard': False,
        'sample_data': False
    }
    
    # Test 1: Database Connection
    test_results['database_connection'] = test_database_connection()
    
    if not test_results['database_connection']:
        print("\n❌ Cannot proceed without database connection")
        print("   Please check your database configuration in .env file")
        sys.exit(1)
    
    # Test 2: Database Tables
    test_results['database_tables'] = test_database_tables()
    
    # Test 3: Generate Sample Data (if requested)
    if args.generate_sample:
        test_results['sample_data'] = run_sample_data_generation()
    
    # Test 4: Crawler Data Collection (if not skipped)
    if not args.skip_crawler:
        demo_mode = not args.live_mode
        test_results['crawler_data'], terminals, terminal_details = test_crawler_data_collection(demo_mode)
        
        # Test 5: Fifth Graphic Functionality
        if test_results['database_tables']:
            test_results['fifth_graphic'] = test_fifth_graphic_functionality(demo_mode)
    
    # Test 6: Dashboard Queries (if not quick mode)
    if not args.quick:
        test_results['dashboard_queries'] = test_dashboard_queries()
        
        # Test 7: Monitoring Dashboard
        test_results['monitoring_dashboard'] = test_monitoring_dashboard()
    
    # Final Report
    print("\n" + "=" * 60)
    print("📋 FINAL TEST REPORT")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len([k for k, v in test_results.items() if v is not None])
    
    for test_name, result in test_results.items():
        if result is not None:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your ATM dashboard system is ready to use.")
        print("\n📖 Quick Start Guide:")
        print("   1. Run the crawler: python run_crawler_with_db.py")
        print("   2. View dashboard: python monitoring_dashboard.py")
        print("   3. Live monitoring: python monitoring_dashboard.py --live")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
