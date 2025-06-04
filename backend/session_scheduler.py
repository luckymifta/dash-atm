"""
Session Management Scheduler for ATM Dashboard
Handles automatic session cleanup and midnight logout enforcement.
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import pytz
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration - using same pattern as user_management_api.py
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "dash"),
    "user": os.getenv("DB_USER", "timlesdev"),
    "password": os.getenv("DB_PASSWORD", "timlesdev")
}

# Timezone configuration
DILI_TIMEZONE = pytz.timezone('Asia/Dili')  # UTC+9

class SessionScheduler:
    """Handles scheduled session management tasks."""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
    
    def get_db_connection(self):
        """Get database connection using same pattern as user_management_api.py."""
        try:
            conn = psycopg2.connect(**DATABASE_CONFIG, cursor_factory=RealDictCursor)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def cleanup_expired_sessions(self):
        """Remove sessions that have expired."""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Delete expired sessions
                    cursor.execute("""
                        DELETE FROM user_sessions 
                        WHERE expires_at < %s AND is_active = true
                    """, (datetime.utcnow(),))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} expired sessions")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def midnight_logout_cleanup(self):
        """Perform midnight logout for all active sessions in Dili timezone."""
        try:
            dili_now = datetime.now(DILI_TIMEZONE)
            midnight_today = dili_now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if we're at midnight (within 1 minute window)
            if not (midnight_today <= dili_now <= midnight_today + timedelta(minutes=1)):
                logger.debug("Not midnight time for logout, skipping...")
                return
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get all active sessions for logging
                    cursor.execute("""
                        SELECT session_token, user_id, created_at, remember_me
                        FROM user_sessions 
                        WHERE is_active = true
                    """)
                    
                    active_sessions = cursor.fetchall()
                    
                    if not active_sessions:
                        logger.info("No active sessions to logout at midnight")
                        return
                    
                    # Deactivate all active sessions
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_active = false, 
                            updated_at = %s
                        WHERE is_active = true
                    """, (datetime.utcnow(),))
                    
                    # Log the midnight logout event for each user
                    for session in active_sessions:
                        cursor.execute("""
                            INSERT INTO user_audit_log (
                                user_id, action, details, ip_address, user_agent, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            session['user_id'],
                            'logout',
                            f"Automatic midnight logout (Dili time) - Session: {session['session_token'][:8]}...",
                            'system',
                            'session_scheduler',
                            datetime.utcnow()
                        ))
                    
                    conn.commit()
                    
                    logger.info(f"Midnight logout completed for {len(active_sessions)} active sessions")
                    
        except Exception as e:
            logger.error(f"Error during midnight logout cleanup: {e}")
    
    def cleanup_old_audit_logs(self):
        """Clean up audit logs older than 90 days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        DELETE FROM user_audit_log 
                        WHERE created_at < %s
                    """, (cutoff_date,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} old audit log entries")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {e}")
    
    def session_health_check(self):
        """Perform health check on session system."""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Count active sessions
                    cursor.execute("""
                        SELECT COUNT(*) as active_count
                        FROM user_sessions 
                        WHERE is_active = true
                    """)
                    active_count = cursor.fetchone()['active_count']
                    
                    # Count sessions by remember_me status
                    cursor.execute("""
                        SELECT remember_me, COUNT(*) as count
                        FROM user_sessions 
                        WHERE is_active = true
                        GROUP BY remember_me
                    """)
                    session_stats = cursor.fetchall()
                    
                    # Count unique active users
                    cursor.execute("""
                        SELECT COUNT(DISTINCT user_id) as unique_users
                        FROM user_sessions 
                        WHERE is_active = true
                    """)
                    unique_users = cursor.fetchone()['unique_users']
                    
                    logger.info(f"Session Health Check - Active Sessions: {active_count}, "
                              f"Unique Users: {unique_users}")
                    
                    for stat in session_stats:
                        session_type = "Remember Me" if stat['remember_me'] else "Regular"
                        logger.info(f"{session_type} sessions: {stat['count']}")
                        
        except Exception as e:
            logger.error(f"Error during session health check: {e}")
    
    def schedule_tasks(self):
        """Schedule all session management tasks."""
        # Clean up expired sessions every 15 minutes
        schedule.every(15).minutes.do(self.cleanup_expired_sessions)
        
        # Check for midnight logout every minute
        schedule.every().minute.do(self.midnight_logout_cleanup)
        
        # Clean up old audit logs daily at 2 AM Dili time
        schedule.every().day.at("02:00").do(self.cleanup_old_audit_logs)
        
        # Session health check every hour
        schedule.every().hour.do(self.session_health_check)
        
        logger.info("Session management tasks scheduled successfully")
    
    def run_scheduler(self):
        """Run the scheduler in a loop."""
        logger.info("Starting session management scheduler...")
        self.running = True
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def start(self):
        """Start the scheduler in a separate thread."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler is already running")
            return
        
        self.schedule_tasks()
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Session scheduler started in background thread")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Session scheduler stopped")

# Global scheduler instance
session_scheduler = SessionScheduler()

def main():
    """Main function to run the scheduler standalone."""
    try:
        scheduler = SessionScheduler()
        scheduler.schedule_tasks()
        
        logger.info("Session Management Scheduler started")
        logger.info("Tasks scheduled:")
        logger.info("- Expired session cleanup: Every 15 minutes")
        logger.info("- Midnight logout check: Every minute")
        logger.info("- Audit log cleanup: Daily at 2 AM Dili time")
        logger.info("- Session health check: Every hour")
        
        # Run initial cleanup
        scheduler.cleanup_expired_sessions()
        scheduler.session_health_check()
        
        # Start scheduler loop
        scheduler.run_scheduler()
        
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        raise

if __name__ == "__main__":
    main()
