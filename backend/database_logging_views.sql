-- SQL Views for Enhanced Log Analysis
-- Run this script to create helpful views for analyzing your ATM retrieval logs

-- 1. Execution Overview View
CREATE OR REPLACE VIEW execution_overview AS
SELECT 
    es.execution_id,
    es.start_time,
    es.end_time,
    es.duration_seconds,
    es.demo_mode,
    es.total_atms,
    es.success,
    es.failover_activated,
    es.failure_type,
    es.connection_status,
    es.regional_records_processed,
    es.terminal_details_processed,
    es.error_count,
    es.warning_count,
    es.info_count,
    -- Calculate success rate
    CASE 
        WHEN es.success THEN 'SUCCESS'
        WHEN es.failover_activated THEN 'FAILOVER_SUCCESS'
        ELSE 'FAILED'
    END AS execution_status,
    -- Performance metrics
    ROUND(es.duration_seconds::numeric / 60, 2) AS duration_minutes,
    CASE 
        WHEN es.duration_seconds > 0 THEN ROUND(es.terminal_details_processed::numeric / es.duration_seconds, 2)
        ELSE 0 
    END AS terminals_per_second
FROM execution_summary es
ORDER BY es.start_time DESC;

-- 2. Error Analysis View
CREATE OR REPLACE VIEW error_analysis AS
SELECT 
    le.execution_id,
    le.execution_phase,
    le.level,
    le.terminal_id,
    le.region_code,
    COUNT(*) as error_count,
    STRING_AGG(DISTINCT le.message, '; ') as error_messages,
    MIN(le.timestamp) as first_occurrence,
    MAX(le.timestamp) as last_occurrence
FROM log_events le
WHERE le.level IN ('ERROR', 'WARNING')
GROUP BY le.execution_id, le.execution_phase, le.level, le.terminal_id, le.region_code
ORDER BY le.execution_id DESC, error_count DESC;

-- 3. Performance by Phase View
CREATE OR REPLACE VIEW performance_by_phase AS
SELECT 
    le.execution_id,
    le.execution_phase,
    COUNT(*) as log_entries,
    MIN(le.timestamp) as phase_start,
    MAX(le.timestamp) as phase_end,
    EXTRACT(EPOCH FROM (MAX(le.timestamp) - MIN(le.timestamp))) as phase_duration_seconds,
    SUM(CASE WHEN le.level = 'ERROR' THEN 1 ELSE 0 END) as error_count,
    SUM(CASE WHEN le.level = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
    SUM(CASE WHEN le.level = 'INFO' THEN 1 ELSE 0 END) as info_count
FROM log_events le
WHERE le.execution_phase IS NOT NULL
GROUP BY le.execution_id, le.execution_phase
ORDER BY le.execution_id DESC, phase_start;

-- 4. Terminal Processing Summary
CREATE OR REPLACE VIEW terminal_processing_summary AS
SELECT 
    le.execution_id,
    le.terminal_id,
    COUNT(*) as log_entries,
    SUM(CASE WHEN le.level = 'ERROR' THEN 1 ELSE 0 END) as errors,
    SUM(CASE WHEN le.level = 'WARNING' THEN 1 ELSE 0 END) as warnings,
    MIN(le.timestamp) as first_log,
    MAX(le.timestamp) as last_log,
    EXTRACT(EPOCH FROM (MAX(le.timestamp) - MIN(le.timestamp))) as processing_duration_seconds,
    -- Extract status from log messages
    STRING_AGG(DISTINCT 
        CASE 
            WHEN le.message LIKE '%status%' THEN SUBSTRING(le.message FROM 'status ([A-Z_]+)')
            ELSE NULL
        END, ', ') as detected_statuses
FROM log_events le
WHERE le.terminal_id IS NOT NULL
GROUP BY le.execution_id, le.terminal_id
ORDER BY le.execution_id DESC, errors DESC, warnings DESC;

-- 5. Daily Execution Summary
CREATE OR REPLACE VIEW daily_execution_summary AS
SELECT 
    DATE(es.start_time) as execution_date,
    COUNT(*) as total_executions,
    SUM(CASE WHEN es.success THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN es.failover_activated THEN 1 ELSE 0 END) as failover_executions,
    AVG(es.duration_seconds) as avg_duration_seconds,
    MAX(es.duration_seconds) as max_duration_seconds,
    MIN(es.duration_seconds) as min_duration_seconds,
    AVG(es.terminal_details_processed) as avg_terminals_processed,
    SUM(es.error_count) as total_errors,
    SUM(es.warning_count) as total_warnings,
    -- Success rate
    ROUND(
        (SUM(CASE WHEN es.success THEN 1 ELSE 0 END)::numeric / COUNT(*)) * 100, 
        2
    ) as success_rate_percent
FROM execution_summary es
GROUP BY DATE(es.start_time)
ORDER BY execution_date DESC;

-- 6. Recent Issues View (Last 24 hours)
CREATE OR REPLACE VIEW recent_issues AS
SELECT 
    le.execution_id,
    le.timestamp,
    le.execution_phase,
    le.level,
    le.terminal_id,
    le.message,
    le.error_details->'exception_type' as exception_type,
    le.error_details->'exception_message' as exception_message
FROM log_events le
WHERE 
    le.timestamp >= NOW() - INTERVAL '24 hours'
    AND le.level IN ('ERROR', 'WARNING')
ORDER BY le.timestamp DESC;

-- 7. Connection Status Trends
CREATE OR REPLACE VIEW connection_status_trends AS
SELECT 
    DATE(es.start_time) as date,
    es.connection_status,
    COUNT(*) as execution_count,
    AVG(es.duration_seconds) as avg_duration,
    AVG(es.terminal_details_processed) as avg_terminals_processed
FROM execution_summary es
GROUP BY DATE(es.start_time), es.connection_status
ORDER BY date DESC, execution_count DESC;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_log_events_timestamp_level ON log_events(timestamp, level);
CREATE INDEX IF NOT EXISTS idx_log_events_execution_phase_level ON log_events(execution_phase, level);
CREATE INDEX IF NOT EXISTS idx_execution_summary_start_time ON execution_summary(start_time);
CREATE INDEX IF NOT EXISTS idx_execution_summary_success ON execution_summary(success);

-- Sample queries to get started:

-- Query 1: Get overview of recent executions
-- SELECT * FROM execution_overview LIMIT 10;

-- Query 2: Find executions with errors
-- SELECT * FROM execution_overview WHERE error_count > 0;

-- Query 3: Analyze performance by phase for a specific execution
-- SELECT * FROM performance_by_phase WHERE execution_id = 'your-execution-id';

-- Query 4: Daily success rates
-- SELECT * FROM daily_execution_summary WHERE execution_date >= CURRENT_DATE - INTERVAL '7 days';

-- Query 5: Recent issues
-- SELECT * FROM recent_issues LIMIT 20;

-- Query 6: Terminal-specific issues
-- SELECT * FROM terminal_processing_summary WHERE errors > 0 OR warnings > 0;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_dashboard_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_reporting_user;
