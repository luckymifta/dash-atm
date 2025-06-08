#!/usr/bin/env python3
"""
Quick database query script to check the data inserted by the ATM retrieval system
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_connector_new import DatabaseConnector

def query_regional_data():
    """Query and display regional data"""
    print("=== REGIONAL DATA ===")
    
    connector = DatabaseConnector()
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    try:
        # Get recent regional data
        cursor.execute("""
            SELECT 
                id,
                unique_request_id,
                region_code,
                retrieval_timestamp,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                total_atms_in_region
            FROM regional_data 
            ORDER BY retrieval_timestamp DESC 
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"Found {len(rows)} regional data records:")
            print("-" * 120)
            print(f"{'ID':<4} {'Region':<8} {'Timestamp':<20} {'Avail':<6} {'Warn':<5} {'Zomb':<5} {'Wound':<6} {'OutSvc':<7} {'Total':<6}")
            print("-" * 120)
            
            for row in rows:
                timestamp = row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else 'None'
                print(f"{row[0]:<4} {row[2]:<8} {timestamp:<20} {row[4]:<6} {row[5]:<5} {row[6]:<5} {row[7]:<6} {row[8]:<7} {row[9]:<6}")
        else:
            print("No regional data found")
            
    except Exception as e:
        print(f"Error querying regional data: {e}")
    finally:
        cursor.close()
        conn.close()

def query_terminal_details():
    """Query and display terminal details"""
    print("\n=== TERMINAL DETAILS ===")
    
    connector = DatabaseConnector()
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    try:
        # Get recent terminal details
        cursor.execute("""
            SELECT 
                id,
                terminal_id,
                location,
                issue_state_name,
                fetched_status,
                retrieved_date,
                fault_data->>'agentErrorDescription' as error_description
            FROM terminal_details 
            ORDER BY retrieved_date DESC 
            LIMIT 15
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"Found {len(rows)} terminal detail records:")
            print("-" * 120)
            print(f"{'ID':<4} {'TermID':<8} {'Location':<20} {'State':<12} {'Status':<12} {'Error':<25}")
            print("-" * 120)
            
            for row in rows:
                location = (row[2][:17] + '...') if row[2] and len(row[2]) > 20 else (row[2] or 'N/A')
                error = (row[6][:22] + '...') if row[6] and len(row[6]) > 25 else (row[6] or 'N/A')
                print(f"{row[0]:<4} {row[1]:<8} {location:<20} {row[3] or 'N/A':<12} {row[4] or 'N/A':<12} {error:<25}")
        else:
            print("No terminal details found")
            
    except Exception as e:
        print(f"Error querying terminal details: {e}")
    finally:
        cursor.close()
        conn.close()

def query_summary_stats():
    """Query and display summary statistics"""
    print("\n=== SUMMARY STATISTICS ===")
    
    connector = DatabaseConnector()
    conn = connector.get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    try:
        # Regional data count
        cursor.execute("SELECT COUNT(*) FROM regional_data")
        regional_count = cursor.fetchone()[0]
        
        # Terminal details count
        cursor.execute("SELECT COUNT(*) FROM terminal_details")
        terminal_count = cursor.fetchone()[0]
        
        # Latest regional data timestamp
        cursor.execute("SELECT MAX(retrieval_timestamp) FROM regional_data")
        latest_regional = cursor.fetchone()[0]
        
        # Latest terminal details timestamp
        cursor.execute("SELECT MAX(retrieved_date) FROM terminal_details")
        latest_terminal = cursor.fetchone()[0]
        
        print(f"Regional data records: {regional_count}")
        print(f"Terminal detail records: {terminal_count}")
        print(f"Latest regional data: {latest_regional}")
        print(f"Latest terminal details: {latest_terminal}")
        
        # Status distribution
        cursor.execute("""
            SELECT fetched_status, COUNT(*) 
            FROM terminal_details 
            GROUP BY fetched_status 
            ORDER BY COUNT(*) DESC
        """)
        
        status_dist = cursor.fetchall()
        if status_dist:
            print("\nTerminal status distribution:")
            for status, count in status_dist:
                print(f"  {status}: {count}")
                
    except Exception as e:
        print(f"Error querying summary stats: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    print("=" * 80)
    print("ATM DATA RETRIEVAL SYSTEM - DATABASE QUERY")
    print("=" * 80)
    print(f"Query time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test connection first
    connector = DatabaseConnector()
    if not connector.test_connection():
        print("❌ Cannot connect to database")
        return
    
    # Run queries
    query_regional_data()
    query_terminal_details()
    query_summary_stats()
    
    print("\n" + "=" * 80)
    print("Query completed successfully!")

if __name__ == "__main__":
    main()
