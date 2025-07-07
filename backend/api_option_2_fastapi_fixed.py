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
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from enum import Enum
import asyncio
import asyncpg
from contextlib import asynccontextmanager
import pytz
import jwt

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path as FastAPIPath, Depends, BackgroundTasks, UploadFile, File, Form, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, ConfigDict
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

# File upload configuration for maintenance system
UPLOAD_CONFIG = {
    'upload_directory': os.getenv('UPLOAD_DIRECTORY', '../uploads/maintenance'),
    'max_file_size': int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024)),  # 10MB default
    'max_files_per_record': int(os.getenv('MAX_FILES_PER_RECORD', 10)),
    'allowed_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx']
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

class UserRole(str, Enum):
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"

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

# Terminal Maintenance Management Models (PRD.md section 2.2.3)
class MaintenanceTypeEnum(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    EMERGENCY = "EMERGENCY"

class MaintenancePriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MaintenanceStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class MaintenanceImage(BaseModel):
    image_id: str = Field(..., description="Unique identifier for the image")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Server file path")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    file_size: int = Field(..., description="File size in bytes")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    )

class MaintenanceCreate(BaseModel):
    terminal_id: str = Field(..., description="Terminal identifier")
    start_datetime: datetime = Field(..., description="Maintenance start time")
    end_datetime: Optional[datetime] = Field(None, description="Maintenance end time")
    problem_description: str = Field(..., min_length=10, max_length=2000, description="Problem description")
    solution_description: Optional[str] = Field(None, max_length=2000, description="Solution description")
    maintenance_type: MaintenanceTypeEnum = Field(MaintenanceTypeEnum.CORRECTIVE, description="Type of maintenance")
    priority: MaintenancePriorityEnum = Field(MaintenancePriorityEnum.MEDIUM, description="Priority level")
    status: MaintenanceStatusEnum = Field(MaintenanceStatusEnum.PLANNED, description="Current status")

    @field_validator('end_datetime')
    @classmethod
    def validate_end_datetime(cls, v, info):
        if v is not None and 'start_datetime' in info.data:
            if v <= info.data['start_datetime']:
                raise ValueError('end_datetime must be after start_datetime')
        return v

    @field_validator('start_datetime')
    @classmethod
    def validate_start_datetime(cls, v):
        # Cannot be more than 1 hour in the future (PRD business rule)
        max_future = datetime.now() + timedelta(hours=1)
        if v > max_future:
            raise ValueError('start_datetime cannot be more than 1 hour in the future')
        return v

class MaintenanceUpdate(BaseModel):
    start_datetime: Optional[datetime] = Field(None, description="Maintenance start time")
    end_datetime: Optional[datetime] = Field(None, description="Maintenance end time")
    problem_description: Optional[str] = Field(None, min_length=10, max_length=2000, description="Problem description")
    solution_description: Optional[str] = Field(None, max_length=2000, description="Solution description")
    maintenance_type: Optional[MaintenanceTypeEnum] = Field(None, description="Type of maintenance")
    priority: Optional[MaintenancePriorityEnum] = Field(None, description="Priority level")
    status: Optional[MaintenanceStatusEnum] = Field(None, description="Current status")

    @field_validator('end_datetime')
    @classmethod
    def validate_end_datetime(cls, v, info):
        if v is not None and 'start_datetime' in info.data and info.data['start_datetime'] is not None:
            if v <= info.data['start_datetime']:
                raise ValueError('end_datetime must be after start_datetime')
        return v

class MaintenanceRecord(BaseModel):
    id: str = Field(..., description="Unique maintenance record identifier")
    terminal_id: str = Field(..., description="Terminal identifier")
    terminal_name: Optional[str] = Field(None, description="Terminal name")
    location: Optional[str] = Field(None, description="Terminal location")
    start_datetime: datetime = Field(..., description="Maintenance start time")
    end_datetime: Optional[datetime] = Field(None, description="Maintenance end time")
    problem_description: str = Field(..., description="Problem description")
    solution_description: Optional[str] = Field(None, description="Solution description")
    maintenance_type: str = Field(..., description="Type of maintenance")
    priority: str = Field(..., description="Priority level")
    status: str = Field(..., description="Current status")
    images: List[MaintenanceImage] = Field(default_factory=list, description="Attached images")
    duration_hours: Optional[float] = Field(None, description="Duration in hours")
    created_by: str = Field(..., description="User who created the record")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class MaintenanceListFilter(BaseModel):
    terminal_id: Optional[str] = Field(None, description="Filter by terminal ID")
    status: Optional[MaintenanceStatusEnum] = Field(None, description="Filter by status")
    maintenance_type: Optional[MaintenanceTypeEnum] = Field(None, description="Filter by type")
    priority: Optional[MaintenancePriorityEnum] = Field(None, description="Filter by priority")
    created_by: Optional[str] = Field(None, description="Filter by creator")
    start_date: Optional[datetime] = Field(None, description="Filter from date")
    end_date: Optional[datetime] = Field(None, description="Filter to date")

class MaintenanceListResponse(BaseModel):
    maintenance_records: List[MaintenanceRecord] = Field(..., description="List of maintenance records")
    total_count: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Records per page")
    has_more: bool = Field(..., description="Whether more records exist")
    filters_applied: Dict[str, Any] = Field(..., description="Applied filters")

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

# Lifespan management
@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
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

# Mount static files directory for image serving
import os
upload_directory = os.getenv('UPLOAD_DIRECTORY', '../uploads/maintenance')
if os.path.exists(upload_directory):
    app.mount("/uploads", StaticFiles(directory=upload_directory), name="uploads")

# Global variables
app_start_time = datetime.now()
db_pool = None

# Global job tracking for refresh operations
refresh_jobs: Dict[str, RefreshJobResponse] = {}
job_executor = ThreadPoolExecutor(max_workers=2)  # Limit concurrent refresh jobs

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

@app.get("/api/v1/atm/status/trends/overall/events", response_model=TrendResponse, tags=["ATM Status"])
async def get_overall_atm_trends_events(
    hours: int = Query(168, ge=1, le=2160, description="Number of hours to look back (1-2160, default 168=7 days)"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get historical trends for overall ATM availability using event-based status changes
    
    Returns time-series data showing actual ATM status change events across all ATMs,
    similar to individual ATM history but aggregated. This provides event-driven timestamps
    instead of fixed time intervals, making it consistent with individual ATM charts.
    
    This endpoint uses terminal_details table to collect all status change events
    and calculates overall availability at each event timestamp.
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Query terminal_details table to get all status change events across all ATMs
        # We'll get distinct timestamps when any ATM changed status, then calculate overall availability at each timestamp
        query = """
            WITH status_events AS (
                SELECT DISTINCT retrieved_date
                FROM terminal_details
                WHERE retrieved_date >= NOW() - INTERVAL '%s hours'
                ORDER BY retrieved_date ASC
            ),
            atm_status_at_events AS (
                SELECT 
                    se.retrieved_date as event_time,
                    td.terminal_id,
                    td.fetched_status,
                    ROW_NUMBER() OVER (
                        PARTITION BY se.retrieved_date, td.terminal_id 
                        ORDER BY td.retrieved_date DESC
                    ) as rn
                FROM status_events se
                LEFT JOIN terminal_details td ON 
                    td.retrieved_date <= se.retrieved_date
                    AND td.retrieved_date >= NOW() - INTERVAL '%s hours'
                WHERE td.terminal_id IS NOT NULL
            ),
            latest_status_per_event AS (
                SELECT 
                    event_time,
                    terminal_id,
                    COALESCE(fetched_status, 'OUT_OF_SERVICE') as status
                FROM atm_status_at_events 
                WHERE rn = 1
            )
            SELECT 
                event_time,
                COUNT(*) as total_atms,
                COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END) as count_available,
                COUNT(CASE WHEN status = 'WARNING' THEN 1 END) as count_warning,
                COUNT(CASE WHEN status = 'ZOMBIE' THEN 1 END) as count_zombie,
                COUNT(CASE WHEN status IN ('WOUNDED', 'HARD', 'CASH') THEN 1 END) as count_wounded,
                COUNT(CASE WHEN status IN ('OUT_OF_SERVICE', 'UNAVAILABLE') THEN 1 END) as count_out_of_service
            FROM latest_status_per_event
            GROUP BY event_time
            HAVING COUNT(*) > 0
            ORDER BY event_time ASC
        """ % (hours, hours)
        
        rows = await conn.fetch(query)
        
        # Enhanced fallback logic: if no data found for requested period, try shorter periods
        actual_hours_used = hours
        fallback_message = None
        
        if not rows:
            # Define fallback periods to try in descending order (shorter periods)
            fallback_periods = [720, 168, 72, 24, 12, 6, 1]  # 30 days, 7 days, 3 days, 1 day, 12h, 6h, 1h
            fallback_periods = [period for period in fallback_periods if period < hours]
            
            logger.info(f"No event data found for {hours}h period in overall trends, trying shorter fallback periods: {fallback_periods}")
            
            for fallback_hours in fallback_periods:
                fallback_query = """
                    WITH status_events AS (
                        SELECT DISTINCT retrieved_date
                        FROM terminal_details
                        WHERE retrieved_date >= NOW() - INTERVAL '%s hours'
                        ORDER BY retrieved_date ASC
                    ),
                    atm_status_at_events AS (
                        SELECT 
                            se.retrieved_date as event_time,
                            td.terminal_id,
                            td.fetched_status,
                            ROW_NUMBER() OVER (
                                PARTITION BY se.retrieved_date, td.terminal_id 
                                ORDER BY td.retrieved_date DESC
                            ) as rn
                        FROM status_events se
                        LEFT JOIN terminal_details td ON 
                            td.retrieved_date <= se.retrieved_date
                            AND td.retrieved_date >= NOW() - INTERVAL '%s hours'
                WHERE td.terminal_id IS NOT NULL
            ),
            latest_status_per_event AS (
                SELECT 
                    event_time,
                    terminal_id,
                    COALESCE(fetched_status, 'OUT_OF_SERVICE') as status
                FROM atm_status_at_events 
                WHERE rn = 1
            )
            SELECT 
                event_time,
                COUNT(*) as total_atms,
                COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END) as count_available,
                COUNT(CASE WHEN status = 'WARNING' THEN 1 END) as count_warning,
                COUNT(CASE WHEN status = 'ZOMBIE' THEN 1 END) as count_zombie,
                COUNT(CASE WHEN status IN ('WOUNDED', 'HARD', 'CASH') THEN 1 END) as count_wounded,
                COUNT(CASE WHEN status IN ('OUT_OF_SERVICE', 'UNAVAILABLE') THEN 1 END) as count_out_of_service
            FROM latest_status_per_event
            GROUP BY event_time
            HAVING COUNT(*) > 0
            ORDER BY event_time ASC
                """ % (fallback_hours, hours, hours, fallback_hours)
                
                rows = await conn.fetch(fallback_query)
                if rows:
                    actual_hours_used = fallback_hours
                    fallback_message = f"Data for {hours}h unavailable, showing {fallback_hours}h"
                    logger.info(f"Using fallback period of {fallback_hours}h for overall event trends")
                    break
        
        if not rows:
            logger.warning("No overall event trend data found even after fallback attempts")
            return TrendResponse(
                region_code="OVERALL",
                time_period=f"{hours} hours (no data)",
                trends=[],
                summary_stats={
                    'data_points': 0,
                    'time_range_hours': 0,
                    'requested_hours': hours,
                    'interval_minutes': None,  # Event-based, no fixed interval
                    'avg_availability': 0,
                    'min_availability': 0,
                    'max_availability': 0,
                    'first_reading': None,
                    'last_reading': None,
                    'data_source': 'terminal_details_events',
                    'total_atms_tracked': 0,
                    'fallback_message': 'No event data available for any period'
                }
            )
        
        # Convert query results to trend points
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
                timestamp=convert_to_dili_time(row['event_time']),
                status_counts=status_counts,
                availability_percentage=round(availability_pct, 2)
            ))
        
        # Calculate summary statistics
        summary_stats = {
            'data_points': len(trends),
            'time_range_hours': actual_hours_used,
            'requested_hours': hours,
            'interval_minutes': None,  # Event-based, no fixed interval
            'avg_availability': round(sum(availability_values) / len(availability_values), 2) if availability_values else 0,
            'min_availability': round(min(availability_values), 2) if availability_values else 0,
            'max_availability': round(max(availability_values), 2) if availability_values else 0,
            'first_reading': trends[0].timestamp.isoformat() if trends else None,
            'last_reading': trends[-1].timestamp.isoformat() if trends else None,
            'data_source': 'terminal_details_events',
            'total_atms_tracked': trends[-1].status_counts.total if trends else 0
        }
        
        # Add fallback message if applicable
        if fallback_message:
            summary_stats['fallback_message'] = fallback_message
        
        return TrendResponse(
            region_code="OVERALL", 
            time_period=f"{actual_hours_used} hours" + (f" (requested {hours}h)" if actual_hours_used != hours else "") + " (events)",
            trends=trends,
            summary_stats=summary_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching overall ATM event trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch overall event trend data")
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
    terminal_id: str = FastAPIPath(..., description="Terminal ID to get history for"),
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

# ============================================================================
# TERMINAL MAINTENANCE MANAGEMENT ENDPOINTS
# Implementation of PRD.md section 2.2.2 API endpoints
# ============================================================================

# ============================================================================
# TERMINAL MAINTENANCE MANAGEMENT ENDPOINTS
# Implementation of PRD.md section 2.2.2 API endpoints
# ============================================================================

# JWT Configuration (same as user_management_api.py)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

# Security dependency for JWT authentication
security = HTTPBearer()

# User database query support
class DatabaseConnectionError(Exception):
    """Exception raised when database connection fails"""
    pass

def execute_user_query(query: str, params: tuple = (), fetch: str = "all"):
    """
    Execute a query against the users database using psycopg2 (for compatibility with user management)
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # User management database configuration
    USER_DB_CONFIG = {
        'host': os.getenv('DB_HOST', '88.222.214.26'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'development_db'),
        'user': os.getenv('DB_USER', 'timlesdev'),
        'password': os.getenv('DB_PASSWORD', 'timlesdev')
    }
    
    try:
        conn = psycopg2.connect(**USER_DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
                
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise DatabaseConnectionError(f"Database query failed: {e}")

# JWT Authentication function (replaces mock authentication)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token and database lookup"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    query = "SELECT * FROM users WHERE id = %s AND is_active = true AND is_deleted = false"
    try:
        user = execute_user_query(query, (user_id,), fetch="one")
        
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert to dict and ensure compatibility with existing code
        user_dict = dict(user)
        return {
            "username": user_dict["username"],
            "role": UserRole(user_dict["role"].upper()),  # Convert role string to enum (uppercase)
            "user_id": str(user_dict["id"]),
            "full_name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
            "email": user_dict.get("email", ""),
            **user_dict  # Include all other user fields
        }
        
    except DatabaseConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Database connection error",
        )
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while authenticating user",
        )

# Optional authentication function (for endpoints that work with or without auth)
async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise return None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        # Get user from database
        query = "SELECT * FROM users WHERE id = %s AND is_active = true AND is_deleted = false"
        user = execute_user_query(query, (user_id,), fetch="one")
        
        if user is None:
            return None
        
        # Convert to dict and ensure compatibility with existing code
        user_dict = dict(user)
        return {
            "username": user_dict["username"],
            "role": UserRole(user_dict["role"].upper()),  # Convert role string to enum (uppercase)
            "user_id": str(user_dict["id"]),
            "full_name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
            "email": user_dict.get("email", ""),
            **user_dict  # Include all other user fields
        }
        
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None

# Mock authentication and authorization functions (integrate with your auth system)
# DEPRECATED: Replaced with actual JWT authentication above
# DEPRECATED: Replaced with actual JWT authentication above
async def get_current_user_DEPRECATED() -> Dict[str, Any]:
    """
    DEPRECATED: Mock function to get current user. 
    Replaced with actual JWT authentication function above.
    """
    # For testing purposes, return a mock admin user
    return {
        "username": "test_admin",
        "role": UserRole.ADMIN,
        "user_id": "admin_123",
        "full_name": "Test Administrator"
    }

def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based authorization.
    Creates a dependency that checks if the current user has one of the allowed roles.
    """
    async def check_roles(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get('role')
        
        # Ensure user_role is a UserRole enum
        if isinstance(user_role, str):
            try:
                user_role = UserRole(user_role.upper())  # Convert to uppercase for enum matching
            except ValueError:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Invalid user role: {user_role}"
                )
        
        if user_role not in allowed_roles:
            allowed_role_names = [role.value for role in allowed_roles]
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {allowed_role_names}. Current role: {user_role.value if user_role else 'None'}"
            )
        
        return current_user
    
    return check_roles

# Create specific role dependencies for maintenance endpoints
require_operator_or_higher = require_roles([UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPERADMIN])
require_admin_or_higher = require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])
require_superadmin = require_roles([UserRole.SUPERADMIN])

