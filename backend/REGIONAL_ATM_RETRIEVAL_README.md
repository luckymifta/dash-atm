# Regional ATM Data Retrieval Script

## Overview

The `regional_atm_retrieval_script.py` provides a complete solution for retrieving ATM regional data from login until obtaining a response with the same structure as the `regional_atm_counts` database table.

## Features

- **Complete Authentication Flow**: Handles login with automatic token management and refresh
- **Regional Data Retrieval**: Fetches fifth_graphic data from the reports dashboard
- **Data Processing**: Converts percentage values to actual ATM counts matching table structure
- **Database Integration**: Optional saving to `regional_atm_counts` table with transaction rollback
- **Demo Mode**: Testing without network connectivity
- **Error Handling**: Comprehensive retry logic and graceful error recovery
- **Multiple Output Formats**: Display, JSON export, and database storage

## Table Structure Compatibility

The script outputs data that matches the `regional_atm_counts` table structure:

```sql
CREATE TABLE regional_atm_counts (
    unique_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_code VARCHAR(10) NOT NULL,
    count_available INTEGER DEFAULT 0,
    count_warning INTEGER DEFAULT 0,
    count_zombie INTEGER DEFAULT 0,
    count_wounded INTEGER DEFAULT 0,
    count_out_of_service INTEGER DEFAULT 0,
    date_creation TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_atms_in_region INTEGER,
    percentage_available DECIMAL(10,8),
    percentage_warning DECIMAL(10,8),
    percentage_zombie DECIMAL(10,8),
    percentage_wounded DECIMAL(10,8),
    percentage_out_of_service DECIMAL(10,8)
);
```

## Usage

### Basic Usage

```bash
# Demo mode (no network required) - display results only
python regional_atm_retrieval_script.py --demo

# Live mode (requires network) - display results only
python regional_atm_retrieval_script.py

# Demo mode with database save
python regional_atm_retrieval_script.py --demo --save-to-db

# Live mode with database save
python regional_atm_retrieval_script.py --save-to-db

# Save to JSON file
python regional_atm_retrieval_script.py --demo --save-json

# Custom total ATM count
python regional_atm_retrieval_script.py --demo --total-atms 20

# Quiet mode (errors and warnings only)
python regional_atm_retrieval_script.py --demo --quiet
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--demo` | Run in demo mode (no actual network requests) |
| `--save-to-db` | Save processed data to database |
| `--total-atms N` | Total number of ATMs for percentage conversion (default: 14) |
| `--save-json` | Save processed data to JSON file |
| `--quiet` | Reduce logging output (errors and warnings only) |

## Script Workflow

### 1. Authentication Phase
```python
# Check connectivity (if not demo mode)
if not demo_mode:
    check_connectivity()

# Authenticate with ATM system
authenticate()  # Returns user_token
```

### 2. Data Retrieval Phase
```python
# Fetch fifth_graphic data from reports dashboard
raw_data = fetch_regional_data()
# Returns: List of regions with percentage data
```

### 3. Data Processing Phase
```python
# Convert percentages to counts and format for database
processed_data = process_regional_data(raw_data)
# Returns: List of records matching regional_atm_counts structure
```

### 4. Storage Phase (Optional)
```python
# Save to database if requested
if save_to_db:
    save_to_database(processed_data)

# Save to JSON if requested
if save_json:
    save_to_json(processed_data)
```

## Example Output

### Console Display
```
================================================================================
REGIONAL ATM COUNTS DATA (matching regional_atm_counts table structure)
================================================================================
Region     Available  Warning  Zombie   Wounded  Out/Svc  Total  Timestamp           
----------------------------------------------------------------------------------------------------
TL-DL      11 (78.6%) 1        0        2        0        14     2025-01-28 10:30:15
TL-AN      12 (85.7%) 0        1        1        0        14     2025-01-28 10:30:15
----------------------------------------------------------------------------------------------------
Total regions processed: 2
```

### JSON Output Structure
```json
{
  "retrieval_timestamp": "2025-01-28T10:30:15.123456",
  "total_regions": 2,
  "regional_data": [
    {
      "unique_request_id": "550e8400-e29b-41d4-a716-446655440000",
      "region_code": "TL-DL",
      "count_available": 11,
      "count_warning": 1,
      "count_zombie": 0,
      "count_wounded": 2,
      "count_out_of_service": 0,
      "date_creation": "2025-01-28T10:30:15.123456+09:00",
      "total_atms_in_region": 14,
      "percentage_available": 0.78571427,
      "percentage_warning": 0.07142857,
      "percentage_zombie": 0.0,
      "percentage_wounded": 0.14285714,
      "percentage_out_of_service": 0.0
    }
  ]
}
```

