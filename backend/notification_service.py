"""
ATM Status Change Notification Service

This service tracks ATM status changes and provides notifications for the frontend.
When an ATM status changes from its previous state, it creates a notification 
that can be displayed to users.

Features:
1. Track status changes by comparing current vs previous status
2. Store notifications in database with metadata
3. Mark notifications as read/unread
4. Provide API endpoints for frontend consumption
5. Auto-cleanup old notifications

Usage:
    from notification_service import NotificationService
    
    service = NotificationService()
    service.check_status_changes()  # Check for new status changes
    notifications = service.get_unread_notifications()  # Get unread notifications
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import asyncpg
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dili timezone
DILI_TIMEZONE = pytz.timezone('Asia/Dili')

# Database configuration - using same as existing API
DATABASE_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

class ATMStatus(str, Enum):
    """ATM Status enumeration"""
    AVAILABLE = "AVAILABLE"
    WARNING = "WARNING"
    WOUNDED = "WOUNDED"
    ZOMBIE = "ZOMBIE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

class NotificationSeverity(str, Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# Status severity mapping
STATUS_SEVERITY_MAP = {
    ATMStatus.AVAILABLE: NotificationSeverity.INFO,
    ATMStatus.WARNING: NotificationSeverity.WARNING,
    ATMStatus.WOUNDED: NotificationSeverity.ERROR,
    ATMStatus.ZOMBIE: NotificationSeverity.CRITICAL,
    ATMStatus.OUT_OF_SERVICE: NotificationSeverity.CRITICAL,
}

class NotificationService:
    """Service for managing ATM status change notifications"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        
    async def init_db_pool(self):
        """Initialize database connection pool"""
        if not self.db_pool:
            try:
                self.db_pool = await asyncpg.create_pool(**DATABASE_CONFIG)
                await self.ensure_notification_tables()
                logger.info("Database pool initialized for notification service")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    async def close_db_pool(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
    
    async def ensure_notification_tables(self):
        """Ensure notification tables exist"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"
        async with self.db_pool.acquire() as conn:
            # Create notifications table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS atm_notifications (
                    id SERIAL PRIMARY KEY,
                    notification_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    terminal_id VARCHAR(50) NOT NULL,
                    location TEXT,
                    previous_status VARCHAR(20),
                    current_status VARCHAR(20) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    read_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB
                )
            """)
            
            # Create ATM status history table for tracking changes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS atm_status_history (
                    id SERIAL PRIMARY KEY,
                    terminal_id VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    location TEXT,
                    issue_state_name VARCHAR(50),
                    serial_number VARCHAR(50),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    fetched_status VARCHAR(50),
                    raw_data JSONB
                )
            """)
            
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_terminal_created 
                ON atm_notifications(terminal_id, created_at DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_unread 
                ON atm_notifications(is_read, created_at DESC) WHERE is_read = FALSE
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_history_terminal 
                ON atm_status_history(terminal_id, updated_at DESC)
            """)
            
            logger.info("Notification tables ensured")
    
    def convert_to_dili_time(self, dt: datetime) -> datetime:
        """Convert datetime to Dili timezone"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(DILI_TIMEZONE)
    
    async def get_current_atm_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get current ATM statuses from terminal_details table"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"    
        async with self.db_pool.acquire() as conn:
            # Get latest status for each terminal
            query = """
                WITH latest_data AS (
                    SELECT DISTINCT ON (terminal_id)
                        terminal_id,
                        location,
                        issue_state_name,
                        serial_number,
                        retrieved_date,
                        fetched_status,
                        raw_terminal_data
                    FROM terminal_details
                    ORDER BY terminal_id, retrieved_date DESC
                )
                SELECT 
                    terminal_id,
                    location,
                    COALESCE(
                        CASE 
                            WHEN fetched_status = 'HARD' THEN 'WOUNDED'
                            WHEN fetched_status IN ('CASH', 'UNAVAILABLE') THEN 'OUT_OF_SERVICE'
                            ELSE fetched_status
                        END,
                        CASE 
                            WHEN issue_state_name = 'HARD' THEN 'WOUNDED'
                            WHEN issue_state_name IN ('CASH', 'UNAVAILABLE') THEN 'OUT_OF_SERVICE'
                            ELSE issue_state_name
                        END,
                        'UNKNOWN'
                    ) as status,
                    issue_state_name,
                    serial_number,
                    retrieved_date,
                    fetched_status,
                    raw_terminal_data
                FROM latest_data
            """
            
            rows = await conn.fetch(query)
            
            result = {}
            for row in rows:
                result[row['terminal_id']] = {
                    'terminal_id': row['terminal_id'],
                    'location': row['location'],
                    'status': row['status'],
                    'issue_state_name': row['issue_state_name'],
                    'serial_number': row['serial_number'],
                    'retrieved_date': row['retrieved_date'],
                    'fetched_status': row['fetched_status'],
                    'raw_terminal_data': row['raw_terminal_data']
                }
            
            return result
    
    async def get_previous_statuses(self) -> Dict[str, str]:
        """Get previous statuses from status history table"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"    
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT DISTINCT ON (terminal_id)
                    terminal_id,
                    status
                FROM atm_status_history
                ORDER BY terminal_id, updated_at DESC
            """
            
            rows = await conn.fetch(query)
            return {row['terminal_id']: row['status'] for row in rows}
    
    async def update_status_history(self, current_statuses: Dict[str, Dict[str, Any]]):
        """Update the status history table with current statuses"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"    
        async with self.db_pool.acquire() as conn:
            for terminal_id, data in current_statuses.items():
                await conn.execute("""
                    INSERT INTO atm_status_history (
                        terminal_id, status, location, issue_state_name, 
                        serial_number, fetched_status, raw_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, 
                    terminal_id,
                    data['status'],
                    data['location'],
                    data['issue_state_name'],
                    data['serial_number'],
                    data['fetched_status'],
                    json.dumps(data['raw_terminal_data']) if data['raw_terminal_data'] else None
                )
    
    async def create_notification(
        self,
        terminal_id: str,
        location: str,
        previous_status: Optional[str],
        current_status: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a new notification for status change"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"
        severity = STATUS_SEVERITY_MAP.get(ATMStatus(current_status), NotificationSeverity.INFO)
        
        # Create notification title and message
        if previous_status:
            title = f"ATM {terminal_id} Status Changed"
            message = f"ATM at {location or 'Unknown Location'} changed from {previous_status} to {current_status}"
        else:
            title = f"New ATM {terminal_id} Detected"
            message = f"ATM at {location or 'Unknown Location'} is now {current_status}"
        
        # Add metadata
        notification_metadata = {
            "status_change": {
                "from": previous_status,
                "to": current_status
            },
            "location": location,
            "timestamp": datetime.now(DILI_TIMEZONE).isoformat(),
            **(metadata or {})
        }
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO atm_notifications (
                    terminal_id, location, previous_status, current_status,
                    severity, title, message, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                terminal_id,
                location,
                previous_status,
                current_status,
                severity.value,
                title,
                message,
                json.dumps(notification_metadata)
            )
        
        logger.info(f"Created notification for ATM {terminal_id}: {previous_status} → {current_status}")
    
    async def check_status_changes(self) -> List[Dict[str, Any]]:
        """Check for ATM status changes and create notifications"""
        try:
            if not self.db_pool:
                await self.init_db_pool()
            
            # Get current and previous statuses
            current_statuses = await self.get_current_atm_statuses()
            previous_statuses = await self.get_previous_statuses()
            
            changes = []
            
            for terminal_id, current_data in current_statuses.items():
                current_status = current_data['status']
                previous_status = previous_statuses.get(terminal_id)
                
                # Check if status changed
                if previous_status != current_status:
                    await self.create_notification(
                        terminal_id=terminal_id,
                        location=current_data['location'],
                        previous_status=previous_status,
                        current_status=current_status,
                        metadata={
                            "serial_number": current_data['serial_number'],
                            "issue_state_name": current_data['issue_state_name'],
                            "fetched_status": current_data['fetched_status']
                        }
                    )
                    
                    changes.append({
                        "terminal_id": terminal_id,
                        "location": current_data['location'],
                        "previous_status": previous_status,
                        "current_status": current_status
                    })
            
            # Update status history
            await self.update_status_history(current_statuses)
            
            if changes:
                logger.info(f"Detected {len(changes)} status changes")
            
            return changes
            
        except Exception as e:
            logger.error(f"Error checking status changes: {e}")
            raise
    
    async def get_notifications(
        self,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get notifications with pagination"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"    
        async with self.db_pool.acquire() as conn:
            # Build query
            where_clause = "WHERE is_read = FALSE" if unread_only else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM atm_notifications {where_clause}"
            total_count = await conn.fetchval(count_query)
            
            # Get notifications
            query = f"""
                SELECT 
                    notification_id,
                    terminal_id,
                    location,
                    previous_status,
                    current_status,
                    severity,
                    title,
                    message,
                    created_at,
                    is_read,
                    read_at,
                    metadata
                FROM atm_notifications
                {where_clause}
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            
            rows = await conn.fetch(query, limit, offset)
            
            notifications = []
            for row in rows:
                notification = {
                    "id": str(row['notification_id']),
                    "terminal_id": row['terminal_id'],
                    "location": row['location'],
                    "previous_status": row['previous_status'],
                    "current_status": row['current_status'],
                    "severity": row['severity'],
                    "title": row['title'],
                    "message": row['message'],
                    "created_at": self.convert_to_dili_time(row['created_at']).isoformat(),
                    "is_read": row['is_read'],
                    "read_at": self.convert_to_dili_time(row['read_at']).isoformat() if row['read_at'] else None,
                    "metadata": row['metadata'] if row['metadata'] else {}
                }
                notifications.append(notification)
            
            return notifications, total_count
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"    
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE atm_notifications 
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP 
                WHERE notification_id = $1
            """, notification_id)
            
            return result == "UPDATE 1"
    
    async def mark_all_notifications_read(self) -> int:
        """Mark all notifications as read"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"    
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE atm_notifications 
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP 
                WHERE is_read = FALSE
            """)
            
            # Extract number from result like "UPDATE 5"
            count = int(result.split()[-1]) if result.startswith("UPDATE") else 0
            return count
    
    async def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up notifications older than specified days"""
        if not self.db_pool:
            await self.init_db_pool()
        
        assert self.db_pool is not None, "Database pool should be initialized"
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM atm_notifications 
                WHERE created_at < $1
            """, cutoff_date)
            
            # Also cleanup old status history
            await conn.execute("""
                DELETE FROM atm_status_history 
                WHERE updated_at < $1
            """, cutoff_date)
            
            count = int(result.split()[-1]) if result.startswith("DELETE") else 0
            logger.info(f"Cleaned up {count} old notifications")
            return count

# Singleton instance
notification_service = NotificationService()

async def run_status_check():
    """Standalone function to check for status changes"""
    try:
        changes = await notification_service.check_status_changes()
        print(f"Status check completed. Found {len(changes)} changes.")
        return changes
    except Exception as e:
        print(f"Error during status check: {e}")
        return []
    finally:
        await notification_service.close_db_pool()

if __name__ == "__main__":
    # For standalone testing
    asyncio.run(run_status_check())
