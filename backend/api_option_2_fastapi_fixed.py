#!/usr/bin/env python3
"""
FastAPI REST API for ATM Status Counts - Option 2 (Fixed)

A modern, high-performance REST API with automatic OpenAPI documentation
for fetching ATM status counts with type safety and validation.

Features:
- Automatic OpenAPI/Swagger documentation
- Type hints and Pydantic models for validation
- High performance with async support
- Built-in data validation
- Interactive API documentation at /docs
- Alternative ReDoc documentation at /redoc
- Comprehensive error handling
- CORS support

Endpoints:
- GET /api/v1/atm/status/summary - Overall ATM status summary
- GET /api/v1/atm/status/regional - Regional breakdown with filters
- GET /api/v1/atm/status/trends/{region_code} - Regional trends
- GET /api/v1/atm/status/latest - Latest data with optional table selection
- GET /api/v1/atm/{terminal_id}/history - Individual ATM historical status data
- GET /api/v1/atm/list - List of ATMs available for historical analysis
- GET /api/v1/health - API health check
- GET /docs - Interactive API documentation
- GET /redoc - Alternative documentation

Installation:
pip install fastapi uvicorn asyncpg python-dotenv

Usage:
uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --reload

Author: ATM Monitoring System  
Created: 2025-01-30
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import asyncio
import asyncpg
from contextlib import asynccontextmanager
import pytz

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Load environment variables
from dotenv import load_dotenv

# Load environment variables from .env file or .env_fastapi.example
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('.env_fastapi.example'):
    load_dotenv('.env_fastapi.example')

# Configure logging
log_file = os.getenv('LOG_FILE', '/var/log/dash-atm/api.log')
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

# Create log directory if it doesn't exist
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir, exist_ok=True)
    except PermissionError:
        # Fallback to current directory if we can't create the log directory
        log_file = 'atm_fastapi.log'

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ATM_FastAPI')

# Notification service import
try:
    from notification_service import NotificationService
except ImportError as e:
    logger.warning(f"Could not import notification service: {e}")
    NotificationService = None

# Database configuration using the updated credentials for development_db
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '88.222.214.26'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'development_db'),
    'user': os.getenv('DB_USER', 'timlesdev'),
    'password': os.getenv('DB_PASSWORD', 'timlesdev')
}

# Timezone configuration
DILI_TZ = pytz.timezone('Asia/Dili')  # UTC+9
UTC_TZ = pytz.UTC

def convert_to_dili_time(utc_timestamp: datetime) -> datetime:
    """
    Convert a UTC timestamp to Dili local time (UTC+9).
    
    Args:
        utc_timestamp: A datetime object in UTC (timezone-aware or naive)
    
    Returns:
        datetime: Timestamp converted to Dili local time
    """
    try:
        # If the timestamp is timezone-naive, assume it's UTC
        if utc_timestamp.tzinfo is None:
            utc_timestamp = UTC_TZ.localize(utc_timestamp)
        
        # Convert to Dili time
        dili_timestamp = utc_timestamp.astimezone(DILI_TZ)
        
        # Return as timezone-naive datetime for JSON serialization
        return dili_timestamp.replace(tzinfo=None)
        
    except Exception as e:
        logger.warning(f"Error converting timestamp to Dili time: {e}")
        # Fallback: return original timestamp
        return utc_timestamp.replace(tzinfo=None) if utc_timestamp.tzinfo else utc_timestamp

# Pydantic Models for Data Validation
class ATMStatusEnum(str, Enum):
    AVAILABLE = "AVAILABLE"
    WARNING = "WARNING"
    ZOMBIE = "ZOMBIE"
    WOUNDED = "WOUNDED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

class TableTypeEnum(str, Enum):
    LEGACY = "legacy"
    NEW = "new"
    BOTH = "both"

class HealthStatusEnum(str, Enum):
    HEALTHY = "HEALTHY"
    ATTENTION = "ATTENTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

# New models for individual ATM historical data
class ATMStatusPoint(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of the status reading")
    status: ATMStatusEnum = Field(..., description="ATM status at this time")
    location: Optional[str] = Field(None, description="ATM location")
    fault_description: Optional[str] = Field(None, description="Fault description if any")
    serial_number: Optional[str] = Field(None, description="ATM serial number")

class ATMHistoricalData(BaseModel):
    terminal_id: str = Field(..., description="Terminal identifier")
    terminal_name: Optional[str] = Field(None, description="Terminal name")
    location: Optional[str] = Field(None, description="Current location")
    serial_number: Optional[str] = Field(None, description="Serial number")
    historical_points: List[ATMStatusPoint] = Field(..., description="Historical status points")
    time_period: str = Field(..., description="Time period covered")
    summary_stats: Dict[str, Any] = Field(..., description="Summary statistics")

class ATMHistoricalResponse(BaseModel):
    atm_data: ATMHistoricalData
    chart_config: Dict[str, Any] = Field(..., description="Configuration for chart display")

class ATMStatusCounts(BaseModel):
    available: int = Field(..., ge=0, description="Number of available ATMs")
    warning: int = Field(..., ge=0, description="Number of ATMs with warnings")
    zombie: int = Field(..., ge=0, description="Number of zombie ATMs")
    wounded: int = Field(..., ge=0, description="Number of wounded ATMs")
    out_of_service: int = Field(..., ge=0, description="Number of out-of-service ATMs")
    total: int = Field(..., ge=0, description="Total number of ATMs")

class RegionalData(BaseModel):
    region_code: str = Field(..., description="Region identifier")
    status_counts: ATMStatusCounts
    availability_percentage: float = Field(..., ge=0, le=100, description="Availability percentage (AVAILABLE + WARNING)")
    last_updated: datetime = Field(..., description="Last update timestamp")
    health_status: HealthStatusEnum = Field(..., description="Overall health classification")

class ATMSummaryResponse(BaseModel):
    total_atms: int = Field(..., ge=0, description="Total ATMs across all regions")
    status_counts: ATMStatusCounts
    overall_availability: float = Field(..., ge=0, le=100, description="Overall availability percentage (AVAILABLE + WARNING)")
    total_regions: int = Field(..., ge=0, description="Number of regions")
    last_updated: datetime = Field(..., description="Last update timestamp")
    data_source: str = Field(..., description="Data source identifier")

class RegionalResponse(BaseModel):
    regional_data: List[RegionalData]
    total_regions: int = Field(..., ge=0)
    summary: ATMStatusCounts
    last_updated: datetime

class TrendPoint(BaseModel):
    timestamp: datetime
    status_counts: ATMStatusCounts
    availability_percentage: float = Field(..., ge=0, le=100, description="Availability percentage (AVAILABLE + WARNING)")

class TrendResponse(BaseModel):
    region_code: str
    time_period: str
    trends: List[TrendPoint]
    summary_stats: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    database_connected: bool
    api_version: str = "2.0.0"
    uptime_seconds: float

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ATM FastAPI application...")
    await create_db_pool()
    
    # Start background notification checker
    background_task = None
    if NotificationService is not None:
        async def notification_checker():
            """Background task to check for ATM status changes"""
            while True:
                try:
                    service = await get_notification_service()
                    changes = await service.check_status_changes()
                    if changes:
                        logger.info(f"Background check found {len(changes)} status changes")
                except Exception as e:
                    logger.error(f"Error in background notification checker: {e}")
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
        
        background_task = asyncio.create_task(notification_checker())
        logger.info("Background notification checker started (5-minute interval)")
    
    yield
    
    # Shutdown
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background notification checker stopped")
    
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

# FastAPI app initialization
app = FastAPI(
    title="ATM Status Monitoring API",
    description="FastAPI-based REST API for ATM status counts and monitoring",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# CORS middleware - Production-ready configuration
cors_origins = os.getenv('CORS_ORIGINS', '["http://localhost:3000"]')
if isinstance(cors_origins, str):
    import json
    try:
        cors_origins = json.loads(cors_origins)
    except json.JSONDecodeError:
        cors_origins = ["http://localhost:3000"]

cors_methods = os.getenv('CORS_ALLOW_METHODS', '["GET", "POST", "PUT", "DELETE", "OPTIONS"]')
if isinstance(cors_methods, str):
    try:
        cors_methods = json.loads(cors_methods)
    except json.JSONDecodeError:
        cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=bool(os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'),
    allow_methods=cors_methods,
    allow_headers=["*"],
)

# Global variables
app_start_time = datetime.now()
db_pool = None

# Database connection functions
async def create_db_pool():
    """Create database connection pool"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            min_size=2,
            max_size=10,
            command_timeout=30
        )
        logger.info("Database connection pool created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        return False

async def get_db_connection() -> Optional[asyncpg.Connection]:
    """Get database connection from pool"""
    global db_pool
    if not db_pool:
        await create_db_pool()
    
    if db_pool:
        try:
            return await db_pool.acquire()
        except Exception as e:
            logger.error(f"Failed to acquire database connection: {e}")
            return None
    return None

async def release_db_connection(conn: Optional[asyncpg.Connection]):
    """Release database connection back to pool"""
    global db_pool
    if db_pool and conn:
        try:
            await db_pool.release(conn)
        except Exception as e:
            logger.error(f"Failed to release database connection: {e}")

# Utility functions
def calculate_health_status(availability_percentage: float) -> HealthStatusEnum:
    """Calculate health status based on availability percentage"""
    if availability_percentage >= 85:
        return HealthStatusEnum.HEALTHY
    elif availability_percentage >= 70:
        return HealthStatusEnum.ATTENTION
    elif availability_percentage >= 50:
        return HealthStatusEnum.WARNING
    else:
        return HealthStatusEnum.CRITICAL

# Dependency functions
async def validate_db_connection():
    """Dependency to validate database connection"""
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Test connection
        await conn.fetchval("SELECT 1")
        await release_db_connection(conn)
        return True
    except Exception as e:
        await release_db_connection(conn)
        logger.error(f"Database connection test failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection test failed")

# API Endpoints

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    API health check endpoint
    
    Returns the current status of the API and database connectivity.
    """
    try:
        # Test database connection
        conn = await get_db_connection()
        db_connected = False
        
        if conn:
            try:
                await conn.fetchval("SELECT 1")
                db_connected = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
            finally:
                await release_db_connection(conn)
        
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        return HealthResponse(
            database_connected=db_connected,
            uptime_seconds=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/api/v1/atm/status/summary", response_model=ATMSummaryResponse, tags=["ATM Status"])
async def get_atm_summary(
    table_type: TableTypeEnum = Query(TableTypeEnum.LEGACY, description="Database table to query"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get overall ATM status summary across all regions
    
    Returns aggregated counts and percentages for all ATM statuses.
    Availability includes both AVAILABLE and WARNING ATMs as they are operational.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        if table_type == TableTypeEnum.LEGACY or table_type == TableTypeEnum.BOTH:
            # Query legacy table (using regional_data with legacy approach)
            query = """
                WITH latest_data AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, retrieval_timestamp
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    SUM(COALESCE(count_available, 0)) as total_available,
                    SUM(COALESCE(count_warning, 0)) as total_warning,
                    SUM(COALESCE(count_zombie, 0)) as total_zombie,
                    SUM(COALESCE(count_wounded, 0)) as total_wounded,
                    SUM(COALESCE(count_out_of_service, 0)) as total_out_of_service,
                    COUNT(DISTINCT region_code) as total_regions,
                    MAX(retrieval_timestamp) as last_updated
                FROM latest_data
            """
            
            row = await conn.fetchrow(query)
            
        elif table_type == TableTypeEnum.NEW:
            # Query new table (regional_data) - use actual columns, not JSONB parsing
            query = """
                WITH latest_data AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        retrieval_timestamp
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    SUM(COALESCE(count_available, 0)) as total_available,
                    SUM(COALESCE(count_warning, 0)) as total_warning,
                    SUM(COALESCE(count_zombie, 0)) as total_zombie,
                    SUM(COALESCE(count_wounded, 0)) as total_wounded,
                    SUM(COALESCE(count_out_of_service, 0)) as total_out_of_service,
                    COUNT(DISTINCT region_code) as total_regions,
                    MAX(retrieval_timestamp) as last_updated
                FROM latest_data
            """
            
            row = await conn.fetchrow(query)
        
        if not row:
            raise HTTPException(status_code=404, detail="No ATM data found")
        
        # Calculate totals
        available = row['total_available'] or 0
        warning = row['total_warning'] or 0
        zombie = row['total_zombie'] or 0
        wounded = row['total_wounded'] or 0
        out_of_service = row['total_out_of_service'] or 0
        total_atms = available + warning + zombie + wounded + out_of_service
        
        # Calculate availability including both AVAILABLE and WARNING ATMs
        operational_atms = available + warning
        availability_percentage = (operational_atms / total_atms * 100) if total_atms > 0 else 0
        
        status_counts = ATMStatusCounts(
            available=available,
            warning=warning,
            zombie=zombie,
            wounded=wounded,
            out_of_service=out_of_service,
            total=total_atms
        )
        
        return ATMSummaryResponse(
            total_atms=total_atms,
            status_counts=status_counts,
            overall_availability=round(availability_percentage, 2),
            total_regions=row['total_regions'] or 0,
            last_updated=convert_to_dili_time(row['last_updated']) if row['last_updated'] else convert_to_dili_time(datetime.utcnow()),
            data_source=table_type.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ATM summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ATM summary data")
    finally:
        await release_db_connection(conn)

@app.get("/api/v1/atm/status/regional", response_model=RegionalResponse, tags=["ATM Status"])
async def get_regional_data(
    region_code: Optional[str] = Query(None, description="Filter by specific region code"),
    table_type: TableTypeEnum = Query(TableTypeEnum.LEGACY, description="Database table to query"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get regional breakdown of ATM status counts
    
    Returns detailed breakdown by region with health status classification.
    Availability includes both AVAILABLE and WARNING ATMs as they are operational.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Build query based on table type
        if table_type == TableTypeEnum.LEGACY:
            base_query = """
                WITH latest_regional AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region, retrieval_timestamp
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    region_code, count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service, total_atms_in_region,
                    retrieval_timestamp as date_creation
                FROM latest_regional
            """
        else:
            # Query new table (regional_data)
            base_query = """
                WITH latest_regional AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region, 
                        retrieval_timestamp
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    region_code, count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service, total_atms_in_region,
                    retrieval_timestamp as date_creation
                FROM latest_regional
            """
        
        # Add region filter if specified
        if region_code:
            base_query += f" WHERE region_code = $1"
            rows = await conn.fetch(base_query, region_code)
        else:
            base_query += " ORDER BY region_code"
            rows = await conn.fetch(base_query)
        
        if not rows:
            raise HTTPException(status_code=404, detail="No regional data found")
        
        regional_data = []
        total_summary = {
            'available': 0, 'warning': 0, 'zombie': 0, 
            'wounded': 0, 'out_of_service': 0, 'total': 0
        }
        last_updated = None
        
        for row in rows:
            available = row['count_available'] or 0
            warning = row['count_warning'] or 0
            zombie = row['count_zombie'] or 0
            wounded = row['count_wounded'] or 0
            out_of_service = row['count_out_of_service'] or 0
            total_region = available + warning + zombie + wounded + out_of_service
            
            # Calculate availability including both AVAILABLE and WARNING ATMs
            operational_atms = available + warning
            availability_pct = (operational_atms / total_region * 100) if total_region > 0 else 0
            
            status_counts = ATMStatusCounts(
                available=available,
                warning=warning,
                zombie=zombie,
                wounded=wounded,
                out_of_service=out_of_service,
                total=total_region
            )
            
            # Update summary totals
            total_summary['available'] += available
            total_summary['warning'] += warning
            total_summary['zombie'] += zombie
            total_summary['wounded'] += wounded
            total_summary['out_of_service'] += out_of_service
            total_summary['total'] += total_region
            
            if not last_updated or row['date_creation'] > last_updated:
                last_updated = row['date_creation']
            
            regional_data.append(RegionalData(
                region_code=row['region_code'],
                status_counts=status_counts,
                availability_percentage=round(availability_pct, 2),
                last_updated=convert_to_dili_time(row['date_creation']) if row['date_creation'] else convert_to_dili_time(datetime.utcnow()),
                health_status=calculate_health_status(availability_pct)
            ))
        
        summary_counts = ATMStatusCounts(
            available=total_summary['available'],
            warning=total_summary['warning'],
            zombie=total_summary['zombie'],
            wounded=total_summary['wounded'],
            out_of_service=total_summary['out_of_service'],
            total=total_summary['total']
        )
        
        return RegionalResponse(
            regional_data=regional_data,
            total_regions=len(rows),
            summary=summary_counts,
            last_updated=convert_to_dili_time(last_updated) if last_updated else convert_to_dili_time(datetime.utcnow())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching regional data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch regional data")
    finally:
        await release_db_connection(conn)

@app.get("/api/v1/atm/status/trends/{region_code}", response_model=TrendResponse, tags=["ATM Status"])
async def get_regional_trends(
    region_code: str = Path(..., description="Region code to get trends for"),
    hours: int = Query(24, ge=1, le=720, description="Number of hours to look back (1-720)"),
    table_type: TableTypeEnum = Query(TableTypeEnum.LEGACY, description="Database table to query"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get historical trends for a specific region
    
    Returns time-series data showing ATM status changes over time.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        if table_type == TableTypeEnum.LEGACY:
            query = """
                SELECT 
                    retrieval_timestamp as date_creation, count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service
                FROM regional_data
                WHERE region_code = $1 
                    AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY retrieval_timestamp ASC
            """ % hours
        else:
            # Query new table (regional_data)
            query = """
                SELECT 
                    retrieval_timestamp as date_creation, 
                    count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service
                FROM regional_data
                WHERE region_code = $1 
                    AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY retrieval_timestamp ASC
            """ % hours
        
        rows = await conn.fetch(query, region_code)
        
        # Enhanced fallback logic: if no data found for requested period, try shorter periods
        actual_hours_used = hours
        fallback_message = None
        
        if not rows:
            # Define fallback periods to try in descending order
            fallback_periods = [168, 72, 24, 12, 6, 1]  # 7 days, 3 days, 1 day, 12h, 6h, 1h
            fallback_periods = [period for period in fallback_periods if period < hours]
            
            logger.info(f"No data found for {hours}h period, trying fallback periods: {fallback_periods}")
            
            for fallback_hours in fallback_periods:
                if table_type == TableTypeEnum.LEGACY:
                    fallback_query = """
                        SELECT 
                            retrieval_timestamp as date_creation, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service
                        FROM regional_data
                        WHERE region_code = $1 
                            AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                        ORDER BY retrieval_timestamp ASC
                    """ % fallback_hours
                else:
                    fallback_query = """
                        SELECT 
                            retrieval_timestamp as date_creation, 
                            count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service
                        FROM regional_data
                        WHERE region_code = $1 
                            AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                        ORDER BY retrieval_timestamp ASC
                    """ % fallback_hours
                
                rows = await conn.fetch(fallback_query, region_code)
                if rows:
                    actual_hours_used = fallback_hours
                    fallback_message = f"Requested {hours}h data unavailable, showing available {fallback_hours}h data instead"
                    logger.info(f"Found {len(rows)} data points for {fallback_hours}h fallback period")
                    break
            
            # If still no data found, raise 404
            if not rows:
                raise HTTPException(status_code=404, detail=f"No trend data found for region {region_code} in any time period")
        
        trends = []
        availability_values = []
        
        for row in rows:
            available = row['count_available'] or 0
            warning = row['count_warning'] or 0
            zombie = row['count_zombie'] or 0
            wounded = row['count_wounded'] or 0
            out_of_service = row['count_out_of_service'] or 0
            total = available + warning + zombie + wounded + out_of_service
            
            # Calculate availability including both AVAILABLE and WARNING ATMs
            operational_atms = available + warning
            availability_pct = (operational_atms / total * 100) if total > 0 else 0
            availability_values.append(availability_pct)
            
            status_counts = ATMStatusCounts(
                available=available,
                warning=warning,
                zombie=zombie,
                wounded=wounded,
                out_of_service=out_of_service,
                total=total
            )
            
            trends.append(TrendPoint(
                timestamp=convert_to_dili_time(row['date_creation']),
                status_counts=status_counts,
                availability_percentage=round(availability_pct, 2)
            ))
        
        # Calculate summary statistics
        summary_stats = {
            'data_points': len(trends),
            'time_range_hours': actual_hours_used,
            'requested_hours': hours,
            'avg_availability': round(sum(availability_values) / len(availability_values), 2) if availability_values else 0,
            'min_availability': round(min(availability_values), 2) if availability_values else 0,
            'max_availability': round(max(availability_values), 2) if availability_values else 0,
            'first_reading': trends[0].timestamp.isoformat() if trends else None,
            'last_reading': trends[-1].timestamp.isoformat() if trends else None
        }
        
        # Add fallback message if applicable
        if fallback_message:
            summary_stats['fallback_message'] = fallback_message
        
        return TrendResponse(
            region_code=region_code,
            time_period=f"{actual_hours_used} hours" + (f" (requested {hours}h)" if actual_hours_used != hours else ""),
            trends=trends,
            summary_stats=summary_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trends for region {region_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trend data")
    finally:
        await release_db_connection(conn)

@app.get("/api/v1/atm/status/latest", tags=["ATM Status"])
async def get_latest_data(
    table_type: TableTypeEnum = Query(TableTypeEnum.BOTH, description="Database table to query"),
    include_terminal_details: bool = Query(False, description="Include terminal details data"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get latest data from all available tables
    
    Returns the most recent data from specified database tables.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        result: Dict[str, Any] = {"data_sources": []}
        
        # Legacy table data
        if table_type in [TableTypeEnum.LEGACY, TableTypeEnum.BOTH]:
            try:
                legacy_query = """
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, retrieval_timestamp
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                """
                legacy_rows = await conn.fetch(legacy_query)
                
                legacy_data = []
                for row in legacy_rows:
                    legacy_data.append({
                        'region_name': row['region_code'],
                        'count_available': row['count_available'],
                        'count_warning': row['count_warning'],
                        'count_zombie': row['count_zombie'],
                        'count_wounded': row['count_wounded'],
                        'count_out_of_service': row['count_out_of_service'],
                        'last_updated': convert_to_dili_time(row['retrieval_timestamp']).isoformat() if row['retrieval_timestamp'] else None
                    })
                
                result["data_sources"].append({
                    "table": "regional_data",
                    "type": "legacy",
                    "records": len(legacy_data),
                    "data": legacy_data
                })
                
            except Exception as e:
                logger.warning(f"Failed to fetch legacy table data: {e}")
        
        # New table data
        if table_type in [TableTypeEnum.NEW, TableTypeEnum.BOTH]:
            try:
                new_query = """
                    SELECT DISTINCT ON (region_code)
                        region_code, raw_regional_data, retrieval_timestamp
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                """
                new_rows = await conn.fetch(new_query)
                
                new_data = []
                for row in new_rows:
                    new_data.append({
                        'region_code': row['region_code'],
                        'raw_regional_data': row['raw_regional_data'],
                        'last_updated': convert_to_dili_time(row['retrieval_timestamp']).isoformat() if row['retrieval_timestamp'] else None
                    })
                
                result["data_sources"].append({
                    "table": "regional_data",
                    "type": "new_jsonb",
                    "records": len(new_data),
                    "data": new_data
                })
                
            except Exception as e:
                logger.warning(f"Failed to fetch new table data: {e}")
        
        # Terminal details if requested
        if include_terminal_details:
            try:
                terminal_query = """
                    SELECT DISTINCT ON (terminal_id)
                        terminal_id, location, issue_state_name, serial_number,
                        fetched_status, retrieved_date, fault_data, metadata
                    FROM terminal_details
                    WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
                    ORDER BY terminal_id, retrieved_date DESC
                """
                terminal_rows = await conn.fetch(terminal_query)
                
                terminal_data = []
                for row in terminal_rows:
                    terminal_data.append({
                        'terminal_id': row['terminal_id'],
                        'location': row['location'],
                        'issue_state_name': row['issue_state_name'],
                        'serial_number': row['serial_number'],
                        'fetched_status': row['fetched_status'],
                        'retrieved_date': convert_to_dili_time(row['retrieved_date']).isoformat() if row['retrieved_date'] else None,
                        'fault_data': row['fault_data'],
                        'metadata': row['metadata']
                    })
                
                result["data_sources"].append({
                    "table": "terminal_details",
                    "type": "terminal_data",
                    "records": len(terminal_data),
                    "data": terminal_data
                })
                
            except Exception as e:
                logger.warning(f"Failed to fetch terminal details: {e}")
        
        if not result["data_sources"]:
            raise HTTPException(status_code=404, detail="No data found in any table")
        
        result["summary"] = {
            "total_tables_queried": len(result["data_sources"]),
            "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat(),
            "table_type_requested": table_type.value
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest data")
    finally:
        await release_db_connection(conn)

@app.get("/api/v1/atm/{terminal_id}/history", response_model=ATMHistoricalResponse, tags=["ATM Historical"])
async def get_atm_history(
    terminal_id: str = Path(..., description="Terminal ID to get history for"),
    hours: int = Query(168, ge=1, le=2160, description="Number of hours to look back (1-2160, default 168=7 days)"),
    include_fault_details: bool = Query(True, description="Include fault descriptions in history"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get historical status data for a specific ATM terminal
    
    This endpoint provides time-series data for individual ATM status changes,
    perfect for creating line charts showing ATM availability history.
    
    Returns:
    - Chronological status points with timestamps
    - Status transitions (AVAILABLE -> WARNING -> WOUNDED, etc.)
    - Fault descriptions when status changes occur
    - Chart configuration for frontend display
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Query terminal_details table for historical data of specific terminal
        query = """
            SELECT 
                terminal_id,
                location,
                issue_state_name,
                serial_number,
                retrieved_date,
                fetched_status,
                fault_data,
                raw_terminal_data
            FROM terminal_details
            WHERE terminal_id = $1 
                AND retrieved_date >= NOW() - INTERVAL '%s hours'
            ORDER BY retrieved_date ASC
        """ % hours
        
        rows = await conn.fetch(query, terminal_id)
        
        # Enhanced fallback logic for individual ATM
        actual_hours_used = hours
        fallback_message = None
        
        if not rows:
            # Try progressively shorter periods for this specific ATM
            fallback_periods = [720, 168, 72, 24, 12, 6, 1]  # 30 days, 7 days, 3 days, 1 day, 12h, 6h, 1h
            fallback_periods = [period for period in fallback_periods if period < hours]
            
            logger.info(f"No data found for ATM {terminal_id} in {hours}h period, trying fallback periods: {fallback_periods}")
            
            for fallback_hours in fallback_periods:
                fallback_query = """
                    SELECT 
                        terminal_id,
                        location,
                        issue_state_name,
                        serial_number,
                        retrieved_date,
                        fetched_status,
                        fault_data,
                        raw_terminal_data
                    FROM terminal_details
                    WHERE terminal_id = $1 
                        AND retrieved_date >= NOW() - INTERVAL '%s hours'
                    ORDER BY retrieved_date ASC
                """ % fallback_hours
                
                rows = await conn.fetch(fallback_query, terminal_id)
                if rows:
                    actual_hours_used = fallback_hours
                    fallback_message = f"Requested {hours}h data unavailable, showing available {fallback_hours}h data instead"
                    logger.info(f"Found {len(rows)} data points for ATM {terminal_id} in {fallback_hours}h period")
                    break
            
            # If still no data found, raise 404
            if not rows:
                raise HTTPException(status_code=404, detail=f"No historical data found for ATM {terminal_id} in any time period")
        
        # Process the historical data
        historical_points = []
        status_distribution = {}
        terminal_info = None
        
        for row in rows:
            # Extract fault description if available and requested
            fault_description = None
            if include_fault_details and row['fault_data']:
                try:
                    fault_data = row['fault_data']
                    if isinstance(fault_data, dict):
                        fault_description = fault_data.get('agentErrorDescription')
                except Exception as e:
                    logger.warning(f"Could not parse fault data for ATM {terminal_id}: {e}")
            
            # Map status to enum
            status_value = row['fetched_status'] or row['issue_state_name'] or 'UNKNOWN'
            
            # Handle status mapping
            if status_value == 'HARD':
                status_value = 'WOUNDED'
            elif status_value == 'CASH':
                status_value = 'OUT_OF_SERVICE'
            elif status_value == 'UNAVAILABLE':
                status_value = 'OUT_OF_SERVICE'
            
            # Ensure status is valid
            try:
                status_enum = ATMStatusEnum(status_value)
            except ValueError:
                logger.warning(f"Unknown status '{status_value}' for ATM {terminal_id}, defaulting to OUT_OF_SERVICE")
                status_enum = ATMStatusEnum.OUT_OF_SERVICE
            
            # Count status distribution
            status_distribution[status_enum.value] = status_distribution.get(status_enum.value, 0) + 1
            
            # Create status point
            status_point = ATMStatusPoint(
                timestamp=convert_to_dili_time(row['retrieved_date']),
                status=status_enum,
                location=row['location'],
                fault_description=fault_description,
                serial_number=row['serial_number']
            )
            historical_points.append(status_point)
            
            # Store terminal info from latest record
            if terminal_info is None:
                terminal_info = {
                    'location': row['location'],
                    'serial_number': row['serial_number']
                }
        
        # Calculate summary statistics
        total_points = len(historical_points)
        status_percentages = {
            status: (count / total_points * 100) if total_points > 0 else 0
            for status, count in status_distribution.items()
        }
        
        # Calculate uptime (AVAILABLE + WARNING as operational)
        operational_count = status_distribution.get('AVAILABLE', 0) + status_distribution.get('WARNING', 0)
        uptime_percentage = (operational_count / total_points * 100) if total_points > 0 else 0
        
        summary_stats = {
            'data_points': total_points,
            'time_range_hours': actual_hours_used,
            'requested_hours': hours,
            'status_distribution': status_distribution,
            'status_percentages': status_percentages,
            'uptime_percentage': round(uptime_percentage, 2),
            'first_reading': historical_points[0].timestamp.isoformat() if historical_points else None,
            'last_reading': historical_points[-1].timestamp.isoformat() if historical_points else None,
            'status_changes': len(set(point.status.value for point in historical_points)),
            'has_fault_data': any(point.fault_description for point in historical_points)
        }
        
        # Add fallback message if applicable
        if fallback_message:
            summary_stats['fallback_message'] = fallback_message
        
        # Create ATM historical data
        atm_historical_data = ATMHistoricalData(
            terminal_id=terminal_id,
            terminal_name=None,  # We don't have terminal name in the database, so set to None
            location=terminal_info['location'] if terminal_info else None,
            serial_number=terminal_info['serial_number'] if terminal_info else None,
            historical_points=historical_points,
            time_period=f"{actual_hours_used} hours" + (f" (requested {hours}h)" if actual_hours_used != hours else ""),
            summary_stats=summary_stats
        )
        
        # Chart configuration for frontend
        chart_config = {
            'chart_type': 'line_chart',
            'x_axis': {
                'field': 'timestamp',
                'label': 'Date & Time',
                'format': 'datetime'
            },
            'y_axis': {
                'field': 'status',
                'label': 'ATM Status',
                'categories': ['AVAILABLE', 'WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE'],
                'colors': {
                    'AVAILABLE': '#28a745',      # Green
                    'WARNING': '#ffc107',        # Yellow  
                    'WOUNDED': '#fd7e14',        # Orange
                    'ZOMBIE': '#6f42c1',         # Purple
                    'OUT_OF_SERVICE': '#dc3545'  # Red
                }
            },
            'tooltip': {
                'include_fields': ['timestamp', 'status', 'fault_description'],
                'timestamp_format': 'MMM DD, YYYY HH:mm'
            },
            'legend': {
                'show': True,
                'position': 'bottom'
            }
        }
        
        return ATMHistoricalResponse(
            atm_data=atm_historical_data,
            chart_config=chart_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history for ATM {terminal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ATM historical data")
    finally:
        await release_db_connection(conn)

@app.get("/api/v1/atm/list", tags=["ATM Historical"])
async def get_atm_list(
    region_code: Optional[str] = Query(None, description="Filter by region code"),
    status_filter: Optional[ATMStatusEnum] = Query(None, description="Filter by current status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of ATMs to return"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get list of available ATMs for historical analysis
    
    Returns a list of ATMs that have historical data available,
    useful for populating dropdown menus or selection lists.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Build query to get latest status for each ATM
        base_query = """
            WITH latest_atm_data AS (
                SELECT DISTINCT ON (terminal_id)
                    terminal_id,
                    location,
                    issue_state_name,
                    serial_number,
                    retrieved_date,
                    fetched_status
                FROM terminal_details
                ORDER BY terminal_id, retrieved_date DESC
            )
            SELECT 
                terminal_id,
                location,
                issue_state_name,
                serial_number,
                retrieved_date,
                fetched_status
            FROM latest_atm_data
        """
        
        # Add filters
        conditions = []
        params = []
        
        if region_code:
            # For simplicity, we'll check if location contains region info
            conditions.append("location ILIKE $" + str(len(params) + 1))
            params.append(f"%{region_code}%")
        
        if status_filter:
            # Handle status mapping
            if status_filter == ATMStatusEnum.WOUNDED:
                conditions.append("(fetched_status = $" + str(len(params) + 1) + " OR issue_state_name = 'HARD')")
                params.append('WOUNDED')
            elif status_filter == ATMStatusEnum.OUT_OF_SERVICE:
                conditions.append("(fetched_status IN ($" + str(len(params) + 1) + ", $" + str(len(params) + 2) + ") OR issue_state_name IN ('CASH', 'UNAVAILABLE'))")
                params.extend(['OUT_OF_SERVICE', 'UNAVAILABLE'])
            else:
                conditions.append("(fetched_status = $" + str(len(params) + 1) + " OR issue_state_name = $" + str(len(params) + 2) + ")")
                params.extend([status_filter.value, status_filter.value])
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += f" ORDER BY terminal_id LIMIT {limit}"
        
        rows = await conn.fetch(base_query, *params)
        
        atm_list = []
        for row in rows:
            # Map status
            status_value = row['fetched_status'] or row['issue_state_name'] or 'UNKNOWN'
            if status_value == 'HARD':
                status_value = 'WOUNDED'
            elif status_value in ['CASH', 'UNAVAILABLE']:
                status_value = 'OUT_OF_SERVICE'
                
            atm_list.append({
                'terminal_id': row['terminal_id'],
                'location': row['location'],
                'current_status': status_value,
                'serial_number': row['serial_number'],
                'last_updated': convert_to_dili_time(row['retrieved_date']).isoformat() if row['retrieved_date'] else None
            })
        
        return {
            'atms': atm_list,
            'total_count': len(atm_list),
            'filters_applied': {
                'region_code': region_code,
                'status_filter': status_filter.value if status_filter else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ATM list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ATM list")
    finally:
        await release_db_connection(conn)

# ========================
# NOTIFICATION ENDPOINTS
# ========================

# Pydantic models for notifications
class NotificationResponse(BaseModel):
    notification_id: str = Field(..., description="Unique notification identifier")
    terminal_id: str = Field(..., description="ATM terminal ID")
    previous_status: Optional[str] = Field(None, description="Previous ATM status")
    current_status: str = Field(..., description="Current ATM status")
    severity: str = Field(..., description="Notification severity level")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    created_at: datetime = Field(..., description="When notification was created")
    is_read: bool = Field(..., description="Whether notification has been read")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total_count: int = Field(..., ge=0, description="Total number of notifications")
    unread_count: int = Field(..., ge=0, description="Number of unread notifications")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    has_more: bool = Field(..., description="Whether there are more notifications")

# Initialize notification service
notification_service = None

async def get_notification_service():
    """Get or create notification service instance"""
    global notification_service
    if NotificationService is None:
        raise HTTPException(status_code=503, detail="Notification service not available")
    if notification_service is None:
        notification_service = NotificationService()
        await notification_service.init_db_pool()
    return notification_service

@app.get("/api/v1/notifications", response_model=NotificationListResponse, tags=["Notifications"])
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Get only unread notifications"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get paginated list of notifications for ATM status changes
    
    Returns notifications sorted by creation time (newest first).
    Supports filtering by read status.
    """
    try:
        if NotificationService is None:
            raise HTTPException(status_code=503, detail="Notification service not available")
            
        service = await get_notification_service()
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        # Get notifications with pagination
        notifications, total_count = await service.get_notifications(
            unread_only=unread_only,
            limit=per_page,
            offset=offset
        )
        
        # Convert to response format
        notification_responses = []
        for notif in notifications:
            # Parse metadata if it's a string
            metadata = notif.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            notification_responses.append(NotificationResponse(
                notification_id=notif['id'],
                terminal_id=notif['terminal_id'],
                previous_status=notif.get('previous_status'),
                current_status=notif['current_status'],
                severity=notif['severity'],
                title=notif['title'],
                message=notif['message'],
                created_at=datetime.fromisoformat(notif['created_at'].replace('Z', '+00:00')),
                is_read=notif['is_read'],
                metadata=metadata
            ))
        
        # Calculate unread count
        unread_count = 0
        if not unread_only:
            _, unread_count = await service.get_notifications(unread_only=True, limit=1)
        else:
            unread_count = total_count
        
        has_more = offset + per_page < total_count
        
        return NotificationListResponse(
            notifications=notification_responses,
            total_count=total_count,
            unread_count=unread_count,
            page=page,
            per_page=per_page,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")

@app.post("/api/v1/notifications/{notification_id}/mark-read", tags=["Notifications"])
async def mark_notification_as_read(
    notification_id: str = Path(..., description="Notification ID to mark as read"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Mark a specific notification as read
    
    Marks the notification with the given ID as read.
    """
    try:
        if NotificationService is None:
            raise HTTPException(status_code=503, detail="Notification service not available")
            
        service = await get_notification_service()
        
        success = await service.mark_notification_read(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "success": True,
            "message": "Notification marked as read",
            "notification_id": notification_id,
            "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@app.post("/api/v1/notifications/mark-all-read", tags=["Notifications"])
async def mark_all_notifications_as_read(
    db_check: bool = Depends(validate_db_connection)
):
    """
    Mark all notifications as read
    
    Marks all unread notifications as read.
    """
    try:
        if NotificationService is None:
            raise HTTPException(status_code=503, detail="Notification service not available")
            
        service = await get_notification_service()
        
        updated_count = await service.mark_all_notifications_read()
        
        return {
            "success": True,
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count,
            "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

@app.post("/api/v1/notifications/check-changes", tags=["Notifications"])
async def check_status_changes(
    db_check: bool = Depends(validate_db_connection)
):
    """
    Manually trigger a check for ATM status changes
    
    This endpoint can be called to immediately check for status changes
    and create notifications. Useful for testing or manual triggers.
    """
    try:
        if NotificationService is None:
            raise HTTPException(status_code=503, detail="Notification service not available")
            
        service = await get_notification_service()
        
        new_notifications = await service.check_status_changes()
        
        return {
            "success": True,
            "message": f"Status check completed. Created {len(new_notifications)} new notifications",
            "new_notifications_count": len(new_notifications),
            "new_notifications": [
                {
                    "terminal_id": notif["terminal_id"],
                    "status_change": f"{notif.get('previous_status', 'Unknown')} → {notif['current_status']}",
                    "severity": notif["severity"]
                }
                for notif in new_notifications
            ],
            "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking status changes: {e}")
        raise HTTPException(status_code=500, detail="Failed to check status changes")

@app.get("/api/v1/notifications/unread-count", tags=["Notifications"])
async def get_unread_count(
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get count of unread notifications
    
    Lightweight endpoint for checking notification badge count.
    """
    try:
        if NotificationService is None:
            return {"unread_count": 0, "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()}
            
        service = await get_notification_service()
        
        # Get unread notifications count
        _, unread_count = await service.get_notifications(unread_only=True, limit=1)
        
        return {
            "unread_count": unread_count,
            "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")

# Custom exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()}
    )

if __name__ == "__main__":
    uvicorn.run(
        "api_option_2_fastapi_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
