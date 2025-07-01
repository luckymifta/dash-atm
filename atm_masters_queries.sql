-- ATM Masters Table - Useful SQL Queries
-- This file contains practical SQL queries for working with the atm_masters table

-- =====================================================
-- 1. BASIC INVENTORY AND REPORTING QUERIES
-- =====================================================

-- Get all active ATMs with basic information
SELECT 
    terminal_id,
    terminal_name,
    brand,
    model,
    bank,
    location,
    region
FROM atm_masters 
WHERE is_active = TRUE
ORDER BY terminal_id;

-- Hardware inventory summary
SELECT 
    brand,
    model,
    COUNT(*) as count,
    STRING_AGG(terminal_id, ', ' ORDER BY terminal_id) as terminal_ids
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY brand, model
ORDER BY brand, model;

-- ATMs by bank
SELECT 
    bank,
    COUNT(*) as total_atms,
    STRING_AGG(terminal_id, ', ' ORDER BY terminal_id) as terminal_ids
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY bank
ORDER BY total_atms DESC;

-- ATMs by location type
SELECT 
    location_type,
    COUNT(*) as count,
    STRING_AGG(terminal_id, ', ' ORDER BY terminal_id) as terminals
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY location_type
ORDER BY count DESC;

-- =====================================================
-- 2. GEOGRAPHIC AND LOCATION QUERIES
-- =====================================================

-- ATMs by region
SELECT 
    region,
    COUNT(*) as count,
    STRING_AGG(location, '; ' ORDER BY terminal_id) as locations
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY region
ORDER BY count DESC;

-- Find ATMs near a specific coordinate (within 5km radius)
-- Example: Find ATMs near Dili center (-8.5569, 125.5603)
SELECT 
    terminal_id,
    terminal_name,
    location,
    latitude,
    longitude,
    ROUND(
        (6371 * acos(
            cos(radians(-8.5569)) * cos(radians(latitude)) * 
            cos(radians(longitude) - radians(125.5603)) + 
            sin(radians(-8.5569)) * sin(radians(latitude))
        ))::numeric, 2
    ) AS distance_km
FROM atm_masters
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL
  AND is_active = TRUE
  AND (6371 * acos(
        cos(radians(-8.5569)) * cos(radians(latitude)) * 
        cos(radians(longitude) - radians(125.5603)) + 
        sin(radians(-8.5569)) * sin(radians(latitude))
      )) <= 5
ORDER BY distance_km;

-- ATMs with missing geographic coordinates
SELECT 
    terminal_id,
    terminal_name,
    location,
    region
FROM atm_masters 
WHERE (latitude IS NULL OR longitude IS NULL)
  AND is_active = TRUE
ORDER BY terminal_id;

-- =====================================================
-- 3. INTEGRATION WITH EXISTING TABLES
-- =====================================================

-- Join with terminals table to show current status
SELECT 
    m.terminal_id,
    m.terminal_name,
    m.location,
    m.brand,
    m.model,
    m.bank,
    t.status as current_status,
    t.updated_at as last_status_update
FROM atm_masters m
LEFT JOIN terminals t ON m.terminal_id = t.terminal_id
WHERE m.is_active = TRUE
ORDER BY m.terminal_id;

-- Join with terminal_details to show latest status information
SELECT 
    m.terminal_id,
    m.terminal_name,
    m.location,
    m.brand,
    m.model,
    td.issue_state_name as current_status,
    td.retrieved_date as last_update
FROM atm_masters m
LEFT JOIN LATERAL (
    SELECT issue_state_name, retrieved_date
    FROM terminal_details 
    WHERE terminal_id = m.terminal_id
    ORDER BY retrieved_date DESC
    LIMIT 1
) td ON TRUE
WHERE m.is_active = TRUE
ORDER BY m.terminal_id;

-- ATMs with recent notifications
SELECT 
    m.terminal_id,
    m.terminal_name,
    m.location,
    n.title,
    n.message,
    n.severity,
    n.created_at
FROM atm_masters m
INNER JOIN atm_notifications n ON m.terminal_id = n.terminal_id
WHERE m.is_active = TRUE
  AND n.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY n.created_at DESC;

-- =====================================================
-- 4. MAINTENANCE AND OPERATIONAL QUERIES
-- =====================================================

-- ATMs requiring maintenance (if maintenance dates are populated)
SELECT 
    terminal_id,
    terminal_name,
    location,
    last_maintenance_date,
    next_maintenance_date,
    CASE 
        WHEN next_maintenance_date < CURRENT_DATE THEN 'OVERDUE'
        WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'DUE SOON'
        ELSE 'OK'
    END as maintenance_status