## Integration Examples

### Programmatic Usage

```python
from regional_atm_retrieval_script import RegionalATMRetriever

# Create retriever instance
retriever = RegionalATMRetriever(demo_mode=True, total_atms=14)

# Execute complete flow
success, processed_data = retriever.retrieve_and_process(save_to_db=True)

if success and processed_data:
    print(f"Successfully processed {len(processed_data)} regions")
    for record in processed_data:
        print(f"Region {record['region_code']}: "
              f"{record['count_available']}/{record['total_atms_in_region']} available")
```

### Database Query After Retrieval

```python
import db_connector

# Get latest regional data from database
latest_data = db_connector.get_latest_regional_data()

for region in latest_data:
    availability_pct = (region['count_available'] / region['total_atms_in_region']) * 100
    print(f"Region {region['region_code']}: {availability_pct:.1f}% available")
```

## Testing

### Run Comprehensive Tests
```bash
python test_regional_atm_retrieval.py
```

### Quick Tests
```bash
python test_regional_atm_retrieval.py --quick
```

### Demo-Only Tests
```bash
python test_regional_atm_retrieval.py --demo-only
```

### Database-Only Tests
```bash
python test_regional_atm_retrieval.py --db-only
```

## Error Handling

The script includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Authentication Failures**: Token refresh and re-authentication
- **Data Validation**: Percentage and count validation with warnings
- **Database Errors**: Transaction rollback on failure
- **Malformed Data**: Graceful handling of missing or invalid fields

### Common Error Scenarios

1. **Network Connectivity Issues**
   ```
   ERROR: Connectivity test failed: Connection timeout
   Solution: Use --demo mode or check network connection
   ```

2. **Authentication Failures**
   ```
   ERROR: Authentication failed: Unable to extract user token
   Solution: Verify credentials in script configuration
   ```

3. **Database Connection Issues**
   ```
   WARNING: Database not available - skipping database save
   Solution: Check database configuration and connectivity
   ```

## Configuration

### Environment Variables (Optional)
```bash
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=atm_monitor
DB_USER=postgres
DB_PASS=your_password
```

### Script Configuration
The script includes these configurable parameters:

```python
# Authentication
LOGIN_URL = "https://172.31.1.46/sigit/user/login?language=EN"
LOGIN_PAYLOAD = {
    "user_name": "Lucky.Saputra",
    "password": "TimlesMon2024"
}

# Data retrieval
REPORTS_URL = "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=subStatus"

# ATM state mapping
SUPPORTED_STATES = {
    'AVAILABLE': 'count_available',
    'WARNING': 'count_warning',
    'ZOMBIE': 'count_zombie',
    'WOUNDED': 'count_wounded',
    'OUT_OF_SERVICE': 'count_out_of_service'
}
```

## Log Files

The script generates detailed logs in `regional_atm_retrieval.log`:

```
2025-01-28 10:30:15,123 INFO [authenticate]: Authentication successful - Token length: 123 characters
2025-01-28 10:30:16,456 INFO [fetch_regional_data]: Successfully retrieved regional data for 2 regions
2025-01-28 10:30:16,789 INFO [process_regional_data]: Successfully processed 2 regional records
2025-01-28 10:30:17,012 INFO [save_to_database]: Successfully saved 2 records to database
```

## Production Deployment

### Scheduled Execution
```bash
# Add to crontab for hourly execution
0 * * * * /usr/bin/python3 /path/to/regional_atm_retrieval_script.py --save-to-db --quiet

# Or run as a systemd service
sudo systemctl enable regional-atm-retrieval.service
sudo systemctl start regional-atm-retrieval.service
```

### Monitoring and Alerting
```bash
# Check for recent successful executions
tail -f regional_atm_retrieval.log | grep "COMPLETED SUCCESSFULLY"

# Monitor for errors
tail -f regional_atm_retrieval.log | grep -E "(ERROR|FAILED)"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   pip install requests urllib3 pytz
   
   # Ensure database connector is available
   python -c "import db_connector; print('DB available')"
   ```

2. **Permission Errors**
   ```bash
   # Ensure log file permissions
   chmod 644 regional_atm_retrieval.log
   
   # Ensure script execution permissions
   chmod +x regional_atm_retrieval_script.py
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connectivity
   python test_regional_atm_retrieval.py --db-only
   ```

### Support and Maintenance

For issues or questions:
1. Check the log file for detailed error messages
2. Run the test suite to identify specific problems
3. Use demo mode to isolate network-related issues
4. Verify database connectivity and table structure

---

**Note**: Since there's currently no network connection to the host, the script has been designed and tested in demo mode. Once network connectivity is restored, the script can be used in live mode for actual data retrieval.
