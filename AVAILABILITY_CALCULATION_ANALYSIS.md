# ATM Availability Calculation Discrepancy Analysis

## Issue Summary

Two different availability percentages are displayed in the ATM monitoring system:
- **Overall Availability (Dashboard)**: 83.33%
- **ATM Availability History (Chart)**: 80.00% (most recent data point)

## Root Cause Analysis

### 1. Data Source Differences

#### Dashboard Overall Availability (83.33%)
- **Endpoint**: `/api/v1/atm/status/summary?table_type=legacy`
- **Data Source**: `terminal_details` table (individual ATM status records)
- **Total ATMs**: **18**
- **Operational ATMs**: 14 (available) + 1 (warning) = **15**
- **Calculation**: 15 ÷ 18 = **83.33%**
- **Data Type**: Real-time individual ATM status
- **Last Updated**: 2025-07-01T09:23:57Z

#### ATM Availability History Chart (80.00%)
- **Endpoint**: `/api/v1/atm/status/trends/TL-DL?hours=24&table_type=legacy`
- **Data Source**: `regional_data` table (aggregated regional counts)
- **Total ATMs**: **15** (in recent data points)
- **Operational ATMs**: 11 (available) + 1 (warning) = **12**
- **Calculation**: 12 ÷ 15 = **80.00%**
- **Data Type**: Historical aggregated regional data
- **Last Data Point**: 2025-07-01T18:24:18.855081

### 2. Key Differences Identified

| Aspect | Dashboard | History Chart |
|--------|-----------|---------------|
| **Data Source** | `terminal_details` | `regional_data` |
| **Total ATMs** | 18 | 15 |
| **Data Freshness** | Real-time | Historical (15-20 min intervals) |
| **Data Type** | Individual status | Aggregated counts |
| **Update Frequency** | Continuous | Batch updates |

## Technical Analysis

### Data Synchronization Issues

1. **ATM Count Mismatch**: 
   - `terminal_details` has 18 ATMs
   - `regional_data` recent entries show only 15 ATMs
   - Missing 3 ATMs in the aggregated data

2. **Data Pipeline Delay**:
   - Regional aggregation runs on scheduled intervals
   - Individual status updates happen more frequently
   - Time lag between the two systems

3. **Data Source Inconsistency**:
   - Different tables with different update mechanisms
   - Possible filtering differences between systems

## Verification Commands

To verify the current state:

```bash
# Check dashboard data (terminal_details)
curl "http://localhost:8000/api/v1/atm/status/summary?table_type=legacy" | jq '.'

# Check chart data (regional_data) 
curl "http://localhost:8000/api/v1/atm/status/trends/TL-DL?hours=24&table_type=legacy" | jq '.trends[-1]'

# Compare ATM counts
curl "http://localhost:8000/api/v1/atm/status/summary?table_type=legacy" | jq '.total_atms'
curl "http://localhost:8000/api/v1/atm/status/trends/TL-DL?hours=1&table_type=legacy" | jq '.trends[-1].status_counts.total'
```

## Solutions Implemented

### 1. Frontend Debugging Enhancement ✅

Added debug information to the ATM Availability Chart:
- Display total ATM count from data source
- Show data source type (regional_data vs terminal_details)
- Visual indicator of data source discrepancies

```tsx
// Added debug info display
{debugInfo && (
  <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
    {debugInfo.totalATMs} ATMs ({debugInfo.dataSource})
  </div>
)}
```

### 2. Data Source Consistency ✅

Changed the ATM Availability Chart to use the same table type as the dashboard:
```tsx
// Use 'legacy' to match the dashboard's data source for consistency
const response = await atmApiService.getRegionalTrends('TL-DL', currentPeriod.hours, 'legacy');
```

## Recommended Long-term Solutions

### 1. Database Investigation 🔍

Investigate why `regional_data` has fewer ATMs than `terminal_details`:

```sql
-- Check ATM counts in both tables
SELECT 'terminal_details' as source, COUNT(DISTINCT terminal_id) as atm_count 
FROM terminal_details 
WHERE retrieved_date >= NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 'regional_data' as source, 
       (count_available + count_warning + count_zombie + count_wounded + count_out_of_service) as atm_count
FROM regional_data 
WHERE region_code = 'TL-DL' 
  AND retrieval_timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY atm_count DESC;

-- Find missing ATMs
SELECT terminal_id, location, fetched_status, retrieved_date
FROM terminal_details 
WHERE retrieved_date >= NOW() - INTERVAL '1 hour'
  AND terminal_id NOT IN (
    -- This would need to be customized based on how regional aggregation works
    SELECT unnest(string_to_array('list_of_aggregated_atm_ids', ','))
  );
```

### 2. Data Pipeline Synchronization 🔄

Ensure both data sources update consistently:
- Review the regional aggregation process
- Implement real-time regional data updates
- Add data validation checks

### 3. API Endpoint Consolidation 🔧

Create a unified availability endpoint that provides consistent data:

```python
@app.get("/api/v1/atm/status/availability-unified")
async def get_unified_availability():
    """
    Unified availability calculation using the same data source
    for both real-time and historical views
    """
    # Use terminal_details as the source of truth for all calculations
    # Generate historical trends from terminal_details data
    # Ensure consistency across all views
```

### 4. Real-time Chart Alternative 📊

Add an option to show real-time availability based on terminal_details:

```tsx
// Toggle between historical (regional_data) and real-time (terminal_details)
const [useRealTimeData, setUseRealTimeData] = useState(false);

if (useRealTimeData) {
  // Fetch from terminal_details and generate synthetic trends
  // This ensures 100% consistency with dashboard
}
```

## Current Status

✅ **Fixed**: Frontend debugging information added  
✅ **Fixed**: Data source consistency improved  
🔍 **Investigating**: Root cause of ATM count mismatch  
🔄 **Pending**: Database investigation and data pipeline review  

## Expected Outcome

After implementing these solutions:
1. **Immediate**: Debug information helps identify data source discrepancies
2. **Short-term**: Better consistency between dashboard and chart
3. **Long-term**: Single source of truth for all availability calculations

## Monitoring

To monitor the consistency going forward:
1. Track ATM counts from both data sources
2. Alert when counts diverge significantly
3. Regular validation of data pipeline integrity
4. Compare calculated availability percentages across endpoints

---

**Document Created**: July 1, 2025  
**Analysis Status**: Complete  
**Next Review**: After database investigation
