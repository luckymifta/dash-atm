#!/usr/bin/env python3
"""
ATM Masters Table Creation Script
Creates the atm_masters table using database configuration from .env file
Includes Dili timezone (+0900) consistency with existing tables
"""

import os
import sys
import logging
from datetime import datetime
import pytz
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    log.info("Environment variables loaded from .env file")
except ImportError:
    log.warning("python-dotenv not installed. Using environment variables directly.")

# Database configuration from environment variables
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "88.222.214.26"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "development_db"),
    "user": os.environ.get("DB_USER", "timlesdev"),
    "password": os.environ.get("DB_PASS", "timlesdev")
}

def get_db_connection():
    """Create a database connection"""
    try:
        log.info(f"Connecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']} as {DB_CONFIG['user']}")
        
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        
        # Set timezone to Dili for consistency
        cursor = conn.cursor()
        cursor.execute("SET timezone = '+09:00';")
        conn.commit()
        cursor.close()
        
        log.info("Successfully connected to database with Dili timezone (+09:00)")
        return conn
        
    except psycopg2.OperationalError as e:
        log.error(f"Database connection error: {str(e)}")
        log.error("Please verify your database credentials and connection settings")
        return None
    except Exception as e:
        log.error(f"Unexpected database error: {str(e)}")
        return None

def create_atm_masters_table():
    """Create the atm_masters table with Dili timezone consistency"""
    
    conn = get_db_connection()
    if not conn:
        log.error("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        log.info("Creating atm_masters table...")
        
        # Create the atm_masters table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS atm_masters (
            -- Primary identifier
            id SERIAL PRIMARY KEY,
            terminal_id VARCHAR(50) UNIQUE NOT NULL,
            
            -- Basic ATM Information
            terminal_name VARCHAR(255),
            external_id VARCHAR(50),
            network_id VARCHAR(50),
            business_id VARCHAR(100),
            technical_code VARCHAR(100),
            
            -- Hardware Specifications
            brand VARCHAR(100) NOT NULL,                    -- Nautilus Hyosun, NCR, Diebold, Wincor Nixdorf
            model VARCHAR(100) NOT NULL,                    -- Monimax 5600, SelfServ 22e, 4900, ProCash 2100xe
            serial_number VARCHAR(100),
            
            -- Location Information
            location VARCHAR(500) NOT NULL,                 -- Primary location description
            location_type VARCHAR(100),                     -- Gas Station, Financial Institution Office, etc.
            address_line_1 VARCHAR(255),
            address_line_2 VARCHAR(255),
            city VARCHAR(100),
            region VARCHAR(100),                            -- TL-DL, TL-AN, etc.
            postal_code VARCHAR(20),
            country VARCHAR(50) DEFAULT 'Timor-Leste',
            
            -- Geographic Coordinates
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            geo_location VARCHAR(50),                       -- Region code for grouping
            
            -- Operational Information
            is_active BOOLEAN DEFAULT TRUE,
            installation_date DATE,
            last_maintenance_date DATE,
            next_maintenance_date DATE,
            service_period VARCHAR(100),
            maintenance_period VARCHAR(100),
            
            -- Metadata with Dili timezone (+0900)
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE '+09:00'),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE '+09:00'),
            created_by VARCHAR(100),
            updated_by VARCHAR(100),
            
            -- Constraints
            CONSTRAINT chk_coordinates CHECK (
                (latitude IS NULL AND longitude IS NULL) OR 
                (latitude IS NOT NULL AND longitude IS NOT NULL AND
                 latitude BETWEEN -90 AND 90 AND 
                 longitude BETWEEN -180 AND 180)
            ),
            CONSTRAINT chk_active_dates CHECK (
                installation_date IS NULL OR 
                installation_date <= CURRENT_DATE
            )
        );
        """
        
        cursor.execute(create_table_sql)
        log.info("✅ atm_masters table created successfully")
        
        # Create indexes for performance
        log.info("Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_atm_masters_terminal_id ON atm_masters(terminal_id);",
            "CREATE INDEX IF NOT EXISTS idx_atm_masters_brand_model ON atm_masters(brand, model);",
            "CREATE INDEX IF NOT EXISTS idx_atm_masters_location ON atm_masters(city, region);",
            "CREATE INDEX IF NOT EXISTS idx_atm_masters_active ON atm_masters(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_atm_masters_geo ON atm_masters(latitude, longitude) WHERE latitude IS NOT NULL;"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        log.info("✅ Indexes created successfully")
        
        # Create update timestamp trigger function with Dili timezone
        log.info("Creating update timestamp trigger...")
        
        trigger_function_sql = """
        CREATE OR REPLACE FUNCTION update_atm_masters_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP AT TIME ZONE '+09:00';
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        cursor.execute(trigger_function_sql)
        
        # Create trigger
        trigger_sql = """
        DROP TRIGGER IF EXISTS trigger_atm_masters_updated_at ON atm_masters;
        CREATE TRIGGER trigger_atm_masters_updated_at
            BEFORE UPDATE ON atm_masters
            FOR EACH ROW
            EXECUTE FUNCTION update_atm_masters_updated_at();
        """
        
        cursor.execute(trigger_sql)
        log.info("✅ Update timestamp trigger created successfully")
        
        # Commit all changes
        conn.commit()
        log.info("✅ All changes committed successfully")
        
        # Verify table creation
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'atm_masters' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        log.info(f"✅ Table verification: atm_masters has {len(columns)} columns")
        
        # Show table structure
        print("\n" + "="*80)
        print("ATM MASTERS TABLE STRUCTURE")
        print("="*80)
        print(f"{'Column Name':<25} {'Data Type':<20} {'Nullable':<10} {'Default'}")
        print("-"*80)
        
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            default_display = str(column_default)[:30] + "..." if column_default and len(str(column_default)) > 30 else str(column_default)
            print(f"{column_name:<25} {data_type:<20} {is_nullable:<10} {default_display}")
        
        print("="*80)
        
        return True
        
    except Exception as e:
        conn.rollback()
        log.error(f"Error creating atm_masters table: {str(e)}")
        return False
        
    finally:
        cursor.close()
        conn.close()

