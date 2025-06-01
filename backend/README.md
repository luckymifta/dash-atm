# ATM Dashboard Monitoring System

A comprehensive monitoring system for ATM status tracking with PostgreSQL database integration and real-time dashboard capabilities.

## Features

- **Real-time ATM Status Monitoring**: Track ATM status across multiple regions
- **Regional Analysis**: Monitor fifth_graphic regional data with percentage and count conversion
- **Database Integration**: Store historical data in PostgreSQL for trend analysis
- **Dashboard Interface**: Command-line dashboard with live monitoring capabilities
- **Health Alerting**: Automated health status classification with alerts
- **Data Freshness Tracking**: Monitor data age and identify stale information
- **Historical Analysis**: Track trends over time with daily and hourly aggregations

## Components

### Core Modules

1. **`atm_crawler_complete.py`** - Main crawler for collecting ATM data
2. **`db_connector.py`** - Database connection and data storage functions
3. **`dashboard_queries.py`** - Advanced queries for dashboard analytics
4. **`monitoring_dashboard.py`** - Command-line monitoring dashboard
5. **`run_crawler_with_db.py`** - Production runner with retry logic
6. **`test_dashboard_integration.py`** - Comprehensive testing suite

### Database Schema

#### Main Tables
- **`terminals`** - ATM terminal status data
- **`terminal_details`** - Detailed terminal fault information

#### Regional Tables
- **`regional_atm_counts`** - Fifth_graphic regional ATM count data
  - `unique_request_id` (UUID, Primary Key)
  - `region_code` (VARCHAR) - Region identifier
  - `count_available` (INTEGER) - Available ATMs count
  - `count_warning` (INTEGER) - Warning status ATMs count
  - `count_zombie` (INTEGER) - Zombie status ATMs count
  - `count_wounded` (INTEGER) - Wounded status ATMs count
  - `count_out_of_service` (INTEGER) - Out of service ATMs count
  - `date_creation` (TIMESTAMP WITH TIME ZONE) - Record timestamp
  - Additional percentage and metadata fields

## Quick Start

### 1. Environment Setup

Create a `.env` file with your database configuration:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=atm_monitor
DB_USER=postgres
DB_PASS=your_password
```

### 2. Database Setup

The system will automatically create required tables on first run. To test:

```bash
python test_dashboard_integration.py --generate-sample
```

### 3. Data Collection

#### Manual Data Collection
```bash
# Demo mode (no network required)
python atm_crawler_complete.py --demo --db

# Live mode (requires network access)
python atm_crawler_complete.py --db
```

#### Continuous Monitoring
```bash
# Run with auto-retry and error handling
python run_crawler_with_db.py

# Demo mode for testing
python run_crawler_with_db.py --demo
```

### 4. Dashboard Monitoring

#### Single Report
```bash
python monitoring_dashboard.py
```

#### Live Dashboard
```bash
# Auto-refresh every 30 seconds
python monitoring_dashboard.py --live

# Custom refresh interval
python monitoring_dashboard.py --live --refresh 60
```

#### Specific Views
```bash
# Summary only
python monitoring_dashboard.py --summary-only

# Alerts only
python monitoring_dashboard.py --alerts-only

# Data freshness check
python monitoring_dashboard.py --freshness-only
```

## Dashboard Features

### Summary View
- Total ATMs across all regions
- Status distribution (Available, Warning, Zombie, Wounded, Out of Service)
- Overall availability percentage
- Last update timestamp

### Regional Analysis
- Region-by-region breakdown
- Availability percentages per region
- ATM count by status type
- Health status classification

### Alerts & Health Status
- **CRITICAL**: <50% availability
- **WARNING**: 50-70% availability  
- **ATTENTION**: 70-85% availability
- **HEALTHY**: >85% availability

### Data Freshness Monitoring
- **FRESH**: <1 hour old
- **RECENT**: 1-6 hours old
- **STALE**: 6-24 hours old
- **VERY_STALE**: >24 hours old

### Trend Analysis
- Hourly trends for recent periods
- Daily historical analysis
- Availability percentage changes
- Data point coverage metrics

## Advanced Queries

The `dashboard_queries.py` module provides functions for:

- `get_dashboard_summary()` - Overall system status
- `get_regional_comparison()` - Region-by-region analysis
- `get_alerting_data()` - Health status and alerts
- `get_data_freshness()` - Data age monitoring
- `get_hourly_trends()` - Recent hourly trends
- `get_historical_analysis()` - Multi-day trend analysis

## Testing

### Full Integration Test
```bash
python test_dashboard_integration.py
```

### Quick Test (Essential Components)
```bash
python test_dashboard_integration.py --quick
```

### Generate Sample Data
```bash
python test_dashboard_integration.py --generate-sample
```

### Test with Live Data
```bash
python test_dashboard_integration.py --live-mode
```

## Data Collection Details

### Fifth Graphic Processing
The system processes fifth_graphic data from the reports dashboard:
- Converts percentage values to actual ATM counts
- Maps state types to database columns
- Handles multiple regions (currently focused on TL-DL)
- Validates percentage totals and count accuracy

### Supported ATM States
- **AVAILABLE**: Operational ATMs
- **WARNING**: ATMs with warnings
- **ZOMBIE**: Non-responsive ATMs
- **WOUNDED**: ATMs with partial functionality
- **OUT_OF_SERVICE**: Completely non-functional ATMs

## Production Deployment

### Continuous Operation
```bash
# Run in background with logging
nohup python run_crawler_with_db.py > crawler.log 2>&1 &

# Monitor logs
tail -f crawler.log
```

### Error Handling
The system includes:
- Automatic retry logic for network failures
- Token refresh for authentication issues
- Demo mode fallback for connectivity problems
- Database transaction rollback on errors
- Comprehensive logging and error reporting

## Monitoring and Maintenance

### Log Files
- `crawler_with_db.log` - Main crawler execution log
- `test_login.log` - Authentication testing log

### Health Checks
- Database connectivity monitoring
- Data freshness alerts
- Regional availability thresholds
- Automatic table creation and verification

### Performance Considerations
- Indexed database queries for fast dashboard response
- Pagination support for large datasets
- Timezone-aware timestamps (Asia/Dili)
- Efficient data aggregation queries

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `.env` file configuration
   - Verify PostgreSQL is running
   - Test with: `python test_dashboard_integration.py`

2. **Login Authentication Errors**
   - Verify network connectivity to 172.31.1.46
   - Check credentials in `atm_crawler_complete.py`
   - Use demo mode: `--demo` flag

3. **No Dashboard Data**
   - Run data collection first: `python atm_crawler_complete.py --demo --db`
   - Generate sample data: `python test_dashboard_integration.py --generate-sample`
   - Check database tables: `python test_dashboard_integration.py --quick`

4. **Stale Data Alerts**
   - Check crawler execution schedule
   - Verify network connectivity
   - Review `crawler_with_db.log` for errors

### Support
For issues or questions, check the log files and run the integration test suite to identify specific problems.
