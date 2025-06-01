#!/usr/bin/env python3
"""
Database Cleanup Script - Remove TL-AN Test Data

This script removes test data for TL-AN region from the database
to ensure the API returns only real production data.

Author: ATM Monitoring System
Created: 2025-06-01
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'dash',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

async def main():
    """Main cleanup function"""
    print("🗑️  ATM Database Cleanup - Remove TL-AN Test Data")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Connect to database
        print("📡 Connecting to database...")
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Database connected successfully")
        print()
        
        # First, let's examine the current data
        print("📊 Current data analysis:")
        print("-" * 40)
        
        # Check regional_data table
        query = """
            SELECT region_code, COUNT(*) as record_count, 
                   MIN(retrieval_timestamp) as first_record,
                   MAX(retrieval_timestamp) as last_record
            FROM regional_data 
            GROUP BY region_code 
            ORDER BY region_code
        """
        
        rows = await conn.fetch(query)
        
        for row in rows:
            print(f"Region: {row['region_code']}")
            print(f"  Records: {row['record_count']}")
            print(f"  First: {row['first_record']}")
            print(f"  Last: {row['last_record']}")
            print()
        
        # Check if TL-AN exists
        tl_an_check = await conn.fetchval(
            "SELECT COUNT(*) FROM regional_data WHERE region_code = 'TL-AN'"
        )
        
        if tl_an_check == 0:
            print("ℹ️  No TL-AN data found in database. Nothing to clean up.")
            return
        
        print(f"🎯 Found {tl_an_check} TL-AN records to remove")
        
        # Proceed with deletion (non-interactive mode)
        print("\n🗑️  Proceeding to remove TL-AN data...")
        print("⚠️  This will delete all TL-AN test data from the database")
        
        print("\n🗑️  Removing TL-AN data...")
        
        # Delete TL-AN data from regional_data table
        delete_count = await conn.execute(
            "DELETE FROM regional_data WHERE region_code = 'TL-AN'"
        )
        
        print(f"✅ Deleted {delete_count.split()[-1] if delete_count else 0} records from regional_data")
        
        # Check if there's a terminal_details table and clean it too
        try:
            terminal_details_count = await conn.fetchval(
                "SELECT COUNT(*) FROM terminal_details WHERE region_code = 'TL-AN'"
            )
            
            if terminal_details_count > 0:
                delete_terminal_count = await conn.execute(
                    "DELETE FROM terminal_details WHERE region_code = 'TL-AN'"
                )
                print(f"✅ Deleted {delete_terminal_count.split()[-1] if delete_terminal_count else 0} records from terminal_details")
            
        except Exception as e:
            print(f"ℹ️  No terminal_details table or no TL-AN data in it: {e}")
        
        print("\n📊 Updated data summary:")
        print("-" * 40)
        
        # Show remaining data
        remaining_rows = await conn.fetch(query)
        
        for row in remaining_rows:
            print(f"Region: {row['region_code']}")
            print(f"  Records: {row['record_count']}")
            print(f"  First: {row['first_record']}")
            print(f"  Last: {row['last_record']}")
            print()
        
        print("✅ Cleanup completed successfully!")
        print("🚀 Your API will now return only production data (TL-DL)")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        print("Please check your database connection and try again.")
        
    finally:
        if 'conn' in locals():
            await conn.close()
            print("📡 Database connection closed")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
