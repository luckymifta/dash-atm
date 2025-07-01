-- ATM Masters Table Creation Script
-- This script creates the atm_masters table to store master information for ATM terminals
-- Compatible with PostgreSQL database

-- Drop table if exists (uncomment if you need to recreate)
-- DROP TABLE IF EXISTS atm_masters CASCADE;

-- Create ATM Masters table
CREATE TABLE IF NOT EXISTS atm_masters (
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_atm_masters_terminal_id ON atm_masters(terminal_id);
CREATE INDEX IF NOT EXISTS idx_atm_masters_bank ON atm_masters(bank);
CREATE INDEX IF NOT EXISTS idx_atm_masters_brand_model ON atm_masters(brand, model);
CREATE INDEX IF NOT EXISTS idx_atm_masters_location ON atm_masters(city, region);
CREATE INDEX IF NOT EXISTS idx_atm_masters_active ON atm_masters(is_active);
CREATE INDEX IF NOT EXISTS idx_atm_masters_geo ON atm_masters(latitude, longitude) WHERE latitude IS NOT NULL;

-- JSONB indexes for flexible queries
CREATE INDEX IF NOT EXISTS idx_atm_masters_hardware_specs ON atm_masters USING GIN(hardware_specs);
CREATE INDEX IF NOT EXISTS idx_atm_masters_software_config ON atm_masters USING GIN(software_config);
CREATE INDEX IF NOT EXISTS idx_atm_masters_custom_attrs ON atm_masters USING GIN(custom_attributes);

-- Create update timestamp trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_atm_masters_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic updated_at timestamp
DROP TRIGGER IF EXISTS trigger_atm_masters_updated_at ON atm_masters;
CREATE TRIGGER trigger_atm_masters_updated_at
    BEFORE UPDATE ON atm_masters
    FOR EACH ROW
    EXECUTE FUNCTION update_atm_masters_updated_at();

-- Insert sample data for your 14 ATMs based on current system analysis
INSERT INTO atm_masters (
    terminal_id, terminal_name, external_id, network_id, business_id, brand, model, bank, 
    location, region, geo_location, latitude, longitude, location_type, 
    is_active, currency, timezone, created_by
) VALUES
-- Real terminal data from your system
('83', 'Nautilus Hyosun Dili Central 1', '45201', 'P24', '00601', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'RUA NICOLAU DOS REIS LOBATO', 'Dili', 'TL-DL', -8.5569, 125.5603, 'Public Area', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('2603', 'BRI Central Office ATM', 'BRI2603', 'P24', 'BRI2603', 'NCR', 'SelfServ 22e', 'BRI', 
 'BRI - CENTRAL OFFICE COLMERA 02', 'Dili', 'TL-DL', -8.5594, 125.5647, 'Financial Institution Office', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('87', 'Pertamina Station ATM', '45205', 'P24', '00605', 'Diebold', '4900', 'BRI', 
 'PERTAMINA INT. BEBORRA RUA. DOS MARTIRES DA PATRIA', 'Dili', 'TL-DL', -8.5712, 125.5389, 'Gas Station', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('88', 'Airport ATM', '45203', 'P24', '00603', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'AERO PORTO NICOLAU LOBATU,DILI', 'Dili', 'TL-DL', -8.5464, 125.5289, 'Airport', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('2604', 'BRI Audian Branch', 'BRI2604', 'P24', 'BRI2604', 'Wincor Nixdorf', 'ProCash 2100xe', 'BRI', 
 'BRI - SUB-BRANCH AUDIAN', 'Dili', 'TL-DL', -8.5534, 125.5712, 'Financial Institution Office', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('85', 'Balide ATM', '45207', 'P24', '00607', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'ESTRADA DE BALIDE, BALIDE', 'Dili', 'TL-DL', -8.5345, 125.5890, 'Public Area', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('147', 'Centro Supermercado ATM', '45214', 'P24', '00614', 'NCR', 'SelfServ 22e', 'BRI', 
 'CENTRO SUPERMERCADO PANTAI KELAPA', 'Dili', 'TL-DL', -8.5623, 125.5456, 'Supermarket', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('49', 'Americo Tomas Avenue ATM', '45209', 'P24', '00609', 'Nautilus Hyosun', 'Monimax 5600', 'BRI', 
 'AV. ALM. AMERICO TOMAS', 'Dili', 'TL-DL', -8.5578, 125.5634, 'Public Area', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('86', 'Fatu Ahi ATM', '45204', 'P24', '00604', 'Diebold', '4900', 'BRI', 
 'FATU AHI', 'Dili', 'TL-DL', -8.5612, 125.5545, 'Public Area', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('2605', 'BRI Hudilaran Branch', 'BRI2605', 'P24', 'BRI2605', 'Wincor Nixdorf', 'ProCash 2100xe', 'BRI', 
 'BRI - SUB BRANCH HUDILARAN', 'Dili', 'TL-DL', -8.5467, 125.5789, 'Financial Institution Office', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('169', 'BRI Fatuhada Branch', '45211', 'P24', '00611', 'NCR', 'SelfServ 22e', 'BRI', 
 'BRI SUB-BRANCH FATUHADA', 'Dili', 'TL-DL', -8.5601, 125.5723, 'Financial Institution Office', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('90', 'Novo Turismo ATM', '45200', 'P24', '00600', 'Nautilus Hyosun', 'Monimax 5600', 'BNU', 
 'NOVO TURISMO, BIDAU LECIDERE', 'Dili', 'TL-DL', -8.5534, 125.5445, 'Hotel', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('89', 'UNTL University ATM', '45202', 'P24', '00602', 'NCR', 'SelfServ 22e', 'BNCTL', 
 'UNTL, RUA JACINTO CANDIDO', 'Dili', 'TL-DL', -8.5456, 125.5667, 'University Area', 
 TRUE, 'USD', 'Asia/Dili', 'system_import'),

('93', 'Timor Plaza ATM', '45209', 'P24', '00609', 'Diebold', '4900', 'Mandiri', 
 'TIMOR PLAZA COMORO', 'Dili', 'TL-DL', -8.5589, 125.5612, 'Shopping Center', 
 TRUE, 'USD', 'Asia/Dili', 'system_import')

ON CONFLICT (terminal_id) DO UPDATE SET
    terminal_name = EXCLUDED.terminal_name,
    external_id = EXCLUDED.external_id,
    network_id = EXCLUDED.network_id,
    business_id = EXCLUDED.business_id,
    brand = EXCLUDED.brand,
    model = EXCLUDED.model,
    bank = EXCLUDED.bank,
    location = EXCLUDED.location,
    region = EXCLUDED.region,
    geo_location = EXCLUDED.geo_location,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    location_type = EXCLUDED.location_type,
    updated_at = CURRENT_TIMESTAMP,
    updated_by = 'system_update';

-- Verify the data was inserted
SELECT 
    terminal_id, 
    terminal_name, 
    brand, 
    model, 
    bank, 
    location, 
    is_active
FROM atm_masters 
ORDER BY terminal_id;

-- Show table structure
\d atm_masters;

COMMIT;
