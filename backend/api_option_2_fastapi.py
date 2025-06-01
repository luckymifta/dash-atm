#!/usr/bin/env python3
"""
FastAPI REST API for ATM Status Counts - Option 2

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
pip install fastapi uvicorn psycopg2-binary python-multipart

Usage:
uvicorn api_option_2_fastapi:app --host 0.0.0.0 --port 8000 --reload

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
import pytz

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('atm_fastapi.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ATM_FastAPI')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'atm_monitor'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

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
    availability_percentage: float = Field(..., ge=0, le=100, description="Availability percentage")
    last_updated: datetime = Field(..., description="Last update timestamp")
    health_status: HealthStatusEnum = Field(..., description="Overall health classification")

class ATMSummaryResponse(BaseModel):
    total_atms: int = Field(..., ge=0, description="Total ATMs across all regions")
    status_counts: ATMStatusCounts
    overall_availability: float = Field(..., ge=0, le=100, description="Overall availability percentage")
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
    availability_percentage: float = Field(..., ge=0, le=100)

class TrendResponse(BaseModel):
    region_code: str
    time_period: str
    trends: List[TrendPoint]
    summary_stats: Dict[str, Any]

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "Request successful"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_connected: bool
    api_version: str = "2.0.0"
    uptime_seconds: float

# FastAPI app initialization
app = FastAPI(
    title="ATM Status Monitoring API",
    description="FastAPI-based REST API for ATM status counts and monitoring",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global variables
app_start_time = datetime.utcnow()
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

async def get_db_connection():
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

async def release_db_connection(conn):
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

@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup"""
    logger.info("Starting ATM FastAPI application...")
    await create_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

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
        
        uptime = (datetime.utcnow() - app_start_time).total_seconds()
        
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
    """
    conn = await get_db_connection()
    
    try:
        if table_type == TableTypeEnum.LEGACY or table_type == TableTypeEnum.BOTH:
            # Query legacy table
            query = """
                WITH latest_data AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        date_creation
                    FROM regional_atm_counts
                    ORDER BY region_code, date_creation DESC
                )
                SELECT 
                    SUM(count_available) as total_available,
                    SUM(count_warning) as total_warning,
                    SUM(count_zombie) as total_zombie,
                    SUM(count_wounded) as total_wounded,
                    SUM(count_out_of_service) as total_out_of_service,
                    SUM(total_atms_in_region) as total_atms,
                    COUNT(DISTINCT region_code) as total_regions,
                    MAX(date_creation) as last_updated
                FROM latest_data
            """
            
            row = await conn.fetchrow(query)
            
        elif table_type == TableTypeEnum.NEW:
            # Query new table
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
                    SUM(count_available) as total_available,
                    SUM(count_warning) as total_warning,
                    SUM(count_zombie) as total_zombie,
                    SUM(count_wounded) as total_wounded,
                    SUM(count_out_of_service) as total_out_of_service,
                    SUM(total_atms_in_region) as total_atms,
                    COUNT(DISTINCT region_code) as total_regions,
                    MAX(retrieval_timestamp) as last_updated
                FROM latest_data
            """
            
            row = await conn.fetchrow(query)
        
        if not row or row['total_atms'] is None:
            raise HTTPException(status_code=404, detail="No ATM data found")
        
        total_atms = row['total_atms'] or 0
        available = row['total_available'] or 0
        availability_percentage = (available / total_atms * 100) if total_atms > 0 else 0
        
        status_counts = ATMStatusCounts(
            available=available,
            warning=row['total_warning'] or 0,
            zombie=row['total_zombie'] or 0,
            wounded=row['total_wounded'] or 0,
            out_of_service=row['total_out_of_service'] or 0,
            total=total_atms
        )
        
        return ATMSummaryResponse(
            total_atms=total_atms,
            status_counts=status_counts,
            overall_availability=round(availability_percentage, 2),
            total_regions=row['total_regions'] or 0,
            last_updated=row['last_updated'] or datetime.utcnow(),
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
    """
    conn = await get_db_connection()
    
    try:
        # Build query based on table type
        if table_type == TableTypeEnum.LEGACY:
            base_query = """
                WITH latest_regional AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        date_creation
                    FROM regional_atm_counts
                    ORDER BY region_code, date_creation DESC
                )
                SELECT * FROM latest_regional
            """
        else:
            base_query = """
                WITH latest_regional AS (
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        retrieval_timestamp as date_creation
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                )
                SELECT * FROM latest_regional
            """
        
        # Add region filter if specified
        if region_code:
            base_query += f" WHERE region_code = '{region_code}'"
        
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
            total_region = row['total_atms_in_region'] or 0
            availability_pct = (available / total_region * 100) if total_region > 0 else 0
            
            status_counts = ATMStatusCounts(
                available=available,
                warning=row['count_warning'] or 0,
                zombie=row['count_zombie'] or 0,
                wounded=row['count_wounded'] or 0,
                out_of_service=row['count_out_of_service'] or 0,
                total=total_region
            )
            
            # Update summary totals
            total_summary['available'] += available
            total_summary['warning'] += (row['count_warning'] or 0)
            total_summary['zombie'] += (row['count_zombie'] or 0)
            total_summary['wounded'] += (row['count_wounded'] or 0)
            total_summary['out_of_service'] += (row['count_out_of_service'] or 0)
            total_summary['total'] += total_region
            
            if not last_updated or row['date_creation'] > last_updated:
                last_updated = row['date_creation']
            
            regional_data.append(RegionalData(
                region_code=row['region_code'],
                status_counts=status_counts,
                availability_percentage=round(availability_pct, 2),
                last_updated=row['date_creation'] or datetime.utcnow(),
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
            last_updated=last_updated or datetime.utcnow()
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
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back (1-168)"),
    table_type: TableTypeEnum = Query(TableTypeEnum.LEGACY, description="Database table to query"),
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get historical trends for a specific region
    
    Returns time-series data showing ATM status changes over time.
    """
    conn = await get_db_connection()
    
    try:
        if table_type == TableTypeEnum.LEGACY:
            query = """
                SELECT 
                    date_creation, count_available, count_warning, count_zombie,
                    count_wounded, count_out_of_service, total_atms_in_region
                FROM regional_atm_counts
                WHERE region_code = $1 
                    AND date_creation >= NOW() - INTERVAL '%s hours'
                ORDER BY date_creation ASC
            """ % hours
        else:
            query = """
                SELECT 
                    retrieval_timestamp as date_creation, count_available, count_warning, 
                    count_zombie, count_wounded, count_out_of_service, total_atms_in_region
                FROM regional_data
                WHERE region_code = $1 
                    AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY retrieval_timestamp ASC
            """ % hours
        
        rows = await conn.fetch(query, region_code)
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No trend data found for region {region_code}")
        
        trends = []
        availability_values = []
        
        for row in rows:
            available = row['count_available'] or 0
            total = row['total_atms_in_region'] or 0
            availability_pct = (available / total * 100) if total > 0 else 0
            availability_values.append(availability_pct)
            
            status_counts = ATMStatusCounts(
                available=available,
                warning=row['count_warning'] or 0,
                zombie=row['count_zombie'] or 0,
                wounded=row['count_wounded'] or 0,
                out_of_service=row['count_out_of_service'] or 0,
                total=total
            )
            
            trends.append(TrendPoint(
                timestamp=row['date_creation'],
                status_counts=status_counts,
                availability_percentage=round(availability_pct, 2)
            ))
        
        # Calculate summary statistics
        summary_stats = {
            'data_points': len(trends),
            'time_range_hours': hours,
            'avg_availability': round(sum(availability_values) / len(availability_values), 2) if availability_values else 0,
            'min_availability': round(min(availability_values), 2) if availability_values else 0,
            'max_availability': round(max(availability_values), 2) if availability_values else 0,
            'first_reading': trends[0].timestamp if trends else None,
            'last_reading': trends[-1].timestamp if trends else None
        }
        
        return TrendResponse(
            region_code=region_code,
            time_period=f"{hours} hours",
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
    
    try:
        result = {"data_sources": []}
        
        # Legacy table data
        if table_type in [TableTypeEnum.LEGACY, TableTypeEnum.BOTH]:
            try:
                legacy_query = """
                    SELECT DISTINCT ON (region_code)
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        date_creation
                    FROM regional_atm_counts
                    ORDER BY region_code, date_creation DESC
                """
                legacy_rows = await conn.fetch(legacy_query)
                
                legacy_data = []
                for row in legacy_rows:
                    legacy_data.append({
                        'region_code': row['region_code'],
                        'count_available': row['count_available'],
                        'count_warning': row['count_warning'],
                        'count_zombie': row['count_zombie'],
                        'count_wounded': row['count_wounded'],
                        'count_out_of_service': row['count_out_of_service'],
                        'total_atms_in_region': row['total_atms_in_region'],
                        'last_updated': row['date_creation']
                    })
                
                result["data_sources"].append({
                    "table": "regional_atm_counts",
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
                        region_code, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region,
                        retrieval_timestamp, raw_regional_data
                    FROM regional_data
                    ORDER BY region_code, retrieval_timestamp DESC
                """
                new_rows = await conn.fetch(new_query)
                
                new_data = []
                for row in new_rows:
                    new_data.append({
                        'region_code': row['region_code'],
                        'count_available': row['count_available'],
                        'count_warning': row['count_warning'],
                        'count_zombie': row['count_zombie'],
                        'count_wounded': row['count_wounded'],
                        'count_out_of_service': row['count_out_of_service'],
                        'total_atms_in_region': row['total_atms_in_region'],
                        'last_updated': row['retrieval_timestamp'],
                        'raw_data': row['raw_regional_data']
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
                    SELECT 
                        terminal_id, location, issue_state_name, serial_number,
                        fetched_status, retrieved_date, fault_data, metadata
                    FROM terminal_details
                    WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
                    ORDER BY retrieved_date DESC
                    LIMIT 100
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
                        'retrieved_date': row['retrieved_date'],
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
            "timestamp": datetime.utcnow(),
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

# Custom exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )

if __name__ == "__main__":
    uvicorn.run(
        "api_option_2_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
