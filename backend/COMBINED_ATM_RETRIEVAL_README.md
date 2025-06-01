# Combined ATM Data Retrieval Script

## Overview

The `combined_atm_retrieval_script.py` provides a comprehensive solution for retrieving both regional ATM counts and detailed terminal fault information. This script combines functionality from:

- `regional_atm_retrieval_script.py` - Regional ATM data with percentage-to-count conversion
- `atm_crawler_complete.py` - Terminal-specific fault details via `fetch_terminal_details` function

## Features

- **Enhanced Data Collection**:
  1. Regional ATM counts (from fifth_graphic dashboard)
  2. Enhanced terminal fault information with unique_request_id and retrievedDate fields
  3. Streamlined workflow focusing on regional data and terminal details

- **Complete Authentication Flow**: Handles login with automatic token management and refresh
- **Comprehensive JSON Output**: Structured data with regional counts and enhanced terminal details
- **Demo Mode**: Testing without network connectivity using realistic sample data
- **Database Integration**: Optional saving to regional_atm_counts table
- **Error Handling**: Retry logic, token refresh, and graceful error recovery
- **Progress Tracking**: Visual progress bars for terminal processing

## Installation & Dependencies

```bash
pip install requests urllib3 pytz tqdm
```

## Usage

### Basic Usage

```bash
# Demo mode (no network required) - display results only
python combined_atm_retrieval_script.py --demo

# Live mode (requires network) - display results only
python combined_atm_retrieval_script.py

# Demo mode with JSON output
python combined_atm_retrieval_script.py --demo --save-json

# Live mode with database save
python combined_atm_retrieval_script.py --save-to-db

# Live mode with both JSON and database save
python combined_atm_retrieval_script.py --save-json --save-to-db

# Custom total ATM count for percentage calculations
python combined_atm_retrieval_script.py --demo --total-atms 20 --save-json

# Quiet mode (errors and warnings only)
python combined_atm_retrieval_script.py --demo --quiet
```

### Command Line Arguments

- `--demo`: Run in demo mode (no actual network requests)
- `--save-to-db`: Save regional data to database (requires db_connector module)
- `--save-json`: Save all retrieved data to JSON file
- `--total-atms NUMBER`: Total number of ATMs for percentage conversion (default: 14)
- `--quiet`: Reduce logging output (errors and warnings only)

## Script Workflow

### Phase 1: Regional ATM Data
```
Authentication → Fetch fifth_graphic data → Process percentages to counts
```

### Phase 2: Terminal Collection for Details
```
For each status (WOUNDED, HARD, CASH, etc.) → Collect terminal list for processing
```

### Phase 3: Enhanced Terminal Details
```
For each terminal → Fetch detailed fault information → Add unique_request_id and retrievedDate
```

## JSON Output Structure

The script generates a comprehensive JSON file in the `saved_data/` directory with the following structure:

```json
{
  "retrieval_timestamp": "2025-05-30T15:32:24.178249+09:00",
  "demo_mode": true,
  "regional_data": [
    {
      "unique_request_id": "...",
      "region_code": "TL-DL",
      "count_available": 11,
      "count_warning": 1,
      "count_zombie": 0,
      "count_wounded": 2,
      "count_out_of_service": 0,
      "date_creation": "2025-05-30T15:32:24.178376+09:00",
      "total_atms_in_region": 14,
      "percentage_available": 0.78571427,
      "percentage_warning": 0.07142857,
      "percentage_zombie": 0.0,
      "percentage_wounded": 0.14285714,
      "percentage_out_of_service": 0.0
    }
  ],
  "terminal_details_data": [
    {
      "unique_request_id": "55f9f0f1-5a4f-4d7b-b7b2-b0545abd4155",
      "terminalId": "80",
      "location": "Sample location for 80",
      "issueStateName": "HARD",
      "serialNumber": "YB762080",
      "retrievedDate": "2025-05-30 17:19:41",
      "year": "2025",
      "month": "MAY",
      "day": "30",
      "externalFaultId": "PRR211980",
      "agentErrorDescription": "MEDIA JAMMED",
      "creationDate": "30:05:2025 17:19:41",
      "fetched_status": "WOUNDED"
    }
  ],
  "summary": {
    "total_regions": 2,
    "total_terminal_details": 21,
    "terminal_details_with_unique_ids": 21,
    "status_counts": {
      "AVAILABLE": 3,
      "WARNING": 3,
      "WOUNDED": 9,
      "ZOMBIE": 3,
      "OUT_OF_SERVICE": 3
    },
    "collection_note": "Terminal status data collection disabled - only regional and terminal details collected"
  }
}
```

### New Enhanced Fields

The enhanced script adds two important fields to terminal_details_data:

- **`unique_request_id`**: A UUID generated for each ATM status record to ensure unique identification
- **`retrievedDate`**: The current retrieval timestamp formatted as 'YYYY-MM-DD HH:MM:SS' for tracking when data was collected

These fields support better data tracking and database operations by providing unique identifiers and precise timestamps for each terminal record.

