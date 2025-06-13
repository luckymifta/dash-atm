#!/usr/bin/env python3
"""
Test script to verify the comprehensive_terminal_search method
"""

from backend.combined_atm_retrieval_script import CombinedATMRetriever

def test_comprehensive_search():
    """Test the comprehensive terminal search method"""
    
    # Expected terminal IDs based on user requirements
    expected_terminals = [
        '83', '2603', '88', '147', '87', '169', '2605', '2604', 
        '93', '49', '86', '89', '85', '90'
    ]
    
    print("=" * 80)
    print("TESTING COMPREHENSIVE TERMINAL SEARCH METHOD")
    print("=" * 80)
    
    print(f"Expected terminals: {sorted(expected_terminals)}")
    print(f"Expected count: {len(expected_terminals)}")
    
    # Initialize retriever in demo mode
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    print("\n--- Testing comprehensive_terminal_search method ---")
    
    try:
        # Test the comprehensive search method
        all_terminals, status_counts = retriever.comprehensive_terminal_search()
        
        print(f"\n--- METHOD RESULTS ---")
        print(f"Returned {len(all_terminals)} terminals")
        print(f"Status counts: {status_counts}")
        
        # Extract terminal IDs
        found_terminal_ids = [t.get('terminalId') for t in all_terminals if t.get('terminalId')]
        
        print(f"Found terminal IDs: {sorted(found_terminal_ids)}")
        
        # Verify all terminals have required fields
        print(f"\n--- DATA SCHEMA VALIDATION ---")
        
        missing_fields_count = 0
        for terminal in all_terminals:
            terminal_id = terminal.get('terminalId')
            
            # Check required fields
            required_fields = ['terminalId', 'fetched_status', 'issueStateCode']
            missing_fields = [field for field in required_fields if not terminal.get(field)]
            
            if missing_fields:
                print(f"❌ Terminal {terminal_id} missing fields: {missing_fields}")
                missing_fields_count += 1
            else:
                print(f"✅ Terminal {terminal_id}: fetched_status={terminal.get('fetched_status')}, issueStateCode={terminal.get('issueStateCode')}")
        
        if missing_fields_count == 0:
            print("✅ All terminals have required data schema fields")
        else:
            print(f"❌ {missing_fields_count} terminals missing required fields")
        
        # Final verification
        print(f"\n--- FINAL VERIFICATION ---")
        
        missing_terminals = set(expected_terminals) - set(found_terminal_ids)
        extra_terminals = set(found_terminal_ids) - set(expected_terminals)
        
        if missing_terminals:
            print(f"❌ MISSING terminals: {sorted(missing_terminals)}")
        else:
            print("✅ No missing terminals")
        
        if extra_terminals:
            print(f"⚠️  EXTRA terminals: {sorted(extra_terminals)}")
        else:
            print("✅ No extra terminals")
        
        if len(found_terminal_ids) == 14 and not missing_terminals and missing_fields_count == 0:
            print("🎉 SUCCESS: Comprehensive search method works perfectly!")
            print("🎉 All 14 terminals found with correct data schema!")
            return True
        else:
            print(f"❌ ISSUES FOUND:")
            if len(found_terminal_ids) != 14:
                print(f"   - Expected 14 terminals, got {len(found_terminal_ids)}")
            if missing_terminals:
                print(f"   - Missing terminals: {sorted(missing_terminals)}")
            if missing_fields_count > 0:
                print(f"   - {missing_fields_count} terminals with missing fields")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during comprehensive search test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_search()
    exit(0 if success else 1)
