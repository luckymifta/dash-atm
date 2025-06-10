# API Data Source Verification Report

## 📊 Overview

This report verifies the data sources used by different API endpoints in `api_option_2_fastapi_fixed.py` to understand potential discrepancies between dashboard card status and ATM information pages.

## 🗄️ Database Tables Analysis

### Current Database Status
- **`regional_data`**: 139 records ✅ (Used by Dashboard Summary)
- **`terminal_details`**: 1,937 records ✅ (Used by ATM List/Information)
- **`regional_atm_counts`**: 0 records ❌ (Legacy table - Empty)

## 🔍 API Endpoints and Data Sources

### 1. Dashboard Summary Endpoint
**Endpoint**: `GET /api/v1/atm/status/summary`
**Data Source**: `regional_data` table
**Query Logic**:
```sql
WITH latest_data AS (
    SELECT DISTINCT ON (region_code)
        region_code, count_available, count_warning, count_zombie,
        count_wounded, count_out_of_service, retrieval_timestamp
    FROM regional_data
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

**Current Data**: 
- Available: 12
- Warning: 0
- Wounded: 1
- Zombie: 1
- Out of Service: 0

### 2. ATM List/Information Endpoint
**Endpoint**: `GET /api/v1/atm/list`
**Data Source**: `terminal_details` table
**Query Logic**:
```sql
WITH latest_atm_data AS (
    SELECT DISTINCT ON (terminal_id)
        terminal_id, location, issue_state_name, serial_number,
        retrieved_date, fetched_status
    FROM terminal_details
    ORDER BY terminal_id, retrieved_date DESC
)
SELECT * FROM latest_atm_data
```

**Current Data**:
- Available: 12 terminals
- Wounded: 1 terminal (Terminal 2604: BRI - SUB-BRANCH AUDIAN)
- Zombie: 1 terminal (Terminal 147: CENTRO SUPERMERCADO PANTAI KELAPA)

## ✅ Verification Results

### Data Consistency Status: CONSISTENT ✅

Both data sources currently show **identical results**:
- **Dashboard Summary (regional_data)**: 1 WOUNDED ATM
- **ATM Information (terminal_details)**: 1 WOUNDED ATM

### Current ATM Status Distribution (14 Total ATMs)
| Terminal ID | Location | Status | Last Updated |
|-------------|----------|---------|--------------|
| 49 | AV. ALM. AMERICO TOMAS | AVAILABLE | 2025-06-10 08:07:58 |
| 83 | RUA NICOLAU DOS REIS LOBATO | AVAILABLE | 2025-06-10 08:07:58 |
| 85 | ESTRADA DE BALIDE, BALIDE | AVAILABLE | 2025-06-10 08:07:58 |
| 86 | FATU AHI | AVAILABLE | 2025-06-10 08:07:58 |
| 87 | PERTAMINA INT. BEBORRA RUA. DOS MARTIRES DA PATRIA | AVAILABLE | 2025-06-10 08:07:58 |
| 88 | AERO PORTO NICOLAU LOBATU,DILI | AVAILABLE | 2025-06-10 08:07:58 |
| 89 | UNTL, RUA JACINTO CANDIDO | AVAILABLE | 2025-06-10 08:07:58 |
| 90 | NOVO TURISMO, BIDAU LECIDERE | AVAILABLE | 2025-06-10 08:07:58 |
| 93 | TIMOR PLAZA COMORO | AVAILABLE | 2025-06-10 08:07:58 |
| 147 | CENTRO SUPERMERCADO PANTAI KELAPA | **ZOMBIE** | 2025-06-10 08:07:58 |
| 169 | BRI SUB-BRANCH FATUHADA | AVAILABLE | 2025-06-10 08:07:58 |
| 2603 | BRI - CENTRAL OFFICE COLMERA 02 | AVAILABLE | 2025-06-10 08:07:58 |
| **2604** | **BRI - SUB-BRANCH AUDIAN** | **WOUNDED** | 2025-06-10 08:07:58 |
| 2605 | BRI - SUB BRANCH HUDILARAN | AVAILABLE | 2025-06-10 08:07:58 |

## 🔄 Historical Analysis

### Terminal 169 Status Change
Terminal 169 (BRI SUB-BRANCH FATUHADA) was previously WOUNDED but recently changed to AVAILABLE:
- **Previous**: WOUNDED status until 2025-06-10 03:33:40
- **Current**: AVAILABLE status since 2025-06-10 08:07:58

This explains why there might have been 2 WOUNDED ATMs previously (Terminals 169 and 2604), but now there's only 1 WOUNDED ATM (Terminal 2604).

## 🎯 Key Findings

### 1. **No Data Source Discrepancy**
Both API endpoints currently show consistent data:
- Dashboard cards and ATM information pages use different database tables
- However, both tables are properly synchronized and show the same status counts

### 2. **Data Sources Are Different But Consistent**
- **Dashboard Summary**: Uses aggregated regional data (`regional_data` table)
- **ATM Information**: Uses individual terminal data (`terminal_details` table)
- Both sources are updated by the same data collection process

### 3. **Status Mapping is Consistent**
Both endpoints properly handle status mapping:
- `HARD` issue state → `WOUNDED` status
- Status filtering works identically across both data sources

### 4. **Legacy Table Issue Resolved**
- The empty `regional_atm_counts` table (legacy) is not used by current API
- All endpoints use the newer `regional_data` and `terminal_details` tables

## 📋 Recommendations

### ✅ **System is Working Correctly**
1. **Data Consistency**: Both data sources show identical results
2. **Proper Synchronization**: Regional aggregates match individual terminal counts
3. **Accurate Status Mapping**: WOUNDED/HARD status handling is consistent

### 🔍 **For Future Monitoring**
1. **Monitor Data Collection**: Ensure `combined_atm_retrieval_script.py` continues to populate both tables
2. **Status Change Tracking**: Terminal 169 recently recovered from WOUNDED to AVAILABLE status
3. **Regular Verification**: Run periodic checks to ensure data source consistency

## 🏁 Conclusion

**The API endpoints in `api_option_2_fastapi_fixed.py` are using different but properly synchronized data sources:**

- **Dashboard Summary** (`/api/v1/atm/status/summary`) → `regional_data` table
- **ATM Information** (`/api/v1/atm/list`) → `terminal_details` table

**Current status: Both sources show 1 WOUNDED ATM (Terminal 2604), demonstrating proper data consistency across different database tables.**

---

**Report Generated**: June 10, 2025  
**Data Timestamp**: 2025-06-10 08:07:58  
**Status**: ✅ VERIFIED - No discrepancy found
