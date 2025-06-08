# ATM Data Retrieval System - Database Setup Guide

## Overview
This guide will help you set up the database tables for your ATM data retrieval system on your new VPS with the development_db.

## Database Configuration
- **Host**: 88.222.214.26
- **Port**: 5432
- **Database**: development_db
- **Username**: timlesdev
- **Password**: timlesdev

## Files Created

### 1. `db_connector_new.py`
- New database connector with updated credentials
- Supports both legacy and new table structures
- Includes comprehensive error handling and logging
- Creates all necessary tables and indexes

### 2. `setup_database.py`
- Complete database setup script
- Tests connection and creates all tables
- Provides detailed feedback and verification

### 3. `test_database_setup.py`
- Comprehensive test suite
- Verifies database connectivity, table creation, and script compatibility
- Includes demo run test

### 4. `requirements_database.txt`
- Python package requirements for database functionality
- Includes PostgreSQL drivers and all dependencies

## Setup Steps

### Step 1: Install Python Dependencies
```bash
# Navigate to your backend directory
cd /Users/luckymifta/Documents/2.\ AREA/dash-atm/backend/

# Install required packages
pip install -r requirements_database.txt
```

### Step 2: Set Up Database Tables
```bash
# Run the database setup script
python setup_database.py
```

Expected output:
```
✅ SUCCESS: Database connection established
✅ SUCCESS: All tables created successfully
✅ SUCCESS: Database setup verified
```

### Step 3: Test the Setup
```bash
# Run the comprehensive test suite
python test_database_setup.py
```

Expected output:
```
✅ Database Connection PASSED
✅ Table Creation PASSED
✅ Script Import PASSED
✅ Demo Run PASSED
🎉 ALL TESTS PASSED! Your database setup is ready.
```

### Step 4: Test with Your ATM Script
```bash
# Test in demo mode with new database tables
python combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables --save-json

# Test with live data (if your network allows)
python combined_atm_retrieval_script.py --save-to-db --use-new-tables --save-json

# Run in continuous mode
python combined_atm_retrieval_script.py --continuous --save-to-db --use-new-tables
```

## Database Tables Created

### 1. `regional_data` (Primary table for regional ATM data)
- `id`: Primary key
- `unique_request_id`: UUID for each request
- `region_code`: Region identifier (TL-DL, TL-AN, etc.)
- `retrieval_timestamp`: When data was retrieved
- `raw_regional_data`: JSONB storage of original API response
- `count_available`, `count_warning`, `count_zombie`, `count_wounded`, `count_out_of_service`: Processed counts
- `total_atms_in_region`: Total ATMs in region

### 2. `terminal_details` (Primary table for terminal-specific data)
- `id`: Primary key
- `unique_request_id`: UUID for each request
- `terminal_id`: Terminal identifier
- `location`: Terminal location
- `issue_state_name`: Current status
- `serial_number`: Terminal serial number
- `retrieved_date`: When data was retrieved
- `fetched_status`: Status at time of retrieval
- `raw_terminal_data`: JSONB storage of complete terminal data
- `fault_data`: JSONB storage of fault information
- `metadata`: JSONB storage of processing metadata

### 3. `regional_atm_counts` (Legacy compatibility table)
- Maintains compatibility with existing code
- Same structure as before but with new database

## Features

### JSONB Support
- All raw API responses are stored in JSONB format
- Enables flexible querying and future data analysis
- Preserves complete original data structure

### Optimized Indexes
- Performance indexes on frequently queried columns
- JSONB indexes for fast JSON querying
- Composite indexes for time-series queries

### UUID Tracking
- Every data retrieval has a unique request ID
- Enables tracking and auditing of data collection cycles

### Timezone Support
- All timestamps use PostgreSQL's TIMESTAMP WITH TIME ZONE
- Proper handling of Dili timezone (UTC+9)

## Troubleshooting

### Connection Issues
1. Verify database server is running
2. Check network connectivity: `ping 88.222.214.26`
3. Test PostgreSQL connection: `psql -h 88.222.214.26 -p 5432 -U timlesdev -d development_db`

### Package Installation Issues
```bash
# If psycopg2 installation fails, try:
pip install psycopg2-binary

# Or use conda:
conda install psycopg2
```

### Table Creation Issues
- Check PostgreSQL logs for detailed errors
- Ensure user has CREATE TABLE privileges
- Verify database exists

## Monitoring and Maintenance

### Check Table Status
```python
from db_connector_new import DatabaseConnector
connector = DatabaseConnector()
info = connector.get_table_info()
print(info)
```

### Query Examples
```sql
-- Check recent regional data
SELECT region_code, retrieval_timestamp, count_available, count_wounded 
FROM regional_data 
ORDER BY retrieval_timestamp DESC 
LIMIT 10;

-- Check terminal details with faults
SELECT terminal_id, location, issue_state_name, fault_data->>'agentErrorDescription' as error
FROM terminal_details 
WHERE fault_data->>'agentErrorDescription' != '' 
ORDER BY retrieved_date DESC;

-- Regional summary
SELECT region_code, 
       AVG(count_available) as avg_available,
       AVG(count_wounded) as avg_wounded
FROM regional_data 
WHERE retrieval_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY region_code;
```

## Success Indicators

✅ **Database Connection**: Can connect to PostgreSQL server
✅ **Tables Created**: All 3 tables exist with proper structure
✅ **Indexes**: Performance indexes are in place
✅ **Script Integration**: Your ATM script can use the new database
✅ **Data Insertion**: Demo mode successfully saves data
✅ **JSONB Storage**: Raw API responses are preserved

## Next Steps After Setup

1. **Production Deployment**: Move script to your VPS
2. **Monitoring Setup**: Set up logging and alerting
3. **Backup Strategy**: Configure regular database backups
4. **API Integration**: Connect to your dashboard frontend
5. **Scheduling**: Set up automated data collection
