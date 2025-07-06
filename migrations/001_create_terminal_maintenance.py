#!/usr/bin/env python3
"""
Database Migration Script: Create Terminal Maintenance Table
Migration: 001_create_terminal_maintenance
Date: 2025-01-30
Description: Creates the terminal_maintenance table with proper constraints,
             indexes, and foreign key relationships as specified in PRD.md

This script creates:
1. terminal_maintenance table with all required fields
2. Performance indexes for optimal query performance
3. Foreign key constraint to terminal_details table
4. Check constraints for data validation
"""

import asyncio
import asyncpg
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Migration_001')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '88.222.214.26'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'development_db'),
    'user': os.getenv('DB_USER', 'timlesdev'),
    'password': os.getenv('DB_PASSWORD', 'timlesdev')
}

# SQL statements for creating the table and indexes
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS terminal_maintenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    terminal_id VARCHAR(50) NOT NULL,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE,
    problem_description TEXT NOT NULL,
    solution_description TEXT,
    maintenance_type VARCHAR(20) DEFAULT 'CORRECTIVE' 
        CHECK (maintenance_type IN ('PREVENTIVE', 'CORRECTIVE', 'EMERGENCY')),
    priority VARCHAR(10) DEFAULT 'MEDIUM' 
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(20) DEFAULT 'PLANNED' 
        CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    images JSONB DEFAULT '[]',
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

# Foreign key constraint (will be added after checking if terminal_details exists)
ADD_FOREIGN_KEY_SQL = """
ALTER TABLE terminal_maintenance 
ADD CONSTRAINT fk_terminal_maintenance_terminal 
FOREIGN KEY (terminal_id) REFERENCES terminal_details(terminal_id) ON DELETE CASCADE;
"""

# Performance indexes
CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_terminal_id ON terminal_maintenance(terminal_id);",
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_start_datetime ON terminal_maintenance(start_datetime);",
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_status ON terminal_maintenance(status);",
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_created_by ON terminal_maintenance(created_by);",
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_maintenance_type ON terminal_maintenance(maintenance_type);",
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_priority ON terminal_maintenance(priority);",
    "CREATE INDEX IF NOT EXISTS idx_terminal_maintenance_created_at ON terminal_maintenance(created_at);"
]

# Trigger for updating updated_at timestamp
CREATE_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION update_terminal_maintenance_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_terminal_maintenance_updated_at ON terminal_maintenance;

CREATE TRIGGER trigger_update_terminal_maintenance_updated_at
    BEFORE UPDATE ON terminal_maintenance
    FOR EACH ROW
    EXECUTE FUNCTION update_terminal_maintenance_updated_at();
"""

# Rollback SQL (for testing purposes)
ROLLBACK_SQL = """
DROP TRIGGER IF EXISTS trigger_update_terminal_maintenance_updated_at ON terminal_maintenance;
DROP FUNCTION IF EXISTS update_terminal_maintenance_updated_at();
DROP TABLE IF EXISTS terminal_maintenance CASCADE;
"""

async def check_terminal_details_table(conn: asyncpg.Connection) -> bool:
    """Check if terminal_details table exists"""
    try:
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'terminal_details'
            );
            """
        )
        return bool(result) if result is not None else False
    except Exception as e:
        logger.warning(f"Could not check for terminal_details table: {e}")
        return False

