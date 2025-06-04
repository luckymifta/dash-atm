"""
User Management API for ATM Dashboard
Provides CRUD operations, password management, session handling, and audit logging
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import bcrypt
import secrets
import jwt
import uuid
import json
from enum import Enum
import asyncio
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_default_users()
    yield
    # Shutdown
    pass

app = FastAPI(title="User Management API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30
MAX_FAILED_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 15

# PostgreSQL configuration from .env file
POSTGRES_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "dash"),
    "user": os.getenv("DB_USER", "timlesdev"),
    "password": os.getenv("DB_PASSWORD", "timlesdev")
}

# Enums
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class AuditAction(str, Enum):
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCK = "account_lock"
    ACCOUNT_UNLOCK = "account_unlock"

# Pydantic Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: str
    password_changed_at: datetime
    failed_login_attempts: int
    account_locked_until: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    performed_by: Optional[str]
    created_at: datetime

# Database helper functions
def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

def execute_query(query: str, params: Optional[tuple] = None, fetch: Optional[str] = None):
    """Execute database query with proper error handling"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch == "one":
                    return cursor.fetchone()
                elif fetch == "all":
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
    except psycopg2.Error as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )

# Utility Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token() -> str:
    """Create a secure refresh token"""
    return secrets.token_urlsafe(32)

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    return request.client.host if request.client else "unknown"

def log_audit_action(
    action: AuditAction,
    user_id: Optional[str] = None,
    entity_type: str = "user",
    entity_id: Optional[str] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    performed_by: Optional[str] = None
):
    """Log an audit action to database"""
    try:
        query = """
            INSERT INTO user_audit_log (
                user_id, action, entity_type, entity_id, old_values, new_values,
                ip_address, user_agent, performed_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            user_id,
            action.value,
            entity_type,
            entity_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            ip_address,
            user_agent,
            performed_by
        )
        execute_query(query, params)
        logger.info(f"Audit log: {action.value} by user {performed_by} on {entity_type} {entity_id}")
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")
        # Don't raise exception as audit logging failure shouldn't break the main operation

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from database"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    query = "SELECT * FROM users WHERE id = %s AND is_active = true AND is_deleted = false"
    user = execute_query(query, (user_id,), fetch="one")
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return dict(user)

# API Endpoints

@app.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin, request: Request):
    """Authenticate user and return tokens"""
    # Find user by username
    query = "SELECT * FROM users WHERE username = %s AND is_deleted = false"
    user = execute_query(query, (user_login.username,), fetch="one")
    
    if not user:
        log_audit_action(
            AuditAction.LOGIN,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            new_values={"username": user_login.username, "result": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user_dict = dict(user)
    user_id = str(user_dict["id"])
    
    # Check if account is locked
    if user_dict.get("account_locked_until") and user_dict["account_locked_until"] > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user_dict['account_locked_until']}"
        )
    
    # Verify password
    if not verify_password(user_login.password, user_dict["password_hash"]):
        # Increment failed attempts
        failed_attempts = user_dict.get("failed_login_attempts", 0) + 1
        
        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            # Lock account
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
            query = """
                UPDATE users 
                SET failed_login_attempts = %s, account_locked_until = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            execute_query(query, (failed_attempts, lock_until, user_id))
            log_audit_action(AuditAction.ACCOUNT_LOCK, user_id=user_id, performed_by="system")
        else:
            # Update failed attempts
            query = """
                UPDATE users 
                SET failed_login_attempts = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            execute_query(query, (failed_attempts, user_id))
        
        log_audit_action(
            AuditAction.LOGIN,
            user_id=user_id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            new_values={"result": "invalid_password", "failed_attempts": failed_attempts}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Reset failed attempts on successful login
    query = """
        UPDATE users 
        SET failed_login_attempts = 0, account_locked_until = NULL, 
            last_login_at = CURRENT_TIMESTAMP, last_login_ip = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(query, (get_client_ip(request), user_id))
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "username": user_dict["username"], "role": user_dict["role"]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token()
    
    # Store session
    session_query = """
        INSERT INTO user_sessions (
            user_id, session_token, refresh_token, expires_at, 
            ip_address, user_agent, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    session_params = (
        user_id,
        access_token,
        refresh_token,
        datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        get_client_ip(request),
        request.headers.get("user-agent"),
        True
    )
    execute_query(session_query, session_params)
    
    log_audit_action(
        AuditAction.LOGIN,
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        new_values={"result": "success"}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user"""
    query = "SELECT * FROM users WHERE id = %s AND is_deleted = false"
    user = execute_query(query, (user_id,), fetch="one")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**dict(user))

@app.get("/users")
async def get_users(
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of users with optional filtering"""
    
    # Validate pagination parameters
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10
    
    # Build the WHERE clause
    where_conditions = ["is_deleted = false"]
    params = []
    
    # Add search filter
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        where_conditions.append(
            "(username ILIKE %s OR email ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s)"
        )
        params.extend([search_term, search_term, search_term, search_term])
    
    # Add role filter
    if role and role.strip():
        where_conditions.append("role = %s")
        params.append(role.strip())
    
    # Add status filter
    if status and status.strip():
        if status.strip().lower() == "active":
            where_conditions.append("is_active = true")
        elif status.strip().lower() == "inactive":
            where_conditions.append("is_active = false")
    
    where_clause = " AND ".join(where_conditions)
    
    # Count total users
    count_query = f"SELECT COUNT(*) FROM users WHERE {where_clause}"
    total_result = execute_query(count_query, tuple(params), fetch="one")
    total = total_result['count'] if total_result else 0
    
    # Calculate pagination
    offset = (page - 1) * limit
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Get users with pagination
    users_query = f"""
        SELECT * FROM users 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    users_params = params + [limit, offset]
    users_result = execute_query(users_query, tuple(users_params), fetch="all")
    
    # Convert to response format
    users = []
    if users_result:
        for user_data in users_result:
            user_dict = dict(user_data)
            users.append(UserResponse(**user_dict))
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

# Initialize with default admin user
def initialize_default_users():
    """Create default admin user if it doesn't exist"""
    try:
        # Check if any admin user exists
        query = "SELECT COUNT(*) FROM users WHERE role IN ('super_admin', 'admin') AND is_deleted = false"
        result = execute_query(query, fetch="one")
        
        if result["count"] > 0:
            logger.info("Admin user already exists - skipping initialization")
            return
        
        # Create default admin user
        admin_id = str(uuid.uuid4())
        password_hash = hash_password("admin123")  # Change this in production!
        
        insert_query = """
            INSERT INTO users (
                id, username, email, password_hash, first_name, last_name,
                role, is_active, is_deleted, password_changed_at, 
                failed_login_attempts, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now(timezone.utc)
        params = (
            admin_id,
            "admin",
            "admin@atm-dashboard.com",
            password_hash,
            "System",
            "Administrator",
            "super_admin",
            True,
            False,
            now,
            0,
            now,
            now
        )
        
        execute_query(insert_query, params)
        
        # Log the creation
        log_audit_action(
            AuditAction.CREATE_USER,
            user_id=admin_id,
            entity_id=admin_id,
            new_values={"username": "admin", "role": "super_admin"},
            performed_by="system"
        )
        
        logger.info("Default admin user created: username=admin, password=admin123")
        logger.warning("⚠️  SECURITY WARNING: Change the default admin password after first login!")
        
    except Exception as e:
        logger.error(f"Failed to initialize default admin user: {e}")
        # Don't raise exception as this shouldn't prevent the API from starting

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
