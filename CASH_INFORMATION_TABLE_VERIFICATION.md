# Terminal Cash Information Table Verification

## Overview

This document summarizes the verification of the `terminal_cash_information` table, which was integrated as part of the cash information retrieval functionality in the combined ATM monitoring script.

## Verification Script

A dedicated verification script has been created to check the table structure, indexes, and sample data:

```
/backend/verify_cash_information_table.py
```

This script performs the following checks:

1. **Table existence check**: Confirms if the `terminal_cash_information` table exists in the database
2. **Column verification**: Validates that all required columns are present with correct data types
3. **Index verification**: Checks for required indexes on the table
4. **Sample data retrieval**: Fetches sample records to verify data integrity
5. **Statistics gathering**: Collects statistics about the data stored in the table

## How to Run the Verification

### Using the Helper Script

A helper script has been provided to simplify running the verification with the correct environment variables:

```bash
cd /path/to/dash-atm/backend
./verify_cash_table.sh --verbose
```

You can customize the database connection parameters:

```bash
./verify_cash_table.sh --host your_db_host --port 5432 --dbname atm_monitor --user postgres --password your_password --verbose
```

### Manual Execution

Alternatively, you can run the verification script directly after setting up the database environment variables:

```bash
# Set database connection environment variables
export DB_HOST="your_database_host"  # Default: localhost
export DB_PORT="your_database_port"  # Default: 5432
export DB_NAME="your_database_name"  # Default: atm_monitor 
export DB_USER="your_database_user"  # Default: postgres
export DB_PASSWORD="your_database_password"

# Run the verification script
cd /path/to/dash-atm/backend
python verify_cash_information_table.py --verbose
```

The `--verbose` flag provides more detailed output, including sample data from the table.

## Expected Table Structure

The verification script checks for the following expected structure:

### Required Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| id | integer | Primary key |
| unique_request_id | uuid | Unique identifier for the request |
| terminal_id | character varying | Terminal identifier |
| business_code | character varying | Business code associated with the terminal |
| technical_code | character varying | Technical code for the terminal |
| external_id | character varying | External identifier |
| retrieval_timestamp | timestamp with time zone | When the data was retrieved |
| event_date | timestamp with time zone | When the cash event occurred |
| total_cash_amount | numeric | Total cash amount in the terminal |
| total_currency | character varying | Currency of the cash amount |
| cassettes_data | jsonb | JSON data about individual cassettes |
| raw_cash_data | jsonb | Original raw data from the source |
| cassette_count | integer | Number of cassettes |
| has_low_cash_warning | boolean | Flag indicating low cash warning |
| has_cash_errors | boolean | Flag indicating cash errors |
| is_null_record | boolean | Flag for null/invalid records |
| null_reason | text | Reason for null record if applicable |
| created_at | timestamp with time zone | Record creation timestamp |

### Required Indexes

The script verifies that the following indexes exist to ensure optimal query performance:

1. Primary key on `id` column
2. Index on `terminal_id` column
3. Index on `retrieval_timestamp` column

## Verification Results

When the verification script is run successfully, it will display detailed information about the table structure and data statistics. 

If the table is properly configured according to the integration requirements, you should see "✅ Table structure verification passed!" in the output.

## Troubleshooting

If the verification fails, check the following:

1. **Database Connection Issues**:
   - Verify database environment variables are set correctly
   - Check if the database server is running
   - Ensure the user has appropriate permissions

2. **Missing Table**:
   - Run the combined ATM retrieval script with cash information retrieval enabled
   - Check for error messages in the application logs

3. **Structure Issues**:
   - If columns are missing or have incorrect types, review the table creation logic in the combined script
   - If indexes are missing, they can be added manually or by re-running the table creation code

## Next Steps

After successful verification:
1. Monitor the table for proper data population
2. Set up regular backups of the cash information data
3. Consider implementing data retention policies for historical cash data
