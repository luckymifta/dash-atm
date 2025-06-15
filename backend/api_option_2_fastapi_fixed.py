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

# Database configuration using the updated credentials
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'dash'),
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

# Fault History Report Models
class FaultDurationData(BaseModel):
    fault_state: str = Field(..., description="ATM fault state (WARNING, WOUNDED, ZOMBIE, OUT_OF_SERVICE)")
    terminal_id: str = Field(..., description="ATM terminal ID")
    start_time: datetime = Field(..., description="When ATM entered fault state")
    end_time: Optional[datetime] = Field(None, description="When ATM returned to AVAILABLE (if it did)")
    duration_minutes: Optional[int] = Field(None, description="Duration in fault state in minutes")
    fault_description: Optional[str] = Field(None, description="Description of the fault")
    fault_type: Optional[str] = Field(None, description="Type of fault (HARDWARE, SOFTWARE, etc.)")
    component_type: Optional[str] = Field(None, description="Component affected")
    terminal_name: Optional[str] = Field(None, description="ATM terminal name")
    location: Optional[str] = Field(None, description="ATM location")

class FaultDurationSummary(BaseModel):
    total_faults: int = Field(..., description="Total number of fault incidents")
    avg_duration_minutes: float = Field(..., description="Average fault duration in minutes")
    max_duration_minutes: int = Field(..., description="Maximum fault duration in minutes")
    min_duration_minutes: int = Field(..., description="Minimum fault duration in minutes")
    faults_resolved: int = Field(..., description="Number of faults that were resolved (returned to AVAILABLE)")
    faults_ongoing: int = Field(..., description="Number of faults still ongoing")

class FaultHistoryReportResponse(BaseModel):
    fault_duration_data: List[FaultDurationData]
    summary_by_state: Dict[str, FaultDurationSummary]
    overall_summary: FaultDurationSummary
    date_range: Dict[str, str] = Field(..., description="Start and end dates of the report")
    terminal_count: int = Field(..., description="Number of terminals included")
    chart_data: Dict[str, Any] = Field(..., description="Chart configuration and data")

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ATM FastAPI application...")
    await create_db_pool()
    yield
    # Shutdown
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

