# Database Index Recommendations for Daily Cash Usage API

## Overview
The Daily Cash Usage API has been optimized for production scale with simplified SQL queries. For optimal performance with large date ranges, the following database indexes are recommended.

## Required Indexes

### 1. Primary Index for Cash Information Queries
```sql
-- Composite index for terminal_cash_information table
CREATE INDEX IF NOT EXISTS idx_tci_terminal_timestamp 
ON terminal_cash_information (terminal_id, retrieval_timestamp);
```

### 2. Date Range Query Optimization
```sql
-- Index for efficient date range filtering
CREATE INDEX IF NOT EXISTS idx_tci_timestamp_cash 
ON terminal_cash_information (retrieval_timestamp, total_cash_amount) 
WHERE total_cash_amount IS NOT NULL AND total_cash_amount > 0;
```

### 3. Timezone Conversion Optimization
```sql
-- Partial index for timezone calculations
CREATE INDEX IF NOT EXISTS idx_tci_dili_date 
ON terminal_cash_information ((retrieval_timestamp AT TIME ZONE 'Asia/Dili')::date, terminal_id)
WHERE total_cash_amount IS NOT NULL AND total_cash_amount > 0;
```

### 4. Terminal Details Join Optimization
```sql
-- Index for terminal location joins
CREATE INDEX IF NOT EXISTS idx_terminal_details_id_location 
ON terminal_details (terminal_id, location);
```

## Performance Benefits

With these indexes in place:
- Date range queries should perform in < 2 seconds for up to 90 days
- Terminal-specific queries will be significantly faster
- Aggregation operations (MIN/MAX/COUNT) will be optimized
- JOIN operations with terminal_details will be efficient

## Deployment Commands

Run these SQL commands on your production database:

```sql
-- Apply all indexes for optimal performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tci_terminal_timestamp 
ON terminal_cash_information (terminal_id, retrieval_timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tci_timestamp_cash 
ON terminal_cash_information (retrieval_timestamp, total_cash_amount) 
WHERE total_cash_amount IS NOT NULL AND total_cash_amount > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tci_dili_date 
ON terminal_cash_information ((retrieval_timestamp AT TIME ZONE 'Asia/Dili')::date, terminal_id)
WHERE total_cash_amount IS NOT NULL AND total_cash_amount > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_terminal_details_id_location 
ON terminal_details (terminal_id, location);
```

Note: Using `CONCURRENTLY` prevents blocking other database operations during index creation.

## Monitoring

After deployment, monitor query performance with:

```sql
-- Check query execution plans
EXPLAIN ANALYZE 
SELECT /* your optimized query here */;

-- Monitor index usage
SELECT 
    indexname, 
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE indexname LIKE 'idx_tci%';
```