FROM atm_masters 
WHERE is_active = TRUE
  AND next_maintenance_date IS NOT NULL
ORDER BY next_maintenance_date;

-- ATMs by installation year (if installation dates are populated)
SELECT 
    EXTRACT(YEAR FROM installation_date) as installation_year,
    COUNT(*) as count,
    STRING_AGG(terminal_id, ', ' ORDER BY terminal_id) as terminal_ids
FROM atm_masters 
WHERE installation_date IS NOT NULL
  AND is_active = TRUE
GROUP BY EXTRACT(YEAR FROM installation_date)
ORDER BY installation_year;

-- =====================================================
-- 5. DATA QUALITY AND VALIDATION QUERIES
-- =====================================================

-- Check for duplicate external_ids
SELECT 
    external_id,
    COUNT(*) as count,
    STRING_AGG(terminal_id, ', ') as terminals
FROM atm_masters 
GROUP BY external_id
HAVING COUNT(*) > 1;

-- Check for missing required fields
SELECT 
    terminal_id,
    CASE WHEN terminal_name IS NULL OR terminal_name = '' THEN 'Missing terminal_name' END as issue1,
    CASE WHEN brand IS NULL OR brand = '' THEN 'Missing brand' END as issue2,
    CASE WHEN model IS NULL OR model = '' THEN 'Missing model' END as issue3,
    CASE WHEN bank IS NULL OR bank = '' THEN 'Missing bank' END as issue4,
    CASE WHEN location IS NULL OR location = '' THEN 'Missing location' END as issue5
FROM atm_masters
WHERE (terminal_name IS NULL OR terminal_name = '')
   OR (brand IS NULL OR brand = '')
   OR (model IS NULL OR model = '')
   OR (bank IS NULL OR bank = '')
   OR (location IS NULL OR location = '');

-- Validate coordinate ranges
SELECT 
    terminal_id,
    latitude,
    longitude,
    CASE 
        WHEN latitude < -90 OR latitude > 90 THEN 'Invalid latitude'
        WHEN longitude < -180 OR longitude > 180 THEN 'Invalid longitude'
        ELSE 'Valid coordinates'
    END as coordinate_status
FROM atm_masters 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- =====================================================
-- 6. DASHBOARD AND SUMMARY QUERIES
-- =====================================================

-- Overall ATM summary statistics
SELECT 
    COUNT(*) as total_atms,
    COUNT(CASE WHEN is_active THEN 1 END) as active_atms,
    COUNT(CASE WHEN NOT is_active THEN 1 END) as inactive_atms,
    COUNT(DISTINCT bank) as total_banks,
    COUNT(DISTINCT brand) as total_brands,
    COUNT(DISTINCT location_type) as location_types,
    COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) as with_coordinates
FROM atm_masters;

-- ATM distribution by bank and brand
SELECT 
    bank,
    brand,
    COUNT(*) as count
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY bank, brand
ORDER BY bank, brand;

-- Location type distribution
SELECT 
    location_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY location_type
ORDER BY count DESC;

-- =====================================================
-- 7. USEFUL UPDATE OPERATIONS
-- =====================================================

-- Update coordinates for a specific ATM
-- UPDATE atm_masters 
-- SET latitude = -8.5569, longitude = 125.5603, updated_by = 'admin'
-- WHERE terminal_id = '83';

-- Bulk update location type based on location text
-- UPDATE atm_masters 
-- SET location_type = 'Financial Institution Office'
-- WHERE location ILIKE '%BRI%' AND location_type IS NULL;

-- Mark ATM as inactive
-- UPDATE atm_masters 
-- SET is_active = FALSE, updated_by = 'admin'
-- WHERE terminal_id = 'XXX';

-- =====================================================
-- 8. EXPORT QUERIES FOR INTEGRATION
-- =====================================================

-- Export format for external systems (CSV-ready)
SELECT 
    terminal_id,
    terminal_name,
    external_id,
    brand,
    model,
    bank,
    location,
    latitude,
    longitude,
    location_type,
    is_active,
    created_at,
    updated_at
FROM atm_masters 
ORDER BY terminal_id;

-- Export with current status (requires terminals table)
SELECT 
    m.terminal_id,
    m.terminal_name,
    m.brand,
    m.model,
    m.bank,
    m.location,
    m.latitude,
    m.longitude,
    COALESCE(t.status, 'UNKNOWN') as current_status,
    m.is_active
FROM atm_masters m
LEFT JOIN terminals t ON m.terminal_id = t.terminal_id
WHERE m.is_active = TRUE
ORDER BY m.terminal_id;
