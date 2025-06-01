#!/usr/bin/env python3
# db_connector.py - Module to store crawler data in PostgreSQL

import psycopg2
import logging
import sys
import os
from datetime import datetime
import json
import uuid
import pytz

# Configure logging
log = logging.getLogger("DBConnector")

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    log.info("Environment variables loaded from .env file")
except ImportError:
    log.warning("python-dotenv not installed. Using environment variables directly.")

# Database configuration from environment variables
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "database": os.environ.get("DB_NAME", "atm_monitor"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "")
}

def get_db_connection():
    """Create a database connection"""
    # Check for required environment variables
    missing_vars = []
    for key, value in DB_CONFIG.items():
        if key == "password" and not value:
            missing_vars.append("DB_PASS")
        elif not value:
            env_key = f"DB_{key.upper()}"
            missing_vars.append(env_key)
    
    if missing_vars:
        log.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        log.warning("Please set these variables or create a .env file")
    
    try:
        # Log connection attempt (without password)
        log.info(f"Connecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']} as {DB_CONFIG['user']}")
        
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        return conn
    except psycopg2.OperationalError as e:
        log.error(f"Database connection error: {str(e)}")
        log.error(f"Please verify your database credentials and connection settings")
        return None
    except Exception as e:
        log.error(f"Unexpected database error: {str(e)}")
        return None