async def check_terminal_id_column(conn: asyncpg.Connection) -> bool:
    """Check if terminal_details table has terminal_id column"""
    try:
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'terminal_details'
                AND column_name = 'terminal_id'
            );
            """
        )
        return bool(result) if result is not None else False
    except Exception as e:
        logger.warning(f"Could not check for terminal_id column: {e}")
        return False

async def create_terminal_maintenance_table(conn: asyncpg.Connection) -> bool:
    """Create the terminal_maintenance table"""
    try:
        logger.info("Creating terminal_maintenance table...")
        await conn.execute(CREATE_TABLE_SQL)
        logger.info("✅ terminal_maintenance table created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create terminal_maintenance table: {e}")
        return False

async def add_foreign_key_constraint(conn: asyncpg.Connection) -> bool:
    """Add foreign key constraint to terminal_details if table exists"""
    try:
        # Check if terminal_details table exists
        if not await check_terminal_details_table(conn):
            logger.warning("⚠️  terminal_details table not found. Skipping foreign key constraint.")
            logger.info("Note: You'll need to add the foreign key constraint manually when terminal_details is available")
            return True
            
        # Check if terminal_id column exists
        if not await check_terminal_id_column(conn):
            logger.warning("⚠️  terminal_id column not found in terminal_details. Skipping foreign key constraint.")
            return True
            
        logger.info("Adding foreign key constraint...")
        await conn.execute(ADD_FOREIGN_KEY_SQL)
        logger.info("✅ Foreign key constraint added successfully")
        return True
    except Exception as e:
        # Check if constraint already exists
        if "already exists" in str(e).lower():
            logger.info("ℹ️  Foreign key constraint already exists")
            return True
        logger.warning(f"⚠️  Failed to add foreign key constraint: {e}")
        logger.info("Note: You can add this constraint manually later when terminal_details is available")
        return True  # Don't fail the migration for this

async def create_indexes(conn: asyncpg.Connection) -> bool:
    """Create performance indexes"""
    try:
        logger.info("Creating performance indexes...")
        for i, index_sql in enumerate(CREATE_INDEXES_SQL, 1):
            await conn.execute(index_sql)
            logger.info(f"✅ Index {i}/{len(CREATE_INDEXES_SQL)} created")
        logger.info("✅ All performance indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        return False

async def create_trigger(conn: asyncpg.Connection) -> bool:
    """Create trigger for automatic updated_at timestamp"""
    try:
        logger.info("Creating updated_at trigger...")
        await conn.execute(CREATE_TRIGGER_SQL)
        logger.info("✅ updated_at trigger created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create trigger: {e}")
        return False

async def verify_table_creation(conn: asyncpg.Connection) -> bool:
    """Verify that the table was created successfully"""
    try:
        # Check table exists
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'terminal_maintenance'
            );
            """
        )
        
        if not table_exists:
            logger.error("❌ Table verification failed: terminal_maintenance table not found")
            return False
            
        # Check columns
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'terminal_maintenance'
            ORDER BY ordinal_position;
            """
        )
        
        logger.info("✅ Table verification successful:")
        logger.info(f"   - Table 'terminal_maintenance' exists")
        logger.info(f"   - Columns count: {len(columns)}")
        
        for col in columns:
            logger.info(f"   - {col['column_name']}: {col['data_type']} "
                       f"{'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Check indexes
        indexes = await conn.fetch(
            """
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'terminal_maintenance';
            """
        )
        
        logger.info(f"   - Indexes count: {len(indexes)}")
        for idx in indexes:
            logger.info(f"   - Index: {idx['indexname']}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Table verification failed: {e}")
        return False

async def run_migration():
    """Run the complete migration"""
    logger.info("=" * 60)
    logger.info("STARTING MIGRATION: 001_create_terminal_maintenance")
    logger.info("=" * 60)
    
    conn = None
    try:
        # Connect to database
        logger.info(f"Connecting to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        conn = await asyncpg.connect(**DB_CONFIG)
        logger.info("✅ Database connection established")
        
        # Run migration steps
        success = True
        
        # Step 1: Create table
        if not await create_terminal_maintenance_table(conn):
            success = False
            
        # Step 2: Add foreign key constraint
        if success and not await add_foreign_key_constraint(conn):
            success = False
            
        # Step 3: Create indexes
        if success and not await create_indexes(conn):
            success = False
            
        # Step 4: Create trigger
        if success and not await create_trigger(conn):
            success = False
            
        # Step 5: Verify table creation
        if success and not await verify_table_creation(conn):
            success = False
        
        if success:
            logger.info("=" * 60)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("Next steps:")
            logger.info("1. Review the created table structure")
            logger.info("2. Test the table with sample data")
            logger.info("3. Implement the FastAPI endpoints")
            logger.info("4. Create the frontend components")
        else:
            logger.error("=" * 60)
            logger.error("❌ MIGRATION FAILED")
            logger.error("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        return False
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed")
    
    return True

async def rollback_migration():
    """Rollback the migration (for testing purposes)"""
    logger.info("=" * 60)
    logger.info("ROLLING BACK MIGRATION: 001_create_terminal_maintenance")
    logger.info("=" * 60)
    
    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        logger.info("✅ Database connection established")
        
        await conn.execute(ROLLBACK_SQL)
        logger.info("✅ Migration rolled back successfully")
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

def main():
    """Main function to run the migration"""
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        asyncio.run(rollback_migration())
    else:
        asyncio.run(run_migration())

if __name__ == "__main__":
    main()
