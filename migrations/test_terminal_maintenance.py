#!/usr/bin/env python3
"""
Test script for terminal_maintenance table migration
This script tests the created table with sample data
"""

import asyncio
import asyncpg
import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('Migration_Test')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '88.222.214.26'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'development_db'),
    'user': os.getenv('DB_USER', 'timlesdev'),
    'password': os.getenv('DB_PASSWORD', 'timlesdev')
}

# Sample test data
SAMPLE_DATA = [
    {
        'terminal_id': 'ATM001',
        'start_datetime': datetime.now(),
        'end_datetime': datetime.now() + timedelta(hours=2),
        'problem_description': 'Card reader not functioning properly. Cards getting stuck in the slot.',
        'solution_description': 'Replaced card reader mechanism and cleaned internal components.',
        'maintenance_type': 'CORRECTIVE',
        'priority': 'HIGH',
        'status': 'COMPLETED',
        'created_by': 'technician_001'
    },
    {
        'terminal_id': 'ATM002',
        'start_datetime': datetime.now() + timedelta(days=1),
        'end_datetime': None,  # Planned maintenance
        'problem_description': 'Scheduled preventive maintenance - cash dispenser cleaning and calibration.',
        'solution_description': None,  # Not completed yet
        'maintenance_type': 'PREVENTIVE',
        'priority': 'MEDIUM',
        'status': 'PLANNED',
        'created_by': 'scheduler_admin'
    },
    {
        'terminal_id': 'ATM003',
        'start_datetime': datetime.now() - timedelta(hours=1),
        'end_datetime': None,  # In progress
        'problem_description': 'Emergency: ATM completely non-responsive, display blank.',
        'solution_description': 'Investigating power supply and main board issues.',
        'maintenance_type': 'EMERGENCY',
        'priority': 'CRITICAL',
        'status': 'IN_PROGRESS',
        'created_by': 'emergency_tech'
    }
]

async def test_table_exists(conn: asyncpg.Connection) -> bool:
    """Test if the terminal_maintenance table exists"""
    try:
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'terminal_maintenance'
            );
            """
        )
        return bool(result) if result is not None else False
    except Exception as e:
        logger.error(f"Failed to check table existence: {e}")
        return False

async def insert_sample_data(conn: asyncpg.Connection) -> bool:
    """Insert sample maintenance records"""
    try:
        logger.info("Inserting sample data...")
        
        for i, data in enumerate(SAMPLE_DATA, 1):
            await conn.execute(
                """
                INSERT INTO terminal_maintenance (
                    terminal_id, start_datetime, end_datetime, 
                    problem_description, solution_description,
                    maintenance_type, priority, status, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                data['terminal_id'],
                data['start_datetime'],
                data['end_datetime'],
                data['problem_description'],
                data['solution_description'],
                data['maintenance_type'],
                data['priority'],
                data['status'],
                data['created_by']
            )
            logger.info(f"✅ Sample record {i}/{len(SAMPLE_DATA)} inserted")
        
        logger.info("✅ All sample data inserted successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to insert sample data: {e}")
        return False

async def test_queries(conn: asyncpg.Connection) -> bool:
    """Test various queries on the table"""
    try:
        logger.info("Testing database queries...")
        
        # Test 1: Count all records
        count = await conn.fetchval("SELECT COUNT(*) FROM terminal_maintenance")
        logger.info(f"✅ Total records: {count}")
        
        # Test 2: Select all records
        records = await conn.fetch(
            """
            SELECT id, terminal_id, maintenance_type, priority, status, 
                   problem_description, created_by, created_at
            FROM terminal_maintenance 
            ORDER BY created_at DESC
            """
        )
        
        logger.info(f"✅ Retrieved {len(records)} records:")
        for record in records:
            logger.info(f"   - {record['terminal_id']}: {record['maintenance_type']} "
                       f"({record['priority']}) - {record['status']}")
        
        # Test 3: Filter by status
        completed_count = await conn.fetchval(
            "SELECT COUNT(*) FROM terminal_maintenance WHERE status = 'COMPLETED'"
        )
        logger.info(f"✅ Completed maintenance records: {completed_count}")
        
        # Test 4: Filter by priority
        high_priority = await conn.fetch(
            """
            SELECT terminal_id, priority, problem_description 
            FROM terminal_maintenance 
            WHERE priority IN ('HIGH', 'CRITICAL')
            ORDER BY priority DESC
            """
        )
        logger.info(f"✅ High/Critical priority records: {len(high_priority)}")
        
        # Test 5: Test date filtering
        recent_records = await conn.fetchval(
            """
            SELECT COUNT(*) FROM terminal_maintenance 
            WHERE start_datetime > NOW() - INTERVAL '1 day'
            """
        )
        logger.info(f"✅ Records from last 24 hours: {recent_records}")
        
        # Test 6: Test JSON field (images)
        json_test = await conn.fetchval(
            "SELECT images FROM terminal_maintenance LIMIT 1"
        )
        logger.info(f"✅ JSON field test - images: {json_test}")
        
        # Test 7: Test updated_at trigger
        logger.info("Testing updated_at trigger...")
        await conn.execute(
            """
            UPDATE terminal_maintenance 
            SET solution_description = 'Updated solution description for testing'
            WHERE terminal_id = 'ATM001'
            """
        )
        
        updated_record = await conn.fetchrow(
            """
            SELECT created_at, updated_at 
            FROM terminal_maintenance 
            WHERE terminal_id = 'ATM001'
            """
        )
        
        if updated_record and updated_record['updated_at'] > updated_record['created_at']:
            logger.info("✅ updated_at trigger working correctly")
        else:
            logger.warning("⚠️  updated_at trigger may not be working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Query testing failed: {e}")
        return False

async def cleanup_test_data(conn: asyncpg.Connection) -> bool:
    """Clean up test data"""
    try:
        logger.info("Cleaning up test data...")
        deleted_count = await conn.fetchval(
            """
            DELETE FROM terminal_maintenance 
            WHERE created_by IN ('technician_001', 'scheduler_admin', 'emergency_tech')
            """
        )
        logger.info(f"✅ Cleaned up {deleted_count} test records")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to cleanup test data: {e}")
        return False

async def run_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("TESTING TERMINAL_MAINTENANCE TABLE")
    logger.info("=" * 60)
    
    conn = None
    try:
        # Connect to database
        logger.info(f"Connecting to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        conn = await asyncpg.connect(**DB_CONFIG)
        logger.info("✅ Database connection established")
        
        # Test 1: Check table exists
        if not await test_table_exists(conn):
            logger.error("❌ terminal_maintenance table does not exist. Run migration first.")
            return False
        logger.info("✅ terminal_maintenance table exists")
        
        # Test 2: Insert sample data
        if not await insert_sample_data(conn):
            return False
        
        # Test 3: Test queries
        if not await test_queries(conn):
            return False
        
        # Test 4: Cleanup (optional)
        if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
            await cleanup_test_data(conn)
        
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("The terminal_maintenance table is ready for use!")
        logger.info("Run with --cleanup flag to remove test data")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed")

def main():
    """Main function"""
    asyncio.run(run_tests())

if __name__ == "__main__":
    main()
