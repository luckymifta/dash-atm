# MAINTENANCE to OUT_OF_SERVICE Status Mapping Implementation

## Summary
✅ **IMPLEMENTATION COMPLETE** - Successfully implemented MAINTENANCE → OUT_OF_SERVICE status mapping for consistent data representation in the ATM monitoring system.

## Changes Made

### 1. Configuration Update ✅
**File**: `backend/atm_config.py`
```python
# Status mapping for consistent data representation
STATUS_MAPPING = {
    'MAINTENANCE': 'OUT_OF_SERVICE'
}
```

### 2. Data Processor Update ✅
**File**: `backend/atm_data_processor.py`
```python
# Import status mapping
from atm_config import STATUS_MAPPING

# Apply mapping in process_terminal_details method
actual_status = item.get('issueStateName', '')
actual_status = STATUS_MAPPING.get(actual_status, actual_status)
```

### 3. Implementation Details

#### Before Mapping:
- Terminals with `MAINTENANCE` status were stored as `MAINTENANCE`
- Inconsistent categorization in regional data calculations
- Mixed status representation in database

#### After Mapping:
- All `MAINTENANCE` terminals are automatically mapped to `OUT_OF_SERVICE`
- Consistent data representation across the system
- Simplified status categorization for reporting

### 4. Database Impact ✅

#### Terminal Details Table:
- `issue_state_name` column: Now stores `OUT_OF_SERVICE` instead of `MAINTENANCE`
- `fetched_status` column: Also stores `OUT_OF_SERVICE` for consistency
- `fault_data` column: Maintains all fault information consistently

#### Regional Data Table:
- `count_out_of_service`: Now includes former MAINTENANCE terminals
- `percentage_out_of_service`: Updated to reflect accurate percentages
- Regional calculations work seamlessly with mapped data

### 5. Testing Results ✅

#### Before Implementation:
```
2620: issue_state=MAINTENANCE, fetched_status=MAINTENANCE, fault_data=True
```

#### After Implementation:
```
2620: issue_state=OUT_OF_SERVICE, fetched_status=OUT_OF_SERVICE, fault_data=True
```

### 6. Benefits

1. **Data Consistency**: All maintenance-related statuses are uniformly categorized
2. **Simplified Reporting**: Cleaner status groupings for dashboards and reports
3. **Improved Analytics**: More accurate out-of-service calculations
4. **Future-Proof**: Easy to add more status mappings as needed

### 7. Regional Data Calculation Impact

The existing regional data calculation logic already handles `OUT_OF_SERVICE` correctly:
```python
elif status in ["OUT_OF_SERVICE", "UNAVAILABLE"]:
    counts['count_out_of_service'] += 1
```

This means MAINTENANCE terminals are now properly counted in the out-of-service category.

### 8. Git Commits

#### Commit 1: Main Implementation
```
feat: Add MAINTENANCE to OUT_OF_SERVICE status mapping for consistency
- Added STATUS_MAPPING configuration in atm_config.py
- Updated atm_data_processor.py to apply status mapping
- Ensures consistent data representation
```

#### Commit 2: Documentation
```
docs: Add comprehensive documentation for ATM data fixes
- Added complete documentation for all implemented fixes
- Provides verification summaries and implementation details
```

## Testing Instructions for Windows

When testing on Windows, you should see:

1. **MAINTENANCE terminals automatically converted to OUT_OF_SERVICE**
2. **Consistent status representation in database**
3. **Proper fault data handling for all mapped statuses**

### Test Commands:
```bash
# Run the main script
python combined_atm_retrieval_script.py

# Check the database for mapping results
# All MAINTENANCE entries should now be OUT_OF_SERVICE
```

## Configuration Extension

The mapping system is extensible. To add more mappings:

```python
STATUS_MAPPING = {
    'MAINTENANCE': 'OUT_OF_SERVICE',
    'CUSTOM_STATUS': 'MAPPED_STATUS',
    # Add more mappings as needed
}
```

## Verification

### Database Query to Verify:
```sql
SELECT terminal_id, issue_state_name, fetched_status 
FROM terminal_details 
WHERE issue_state_name = 'OUT_OF_SERVICE' 
OR issue_state_name = 'MAINTENANCE'
ORDER BY created_at DESC;
```

Expected Result: No `MAINTENANCE` entries, all should be `OUT_OF_SERVICE`.

## Status: IMPLEMENTATION COMPLETE ✅

The MAINTENANCE → OUT_OF_SERVICE mapping is fully implemented and ready for production testing on Windows machines.

---
**Implementation Date**: January 2025  
**Git Branch**: `feature/sigit-cash-information`  
**Status**: ✅ DEPLOYED TO GITHUB - Ready for Windows testing

### Next Steps:
1. Test the script on Windows machine
2. Verify status mapping in production database
3. Confirm regional data calculations are accurate
4. Monitor for any edge cases or additional mapping needs