def verify_timezone_consistency():
    """Verify that the timezone is set correctly for Dili (+0900)"""
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Check current timezone setting
        cursor.execute("SHOW timezone;")
        tz_result = cursor.fetchone()
        current_tz = tz_result[0] if tz_result else "Unknown"
        log.info(f"Current database timezone: {current_tz}")
        
        # Check sample timestamp with timezone
        cursor.execute("SELECT CURRENT_TIMESTAMP AT TIME ZONE '+09:00' as dili_time;")
        time_result = cursor.fetchone()
        dili_time = time_result[0] if time_result else "Unknown"
        log.info(f"Current Dili time (+09:00): {dili_time}")
        
        return True
        
    except Exception as e:
        log.error(f"Error verifying timezone: {str(e)}")
        return False
        
    finally:
        cursor.close()
        conn.close()

def insert_sample_data():
    """Insert sample data for the 14 existing ATMs"""
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        log.info("Inserting sample data for 14 ATMs...")
        
        # Sample data based on your existing ATMs
        sample_data = [
            ('83', 'Nautilus Hyosun Dili Central 1', '45201', 'P24', '00601', 'Nautilus Hyosun', 'Monimax 5600', 'RUA NICOLAU DOS REIS LOBATO', 'Public Area', 'Dili', 'TL-DL', 'Timor-Leste', -8.5569, 125.5603, 'TL-DL', True, 'system_import'),
            ('2603', 'BRI Central Office ATM', 'BRI2603', 'P24', 'BRI2603', 'NCR', 'SelfServ 22e', 'BRI - CENTRAL OFFICE COLMERA 02', 'Financial Institution Office', 'Dili', 'TL-DL', 'Timor-Leste', -8.5594, 125.5647, 'TL-DL', True, 'system_import'),
            ('87', 'Pertamina Station ATM', '45205', 'P24', '00605', 'Diebold', '4900', 'PERTAMINA INT. BEBORRA RUA. DOS MARTIRES DA PATRIA', 'Gas Station', 'Dili', 'TL-DL', 'Timor-Leste', -8.5712, 125.5389, 'TL-DL', True, 'system_import'),
            ('88', 'Airport ATM', '45203', 'P24', '00603', 'Nautilus Hyosun', 'Monimax 5600', 'AERO PORTO NICOLAU LOBATU,DILI', 'Airport', 'Dili', 'TL-DL', 'Timor-Leste', -8.5464, 125.5289, 'TL-DL', True, 'system_import'),
            ('2604', 'BRI Audian Branch', 'BRI2604', 'P24', 'BRI2604', 'Wincor Nixdorf', 'ProCash 2100xe', 'BRI - SUB-BRANCH AUDIAN', 'Financial Institution Office', 'Dili', 'TL-DL', 'Timor-Leste', -8.5534, 125.5712, 'TL-DL', True, 'system_import'),
            ('85', 'Balide ATM', '45207', 'P24', '00607', 'Nautilus Hyosun', 'Monimax 5600', 'ESTRADA DE BALIDE, BALIDE', 'Public Area', 'Dili', 'TL-DL', 'Timor-Leste', -8.5345, 125.5890, 'TL-DL', True, 'system_import'),
            ('147', 'Centro Supermercado ATM', '45214', 'P24', '00614', 'NCR', 'SelfServ 22e', 'CENTRO SUPERMERCADO PANTAI KELAPA', 'Supermarket', 'Dili', 'TL-DL', 'Timor-Leste', -8.5623, 125.5456, 'TL-DL', True, 'system_import'),
            ('49', 'Americo Tomas Avenue ATM', '45209', 'P24', '00609', 'Nautilus Hyosun', 'Monimax 5600', 'AV. ALM. AMERICO TOMAS', 'Public Area', 'Dili', 'TL-DL', 'Timor-Leste', -8.5578, 125.5634, 'TL-DL', True, 'system_import'),
            ('86', 'Fatu Ahi ATM', '45204', 'P24', '00604', 'Diebold', '4900', 'FATU AHI', 'Public Area', 'Dili', 'TL-DL', 'Timor-Leste', -8.5612, 125.5545, 'TL-DL', True, 'system_import'),
            ('2605', 'BRI Hudilaran Branch', 'BRI2605', 'P24', 'BRI2605', 'Wincor Nixdorf', 'ProCash 2100xe', 'BRI - SUB BRANCH HUDILARAN', 'Financial Institution Office', 'Dili', 'TL-DL', 'Timor-Leste', -8.5467, 125.5789, 'TL-DL', True, 'system_import'),
            ('169', 'BRI Fatuhada Branch', '45211', 'P24', '00611', 'NCR', 'SelfServ 22e', 'BRI SUB-BRANCH FATUHADA', 'Financial Institution Office', 'Dili', 'TL-DL', 'Timor-Leste', -8.5601, 125.5723, 'TL-DL', True, 'system_import'),
            ('90', 'Novo Turismo ATM', '45200', 'P24', '00600', 'Nautilus Hyosun', 'Monimax 5600', 'NOVO TURISMO, BIDAU LECIDERE', 'Hotel', 'Dili', 'TL-DL', 'Timor-Leste', -8.5534, 125.5445, 'TL-DL', True, 'system_import'),
            ('89', 'UNTL University ATM', '45202', 'P24', '00602', 'NCR', 'SelfServ 22e', 'UNTL, RUA JACINTO CANDIDO', 'University Area', 'Dili', 'TL-DL', 'Timor-Leste', -8.5456, 125.5667, 'TL-DL', True, 'system_import'),
            ('93', 'Timor Plaza ATM', '45209', 'P24', '00609', 'Diebold', '4900', 'TIMOR PLAZA COMORO', 'Shopping Center', 'Dili', 'TL-DL', 'Timor-Leste', -8.5589, 125.5612, 'TL-DL', True, 'system_import')
        ]
        
        insert_sql = """
        INSERT INTO atm_masters (
            terminal_id, terminal_name, external_id, network_id, business_id, 
            brand, model, location, location_type, city, region, country, 
            latitude, longitude, geo_location, is_active, created_by
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (terminal_id) DO UPDATE SET
            terminal_name = EXCLUDED.terminal_name,
            external_id = EXCLUDED.external_id,
            network_id = EXCLUDED.network_id,
            business_id = EXCLUDED.business_id,
            brand = EXCLUDED.brand,
            model = EXCLUDED.model,
            location = EXCLUDED.location,
            location_type = EXCLUDED.location_type,
            city = EXCLUDED.city,
            region = EXCLUDED.region,
            country = EXCLUDED.country,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            geo_location = EXCLUDED.geo_location,
            updated_at = CURRENT_TIMESTAMP AT TIME ZONE '+09:00',
            updated_by = 'system_update';
        """
        
        cursor.executemany(insert_sql, sample_data)
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM atm_masters;")
        count_result = cursor.fetchone()
        total_count = count_result[0] if count_result else 0
        
        conn.commit()
        log.info(f"✅ Sample data inserted successfully. Total ATMs: {total_count}")
        
        # Display inserted data
        cursor.execute("""
            SELECT terminal_id, terminal_name, brand, model, location, created_at 
            FROM atm_masters 
            ORDER BY terminal_id;
        """)
        
        results = cursor.fetchall()
        
        print("\n" + "="*100)
        print("INSERTED ATM DATA")
        print("="*100)
        print(f"{'Terminal ID':<12} {'Name':<25} {'Brand':<15} {'Model':<15} {'Location':<30}")
        print("-"*100)
        
        for row in results:
            terminal_id, name, brand, model, location, created_at = row
            location_short = location[:28] + "..." if len(location) > 30 else location
            print(f"{terminal_id:<12} {name[:23]:<25} {brand:<15} {model:<15} {location_short:<30}")
        
        print("="*100)
        
        return True
        
    except Exception as e:
        conn.rollback()
        log.error(f"Error inserting sample data: {str(e)}")
        return False
        
    finally:
        cursor.close()
        conn.close()

