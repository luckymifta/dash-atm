#!/usr/bin/env python3
# monitoring_dashboard.py - Simple command-line monitoring dashboard for ATM status

import os
import sys
import time
import argparse
import logging
from datetime import datetime
import dashboard_queries

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("MonitoringDashboard")

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_percentage(value, threshold_good=85, threshold_warning=70):
    """Format percentage with color coding"""
    if value >= threshold_good:
        return f"🟢 {value}%"
    elif value >= threshold_warning:
        return f"🟡 {value}%"
    else:
        return f"🔴 {value}%"

def format_health_status(status):
    """Format health status with emoji"""
    status_map = {
        'HEALTHY': '🟢 HEALTHY',
        'ATTENTION': '🟡 ATTENTION',
        'WARNING': '🟠 WARNING',
        'CRITICAL': '🔴 CRITICAL'
    }
    return status_map.get(status, f"❓ {status}")

def format_freshness_status(status):
    """Format data freshness with emoji"""
    status_map = {
        'FRESH': '🟢 FRESH',
        'RECENT': '🟡 RECENT',
        'STALE': '🟠 STALE',
        'VERY_STALE': '🔴 VERY STALE'
    }
    return status_map.get(status, f"❓ {status}")

def display_dashboard_summary():
    """Display the main dashboard summary"""
    print("=" * 80)
    print("🏦 ATM DASHBOARD MONITORING SYSTEM")
    print("=" * 80)
    
    summary = dashboard_queries.get_dashboard_summary()
    if not summary:
        print("❌ Error: Unable to retrieve dashboard summary")
        return
    
    print(f"📊 SYSTEM OVERVIEW (Last Update: {summary['last_update']})")
    print("-" * 50)
    print(f"Total Regions: {summary['total_regions']}")
    print(f"Total ATMs: {summary['grand_total_atms']}")
    print()
    
    # Status breakdown
    print("📈 ATM STATUS DISTRIBUTION:")
    print(f"  🟢 Available:      {summary['total_available']:3d} ({summary['percentage_available']:5.1f}%)")
    print(f"  🟡 Warning:        {summary['total_warning']:3d} ({summary['percentage_warning']:5.1f}%)")
    print(f"  🟠 Zombie:         {summary['total_zombie']:3d} ({summary['percentage_zombie']:5.1f}%)")
    print(f"  🔴 Wounded:        {summary['total_wounded']:3d} ({summary['percentage_wounded']:5.1f}%)")
    print(f"  ⚫ Out of Service: {summary['total_out_of_service']:3d} ({summary['percentage_out_of_service']:5.1f}%)")
    
    # Overall health indicator
    availability = summary['percentage_available']
    print()
    print(f"🎯 OVERALL AVAILABILITY: {format_percentage(availability)}")
    
    total_issues = summary['total_warning'] + summary['total_zombie'] + summary['total_wounded'] + summary['total_out_of_service']
    print(f"⚠️  TOTAL ISSUES: {total_issues} ATMs")

def display_regional_status():
    """Display regional status breakdown"""
    print("\n" + "=" * 80)
    print("🗺️  REGIONAL STATUS BREAKDOWN")
    print("=" * 80)
    
    regions = dashboard_queries.get_regional_comparison()
    if not regions:
        print("❌ Error: Unable to retrieve regional data")
        return
    
    print(f"{'Region':<8} {'Available':<10} {'Warning':<8} {'Zombie':<8} {'Wounded':<8} {'Out/Svc':<8} {'Health':<12}")
    print("-" * 80)
    
    for region in regions:
        print(f"{region['region_code']:<8} "
              f"{region['count_available']:3d} ({region['availability_percentage']:5.1f}%) "
              f"{region['count_warning']:3d}      "
              f"{region['count_zombie']:3d}      "
              f"{region['count_wounded']:3d}      "
              f"{region['count_out_of_service']:3d}      "
              f"{format_percentage(region['availability_percentage'])}")

def display_alerts():
    """Display current alerts and issues"""
    print("\n" + "=" * 80)
    print("🚨 ALERTS & HEALTH STATUS")
    print("=" * 80)
    
    alerts = dashboard_queries.get_alerting_data()
    if not alerts:
        print("❌ Error: Unable to retrieve alert data")
        return
    
    # Group alerts by health status
    critical_regions = [a for a in alerts if a['health_status'] == 'CRITICAL']
    warning_regions = [a for a in alerts if a['health_status'] == 'WARNING']
    attention_regions = [a for a in alerts if a['health_status'] == 'ATTENTION']
    healthy_regions = [a for a in alerts if a['health_status'] == 'HEALTHY']
    
    if critical_regions:
        print("🔴 CRITICAL REGIONS:")
        for region in critical_regions:
            print(f"   {region['region_code']}: {region['availability_percentage']}% available "
                  f"({region['count_available']}/{region['total_atms_in_region']} ATMs)")
    
    if warning_regions:
        print("🟠 WARNING REGIONS:")
        for region in warning_regions:
            print(f"   {region['region_code']}: {region['availability_percentage']}% available "
                  f"({region['count_available']}/{region['total_atms_in_region']} ATMs)")
    
    if attention_regions:
        print("🟡 ATTENTION REGIONS:")
        for region in attention_regions:
            print(f"   {region['region_code']}: {region['availability_percentage']}% available "
                  f"({region['count_available']}/{region['total_atms_in_region']} ATMs)")
    
    if healthy_regions:
        print("🟢 HEALTHY REGIONS:")
        for region in healthy_regions:
            print(f"   {region['region_code']}: {region['availability_percentage']}% available "
                  f"({region['count_available']}/{region['total_atms_in_region']} ATMs)")
    
    if not any([critical_regions, warning_regions, attention_regions, healthy_regions]):
        print("ℹ️  No data available for health status analysis")

