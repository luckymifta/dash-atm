#!/usr/bin/env python3
"""
Example script showing how to use the new database logging system
with the Combined ATM Retrieval Script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from combined_atm_retrieval_script import CombinedATMRetriever
import logging

def main():
    """
    Example of running the ATM retrieval with database logging enabled
    """
    
    print("🚀 Starting ATM Retrieval with Database Logging")
    print("=" * 60)
    
    try:
        # Initialize retriever with database logging enabled
        retriever = CombinedATMRetriever(
            demo_mode=False,  # Set to True for testing
            total_atms=14,
            enable_db_logging=True  # Enable database logging
        )
        
        # Run the complete retrieval process
        success, all_data = retriever.retrieve_and_process_all_data(
            save_to_db=True,
            use_new_tables=True  # Use new database tables with JSONB support
        )
        
        if success:
            print("✅ ATM data retrieval completed successfully!")
            print(f"   - Regional records: {len(all_data.get('regional_data', []))}")
            print(f"   - Terminal details: {len(all_data.get('terminal_details_data', []))}")
            print(f"   - Failover mode: {all_data.get('failover_mode', False)}")
            
            # Summary information
            summary = all_data.get('summary', {})
            if 'status_counts' in summary:
                print("   - Status distribution:")
                for status, count in summary['status_counts'].items():
                    print(f"     {status}: {count}")
        else:
            print("❌ ATM data retrieval failed")
            
    except Exception as e:
        logging.error(f"Error during ATM retrieval: {e}")
        print(f"❌ Error: {e}")
        
    print("=" * 60)
    print("🏁 ATM Retrieval with Database Logging Complete")

if __name__ == "__main__":
    main()
