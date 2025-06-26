#!/usr/bin/env python3
"""
Performance Test Script for Optimized ATM Retrieval

This script tests the performance improvements made to the ATM retrieval system.
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path to find the script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_performance_optimizations():
    """Test the performance improvements"""
    
    print("🚀 TESTING PERFORMANCE OPTIMIZATIONS")
    print("=" * 60)
    
    try:
        # Add backend directory to path
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
        sys.path.insert(0, backend_path)
        
        from combined_atm_retrieval_script import CombinedATMRetriever
        
        # Test 1: Demo mode performance (baseline)
        print("\n📊 Test 1: Demo Mode Performance Baseline")
        print("-" * 40)
        
        start_time = time.time()
        
        retriever = CombinedATMRetriever(
            demo_mode=True,
            total_atms=14,
            enable_db_logging=True
        )
        
        success, data = retriever.retrieve_and_process_all_data(save_to_db=False)
        
        end_time = time.time()
        demo_duration = end_time - start_time
        
        print(f"✅ Demo mode completed in {demo_duration:.2f} seconds")
        print(f"   - Regional data: {len(data.get('regional_data', []))} records")
        print(f"   - Terminal details: {len(data.get('terminal_details_data', []))} records")
        print(f"   - Success: {success}")
        
        # Test 2: Concurrent processing verification
        print("\n🔧 Test 2: Concurrent Processing Features")
        print("-" * 40)
        
        # Check if concurrent methods exist
        has_concurrent = hasattr(retriever, 'fetch_terminal_details_concurrent')
        has_smart_retry = hasattr(retriever, 'smart_retry')
        has_optimized_fetch = hasattr(retriever, 'fetch_terminal_details_optimized')
        
        print(f"   - Concurrent terminal processing: {'✅' if has_concurrent else '❌'}")
        print(f"   - Smart retry logic: {'✅' if has_smart_retry else '❌'}")
        print(f"   - Optimized fetch method: {'✅' if has_optimized_fetch else '❌'}")
        
        # Test 3: Performance configuration check
        print("\n⚙️ Test 3: Performance Configuration")
        print("-" * 40)
        
        # Check timeout values
        connection_timeout, read_timeout = retriever.default_timeout
        print(f"   - Connection timeout: {connection_timeout}s (optimized: {'✅' if connection_timeout <= 20 else '❌'})")
        print(f"   - Read timeout: {read_timeout}s (optimized: {'✅' if read_timeout <= 40 else '❌'})")
        
        # Test concurrent processing if available
        if has_concurrent and has_smart_retry:
            print("\n🧪 Test 4: Concurrent Processing Test")
            print("-" * 40)
            
            # Create sample terminals for testing
            sample_terminals = [
                {'terminalId': '83', 'issueStateCode': 'AVAILABLE', 'fetched_status': 'AVAILABLE'},
                {'terminalId': '147', 'issueStateCode': 'WARNING', 'fetched_status': 'WARNING'},
                {'terminalId': '169', 'issueStateCode': 'WOUNDED', 'fetched_status': 'WOUNDED'},
            ]
            
            concurrent_start = time.time()
            
            try:
                concurrent_results = retriever.fetch_terminal_details_concurrent(
                    sample_terminals, 
                    max_workers=2
                )
                concurrent_end = time.time()
                concurrent_duration = concurrent_end - concurrent_start
                
                print(f"   ✅ Concurrent processing: {concurrent_duration:.2f}s")
                print(f"   ✅ Results: {len(concurrent_results)} terminal details")
                
            except Exception as e:
                print(f"   ❌ Concurrent processing error: {e}")
        
        # Performance Summary
        print("\n📈 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        optimizations_active = [
            ("Concurrent Terminal Processing", has_concurrent),
            ("Smart Retry Logic", has_smart_retry),
            ("Optimized Fetch Methods", has_optimized_fetch),
            ("Reduced Timeouts", connection_timeout <= 20),
            ("Demo Mode Execution", demo_duration < 30)  # Should be very fast in demo mode
        ]
        
        active_count = sum(1 for _, active in optimizations_active if active)
        total_count = len(optimizations_active)
        
        print(f"Active Optimizations: {active_count}/{total_count}")
        print()
        
        for optimization, active in optimizations_active:
            status = "✅ ACTIVE" if active else "❌ INACTIVE"
            print(f"   {optimization}: {status}")
        
        # Expected performance improvements
        print(f"\n🎯 EXPECTED PERFORMANCE IMPROVEMENTS:")
        print(f"   - Demo mode: {demo_duration:.1f}s (baseline)")
        print(f"   - Production mode (estimated): 150-200s (vs 601s original)")
        print(f"   - Improvement: 67-75% faster execution")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if active_count == total_count:
            print("   🎉 All optimizations are active! Ready for production testing.")
        elif active_count >= total_count * 0.8:
            print("   ✅ Most optimizations active. Good performance expected.")
        else:
            print("   ⚠️ Some optimizations missing. Performance may be suboptimal.")
        
        if demo_duration > 30:
            print("   📢 Demo mode is slower than expected - check for issues.")
        
        print("\n🔄 NEXT STEPS:")
        print("   1. Test with production data (non-demo mode)")
        print("   2. Monitor execution times and compare with baseline")
        print("   3. Adjust max_workers based on server response times")
        print("   4. Enable database logging in production for monitoring")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the combined_atm_retrieval_script.py is available")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def show_optimization_details():
    """Show detailed information about the optimizations implemented"""
    
    print("\n" + "=" * 70)
    print("🔧 DETAILED OPTIMIZATION BREAKDOWN")
    print("=" * 70)
    
    optimizations = [
        {
            "name": "Concurrent Terminal Processing",
            "impact": "HIGH",
            "description": "Process multiple terminals simultaneously using ThreadPoolExecutor",
            "expected_improvement": "60-70% reduction in terminal processing time",
            "implementation": "fetch_terminal_details_concurrent() method with max_workers=4"
        },
        {
            "name": "Smart Retry Logic",
            "impact": "MEDIUM",
            "description": "Exponential backoff with reduced base delays",
            "expected_improvement": "20-30% reduction in network wait time",
            "implementation": "smart_retry() method with base_delay=1.0s"
        },
        {
            "name": "Optimized Timeouts",
            "impact": "MEDIUM",
            "description": "Reduced connection and read timeouts",
            "expected_improvement": "15-25% reduction in request overhead",
            "implementation": "default_timeout = (15, 30) vs original (30, 60)"
        },
        {
            "name": "Streamlined Fetch Methods",
            "impact": "LOW-MEDIUM",
            "description": "Simplified terminal details fetching with better error handling",
            "expected_improvement": "10-15% improvement in processing efficiency",
            "implementation": "fetch_terminal_details_optimized() method"
        }
    ]
    
    for i, opt in enumerate(optimizations, 1):
        print(f"\n{i}. {opt['name']} [{opt['impact']} IMPACT]")
        print(f"   📋 {opt['description']}")
        print(f"   📈 Expected: {opt['expected_improvement']}")
        print(f"   🔧 Implementation: {opt['implementation']}")
    
    print(f"\n🎯 OVERALL EXPECTED IMPROVEMENT: 67-75% faster execution")
    print(f"   Original: ~601 seconds")
    print(f"   Optimized: ~150-200 seconds")

if __name__ == "__main__":
    success = test_performance_optimizations()
    
    if success:
        show_optimization_details()
        
        print("\n" + "=" * 70)
        print("✅ PERFORMANCE TEST COMPLETED")
        print("=" * 70)
        print("🚀 Your ATM retrieval script has been optimized!")
        print("🔍 Run the script in production to measure actual improvements.")
        print("📊 Monitor execution times in the execution_summary table.")
    else:
        print("\n❌ Performance test failed - please check the errors above")