@app.get("/api/v1/atm/fault-history-report", response_model=FaultHistoryReportResponse, tags=["Fault Analysis"])
async def get_fault_history_report(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    terminal_ids: Optional[str] = Query(None, description="Comma-separated terminal IDs, or 'all' for all terminals"),
    include_ongoing: bool = Query(True, description="Include ongoing faults that haven't been resolved"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Generate comprehensive fault history report showing how long ATMs stay in fault states
    
    This endpoint analyzes fault duration patterns to understand:
    - How long ATMs stay in WARNING, WOUNDED, ZOMBIE, OUT_OF_SERVICE states
    - When they return to AVAILABLE state
    - Average fault durations by state
    - Fault patterns and trends
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Parse and validate dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC_TZ)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=UTC_TZ)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        if start_dt > end_dt:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # Build terminal filter
        terminal_filter = ""
        if terminal_ids and terminal_ids.lower() != "all":
            terminal_list = [tid.strip() for tid in terminal_ids.split(",") if tid.strip()]
            if terminal_list:
                placeholders = ",".join([f"${i+3}" for i in range(len(terminal_list))])
                terminal_filter = f"AND td.terminal_id IN ({placeholders})"
        
        # Query to find fault state transitions
        fault_analysis_query = f"""
        WITH status_changes AS (
            SELECT 
                terminal_id,
                location,
                fetched_status,
                retrieved_date,
                LAG(fetched_status) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as prev_status,
                LEAD(fetched_status) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as next_status,
                LEAD(retrieved_date) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as next_time,
                fault_data
            FROM terminal_details td
            WHERE retrieved_date BETWEEN $1 AND $2
            {terminal_filter}
            ORDER BY terminal_id, retrieved_date
        ),
        fault_periods AS (
            SELECT 
                terminal_id,
                location,
                fetched_status as fault_state,
                retrieved_date as fault_start,
                next_time as fault_end,
                CASE 
                    WHEN next_status = 'AVAILABLE' THEN 
                        EXTRACT(EPOCH FROM (next_time - retrieved_date))/60
                    ELSE NULL
                END as duration_minutes,
                fault_data,
                CASE 
                    WHEN next_status = 'AVAILABLE' THEN true
                    ELSE false
                END as resolved
            FROM status_changes
            WHERE fetched_status IN ('WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE')
            AND (prev_status IS NULL OR prev_status = 'AVAILABLE' OR prev_status != fetched_status)
        )
        SELECT 
            fp.terminal_id,
            fp.location,
            fp.fault_state,
            fp.fault_start,
            fp.fault_end,
            fp.duration_minutes,
            fp.resolved,
            COALESCE(fp.fault_data->>'fault_description', 'No description') as fault_description,
            COALESCE(fp.fault_data->>'fault_type', 'Unknown') as fault_type,
            COALESCE(fp.fault_data->>'component_type', 'Unknown') as component_type
        FROM fault_periods fp
        ORDER BY fp.terminal_id, fp.fault_start
        """
        
        # Execute query with parameters
        query_params: List[Any] = [start_dt, end_dt]
        if terminal_ids and terminal_ids.lower() != "all":
            terminal_list = [tid.strip() for tid in terminal_ids.split(",") if tid.strip()]
            query_params.extend(terminal_list)
        
        rows = await conn.fetch(fault_analysis_query, *query_params)
        
        # Process results
        fault_duration_data = []
        summary_by_state = {}
        
        for row in rows:
            # Convert timestamps to Dili time
            start_time = convert_to_dili_time(row['fault_start'])
            end_time = convert_to_dili_time(row['fault_end']) if row['fault_end'] else None
            
            fault_data = FaultDurationData(
                fault_state=row['fault_state'],
                terminal_id=row['terminal_id'],
                start_time=start_time,
                end_time=end_time,
                duration_minutes=int(row['duration_minutes']) if row['duration_minutes'] else None,
                fault_description=row['fault_description'],
                fault_type=row['fault_type'],
                component_type=row['component_type'],
                terminal_name=f"ATM {row['terminal_id']}",
                location=row['location']
            )
            fault_duration_data.append(fault_data)
            
            # Build summary by state
            state = row['fault_state']
            if state not in summary_by_state:
                summary_by_state[state] = {
                    'total_faults': 0,
                    'durations': [],
                    'resolved': 0,
                    'ongoing': 0
                }
            
            summary_by_state[state]['total_faults'] += 1
            if row['duration_minutes']:
                summary_by_state[state]['durations'].append(row['duration_minutes'])
                summary_by_state[state]['resolved'] += 1
            else:
                summary_by_state[state]['ongoing'] += 1
        
        # Calculate summaries
        final_summary_by_state = {}
        overall_durations = []
        total_faults = 0
        total_resolved = 0
        total_ongoing = 0
        
        for state, data in summary_by_state.items():
            durations = data['durations']
            avg_duration = sum(durations) / len(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            
            final_summary_by_state[state] = FaultDurationSummary(
                total_faults=data['total_faults'],
                avg_duration_minutes=round(avg_duration, 2),
                max_duration_minutes=int(max_duration),
                min_duration_minutes=int(min_duration),
                faults_resolved=data['resolved'],
                faults_ongoing=data['ongoing']
            )
            
            overall_durations.extend(durations)
            total_faults += data['total_faults']
            total_resolved += data['resolved']
            total_ongoing += data['ongoing']
        
        # Overall summary
        overall_avg = sum(overall_durations) / len(overall_durations) if overall_durations else 0
        overall_max = max(overall_durations) if overall_durations else 0
        overall_min = min(overall_durations) if overall_durations else 0
        
        overall_summary = FaultDurationSummary(
            total_faults=total_faults,
            avg_duration_minutes=round(overall_avg, 2),
            max_duration_minutes=int(overall_max),
            min_duration_minutes=int(overall_min),
            faults_resolved=total_resolved,
            faults_ongoing=total_ongoing
        )
        
        # Get unique terminal count
        unique_terminals = len(set(row['terminal_id'] for row in rows))
        
        # Generate chart data
        chart_data = {
            "duration_by_state": [
                {
                    "state": state,
                    "avg_duration_hours": round(summary.avg_duration_minutes / 60, 2),
                    "total_faults": summary.total_faults,
                    "resolution_rate": round((summary.faults_resolved / summary.total_faults * 100), 2) if summary.total_faults > 0 else 0
                }
                for state, summary in final_summary_by_state.items()
            ],
            "timeline_data": [
                {
                    "terminal_id": fault.terminal_id,
                    "fault_state": fault.fault_state,
                    "start_time": fault.start_time.isoformat(),
                    "duration_hours": round(fault.duration_minutes / 60, 2) if fault.duration_minutes else None,
                    "resolved": fault.end_time is not None
                }
                for fault in fault_duration_data
            ],
            "colors": {
                "WARNING": "#ffc107",
                "WOUNDED": "#fd7e14", 
                "ZOMBIE": "#6f42c1",
                "OUT_OF_SERVICE": "#dc3545"
            }
        }
        
        return FaultHistoryReportResponse(
            fault_duration_data=fault_duration_data,
            summary_by_state=final_summary_by_state,
            overall_summary=overall_summary,
            date_range={
                "start_date": start_date,
                "end_date": end_date
            },
            terminal_count=unique_terminals,
            chart_data=chart_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating fault history report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate fault history report")
    finally:
        await release_db_connection(conn)

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
