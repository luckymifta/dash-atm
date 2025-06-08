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
import pytz
from typing import Union

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
    
    # Start session scheduler
    try:
        from session_scheduler import session_scheduler
        session_scheduler.start()
        logger.info("Session scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start session scheduler: {e}")
    
    yield
    
    # Shutdown
    try:
        from session_scheduler import session_scheduler
        session_scheduler.stop()
        logger.info("Session scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping session scheduler: {e}")
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

# Timezone configuration for Dili, East Timor (UTC+9)
DILI_TIMEZONE = pytz.timezone('Asia/Dili')

# Session management configuration
SESSION_TIMEOUT_WARNING_MINUTES = 5  # Warn user 5 minutes before token expiration
AUTO_LOGOUT_DILI_TIME = "00:00"  # Automatic logout at midnight Dili time
REMEMBER_ME_DAYS = 30  # Extended session for "Remember Me"

# PostgreSQL configuration - Hardcoded for your development_db (no .env dependency)
POSTGRES_CONFIG = {
    "host": "88.222.214.26",
    "port": 5432,
    "database": "development_db",
    "user": "timlesdev",
    "password": "timlesdev",
    "sslmode": "prefer"  # Added SSL configuration
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
    remember_me: bool = False  # Added remember me functionality

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

def get_dili_time() -> datetime:
    """Get current time in Dili timezone"""
    return datetime.now(DILI_TIMEZONE)

def get_next_midnight_dili() -> datetime:
    """Get next midnight in Dili timezone"""
    now_dili = get_dili_time()
    next_midnight = now_dili.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return next_midnight

def should_auto_logout(user_last_activity: datetime) -> bool:
    """Check if user should be automatically logged out based on Dili midnight rule"""
    if not user_last_activity:
        return False
    
    # Convert last activity to Dili timezone
    if user_last_activity.tzinfo is None:
        user_last_activity = pytz.utc.localize(user_last_activity)
    
    last_activity_dili = user_last_activity.astimezone(DILI_TIMEZONE)
    current_dili = get_dili_time()
    
    # If it's past midnight and last activity was before midnight, logout
    last_activity_date = last_activity_dili.date()
    current_date = current_dili.date()
    
    if current_date > last_activity_date:
        return True
    
    return False

def update_session_activity(user_id: str, session_token: str) -> None:
    """Update last accessed time for session"""
    try:
        query = """
            UPDATE user_sessions 
            SET last_accessed_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND session_token = %s AND is_active = true
        """
        execute_query(query, (user_id, session_token))
    except Exception as e:
        logger.error(f"Failed to update session activity: {e}")

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
    
    # Check if session is still active in database
    session_query = """
        SELECT id FROM user_sessions 
        WHERE session_token = %s AND user_id = %s AND is_active = true
        AND expires_at > CURRENT_TIMESTAMP
    """
    active_session = execute_query(session_query, (token, user_id), fetch="one")
    
    if active_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
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
    
    # Create tokens with extended expiration for "Remember Me"
    if user_login.remember_me:
        access_token_expires = timedelta(days=REMEMBER_ME_DAYS)
        refresh_token_expires = timedelta(days=REMEMBER_ME_DAYS * 2)
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={
            "sub": user_id, 
            "username": user_dict["username"], 
            "role": user_dict["role"],
            "remember_me": user_login.remember_me
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token()
    
    # Store session with enhanced tracking
    session_query = """
        INSERT INTO user_sessions (
            user_id, session_token, refresh_token, expires_at, 
            ip_address, user_agent, is_active, remember_me, last_accessed_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    session_expires_at = datetime.now(timezone.utc) + refresh_token_expires
    session_params = (
        user_id,
        access_token,
        refresh_token,
        session_expires_at,
        get_client_ip(request),
        request.headers.get("user-agent"),
        True,
        user_login.remember_me,
        datetime.now(timezone.utc)  # last_accessed_at
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

@app.post("/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout user and invalidate session"""
    try:
        user_id = current_user["id"]
        
        # Get the token from the Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Deactivate session in database
            query = """
                UPDATE user_sessions 
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND session_token = %s AND is_active = true
            """
            execute_query(query, (user_id, token))
            
            # Log the logout action
            log_audit_action(
                AuditAction.LOGOUT,
                user_id=user_id,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                new_values={"result": "success"}
            )
            
            logger.info(f"User {current_user['username']} logged out successfully")
            return {"message": "Logout successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid authentication token provided"
            )
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Even if there's an error, we should still return success
        # since the client will clear the token anyway
        return {"message": "Logout completed"}

@app.get("/users/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get active sessions for a user"""
    # Only allow users to view their own sessions or admins to view any
    if current_user["id"] != user_id and current_user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these sessions"
        )
    
    query = """
        SELECT session_token, ip_address, user_agent, created_at, 
               last_accessed_at, expires_at, is_active
        FROM user_sessions 
        WHERE user_id = %s AND is_active = true
        ORDER BY last_accessed_at DESC
    """
    sessions = execute_query(query, (user_id,), fetch="all")
    
    return {"sessions": [dict(session) for session in sessions] if sessions else []}

@app.delete("/sessions/{session_token}")
async def revoke_session(
    session_token: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke a specific session"""
    user_id = current_user["id"]
    
    try:
        # First check if the session exists and belongs to the user
        check_query = """
            SELECT id FROM user_sessions 
            WHERE session_token = %s AND user_id = %s AND is_active = true
        """
        existing_session = execute_query(check_query, (session_token, user_id), fetch="one")
        
        if not existing_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already inactive"
            )
        
        # Deactivate the session
        update_query = """
            UPDATE user_sessions 
            SET is_active = false, updated_at = %s
            WHERE session_token = %s AND user_id = %s AND is_active = true
        """
        rows_affected = execute_query(update_query, (datetime.utcnow(), session_token, user_id))
        
        if rows_affected and rows_affected > 0:
            log_audit_action(
                AuditAction.LOGOUT,
                user_id=user_id,
                new_values={"action": "session_revoked", "session_token": session_token[:20] + "..."}
            )
            return {"message": "Session revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke session"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

@app.post("/auth/refresh-session")
async def refresh_session(request: Request, current_user: dict = Depends(get_current_user)):
    """Refresh user session and update activity"""
    try:
        user_id = current_user["id"]
        
        # Get the current token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Update session activity
            update_session_activity(user_id, token)
            
            # Check if user should be auto-logged out due to midnight rule
            query = """
                SELECT last_accessed_at FROM user_sessions 
                WHERE user_id = %s AND session_token = %s AND is_active = true
            """
            session_data = execute_query(query, (user_id, token), fetch="one")
            
            if session_data and should_auto_logout(session_data["last_accessed_at"]):
                # Force logout due to midnight rule
                logout_query = """
                    UPDATE user_sessions 
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND session_token = %s
                """
                execute_query(logout_query, (user_id, token))
                
                log_audit_action(
                    AuditAction.LOGOUT,
                    user_id=user_id,
                    new_values={"reason": "auto_logout_midnight_dili"}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired due to automatic midnight logout"
                )
            
            # Calculate time until next midnight in Dili
            next_midnight = get_next_midnight_dili()
            current_time = get_dili_time()
            time_until_midnight = (next_midnight - current_time).total_seconds()
            
            # Calculate time until token expiration
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
            time_until_exp = (token_exp - datetime.now(timezone.utc)).total_seconds()
            
            return {
                "message": "Session refreshed",
                "time_until_midnight_seconds": int(time_until_midnight),
                "time_until_token_expiry_seconds": int(max(0, time_until_exp)),
                "dili_time": current_time.isoformat(),
                "next_midnight_dili": next_midnight.isoformat(),
                "should_warn_expiry": time_until_exp <= (SESSION_TIMEOUT_WARNING_MINUTES * 60)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid authentication token provided"
            )
            
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Session refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh session"
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

# ==================== USER CRUD OPERATIONS ====================

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create a new user (admin/super_admin only)"""
    
    # Check permissions
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create users"
        )
    
    try:
        # Check if username already exists
        check_query = "SELECT id FROM users WHERE username = %s AND is_deleted = false"
        existing_user = execute_query(check_query, (user_data.username,), fetch="one")
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        check_email_query = "SELECT id FROM users WHERE email = %s AND is_deleted = false"
        existing_email = execute_query(check_email_query, (user_data.email,), fetch="one")
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(user_data.password)
        now = datetime.now(timezone.utc)
        
        insert_query = """
            INSERT INTO users (
                id, username, email, password_hash, first_name, last_name,
                phone, role, is_active, is_deleted, password_changed_at,
                failed_login_attempts, created_at, updated_at, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            user_id,
            user_data.username,
            user_data.email,
            password_hash,
            user_data.first_name,
            user_data.last_name,
            user_data.phone,
            user_data.role,
            user_data.is_active,
            False,  # is_deleted
            now,    # password_changed_at
            0,      # failed_login_attempts
            now,    # created_at
            now,    # updated_at
            current_user.get("id")  # created_by
        )
        
        execute_query(insert_query, params)
        
        # Log the action
        log_audit_action(
            AuditAction.CREATE_USER,
            user_id=current_user.get("id"),
            entity_id=user_id,
            new_values={
                "username": user_data.username,
                "email": user_data.email,
                "role": user_data.role,
                "is_active": user_data.is_active
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            performed_by=current_user.get("username")
        )
        
        # Get the created user
        get_query = "SELECT * FROM users WHERE id = %s"
        user = execute_query(get_query, (user_id,), fetch="one")
        
        logger.info(f"User created successfully: {user_data.username} by {current_user.get('username')}")
        return UserResponse(**dict(user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update user information"""
    
    # Check if user exists
    user_query = "SELECT * FROM users WHERE id = %s AND is_deleted = false"
    user = execute_query(user_query, (user_id,), fetch="one")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Permission checks
    current_user_role = current_user.get("role")
    target_user_role = user["role"]
    
    # Users can update their own basic info (except role and is_active)
    is_self_update = current_user.get("id") == user_id
    is_admin = current_user_role in ["admin", "super_admin"]
    
    if not (is_self_update or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this user"
        )
    
    # Restrict what regular users can update about themselves
    if is_self_update and not is_admin:
        # Users can only update their basic info, not role or active status
        if user_data.role is not None or user_data.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change role or active status"
            )
    
    # Super admin restrictions
    if target_user_role == "super_admin" and current_user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can modify super admin accounts"
        )
    
    try:
        # Build update query dynamically
        update_fields = []
        params = []
        old_values = {}
        new_values = {}
        
        # Check each field and add to update if provided
        for field, value in user_data.dict(exclude_unset=True).items():
            if value is not None:
                # Check for username uniqueness
                if field == "username" and value != user["username"]:
                    check_query = "SELECT id FROM users WHERE username = %s AND is_deleted = false AND id != %s"
                    existing = execute_query(check_query, (value, user_id), fetch="one")
                    if existing:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already exists"
                        )
                
                # Check for email uniqueness
                if field == "email" and value != user["email"]:
                    check_query = "SELECT id FROM users WHERE email = %s AND is_deleted = false AND id != %s"
                    existing = execute_query(check_query, (value, user_id), fetch="one")
                    if existing:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already exists"
                        )
                
                update_fields.append(f"{field} = %s")
                params.append(value)
                old_values[field] = user[field]
                new_values[field] = value
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Add updated_at
        update_fields.append("updated_at = %s")
        params.append(datetime.now(timezone.utc))
        params.append(user_id)
        
        update_query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        
        execute_query(update_query, tuple(params))
        
        # Log the action
        log_audit_action(
            AuditAction.UPDATE_USER,
            user_id=current_user.get("id"),
            entity_id=user_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            performed_by=current_user.get("username")
        )
        
        # Get updated user
        updated_user = execute_query(user_query, (user_id,), fetch="one")
        
        logger.info(f"User updated successfully: {user['username']} by {current_user.get('username')}")
        return UserResponse(**dict(updated_user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a user (admin/super_admin only)"""
    
    # Check permissions
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete users"
        )
    
    # Check if user exists
    user_query = "SELECT * FROM users WHERE id = %s AND is_deleted = false"
    user = execute_query(user_query, (user_id,), fetch="one")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if current_user.get("id") == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Super admin protection
    if user["role"] == "super_admin" and current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete super admin accounts"
        )
    
    try:
        # Soft delete the user
        now = datetime.now(timezone.utc)
        delete_query = """
            UPDATE users 
            SET is_deleted = true, is_active = false, updated_at = %s
            WHERE id = %s
        """
        execute_query(delete_query, (now, user_id))
        
        # Invalidate all sessions for this user
        invalidate_query = "UPDATE user_sessions SET is_active = false WHERE user_id = %s"
        execute_query(invalidate_query, (user_id,))
        
        # Log the action
        log_audit_action(
            AuditAction.DELETE_USER,
            user_id=current_user.get("id"),
            entity_id=user_id,
            old_values={"username": user["username"], "is_deleted": False},
            new_values={"is_deleted": True},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            performed_by=current_user.get("username")
        )
        
        logger.info(f"User deleted successfully: {user['username']} by {current_user.get('username')}")
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@app.put("/users/{user_id}/password")
async def change_password(
    user_id: str,
    password_data: PasswordUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    
    # Check if user exists
    user_query = "SELECT * FROM users WHERE id = %s AND is_deleted = false"
    user = execute_query(user_query, (user_id,), fetch="one")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Permission checks
    is_self_update = current_user.get("id") == user_id
    is_admin = current_user.get("role") in ["admin", "super_admin"]
    
    if not (is_self_update or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to change this user's password"
        )
    
    # For self-updates, verify current password
    if is_self_update:
        if not verify_password(password_data.current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
    
    # Super admin protection
    if user["role"] == "super_admin" and current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can change super admin passwords"
        )
    
    try:
        # Hash new password
        new_password_hash = hash_password(password_data.new_password)
        now = datetime.now(timezone.utc)
        
        # Update password
        update_query = """
            UPDATE users 
            SET password_hash = %s, password_changed_at = %s, 
                failed_login_attempts = 0, account_locked_until = NULL,
                updated_at = %s
            WHERE id = %s
        """
        execute_query(update_query, (new_password_hash, now, now, user_id))
        
        # Invalidate all other sessions for this user (except current one if self-update)
        if is_self_update:
            # Keep current session active, invalidate others
            current_session_token = request.headers.get("authorization", "").replace("Bearer ", "")
            invalidate_query = """
                UPDATE user_sessions 
                SET is_active = false 
                WHERE user_id = %s AND session_token != %s
            """
            execute_query(invalidate_query, (user_id, current_session_token))
        else:
            # Invalidate all sessions for user
            invalidate_query = "UPDATE user_sessions SET is_active = false WHERE user_id = %s"
            execute_query(invalidate_query, (user_id,))
        
        # Log the action
        log_audit_action(
            AuditAction.PASSWORD_CHANGE,
            user_id=current_user.get("id"),
            entity_id=user_id,
            new_values={"password_changed": True},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            performed_by=current_user.get("username")
        )
        
        logger.info(f"Password changed successfully for user: {user['username']} by {current_user.get('username')}")
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

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
