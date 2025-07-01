# ATM Masters Table - Comprehensive Design Recommendation

## 📋 Overview

Based on the analysis of your existing database schema and ATM data patterns, here's a comprehensive recommendation for the `atm_masters` table to store master information for ATM terminals.

## 🗄️ Recommended Table Structure

### Complete SQL DDL

```sql
-- ATM Masters table for storing master configuration and reference data
CREATE TABLE atm_masters (
    -- Primary identifiers
    id SERIAL PRIMARY KEY,
    terminal_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Basic ATM Information
    terminal_name VARCHAR(255),
    external_id VARCHAR(50),
    network_id VARCHAR(50),
    business_id VARCHAR(100),
    technical_code VARCHAR(100),
    
    -- Hardware Specifications
    brand VARCHAR(100) NOT NULL,                    -- Nautilus Hyosun, NCR, Diebold, Wincor Nixdorf
    model VARCHAR(100) NOT NULL,                    -- Monimax 5600, SelfServ 22e, 4900, ProCash 2100xe
    serial_number VARCHAR(100),
    manufacturer_year INTEGER,
    
    -- Financial Institution
    bank VARCHAR(50) NOT NULL,                      -- BRI, BNU, BNCTL, Mandiri
    supplier VARCHAR(100),
    
    -- Location Information
    location VARCHAR(500) NOT NULL,                 -- Primary location description
    location_type VARCHAR(100),                     -- Gas Station, Financial Institution Office, etc.
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    region VARCHAR(100),                            -- TL-DL, TL-AN, etc.
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'Timor-Leste',
    
    -- Geographic Coordinates
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    geo_location VARCHAR(50),                       -- Region code for grouping
    
    -- Technical Configuration
    terminal_type VARCHAR(50) DEFAULT 'ATM',
    os_version VARCHAR(50),
    xfs_version VARCHAR(50),
    connection_type VARCHAR(50),                    -- Network connection type
    
    -- Operational Information
    is_active BOOLEAN DEFAULT TRUE,
    installation_date DATE,
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    service_period VARCHAR(100),
    maintenance_period VARCHAR(100),
    
    -- Service Configuration
    has_advertising BOOLEAN DEFAULT FALSE,
    supports_cash_deposit BOOLEAN DEFAULT FALSE,
    supports_bill_payment BOOLEAN DEFAULT FALSE,
    max_cash_capacity INTEGER,                      -- Maximum cash capacity
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Contact Information
    site_contact_name VARCHAR(255),
    site_contact_phone VARCHAR(50),
    site_contact_email VARCHAR(255),
    
    -- Additional Configuration
    timezone VARCHAR(50) DEFAULT 'Asia/Dili',
    language_code VARCHAR(10) DEFAULT 'EN',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    -- JSONB for flexible configuration
    hardware_specs JSONB,                          -- Additional hardware specifications
    software_config JSONB,                        -- Software configuration details
    compliance_info JSONB,                        -- Regulatory compliance information
    custom_attributes JSONB,                      -- Any custom attributes
    
    -- Constraints
    CONSTRAINT chk_coordinates CHECK (
        (latitude IS NULL AND longitude IS NULL) OR 
        (latitude IS NOT NULL AND longitude IS NOT NULL AND
         latitude BETWEEN -90 AND 90 AND 
         longitude BETWEEN -180 AND 180)
    ),
    CONSTRAINT chk_active_dates CHECK (
        installation_date IS NULL OR 
        installation_date <= CURRENT_DATE
    )
);

-- Indexes for performance
CREATE INDEX idx_atm_masters_terminal_id ON atm_masters(terminal_id);
CREATE INDEX idx_atm_masters_bank ON atm_masters(bank);
CREATE INDEX idx_atm_masters_brand_model ON atm_masters(brand, model);
CREATE INDEX idx_atm_masters_location ON atm_masters(city, region);
CREATE INDEX idx_atm_masters_active ON atm_masters(is_active);
CREATE INDEX idx_atm_masters_geo ON atm_masters(latitude, longitude) WHERE latitude IS NOT NULL;

-- JSONB indexes for flexible queries
CREATE INDEX idx_atm_masters_hardware_specs ON atm_masters USING GIN(hardware_specs);
CREATE INDEX idx_atm_masters_software_config ON atm_masters USING GIN(software_config);
CREATE INDEX idx_atm_masters_custom_attrs ON atm_masters USING GIN(custom_attributes);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_atm_masters_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atm_masters_updated_at
    BEFORE UPDATE ON atm_masters
    FOR EACH ROW
    EXECUTE FUNCTION update_atm_masters_updated_at();
```

