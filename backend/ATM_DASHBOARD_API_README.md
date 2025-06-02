# ATM Dashboard FastAPI Application

## Overview
The ATM Dashboard FastAPI application is now running successfully and provides comprehensive ATM monitoring capabilities with modern FastAPI features.

## 🚀 Current Status
- **Status**: ✅ RUNNING
- **URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Database**: ✅ Connected to PostgreSQL
- **Health Status**: ✅ Healthy

## 📊 API Endpoints

### System Health
- `GET /api/v1/health` - API health check and database connectivity

### ATM Status Monitoring
- `GET /api/v1/atm/status/summary` - Overall ATM status summary across all regions
- `GET /api/v1/atm/status/regional` - Regional breakdown with filters
- `GET /api/v1/atm/status/trends/{region_code}` - Regional trends over time
- `GET /api/v1/atm/status/latest` - Latest data with optional table selection

### Query Parameters
- `table_type`: Choose between `legacy`, `new`, or `both` data sources
- `region_filter`: Filter by specific regions
- `include_terminal_details`: Include detailed terminal information
- `time_period`: Specify time range for trends (1h, 6h, 24h, 7d, 30d)

## 🔧 Features

### Database Integration
- **PostgreSQL Connection**: Async connection pooling with asyncpg
- **Multiple Data Sources**: Legacy and new table support
- **Connection Health**: Automatic health monitoring
- **Error Handling**: Comprehensive database error management

### API Features
- **FastAPI Framework**: Modern, high-performance Python web framework
- **Automatic Documentation**: Interactive Swagger UI and ReDoc
- **Type Safety**: Pydantic models for request/response validation
- **CORS Support**: Cross-origin requests enabled
- **Async Support**: Non-blocking database operations
- **Logging**: Comprehensive logging to file and console

### Health Status Classification
- **HEALTHY**: ≥85% availability
- **ATTENTION**: 70-84% availability  
- **WARNING**: 50-69% availability
- **CRITICAL**: <50% availability

## 📋 ATM Status Types
- **AVAILABLE**: Fully operational ATMs
- **WARNING**: ATMs with minor issues
- **ZOMBIE**: Non-responsive ATMs
- **WOUNDED**: ATMs with significant issues
- **OUT_OF_SERVICE**: Completely offline ATMs

## 🧪 Testing Examples

### Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### ATM Summary
```bash
curl -X GET "http://localhost:8000/api/v1/atm/status/summary"
```

### Regional Data
```bash
curl -X GET "http://localhost:8000/api/v1/atm/status/regional"
```

### Latest Data with Terminal Details
```bash
curl -X GET "http://localhost:8000/api/v1/atm/status/latest?include_terminal_details=true"
```

## 🔗 Integration with User Management API

Both APIs are running simultaneously:
- **ATM Dashboard API**: Port 8000 (ATM monitoring data)
- **User Management API**: Port 8001 (Authentication & user management)

### Potential Integration Points
1. **Authentication**: Use User Management API JWT tokens for ATM Dashboard access
2. **Role-based Access**: Different ATM data views based on user roles
3. **Audit Logging**: Track ATM data access through User Management audit system
4. **User Sessions**: Correlate ATM dashboard usage with user sessions

## 📈 Current Data Summary
From latest test:
- **Total ATMs**: 14
- **Available**: 7 (50%)
- **Warning**: 2 (14.3%)
- **Wounded**: 5 (35.7%)
- **Overall Availability**: 64.29%
- **Health Status**: WARNING
- **Region**: TL-DL

## 🛠️ Technical Details
- **Framework**: FastAPI 0.115.12
- **Server**: Uvicorn with auto-reload
- **Database**: PostgreSQL (asyncpg driver)
- **Environment**: .env configuration
- **Python Version**: Python 3.x
- **Architecture**: Async/await pattern

## 📝 Recent Updates
- ✅ Fixed deprecated `datetime.utcnow()` usage
- ✅ Updated to modern FastAPI lifespan management
- ✅ Established database connection pooling
- ✅ Verified all endpoints functionality
- ✅ Confirmed data retrieval from PostgreSQL

The ATM Dashboard FastAPI application is fully operational and ready for production use!