def main():
    """Main execution function"""
    
    print("="*80)
    print("ATM MASTERS TABLE CREATION SCRIPT")
    print("="*80)
    print("This script will:")
    print("1. Connect to your PostgreSQL database using .env configuration")
    print("2. Create the atm_masters table with Dili timezone (+0900)")
    print("3. Create necessary indexes and triggers")
    print("4. Insert sample data for your 14 existing ATMs")
    print("="*80)
    
    # Check database connection
    log.info("Step 1: Testing database connection...")
    conn = get_db_connection()
    if not conn:
        log.error("❌ Failed to connect to database. Please check your .env configuration.")
        return False
    conn.close()
    log.info("✅ Database connection successful")
    
    # Verify timezone
    log.info("Step 2: Verifying timezone configuration...")
    if not verify_timezone_consistency():
        log.error("❌ Timezone verification failed")
        return False
    log.info("✅ Timezone configuration verified")
    
    # Create table
    log.info("Step 3: Creating atm_masters table...")
    if not create_atm_masters_table():
        log.error("❌ Table creation failed")
        return False
    log.info("✅ Table creation successful")
    
    # Insert sample data
    log.info("Step 4: Inserting sample data...")
    if not insert_sample_data():
        log.error("❌ Sample data insertion failed")
        return False
    log.info("✅ Sample data insertion successful")
    
    print("\n" + "="*80)
    print("🎉 ATM MASTERS TABLE SETUP COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("Next steps:")
    print("1. Verify the data using: SELECT * FROM atm_masters ORDER BY terminal_id;")
    print("2. Test timezone consistency with existing tables")
    print("3. Consider adding foreign key relationships to existing tables")
    print("4. Update your applications to use the new atm_masters table")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
