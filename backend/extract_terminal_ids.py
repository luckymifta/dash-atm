#!/usr/bin/env python3
"""
Extract all terminal IDs from existing ATM data files to create a comprehensive list
for terminal details retrieval.
"""

import json
import glob
import os
from typing import Set, List, Dict, Any

def extract_terminal_ids_from_file(file_path: str) -> Set[str]:
    """Extract terminal IDs from a single JSON file"""
    terminal_ids = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different data structures
        if isinstance(data, dict):
            if 'atm_data' in data:
                # Format from atm_details_*.json files
                for terminal in data['atm_data']:
                    terminal_id = terminal.get('terminal_id')
                    if terminal_id:
                        terminal_ids.add(str(terminal_id))
            
            elif 'terminal_details' in data:
                # Format from retrieval output files
                for terminal in data['terminal_details']:
                    terminal_id = terminal.get('terminal_id')
                    if terminal_id:
                        terminal_ids.add(str(terminal_id))
            
            elif 'terminals' in data:
                # Direct terminal list
                for terminal in data['terminals']:
                    terminal_id = terminal.get('terminal_id') or terminal.get('terminalId')
                    if terminal_id:
                        terminal_ids.add(str(terminal_id))
        
        elif isinstance(data, list):
            # Direct list of terminals
            for terminal in data:
                if isinstance(terminal, dict):
                    terminal_id = terminal.get('terminal_id') or terminal.get('terminalId')
                    if terminal_id:
                        terminal_ids.add(str(terminal_id))
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return terminal_ids

def main():
    """Extract all terminal IDs and create configuration files"""
    
    # Get all JSON files
    json_files = glob.glob("atm_*.json")
    
    all_terminal_ids = set()
    files_processed = 0
    
    print("Extracting terminal IDs from JSON files...")
    
    for file_path in json_files:
        if os.path.isfile(file_path):
            print(f"Processing: {file_path}")
            terminal_ids = extract_terminal_ids_from_file(file_path)
            all_terminal_ids.update(terminal_ids)
            files_processed += 1
            print(f"  Found {len(terminal_ids)} terminal IDs")
    
    print(f"\nProcessed {files_processed} files")
    print(f"Total unique terminal IDs found: {len(all_terminal_ids)}")
    
    # Sort terminal IDs numerically where possible
    sorted_terminal_ids = sorted(all_terminal_ids, key=lambda x: int(x) if x.isdigit() else float('inf'))
    
    # Create different configuration formats
    
    # 1. Simple list for command line use
    simple_list = ','.join(sorted_terminal_ids)
    with open('terminal_ids_list.txt', 'w') as f:
        f.write(simple_list)
    print(f"✅ Saved simple list to: terminal_ids_list.txt")
    
    # 2. JSON configuration for script input
    terminal_configs = []
    
    # Categorize terminals by likely issue states based on ID patterns
    for terminal_id in sorted_terminal_ids:
        # Default to HARD for comprehensive fault checking
        issue_state_code = "HARD"
        
        # You can customize this logic based on your knowledge of the terminals
        if terminal_id.isdigit():
            tid_num = int(terminal_id)
            if tid_num < 100:
                issue_state_code = "HARD"  # Lower IDs might have more hardware issues
            elif tid_num < 1000:
                issue_state_code = "CASH"  # Mid-range might have cash issues
            else:
                issue_state_code = "WARNING"  # Higher IDs might have warnings
        
        terminal_configs.append({
            "terminal_id": terminal_id,
            "issue_state_code": issue_state_code
        })
    
    config_data = {
        "description": "Comprehensive terminal configuration for ATM details retrieval",
        "generated_on": "2025-05-30",
        "total_terminals": len(terminal_configs),
        "terminals": terminal_configs
    }
    
    with open('terminals_config.json', 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved JSON configuration to: terminals_config.json")
    
    # 3. Create batches for processing (to avoid overwhelming the server)
    batch_size = 20
    batches = []
    
    for i in range(0, len(terminal_configs), batch_size):
        batch = terminal_configs[i:i + batch_size]
        batches.append({
            "batch_number": len(batches) + 1,
            "terminals": batch
        })
    
    for i, batch in enumerate(batches, 1):
        batch_filename = f'terminals_batch_{i:02d}.json'
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump(batch, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved batch {i} to: {batch_filename} ({len(batch['terminals'])} terminals)")
    
    # Display some statistics
    print(f"\nTerminal ID Statistics:")
    print(f"  Total unique terminals: {len(all_terminal_ids)}")
    print(f"  Numeric IDs: {len([tid for tid in sorted_terminal_ids if tid.isdigit()])}")
    print(f"  Non-numeric IDs: {len([tid for tid in sorted_terminal_ids if not tid.isdigit()])}")
    print(f"  Created {len(batches)} batches of {batch_size} terminals each")
    
    # Show first few terminal IDs as sample
    print(f"\nSample terminal IDs:")
    for tid in sorted_terminal_ids[:10]:
        print(f"  {tid}")
    if len(sorted_terminal_ids) > 10:
        print(f"  ... and {len(sorted_terminal_ids) - 10} more")

if __name__ == "__main__":
    main()