## 📊 Sample Data Based on Your Current ATMs

```sql
-- Insert sample master data for your 14 ATMs
INSERT INTO atm_masters (
    terminal_id, terminal_name, external_id, brand, model, bank, location, 
    region, geo_location, latitude, longitude, location_type, is_active
) VALUES
-- Real terminal data from your system
('83', 'Nautilus Hyosun Dili Central 1', '45201', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'RUA NICOLAU DOS REIS LOBATO', 'TL-DL', 'TL-DL', -8.5569, 125.5603, 'Public Area', TRUE),

('2603', 'BRI Central Office ATM', 'BRI2603', 'NCR', 'SelfServ 22e', 'BRI', 
 'BRI - CENTRAL OFFICE COLMERA 02', 'TL-DL', 'TL-DL', -8.5594, 125.5647, 'Financial Institution Office', TRUE),

('87', 'Pertamina Station ATM', '45205', 'Diebold', '4900', 'BRI', 
 'PERTAMINA INT. BEBORRA RUA. DOS MARTIRES DA PATRIA', 'TL-DL', 'TL-DL', -8.5712, 125.5389, 'Gas Station', TRUE),

('88', 'Airport ATM', '45203', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'AERO PORTO NICOLAU LOBATU,DILI', 'TL-DL', 'TL-DL', -8.5464, 125.5289, 'Airport', TRUE),

('2604', 'BRI Audian Branch', 'BRI2604', 'Wincor Nixdorf', 'ProCash 2100xe', 'BRI', 
 'BRI - SUB-BRANCH AUDIAN', 'TL-DL', 'TL-DL', -8.5534, 125.5712, 'Financial Institution Office', TRUE),

('85', 'Balide ATM', '45207', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'ESTRADA DE BALIDE, BALIDE', 'TL-DL', 'TL-DL', -8.5345, 125.5890, 'Public Area', TRUE),

('147', 'Centro Supermercado ATM', '45214', 'NCR', 'SelfServ 22e', 'BRI', 
 'CENTRO SUPERMERCADO PANTAI KELAPA', 'TL-DL', 'TL-DL', -8.5623, 125.5456, 'Supermarket', TRUE),

('49', 'Americo Tomas Avenue ATM', '45209', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'AV. ALM. AMERICO TOMAS', 'TL-DL', 'TL-DL', -8.5578, 125.5634, 'Public Area', TRUE),

('86', 'Fatu Ahi ATM', '45204', 'Diebold', '4900', 'BRI', 
 'FATU AHI', 'TL-DL', 'TL-DL', -8.5612, 125.5545, 'Public Area', TRUE),

('2605', 'BRI Hudilaran Branch', 'BRI2605', 'Wincor Nixdorf', 'ProCash 2100xe', 'BRI', 
 'BRI - SUB BRANCH HUDILARAN', 'TL-DL', 'TL-DL', -8.5467, 125.5789, 'Financial Institution Office', TRUE),

('169', 'BRI Fatuhada Branch', '45211', 'NCR', 'SelfServ 22e', 'BRI', 
 'BRI SUB-BRANCH FATUHADA', 'TL-DL', 'TL-DL', -8.5601, 125.5723, 'Financial Institution Office', TRUE),

('90', 'Novo Turismo ATM', '45200', 'Nautilus Hyosun', 'Monimax 5600', 'BNU', 
 'NOVO TURISMO, BIDAU LECIDERE', 'TL-DL', 'TL-DL', -8.5534, 125.5445, 'Hotel', TRUE),

('89', 'UNTL University ATM', '45202', 'NCR', 'SelfServ 22e', 'BNCTL', 
 'UNTL, RUA JACINTO CANDIDO', 'TL-DL', 'TL-DL', -8.5456, 125.5667, 'University Area', TRUE),

('93', 'Timor Plaza ATM', '45209', 'Diebold', '4900', 'Mandiri', 
 'TIMOR PLAZA COMORO', 'TL-DL', 'TL-DL', -8.5589, 125.5612, 'Shopping Center', TRUE);
```

