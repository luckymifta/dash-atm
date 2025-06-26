import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import psycopg2
from contextlib import contextmanager


class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that saves log records to PostgreSQL database
    """
    
    def __init__(self, db_connector, execution_id: str, demo_mode: bool = False):
        super().__init__()
        self.db_connector = db_connector
        self.execution_id = execution_id
        self.demo_mode = demo_mode
        self.current_phase = "INITIALIZATION"
        self.current_terminal_id = None
        self.current_region_code = None
        
        # Performance tracking
        self.phase_start_times = {}
        self.performance_metrics = {}
        
        # Create tables if they don't exist
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create log tables if they don't exist"""
        if self.demo_mode:
            return  # Skip table creation in demo mode
            
        conn = self.db_connector.get_db_connection()
        if not conn:
            return
            
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Create log_events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    execution_id UUID NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    logger_name VARCHAR(100),
                    message TEXT NOT NULL,
                    module VARCHAR(100),
                    function_name VARCHAR(100),
                    line_number INTEGER,
                    execution_phase VARCHAR(50),
                    terminal_id VARCHAR(20),
                    region_code VARCHAR(10),
                    error_details JSONB,
                    performance_metrics JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create execution_summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_summary (
                    execution_id UUID PRIMARY KEY,
                    start_time TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    duration_seconds INTEGER,
                    demo_mode BOOLEAN,
                    total_atms INTEGER,
                    success BOOLEAN,
                    failover_activated BOOLEAN,
                    failure_type VARCHAR(50),
                    connection_status VARCHAR(50),
                    regional_records_processed INTEGER,
                    terminal_details_processed INTEGER,
                    error_count INTEGER,
                    warning_count INTEGER,
                    info_count INTEGER,
                    performance_summary JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_execution_id ON log_events(execution_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_timestamp ON log_events(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_level ON log_events(level);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_phase ON log_events(execution_phase);")
            
            conn.commit()
            
        except Exception as e:
            print(f"Failed to create log tables: {e}")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            conn.close()
    
    def set_context(self, phase: Optional[str] = None, terminal_id: Optional[str] = None, region_code: Optional[str] = None):
        """Set context information for subsequent log records"""
        if phase:
            # Track phase transitions for performance
            if self.current_phase and self.current_phase != phase:
                self._record_phase_end(self.current_phase)
            
            self.current_phase = phase
            self._record_phase_start(phase)
            
        if terminal_id:
            self.current_terminal_id = terminal_id
        if region_code:
            self.current_region_code = region_code
    
    def _record_phase_start(self, phase: str):
        """Record the start time of a phase"""
        self.phase_start_times[phase] = datetime.now()
    
    def _record_phase_end(self, phase: str):
        """Record the end time and duration of a phase"""
        if phase in self.phase_start_times:
            start_time = self.phase_start_times[phase]
            duration = (datetime.now() - start_time).total_seconds()
            self.performance_metrics[phase] = {
                'start_time': start_time.isoformat(),
                'duration_seconds': duration
            }
    
    def emit(self, record):
        """Save log record to database"""
        if self.demo_mode:
            return  # Skip database logging in demo mode
            
        try:
            # Extract error details if this is an exception
            error_details = None
            if record.exc_info and record.exc_info[0]:
                error_details = {
                    'exception_type': record.exc_info[0].__name__,
                    'exception_message': str(record.exc_info[1]),
                    'traceback': self.format(record)
                }
            
            # Extract performance metrics if available
            perf_metrics = None
            if hasattr(record, 'performance_data'):
                perf_metrics = getattr(record, 'performance_data')
            
            # Parse terminal ID from message if not set in context
            terminal_id = self.current_terminal_id
            if not terminal_id and 'terminal' in record.getMessage().lower():
                # Try to extract terminal ID from message
                import re
                match = re.search(r'terminal\s+(\d+)', record.getMessage(), re.IGNORECASE)
                if match:
                    terminal_id = match.group(1)
            
            self._save_to_database(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                logger_name=record.name,
                message=record.getMessage(),
                module=record.module if hasattr(record, 'module') else record.pathname.split('/')[-1],
                function_name=record.funcName,
                line_number=record.lineno,
                execution_phase=self.current_phase,
                terminal_id=terminal_id,
                region_code=self.current_region_code,
                error_details=error_details,
                performance_metrics=perf_metrics
            )
            
        except Exception as e:
            # Don't let logging errors break the main application
            print(f"Failed to save log to database: {e}")
    
    def _save_to_database(self, **kwargs):
        """Save a single log record to database"""
        conn = self.db_connector.get_db_connection()
        if not conn:
            return
            
        cursor = None
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO log_events (
                    timestamp, execution_id, level, logger_name, message,
                    module, function_name, line_number, execution_phase,
                    terminal_id, region_code, error_details, performance_metrics
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                kwargs['timestamp'],
                self.execution_id,
                kwargs['level'],
                kwargs['logger_name'],
                kwargs['message'],
                kwargs['module'],
                kwargs['function_name'],
                kwargs['line_number'],
                kwargs['execution_phase'],
                kwargs['terminal_id'],
                kwargs['region_code'],
                json.dumps(kwargs['error_details']) if kwargs['error_details'] else None,
                json.dumps(kwargs['performance_metrics']) if kwargs['performance_metrics'] else None
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Database log save failed: {e}")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            conn.close()
    
    def save_execution_summary(self, summary_data: Dict[str, Any]):
        """Save execution summary to database"""
        if self.demo_mode:
            return
            
        # Finalize performance metrics
        if self.current_phase:
            self._record_phase_end(self.current_phase)
        
        conn = self.db_connector.get_db_connection()
        if not conn:
            return
            
        cursor = None
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO execution_summary (
                    execution_id, start_time, end_time, duration_seconds,
                    demo_mode, total_atms, success, failover_activated,
                    failure_type, connection_status, regional_records_processed,
                    terminal_details_processed, error_count, warning_count,
                    info_count, performance_summary
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (execution_id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    duration_seconds = EXCLUDED.duration_seconds,
                    success = EXCLUDED.success,
                    failover_activated = EXCLUDED.failover_activated,
                    failure_type = EXCLUDED.failure_type,
                    connection_status = EXCLUDED.connection_status,
                    regional_records_processed = EXCLUDED.regional_records_processed,
                    terminal_details_processed = EXCLUDED.terminal_details_processed,
                    error_count = EXCLUDED.error_count,
                    warning_count = EXCLUDED.warning_count,
                    info_count = EXCLUDED.info_count,
                    performance_summary = EXCLUDED.performance_summary
            """, (
                self.execution_id,
                summary_data.get('start_time'),
                summary_data.get('end_time'),
                summary_data.get('duration_seconds'),
                summary_data.get('demo_mode', False),
                summary_data.get('total_atms'),
                summary_data.get('success'),
                summary_data.get('failover_activated', False),
                summary_data.get('failure_type'),
                summary_data.get('connection_status'),
                summary_data.get('regional_records_processed'),
                summary_data.get('terminal_details_processed'),
                summary_data.get('error_count', 0),
                summary_data.get('warning_count', 0),
                summary_data.get('info_count', 0),
                json.dumps(self.performance_metrics)
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Failed to save execution summary: {e}")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            conn.close()


class LogMetricsCollector:
    """Utility class to collect log metrics during execution"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.debug_count = 0
        self.start_time = datetime.now()
        self.end_time = None
    
    def increment_level(self, level: str):
        level_upper = level.upper()
        if level_upper == 'ERROR':
            self.error_count += 1
        elif level_upper == 'WARNING':
            self.warning_count += 1
        elif level_upper == 'INFO':
            self.info_count += 1
        elif level_upper == 'DEBUG':
            self.debug_count += 1
    
    def finalize(self):
        self.end_time = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        duration = 0
        if self.end_time and self.start_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': int(duration),
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'debug_count': self.debug_count
        }
