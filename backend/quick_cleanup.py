#!/usr/bin/env python3
"""
Quick Database Cleanup Script for ATM Data Retrieval System
"""

from db_connector_new import DatabaseConnector
import sys

def cleanup_database():
    """Clean up all data from ATM tables"""
    print("Starting database cleanup...")
    
    connector = DatabaseConnector()
    
    # Test connection
    if not connector.test_connection():
        print("❌ Cannot connect to database")
        return False
    
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Cannot get database connection")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Get current counts
        print("\nCurrent data counts:")
        tables = ['regional_data', 'terminal_details', 'regional_atm_counts']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                count = result[0] if result else 0
                print(f"  {table}: {count} records")
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        print("\nCleaning up tables...")
        
        # Clean up tables
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
                print(f"✅ Cleaned {table}")
            except Exception as e:
                print(f"❌ Error cleaning {table}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify cleanup
        print("\nVerifying cleanup:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                count = result[0] if result else 0
                print(f"  {table}: {count} records")
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        print("\n✅ Database cleanup completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Database cleanup failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    cleanup_database()