## 🔗 Integration with Existing Tables

### Relationship Recommendations

```sql
-- Add foreign key relationships to existing tables
-- Note: Execute these after ensuring data consistency

-- Link terminals table to atm_masters
ALTER TABLE terminals 
ADD CONSTRAINT fk_terminals_atm_masters 
FOREIGN KEY (terminal_id) REFERENCES atm_masters(terminal_id);

-- Link terminal_details to atm_masters
ALTER TABLE terminal_details 
ADD CONSTRAINT fk_terminal_details_atm_masters 
FOREIGN KEY (terminal_id) REFERENCES atm_masters(terminal_id);

-- Link atm_notifications to atm_masters
ALTER TABLE atm_notifications 
ADD CONSTRAINT fk_atm_notifications_atm_masters 
FOREIGN KEY (terminal_id) REFERENCES atm_masters(terminal_id);
```

## 📈 Benefits of the ATM Masters Table

### 1. **Centralized Configuration Management**
- Single source of truth for ATM hardware and location data
- Simplified maintenance and updates
- Consistent data across all applications

### 2. **Enhanced Reporting Capabilities**
- Better geographical analysis with precise coordinates
- Hardware inventory management
- Maintenance scheduling and tracking

### 3. **Improved Data Quality**
- Structured data with proper constraints
- Validation of geographical coordinates
- Standardized location and hardware information

### 4. **Flexible Configuration**
- JSONB fields for custom attributes
- Future-proof design for new requirements
- Easy integration with existing monitoring systems

## 🔧 Usage Examples

### Query ATMs by Region
```sql
SELECT terminal_id, terminal_name, location, brand, model
FROM atm_masters 
WHERE region = 'TL-DL' AND is_active = TRUE
ORDER BY location;
```

### Hardware Inventory Report
```sql
SELECT 
    brand,
    model,
    COUNT(*) as count,
    STRING_AGG(terminal_id, ', ') as terminal_ids
FROM atm_masters 
WHERE is_active = TRUE
GROUP BY brand, model
ORDER BY brand, model;
```

### ATMs Near Coordinates (within 5km)
```sql
SELECT 
    terminal_id,
    location,
    (6371 * acos(cos(radians(-8.5569)) * cos(radians(latitude)) * 
     cos(radians(longitude) - radians(125.5603)) + 
     sin(radians(-8.5569)) * sin(radians(latitude)))) AS distance_km
FROM atm_masters
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL
  AND is_active = TRUE
HAVING distance_km <= 5
ORDER BY distance_km;
```

### Join with Current Status
```sql
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
ORDER BY m.location;
```

## 🚀 Implementation Steps

1. **Create the `atm_masters` table** using the provided DDL
2. **Populate with existing ATM data** using the sample INSERT statements
3. **Validate data integrity** with the existing operational tables
4. **Add foreign key constraints** to link with existing tables
5. **Update your applications** to use the masters table for configuration
6. **Create maintenance procedures** for keeping the data current

## 📝 Maintenance Considerations

- **Regular Updates**: Keep hardware specifications and location data current
- **Data Validation**: Implement procedures to validate coordinates and configuration
- **Audit Trail**: Consider adding audit logging for changes to master data
- **Backup Strategy**: Include in your database backup and recovery procedures

This design provides a comprehensive foundation for ATM master data management while integrating seamlessly with your existing monitoring system.