def check_db_tables():
    """Check if required tables exist and create them if not"""
    conn = get_db_connection()
    if not conn:
        log.error("Failed to connect to database - cannot check tables")
        return False
    
    cursor = conn.cursor()
    try:
        # Check if terminals table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'terminals')")
        terminals_result = cursor.fetchone()
        terminals_exists = terminals_result[0] if terminals_result else False
        
        # Check if terminal_faults table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'terminal_faults')")
        faults_result = cursor.fetchone()
        faults_exists = faults_result[0] if faults_result else False
        
        # Create tables if they don't exist
        if not terminals_exists:
            log.info("Creating terminals table...")
            cursor.execute("""
                CREATE TABLE terminals (
                    id UUID PRIMARY KEY,
                    terminal_id VARCHAR(50) UNIQUE NOT NULL,
                    network_id VARCHAR(50),
                    external_id VARCHAR(50),
                    brand VARCHAR(100),
                    model VARCHAR(100),
                    supplier VARCHAR(100),
                    location VARCHAR(255),
                    geo_location VARCHAR(50),
                    terminal_type VARCHAR(50),
                    status VARCHAR(50),
                    issue_state_code VARCHAR(50),
                    bank VARCHAR(50),
                    serial_number VARCHAR(100),
                    technical_code VARCHAR(100),
                    business_id VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_connected BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_terminal_status ON terminals(status)")
            cursor.execute("CREATE INDEX idx_terminal_location ON terminals(location)")
            cursor.execute("CREATE INDEX idx_terminal_updated_at ON terminals(updated_at)")
            
        if not faults_exists:
            log.info("Creating terminal_faults table...")
            cursor.execute("""
                CREATE TABLE terminal_faults (
                    id UUID PRIMARY KEY,
                    terminal_id VARCHAR(50) REFERENCES terminals(terminal_id) ON DELETE CASCADE,
                    fault_id VARCHAR(100),
                    external_fault_id VARCHAR(100) UNIQUE,
                    fault_type_code VARCHAR(50),
                    component_type_code VARCHAR(50),
                    issue_state_name VARCHAR(50),
                    year VARCHAR(4),
                    month VARCHAR(3),
                    day VARCHAR(2),
                    agent_error_description TEXT,
                    fault_date TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_fault_terminal_id ON terminal_faults(terminal_id)")
            cursor.execute("CREATE INDEX idx_fault_date ON terminal_faults(fault_date)")
            cursor.execute("CREATE INDEX idx_fault_type ON terminal_faults(fault_type_code)")
            cursor.execute("CREATE INDEX idx_fault_error ON terminal_faults(agent_error_description)")
        
        # Create stats view if it doesn't exist
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.views WHERE table_name = 'terminal_stats')")
        stats_result = cursor.fetchone()
        stats_exists = stats_result[0] if stats_result else False
        
        if not stats_exists:
            log.info("Creating terminal_stats view...")
            cursor.execute("""
                CREATE VIEW terminal_stats AS
                SELECT 
                    status,
                    COUNT(*) as count
                FROM 
                    terminals
                GROUP BY 
                    status
            """)
        
        conn.commit()
        log.info("Database tables check completed")
        return True
        
    except Exception as e:
        conn.rollback()
        log.error(f"Database error while checking tables: {str(e)}")
        return False
        
    finally:
        cursor.close()
        conn.close()

def save_to_database(all_terminals, terminal_details):
    """Save crawler data to PostgreSQL (INSERT only, with unique requestId for history, and Dili local time for created_at)"""
    check_db_tables()
    conn = get_db_connection()
    if not conn:
        log.error("Failed to connect to database - cannot save data")
        return False
    cursor = conn.cursor()
    try:
        dili_tz = pytz.timezone('Asia/Dili')
        now_dili = datetime.now(dili_tz)
        # Process terminals (INSERT only, with requestId)
        for terminal in all_terminals:
            terminal_id = terminal.get('terminalId', '')
            if not terminal_id:
                continue
            request_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO terminals (
                    id, terminal_id, network_id, external_id, brand, model, supplier,
                    location, geo_location, terminal_type, status, issue_state_code,
                    bank, serial_number, technical_code, business_id, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    terminal_id,
                    terminal.get('networkId', ''),
                    terminal.get('externalId', ''),
                    terminal.get('brand', ''),
                    terminal.get('model', ''),
                    terminal.get('supplier', ''),
                    terminal.get('location', ''),
                    terminal.get('geoLocation', ''),
                    terminal.get('terminalType', 'ATM'),
                    terminal.get('fetched_status', ''),
                    terminal.get('issueStateCode', ''),
                    terminal.get('bank', 'BRI'),
                    terminal.get('serialNumber', ''),
                    terminal.get('technicalCode', ''),
                    terminal.get('businessId', ''),
                    now_dili,
                    now_dili
                )
            )
        # Process terminal faults (INSERT only, with requestId)
        for detail in terminal_details:
            if detail.get('externalFaultId'):
                terminal_id = detail.get('terminalId', '')
                external_fault_id = detail.get('externalFaultId', '')
                if not terminal_id or not external_fault_id:
                    continue
                request_id = str(uuid.uuid4())
                fault_date = None
                year = detail.get('year', '')
                month = detail.get('month', '')
                day = detail.get('day', '')
                if year and month and day:
                    try:
                        month_map = {
                            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                        }
                        month_num = month_map.get(month, 1)
                        fault_date = datetime(int(year), month_num, int(day), tzinfo=dili_tz)
                    except (ValueError, TypeError):
                        fault_date = None
                cursor.execute(
                    """
                    INSERT INTO terminal_faults (
                        id, terminal_id, fault_id, external_fault_id, fault_type_code,
                        component_type_code, issue_state_name, year, month, day,
                        agent_error_description, fault_date, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        request_id,
                        terminal_id,
                        detail.get('faultId', ''),
                        external_fault_id,
                        detail.get('faultTypeCode', ''),
                        detail.get('componentTypeCode', ''),
                        detail.get('issueStateName', ''),
                        year,
                        month,
                        day,
                        detail.get('agentErrorDescription', ''),
                        fault_date,
                        now_dili
                    )
                )
        conn.commit()
        log.info(f"Successfully saved {len(all_terminals)} terminals and {len(terminal_details)} fault records to database (INSERT only, with requestId, Dili time)")
        return True
    except Exception as e:
        conn.rollback()
        log.error(f"Database error while saving data: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_regional_atm_counts_table():
    """Check if regional_atm_counts table exists and create it if not"""
    conn = get_db_connection()
    if not conn:
        log.error("Failed to connect to database - cannot check regional_atm_counts table")
        return False
    
    cursor = conn.cursor()
    try:
        # Check if regional_atm_counts table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'regional_atm_counts')")
        table_result = cursor.fetchone()
        table_exists = table_result[0] if table_result else False
        
        if not table_exists:
            log.info("Creating regional_atm_counts table...")
            cursor.execute("""
                CREATE TABLE regional_atm_counts (
                    unique_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    region_code VARCHAR(10) NOT NULL,
                    count_available INTEGER DEFAULT 0,
                    count_warning INTEGER DEFAULT 0,
                    count_zombie INTEGER DEFAULT 0,
                    count_wounded INTEGER DEFAULT 0,
                    count_out_of_service INTEGER DEFAULT 0,
                    date_creation TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Additional useful fields
                    total_atms_in_region INTEGER,
                    percentage_available DECIMAL(10,8),
                    percentage_warning DECIMAL(10,8),
                    percentage_zombie DECIMAL(10,8),
                    percentage_wounded DECIMAL(10,8),
                    percentage_out_of_service DECIMAL(10,8),
                    
                    -- Constraints
                    CONSTRAINT chk_counts_positive CHECK (
                        count_available >= 0 AND 
                        count_warning >= 0 AND 
                        count_zombie >= 0 AND 
                        count_wounded >= 0 AND 
                        count_out_of_service >= 0
                    )
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_regional_atm_region ON regional_atm_counts(region_code)")
            cursor.execute("CREATE INDEX idx_regional_atm_date ON regional_atm_counts(date_creation)")
            cursor.execute("CREATE INDEX idx_regional_atm_region_date ON regional_atm_counts(region_code, date_creation)")
            
            log.info("regional_atm_counts table created successfully")
        
        conn.commit()
        log.info("Regional ATM counts table check completed")
        return True
        
    except Exception as e:
        conn.rollback()
        log.error(f"Database error while checking regional_atm_counts table: {str(e)}")
        return False
        
    finally:
        cursor.close()
        conn.close()


def save_fifth_graphic_to_database(fifth_graphic_data, total_atms=14):
    """
    Save fifth_graphic data to regional_atm_counts table
    
    Args:
        fifth_graphic_data: List containing fifth_graphic data from dashboard response
        total_atms: Total number of ATMs for percentage to count conversion (default: 14)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not fifth_graphic_data:
        log.warning("No fifth_graphic data provided")
        return False
    
    # Ensure table exists
    if not check_regional_atm_counts_table():
        log.error("Failed to ensure regional_atm_counts table exists")
        return False
    
    conn = get_db_connection()
    if not conn:
        log.error("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    try:
        dili_tz = pytz.timezone('Asia/Dili')
        now_dili = datetime.now(dili_tz)
        
        for region_data in fifth_graphic_data:
            region_code = region_data.get("hc-key", "UNKNOWN")
            state_count = region_data.get("state_count", {})
            
            if not state_count:
                log.warning(f"No state_count data found for region {region_code}")
                continue
            
            # Initialize counts
            counts = {
                'count_available': 0,
                'count_warning': 0,
                'count_zombie': 0,
                'count_wounded': 0,
                'count_out_of_service': 0
            }
            
            # Initialize percentages
            percentages = {
                'percentage_available': 0.0,
                'percentage_warning': 0.0,
                'percentage_zombie': 0.0,
                'percentage_wounded': 0.0,
                'percentage_out_of_service': 0.0
            }
            
            # Process each state in the region
            for state_type, percentage_str in state_count.items():
                try:
                    percentage_value = float(percentage_str)
                    count_value = round(percentage_value * total_atms)
                    
                    # Map state types to our database columns
                    if state_type.upper() == 'AVAILABLE':
                        counts['count_available'] = count_value
                        percentages['percentage_available'] = percentage_value
                    elif state_type.upper() == 'WARNING':
                        counts['count_warning'] = count_value
                        percentages['percentage_warning'] = percentage_value
                    elif state_type.upper() == 'ZOMBIE':
                        counts['count_zombie'] = count_value
                        percentages['percentage_zombie'] = percentage_value
                    elif state_type.upper() == 'WOUNDED':
                        counts['count_wounded'] = count_value
                        percentages['percentage_wounded'] = percentage_value
                    elif state_type.upper() == 'OUT_OF_SERVICE':
                        counts['count_out_of_service'] = count_value
                        percentages['percentage_out_of_service'] = percentage_value
                    else:
                        log.warning(f"Unknown state type: {state_type} for region {region_code}")
                        
                except (ValueError, TypeError) as e:
                    log.error(f"Error processing state {state_type} for region {region_code}: {e}")
                    continue
            
            # Insert the record
            cursor.execute("""
                INSERT INTO regional_atm_counts (
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    date_creation,
                    total_atms_in_region,
                    percentage_available,
                    percentage_warning,
                    percentage_zombie,
                    percentage_wounded,
                    percentage_out_of_service
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                region_code,
                counts['count_available'],
                counts['count_warning'],
                counts['count_zombie'],
                counts['count_wounded'],
                counts['count_out_of_service'],
                now_dili,
                total_atms,
                percentages['percentage_available'],
                percentages['percentage_warning'],
                percentages['percentage_zombie'],
                percentages['percentage_wounded'],
                percentages['percentage_out_of_service']
            ))
            
            log.info(f"Saved regional data for {region_code}: Available={counts['count_available']}, "
                    f"Warning={counts['count_warning']}, Zombie={counts['count_zombie']}, "
                    f"Wounded={counts['count_wounded']}, Out_of_Service={counts['count_out_of_service']}")
        
        conn.commit()
        log.info(f"Successfully saved {len(fifth_graphic_data)} regional ATM count records to database")
        return True
        
    except Exception as e:
        conn.rollback()
        log.error(f"Database error while saving fifth_graphic data: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_latest_regional_data():
    """Get the latest regional ATM count data"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                region_code,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                total_atms_in_region,
                date_creation
            FROM regional_atm_counts
            WHERE date_creation = (SELECT MAX(date_creation) FROM regional_atm_counts)
            ORDER BY region_code
        """)
        
        results = cursor.fetchall()
        
        regional_data = []
        for row in results:
            regional_data.append({
                'region_code': row[0],
                'count_available': row[1],
                'count_warning': row[2],
                'count_zombie': row[3],
                'count_wounded': row[4],
                'count_out_of_service': row[5],
                'total_atms_in_region': row[6],
                'date_creation': row[7]
            })
        
        return regional_data
        
    except Exception as e:
        log.error(f"Error fetching latest regional data: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_regional_trends(region_code, hours_back=24):
    """Get regional ATM count trends for the specified time period"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                date_creation,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                total_atms_in_region
            FROM regional_atm_counts
            WHERE region_code = %s 
                AND date_creation >= NOW() - INTERVAL '%s hours'
            ORDER BY date_creation
        """, (region_code, hours_back))
        
        results = cursor.fetchall()
        
        trends = []
        for row in results:
            trends.append({
                'date_creation': row[0],
                'count_available': row[1],
                'count_warning': row[2],
                'count_zombie': row[3],
                'count_wounded': row[4],
                'count_out_of_service': row[5],
                'total_atms_in_region': row[6]
            })
        
        return trends
        
    except Exception as e:
        log.error(f"Error fetching regional trends for {region_code}: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()
