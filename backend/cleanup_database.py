#!/usr/bin/env python3
"""
Database Cleanup Script for ATM Data Retrieval System
This script will clean up all data in the ATM database tables while preserving table structure
"""

import sys
import os
from datetime import datetime
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_connector_new import DatabaseConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s",
    handlers=[
        logging.FileHandler("database_cleanup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("DatabaseCleanup")

def confirm_cleanup():
    """Ask user for confirmation before proceeding with cleanup"""
    print("=" * 80)
    print("⚠️  DATABASE CLEANUP WARNING")
    print("=" * 80)
    print("This operation will DELETE ALL DATA from the following tables:")
    print("- regional_data")
    print("- terminal_details") 
    print("- regional_atm_counts (legacy)")
    print()
    print("The table structures will be preserved, but all data will be lost.")
    print("This action CANNOT BE UNDONE!")
    print()
    
    response = input("Are you sure you want to proceed? Type 'YES' to continue: ")
    return response.upper() == 'YES'

def get_table_stats(connector):
    """Get current table statistics before cleanup"""
    print("\n=== CURRENT DATABASE STATE ===")
    
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return {}
    
    cursor = conn.cursor()
    stats = {}
    
    tables = ['regional_data', 'terminal_details', 'regional_atm_counts']
    
    try:
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                count = result[0] if result else 0
                stats[table] = count
                print(f"{table}: {count} records")
            except Exception as e:
                stats[table] = f"Error: {e}"
                print(f"{table}: Error - {e}")
        
        return stats
        
    except Exception as e:
        log.error(f"Error getting table stats: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def cleanup_database(connector):
    """Clean up all data from ATM tables"""
    print("\n=== STARTING DATABASE CLEANUP ===")
    
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Tables to clean up (in order to handle foreign key constraints)
        tables_to_clean = [
            'terminal_details',
            'regional_data', 
            'regional_atm_counts'
        ]
        
        cleanup_results = {}
        
        for table in tables_to_clean:
            try:
                log.info(f"Cleaning table: {table}")
                
                # Get count before cleanup
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                before_count = result[0] if result else 0
                
                # Delete all records
                cursor.execute(f"DELETE FROM {table}")
                
                # Reset auto-increment sequence
                cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
                
                # Get count after cleanup
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                after_count = result[0] if result else 0
                
                cleanup_results[table] = {
                    'before': before_count,
                    'after': after_count,
                    'deleted': before_count - after_count
                }
                
                print(f"✅ {table}: {before_count} → {after_count} records (deleted {before_count - after_count})")
                
            except Exception as e:
                cleanup_results[table] = {'error': str(e)}
                print(f"❌ {table}: Error - {e}")
                log.error(f"Error cleaning {table}: {e}")
        
        # Commit all changes
        conn.commit()
        log.info("Database cleanup completed successfully")
        
        return cleanup_results
        
    except Exception as e:
        conn.rollback()
        log.error(f"Error during database cleanup: {e}")
        print(f"❌ Database cleanup failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def vacuum_database(connector):
    """Run VACUUM to reclaim space after cleanup"""
    print("\n=== OPTIMIZING DATABASE ===")
    
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Cannot connect to database for optimization")
        return False
    
    # Set autocommit for VACUUM
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        tables = ['regional_data', 'terminal_details', 'regional_atm_counts']
        
        for table in tables:
            try:
                log.info(f"Vacuuming table: {table}")
                cursor.execute(f"VACUUM ANALYZE {table}")
                print(f"✅ Optimized {table}")
            except Exception as e:
                print(f"⚠️  {table}: Optimization warning - {e}")
                log.warning(f"Vacuum warning for {table}: {e}")
        
        return True
        
    except Exception as e:
        log.error(f"Error during database optimization: {e}")
        print(f"❌ Database optimization failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_cleanup(connector):
    """Verify that cleanup was successful"""
    print("\n=== VERIFYING CLEANUP ===")
    
    table_info = connector.get_table_info()
    
    if not table_info.get('tables'):
        print("❌ Cannot verify cleanup - no table information available")
        return False
    
    all_empty = True
    for table in ['regional_data', 'terminal_details', 'regional_atm_counts']:
        if table in table_info.get('tables', []):
            count = table_info.get('row_counts', {}).get(table, 'Unknown')
            if isinstance(count, int):
                if count == 0:
                    print(f"✅ {table}: Empty (0 records)")
                else:
                    print(f"❌ {table}: Still has {count} records")
                    all_empty = False
            else:
                print(f"⚠️  {table}: {count}")
    
    return all_empty

def main():
    """Main cleanup function"""
    print("=" * 80)
    print("ATM DATA RETRIEVAL SYSTEM - DATABASE CLEANUP")
    print("=" * 80)
    print(f"Cleanup started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database configuration info
    print("Database Configuration:")
    print("  Host: 88.222.214.26")
    print("  Port: 5432") 
    print("  Database: development_db")
    print("  Username: timlesdev")
    print()
    
    # Initialize database connector
    log.info("Initializing database connector...")
    connector = DatabaseConnector()
    
    # Test connection
    if not connector.test_connection():
        print("❌ FAILED: Cannot connect to database")
        return False
    
    # Get current state
    stats_before = get_table_stats(connector)
    
    # Confirm cleanup
    if not confirm_cleanup():
        print("\n❌ Cleanup cancelled by user")
        return False
    
    # Perform cleanup
    cleanup_results = cleanup_database(connector)
    if not cleanup_results:
        print("\n❌ Cleanup failed")
        return False
    
    # Optimize database
    vacuum_success = vacuum_database(connector)
    
    # Verify cleanup
    verification_success = verify_cleanup(connector)
    
    # Final summary
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    
    total_deleted = 0
    if isinstance(cleanup_results, dict):
        for table, result in cleanup_results.items():
            if isinstance(result, dict) and 'deleted' in result:
                deleted = result['deleted']
                total_deleted += deleted
                print(f"{table}: {deleted} records deleted")
            elif isinstance(result, dict) and 'error' in result:
                print(f"{table}: Error - {result['error']}")
    
    print(f"\nTotal records deleted: {total_deleted}")
    print(f"Database optimization: {'✅ Success' if vacuum_success else '❌ Failed'}")
    print(f"Verification: {'✅ All tables empty' if verification_success else '❌ Some tables not empty'}")
    
    if verification_success:
        print("\n🎉 DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
        print()
        print("Your database is now in a clean state and ready for:")
        print("1. Fresh ATM data collection")
        print("2. Testing with demo mode")
        print("3. Production data retrieval")
        print()
        print("Next steps:")
        print("- Run: python combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables")
        print("- Monitor logs for successful data insertion")
    else:
        print("\n⚠️  CLEANUP INCOMPLETE")
        print("Some tables may still contain data. Please check the errors above.")
    
    print("=" * 80)
    
    return verification_success

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nCleanup completed successfully!")
            sys.exit(0)
        else:
            print("\nCleanup failed or incomplete!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error during cleanup: {e}")
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