def display_data_freshness():
    """Display data freshness information"""
    print("\n" + "=" * 80)
    print("⏰ DATA FRESHNESS")
    print("=" * 80)
    
    freshness = dashboard_queries.get_data_freshness()
    if not freshness:
        print("❌ Error: Unable to retrieve data freshness information")
        return
    
    print(f"{'Region':<8} {'Last Update':<20} {'Hours Ago':<10} {'Status':<12} {'Records':<8}")
    print("-" * 60)
    
    for fresh in freshness:
        last_update = fresh['latest_update'].strftime("%Y-%m-%d %H:%M") if fresh['latest_update'] else "Never"
        print(f"{fresh['region_code']:<8} "
              f"{last_update:<20} "
              f"{fresh['hours_since_update']:6.1f}    "
              f"{format_freshness_status(fresh['freshness_status']):<20} "
              f"{fresh['total_records']:<8}")

def display_recent_trends():
    """Display recent hourly trends"""
    print("\n" + "=" * 80)
    print("📈 RECENT TRENDS (Last 6 Hours)")
    print("=" * 80)
    
    trends = dashboard_queries.get_hourly_trends(hours_back=6)
    if not trends:
        print("❌ Error: Unable to retrieve trend data")
        return
    
    if not trends:
        print("ℹ️  No trend data available for the last 6 hours")
        return
    
    print(f"{'Time':<16} {'Region':<8} {'Avail':<6} {'Warn':<5} {'Zomb':<5} {'Woun':<5} {'Out':<5} {'Total':<6}")
    print("-" * 60)
    
    for trend in trends[:20]:  # Show only recent 20 entries
        time_str = trend['hour_bucket'].strftime("%m-%d %H:00") if trend['hour_bucket'] else "Unknown"
        print(f"{time_str:<16} "
              f"{trend['region_code']:<8} "
              f"{trend['avg_available']:5.1f} "
              f"{trend['avg_warning']:4.1f} "
              f"{trend['avg_zombie']:4.1f} "
              f"{trend['avg_wounded']:4.1f} "
              f"{trend['avg_out_of_service']:4.1f} "
              f"{trend['avg_total_atms']:5.1f}")

def display_historical_summary():
    """Display historical summary for the last 7 days"""
    print("\n" + "=" * 80)
    print("📊 HISTORICAL SUMMARY (Last 7 Days)")
    print("=" * 80)
    
    historical = dashboard_queries.get_historical_analysis(days_back=7)
    if not historical:
        print("❌ Error: Unable to retrieve historical data")
        return
    
    if not historical:
        print("ℹ️  No historical data available for the last 7 days")
        return
    
    # Group by region and show recent days
    regions_data = {}
    for entry in historical:
        region = entry['region_code']
        if region not in regions_data:
            regions_data[region] = []
        regions_data[region].append(entry)
    
    print(f"{'Region':<8} {'Recent Days Availability %':<30} {'Trend':<10}")
    print("-" * 60)
    
    for region, data in regions_data.items():
        # Get last 5 days
        recent_days = sorted(data, key=lambda x: x['date_bucket'], reverse=True)[:5]
        
        # Format availability percentages
        avail_str = " | ".join([f"{d['daily_availability_percentage']:5.1f}" for d in recent_days])
        
        # Calculate trend
        if len(recent_days) >= 2:
            latest_change = recent_days[0]['daily_change']
            if latest_change > 5:
                trend = "📈 UP"
            elif latest_change < -5:
                trend = "📉 DOWN"
            else:
                trend = "➡️  STABLE"
        else:
            trend = "❓ N/A"
        
        print(f"{region:<8} {avail_str:<30} {trend:<10}")

def run_single_report():
    """Run a single comprehensive dashboard report"""
    display_dashboard_summary()
    display_regional_status()
    display_alerts()
    display_data_freshness()
    display_recent_trends()
    display_historical_summary()
    
    print("\n" + "=" * 80)
    print(f"📅 Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def run_live_dashboard(refresh_seconds=30):
    """Run live dashboard with auto-refresh"""
    print("🔄 Starting live dashboard mode...")
    print(f"🕐 Auto-refresh every {refresh_seconds} seconds")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            clear_screen()
            
            print("🔴 LIVE MODE - Auto-refreshing")
            run_single_report()
            
            print(f"\n⏱️  Next refresh in {refresh_seconds} seconds... (Press Ctrl+C to exit)")
            time.sleep(refresh_seconds)
            
    except KeyboardInterrupt:
        print("\n👋 Live dashboard stopped by user")

def main():
    """Main function to handle command line arguments and run the dashboard"""
    parser = argparse.ArgumentParser(description="ATM Monitoring Dashboard")
    parser.add_argument('--live', action='store_true', help='Run in live mode with auto-refresh')
    parser.add_argument('--refresh', type=int, default=30, help='Refresh interval in seconds for live mode (default: 30)')
    parser.add_argument('--summary-only', action='store_true', help='Show only the summary section')
    parser.add_argument('--alerts-only', action='store_true', help='Show only alerts and health status')
    parser.add_argument('--freshness-only', action='store_true', help='Show only data freshness information')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.live:
        logging.getLogger().setLevel(logging.WARNING)  # Reduce noise in live mode
    
    try:
        if args.live:
            run_live_dashboard(args.refresh)
        elif args.summary_only:
            display_dashboard_summary()
        elif args.alerts_only:
            display_alerts()
        elif args.freshness_only:
            display_data_freshness()
        else:
            run_single_report()
            
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        log.error(f"Dashboard error: {str(e)}")
        print(f"❌ Dashboard error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
