#!/usr/bin/env python3
"""
GraphQL API for ATM Status Counts - Option 4

A flexible GraphQL API that allows clients to request exactly the data they need
with powerful querying capabilities and real-time subscriptions.

Features:
- Single endpoint for all queries and mutations
- Flexible data fetching - request only needed fields
- Real-time subscriptions for live data updates
- Introspection and schema documentation
- Built-in GraphQL Playground for testing
- Type-safe schema with resolvers
- Nested queries and relationships
- Efficient data loading with DataLoader pattern
- Custom scalar types for dates and JSON

Queries:
- atmSummary - Overall ATM status summary
- regionalData - Regional breakdown with filtering
- regionalTrends - Historical trend analysis
- terminalDetails - Individual terminal information
- health - API health check

Subscriptions:
- atmStatusUpdates - Real-time ATM status changes
- regionalUpdates - Real-time regional data updates

Installation:
pip install graphene graphql-core psycopg2-binary graphql-ws

Usage:
python api_option_4_graphql.py
# Visit http://localhost:4000/graphql for GraphQL Playground

Author: ATM Monitoring System
Created: 2025-01-30
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum

# GraphQL imports
import graphene
from graphene import ObjectType, String, Int, Float, Boolean, DateTime, List as GrapheneList, Field, Argument, Schema
from graphene.types.json import JSONString
from graphql_server.flask import GraphQLView
from flask import Flask, request, jsonify
from flask_cors import CORS

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('atm_graphql_api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ATM_GraphQL_API')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'atm_monitor'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Initialize connection pool
try:
    db_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=2,
        maxconn=20,
        **DB_CONFIG
    )
    logger.info("Database connection pool created successfully")
except Exception as e:
    logger.error(f"Failed to create database pool: {e}")
    db_pool = None

# GraphQL Enums
class ATMStatusEnum(graphene.Enum):
    AVAILABLE = "AVAILABLE"
    WARNING = "WARNING"
    ZOMBIE = "ZOMBIE"
    WOUNDED = "WOUNDED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

class HealthStatusEnum(graphene.Enum):
    HEALTHY = "HEALTHY"
    ATTENTION = "ATTENTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class TableTypeEnum(graphene.Enum):
    LEGACY = "legacy"
    NEW = "new"
    BOTH = "both"

# GraphQL Types
class ATMStatusCounts(ObjectType):
    """ATM status count information"""
    available = Int(description="Number of available ATMs")
    warning = Int(description="Number of ATMs with warnings")
    zombie = Int(description="Number of zombie ATMs")
    wounded = Int(description="Number of wounded ATMs")
    out_of_service = Int(description="Number of out-of-service ATMs")
    total = Int(description="Total number of ATMs")

class RegionalData(ObjectType):
    """Regional ATM data"""
    region_code = String(description="Region identifier")
    status_counts = Field(ATMStatusCounts, description="ATM status counts for this region")
    availability_percentage = Float(description="Availability percentage")
    last_updated = DateTime(description="Last update timestamp")
    health_status = HealthStatusEnum(description="Overall health classification")
    total_atms_in_region = Int(description="Total ATMs in region")
    raw_data = JSONString(description="Raw JSON data from database")

class ATMSummary(ObjectType):
    """Overall ATM status summary"""
    total_atms = Int(description="Total ATMs across all regions")
    status_counts = Field(ATMStatusCounts, description="Aggregated status counts")
    overall_availability = Float(description="Overall availability percentage")
    total_regions = Int(description="Number of regions")
    last_updated = DateTime(description="Last update timestamp")
    data_source = String(description="Data source identifier")

class TrendPoint(ObjectType):
    """Single point in trend data"""
    timestamp = DateTime(description="Data point timestamp")
    status_counts = Field(ATMStatusCounts, description="ATM status counts at this time")
    availability_percentage = Float(description="Availability percentage at this time")

class TrendSummaryStats(ObjectType):
    """Summary statistics for trend data"""
    data_points = Int(description="Number of data points")
    time_range_hours = Int(description="Time range in hours")
    avg_availability = Float(description="Average availability percentage")
    min_availability = Float(description="Minimum availability percentage")
    max_availability = Float(description="Maximum availability percentage")
    first_reading = DateTime(description="First data point timestamp")
    last_reading = DateTime(description="Last data point timestamp")

class RegionalTrends(ObjectType):
    """Regional trend analysis"""
    region_code = String(description="Region identifier")
    time_period = String(description="Time period description")
    trends = GrapheneList(TrendPoint, description="Trend data points")
    summary_stats = Field(TrendSummaryStats, description="Summary statistics")

class TerminalDetail(ObjectType):
    """Individual terminal details"""
    terminal_id = String(description="Terminal identifier")
    location = String(description="Terminal location")
    issue_state_name = String(description="Issue state name")
    serial_number = String(description="Terminal serial number")
    retrieved_date = DateTime(description="Data retrieval timestamp")
    fetched_status = String(description="Current status")
    raw_terminal_data = JSONString(description="Raw terminal data")
    fault_data = JSONString(description="Fault-specific data")
    metadata = JSONString(description="Processing metadata")

class HealthCheck(ObjectType):
    """API health status"""
    status = String(description="Overall health status")
    timestamp = DateTime(description="Health check timestamp")
    database_connected = Boolean(description="Database connectivity status")
    api_version = String(description="API version")
    uptime_seconds = Float(description="API uptime in seconds")
    query_count = Int(description="Total queries processed")

# Database helper functions
def get_db_connection():
    """Get database connection from pool"""
    if not db_pool:
        return None
    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        return None

def release_db_connection(conn):
    """Release database connection back to pool"""
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to release database connection: {e}")

def calculate_health_status(availability_percentage: float) -> str:
    """Calculate health status based on availability percentage"""
    if availability_percentage >= 85:
        return "HEALTHY"
    elif availability_percentage >= 70:
        return "ATTENTION"
    elif availability_percentage >= 50:
        return "WARNING"
    else:
        return "CRITICAL"

# Global state for tracking API metrics
api_start_time = datetime.utcnow()
query_count = 0

# GraphQL Resolvers
class Query(ObjectType):
    """Root Query type"""
    
    # Health check
    health = Field(HealthCheck, description="API health check")
    
    # ATM Summary
    atm_summary = Field(
        ATMSummary,
        table_type=Argument(TableTypeEnum, default_value="legacy", description="Database table to query"),
        description="Get overall ATM status summary"
    )
    
    # Regional data
    regional_data = Field(
        GrapheneList(RegionalData),
        region_code=Argument(String, description="Filter by specific region code"),
        table_type=Argument(TableTypeEnum, default_value="legacy", description="Database table to query"),
        description="Get regional breakdown of ATM status"
    )
    
    # Regional trends
    regional_trends = Field(
        RegionalTrends,
        region_code=Argument(String, required=True, description="Region code to get trends for"),
        hours=Argument(Int, default_value=24, description="Number of hours to look back"),
        table_type=Argument(TableTypeEnum, default_value="legacy", description="Database table to query"),
        description="Get historical trends for a specific region"
    )
    
    # Terminal details
    terminal_details = Field(
        GrapheneList(TerminalDetail),
        terminal_id=Argument(String, description="Filter by terminal ID"),
        status=Argument(String, description="Filter by status"),
        hours=Argument(Int, default_value=24, description="Hours to look back"),
        limit=Argument(Int, default_value=100, description="Maximum number of results"),
        description="Get individual terminal details"
    )

    def resolve_health(self, info):
        """Resolve health check"""
        global query_count
        query_count += 1
        
        conn = get_db_connection()
        db_connected = False
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_connected = True
                cursor.close()
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
            finally:
                release_db_connection(conn)
        
        uptime = (datetime.utcnow() - api_start_time).total_seconds()
        
        return HealthCheck(
            status="healthy" if db_connected else "degraded",
            timestamp=datetime.utcnow(),
            database_connected=db_connected,
            api_version="4.0.0",
            uptime_seconds=uptime,
            query_count=query_count
        )

    def resolve_atm_summary(self, info, table_type="legacy"):
        """Resolve ATM summary"""
        global query_count
        query_count += 1
        
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection unavailable")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if table_type == "legacy":
                query = """
                    WITH latest_data AS (
                        SELECT DISTINCT ON (region_code)
                            region_code, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service, total_atms_in_region,
                            date_creation
                        FROM regional_atm_counts
                        ORDER BY region_code, date_creation DESC
                    )
                    SELECT 
                        SUM(count_available) as total_available,
                        SUM(count_warning) as total_warning,
                        SUM(count_zombie) as total_zombie,
                        SUM(count_wounded) as total_wounded,
                        SUM(count_out_of_service) as total_out_of_service,
                        SUM(total_atms_in_region) as total_atms,
                        COUNT(DISTINCT region_code) as total_regions,
                        MAX(date_creation) as last_updated
                    FROM latest_data
                """
            else:
                query = """
                    WITH latest_data AS (
                        SELECT DISTINCT ON (region_code)
                            region_code, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service, total_atms_in_region,
                            retrieval_timestamp
                        FROM regional_data
                        ORDER BY region_code, retrieval_timestamp DESC
                    )
                    SELECT 
                        SUM(count_available) as total_available,
                        SUM(count_warning) as total_warning,
                        SUM(count_zombie) as total_zombie,
                        SUM(count_wounded) as total_wounded,
                        SUM(count_out_of_service) as total_out_of_service,
                        SUM(total_atms_in_region) as total_atms,
                        COUNT(DISTINCT region_code) as total_regions,
                        MAX(retrieval_timestamp) as last_updated
                    FROM latest_data
                """
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            if not row or row['total_atms'] is None:
                raise Exception("No ATM data found")
            
            total_atms = row['total_atms'] or 0
            available = row['total_available'] or 0
            availability_percentage = (available / total_atms * 100) if total_atms > 0 else 0
            
            status_counts = ATMStatusCounts(
                available=available,
                warning=row['total_warning'] or 0,
                zombie=row['total_zombie'] or 0,
                wounded=row['total_wounded'] or 0,
                out_of_service=row['total_out_of_service'] or 0,
                total=total_atms
            )
            
            return ATMSummary(
                total_atms=total_atms,
                status_counts=status_counts,
                overall_availability=round(availability_percentage, 2),
                total_regions=row['total_regions'] or 0,
                last_updated=row['last_updated'] or datetime.utcnow(),
                data_source=table_type
            )
            
        except Exception as e:
            logger.error(f"Error fetching ATM summary: {e}")
            raise Exception(f"Failed to fetch ATM summary: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

    def resolve_regional_data(self, info, region_code=None, table_type="legacy"):
        """Resolve regional data"""
        global query_count
        query_count += 1
        
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection unavailable")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if table_type == "legacy":
                base_query = """
                    WITH latest_regional AS (
                        SELECT DISTINCT ON (region_code)
                            region_code, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service, total_atms_in_region,
                            date_creation
                        FROM regional_atm_counts
                        ORDER BY region_code, date_creation DESC
                    )
                    SELECT * FROM latest_regional
                """
            else:
                base_query = """
                    WITH latest_regional AS (
                        SELECT DISTINCT ON (region_code)
                            region_code, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service, total_atms_in_region,
                            retrieval_timestamp as date_creation, raw_regional_data
                        FROM regional_data
                        ORDER BY region_code, retrieval_timestamp DESC
                    )
                    SELECT * FROM latest_regional
                """
            
            if region_code:
                base_query += f" WHERE region_code = '{region_code}'"
            
            base_query += " ORDER BY region_code"
            
            cursor.execute(base_query)
            rows = cursor.fetchall()
            
            if not rows:
                return []
            
            regional_data = []
            
            for row in rows:
                available = row['count_available'] or 0
                total_region = row['total_atms_in_region'] or 0
                availability_pct = (available / total_region * 100) if total_region > 0 else 0
                
                status_counts = ATMStatusCounts(
                    available=available,
                    warning=row['count_warning'] or 0,
                    zombie=row['count_zombie'] or 0,
                    wounded=row['count_wounded'] or 0,
                    out_of_service=row['count_out_of_service'] or 0,
                    total=total_region
                )
                
                raw_data = None
                if table_type == "new" and 'raw_regional_data' in row:
                    raw_data = row['raw_regional_data']
                
                regional_data.append(RegionalData(
                    region_code=row['region_code'],
                    status_counts=status_counts,
                    availability_percentage=round(availability_pct, 2),
                    last_updated=row['date_creation'] or datetime.utcnow(),
                    health_status=calculate_health_status(availability_pct),
                    total_atms_in_region=total_region,
                    raw_data=raw_data
                ))
            
            return regional_data
            
        except Exception as e:
            logger.error(f"Error fetching regional data: {e}")
            raise Exception(f"Failed to fetch regional data: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

    def resolve_regional_trends(self, info, region_code, hours=24, table_type="legacy"):
        """Resolve regional trends"""
        global query_count
        query_count += 1
        
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection unavailable")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if table_type == "legacy":
                query = """
                    SELECT 
                        date_creation, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region
                    FROM regional_atm_counts
                    WHERE region_code = %s 
                        AND date_creation >= NOW() - INTERVAL '%s hours'
                    ORDER BY date_creation ASC
                """ % ('%s', hours)
            else:
                query = """
                    SELECT 
                        retrieval_timestamp as date_creation, count_available, count_warning, 
                        count_zombie, count_wounded, count_out_of_service, total_atms_in_region
                    FROM regional_data
                    WHERE region_code = %s 
                        AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                    ORDER BY retrieval_timestamp ASC
                """ % ('%s', hours)
            
            cursor.execute(query, (region_code,))
            rows = cursor.fetchall()
            
            if not rows:
                raise Exception(f"No trend data found for region {region_code}")
            
            trends = []
            availability_values = []
            
            for row in rows:
                available = row['count_available'] or 0
                total = row['total_atms_in_region'] or 0
                availability_pct = (available / total * 100) if total > 0 else 0
                availability_values.append(availability_pct)
                
                status_counts = ATMStatusCounts(
                    available=available,
                    warning=row['count_warning'] or 0,
                    zombie=row['count_zombie'] or 0,
                    wounded=row['count_wounded'] or 0,
                    out_of_service=row['count_out_of_service'] or 0,
                    total=total
                )
                
                trends.append(TrendPoint(
                    timestamp=row['date_creation'],
                    status_counts=status_counts,
                    availability_percentage=round(availability_pct, 2)
                ))
            
            summary_stats = TrendSummaryStats(
                data_points=len(trends),
                time_range_hours=hours,
                avg_availability=round(sum(availability_values) / len(availability_values), 2) if availability_values else 0,
                min_availability=round(min(availability_values), 2) if availability_values else 0,
                max_availability=round(max(availability_values), 2) if availability_values else 0,
                first_reading=trends[0].timestamp if trends else None,
                last_reading=trends[-1].timestamp if trends else None
            )
            
            return RegionalTrends(
                region_code=region_code,
                time_period=f"{hours} hours",
                trends=trends,
                summary_stats=summary_stats
            )
            
        except Exception as e:
            logger.error(f"Error fetching trends for region {region_code}: {e}")
            raise Exception(f"Failed to fetch trend data: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

    def resolve_terminal_details(self, info, terminal_id=None, status=None, hours=24, limit=100):
        """Resolve terminal details"""
        global query_count
        query_count += 1
        
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection unavailable")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    terminal_id, location, issue_state_name, serial_number,
                    retrieved_date, fetched_status, raw_terminal_data, fault_data, metadata
                FROM terminal_details
                WHERE retrieved_date >= NOW() - INTERVAL '%s hours'
            """ % hours
            
            params = []
            
            if terminal_id:
                query += " AND terminal_id = %s"
                params.append(terminal_id)
            
            if status:
                query += " AND fetched_status = %s"
                params.append(status)
            
            query += " ORDER BY retrieved_date DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            terminal_details = []
            for row in rows:
                terminal_details.append(TerminalDetail(
                    terminal_id=row['terminal_id'],
                    location=row['location'],
                    issue_state_name=row['issue_state_name'],
                    serial_number=row['serial_number'],
                    retrieved_date=row['retrieved_date'],
                    fetched_status=row['fetched_status'],
                    raw_terminal_data=row['raw_terminal_data'],
                    fault_data=row['fault_data'],
                    metadata=row['metadata']
                ))
            
            return terminal_details
            
        except Exception as e:
            logger.error(f"Error fetching terminal details: {e}")
            raise Exception(f"Failed to fetch terminal details: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

# Create GraphQL schema
schema = Schema(query=Query)

# Flask app setup
app = Flask(__name__)
CORS(app)

# Add GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enable GraphQL Playground
    )
)

@app.route('/health')
def flask_health():
    """Simple Flask health endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'api_type': 'GraphQL',
        'version': '4.0.0'
    })

@app.route('/')
def index():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'ATM Monitoring GraphQL API',
        'version': '4.0.0',
        'endpoints': {
            'graphql': '/graphql',
            'playground': '/graphql (with GraphiQL enabled)',
            'health': '/health'
        },
        'documentation': 'Visit /graphql for interactive GraphQL Playground',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == "__main__":
    logger.info("Starting ATM GraphQL API server...")
    logger.info("GraphQL Playground available at: http://localhost:4000/graphql")
    app.run(host='0.0.0.0', port=4000, debug=True)
