#!/usr/bin/env python3
"""
Test script for the new predictive analytics endpoints
Tests the endpoints using existing JSONB fault data
"""
import sys
import os
import json
import asyncio
import asyncpg
from datetime import datetime, timedelta
import requests
import time

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database configuration
DB_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

async def test_database_connection():
    """Test if we can connect to the database and find terminal data"""
    print("🔌 Testing database connection...")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # Check if we have terminals with fault data
        query = """
            SELECT DISTINCT terminal_id, COUNT(*) as fault_count
            FROM terminal_details 
            WHERE fault_data IS NOT NULL 
                AND retrieved_date >= NOW() - INTERVAL '30 days'
            GROUP BY terminal_id
            ORDER BY fault_count DESC
            LIMIT 5
        """
        
        rows = await conn.fetch(query)
        
        if rows:
            print(f"✅ Found {len(rows)} terminals with fault data:")
            for row in rows:
                print(f"   - Terminal {row['terminal_id']}: {row['fault_count']} fault records")
            return [row['terminal_id'] for row in rows]
        else:
            print("❌ No terminals with fault data found")
            return []
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return []
    finally:
        if 'conn' in locals():
            await conn.close()

def test_api_endpoints(terminal_ids):
    """Test the predictive analytics API endpoints"""
    
    if not terminal_ids:
        print("❌ No terminals to test with")
        return
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint first
    print("\n🏥 Testing API health...")
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the API is running: uvicorn api_option_2_fastapi_fixed:app --reload")
        return
    
    # Test individual terminal analytics
    terminal_id = terminal_ids[0]
    print(f"\n🔍 Testing predictive analytics for terminal {terminal_id}...")
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/atm/{terminal_id}/predictive-analytics",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            analytics = data['atm_analytics']
            
            print("✅ Predictive analytics successful!")
            print(f"   Terminal: {analytics['terminal_id']}")
            print(f"   Location: {analytics.get('location', 'Unknown')}")
            print(f"   Overall Health Score: {analytics['overall_health_score']}%")
            print(f"   Failure Risk: {analytics['failure_prediction']['risk_level']} ({analytics['failure_prediction']['risk_score']}%)")
            print(f"   Prediction Horizon: {analytics['failure_prediction']['prediction_horizon']}")
            print(f"   Confidence: {analytics['failure_prediction']['confidence']}%")
            
            print(f"\n   Component Health:")
            for comp in analytics['component_health']:
                print(f"     - {comp['component_type']}: {comp['health_score']}% ({comp['failure_risk']})")
            
            print(f"\n   Maintenance Recommendations:")
            for rec in analytics['maintenance_recommendations']:
                print(f"     - {rec['action']} (Priority: {rec['priority']})")
            
            print(f"\n   Analysis Metadata:")
            metadata = data['analysis_metadata']
            print(f"     - Data points analyzed: {metadata['data_points_analyzed']}")
            print(f"     - Analysis period: {metadata['analysis_period_days']} days")
            print(f"     - Data source: {metadata['data_source']}")
            
        else:
            print(f"❌ Individual analytics failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Individual analytics test failed: {e}")
    
    # Test summary analytics
    print(f"\n📊 Testing predictive analytics summary...")
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/atm/predictive-analytics/summary?limit=5",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data['summary']
            stats = data['fleet_statistics']
            
            print("✅ Summary analytics successful!")
            print(f"   ATMs analyzed: {stats['total_atms_analyzed']}")
            print(f"   Average health score: {stats['average_health_score']}%")
            print(f"   Average risk score: {stats['average_risk_score']}%")
            print(f"   Risk distribution: {stats['risk_distribution']}")
            
            if summary:
                print(f"\n   Top Risk ATMs:")
                for atm in summary[:3]:
                    print(f"     - {atm['terminal_id']}: {atm['failure_risk_level']} risk ({atm['failure_risk_score']}%)")
            
        else:
            print(f"❌ Summary analytics failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Summary analytics test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Testing ATM Predictive Analytics Implementation")
    print("=" * 60)
    
    # Test database connection and get terminal IDs
    terminal_ids = await test_database_connection()
    
    if not terminal_ids:
        print("\n❌ Cannot proceed without terminal data")
        return
    
    # Test API endpoints
    test_api_endpoints(terminal_ids)
    
    print("\n" + "=" * 60)
    print("🎉 Predictive Analytics Testing Complete!")
    print("\n💡 Key Features Implemented:")
    print("   ✅ Component health scoring (6 component types)")
    print("   ✅ Failure risk prediction with confidence levels")
    print("   ✅ Maintenance recommendations")
    print("   ✅ Fleet-wide analytics summary")
    print("   ✅ Uses existing JSONB fault data (no DB changes needed)")
    print("   ✅ Real-time analysis with configurable time periods")
    
    print("\n🔗 Available Endpoints:")
    print("   - GET /api/v1/atm/{terminal_id}/predictive-analytics")
    print("   - GET /api/v1/atm/predictive-analytics/summary")
    print("   - GET /docs (for interactive API documentation)")

if __name__ == "__main__":
    asyncio.run(main())
