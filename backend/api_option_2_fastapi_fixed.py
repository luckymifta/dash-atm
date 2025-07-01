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
- GET /api/v1/atm/status/trends/overall - Overall ATM availability trends (real ATM data)
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
from fastapi import FastAPI, HTTPException, Query, Path, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Additional imports for background task management
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
from pathlib import Path as PathLib

# Additional imports for predictive analytics
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from statistics import mean, median
import re

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

def convert_to_dili_time(timestamp: datetime) -> datetime:
    """
    Convert a timestamp to Dili local time (UTC+9).
    Handles both UTC timestamps and timestamps already in Dili time.
    
    Args:
        timestamp: A datetime object (timezone-aware or naive)
    
    Returns:
        datetime: Timestamp in Dili local time (timezone-naive for JSON serialization)
    """
    try:
        # If the timestamp has timezone info
        if timestamp.tzinfo is not None:
            # Check if it's already in Dili time (UTC+9)
            if timestamp.utcoffset() == timedelta(hours=9):
                # Already in Dili time, just remove timezone info
                return timestamp.replace(tzinfo=None)
            else:
                # Convert from other timezone to Dili time
                dili_timestamp = timestamp.astimezone(DILI_TZ)
                return dili_timestamp.replace(tzinfo=None)
        else:
            # Timezone-naive timestamp
            # Since data retrieval scripts now store Dili time directly,
            # we need to check if this might already be Dili time
            # For now, we'll assume timezone-naive timestamps are already in Dili time
            # (from our updated data retrieval scripts)
            return timestamp
        
    except Exception as e:
        logger.warning(f"Error processing timestamp: {e}")
        # Fallback: return original timestamp
        return timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp

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

# Refresh job models
class RefreshJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class RefreshJobResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: RefreshJobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    progress: float = Field(0.0, ge=0, le=100, description="Job progress percentage")
    message: str = Field("", description="Current status message")
    error: Optional[str] = Field(None, description="Error message if job failed")

class RefreshJobRequest(BaseModel):
    force: bool = Field(False, description="Force refresh even if recent data exists")
    use_new_tables: bool = Field(True, description="Use new database tables for storage")

# Fault History Report Models
class FaultDurationData(BaseModel):
    fault_state: str = Field(..., description="ATM fault state (WARNING, WOUNDED, ZOMBIE, OUT_OF_SERVICE)")
    terminal_id: str = Field(..., description="ATM terminal ID")
    start_time: datetime = Field(..., description="When ATM entered fault state")
    end_time: Optional[datetime] = Field(None, description="When ATM returned to AVAILABLE (if it did)")
    duration_minutes: Optional[float] = Field(None, description="Duration in fault state in minutes (decimal precision)")
    fault_description: Optional[str] = Field(None, description="Description of the fault")
    fault_type: Optional[str] = Field(None, description="Type of fault (HARDWARE, SOFTWARE, etc.)")
    component_type: Optional[str] = Field(None, description="Component affected")
    terminal_name: Optional[str] = Field(None, description="ATM terminal name")
    location: Optional[str] = Field(None, description="ATM location")
    agent_error_description: Optional[str] = Field(None, description="Detailed agent error description")

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

# Global job tracking
refresh_jobs: Dict[str, RefreshJobResponse] = {}
job_executor = ThreadPoolExecutor(max_workers=2)  # Limit concurrent refresh jobs

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
    
    NOTE: Now uses terminal_details table to match ATM Information page data source
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Use terminal_details table as single source of truth (EXACTLY like ATM Information page)
        # This fixes the data discrepancy between dashboard cards and ATM info page
        # Use identical query logic to ATM information endpoint for perfect consistency
        query = """
            SELECT DISTINCT ON (terminal_id)
                terminal_id, fetched_status, retrieved_date
            FROM terminal_details
            WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
            ORDER BY terminal_id, retrieved_date DESC
        """
        
        rows = await conn.fetch(query)
        
        # Enhanced fallback logic: if no data found for 24h, try longer periods
        actual_hours_used = 24
        if not rows:
            # Try progressively longer periods
            fallback_periods = [48, 72, 168, 336, 720]  # 2 days, 3 days, 1 week, 2 weeks, 1 month
            
            logger.info(f"No data found for 24h period in summary, trying longer fallback periods: {fallback_periods}")
            
            for fallback_hours in fallback_periods:
                fallback_query = """
                    SELECT DISTINCT ON (terminal_id)
                        terminal_id, fetched_status, retrieved_date
                    FROM terminal_details
                    WHERE retrieved_date >= NOW() - INTERVAL '%s hours'
                    ORDER BY terminal_id, retrieved_date DESC
                """ % fallback_hours
                
                rows = await conn.fetch(fallback_query)
                if rows:
                    actual_hours_used = fallback_hours
                    logger.info(f"Found {len(rows)} ATM records using {fallback_hours}h fallback period")
                    break
        
        if not rows:
            raise HTTPException(status_code=404, detail="No ATM data found")
        
        # Count statuses exactly like ATM information page does
        status_counts = {}
        last_updated = None
        
        for row in rows:
            status = row['fetched_status'] or 'UNKNOWN'
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Track latest update time
            if not last_updated or (row['retrieved_date'] and row['retrieved_date'] > last_updated):
                last_updated = row['retrieved_date']
        
        # Map status counts with same logic as status mapping, but handle additional statuses
        available = status_counts.get('AVAILABLE', 0)
        warning = status_counts.get('WARNING', 0)
        # Map WOUNDED, HARD, CASH to wounded category
        wounded = status_counts.get('WOUNDED', 0) + status_counts.get('HARD', 0) + status_counts.get('CASH', 0)
        zombie = status_counts.get('ZOMBIE', 0)
        # Map OUT_OF_SERVICE, UNAVAILABLE to out_of_service category  
        out_of_service = status_counts.get('OUT_OF_SERVICE', 0) + status_counts.get('UNAVAILABLE', 0)
        
        total_atms = len(rows)  # Count actual rows, not calculated sum
        
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
            total_regions=1,  # Using terminal details, so we don't have regional breakdown
            last_updated=last_updated if last_updated else datetime.utcnow(),
            data_source="terminal_details"  # Updated to reflect actual data source
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
        # Build query based on table type - TL-DL region only
        if table_type == TableTypeEnum.LEGACY:
            base_query = """
                WITH latest_regional AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region, retrieval_timestamp
                    FROM regional_data
                    WHERE region_code = 'TL-DL'
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    region_code, count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service, total_atms_in_region,
                    retrieval_timestamp as date_creation
                FROM latest_regional
            """
        else:
            # Query new table (regional_data) - TL-DL region only
            base_query = """
                WITH latest_regional AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region, 
                        retrieval_timestamp
                    FROM regional_data
                    WHERE region_code = 'TL-DL'
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT 
                    region_code, count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service, total_atms_in_region,
                    retrieval_timestamp as date_creation
                FROM latest_regional
            """
        
        # Add region filter if specified (but force TL-DL if none specified)
        if region_code and region_code == 'TL-DL':
            base_query += f" WHERE region_code = $1"
            rows = await conn.fetch(base_query, region_code)
        elif region_code and region_code != 'TL-DL':
            # If someone requests a different region, return empty data
            rows = []
        else:
            # Default to TL-DL only
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

