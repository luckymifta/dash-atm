#!/usr/bin/env python3
"""
Windows Service wrapper for the Combined ATM Retrieval Script

This script wraps the main application to run as a Windows service using pywin32.
It provides automatic startup, restart on failure, and proper Windows service integration.
"""

import socket
import sys
import os
import time
import subprocess
import logging
from threading import Thread
import signal
from typing import Optional, Any

# Windows-specific imports with fallbacks for development on non-Windows systems
WINDOWS_MODULES_AVAILABLE = False
try:
    import win32serviceutil  # type: ignore
    import win32service  # type: ignore
    import win32event  # type: ignore
    import servicemanager  # type: ignore
    WINDOWS_MODULES_AVAILABLE = True
except ImportError:
    # Windows-specific modules not available on non-Windows systems
    # This is expected when developing on macOS/Linux
    # Create minimal stubs to prevent import errors during development
    win32serviceutil = None  # type: ignore
    win32service = None  # type: ignore
    win32event = None  # type: ignore
    servicemanager = None  # type: ignore

class ATMMonitorService(win32serviceutil.ServiceFramework if WINDOWS_MODULES_AVAILABLE else object):  # type: ignore
    _svc_name_ = "ATMMonitorService"
    _svc_display_name_ = "ATM Monitor Continuous Service"
    _svc_description_ = "Continuous ATM data retrieval and monitoring service"
    
    def __init__(self, args: Any = None) -> None:
        if WINDOWS_MODULES_AVAILABLE:
            win32serviceutil.ServiceFramework.__init__(self, args)  # type: ignore
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)  # type: ignore
        else:
            self.hWaitStop = None
        self.is_running = True
        self.process: Optional[subprocess.Popen[str]] = None
        
        # Set up logging
        self.setup_logging()
        self.logger.info("ATM Monitor Service initialized")
    
    def setup_logging(self) -> None:
        """Setup service-specific logging"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logging
        log_file = os.path.join(log_dir, 'service.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s [Service]: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ATMService')
    
    def SvcStop(self) -> None:
        """Called when the service is asked to stop"""
        self.logger.info("Service stop requested")
        if WINDOWS_MODULES_AVAILABLE:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)  # type: ignore
            win32event.SetEvent(self.hWaitStop)  # type: ignore
        self.is_running = False
        
        # Terminate the subprocess if it's running
        if self.process and self.process.poll() is None:
            self.logger.info("Terminating main process...")
            try:
                self.process.terminate()
                # Wait up to 30 seconds for graceful shutdown
                self.process.wait(timeout=30)
                self.logger.info("Main process terminated gracefully")
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't terminate gracefully, killing...")
                self.process.kill()
                self.logger.info("Main process killed")
            except Exception as e:
                self.logger.error(f"Error terminating process: {e}")
    
    def SvcDoRun(self) -> None:
        """Main service execution"""
        self.logger.info("ATM Monitor Service starting...")
        if WINDOWS_MODULES_AVAILABLE:
            servicemanager.LogMsg(  # type: ignore
                servicemanager.EVENTLOG_INFORMATION_TYPE,  # type: ignore
                servicemanager.PYS_SERVICE_STARTED,  # type: ignore
                (self._svc_name_, '')
            )
        
        # Run the main service loop
        self.main_loop()
        
        self.logger.info("ATM Monitor Service stopped")
        if WINDOWS_MODULES_AVAILABLE:
            servicemanager.LogMsg(  # type: ignore
                servicemanager.EVENTLOG_INFORMATION_TYPE,  # type: ignore
                servicemanager.PYS_SERVICE_STOPPED,  # type: ignore
                (self._svc_name_, '')
            )
    
    def main_loop(self) -> None:
        """Main service loop with restart capability"""
        restart_count = 0
        max_restarts = 5
        restart_delay = 60  # seconds
        
        while self.is_running:
            try:
                # Check if we should restart
                if restart_count >= max_restarts:
                    self.logger.error(f"Maximum restart attempts ({max_restarts}) reached. Stopping service.")
                    break
                
                # Start the main application
                self.logger.info(f"Starting ATM Monitor application (attempt {restart_count + 1})")
                self.start_main_application()
                
                # Wait for process to complete or service to stop
                while self.is_running and self.process and self.process.poll() is None:
                    # Check every 5 seconds
                    if WINDOWS_MODULES_AVAILABLE and self.hWaitStop:
                        if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0:  # type: ignore
                            break
                    else:
                        time.sleep(5)
                
                # Check why the process stopped
                if self.process:
                    exit_code = self.process.poll()
                    if exit_code is not None and exit_code != 0:
                        restart_count += 1
                        self.logger.error(f"Main application exited with code {exit_code}")
                        
                        if self.is_running and restart_count < max_restarts:
                            self.logger.info(f"Restarting in {restart_delay} seconds...")
                            time.sleep(restart_delay)
                    else:
                        # Clean exit or service stop requested
                        break
                else:
                    break
                    
            except Exception as e:
                restart_count += 1
                self.logger.error(f"Error in main loop: {e}")
                if self.is_running and restart_count < max_restarts:
                    self.logger.info(f"Restarting in {restart_delay} seconds...")
                    time.sleep(restart_delay)
    
    def start_main_application(self) -> None:
        """Start the main ATM retrieval application"""
        try:
            # Get the script directory
            script_dir = os.path.dirname(__file__)
            script_path = os.path.join(script_dir, 'combined_atm_retrieval_script.py')
            
            # Check if virtual environment exists
            venv_python = os.path.join(script_dir, 'venv', 'Scripts', 'python.exe')
            if os.path.exists(venv_python):
                python_executable = venv_python
            else:
                python_executable = sys.executable
            
            # Prepare command
            cmd = [
                python_executable,
                script_path,
                '--continuous',
                '--save-to-db',
                '--use-new-tables',
                '--quiet'
            ]
            
            # Set working directory to script directory
            os.chdir(script_dir)
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.logger.info(f"Started main application with PID {self.process.pid}")
            
            # Start a thread to log output
            output_thread = Thread(target=self.log_output, daemon=True)
            output_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start main application: {e}")
            raise
    
    def log_output(self) -> None:
        """Log output from the main application"""
        if not self.process or not self.process.stdout:
            return
        
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line and self.is_running:
                    # Remove newline and log
                    self.logger.info(f"[App] {line.rstrip()}")
        except Exception as e:
            self.logger.error(f"Error reading application output: {e}")

def main() -> None:
    """Main entry point for service management"""
    if not WINDOWS_MODULES_AVAILABLE:
        print("Error: Windows service modules not available. This script must be run on Windows.")
        sys.exit(1)
    
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()  # type: ignore
        servicemanager.PrepareToHostSingle(ATMMonitorService)  # type: ignore
        servicemanager.StartServiceCtrlDispatcher()  # type: ignore
    else:
        # Handle command line arguments
        win32serviceutil.HandleCommandLine(ATMMonitorService)  # type: ignore

if __name__ == '__main__':
    main()
