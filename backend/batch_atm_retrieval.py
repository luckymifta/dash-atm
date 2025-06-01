#!/usr/bin/env python3
"""
Batch ATM Details Retrieval Runner
==================================

This script runs the ATM details retrieval in manageable batches to avoid
overwhelming the server and to provide better progress tracking.
"""

import json
import time
import subprocess
import sys
import os
from datetime import datetime

def load_terminal_config(config_file):
    """Load terminal configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
        return data.get('terminals', [])
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return []

def create_batches(terminals, batch_size=10):
    """Split terminals into batches"""
    batches = []
    for i in range(0, len(terminals), batch_size):
        batch = terminals[i:i + batch_size]
        batches.append(batch)
    return batches

def run_batch_retrieval(batch_terminals, batch_num, total_batches, demo_mode=False, verbose=False):
    """Run retrieval for a single batch"""
    print(f"\n{'='*60}")
    print(f"PROCESSING BATCH {batch_num}/{total_batches}")
    print(f"Terminals in this batch: {len(batch_terminals)}")
    print(f"{'='*60}")
    
    # Create terminal ID list
    terminal_ids = [t['terminal_id'] for t in batch_terminals]
    terminal_ids_str = ','.join(terminal_ids)
    
    # Build command
    cmd = [
        'python', 'atm_details_retrieval.py',
        '--terminals', terminal_ids_str,
        '--output', f'batch_{batch_num:03d}_results.json'
    ]
    
    if demo_mode:
        cmd.append('--demo')
    
    if verbose:
        cmd.append('--verbose')
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Terminal IDs: {terminal_ids}")
    
    # Run the command
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        print(f"Batch {batch_num} completed in {end_time - start_time:.1f} seconds")
        
        if result.returncode == 0:
            print(f"✅ Batch {batch_num} SUCCESS")
            if verbose:
                print("STDOUT:", result.stdout)
        else:
            print(f"❌ Batch {batch_num} FAILED (exit code: {result.returncode})")
            print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Batch {batch_num} TIMEOUT (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Batch {batch_num} ERROR: {e}")
        return False

def combine_batch_results(num_batches, output_file='combined_atm_details.json'):
    """Combine all batch results into a single file"""
    print(f"\n{'='*60}")
    print("COMBINING BATCH RESULTS")
    print(f"{'='*60}")
    
    combined_results = []
    combined_metadata = {
        "combined_timestamp": datetime.now().isoformat(),
        "total_batches": num_batches,
        "successful_batches": 0,
        "total_terminals": 0,
        "combined_statistics": {
            "total_requested": 0,
            "successful_retrievals": 0,
            "failed_retrievals": 0,
            "token_refreshes": 0,
            "retries_performed": 0
        }
    }
    
    for batch_num in range(1, num_batches + 1):
        batch_file = f'batch_{batch_num:03d}_results.json'
        
        if os.path.exists(batch_file):
            try:
                with open(batch_file, 'r') as f:
                    batch_data = json.load(f)
                
                # Extract terminal details
                terminal_details = batch_data.get('terminal_details', [])
                combined_results.extend(terminal_details)
                
                # Aggregate statistics
                batch_stats = batch_data.get('retrieval_metadata', {}).get('statistics', {})
                for key in combined_metadata["combined_statistics"]:
                    combined_metadata["combined_statistics"][key] += batch_stats.get(key, 0)
                
                combined_metadata["successful_batches"] += 1
                print(f"✅ Batch {batch_num}: {len(terminal_details)} terminals")
                
            except Exception as e:
                print(f"❌ Error reading batch {batch_num}: {e}")
        else:
            print(f"⚠️  Batch file {batch_file} not found")
    
    combined_metadata["total_terminals"] = len(combined_results)
    
    # Calculate combined success rate
    total_req = combined_metadata["combined_statistics"]["total_requested"]
    successful = combined_metadata["combined_statistics"]["successful_retrievals"]
    combined_metadata["combined_statistics"]["success_rate"] = (
        (successful / total_req * 100) if total_req > 0 else 0
    )
    
    # Save combined results
    final_output = {
        "retrieval_metadata": combined_metadata,
        "terminal_details": combined_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"  Total terminals processed: {len(combined_results)}")
    print(f"  Successful batches: {combined_metadata['successful_batches']}/{num_batches}")
    print(f"  Overall success rate: {combined_metadata['combined_statistics']['success_rate']:.1f}%")
    print(f"  Combined results saved to: {output_file}")
    
    return output_file

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ATM details retrieval in batches')
    parser.add_argument('--config', default='all_terminals_config.json', 
                       help='Terminal configuration file (default: all_terminals_config.json)')
    parser.add_argument('--batch-size', type=int, default=10, 
                       help='Number of terminals per batch (default: 10)')
    parser.add_argument('--demo', action='store_true', 
                       help='Run in demo mode')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('--delay', type=int, default=30, 
                       help='Delay between batches in seconds (default: 30)')
    parser.add_argument('--max-batches', type=int, 
                       help='Maximum number of batches to process (for testing)')
    
    args = parser.parse_args()
    
    print(f"ATM Details Batch Retrieval Runner")
    print(f"{'='*60}")
    print(f"Configuration file: {args.config}")
    print(f"Batch size: {args.batch_size}")
    print(f"Demo mode: {args.demo}")
    print(f"Delay between batches: {args.delay} seconds")
    
    # Load terminal configuration
    terminals = load_terminal_config(args.config)
    if not terminals:
        print("❌ No terminals loaded from configuration file")
        return 1
    
    print(f"Loaded {len(terminals)} terminals from configuration")
    
    # Create batches
    batches = create_batches(terminals, args.batch_size)
    total_batches = len(batches)
    
    if args.max_batches:
        batches = batches[:args.max_batches]
        total_batches = len(batches)
        print(f"Limited to {total_batches} batches for testing")
    
    print(f"Created {total_batches} batches")
    
    # Process each batch
    successful_batches = 0
    start_time = time.time()
    
    for i, batch_terminals in enumerate(batches, 1):
        success = run_batch_retrieval(
            batch_terminals, i, total_batches, 
            demo_mode=args.demo, verbose=args.verbose
        )
        
        if success:
            successful_batches += 1
        
        # Delay between batches (except for the last one)
        if i < total_batches and args.delay > 0:
            print(f"⏳ Waiting {args.delay} seconds before next batch...")
            time.sleep(args.delay)
    
    end_time = time.time()
    
    # Combine results
    if successful_batches > 0:
        combined_file = combine_batch_results(total_batches)
        
        print(f"\n🎉 BATCH PROCESSING COMPLETED!")
        print(f"  Total time: {(end_time - start_time) / 60:.1f} minutes")
        print(f"  Successful batches: {successful_batches}/{total_batches}")
        print(f"  Combined results: {combined_file}")
        
        return 0
    else:
        print(f"\n❌ NO SUCCESSFUL BATCHES")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
