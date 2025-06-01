# Combined ATM Retrieval Script - New Database Tables Integration

## 📋 Overview

Successfully enhanced the combined ATM retrieval script to support storing retrieved data into new database tables with JSONB support. The integration provides both backward compatibility with existing functionality and new enhanced data storage capabilities.

## ✅ Completed Features

### 1. **New Database Tables Support**
- **`regional_data`** table for storing regional ATM count data with JSONB support
- **`terminal_details`** table for storing terminal details data with JSONB support
- Both tables include raw JSON data preservation for enhanced analysis capabilities

### 2. **Command Line Integration**
```bash
# Use new database tables
python combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables

# Use original database tables (backward compatibility)
python combined_atm_retrieval_script.py --demo --save-to-db
```

### 3. **Enhanced Data Storage**
- **Regional Data**: Structured counts + raw fifth_graphic JSON data in JSONB format
- **Terminal Details**: Structured fields + raw terminal data, fault data, and metadata in JSONB format
- **Indexing**: Optimized indexes for performance on key columns and JSONB data

### 4. **Schema Compatibility**
- Aligned with existing database table schemas
- No breaking changes to existing functionality
- Smooth integration with current data structures

## 🗄️ Database Schema

### Regional Data Table (`regional_data`)
```sql
CREATE TABLE regional_data (
    id SERIAL PRIMARY KEY,
    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
    region_code VARCHAR(10) NOT NULL,
    retrieval_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_regional_data JSONB NOT NULL,  -- Complete raw API response
    count_available INTEGER,
    count_warning INTEGER,
    count_zombie INTEGER,
    count_wounded INTEGER,
    count_out_of_service INTEGER,
    total_atms_in_region INTEGER
);
```

### Terminal Details Table (`terminal_details`)
```sql
CREATE TABLE terminal_details (
    id SERIAL PRIMARY KEY,
    unique_request_id UUID NOT NULL DEFAULT gen_random_uuid(),
    terminal_id VARCHAR(50) NOT NULL,
    location TEXT,
    issue_state_name VARCHAR(50),
    serial_number VARCHAR(50),
    retrieved_date TIMESTAMP WITH TIME ZONE NOT NULL,
    fetched_status VARCHAR(50) NOT NULL,
    raw_terminal_data JSONB NOT NULL,  -- Complete terminal info
    fault_data JSONB,                  -- Fault-specific information
    metadata JSONB                     -- Processing metadata
);
```

## 🔍 JSONB Data Structure

### Regional Data JSONB (`raw_regional_data`)
Contains the complete fifth_graphic API response:
```json
{
  "hc-key": "TL-DL",
  "value": 78.57142857142857,
  "color": "#90ED7D"
}
```

### Terminal Details JSONB (`fault_data`)
Contains fault-specific information:
```json
{
  "year": "2025",
  "month": "MAY", 
  "day": "30",
  "externalFaultId": "PRR211980",
  "agentErrorDescription": "DEVICE ERROR",
  "creationDate": "2025-05-30"
}
```

### Terminal Details JSONB (`metadata`)
Contains processing metadata:
```json
{
  "retrieval_timestamp": "2025-05-30T18:34:07.356309+09:00",
  "demo_mode": true,
  "unique_request_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_info": {
    "has_fault_data": true,
    "has_location": true,
    "status_at_retrieval": "WOUNDED"
  }
}
```

## 🚀 Usage Examples

### With New Tables
```bash
# Demo mode with new database tables
python combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables --total-atms 14

# Live mode with new database tables (when network available)
python combined_atm_retrieval_script.py --save-to-db --use-new-tables
```

### Backward Compatibility
```bash
# Original functionality remains unchanged
python combined_atm_retrieval_script.py --demo --save-to-db
```

## 🔧 Key Technical Improvements

### 1. **Schema Alignment**
- Fixed column mapping between script and database
- Removed non-existent columns from INSERT statements
- Aligned table creation with actual database schemas

### 2. **JSONB Integration**
- Raw data preservation for future analysis
- Queryable JSON data using PostgreSQL JSONB operators
- Efficient storage and indexing

### 3. **Error Handling**
- Comprehensive database error handling
- Transaction rollback on failures
- Detailed logging for troubleshooting

### 4. **Performance Optimization**
- Strategic indexing on key columns
- JSONB GIN indexes for efficient JSON queries
- Optimized insert operations

## 📊 Verification Results

Successfully tested with demo data:
- **Regional Data**: 2 records saved to `regional_data` table
- **Terminal Details**: 21 records saved to `terminal_details` table
- **JSONB Data**: Properly stored and queryable
- **Backward Compatibility**: Original functionality maintained

### Sample Query Examples
```sql
-- Query regional data with JSONB
SELECT region_code, 
       raw_regional_data->>'hc-key' as original_key,
       count_available, total_atms_in_region
FROM regional_data;

-- Query terminal details with JSONB  
SELECT terminal_id,
       fault_data->>'externalFaultId' as fault_id,
       metadata->>'demo_mode' as demo_mode,
       fetched_status
FROM terminal_details
WHERE fault_data->>'externalFaultId' IS NOT NULL;
```

## 🎯 Benefits

1. **Enhanced Data Storage**: Complete raw data preservation
2. **Future-Proof**: JSONB support for evolving data structures  
3. **Backward Compatible**: No disruption to existing workflows
4. **Performance**: Optimized indexing and query capabilities
5. **Flexibility**: Easy data analysis and reporting
6. **Reliability**: Comprehensive error handling and logging

## 📝 Next Steps

1. **Production Testing**: Test with live data when network connectivity is available
2. **Monitoring**: Implement monitoring for new table performance
3. **Analytics**: Develop queries and reports using JSONB data
4. **Documentation**: Update user guides and API documentation

---

**Status**: ✅ **COMPLETED AND TESTED**  
**Integration**: Fully functional with both new and original database functionality  
**Compatibility**: Backward compatible with existing scripts and workflows