# Utility functions for maintenance operations
async def get_maintenance_connection():
    """Get database connection for maintenance operations"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return await db_pool.acquire()

async def release_maintenance_connection(conn):
    """Release database connection"""
    if conn and db_pool:
        await db_pool.release(conn)

async def verify_terminal_exists(conn, terminal_id: str) -> bool:
    """Verify that a terminal exists in the system"""
    try:
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM terminal_details WHERE terminal_id = $1)",
            terminal_id
        )
        return bool(result) if result is not None else False
    except Exception:
        # If terminal_details table doesn't exist, skip validation for now
        return True

async def calculate_duration_hours(start_datetime: datetime, end_datetime: Optional[datetime]) -> Optional[float]:
    """Calculate duration in hours between start and end datetime"""
    if end_datetime is None:
        return None
    delta = end_datetime - start_datetime
    return round(delta.total_seconds() / 3600, 2)

async def get_terminal_info(conn, terminal_id: str) -> Dict[str, Optional[str]]:
    """Get terminal name and location from terminal_details"""
    try:
        result = await conn.fetchrow(
            """
            SELECT terminal_name, location 
            FROM terminal_details 
            WHERE terminal_id = $1
            """,
            terminal_id
        )
        if result:
            return {
                "terminal_name": result['terminal_name'],
                "location": result['location']
            }
    except Exception:
        # If terminal_details table doesn't exist, return None values
        pass
    
    return {"terminal_name": None, "location": None}

# File upload utilities
try:
    import aiofiles  # Optional: pip install aiofiles for async file operations
except ImportError:
    aiofiles = None  # Fallback to synchronous file operations

async def save_uploaded_file(file: UploadFile, maintenance_id: str) -> MaintenanceImage:
    """Save uploaded file and return image metadata"""
    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    # Validate file type
    file_ext = PathLib(file.filename).suffix.lower()
    if file_ext not in UPLOAD_CONFIG['allowed_extensions']:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(UPLOAD_CONFIG['allowed_extensions'])}"
        )
    
    # Check file size
    content = await file.read()
    file_size = len(content)
    
    if file_size > UPLOAD_CONFIG['max_file_size']:
        raise HTTPException(
            status_code=400,
            detail=f"File size {file_size} bytes exceeds maximum allowed size of {UPLOAD_CONFIG['max_file_size']} bytes"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = PathLib(UPLOAD_CONFIG['upload_directory']) / maintenance_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    image_id = str(uuid.uuid4())
    filename = f"{image_id}{file_ext}"
    file_path = upload_dir / filename
    
    # Save file (use regular file operations if aiofiles not available)
    if aiofiles:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    else:
        with open(file_path, 'wb') as f:
            f.write(content)
    
    return MaintenanceImage(
        image_id=image_id,
        filename=file.filename,
        file_path=str(file_path),
        uploaded_at=datetime.now(),
        file_size=file_size
    )

# Maintenance CRUD Endpoints

@app.get("/api/v1/maintenance", response_model=MaintenanceListResponse, tags=["Terminal Maintenance"])
async def list_maintenance_records(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Records per page"),
    terminal_id: Optional[str] = Query(None, description="Filter by terminal ID"),
    status: Optional[MaintenanceStatusEnum] = Query(None, description="Filter by status"),
    maintenance_type: Optional[MaintenanceTypeEnum] = Query(None, description="Filter by type"),
    priority: Optional[MaintenancePriorityEnum] = Query(None, description="Filter by priority"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    start_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)  # Optional authentication for testing
):
    """
    List maintenance records with filtering and pagination.
    All authenticated users can read maintenance records.
    """
    conn = await get_maintenance_connection()
    try:
        # Build WHERE clause based on filters
        where_conditions = []
        params = []
        param_count = 0
        
        if terminal_id:
            param_count += 1
            where_conditions.append(f"terminal_id = ${param_count}")
            params.append(terminal_id)
        
        if status:
            param_count += 1
            where_conditions.append(f"status = ${param_count}")
            params.append(status.value)
        
        if maintenance_type:
            param_count += 1
            where_conditions.append(f"maintenance_type = ${param_count}")
            params.append(maintenance_type.value)
        
        if priority:
            param_count += 1
            where_conditions.append(f"priority = ${param_count}")
            params.append(priority.value)
        
        if created_by:
            param_count += 1
            where_conditions.append(f"created_by = ${param_count}")
            params.append(created_by)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                param_count += 1
                where_conditions.append(f"start_datetime >= ${param_count}")
                params.append(start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                param_count += 1
                where_conditions.append(f"start_datetime <= ${param_count}")
                params.append(end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # Count total records
        count_query = f"SELECT COUNT(*) FROM terminal_maintenance {where_clause}"
        total_count = await conn.fetchval(count_query, *params)
        
        # Calculate pagination
        offset = (page - 1) * per_page
        
        # Fetch records
        query = f"""
            SELECT id, terminal_id, start_datetime, end_datetime, 
                   problem_description, solution_description, 
                   maintenance_type, priority, status, images,
                   created_by, created_at, updated_at
            FROM terminal_maintenance 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([per_page, offset])
        
        records = await conn.fetch(query, *params)
        
        # Convert to response models
        maintenance_records = []
        for record in records:
            # Get terminal info
            terminal_info = await get_terminal_info(conn, record['terminal_id'])
            
            # Calculate duration
            duration_hours = await calculate_duration_hours(
                record['start_datetime'], 
                record['end_datetime']
            )
            
            # Parse images JSON
            images = []
            if record['images']:
                try:
                    images_data = json.loads(record['images']) if isinstance(record['images'], str) else record['images']
                    images = [MaintenanceImage(**img) for img in images_data]
                except (json.JSONDecodeError, TypeError):
                    images = []
            
            maintenance_record = MaintenanceRecord(
                id=str(record['id']),
                terminal_id=record['terminal_id'],
                terminal_name=terminal_info['terminal_name'],
                location=terminal_info['location'],
                start_datetime=convert_to_dili_time(record['start_datetime']),
                end_datetime=convert_to_dili_time(record['end_datetime']) if record['end_datetime'] else None,
                problem_description=record['problem_description'],
                solution_description=record['solution_description'],
                maintenance_type=record['maintenance_type'],
                priority=record['priority'],
                status=record['status'],
                images=images,
                duration_hours=duration_hours,
                created_by=record['created_by'],
                created_at=convert_to_dili_time(record['created_at']),
                updated_at=convert_to_dili_time(record['updated_at'])
            )
            maintenance_records.append(maintenance_record)
        
        # Prepare filters applied
        filters_applied = {}
        if terminal_id: filters_applied['terminal_id'] = terminal_id
        if status: filters_applied['status'] = status.value
        if maintenance_type: filters_applied['maintenance_type'] = maintenance_type.value
        if priority: filters_applied['priority'] = priority.value
        if created_by: filters_applied['created_by'] = created_by
        if start_date: filters_applied['start_date'] = start_date
        if end_date: filters_applied['end_date'] = end_date
        
        return MaintenanceListResponse(
            maintenance_records=maintenance_records,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_more=(offset + len(records)) < total_count,
            filters_applied=filters_applied
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing maintenance records: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve maintenance records")
    finally:
        await release_maintenance_connection(conn)

@app.post("/api/v1/maintenance", response_model=MaintenanceRecord, status_code=201, tags=["Terminal Maintenance"])
async def create_maintenance_record(
    maintenance: MaintenanceCreate,
    current_user: Dict[str, Any] = Depends(require_operator_or_higher)
):
    """
    Create a new maintenance record.
    Requires operator, admin, or superadmin role.
    """
    conn = await get_maintenance_connection()
    try:
        # Verify terminal exists
        if not await verify_terminal_exists(conn, maintenance.terminal_id):
            raise HTTPException(status_code=404, detail=f"Terminal {maintenance.terminal_id} not found")
        
        # Insert maintenance record
        record_id = await conn.fetchval(
            """
            INSERT INTO terminal_maintenance (
                terminal_id, start_datetime, end_datetime, 
                problem_description, solution_description,
                maintenance_type, priority, status, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            maintenance.terminal_id,
            maintenance.start_datetime,
            maintenance.end_datetime,
            maintenance.problem_description,
            maintenance.solution_description,
            maintenance.maintenance_type.value,
            maintenance.priority.value,
            maintenance.status.value,
            current_user['username']
        )
        
        # Fetch the created record
        record = await conn.fetchrow(
            """
            SELECT id, terminal_id, start_datetime, end_datetime, 
                   problem_description, solution_description, 
                   maintenance_type, priority, status, images,
                   created_by, created_at, updated_at
            FROM terminal_maintenance WHERE id = $1
            """,
            record_id
        )
        
        # Get terminal info
        terminal_info = await get_terminal_info(conn, record['terminal_id'])
        
        # Calculate duration
        duration_hours = await calculate_duration_hours(
            record['start_datetime'], 
            record['end_datetime']
        )
        
        return MaintenanceRecord(
            id=str(record['id']),
            terminal_id=record['terminal_id'],
            terminal_name=terminal_info['terminal_name'],
            location=terminal_info['location'],
            start_datetime=convert_to_dili_time(record['start_datetime']),
            end_datetime=convert_to_dili_time(record['end_datetime']) if record['end_datetime'] else None,
            problem_description=record['problem_description'],
            solution_description=record['solution_description'],
            maintenance_type=record['maintenance_type'],
            priority=record['priority'],
            status=record['status'],
            images=[],  # No images initially
            duration_hours=duration_hours,
            created_by=record['created_by'],
            created_at=convert_to_dili_time(record['created_at']),
            updated_at=convert_to_dili_time(record['updated_at'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating maintenance record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create maintenance record")
    finally:
        await release_maintenance_connection(conn)

@app.get("/api/v1/maintenance/{maintenance_id}", response_model=MaintenanceRecord, tags=["Terminal Maintenance"])
async def get_maintenance_record(
    maintenance_id: str = FastAPIPath(..., description="Maintenance record ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)  # All authenticated users can read
):
    """
    Get a specific maintenance record by ID.
    All authenticated users can read maintenance records.
    """
    conn = await get_maintenance_connection()
    try:
        # Fetch the record
        record = await conn.fetchrow(
            """
            SELECT id, terminal_id, start_datetime, end_datetime, 
                   problem_description, solution_description, 
                   maintenance_type, priority, status, images,
                   created_by, created_at, updated_at
            FROM terminal_maintenance WHERE id = $1
            """,
            maintenance_id
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        # Get terminal info
        terminal_info = await get_terminal_info(conn, record['terminal_id'])
        
        # Calculate duration
        duration_hours = await calculate_duration_hours(
            record['start_datetime'], 
            record['end_datetime']
        )
        
        # Parse images JSON
        images = []
        if record['images']:
            try:
                images_data = json.loads(record['images']) if isinstance(record['images'], str) else record['images']
                images = [MaintenanceImage(**img) for img in images_data]
            except (json.JSONDecodeError, TypeError):
                images = []
        
        return MaintenanceRecord(
            id=str(record['id']),
            terminal_id=record['terminal_id'],
            terminal_name=terminal_info['terminal_name'],
            location=terminal_info['location'],
            start_datetime=convert_to_dili_time(record['start_datetime']),
            end_datetime=convert_to_dili_time(record['end_datetime']) if record['end_datetime'] else None,
            problem_description=record['problem_description'],
            solution_description=record['solution_description'],
            maintenance_type=record['maintenance_type'],
            priority=record['priority'],
            status=record['status'],
            images=images,
            duration_hours=duration_hours,
            created_by=record['created_by'],
            created_at=convert_to_dili_time(record['created_at']),
            updated_at=convert_to_dili_time(record['updated_at'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving maintenance record: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve maintenance record")
    finally:
        await release_maintenance_connection(conn)

@app.put("/api/v1/maintenance/{maintenance_id}", response_model=MaintenanceRecord, tags=["Terminal Maintenance"])
async def update_maintenance_record(
    maintenance: MaintenanceUpdate,
    maintenance_id: str = FastAPIPath(..., description="Maintenance record ID"),
    current_user: Dict[str, Any] = Depends(require_operator_or_higher)
):
    """
    Update a maintenance record.
    Requires operator, admin, or superadmin role.
    """
    conn = await get_maintenance_connection()
    try:
        # Check if record exists
        existing = await conn.fetchval(
            "SELECT id FROM terminal_maintenance WHERE id = $1",
            maintenance_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        param_count = 0
        
        for field, value in maintenance.dict(exclude_unset=True).items():
            if value is not None:
                param_count += 1
                if field.endswith('_datetime') and isinstance(value, datetime):
                    update_fields.append(f"{field} = ${param_count}")
                    params.append(value)
                elif isinstance(value, Enum):
                    update_fields.append(f"{field} = ${param_count}")
                    params.append(value.value)
                else:
                    update_fields.append(f"{field} = ${param_count}")
                    params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at
        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.now())
        
        # Add WHERE clause parameter
        param_count += 1
        params.append(maintenance_id)
        
        update_query = f"""
            UPDATE terminal_maintenance 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
        """
        
        await conn.execute(update_query, *params)
        
        # Fetch updated record
        return await get_maintenance_record(maintenance_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating maintenance record: {e}")
        raise HTTPException(status_code=500, detail="Failed to update maintenance record")
    finally:
        await release_maintenance_connection(conn)

@app.delete("/api/v1/maintenance/{maintenance_id}", tags=["Terminal Maintenance"])
async def delete_maintenance_record(
    maintenance_id: str = FastAPIPath(..., description="Maintenance record ID"),
    current_user: Dict[str, Any] = Depends(require_admin_or_higher)
):
    """
    Delete a maintenance record.
    Requires admin or superadmin role.
    """
    conn = await get_maintenance_connection()
    try:
        # Check if record exists and get image info for cleanup
        record = await conn.fetchrow(
            "SELECT id, images FROM terminal_maintenance WHERE id = $1",
            maintenance_id
        )
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        # Delete associated image files
        if record['images']:
            try:
                images_data = json.loads(record['images']) if isinstance(record['images'], str) else record['images']
                for img_data in images_data:
                    file_path = PathLib(img_data.get('file_path', ''))
                    if file_path.exists():
                        file_path.unlink()
            except Exception as e:
                logger.warning(f"Error cleaning up image files: {e}")
        
        # Delete the record
        deleted_count = await conn.fetchval(
            "DELETE FROM terminal_maintenance WHERE id = $1",
            maintenance_id
        )
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        return {"message": "Maintenance record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting maintenance record: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete maintenance record")
    finally:
        await release_maintenance_connection(conn)

@app.get("/api/v1/atm/{terminal_id}/maintenance", response_model=MaintenanceListResponse, tags=["Terminal Maintenance"])
async def get_atm_maintenance_history(
    terminal_id: str = FastAPIPath(..., description="Terminal ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Records per page"),
    current_user: Dict[str, Any] = Depends(get_current_user)  # All authenticated users can read
):
    """
    Get maintenance history for a specific ATM terminal.
    All authenticated users can read maintenance records.
    """
    conn = await get_maintenance_connection()
    try:
        # Verify terminal exists
        if not await verify_terminal_exists(conn, terminal_id):
            raise HTTPException(status_code=404, detail=f"Terminal {terminal_id} not found")
        
        # Count total records for this terminal
        total_count = await conn.fetchval(
            "SELECT COUNT(*) FROM terminal_maintenance WHERE terminal_id = $1",
            terminal_id
        )
        
        # Calculate pagination
        offset = (page - 1) * per_page
        
        # Fetch records
        records = await conn.fetch(
            """
            SELECT id, terminal_id, start_datetime, end_datetime, 
                   problem_description, solution_description, 
                   maintenance_type, priority, status, images,
                   created_by, created_at, updated_at
            FROM terminal_maintenance 
            WHERE terminal_id = $1
            ORDER BY start_datetime DESC
            LIMIT $2 OFFSET $3
            """,
            terminal_id, per_page, offset
        )
        
        # Convert to response models
        maintenance_records = []
        terminal_info = await get_terminal_info(conn, terminal_id)
        
        for record in records:
            # Calculate duration
            duration_hours = await calculate_duration_hours(
                record['start_datetime'], 
                record['end_datetime']
            )
            
            # Parse images JSON
            images = []
            if record['images']:
                try:
                    images_data = json.loads(record['images']) if isinstance(record['images'], str) else record['images']
                    images = [MaintenanceImage(**img) for img in images_data]
                except (json.JSONDecodeError, TypeError):
                    images = []
            
            maintenance_record = MaintenanceRecord(
                id=str(record['id']),
                terminal_id=record['terminal_id'],
                terminal_name=terminal_info['terminal_name'],
                location=terminal_info['location'],
                start_datetime=convert_to_dili_time(record['start_datetime']),
                end_datetime=convert_to_dili_time(record['end_datetime']) if record['end_datetime'] else None,
                problem_description=record['problem_description'],
                solution_description=record['solution_description'],
                maintenance_type=record['maintenance_type'],
                priority=record['priority'],
                status=record['status'],
                images=images,
                duration_hours=duration_hours,
                created_by=record['created_by'],
                created_at=convert_to_dili_time(record['created_at']),
                updated_at=convert_to_dili_time(record['updated_at'])
            )
            maintenance_records.append(maintenance_record)
        
        return MaintenanceListResponse(
            maintenance_records=maintenance_records,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_more=(offset + len(records)) < total_count,
            filters_applied={"terminal_id": terminal_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ATM maintenance history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ATM maintenance history")
    finally:
        await release_maintenance_connection(conn)

@app.post("/api/v1/maintenance/{maintenance_id}/images", tags=["Terminal Maintenance"])
async def upload_maintenance_images(
    files: List[UploadFile],
    maintenance_id: str = FastAPIPath(..., description="Maintenance record ID"),
    current_user: Dict[str, Any] = Depends(require_operator_or_higher)
):
    """
    Upload images for a maintenance record.
    Requires operator, admin, or superadmin role.
    """
    conn = await get_maintenance_connection()
    try:
        # Check if maintenance record exists
        record = await conn.fetchrow(
            "SELECT id, images FROM terminal_maintenance WHERE id = $1",
            maintenance_id
        )
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        # Check current image count
        current_images = []
        if record['images']:
            try:
                current_images = json.loads(record['images']) if isinstance(record['images'], str) else record['images']
            except (json.JSONDecodeError, TypeError):
                current_images = []
        
        if len(current_images) + len(files) > UPLOAD_CONFIG['max_files_per_record']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot upload {len(files)} files. Maximum {UPLOAD_CONFIG['max_files_per_record']} files per record allowed."
            )
        
        # Save uploaded files
        uploaded_images = []
        for file in files:
            try:
                image = await save_uploaded_file(file, maintenance_id)
                uploaded_images.append(image)
            except Exception as e:
                # Clean up any files that were already saved
                for img in uploaded_images:
                    try:
                        PathLib(img.file_path).unlink()
                    except:
                        pass
                raise e
        
        # Update database with new image info
        all_images = current_images + [img.model_dump(mode='json') for img in uploaded_images]
        
        await conn.execute(
            "UPDATE terminal_maintenance SET images = $1, updated_at = $2 WHERE id = $3",
            json.dumps(all_images),
            datetime.now(),
            maintenance_id
        )
        
        return {
            "message": f"Successfully uploaded {len(uploaded_images)} images",
            "uploaded_images": uploaded_images,
            "total_images": len(all_images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading maintenance images: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload images")
    finally:
        await release_maintenance_connection(conn)

@app.get("/api/v1/maintenance/images/{maintenance_id}/{image_id}", tags=["Terminal Maintenance"])
async def get_maintenance_image(
    maintenance_id: str = FastAPIPath(..., description="Maintenance record ID"),
    image_id: str = FastAPIPath(..., description="Image ID")
):
    """
    Serve a maintenance image file.
    Returns the actual image file.
    """
    try:
        # Construct the file path based on the upload structure
        upload_dir = PathLib(UPLOAD_CONFIG['upload_directory']) / maintenance_id
        
        # Find the file with the matching image_id (could have different extensions)
        image_file = None
        for ext in UPLOAD_CONFIG['allowed_extensions']:
            potential_file = upload_dir / f"{image_id}{ext}"
            if potential_file.exists():
                image_file = potential_file
                break
        
        if not image_file:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Return the file
        return FileResponse(
            path=str(image_file),
            media_type=f"image/{image_file.suffix[1:]}",  # Use proper MIME type
            headers={
                "Content-Disposition": "inline",  # Display inline instead of attachment
                "Access-Control-Allow-Origin": "*",  # Allow all origins for images
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving maintenance image: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

@app.delete("/api/v1/maintenance/{maintenance_id}/images/{image_id}", tags=["Terminal Maintenance"])
async def delete_maintenance_image(
    maintenance_id: str = FastAPIPath(..., description="Maintenance record ID"),
    image_id: str = FastAPIPath(..., description="Image ID to delete"),
    current_user: Dict[str, Any] = Depends(require_operator_or_higher)
):
    """
    Delete a specific image from a maintenance record.
    Requires operator, admin, or superadmin role.
    """
    conn = await get_maintenance_connection()
    try:
        # Get current images
        record = await conn.fetchrow(
            "SELECT id, images FROM terminal_maintenance WHERE id = $1",
            maintenance_id
        )
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        current_images = []
        if record['images']:
            try:
                current_images = json.loads(record['images']) if isinstance(record['images'], str) else record['images']
            except (json.JSONDecodeError, TypeError):
                current_images = []
        
        # Find and remove the image
        image_to_delete = None
        updated_images = []
        
        for img_data in current_images:
            if img_data.get('image_id') == image_id:
                image_to_delete = img_data
            else:
                updated_images.append(img_data)
        
        if not image_to_delete:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete physical file
        try:
            file_path = PathLib(image_to_delete['file_path'])
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Error deleting physical file: {e}")
        
        # Update database
        await conn.execute(
            "UPDATE terminal_maintenance SET images = $1, updated_at = $2 WHERE id = $3",
            json.dumps(updated_images),
            datetime.now(),
            maintenance_id
        )
        
        return {
            "message": "Image deleted successfully",
            "deleted_image_id": image_id,
            "remaining_images": len(updated_images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting maintenance image: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")
    finally:
        await release_maintenance_connection(conn)

# ============================================================================
# END TERMINAL MAINTENANCE MANAGEMENT ENDPOINTS
# ============================================================================

# Main execution block
if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    reload = os.getenv('RELOAD', 'true').lower() == 'true'
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    
    logger.info("=" * 60)
    logger.info("🚀 Starting ATM Dashboard FastAPI Server")
    logger.info("=" * 60)
    logger.info(f"Server: {host}:{port}")
    logger.info(f"Reload: {reload}")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"API Documentation: http://{host}:{port}/docs")
    logger.info(f"Alternative Docs: http://{host}:{port}/redoc")
    logger.info(f"Health Check: http://{host}:{port}/api/v1/health")
    logger.info("=" * 60)
    
    try:
        # Start the server
        uvicorn.run(
            "api_option_2_fastapi_fixed:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
