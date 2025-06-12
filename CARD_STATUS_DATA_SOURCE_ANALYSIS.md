# 🔍 ATM Card Status Data Source Discrepancy Analysis

## 🎯 Issue Summary

**Problem**: The dashboard main page cards (Total ATMs, Available, Warning, Wounded, Out Of Service) show different data compared to the ATM information page (`/atm-information`).

## 📊 Root Cause Analysis

### 1. **Different Data Sources**

| Page | API Endpoint | Database Table | Purpose |
|------|-------------|----------------|---------|
| **Dashboard Cards** | `/api/v1/atm/status/summary` | `regional_data` | Aggregated regional counts |
| **ATM Information** | `/api/v1/atm/status/latest` | `terminal_details` | Individual terminal details |

### 2. **Data Flow Differences**

#### Dashboard Cards Data Flow:
```
ATM Management System → Fifth Graphic API → regional_data table → Dashboard Cards
```

#### ATM Information Data Flow:
```
ATM Management System → Terminal Details API → terminal_details table → ATM Information Page
```

## 🔍 Technical Details

### Dashboard Summary Endpoint
**File**: `backend/api_option_2_fastapi_fixed.py` (line 489)
**Function**: `get_atm_summary()`
**Query**:
```sql
WITH latest_data AS (
    SELECT DISTINCT ON (region_code)
        region_code, count_available, count_warning, count_zombie,
        count_wounded, count_out_of_service, total_atms_in_region,
        retrieval_timestamp
    FROM regional_data
    WHERE region_code = 'TL-DL'
    ORDER BY region_code, retrieval_timestamp DESC
)
SELECT 
    SUM(count_available) as total_available,
    SUM(count_warning) as total_warning,
    SUM(count_zombie) as total_zombie,
    SUM(count_wounded) as total_wounded,
    SUM(count_out_of_service) as total_out_of_service
FROM latest_data
```

### ATM Information Data Source
**File**: `frontend/src/app/atm-information/page.tsx` (line 34)
**Function**: `fetchTerminalDetails()`
**API Call**: `atmApiService.getTerminalDetails('both', true)`
**Query**: Gets individual terminal records from `terminal_details` table

## 🚨 Potential Causes

### 1. **Update Timing Mismatch**
- Regional data might be updated at different intervals than terminal details
- One data source might be more recent than the other

### 2. **Data Collection Scope**
- Regional data aggregates status counts from API reports
- Terminal details retrieves individual terminal information
- Different ATMs might be included in each dataset

### 3. **Status Mapping Differences**
- Regional API might use different status categorization
- Terminal details might have more granular statuses (HARD, CASH, etc.)
- Status mapping logic might differ between the two sources

### 4. **Database Synchronization Issues**
- The two tables might not be updated simultaneously
- Data might be coming from different API endpoints with different results

## 🛠 Verification Steps

### 1. **Run Verification Script**
```bash
cd /Users/luckymifta/Documents/2.\ AREA/dash-atm
python verify_card_data_sources.py
```

### 2. **Manual Database Checks**
```sql
-- Check regional_data (Dashboard source)
SELECT region_code, count_available, count_warning, count_wounded, 
       count_zombie, count_out_of_service, retrieval_timestamp
FROM regional_data 
ORDER BY retrieval_timestamp DESC 
LIMIT 5;

-- Check terminal_details (ATM Info source)
SELECT fetched_status, COUNT(*) as count
FROM (
    SELECT DISTINCT ON (terminal_id) 
           terminal_id, fetched_status, retrieved_date
    FROM terminal_details
    ORDER BY terminal_id, retrieved_date DESC
) latest_terminals
GROUP BY fetched_status
ORDER BY count DESC;
```

### 3. **API Endpoint Testing**
```bash
# Test dashboard summary
curl "http://localhost:8000/api/v1/atm/status/summary" | jq

# Test ATM information data
curl "http://localhost:8000/api/v1/atm/status/latest?include_terminal_details=true" | jq
```

## 💡 Recommended Solutions

### Option 1: **Use Single Source of Truth**
- Modify one page to use the same data source as the other
- Ensures consistency but might lose some detail/granularity

### Option 2: **Synchronize Data Sources**
- Ensure both tables are updated from the same source
- Implement data validation to check consistency

### Option 3: **Real-time Calculation**
- Calculate dashboard cards from terminal_details data in real-time
- More accurate but potentially slower

### Option 4: **Data Reconciliation Process**
- Implement a process to reconcile differences
- Alert when discrepancies are detected

## 🔧 Implementation Priority

### Immediate Fix (Quick Win):
1. **Verify update timestamps** - Check which data is more recent
2. **Use more recent data source** for both pages temporarily
3. **Add data source indicators** to show which data is being used

### Long-term Solution:
1. **Implement unified data collection** from single API source
2. **Create data validation** to ensure consistency
3. **Add monitoring** to detect future discrepancies

## 📋 Next Steps

1. **Run the verification script** to identify exact discrepancies
2. **Check database update logs** to understand timing differences
3. **Review data collection scripts** to ensure they're hitting same endpoints
4. **Implement temporary fix** using single source
5. **Plan long-term data architecture** improvement

## 🎯 Files to Review

### Backend Files:
- `backend/api_option_2_fastapi_fixed.py` (line 489) - Dashboard summary endpoint
- `backend/combined_atm_retrieval_script.py` - Regional data collection
- `backend/atm_details_retrieval_script.py` - Terminal details collection

### Frontend Files:
- `frontend/src/app/dashboard/page.tsx` - Dashboard cards
- `frontend/src/app/atm-information/page.tsx` - ATM information page
- `frontend/src/services/atmApi.ts` - API service layer

### Database Tables:
- `regional_data` - Used by dashboard cards
- `terminal_details` - Used by ATM information page
- `regional_atm_counts` - Legacy table (might still be used)

---

**Created**: December 6, 2024  
**Status**: Analysis Complete - Verification Script Ready  
**Priority**: High - Affects data accuracy across application
