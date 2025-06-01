#!/usr/bin/env python3
"""
ATM Network Connectivity Monitor and Auto-Retrieval
===================================================

This script monitors network connectivity to the ATM system and automatically
starts the retrieval process when connectivity is established.
"""

import time
import subprocess
import sys
import os
from datetime import datetime
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_atm_connectivity(timeout=10):
    """Check if we can connect to the ATM system"""
    url = "https://172.31.1.46/sigit/user/login?language=EN"
    try:
        response = requests.head(url, timeout=timeout, verify=False)
        return True, response.status_code
    except Exception as e:
        return False, str(e)

def run_full_retrieval(demo_mode=False):
    """Run the full ATM details retrieval"""
    print(f"\n{'='*80}")
    print(f"🚀 STARTING FULL ATM DETAILS RETRIEVAL")
    print(f"{'='*80}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Demo mode: {demo_mode}")
    
    # Build command for batch retrieval
    cmd = [
        'python', 'batch_atm_retrieval.py',
        '--config', 'all_terminals_config.json',
        '--batch-size', '15',  # Reasonable batch size
        '--delay', '45',       # 45 seconds between batches
        '--verbose'
    ]
    
    if demo_mode:
        cmd.append('--demo')
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run the batch retrieval
        result = subprocess.run(cmd, text=True)
        
        if result.returncode == 0:
            print(f"✅ Full retrieval completed successfully!")
            
            # Check if combined results file exists
            if os.path.exists('combined_atm_details.json'):
                # Get file size for quick stats
                file_size = os.path.getsize('combined_atm_details.json')
                print(f"📊 Combined results file size: {file_size:,} bytes")
                
                # Try to get basic stats from the file
                try:
                    import json
                    with open('combined_atm_details.json', 'r') as f:
                        data = json.load(f)
                    
                    metadata = data.get('retrieval_metadata', {})
                    total_terminals = metadata.get('total_terminals', 0)
                    stats = metadata.get('combined_statistics', {})
                    success_rate = stats.get('success_rate', 0)
                    
                    print(f"📈 Total terminals processed: {total_terminals}")
                    print(f"📈 Success rate: {success_rate:.1f}%")
                    
                except Exception as e:
                    print(f"⚠️  Could not read result statistics: {e}")
            
            return True
        else:
            print(f"❌ Full retrieval failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running full retrieval: {e}")
        return False

def main():
    """Main monitoring and retrieval function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor connectivity and run ATM retrieval')
    parser.add_argument('--demo', action='store_true', 
                       help='Run in demo mode (no network required)')
    parser.add_argument('--run-now', action='store_true', 
                       help='Run retrieval immediately without connectivity check')
    parser.add_argument('--check-interval', type=int, default=60, 
                       help='Connectivity check interval in seconds (default: 60)')
    parser.add_argument('--max-checks', type=int, default=1440, 
                       help='Maximum number of connectivity checks (default: 1440 = 24 hours)')
    
    args = parser.parse_args()
    
    print(f"ATM Network Connectivity Monitor")
    print(f"{'='*50}")
    print(f"Demo mode: {args.demo}")
    print(f"Check interval: {args.check_interval} seconds")
    print(f"Maximum checks: {args.max_checks}")
    
    if args.run_now or args.demo:
        # Run immediately
        print("\n🚀 Running retrieval immediately...")
        success = run_full_retrieval(demo_mode=args.demo)
        return 0 if success else 1
    
    # Monitor connectivity
    print(f"\n👀 Starting connectivity monitoring...")
    check_count = 0
    
    while check_count < args.max_checks:
        check_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        connected, status = check_atm_connectivity()
        
        if connected:
            print(f"✅ [{timestamp}] Connection established! Status: {status}")
            print(f"🎯 Starting automatic retrieval...")
            
            success = run_full_retrieval(demo_mode=False)
            
            if success:
                print(f"🎉 Automatic retrieval completed successfully!")
                return 0
            else:
                print(f"❌ Automatic retrieval failed, continuing monitoring...")
        else:
            print(f"❌ [{timestamp}] Check {check_count}/{args.max_checks}: No connection ({status})")
        
        if check_count < args.max_checks:
            print(f"⏳ Waiting {args.check_interval} seconds for next check...")
            time.sleep(args.check_interval)
    
    print(f"\n⏰ Maximum connectivity checks reached ({args.max_checks})")
    print(f"🛑 Monitoring stopped")
    return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
