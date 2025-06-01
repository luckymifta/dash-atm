# ATM Fault Processing Enhancement

## Overview
Enhanced the ATM monitoring system to extract comprehensive fault information from the API response, including additional fields for better fault analysis and reporting.

## Enhanced Fault Data Structure

The fault processing now extracts the following fields from each fault record:

### Core Fault Information
- **`creation_date`**: Unix timestamp converted to Dili local time (UTC+9) in ISO format
- **`creation_date_timestamp`**: Datetime object for database operations
- **`external_fault_id`**: External fault identifier/error code
- **`agent_error_description`**: Human-readable fault description

### NEW Enhanced Fields
- **`fault_type_code`**: The fault type classification (e.g., "HARDWARE", "SOFTWARE", "NETWORK", "CASH", "RECEIPT", "CARD_READER")
- **`component_type_code`**: Component that experienced the fault (e.g., "DISPENSER", "READER", "PRINTER", "NETWORK_MODULE", "DEPOSIT_MODULE", "SENSOR")
- **`issue_state_name`**: The issue state/severity (e.g., "ERROR", "WARNING", "CRITICAL", "MAINTENANCE")
- **`year`**: Year extracted from creation date (4-digit string)
- **`month`**: Month extracted from creation date (2-digit zero-padded string)
- **`date`**: Day extracted from creation date (2-digit zero-padded string)

### Example Fault Record
```json
{
  "creation_date": "2025-05-29T09:49:51.390000+09:00",
  "creation_date_timestamp": "2025-05-29 09:49:51.390000+09:00",
  "fault_type_code": "CASH",
  "component_type_code": "READER", 
  "issue_state_name": "WARNING",
  "year": "2025",
  "month": "05",
  "date": "29",
  "external_fault_id": "ERR_8064",
  "agent_error_description": "Power supply voltage fluctuation",
  "raw_fault_data": {
    "creationDate": 1748479791390,
    "faultTypeCode": "CASH",
    "componenTypeCode": "READER",
    "issueStateName": "WARNING",
    "year": "2025",
    "month": "05", 
    "date": "29",
    "externalFaultId": "ERR_8064",
    "agentErrorDescription": "Power supply voltage fluctuation"
  }
}
```

## API Field Mapping

| Output Field | API Field | Description |
|--------------|-----------|-------------|
| `creation_date` | `creationDate` | Unix timestamp → UTC+9 ISO format |
| `fault_type_code` | `faultTypeCode` | Fault classification |
| `component_type_code` | `componenTypeCode` | Component identifier |
| `issue_state_name` | `issueStateName` | Issue severity/state |
| `year` | `year` OR extracted from `creationDate` | 4-digit year |
| `month` | `month` OR extracted from `creationDate` | 2-digit month |
| `date` | `date` OR extracted from `creationDate` | 2-digit day |
| `external_fault_id` | `externalFaultId` | Error code/identifier |
| `agent_error_description` | `agentErrorDescription` | Human-readable description |

## Implementation Details

### Date/Time Processing
- Unix timestamps are converted from milliseconds to seconds
- All dates are converted to Dili timezone (UTC+9)
- Date components (year, month, date) are extracted and zero-padded
- Fallback to raw API fields if timestamp parsing fails

### Error Handling
- Graceful handling of missing or invalid fault data
- Logging of parsing errors with context
- Preservation of raw fault data for debugging

### Testing
- Enhanced demo mode generates realistic fault data
- All status types (AVAILABLE, WARNING, WOUNDED, ZOMBIE, OUT_OF_SERVICE) tested
- Comprehensive response and processed data files validated

## Files Modified
- `atm_details_retrieval_script.py`: Enhanced fault processing logic
- Demo data generation updated with new fault fields

## Status
✅ **COMPLETED** - All enhanced fault fields are extracted and processed correctly.

## Usage
The enhanced fault processing works automatically with both demo and production modes:

```bash
# Test with demo data
python3 atm_details_retrieval_script.py --demo --save-json

# Production usage 
python3 atm_details_retrieval_script.py --save-json
```

Both comprehensive response and processed ATM data files now include the enhanced fault information.