@app.get("/api/v1/atm/status/trends/overall", response_model=TrendResponse, tags=["ATM Status"])
async def get_overall_atm_trends(
    hours: int = Query(24, ge=1, le=720, description="Number of hours to look back (1-720)"),
    interval_minutes: int = Query(60, ge=15, le=360, description="Data aggregation interval in minutes (15-360)"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get historical trends for overall ATM availability using real ATM data
    
    Returns time-series data showing aggregated ATM status changes over time from all individual ATMs.
    This endpoint uses terminal_details table (real ATM data) instead of regional aggregates,
    ensuring consistency with the dashboard summary that uses the same data source.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Query terminal_details table to get time-series data for all ATMs
        # Group by time intervals to aggregate the data points
        query = """
            WITH time_intervals AS (
                SELECT generate_series(
                    date_trunc('hour', NOW() - INTERVAL '%s hours'),
                    date_trunc('hour', NOW()),
                    INTERVAL '%s minutes'
                ) AS interval_start
            ),
            atm_status_at_intervals AS (
                SELECT 
                    ti.interval_start,
                    td.terminal_id,
                    td.fetched_status,
                    ROW_NUMBER() OVER (
                        PARTITION BY ti.interval_start, td.terminal_id 
                        ORDER BY td.retrieved_date DESC
                    ) as rn
                FROM time_intervals ti
                LEFT JOIN terminal_details td ON 
                    td.retrieved_date >= ti.interval_start 
                    AND td.retrieved_date < ti.interval_start + INTERVAL '%s minutes'
                WHERE td.retrieved_date >= NOW() - INTERVAL '%s hours'
            ),
            latest_status_per_interval AS (
                SELECT 
                    interval_start,
                    terminal_id,
                    COALESCE(fetched_status, 'OUT_OF_SERVICE') as status
                FROM atm_status_at_intervals 
                WHERE rn = 1 OR fetched_status IS NULL
            )
            SELECT 
                interval_start,
                COUNT(*) as total_atms,
                COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END) as count_available,
                COUNT(CASE WHEN status = 'WARNING' THEN 1 END) as count_warning,
                COUNT(CASE WHEN status = 'ZOMBIE' THEN 1 END) as count_zombie,
                COUNT(CASE WHEN status IN ('WOUNDED', 'HARD', 'CASH') THEN 1 END) as count_wounded,
                COUNT(CASE WHEN status IN ('OUT_OF_SERVICE', 'UNAVAILABLE') THEN 1 END) as count_out_of_service
            FROM latest_status_per_interval
            GROUP BY interval_start
            HAVING COUNT(*) > 0
            ORDER BY interval_start ASC
        """ % (hours, interval_minutes, interval_minutes, hours)
        
        rows = await conn.fetch(query)
        
        # Enhanced fallback logic: if no data found for requested period, try shorter periods
        actual_hours_used = hours
        fallback_message = None
        
        if not rows:
            # Define fallback periods to try in descending order (shorter periods)
            fallback_periods = [12, 6, 3, 1]  # 12h, 6h, 3h, 1h
            fallback_periods = [period for period in fallback_periods if period < hours]
            
            logger.info(f"No data found for {hours}h period in overall trends, trying shorter fallback periods: {fallback_periods}")
            
            for fallback_hours in fallback_periods:
                fallback_query = """
                    WITH time_intervals AS (
                        SELECT generate_series(
                            date_trunc('hour', NOW() - INTERVAL '%s hours'),
                            date_trunc('hour', NOW()),
                            INTERVAL '%s minutes'
                        ) AS interval_start
                    ),
                    atm_status_at_intervals AS (
                        SELECT 
                            ti.interval_start,
                            td.terminal_id,
                            td.fetched_status,
                            ROW_NUMBER() OVER (
                                PARTITION BY ti.interval_start, td.terminal_id 
                                ORDER BY td.retrieved_date DESC
                            ) as rn
                        FROM time_intervals ti
                        LEFT JOIN terminal_details td ON 
                            td.retrieved_date >= ti.interval_start 
                            AND td.retrieved_date < ti.interval_start + INTERVAL '%s minutes'
                        WHERE td.retrieved_date >= NOW() - INTERVAL '%s hours'
                    ),
                    latest_status_per_interval AS (
                        SELECT 
                            interval_start,
                            terminal_id,
                            COALESCE(fetched_status, 'OUT_OF_SERVICE') as status
                        FROM atm_status_at_intervals 
                        WHERE rn = 1 OR fetched_status IS NULL
                    )
                    SELECT 
                        interval_start,
                        COUNT(*) as total_atms,
                        COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END) as count_available,
                        COUNT(CASE WHEN status = 'WARNING' THEN 1 END) as count_warning,
                        COUNT(CASE WHEN status = 'ZOMBIE' THEN 1 END) as count_zombie,
                        COUNT(CASE WHEN status IN ('WOUNDED', 'HARD', 'CASH') THEN 1 END) as count_wounded,
                        COUNT(CASE WHEN status IN ('OUT_OF_SERVICE', 'UNAVAILABLE') THEN 1 END) as count_out_of_service
                    FROM latest_status_per_interval
                    GROUP BY interval_start
                    HAVING COUNT(*) > 0
                    ORDER BY interval_start ASC
                """ % (fallback_hours, interval_minutes, interval_minutes, fallback_hours)
                
                rows = await conn.fetch(fallback_query)
                if rows:
                    actual_hours_used = fallback_hours
                    fallback_message = f"Requested {hours}h data unavailable, showing available {fallback_hours}h data instead"
                    logger.info(f"Found {len(rows)} data points for {fallback_hours}h fallback period")
                    break
            
            # If still no data found, raise 404
            if not rows:
                raise HTTPException(status_code=404, detail=f"No overall trend data found in any time period")
        
        trends = []
        availability_values = []
        
        for row in rows:
            available = row['count_available'] or 0
            warning = row['count_warning'] or 0
            zombie = row['count_zombie'] or 0
            wounded = row['count_wounded'] or 0
            out_of_service = row['count_out_of_service'] or 0
            total = row['total_atms'] or 0
            
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
                timestamp=convert_to_dili_time(row['interval_start']),
                status_counts=status_counts,
                availability_percentage=round(availability_pct, 2)
            ))
        
        # Calculate summary statistics
        summary_stats = {
            'data_points': len(trends),
            'time_range_hours': actual_hours_used,
            'requested_hours': hours,
            'interval_minutes': interval_minutes,
            'avg_availability': round(sum(availability_values) / len(availability_values), 2) if availability_values else 0,
            'min_availability': round(min(availability_values), 2) if availability_values else 0,
            'max_availability': round(max(availability_values), 2) if availability_values else 0,
            'first_reading': trends[0].timestamp.isoformat() if trends else None,
            'last_reading': trends[-1].timestamp.isoformat() if trends else None,
            'data_source': 'terminal_details',
            'total_atms_tracked': trends[-1].status_counts.total if trends else 0
        }
        
        # Add fallback message if applicable
        if fallback_message:
            summary_stats['fallback_message'] = fallback_message
        
        return TrendResponse(
            region_code="OVERALL", 
            time_period=f"{actual_hours_used} hours" + (f" (requested {hours}h)" if actual_hours_used != hours else ""),
            trends=trends,
            summary_stats=summary_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching overall ATM trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch overall trend data")
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
    Only supports TL-DL region to avoid connection failures.
    """
    # Force TL-DL region only
    if region_code != 'TL-DL':
        raise HTTPException(status_code=400, detail="Only TL-DL region is supported")
        
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
            # Define fallback periods to try in ascending order (longer periods first)
            fallback_periods = [48, 72, 168, 336, 720]  # 2 days, 3 days, 1 week, 2 weeks, 1 month
            fallback_periods = [period for period in fallback_periods if period > hours]
            
            logger.info(f"No data found for {hours}h period, trying longer fallback periods: {fallback_periods}")
            
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
        
        # Legacy table data - TL-DL region only
        if table_type in [TableTypeEnum.LEGACY, TableTypeEnum.BOTH]:
            try:
                legacy_query = """
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, retrieval_timestamp
                    FROM regional_data
                    WHERE region_code = 'TL-DL'
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
        
        # New table data - TL-DL region only
        if table_type in [TableTypeEnum.NEW, TableTypeEnum.BOTH]:
            try:
                new_query = """
                    SELECT DISTINCT ON (region_code)
                        region_code, raw_regional_data, retrieval_timestamp
                    FROM regional_data
                    WHERE region_code = 'TL-DL'
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
                        fetched_status, retrieved_date, fault_data, metadata,
                        raw_terminal_data
                    FROM terminal_details
                    WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
                    ORDER BY terminal_id, retrieved_date DESC
                """
                terminal_rows = await conn.fetch(terminal_query)
                
                # Enhanced fallback logic: if no terminal data found for 24h, try longer periods
                actual_hours_used = 24
                if not terminal_rows:
                    # Try progressively longer periods
                    fallback_periods = [48, 72, 168, 336, 720]  # 2 days, 3 days, 1 week, 2 weeks, 1 month
                    
                    logger.info(f"No terminal details found for 24h period, trying longer fallback periods: {fallback_periods}")
                    
                    for fallback_hours in fallback_periods:
                        fallback_query = """
                            SELECT DISTINCT ON (terminal_id)
                                terminal_id, location, issue_state_name, serial_number,
                                fetched_status, retrieved_date, fault_data, metadata,
                                raw_terminal_data
                            FROM terminal_details
                            WHERE retrieved_date >= NOW() - INTERVAL '%s hours'
                            ORDER BY terminal_id, retrieved_date DESC
                        """ % fallback_hours
                        
                        terminal_rows = await conn.fetch(fallback_query)
                        if terminal_rows:
                            actual_hours_used = fallback_hours
                            logger.info(f"Found {len(terminal_rows)} terminal records using {fallback_hours}h fallback period")
                            break
                
                terminal_data = []
                for row in terminal_rows:
                    # Parse raw_terminal_data to extract additional fields
                    additional_fields = {}
                    if row['raw_terminal_data']:
                        try:
                            if isinstance(row['raw_terminal_data'], str):
                                raw_data = json.loads(row['raw_terminal_data'])
                            else:
                                raw_data = row['raw_terminal_data']
                            
                            # Extract additional fields from raw data
                            if isinstance(raw_data, dict):
                                additional_fields.update({
                                    'external_id': raw_data.get('externalId', row['terminal_id']),
                                    'bank': raw_data.get('bank') if raw_data.get('bank') else None,  # Don't use 'Unknown' default
                                    'brand': raw_data.get('brand'),
                                    'model': raw_data.get('model'),
                                    'city': raw_data.get('city'),
                                    'region': raw_data.get('region'),
                                })
                        except (json.JSONDecodeError, AttributeError):
                            logger.warning(f"Failed to parse raw_terminal_data for terminal {row['terminal_id']}")
                    
                    terminal_data.append({
                        'terminal_id': str(row['terminal_id']),
                        'external_id': additional_fields.get('external_id', str(row['terminal_id'])),
                        'location': row['location'],
                        'location_str': row['location'],  # Frontend expects location_str
                        'city': additional_fields.get('city'),
                        'region': additional_fields.get('region'),
                        'bank': additional_fields.get('bank'),
                        'brand': additional_fields.get('brand'),
                        'model': additional_fields.get('model'),
                        'issue_state_name': row['issue_state_name'],
                        'status': row['fetched_status'],
                        'fetched_status': row['fetched_status'],
                        'serial_number': row['serial_number'],
                        'retrieved_date': convert_to_dili_time(row['retrieved_date']).isoformat() if row['retrieved_date'] else None,
                        'last_updated': convert_to_dili_time(row['retrieved_date']).isoformat() if row['retrieved_date'] else None,
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
        # Share the main application's connection pool instead of creating a new one
        if db_pool is not None:
            notification_service.set_shared_pool(db_pool)
        await notification_service.ensure_notification_tables()
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

# Background task function for running the combined ATM retrieval script
def run_atm_refresh_script(job_id: str, use_new_tables: bool = True):
    """
    Background task function to run the combined ATM retrieval script
    """
    try:
        # Update job status to running
        if job_id in refresh_jobs:
            refresh_jobs[job_id].status = RefreshJobStatus.RUNNING
            refresh_jobs[job_id].started_at = datetime.utcnow()
            refresh_jobs[job_id].message = "Starting ATM data retrieval..."
            refresh_jobs[job_id].progress = 10.0

        # Get the script path (should be in the same directory as this API file)
        script_path = PathLib(__file__).parent / "combined_atm_retrieval_script.py"
        
        if not script_path.exists():
            raise FileNotFoundError(f"Combined ATM retrieval script not found at {script_path}")

        # Prepare command arguments
        cmd = [sys.executable, str(script_path), "--save-to-db"]
        if use_new_tables:
            cmd.append("--use-new-tables")

        logger.info(f"Starting ATM refresh job {job_id} with command: {' '.join(cmd)}")

        # Update progress
        if job_id in refresh_jobs:
            refresh_jobs[job_id].message = "Executing data retrieval script..."
            refresh_jobs[job_id].progress = 30.0

        # Run the script
        result = subprocess.run(
            cmd,
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes timeout
        )

        # Update progress
        if job_id in refresh_jobs:
            refresh_jobs[job_id].progress = 80.0
            refresh_jobs[job_id].message = "Processing results..."

        if result.returncode == 0:
            # Success
            if job_id in refresh_jobs:
                refresh_jobs[job_id].status = RefreshJobStatus.COMPLETED
                refresh_jobs[job_id].completed_at = datetime.utcnow()
                refresh_jobs[job_id].progress = 100.0
                refresh_jobs[job_id].message = "ATM data refresh completed successfully"
                
            logger.info(f"ATM refresh job {job_id} completed successfully")
            logger.debug(f"Script output: {result.stdout}")
        else:
            # Script failed
            error_msg = f"Script failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr}"
                
            if job_id in refresh_jobs:
                refresh_jobs[job_id].status = RefreshJobStatus.FAILED
                refresh_jobs[job_id].completed_at = datetime.utcnow()
                refresh_jobs[job_id].error = error_msg
                refresh_jobs[job_id].message = "ATM data refresh failed"
                
            logger.error(f"ATM refresh job {job_id} failed: {error_msg}")
            logger.debug(f"Script stderr: {result.stderr}")
            logger.debug(f"Script stdout: {result.stdout}")

    except subprocess.TimeoutExpired:
        error_msg = "Script execution timed out after 15 minutes"
        if job_id in refresh_jobs:
            refresh_jobs[job_id].status = RefreshJobStatus.FAILED
            refresh_jobs[job_id].completed_at = datetime.utcnow()
            refresh_jobs[job_id].error = error_msg
            refresh_jobs[job_id].message = "ATM data refresh timed out"
        logger.error(f"ATM refresh job {job_id} timed out")
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        if job_id in refresh_jobs:
            refresh_jobs[job_id].status = RefreshJobStatus.FAILED
            refresh_jobs[job_id].completed_at = datetime.utcnow()
            refresh_jobs[job_id].error = error_msg
            refresh_jobs[job_id].message = "ATM data refresh failed"
        logger.error(f"ATM refresh job {job_id} failed with error: {e}")

# Refresh endpoints
@app.post("/api/v1/atm/refresh", response_model=RefreshJobResponse, tags=["ATM Refresh"])
async def trigger_atm_refresh(
    background_tasks: BackgroundTasks,
    refresh_request: RefreshJobRequest = RefreshJobRequest(force=False, use_new_tables=True)
):
    """
    Trigger an immediate refresh of ATM data
    
    This endpoint starts a background job to run the combined ATM retrieval script,
    which will fetch fresh data from the ATM monitoring system and update the database.
    The job runs asynchronously, so you can check its status using the job ID returned.
    """
    try:
        # Check if there's already a running job
        running_jobs = [job for job in refresh_jobs.values() if job.status == RefreshJobStatus.RUNNING]
        if running_jobs and not refresh_request.force:
            raise HTTPException(
                status_code=409, 
                detail="A refresh job is already running. Use force=true to queue another job."
            )

        # Create new job
        job_id = str(uuid.uuid4())
        job = RefreshJobResponse(
            job_id=job_id,
            status=RefreshJobStatus.QUEUED,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            progress=0.0,
            message="Refresh job queued",
            error=None
        )
        
        refresh_jobs[job_id] = job
        
        # Add background task
        background_tasks.add_task(
            run_atm_refresh_script, 
            job_id, 
            refresh_request.use_new_tables
        )
        
        logger.info(f"ATM refresh job {job_id} queued")
        
        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering ATM refresh: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger refresh")

@app.get("/api/v1/atm/refresh/{job_id}", response_model=RefreshJobResponse, tags=["ATM Refresh"])
async def get_refresh_job_status(job_id: str = Path(..., description="Job ID to check")):
    """
    Get the status of a refresh job
    
    Check the current status, progress, and any error messages for a specific refresh job.
    """
    if job_id not in refresh_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return refresh_jobs[job_id]

@app.get("/api/v1/atm/refresh", response_model=List[RefreshJobResponse], tags=["ATM Refresh"])
async def list_refresh_jobs(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of jobs to return"),
    status: Optional[RefreshJobStatus] = Query(None, description="Filter by job status")
):
    """
    List refresh jobs
    
    Get a list of recent refresh jobs, optionally filtered by status.
    """
    jobs = list(refresh_jobs.values())
    
    # Filter by status if specified
    if status:
        jobs = [job for job in jobs if job.status == status]
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply limit
    return jobs[:limit]

# Custom exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()}
    )

# ========================
# PREDICTIVE ANALYTICS ENDPOINTS (Using Existing Data)
# ========================

# Pydantic models for predictive analytics
class ComponentHealthScore(BaseModel):
    component_type: str = Field(..., description="Component type (DISPENSER, READER, etc.)")
    health_score: float = Field(..., ge=0, le=100, description="Health score percentage")
    failure_risk: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    last_fault_date: Optional[datetime] = Field(None, description="Last fault timestamp")
    fault_frequency: int = Field(..., ge=0, description="Number of faults in last 30 days")

class FailurePrediction(BaseModel):
    risk_score: float = Field(..., ge=0, le=100, description="Failure risk score percentage")
    risk_level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    prediction_horizon: str = Field(..., description="Prediction time horizon")
    confidence: float = Field(..., ge=0, le=100, description="Prediction confidence percentage")
    contributing_factors: List[str] = Field(..., description="Main factors contributing to prediction")

class MaintenanceRecommendation(BaseModel):
    action: str = Field(..., description="Recommended maintenance action")
    priority: str = Field(..., description="Priority level (LOW, MEDIUM, HIGH, URGENT)")
    estimated_time: str = Field(..., description="Estimated time to complete")
    components: List[str] = Field(..., description="Components requiring attention")
    description: str = Field(..., description="Detailed description of recommendation")

class ATMPredictiveAnalytics(BaseModel):
    terminal_id: str = Field(..., description="Terminal identifier")
    location: Optional[str] = Field(None, description="ATM location")
    overall_health_score: float = Field(..., ge=0, le=100, description="Overall ATM health score")
    failure_prediction: FailurePrediction
    component_health: List[ComponentHealthScore]
    maintenance_recommendations: List[MaintenanceRecommendation]
    data_quality_score: float = Field(..., ge=0, le=100, description="Quality of data used for prediction")
    last_analysis: datetime = Field(..., description="When analysis was performed")
    analysis_period: str = Field(..., description="Data period used for analysis")

class PredictiveAnalyticsResponse(BaseModel):
    atm_analytics: ATMPredictiveAnalytics
    analysis_metadata: Dict[str, Any] = Field(..., description="Metadata about the analysis")

# Utility functions for predictive analytics using existing JSONB data
def calculate_component_health_score(fault_history: List[Dict[str, Any]], component_type: str) -> ComponentHealthScore:
    """Calculate health score for a specific component based on fault history from JSONB data"""
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    component_faults = []
    last_fault_date = None
    
    # Component mapping - map component types to keywords in fault descriptions
    component_keywords = {
        'DISPENSER': ['CDM', 'dispenser', 'notes', 'cash', 'bills', 'currency'],
        'READER': ['reader', 'card', 'magnetic', 'chip'],
        'PRINTER': ['printer', 'receipt', 'paper', 'print'],
        'NETWORK_MODULE': ['network', 'communications', 'connection', 'comms'],
        'DEPOSIT_MODULE': ['deposit', 'check', 'envelope'],
        'SENSOR': ['sensor', 'detect', 'proximity', 'motion']
    }
    
    for fault in fault_history:
        # Try to parse the creation date from the actual fault data structure
        creation_date = fault.get('agentErrorDescription')
        fault_date = None
        
        if creation_date:
            try:
                if isinstance(creation_date, str):
                    # Handle different date formats found in the data
                    # Format: "11:06:2025 11:40:18" (day:month:year hour:minute:second)
                    if ':' in creation_date and len(creation_date.split(' ')) == 2:
                        date_part, time_part = creation_date.split(' ')
                        day, month_num, year = date_part.split(':')
                        hour, minute, second = time_part.split(':')
                        
                        # Convert month number to actual month
                        month_map = {
                            '01': 1, '02': 2, '03': 3, '04': 4, '05': 5, '06': 6,
                            '07': 7, '08': 8, '09': 9, '10': 10, '11': 11, '12': 12,
                            'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4,
                            'MAY': 5, 'JUNE': 6, 'JULY': 7, 'AUGUST': 8,
                            'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
                        }
                        
                        month_int = month_map.get(month_num, int(month_num) if month_num.isdigit() else 1)
                        fault_date = datetime(int(year), month_int, int(day), int(hour), int(minute), int(second))
                    else:
                        # Try ISO format
                        fault_date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                elif isinstance(creation_date, (int, float)):
                    # Unix timestamp
                    fault_date = datetime.fromtimestamp(creation_date / 1000)
            except Exception as e:
                # If date parsing fails, include the fault anyway but without date filtering
                fault_date = now  # Treat as recent
        
        # Check if this fault is related to the specified component
        fault_description = fault.get('agentErrorDescription', '').lower()
        external_fault_id = fault.get('externalFaultId', '').lower()
        
        # Check if fault relates to this component type
        is_component_fault = False
        if component_type in component_keywords:
            keywords = component_keywords[component_type]
            for keyword in keywords:
                if keyword.lower() in fault_description or keyword.lower() in external_fault_id:
                    is_component_fault = True
                    break
        
        if is_component_fault:
            if fault_date and fault_date >= thirty_days_ago:
                component_faults.append(fault)
                if not last_fault_date or fault_date > last_fault_date:
                    last_fault_date = fault_date
            elif not fault_date:
                # Include faults without parseable dates
                component_faults.append(fault)
    
    fault_count = len(component_faults)
    base_score = 100
    
    # Reduce score based on fault frequency and severity
    for fault in component_faults:
        # Determine severity based on fault description keywords
        fault_description = fault.get('agentErrorDescription', '').lower()
        
        # Critical keywords that indicate severe issues
        critical_keywords = ['timeout', 'failure', 'error', 'jam', 'stuck', 'blocked']
        warning_keywords = ['out of', 'empty', 'low', 'warning', 'check']
        
        if any(keyword in fault_description for keyword in critical_keywords):
            severity_impact = 12  # Critical impact
        elif any(keyword in fault_description for keyword in warning_keywords):
            severity_impact = 6   # Warning impact
        else:
            severity_impact = 8   # Default moderate impact
        
        base_score -= severity_impact
    
    health_score = max(0, min(100, base_score))
    
    # Determine risk level
    if health_score >= 85:
        risk_level = "LOW"
    elif health_score >= 70:
        risk_level = "MEDIUM" 
    elif health_score >= 50:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"
    
    return ComponentHealthScore(
        component_type=component_type,
        health_score=round(health_score, 1),
        failure_risk=risk_level,
        last_fault_date=last_fault_date,
        fault_frequency=fault_count
    )

def predict_atm_failure(fault_history: List[Dict[str, Any]], component_health: List[ComponentHealthScore]) -> FailurePrediction:
    """Predict ATM failure based on existing fault data"""
    # Calculate risk based on component health and fault patterns
    avg_component_health = mean([comp.health_score for comp in component_health]) if component_health else 100
    
    # Count recent faults (last 7 days)
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    recent_faults = []
    
    for fault in fault_history:
        creation_date = fault.get('creationDate')
        fault_date = None
        
        if creation_date:
            try:
                if isinstance(creation_date, str):
                    # Handle the specific date format found in the data
                    # Format: "11:06:2025 11:40:18" (day:month:year hour:minute:second)
                    if ':' in creation_date and len(creation_date.split(' ')) == 2:
                        date_part, time_part = creation_date.split(' ')
                        day, month_num, year = date_part.split(':')
                        hour, minute, second = time_part.split(':')
                        
                        # Convert month number to actual month
                        month_map = {
                            '01': 1, '02': 2, '03': 3, '04': 4, '05': 5, '06': 6,
                            '07': 7, '08': 8, '09': 9, '10': 10, '11': 11, '12': 12
                        }
                        
                        month_int = month_map.get(month_num, int(month_num) if month_num.isdigit() else 1)
                        fault_date = datetime(int(year), month_int, int(day), int(hour), int(minute), int(second))
                    else:
                        # Try ISO format
                        fault_date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                elif isinstance(creation_date, (int, float)):
                    fault_date = datetime.fromtimestamp(creation_date / 1000)
                    
                if fault_date and fault_date >= seven_days_ago:
                    recent_faults.append(fault)
            except Exception as e:
                # If date parsing fails, include the fault anyway as potentially recent
                recent_faults.append(fault)
    
    # Calculate risk score
    risk_score = (100 - avg_component_health) * 0.6 + min(len(recent_faults) * 15, 40)
    risk_score = max(0, min(100, risk_score))
    
    # Determine risk level and prediction horizon
    if risk_score < 25:
        risk_level = "LOW"
        horizon = "30+ days"
        confidence = 75
    elif risk_score < 50:
        risk_level = "MEDIUM"
        horizon = "14-30 days"
        confidence = 80
    elif risk_score < 75:
        risk_level = "HIGH"
        horizon = "7-14 days"
        confidence = 85
    else:
        risk_level = "CRITICAL"
        horizon = "1-7 days"
        confidence = 90
    
    # Contributing factors
    factors = []
    if avg_component_health < 70:
        factors.append("Component degradation detected")
    if len(recent_faults) > 3:
        factors.append("High recent fault frequency")
    if not factors:
        factors = ["Normal operational patterns"]
    
    return FailurePrediction(
        risk_score=round(risk_score, 1),
        risk_level=risk_level,
        prediction_horizon=horizon,
        confidence=confidence,
        contributing_factors=factors
    )

def generate_maintenance_recommendations(component_health: List[ComponentHealthScore], 
                                       failure_prediction: FailurePrediction) -> List[MaintenanceRecommendation]:
    """Generate maintenance recommendations based on analysis"""
    recommendations = []
    
    # Component-specific recommendations
    for comp in component_health:
        if comp.health_score < 70:
            if comp.component_type in ["DISPENSER", "READER", "PRINTER"]:
                priority = "HIGH" if comp.health_score < 50 else "MEDIUM"
                recommendations.append(MaintenanceRecommendation(
                    action=f"Inspect and service {comp.component_type.lower()}",
                    priority=priority,
                    estimated_time="2-3 hours",
                    components=[comp.component_type],
                    description=f"{comp.component_type} health score is {comp.health_score}%. Requires attention."
                ))
    
    # Risk-based recommendations
    if failure_prediction.risk_level in ["HIGH", "CRITICAL"]:
        recommendations.append(MaintenanceRecommendation(
            action="Comprehensive ATM inspection",
            priority="URGENT" if failure_prediction.risk_level == "CRITICAL" else "HIGH",
            estimated_time="4-6 hours",
            components=["ALL"],
            description=f"High failure risk detected ({failure_prediction.risk_score}%). Perform complete diagnostic check."
        ))
    
    # Default recommendation if no issues found
    if not recommendations:
        recommendations.append(MaintenanceRecommendation(
            action="Routine preventive maintenance",
            priority="LOW",
            estimated_time="2 hours",
            components=["ALL"],
            description="ATM appears healthy. Perform routine checks to maintain optimal performance."
        ))
    
    return recommendations

@app.get("/api/v1/atm/{terminal_id}/predictive-analytics", response_model=PredictiveAnalyticsResponse, tags=["Predictive Analytics"])
async def get_atm_predictive_analytics(
    terminal_id: str = Path(..., description="Terminal ID to analyze"),
    analysis_days: int = Query(30, ge=7, le=90, description="Days of data to analyze"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get predictive analytics for a specific ATM using existing JSONB fault data
    
    Analyzes fault history from terminal_details table and provides:
    - Component health scores  
    - Failure risk predictions
    - Maintenance recommendations
    - Data quality assessment
    
    No database schema changes required - uses existing JSONB fault data.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Get latest terminal info and fault data
        query = """
            SELECT 
                terminal_id, location, fault_data, retrieved_date
            FROM terminal_details
            WHERE terminal_id = $1 
                AND retrieved_date >= NOW() - INTERVAL '%s days'
                AND fault_data IS NOT NULL
            ORDER BY retrieved_date DESC
        """ % analysis_days
        
        rows = await conn.fetch(query, terminal_id)
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No fault data found for terminal {terminal_id} in the last {analysis_days} days")
        
        # Extract fault history from JSONB data
        fault_history = []
        location = None
        
        for row in rows:
            if not location:
                location = row['location']
                
            if row['fault_data']:
                try:
                    fault_data = row['fault_data']
                    
                    # Parse JSON string if needed
                    if isinstance(fault_data, str):
                        try:
                            fault_data = json.loads(fault_data)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse fault_data as JSON for terminal {terminal_id}")
                            continue
                    
                    if isinstance(fault_data, dict):
                        fault_history.append(fault_data)
                    elif isinstance(fault_data, list):
                        # If fault_data is a list, extend fault_history with each item
                        fault_history.extend([item for item in fault_data if isinstance(item, dict)])
                except Exception as e:
                    logger.warning(f"Could not parse fault data for terminal {terminal_id}: {e}")
        
        if not fault_history:
            raise HTTPException(
                status_code=404, 
                detail=f"No valid fault data found for terminal {terminal_id} in the last {analysis_days} days"
            )
        
        # Analyze component health
        component_types = ["DISPENSER", "READER", "PRINTER", "NETWORK_MODULE", "DEPOSIT_MODULE", "SENSOR"]
        component_health = []
        
        for comp_type in component_types:
            health_score = calculate_component_health_score(fault_history, comp_type)
            component_health.append(health_score)
        
        # Calculate overall health
        overall_health = mean([comp.health_score for comp in component_health])
        
        # Predict failure
        failure_prediction = predict_atm_failure(fault_history, component_health)
        
        # Generate recommendations
        maintenance_recommendations = generate_maintenance_recommendations(component_health, failure_prediction)
        
        # Calculate data quality score
        data_points = len(fault_history)
        expected_data_points = analysis_days * 1  # Assume 1 check per day minimum
        data_quality = min(100, (data_points / expected_data_points) * 100) if expected_data_points > 0 else 0
        
        # Create response
        atm_analytics = ATMPredictiveAnalytics(
            terminal_id=terminal_id,
            location=location,
            overall_health_score=round(overall_health, 1),
            failure_prediction=failure_prediction,
            component_health=component_health,
            maintenance_recommendations=maintenance_recommendations,
            data_quality_score=round(data_quality, 1),
            last_analysis=convert_to_dili_time(datetime.utcnow()),
            analysis_period=f"{analysis_days} days"
        )
        
        analysis_metadata = {
            "data_points_analyzed": data_points,
            "analysis_period_days": analysis_days,
            "components_analyzed": len(component_types),
            "algorithm_version": "1.0-jsonb",
            "analysis_timestamp": convert_to_dili_time(datetime.utcnow()).isoformat(),
            "data_source": "terminal_details.fault_data (JSONB)"
        }
        
        return PredictiveAnalyticsResponse(
            atm_analytics=atm_analytics,
            analysis_metadata=analysis_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictive analytics for ATM {terminal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictive analytics")
    finally:
        await release_db_connection(conn)

@app.get("/api/v1/atm/predictive-analytics/summary", tags=["Predictive Analytics"])
async def get_predictive_analytics_summary(
    risk_level_filter: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of ATMs to analyze"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get predictive analytics summary for multiple ATMs using existing data
    
    Provides a quick overview of failure risks across the ATM fleet.
    Uses existing JSONB fault data without requiring database changes.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Get terminals with recent fault data
        terminals_query = """
            SELECT DISTINCT terminal_id, location
            FROM terminal_details
            WHERE retrieved_date >= NOW() - INTERVAL '7 days'
                AND fault_data IS NOT NULL
            ORDER BY terminal_id
            LIMIT $1
        """
        
        terminal_rows = await conn.fetch(terminals_query, limit)
        
        if not terminal_rows:
            return {
                "summary": [],
                "fleet_statistics": {
                    "total_atms_analyzed": 0,
                    "average_health_score": 0,
                    "average_risk_score": 0,
                    "risk_distribution": {},
                    "analysis_timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()
                },
                "message": "No terminals with recent fault data found"
            }
        
        summary_results = []
        
        for terminal_row in terminal_rows:
            terminal_id = terminal_row['terminal_id']
            
            try:
                # Get fault data for this terminal
                fault_query = """
                    SELECT fault_data
                    FROM terminal_details
                    WHERE terminal_id = $1 
                        AND retrieved_date >= NOW() - INTERVAL '14 days'
                        AND fault_data IS NOT NULL
                    ORDER BY retrieved_date DESC
                """
                
                fault_rows = await conn.fetch(fault_query, terminal_id)
                
                fault_history = []
                for fault_row in fault_rows:
                    if fault_row['fault_data']:
                        try:
                            fault_data = fault_row['fault_data']
                            
                            # Parse JSON string if needed
                            if isinstance(fault_data, str):
                                try:
                                    fault_data = json.loads(fault_data)
                                except json.JSONDecodeError:
                                    continue
                    
                            if isinstance(fault_data, dict):
                                fault_history.append(fault_data)
                        except:
                            continue
                
                if not fault_history:
                    continue
                
                # Quick analysis
                component_types = ["DISPENSER", "READER", "PRINTER", "NETWORK_MODULE"]
                component_health = []
                
                for comp_type in component_types:
                    health_score = calculate_component_health_score(fault_history, comp_type)
                    component_health.append(health_score)
                
                overall_health = mean([comp.health_score for comp in component_health])
                failure_prediction = predict_atm_failure(fault_history, component_health)
                
                # Apply filter if specified
                if risk_level_filter and failure_prediction.risk_level != risk_level_filter:
                    continue
                
                summary_results.append({
                    "terminal_id": terminal_id,
                    "location": terminal_row['location'],
                    "overall_health_score": round(overall_health, 1),
                    "risk_level": failure_prediction.risk_level,
                    "risk_score": failure_prediction.risk_score,
                    "prediction_horizon": failure_prediction.prediction_horizon,
                    "confidence": failure_prediction.confidence,
                    "critical_components": len([comp for comp in component_health if comp.failure_risk == "CRITICAL"]),
                    "last_analysis": convert_to_dili_time(datetime.utcnow()).isoformat()
                })
                
            except Exception as e:
                logger.warning(f"Could not analyze terminal {terminal_id}: {e}")
                continue
        
        # Sort by risk score (highest first)
        summary_results.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Calculate fleet statistics
        if summary_results:
            risk_distribution = Counter([result['risk_level'] for result in summary_results])
            avg_health = mean([result['overall_health_score'] for result in summary_results])
            avg_risk = mean([result['risk_score'] for result in summary_results])
        else:
            risk_distribution = {}
            avg_health = 0
            avg_risk = 0
        
        return {
            "summary": summary_results,
            "fleet_statistics": {
                "total_atms_analyzed": len(summary_results),
                "average_health_score": round(avg_health, 1),
                "average_risk_score": round(avg_risk, 1),
                "risk_distribution": dict(risk_distribution),
                "analysis_timestamp": convert_to_dili_time(datetime.utcnow()).isoformat()
            },
            "filters_applied": {
                "risk_level_filter": risk_level_filter,
                "limit": limit
            },
            "data_source": "terminal_details.fault_data (JSONB)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictive analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictive analytics summary")
    finally:
        await release_db_connection(conn)

# ========================
# FAULT HISTORY REPORT ENDPOINT
# ========================

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
        
        # Enhanced fault cycle analysis query - tracks complete fault cycles
        fault_analysis_query = f"""
        WITH status_transitions AS (
            SELECT 
                terminal_id,
                location,
                fetched_status,
                retrieved_date,
                LAG(fetched_status) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as prev_status,
                LEAD(fetched_status) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as next_status,
                LEAD(retrieved_date) OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as next_time,
                fault_data,
                ROW_NUMBER() OVER (PARTITION BY terminal_id ORDER BY retrieved_date) as row_num
            FROM terminal_details td
            WHERE retrieved_date BETWEEN $1 AND $2
            {terminal_filter}
            ORDER BY terminal_id, retrieved_date
        ),
        fault_cycle_starts AS (
            -- Find all entries where ATM enters fault state from AVAILABLE/ONLINE
            SELECT 
                terminal_id,
                location,
                fetched_status as fault_state,
                retrieved_date as fault_start,
                fault_data
            FROM status_transitions
            WHERE fetched_status IN ('WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE')
            AND (prev_status IS NULL OR prev_status IN ('AVAILABLE', 'ONLINE'))
        ),
        fault_cycle_ends AS (
            -- Find all entries where ATM returns to AVAILABLE/ONLINE from fault state
            SELECT 
                terminal_id,
                prev_status as end_fault_state,
                retrieved_date as fault_end
            FROM status_transitions
            WHERE fetched_status IN ('AVAILABLE', 'ONLINE')
            AND prev_status IN ('WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE')
        ),
        complete_fault_cycles AS (
            SELECT 
                fcs.terminal_id,
                fcs.location,
                fcs.fault_state,
                fcs.fault_start,
                fcs.fault_data,
                -- Find the next resolution for this fault cycle
                (SELECT MIN(fce.fault_end) 
                 FROM fault_cycle_ends fce 
                 WHERE fce.terminal_id = fcs.terminal_id 
                 AND fce.fault_end > fcs.fault_start) as fault_end
            FROM fault_cycle_starts fcs
        )
        SELECT 
            cfc.terminal_id,
            cfc.location,
            cfc.fault_state,
            cfc.fault_start,
            cfc.fault_end,
            -- Calculate actual duration from fault start to resolution (or ongoing)
            CASE 
                WHEN cfc.fault_end IS NOT NULL THEN 
                    EXTRACT(EPOCH FROM (cfc.fault_end - cfc.fault_start))/60
                WHEN cfc.fault_end IS NULL AND $2 > cfc.fault_start THEN
                    EXTRACT(EPOCH FROM ($2 - cfc.fault_start))/60
                ELSE NULL
            END as duration_minutes,
            -- Mark as resolved only when fault_end exists (returned to AVAILABLE)
            CASE 
                WHEN cfc.fault_end IS NOT NULL THEN true
                ELSE false
            END as resolved,
            COALESCE(cfc.fault_data->>'agentErrorDescription', cfc.fault_data->>'fault_description', 'No description') as fault_description,
            COALESCE(cfc.fault_data->>'fault_type', 'Unknown') as fault_type,
            COALESCE(cfc.fault_data->>'component_type', 'Unknown') as component_type,
            cfc.fault_data->>'agentErrorDescription' as agent_error_description
        FROM complete_fault_cycles cfc
        {"WHERE 1=1" if include_ongoing else "WHERE cfc.fault_end IS NOT NULL"}
        ORDER BY cfc.terminal_id, cfc.fault_start
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
                duration_minutes=float(row['duration_minutes']) if row['duration_minutes'] else None,
                fault_description=row['fault_description'],
                fault_type=row['fault_type'],
                component_type=row['component_type'],
                terminal_name=f"ATM {row['terminal_id']}",
                location=row['location'],
                agent_error_description=row.get('agent_error_description')
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
                
            # Use the resolved flag from the database query
            if row['resolved']:
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

if __name__ == "__main__":
    uvicorn.run(
        "api_option_2_fastapi_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
