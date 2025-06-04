#!/usr/bin/env python3
"""
Flask REST API for ATM Status Counts - Option 1

A lightweight, production-ready REST API for fetching ATM status counts
from both legacy and new database tables with comprehensive error handling.

Features:
- Multiple endpoints for different data views
- Support for both legacy and new database tables
- CORS support for frontend integration
- Comprehensive error handling and logging
- JSON response with standardized format
- Optional real-time data refresh
- Performance optimized queries

Endpoints:
- GET /api/v1/atm/status/summary - Overall ATM status summary
- GET /api/v1/atm/status/regional - Regional breakdown
- GET /api/v1/atm/status/trends - Historical trends
- GET /api/v1/atm/status/latest - Latest data from all tables
- GET /api/v1/health - API health check

Author: ATM Monitoring System
Created: 2025-01-30
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pytz

# Flask imports
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('atm_api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ATM_API')

# Try to import database connector
try:
    import db_connector
    DB_AVAILABLE = True
    logger.info("Database connector available")
except ImportError:
    db_connector = None
    DB_AVAILABLE = False
    logger.error("Database connector not available")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
API_VERSION = "1.0.0"
DILI_TZ = pytz.timezone('Asia/Dili')

class ATMStatusAPI:
    """Main API class for ATM status data"""
    
    def __init__(self):
        self.db_available = DB_AVAILABLE
        logger.info("ATM Status API initialized")
    
    def get_db_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Get database connection"""
        if not self.db_available or not db_connector:
            return None
        return db_connector.get_db_connection()
    
    def get_overall_summary(self) -> Dict[str, Any]:
        """Get overall ATM status summary from latest data"""
        conn = self.get_db_connection()
        if not conn:
            return {"error": "Database not available"}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Query latest data from regional_atm_counts
            cursor.execute("""
                WITH latest_data AS (
                    SELECT DISTINCT ON (region_code) 
                        region_code,
                        count_available,
                        count_warning, 
                        count_zombie,
                        count_wounded,
                        count_out_of_service,
                        total_atms_in_region,
                        date_creation
                    FROM regional_atm_counts 
                    ORDER BY region_code, date_creation DESC
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
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return {"error": "No data found"}
            
            # Calculate percentages
            total_atms = result['grand_total_atms'] or 0
            summary = dict(result)
            
            if total_atms > 0:
                summary['percentage_available'] = round((summary['total_available'] / total_atms) * 100, 2)
                summary['percentage_warning'] = round((summary['total_warning'] / total_atms) * 100, 2)
                summary['percentage_zombie'] = round((summary['total_zombie'] / total_atms) * 100, 2)
                summary['percentage_wounded'] = round((summary['total_wounded'] / total_atms) * 100, 2)
                summary['percentage_out_of_service'] = round((summary['total_out_of_service'] / total_atms) * 100, 2)
            else:
                summary.update({
                    'percentage_available': 0,
                    'percentage_warning': 0,
                    'percentage_zombie': 0,
                    'percentage_wounded': 0,
                    'percentage_out_of_service': 0
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting overall summary: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def get_regional_breakdown(self) -> List[Dict[str, Any]]:
        """Get regional breakdown of ATM status"""
        conn = self.get_db_connection()
        if not conn:
            return [{"error": "Database not available"}]
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get latest data for each region
            cursor.execute("""
                SELECT DISTINCT ON (region_code)
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region,
                    date_creation,
                    percentage_available,
                    percentage_warning,
                    percentage_zombie,
                    percentage_wounded,
                    percentage_out_of_service
                FROM regional_atm_counts
                ORDER BY region_code, date_creation DESC
            """)
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting regional breakdown: {e}")
            return [{"error": str(e)}]
        finally:
            cursor.close()
            conn.close()
    
    def get_trends(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get ATM status trends over time"""
        conn = self.get_db_connection()
        if not conn:
            return {"error": "Database not available"}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get trend data
            cursor.execute("""
                SELECT 
                    date_creation,
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region
                FROM regional_atm_counts
                WHERE date_creation >= NOW() - INTERVAL %s
                ORDER BY date_creation DESC, region_code
            """, (f"{hours_back} hours",))
            
            results = cursor.fetchall()
            
            # Group by region
            regional_trends = {}
            for row in results:
                region = row['region_code']
                if region not in regional_trends:
                    regional_trends[region] = []
                regional_trends[region].append(dict(row))
            
            return {
                "hours_back": hours_back,
                "data_points": len(results),
                "regional_trends": regional_trends
            }
            
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def get_latest_from_new_tables(self) -> Dict[str, Any]:
        """Get latest data from new JSONB-enabled tables"""
        conn = self.get_db_connection()
        if not conn:
            return {"error": "Database not available"}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if new tables exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'regional_data'
                )
            """)
            
            if not cursor.fetchone()[0]:
                return {"error": "New tables not available"}
            
            # Get latest regional data
            cursor.execute("""
                SELECT DISTINCT ON (region_code)
                    region_code,
                    count_available,
                    count_warning,
                    count_zombie,
                    count_wounded,
                    count_out_of_service,
                    total_atms_in_region,
                    retrieval_timestamp,
                    raw_regional_data
                FROM regional_data
                ORDER BY region_code, retrieval_timestamp DESC
            """)
            
            regional_results = cursor.fetchall()
            
            # Get terminal details summary
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'terminal_details'
                )
            """)
            
            terminal_summary = {}
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT 
                        fetched_status,
                        COUNT(*) as count
                    FROM terminal_details
                    WHERE retrieved_date >= NOW() - INTERVAL '24 hours'
                    GROUP BY fetched_status
                    ORDER BY count DESC
                """)
                
                terminal_results = cursor.fetchall()
                terminal_summary = {row['fetched_status']: row['count'] for row in terminal_results}
            
            return {
                "regional_data": [dict(row) for row in regional_results],
                "terminal_summary": terminal_summary,
                "source": "new_tables"
            }
            
        except Exception as e:
            logger.error(f"Error getting data from new tables: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
            conn.close()

# Initialize API instance
api = ATMStatusAPI()

# API Routes
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now(DILI_TZ).isoformat(),
        "database_available": api.db_available
    })

@app.route('/api/v1/atm/status/summary', methods=['GET'])
def get_status_summary():
    """Get overall ATM status summary"""
    try:
        summary = api.get_overall_summary()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(DILI_TZ).isoformat(),
            "data": summary
        })
    
    except Exception as e:
        logger.error(f"Error in status summary endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(DILI_TZ).isoformat()
        }), 500

@app.route('/api/v1/atm/status/regional', methods=['GET'])
def get_regional_status():
    """Get regional breakdown of ATM status"""
    try:
        breakdown = api.get_regional_breakdown()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(DILI_TZ).isoformat(),
            "data": breakdown
        })
    
    except Exception as e:
        logger.error(f"Error in regional status endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(DILI_TZ).isoformat()
        }), 500

@app.route('/api/v1/atm/status/trends', methods=['GET'])
def get_status_trends():
    """Get ATM status trends"""
    try:
        hours_back = request.args.get('hours', 24, type=int)
        trends = api.get_trends(hours_back)
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(DILI_TZ).isoformat(),
            "data": trends
        })
    
    except Exception as e:
        logger.error(f"Error in trends endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(DILI_TZ).isoformat()
        }), 500

@app.route('/api/v1/atm/status/latest', methods=['GET'])
def get_latest_data():
    """Get latest data from new JSONB tables"""
    try:
        latest = api.get_latest_from_new_tables()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(DILI_TZ).isoformat(),
            "data": latest
        })
    
    except Exception as e:
        logger.error(f"Error in latest data endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(DILI_TZ).isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "timestamp": datetime.now(DILI_TZ).isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now(DILI_TZ).isoformat()
    }), 500

if __name__ == '__main__':
    logger.info("Starting ATM Status API server...")
    
    # Development configuration
    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # Production configuration
        app.run(host='127.0.0.1', port=5000, debug=False)
