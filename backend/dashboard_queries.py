#!/usr/bin/env python3
# dashboard_queries.py - Advanced queries for ATM Dashboard Monitoring

import logging
import db_connector
from datetime import datetime, timedelta
import pytz

# Configure logging
log = logging.getLogger("DashboardQueries")

def get_dashboard_summary():
    """Get overall dashboard summary with current ATM status"""
    conn = db_connector.get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Get latest regional data summary
        cursor.execute("""
            WITH latest_data AS (
                SELECT 
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region,
                    date_creation,
                    ROW_NUMBER() OVER (PARTITION BY region_code ORDER BY date_creation DESC) as rn
                FROM regional_atm_counts
            )
            SELECT 
                COUNT(DISTINCT region_code) as total_regions,
                SUM(count_available) as total_available,
                SUM(count_warning) as total_warning,
                SUM(count_zombie) as total_zombie,
                SUM(count_wounded) as total_wounded,
                SUM(count_out_of_service) as total_out_of_service,
                SUM(total_atms_in_region) as grand_total_atms,
                MAX(date_creation) as last_update
            FROM latest_data 
            WHERE rn = 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            summary = {
                'total_regions': result[0] or 0,
                'total_available': result[1] or 0,
                'total_warning': result[2] or 0,
                'total_zombie': result[3] or 0,
                'total_wounded': result[4] or 0,
                'total_out_of_service': result[5] or 0,
                'grand_total_atms': result[6] or 0,
                'last_update': result[7]
            }
            
            # Calculate percentages
            if summary['grand_total_atms'] > 0:
                total = summary['grand_total_atms']
                summary['percentage_available'] = round((summary['total_available'] / total) * 100, 2)
                summary['percentage_warning'] = round((summary['total_warning'] / total) * 100, 2)
                summary['percentage_zombie'] = round((summary['total_zombie'] / total) * 100, 2)
                summary['percentage_wounded'] = round((summary['total_wounded'] / total) * 100, 2)
                summary['percentage_out_of_service'] = round((summary['total_out_of_service'] / total) * 100, 2)
            else:
                summary['percentage_available'] = 0
                summary['percentage_warning'] = 0
                summary['percentage_zombie'] = 0
                summary['percentage_wounded'] = 0
                summary['percentage_out_of_service'] = 0
                
            return summary
        
        return None
        
    except Exception as e:
        log.error(f"Error getting dashboard summary: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_regional_comparison():
    """Get comparison of ATM status across all regions"""
    conn = db_connector.get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute("""
            WITH latest_regional AS (
                SELECT 
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region,
                    date_creation,
                    ROW_NUMBER() OVER (PARTITION BY region_code ORDER BY date_creation DESC) as rn
                FROM regional_atm_counts
            )
            SELECT 
                region_code,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                total_atms_in_region,
                date_creation,
                ROUND((count_available::DECIMAL / NULLIF(total_atms_in_region, 0)) * 100, 2) as availability_percentage,
                ROUND(((count_warning + count_zombie + count_wounded + count_out_of_service)::DECIMAL / NULLIF(total_atms_in_region, 0)) * 100, 2) as issue_percentage
            FROM latest_regional 
            WHERE rn = 1
            ORDER BY region_code
        """)
        
        results = cursor.fetchall()
        
        regional_data = []
        for row in results:
            regional_data.append({
                'region_code': row[0],
                'count_available': row[1],
                'count_warning': row[2],
                'count_zombie': row[3],
                'count_wounded': row[4],
                'count_out_of_service': row[5],
                'total_atms_in_region': row[6],
                'date_creation': row[7],
                'availability_percentage': float(row[8]) if row[8] else 0,
                'issue_percentage': float(row[9]) if row[9] else 0
            })
        
        return regional_data
        
    except Exception as e:
        log.error(f"Error getting regional comparison: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_hourly_trends(hours_back=24):
    """Get hourly trends for all regions"""
    conn = db_connector.get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                DATE_TRUNC('hour', date_creation) as hour_bucket,
                region_code,
                AVG(count_available) as avg_available,
                AVG(count_warning) as avg_warning,
                AVG(count_zombie) as avg_zombie,
                AVG(count_wounded) as avg_wounded,
                AVG(count_out_of_service) as avg_out_of_service,
                AVG(total_atms_in_region) as avg_total_atms,
                COUNT(*) as data_points
            FROM regional_atm_counts
            WHERE date_creation >= NOW() - INTERVAL '%s hours'
            GROUP BY DATE_TRUNC('hour', date_creation), region_code
            ORDER BY hour_bucket DESC, region_code
        """, (hours_back,))
        
        results = cursor.fetchall()
        
        trends = []
        for row in results:
            trends.append({
                'hour_bucket': row[0],
                'region_code': row[1],
                'avg_available': round(float(row[2]), 1) if row[2] else 0,
                'avg_warning': round(float(row[3]), 1) if row[3] else 0,
                'avg_zombie': round(float(row[4]), 1) if row[4] else 0,
                'avg_wounded': round(float(row[5]), 1) if row[5] else 0,
                'avg_out_of_service': round(float(row[6]), 1) if row[6] else 0,
                'avg_total_atms': round(float(row[7]), 1) if row[7] else 0,
                'data_points': row[8]
            })
        
        return trends
        
    except Exception as e:
        log.error(f"Error getting hourly trends: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_alerting_data():
    """Get data for alerting - identify regions with critical issues"""
    conn = db_connector.get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute("""
            WITH latest_regional AS (
                SELECT 
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region,
                    date_creation,
                    ROW_NUMBER() OVER (PARTITION BY region_code ORDER BY date_creation DESC) as rn
                FROM regional_atm_counts
            ),
            regional_health AS (
                SELECT 
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region,
                    date_creation,
                    ROUND((count_available::DECIMAL / NULLIF(total_atms_in_region, 0)) * 100, 2) as availability_percentage,
                    ROUND((count_out_of_service::DECIMAL / NULLIF(total_atms_in_region, 0)) * 100, 2) as out_of_service_percentage,
                    ROUND(((count_wounded + count_zombie)::DECIMAL / NULLIF(total_atms_in_region, 0)) * 100, 2) as critical_percentage
                FROM latest_regional 
                WHERE rn = 1
            )
            SELECT 
                region_code,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                total_atms_in_region,
                date_creation,
                availability_percentage,
                out_of_service_percentage,
                critical_percentage,
                CASE 
                    WHEN availability_percentage < 50 THEN 'CRITICAL'
                    WHEN availability_percentage < 70 THEN 'WARNING'
                    WHEN availability_percentage < 85 THEN 'ATTENTION'
                    ELSE 'HEALTHY'
                END as health_status,
                CASE 
                    WHEN out_of_service_percentage > 30 THEN 'HIGH_OUTAGE'
                    WHEN out_of_service_percentage > 15 THEN 'MEDIUM_OUTAGE'
                    WHEN out_of_service_percentage > 5 THEN 'LOW_OUTAGE'
                    ELSE 'NORMAL'
                END as outage_level
            FROM regional_health
            ORDER BY availability_percentage ASC, region_code
        """)
        
        results = cursor.fetchall()
        
        alert_data = []
        for row in results:
            alert_data.append({
                'region_code': row[0],
                'count_available': row[1],
                'count_warning': row[2],
                'count_zombie': row[3],
                'count_wounded': row[4],
                'count_out_of_service': row[5],
                'total_atms_in_region': row[6],
                'date_creation': row[7],
                'availability_percentage': float(row[8]) if row[8] else 0,
                'out_of_service_percentage': float(row[9]) if row[9] else 0,
                'critical_percentage': float(row[10]) if row[10] else 0,
                'health_status': row[11],
                'outage_level': row[12]
            })
        
        return alert_data
        
    except Exception as e:
        log.error(f"Error getting alerting data: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_data_freshness():
    """Check data freshness and identify stale data"""
    conn = db_connector.get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        # Get timezone-aware current time in Dili timezone
        dili_tz = pytz.timezone('Asia/Dili')
        now_dili = datetime.now(dili_tz)
        
        cursor.execute("""
            WITH latest_per_region AS (
                SELECT 
                    region_code,
                    MAX(date_creation) as latest_update,
                    COUNT(*) as total_records
                FROM regional_atm_counts
                GROUP BY region_code
            )
            SELECT 
                region_code,
                latest_update,
                total_records,
                EXTRACT(EPOCH FROM (%s - latest_update))/3600 as hours_since_update
            FROM latest_per_region
            ORDER BY hours_since_update DESC
        """, (now_dili,))
        
        results = cursor.fetchall()
        
        freshness_data = []
        for row in results:
            hours_since = float(row[3]) if row[3] else 0
            
            # Determine freshness status
            if hours_since <= 1:
                status = 'FRESH'
            elif hours_since <= 6:
                status = 'RECENT'
            elif hours_since <= 24:
                status = 'STALE'
            else:
                status = 'VERY_STALE'
            
            freshness_data.append({
                'region_code': row[0],
                'latest_update': row[1],
                'total_records': row[2],
                'hours_since_update': round(hours_since, 2),
                'freshness_status': status
            })
        
        return freshness_data
        
    except Exception as e:
        log.error(f"Error getting data freshness: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_historical_analysis(days_back=7):
    """Get historical analysis for trend identification"""
    conn = db_connector.get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute("""
            WITH daily_aggregates AS (
                SELECT 
                    DATE(date_creation) as date_bucket,
                    region_code,
                    AVG(count_available) as avg_available,
                    AVG(count_warning) as avg_warning,
                    AVG(count_zombie) as avg_zombie,
                    AVG(count_wounded) as avg_wounded,
                    AVG(count_out_of_service) as avg_out_of_service,
                    AVG(total_atms_in_region) as avg_total_atms,
                    COUNT(*) as measurements_per_day
                FROM regional_atm_counts
                WHERE date_creation >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(date_creation), region_code
            ),
            trend_analysis AS (
                SELECT 
                    region_code,
                    date_bucket,
                    avg_available,
                    avg_total_atms,
                    ROUND((avg_available / NULLIF(avg_total_atms, 0)) * 100, 2) as daily_availability_percentage,
                    LAG(ROUND((avg_available / NULLIF(avg_total_atms, 0)) * 100, 2)) OVER (PARTITION BY region_code ORDER BY date_bucket) as prev_day_availability,
                    measurements_per_day
                FROM daily_aggregates
            )
            SELECT 
                region_code,
                date_bucket,
                daily_availability_percentage,
                prev_day_availability,
                CASE 
                    WHEN prev_day_availability IS NULL THEN 0
                    ELSE ROUND(daily_availability_percentage - prev_day_availability, 2)
                END as daily_change,
                measurements_per_day
            FROM trend_analysis
            ORDER BY region_code, date_bucket DESC
        """, (days_back,))
        
        results = cursor.fetchall()
        
        historical_data = []
        for row in results:
            historical_data.append({
                'region_code': row[0],
                'date_bucket': row[1],
                'daily_availability_percentage': float(row[2]) if row[2] else 0,
                'prev_day_availability': float(row[3]) if row[3] else 0,
                'daily_change': float(row[4]) if row[4] else 0,
                'measurements_per_day': row[5]
            })
        
        return historical_data
        
    except Exception as e:
        log.error(f"Error getting historical analysis: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

# Main execution for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== ATM Dashboard Query Testing ===")
    
    # Test dashboard summary
    print("\n1. Dashboard Summary:")
    summary = get_dashboard_summary()
    if summary:
        print(f"   Total Regions: {summary['total_regions']}")
        print(f"   Total ATMs: {summary['grand_total_atms']}")
        print(f"   Available: {summary['total_available']} ({summary['percentage_available']}%)")
        print(f"   Issues: {summary['total_warning'] + summary['total_zombie'] + summary['total_wounded'] + summary['total_out_of_service']}")
        print(f"   Last Update: {summary['last_update']}")
    
    # Test regional comparison
    print("\n2. Regional Comparison:")
    regions = get_regional_comparison()
    if regions:
        for region in regions:
            print(f"   {region['region_code']}: {region['availability_percentage']}% available")
    
    # Test alerting data
    print("\n3. Health Status:")
    alerts = get_alerting_data()
    if alerts:
        for alert in alerts:
            print(f"   {alert['region_code']}: {alert['health_status']} ({alert['availability_percentage']}% available)")
    
    # Test data freshness
    print("\n4. Data Freshness:")
    freshness = get_data_freshness()
    if freshness:
        for fresh in freshness:
            print(f"   {fresh['region_code']}: {fresh['freshness_status']} ({fresh['hours_since_update']:.1f}h ago)")
    
    print("\n=== Testing Complete ===")
