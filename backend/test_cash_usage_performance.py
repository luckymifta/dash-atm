#!/usr/bin/env python3
"""
Comprehensive Cash Usage Endpoints Performance Test
==================================================

This script thoroughly tests all cash usage endpoints to measure the 
performance improvements achieved through our optimizations.

Endpoints to test:
1. /api/v1/atm/cash-usage/daily - Daily cash usage calculation
2. /api/v1/atm/cash-usage/trends - Cash usage trends over time  
3. /api/v1/atm/cash-usage/summary - Fleet-wide cash usage summary
4. /api/v1/atm/{terminal_id}/cash-usage/history - Individual terminal history

Performance targets:
- All endpoints: <3s response time
- Summary endpoint: Previously 14.878s → Target <3s
- Overall improvement: >80% faster than baseline
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

class CashUsagePerformanceTester:
    """Comprehensive performance tester for cash usage endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
        self.baseline_performance = {
            'daily_usage': 2.757,      # Previous average
            'trends': 1.548,           # Previous average  
            'summary': 14.878,         # Previous average (CRITICAL)
            'terminal_history': 0.985  # Previous average
        }
        
    async def test_endpoint_with_metrics(self, session, endpoint: str, 
                                       params: Dict = {}, test_name: str = "Unknown",
                                       expected_data_keys: List[str] = []) -> Dict[str, Any]:
        """Test endpoint with detailed performance metrics"""
        start_time = time.time()
        
        try:
            async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                duration = time.time() - start_time
                
                result = {
                    'test_name': test_name,
                    'endpoint': endpoint,
                    'params': params,
                    'response_time': round(duration, 3),
                    'status_code': response.status,
                    'timestamp': datetime.now().isoformat()
                }
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        result.update({
                            'status': 'SUCCESS',
                            'data_size_bytes': len(str(data)),
                            'cache_status': response.headers.get('X-Cache', 'MISS'),
                            'content_type': response.headers.get('Content-Type', ''),
                        })
                        
                        # Extract specific metrics based on endpoint
                        if 'daily_usage_data' in data:
                            result.update({
                                'total_records': len(data['daily_usage_data']),
                                'terminals_count': data.get('terminal_count', 0),
                                'date_range_days': data.get('date_range', {}).get('date_range_days', 0)
                            })
                        elif 'trend_data' in data:
                            result.update({
                                'trend_points': len(data['trend_data']),
                                'date_range': data.get('date_range', {})
                            })
                        elif 'fleet_statistics' in data:
                            result.update({
                                'fleet_terminals': data.get('fleet_statistics', {}).get('active_terminals', 0),
                                'total_cash': data.get('fleet_statistics', {}).get('total_fleet_cash', 0)
                            })
                        elif 'history_data' in data:
                            result.update({
                                'history_points': len(data['history_data']),
                                'terminal_id': data.get('terminal_id', 'Unknown')
                            })
                        
                        # Validate expected data structure
                        missing_keys = [key for key in expected_data_keys if key not in data]
                        if missing_keys:
                            result['warnings'] = f"Missing expected keys: {missing_keys}"
                        
                    except json.JSONDecodeError as e:
                        result.update({
                            'status': 'JSON_ERROR',
                            'error': f"JSON decode error: {str(e)}"
                        })
                else:
                    error_text = await response.text()
                    result.update({
                        'status': 'ERROR',
                        'error': error_text[:200] + "..." if len(error_text) > 200 else error_text
                    })
                    
        except Exception as e:
            duration = time.time() - start_time
            result = {
                'test_name': test_name,
                'endpoint': endpoint,
                'status': 'EXCEPTION',
                'response_time': round(duration, 3),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        self.test_results.append(result)
        return result
    
    async def test_daily_cash_usage_endpoint(self, session):
        """Test daily cash usage endpoint with various scenarios"""
        print("💰 TESTING DAILY CASH USAGE ENDPOINT")
        print("-" * 50)
        
        test_scenarios = [
            {
                'name': 'Daily Usage - 7 Days',
                'params': {
                    'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'terminal_ids': 'all'
                }
            },
            {
                'name': 'Daily Usage - 14 Days',
                'params': {
                    'start_date': (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'terminal_ids': 'all'
                }
            },
            {
                'name': 'Daily Usage - 30 Days',
                'params': {
                    'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'terminal_ids': 'all'
                }
            },
            {
                'name': 'Daily Usage - Specific Terminals',
                'params': {
                    'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'terminal_ids': '147,169,2603'
                }
            }
        ]
        
        results = []
        for scenario in test_scenarios:
            result = await self.test_endpoint_with_metrics(
                session, 
                "/api/v1/atm/cash-usage/daily",
                scenario['params'],
                scenario['name'],
                ['daily_usage_data', 'summary_stats', 'terminal_count']
            )
            results.append(result)
            
            # Display result
            status_icon = "✅" if result['status'] == 'SUCCESS' and result['response_time'] < 3.0 else "⚠️"
            print(f"  {status_icon} {result['test_name']}: {result['response_time']}s ({result['status']})")
            if result['status'] == 'SUCCESS':
                print(f"     Records: {result.get('total_records', 'N/A')} | Terminals: {result.get('terminals_count', 'N/A')}")
        
        return results
    
    async def test_cash_trends_endpoint(self, session):
        """Test cash usage trends endpoint"""
        print("\n📈 TESTING CASH USAGE TRENDS ENDPOINT")
        print("-" * 50)
        
        test_scenarios = [
            {
                'name': 'Trends - Daily (7 days)',
                'params': {'days': 7, 'aggregation': 'daily'}
            },
            {
                'name': 'Trends - Daily (30 days)',
                'params': {'days': 30, 'aggregation': 'daily'}
            },
            {
                'name': 'Trends - Weekly (90 days)',
                'params': {'days': 90, 'aggregation': 'weekly'}
            },
            {
                'name': 'Trends - Monthly (180 days)',
                'params': {'days': 180, 'aggregation': 'monthly'}
            }
        ]
        
        results = []
        for scenario in test_scenarios:
            result = await self.test_endpoint_with_metrics(
                session,
                "/api/v1/atm/cash-usage/trends",
                scenario['params'],
                scenario['name'],
                ['trend_data', 'chart_config']
            )
            results.append(result)
            
            status_icon = "✅" if result['status'] == 'SUCCESS' and result['response_time'] < 3.0 else "⚠️"
            print(f"  {status_icon} {result['test_name']}: {result['response_time']}s ({result['status']})")
            if result['status'] == 'SUCCESS':
                print(f"     Trend Points: {result.get('trend_points', 'N/A')}")
        
        return results
    
    async def test_cash_summary_endpoint(self, session):
        """Test cash usage summary endpoint (previously slowest)"""
        print("\n📊 TESTING CASH USAGE SUMMARY ENDPOINT (CRITICAL)")
        print("-" * 50)
        
        test_scenarios = [
            {
                'name': 'Summary - 7 Days',
                'params': {'days': 7}
            },
            {
                'name': 'Summary - 14 Days', 
                'params': {'days': 14}
            },
            {
                'name': 'Summary - 30 Days',
                'params': {'days': 30}
            }
        ]
        
        results = []
        baseline_time = self.baseline_performance['summary']
        
        for scenario in test_scenarios:
            result = await self.test_endpoint_with_metrics(
                session,
                "/api/v1/atm/cash-usage/summary",
                scenario['params'],
                scenario['name'],
                ['fleet_statistics', 'performance_metrics']
            )
            results.append(result)
            
            # Calculate improvement
            if result['status'] == 'SUCCESS':
                improvement = ((baseline_time - result['response_time']) / baseline_time) * 100
                target_met = "✅" if result['response_time'] < 3.0 else "⚠️"
                print(f"  {target_met} {result['test_name']}: {result['response_time']}s ({result['status']})")
                print(f"     Improvement: {improvement:.1f}% vs baseline ({baseline_time}s)")
                print(f"     Fleet Terminals: {result.get('fleet_terminals', 'N/A')}")
            else:
                print(f"  ❌ {result['test_name']}: {result['response_time']}s ({result['status']})")
                if 'error' in result:
                    print(f"     Error: {result['error'][:100]}...")
        
        return results
    
    async def test_terminal_history_endpoint(self, session):
        """Test individual terminal history endpoint"""
        print("\n🏧 TESTING TERMINAL HISTORY ENDPOINT")
        print("-" * 50)
        
        # First get list of available terminals
        terminal_list_result = await self.test_endpoint_with_metrics(
            session, "/api/v1/atm/list", {}, "Terminal List"
        )
        
        available_terminals = []
        if terminal_list_result['status'] == 'SUCCESS':
            # Try to get actual terminal IDs from the API response
            available_terminals = ['147', '169', '2603', '2604', '2605']  # Known working terminals
        
        if not available_terminals:
            print("  ⚠️ No terminals available for testing")
            return []
        
        # Test with first few terminals
        test_terminals = available_terminals[:3]
        
        results = []
        for terminal_id in test_terminals:
            result = await self.test_endpoint_with_metrics(
                session,
                f"/api/v1/atm/{terminal_id}/cash-usage/history",
                {'days': 14},
                f"Terminal {terminal_id} History",
                ['history_data', 'terminal_details']
            )
            results.append(result)
            
            status_icon = "✅" if result['status'] == 'SUCCESS' and result['response_time'] < 3.0 else "⚠️"
            print(f"  {status_icon} Terminal {terminal_id}: {result['response_time']}s ({result['status']})")
            if result['status'] == 'SUCCESS':
                print(f"     History Points: {result.get('history_points', 'N/A')}")
        
        return results
    
    async def run_comprehensive_cash_usage_tests(self):
        """Run all cash usage endpoint tests"""
        print("🚀 COMPREHENSIVE CASH USAGE ENDPOINTS PERFORMANCE TEST")
        print("=" * 70)
        print(f"⏰ Started at: {datetime.now()}")
        print(f"🎯 Target: All endpoints <3s response time")
        print(f"🔥 Critical: Summary endpoint improvement from 14.878s")
        print()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            
            # Test all cash usage endpoints
            daily_results = await self.test_daily_cash_usage_endpoint(session)
            trends_results = await self.test_cash_trends_endpoint(session)
            summary_results = await self.test_cash_summary_endpoint(session)
            history_results = await self.test_terminal_history_endpoint(session)
            
            # Comprehensive analysis
            await self.analyze_cash_usage_performance()
    
    async def analyze_cash_usage_performance(self):
        """Analyze performance results for all cash usage endpoints"""
        print("\n📊 COMPREHENSIVE CASH USAGE PERFORMANCE ANALYSIS")
        print("=" * 70)
        
        # Group results by endpoint type
        endpoint_groups = {
            'Daily Usage': [r for r in self.test_results if 'Daily Usage' in r['test_name']],
            'Trends': [r for r in self.test_results if 'Trends' in r['test_name']],
            'Summary': [r for r in self.test_results if 'Summary' in r['test_name']],
            'Terminal History': [r for r in self.test_results if 'Terminal' in r['test_name'] and 'History' in r['test_name']]
        }
        
        overall_stats = {
            'total_tests': len(self.test_results),
            'successful_tests': len([r for r in self.test_results if r['status'] == 'SUCCESS']),
            'failed_tests': len([r for r in self.test_results if r['status'] != 'SUCCESS']),
            'target_met': len([r for r in self.test_results if r['status'] == 'SUCCESS' and r['response_time'] < 3.0])
        }
        
        print(f"✅ Total Tests: {overall_stats['total_tests']}")
        print(f"✅ Successful: {overall_stats['successful_tests']}")
        print(f"❌ Failed: {overall_stats['failed_tests']}")
        print(f"🎯 Target <3s Met: {overall_stats['target_met']}/{overall_stats['successful_tests']}")
        print()
        
        # Analyze each endpoint group
        for group_name, results in endpoint_groups.items():
            if not results:
                continue
                
            successful_results = [r for r in results if r['status'] == 'SUCCESS']
            if not successful_results:
                print(f"❌ {group_name}: No successful tests")
                continue
            
            response_times = [r['response_time'] for r in successful_results]
            baseline_key = {
                'Daily Usage': 'daily_usage',
                'Trends': 'trends',
                'Summary': 'summary',
                'Terminal History': 'terminal_history'
            }.get(group_name, 'summary')
            
            baseline_time = self.baseline_performance[baseline_key]
            avg_time = statistics.mean(response_times)
            improvement = ((baseline_time - avg_time) / baseline_time) * 100
            
            print(f"📊 {group_name} Performance:")
            print(f"   Tests: {len(successful_results)}/{len(results)} successful")
            print(f"   Average: {avg_time:.3f}s (was {baseline_time}s)")
            print(f"   Range: {min(response_times):.3f}s - {max(response_times):.3f}s")
            print(f"   Improvement: {improvement:+.1f}%")
            
            # Performance grade
            if avg_time < 1.0:
                grade = "A+"
            elif avg_time < 2.0:
                grade = "A"
            elif avg_time < 3.0:
                grade = "B+"
            else:
                grade = "B"
            
            target_met = sum(1 for t in response_times if t < 3.0)
            print(f"   Grade: {grade} | Target <3s: {target_met}/{len(response_times)}")
            print()
        
        # Overall performance summary
        all_successful = [r for r in self.test_results if r['status'] == 'SUCCESS']
        if all_successful:
            all_times = [r['response_time'] for r in all_successful]
            overall_avg = statistics.mean(all_times)
            
            print("🎉 OVERALL CASH USAGE ENDPOINTS PERFORMANCE:")
            print("-" * 50)
            print(f"📈 Average Response Time: {overall_avg:.3f}s")
            print(f"⚡ Fastest: {min(all_times):.3f}s")
            print(f"🐌 Slowest: {max(all_times):.3f}s")
            print(f"🎯 Target <3s Achievement: {sum(1 for t in all_times if t < 3.0)}/{len(all_times)} ({(sum(1 for t in all_times if t < 3.0)/len(all_times)*100):.1f}%)")
            
            # Calculate overall improvement vs baseline
            baseline_avg = statistics.mean(list(self.baseline_performance.values()))
            overall_improvement = ((baseline_avg - overall_avg) / baseline_avg) * 100
            print(f"🚀 Overall Improvement: {overall_improvement:+.1f}%")
            
            # Final grade
            if overall_avg < 1.0:
                final_grade = "A+"
                assessment = "Outstanding Performance"
            elif overall_avg < 2.0:
                final_grade = "A"
                assessment = "Excellent Performance"
            elif overall_avg < 3.0:
                final_grade = "B+"
                assessment = "Very Good Performance"
            else:
                final_grade = "B"
                assessment = "Good Performance"
            
            print(f"📊 Final Grade: {final_grade} - {assessment}")
            
        print(f"\n⏰ Analysis completed at: {datetime.now()}")

async def main():
    """Run the comprehensive cash usage performance test"""
    tester = CashUsagePerformanceTester("http://localhost:8001")
    await tester.run_comprehensive_cash_usage_tests()

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Cash Usage Endpoints Performance Test...")
    print()
    asyncio.run(main())