## Example Output

When you run the script, you'll see detailed progress and results:

```
================================================================================
COMBINED ATM DATA RETRIEVAL RESULTS
================================================================================
Retrieval Time: 2025-05-30T15:32:24.178249+09:00
Demo Mode: True
Total Regions: 2
Total Terminals: 21
Terminal Details Retrieved: 18

--- REGIONAL ATM COUNTS ---
Region     Available  Warning  Zombie   Wounded  Out/Svc  Total 
----------------------------------------------------------------------
TL-DL       11 ( 78.6%)   1        0        2        0       14
TL-AN       12 ( 85.7%)   0        1        0        1       14

--- TERMINAL STATUS SUMMARY ---
WOUNDED: 3 terminals (14.3%)
HARD: 3 terminals (14.3%)
CASH: 3 terminals (14.3%)
UNAVAILABLE: 3 terminals (14.3%)
AVAILABLE: 3 terminals (14.3%)
WARNING: 3 terminals (14.3%)
ZOMBIE: 3 terminals (14.3%)
Total: 21 terminals

--- TERMINAL DETAILS SUMMARY ---
Fault Summary:
  DEVICE ERROR: 9
  MEDIA JAMMED: 6
  CASH LOW: 3
================================================================================
```

## Integration Examples

### Programmatic Usage

```python
from combined_atm_retrieval_script import CombinedATMRetriever

# Create retriever instance
retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)

# Execute complete flow
success, all_data = retriever.retrieve_and_process_all_data(save_to_db=True)

if success:
    print(f"Successfully processed:")
    print(f"- {len(all_data['regional_data'])} regions")
    print(f"- {len(all_data['terminal_details_data'])} terminal details")
    
    # Save to custom JSON file
    retriever.save_to_json(all_data, "custom_filename.json")
```

### Processing Retrieved Data

```python
# Extract specific information
for region in all_data['regional_data']:
    print(f"Region {region['region_code']}: "
          f"{region['count_available']}/{region['total_atms_in_region']} available")

# Find terminals with specific faults
for detail in all_data['terminal_details_data']:
    if 'MEDIA JAMMED' in detail.get('agentErrorDescription', ''):
        print(f"Terminal {detail['terminalId']} has media jam at {detail['location']}")
```

## Key Components

### CombinedATMRetriever Class

The main class that handles all data retrieval operations:

- `__init__(demo_mode, total_atms)`: Initialize retriever
- `authenticate()`: Handle login and token management
- `fetch_regional_data()`: Get fifth_graphic data
- `get_terminals_by_status(param_value)`: Get terminals by status
- `fetch_terminal_details(terminal_id, issue_state_code)`: Get detailed fault info
- `process_regional_data(raw_data)`: Convert percentages to counts
- `retrieve_and_process_all_data(save_to_db)`: Main orchestration method
- `save_to_json(data, filename)`: Save data to JSON file

### Integrated fetch_terminal_details Function

This function was extracted from `atm_crawler_complete.py` and provides:

- Detailed terminal fault information
- Error handling with retry logic
- Token refresh on authentication failures
- Support for all issue state codes (HARD, CASH, WOUNDED, etc.)

## Error Handling

The script includes comprehensive error handling:

- **Network Issues**: Automatic retry with exponential backoff
- **Authentication**: Token refresh on 401 errors
- **Data Validation**: Structure validation for all API responses
- **Graceful Fallback**: Demo mode when network is unavailable
- **Detailed Logging**: Complete error traces and debugging information

## Files Generated

1. **Log File**: `combined_atm_retrieval.log` - Detailed execution log
2. **JSON Output**: `saved_data/combined_atm_data_YYYYMMDD_HHMMSS.json` - Complete data export
3. **Database Records**: Optional insertion into `regional_atm_counts` table

## Testing

```bash
# Quick demo test
python combined_atm_retrieval_script.py --demo --save-json

# Test with custom parameters
python combined_atm_retrieval_script.py --demo --total-atms 20 --save-json

# Test database integration
python combined_atm_retrieval_script.py --demo --save-to-db

# Quiet mode test
python combined_atm_retrieval_script.py --demo --quiet
```

## Troubleshooting

### Common Issues

1. **Network Connectivity**: Use `--demo` flag for testing
2. **Database Connection**: Ensure `db_connector.py` is available
3. **Authentication**: Check credentials in LOGIN_PAYLOAD
4. **Permissions**: Ensure write access to `saved_data/` directory

### Debug Mode

Add debug logging by modifying the logging level in the script:

```python
logging.getLogger().setLevel(logging.DEBUG)
```

## Production Deployment

For production use:

1. Remove demo mode
2. Configure proper credentials
3. Set up log rotation
4. Monitor database performance
5. Schedule regular execution via cron

## Data Retention

The script generates timestamped files to avoid conflicts:
- JSON files: `combined_atm_data_YYYYMMDD_HHMMSS.json`
- Log rotation recommended for production
- Database records include unique request IDs for tracking
