#!/usr/bin/env python3
"""
Test script to verify that all 14 terminals are correctly processed in PHASE 3
"""

from backend.combined_atm_retrieval_script import CombinedATMRetriever

def test_terminal_collection():
    """Test the terminal collection logic in demo mode"""
    
    # Expected terminal IDs based on user requirements
    expected_terminals = [
        '83', '2603', '88', '147', '87', '169', '2605', '2604', 
        '93', '49', '86', '89', '85', '90'
    ]
    
    print("=" * 80)
    print("TESTING TERMINAL COLLECTION LOGIC - PHASE 3 VERIFICATION")
    print("=" * 80)
    
    print(f"Expected terminals: {sorted(expected_terminals)}")
    print(f"Expected count: {len(expected_terminals)}")
    
    # Initialize retriever in demo mode
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    print("\n--- STEP 1: Testing individual status collections ---")
    
    # Test each parameter value individually
    all_collected_terminals = []
    status_breakdown = {}
    
    parameter_values = ['AVAILABLE', 'WARNING', 'WOUNDED', 'HARD', 'CASH', 'ZOMBIE', 'UNAVAILABLE']
    
    for param_value in parameter_values:
        terminals = retriever.get_terminals_by_status(param_value)
        terminal_ids = [t.get('terminalId') for t in terminals if t.get('terminalId')]
        
        status_breakdown[param_value] = terminal_ids
        all_collected_terminals.extend(terminal_ids)
        
        print(f"  {param_value}: {len(terminal_ids)} terminals -> {terminal_ids}")
    
    print(f"\n--- STEP 2: Analyzing collection results ---")
    print(f"Total terminals collected (with duplicates): {len(all_collected_terminals)}")
    
    # Remove duplicates
    unique_terminals = list(set(all_collected_terminals))
    print(f"Unique terminals collected: {len(unique_terminals)}")
    print(f"Unique terminal IDs: {sorted(unique_terminals)}")
    
    # Compare with expected
    missing_terminals = set(expected_terminals) - set(unique_terminals)
    extra_terminals = set(unique_terminals) - set(expected_terminals)
    
    print(f"\n--- STEP 3: Verification Results ---")
    
    if missing_terminals:
        print(f"❌ MISSING terminals: {sorted(missing_terminals)}")
    else:
        print("✅ No missing terminals")
    
    if extra_terminals:
        print(f"⚠️  EXTRA terminals: {sorted(extra_terminals)}")
    else:
        print("✅ No extra terminals")
    
    if len(unique_terminals) == 14 and not missing_terminals:
        print("✅ SUCCESS: All 14 expected terminals are collected!")
    else:
        print(f"❌ ISSUE: Expected 14 terminals, got {len(unique_terminals)}")
    
    print(f"\n--- STEP 4: Testing PHASE 3 deduplication logic ---")
    
    # Simulate the deduplication logic from retrieve_and_process_all_data
    all_terminals_with_status = []
    for param_value in parameter_values:
        terminals = retriever.get_terminals_by_status(param_value)
        for terminal in terminals:
            terminal['fetched_status'] = param_value
            all_terminals_with_status.append(terminal)
    
    print(f"Total terminals before deduplication: {len(all_terminals_with_status)}")
    
    # Apply the same deduplication logic as in the script
    unique_terminals_dict = {}
    duplicate_count = 0
    
    for terminal in all_terminals_with_status:
        terminal_id = terminal.get('terminalId')
        if terminal_id:
            if terminal_id in unique_terminals_dict:
                duplicate_count += 1
                print(f"  Duplicate found: {terminal_id} (status: {terminal.get('fetched_status')} vs existing: {unique_terminals_dict[terminal_id].get('fetched_status')})")
            else:
                unique_terminals_dict[terminal_id] = terminal
    
    final_terminals = list(unique_terminals_dict.values())
    final_terminal_ids = [t.get('terminalId') for t in final_terminals]
    
    print(f"Terminals after deduplication: {len(final_terminals)}")
    print(f"Removed {duplicate_count} duplicates")
    print(f"Final terminal IDs for PHASE 3: {sorted(final_terminal_ids)}")
    
    print(f"\n--- FINAL VERIFICATION ---")
    if len(final_terminal_ids) == 14 and set(final_terminal_ids) == set(expected_terminals):
        print("🎉 SUCCESS: PHASE 3 will process exactly the 14 expected terminals!")
        return True
    else:
        print(f"❌ ISSUE: PHASE 3 will process {len(final_terminal_ids)} terminals instead of 14")
        print(f"Missing: {set(expected_terminals) - set(final_terminal_ids)}")
        print(f"Extra: {set(final_terminal_ids) - set(expected_terminals)}")
        return False

if __name__ == "__main__":
    success = test_terminal_collection()
    exit(0 if success else 1)
