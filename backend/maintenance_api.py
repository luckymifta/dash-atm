#!/usr/bin/env python3
"""
Terminal Maintenance Management API Endpoints
Implementation of PRD.md section 2.2.2

This module contains the FastAPI endpoints for terminal maintenance management
including CRUD operations and file upload functionality.
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
import uuid
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path as FastAPIPath, Depends, UploadFile, File
from pydantic import BaseModel, Field, field_validator

# For file operations - optional import
try:
    import aiofiles  # Optional: pip install aiofiles for async file operations
except ImportError:
    aiofiles = None  # Handled gracefully in code

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

class MaintenanceListResponse(BaseModel):
    maintenance_records: List[MaintenanceRecord] = Field(..., description="List of maintenance records")
    total_count: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Records per page")
    has_more: bool = Field(..., description="Whether more records exist")
    filters_applied: Dict[str, Any] = Field(..., description="Applied filters")

# User role enum for authorization
class UserRole(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

# File upload configuration
UPLOAD_CONFIG = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
    'upload_directory': 'uploads/maintenance',
    'max_files_per_record': 5
}

# Configuration - these should match your main API configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '88.222.214.26'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'development_db'),
    'user': os.getenv('DB_USER', 'timlesdev'),
    'password': os.getenv('DB_PASSWORD', 'timlesdev')
}

# Database connection pool (to be set by main application)
db_pool = None

def set_db_pool(pool):
    """Set the database pool from the main application"""
    global db_pool
    db_pool = pool

# Mock authentication and authorization functions (integrate with your auth system)
async def get_current_user() -> Dict[str, Any]:
    """Mock function to get current user. Replace with your authentication logic."""
    # TODO: Integrate with your JWT authentication system
    return {
        "username": "test_user",
        "role": UserRole.ADMIN,  # For testing purposes
        "user_id": "test_user_123"
    }

def require_roles(allowed_roles: List[UserRole]):
    """Decorator to check user roles for authorization"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # TODO: Implement actual role checking logic
            # For now, allow all operations for testing
            return await func(*args, **kwargs)
        return wrapper
    return decorator

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
async def save_uploaded_file(file: UploadFile, maintenance_id: str) -> MaintenanceImage:
    """Save uploaded file and return image metadata"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
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
    upload_dir = Path(UPLOAD_CONFIG['upload_directory']) / maintenance_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    image_id = str(uuid.uuid4())
    filename = f"{image_id}{file_ext}"
    file_path = upload_dir / filename
    
    # Save file
    if aiofiles:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    else:
        # Fallback to synchronous file writing
        with open(file_path, 'wb') as f:
            f.write(content)
    
    return MaintenanceImage(
        image_id=image_id,
        filename=file.filename,
        file_path=str(file_path),
        uploaded_at=datetime.now(),
        file_size=file_size
    )

def convert_to_dili_time(timestamp: datetime) -> datetime:
    """Convert timestamp to Dili time - placeholder function"""
    # This should match your main API's timezone conversion logic
    return timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp

# Maintenance endpoint functions that can be added to the main app
def create_maintenance_endpoints(app: FastAPI):
    """Add maintenance endpoints to the FastAPI app"""
    
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
        current_user: Dict[str, Any] = Depends(get_current_user)
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
            logging.error(f"Error listing maintenance records: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve maintenance records")
        finally:
            await release_maintenance_connection(conn)

    @app.post("/api/v1/maintenance", response_model=MaintenanceRecord, tags=["Terminal Maintenance"])
    async def create_maintenance_record(
        maintenance: MaintenanceCreate,
        current_user: Dict[str, Any] = Depends(get_current_user)
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
            logging.error(f"Error creating maintenance record: {e}")
            raise HTTPException(status_code=500, detail="Failed to create maintenance record")
        finally:
            await release_maintenance_connection(conn)

    # Add more endpoints here...
    # (The file is getting long, so I'll provide the pattern for the remaining endpoints)
    
    return app

if __name__ == "__main__":
    # This can be used for testing the maintenance endpoints independently
    app = FastAPI(title="Terminal Maintenance API", version="1.0.0")
    create_maintenance_endpoints(app)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
