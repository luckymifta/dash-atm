#!/usr/bin/env python3
"""
Debug Terminal Collection Script

This script helps diagnose why combined_atm_retrieval_script.py is only 
retrieving 13 terminals instead of the expected 14 ATMs.

It will:
1. Run each PARAMETER_VALUE separately to see how many terminals each status returns
2. Check for duplicate terminal IDs across different statuses
3. Identify which ATM might be missing or getting filtered out
4. Provide recommendations for fixing the issue
"""

import json
import logging
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set
import sys
import os

# Add the backend directory to the path so we can import from combined_atm_retrieval_script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from combined_atm_retrieval_script import CombinedATMRetriever, PARAMETER_VALUES

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler("debug_terminal_collection.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("DebugTerminalCollection")

def analyze_terminal_collection(demo_mode: bool = False):
    """
    Analyze terminal collection by status to identify the 13 vs 14 issue
    """
    log.info("=" * 80)
    log.info("DEBUGGING TERMINAL COLLECTION FOR 13 vs 14 ATM ISSUE")
    log.info("=" * 80)
    
    retriever = CombinedATMRetriever(demo_mode=demo_mode, total_atms=14)
    
    # Step 1: Authenticate
    if not retriever.authenticate():
        log.error("Authentication failed - cannot proceed with debugging")
        return
    
    # Step 2: Collect terminals for each status separately
    all_terminals_by_status = {}
    all_terminal_ids = set()
    terminal_id_to_statuses = defaultdict(list)
    
    log.info("\n--- STEP 1: Collecting terminals by individual status ---")
    
    for param_value in PARAMETER_VALUES:
        log.info(f"\nFetching terminals for status: {param_value}")
        terminals = retriever.get_terminals_by_status(param_value)
        
        if terminals:
            log.info(f"✅ Found {len(terminals)} terminals for status {param_value}")
            all_terminals_by_status[param_value] = terminals
            
            # Track terminal IDs and which statuses they appear in
            for terminal in terminals:
                terminal_id = terminal.get('terminalId', 'UNKNOWN')
                all_terminal_ids.add(terminal_id)
                terminal_id_to_statuses[terminal_id].append(param_value)
                log.debug(f"   Terminal {terminal_id} found in status {param_value}")
        else:
            log.warning(f"❌ No terminals found for status {param_value}")
            all_terminals_by_status[param_value] = []
    
    # Step 3: Analysis
    log.info("\n--- STEP 2: Analysis Results ---")
    
    total_unique_terminals = len(all_terminal_ids)
    total_terminal_instances = sum(len(terminals) for terminals in all_terminals_by_status.values())
    
    log.info(f"📊 SUMMARY:")
    log.info(f"   Total unique terminal IDs found: {total_unique_terminals}")
    log.info(f"   Total terminal instances across all statuses: {total_terminal_instances}")
    log.info(f"   Expected terminals: 14")
    log.info(f"   Missing terminals: {14 - total_unique_terminals}")
    
    # Show status breakdown
    log.info(f"\n📋 BREAKDOWN BY STATUS:")
    for status, terminals in all_terminals_by_status.items():
        log.info(f"   {status}: {len(terminals)} terminals")
        if terminals:
            ids = [t.get('terminalId', 'UNKNOWN') for t in terminals]
            log.info(f"     IDs: {', '.join(ids)}")
    
    # Check for duplicates
    log.info(f"\n🔍 DUPLICATE ANALYSIS:")
    duplicates_found = False
    for terminal_id, statuses in terminal_id_to_statuses.items():
        if len(statuses) > 1:
            duplicates_found = True
            log.warning(f"   Terminal {terminal_id} appears in multiple statuses: {', '.join(statuses)}")
    
    if not duplicates_found:
        log.info("   ✅ No duplicates found - each terminal appears in only one status")
    
    # Step 4: Compare with combined collection (simulating the actual script logic)
    log.info("\n--- STEP 3: Simulating Combined Collection Logic ---")
    
    combined_terminals = []
    status_counts = {}
    
    for param_value in PARAMETER_VALUES:
        terminals = all_terminals_by_status.get(param_value, [])
        
        if terminals:
            # Add each terminal to our combined list for detail processing
            for terminal in terminals:
                # Add the status we searched for (this is what the actual script does)
                terminal['fetched_status'] = param_value
                combined_terminals.append(terminal)
            
            # Track how many terminals we found for each status
            status_counts[param_value] = len(terminals)
            log.info(f"Added {len(terminals)} terminals with status {param_value} to combined list")
        else:
            log.warning(f"No terminals found with status {param_value}")
            status_counts[param_value] = 0
    
    log.info(f"\n📊 COMBINED COLLECTION RESULTS:")
    log.info(f"   Total terminals in combined list: {len(combined_terminals)}")
    log.info(f"   Unique terminal IDs in combined list: {len(set(t.get('terminalId', 'UNKNOWN') for t in combined_terminals))}")
    
    # Check if the combined logic loses any terminals
    combined_terminal_ids = set(t.get('terminalId', 'UNKNOWN') for t in combined_terminals)
    missing_in_combined = all_terminal_ids - combined_terminal_ids
    extra_in_combined = combined_terminal_ids - all_terminal_ids
    
    if missing_in_combined:
        log.error(f"   ❌ Terminals lost in combined logic: {', '.join(missing_in_combined)}")
    if extra_in_combined:
        log.warning(f"   ⚠️ Extra terminals in combined logic: {', '.join(extra_in_combined)}")
    
    # Step 5: Recommendations
    log.info("\n--- STEP 4: Recommendations ---")
    
    if total_unique_terminals < 14:
        log.warning(f"🔧 ISSUE IDENTIFIED: Only {total_unique_terminals} unique terminals found, expected 14")
        log.info("   Possible causes:")
        log.info("   1. One or more ATMs are in a status not covered by PARAMETER_VALUES")
        log.info("   2. Network/API issues preventing retrieval of some terminals")
        log.info("   3. ATM is temporarily offline or in maintenance mode")
        log.info("   4. Authentication/permission issues for certain terminal data")
        
        log.info("   Recommendations:")
        log.info("   1. Check the ATM monitoring dashboard manually to see all 14 terminals")
        log.info("   2. Look for additional status types not in PARAMETER_VALUES")
        log.info("   3. Check if any ATMs are in 'MAINTENANCE' or 'OFFLINE' status")
        log.info("   4. Run the script multiple times to see if the issue is intermittent")
    
    elif len(combined_terminals) < total_unique_terminals:
        log.warning("🔧 ISSUE IDENTIFIED: Combined collection logic is losing terminals")
        log.info("   This suggests an issue with the collection logic itself")
    
    else:
        log.info("✅ No obvious issues found with terminal collection logic")
        log.info("   The issue might be:")
        log.info("   1. Intermittent network issues")
        log.info("   2. Timing-related problems")
        log.info("   3. Status-specific filtering by the API")
    
    # Step 6: Save detailed results
    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "demo_mode": demo_mode,
        "analysis_results": {
            "total_unique_terminals": total_unique_terminals,
            "total_terminal_instances": total_terminal_instances,
            "expected_terminals": 14,
            "missing_count": 14 - total_unique_terminals,
            "terminals_by_status": {
                status: [t.get('terminalId', 'UNKNOWN') for t in terminals]
                for status, terminals in all_terminals_by_status.items()
            },
            "duplicate_analysis": {
                terminal_id: statuses 
                for terminal_id, statuses in terminal_id_to_statuses.items()
                if len(statuses) > 1
            },
            "all_terminal_ids": sorted(list(all_terminal_ids)),
            "status_counts": status_counts
        },
        "raw_terminal_data": all_terminals_by_status
    }
    
    debug_filename = f"terminal_collection_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(debug_filename, 'w') as f:
        json.dump(debug_data, f, indent=2, default=str)
    
    log.info(f"\n💾 Detailed debug data saved to: {debug_filename}")
    log.info("\n" + "=" * 80)
    log.info("DEBUG ANALYSIS COMPLETE")
    log.info("=" * 80)
    
    return debug_data

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Debug Terminal Collection - Find why only 13 instead of 14 ATMs are retrieved"
    )
    parser.add_argument('--demo', action='store_true', 
                       help='Run in demo mode (no actual network requests)')
    
    args = parser.parse_args()
    
    try:
        analyze_terminal_collection(demo_mode=args.demo)
        return 0
    except Exception as e:
        log.error(f"Debug analysis failed: {str(e)}")
        log.debug("Error details:", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
