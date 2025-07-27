#!/usr/bin/env python3
"""
Advanced Database Query Optimization for ATM Cash Usage
======================================================

This module provides optimized database queries with:
1. Optimized JOIN operations for location data
2. Efficient date partitioning strategies
3. Performance monitoring and query analysis
4. Connection pooling optimization

Optimizations:
- Composite index usage
- CTE (Common Table Expressions) for complex queries
- Efficient date range filtering
- Location data JOIN optimization
- Query result caching at database level
"""

import asyncio
import asyncpg
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Advanced database query optimizer for ATM cash usage data"""
    
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.connection_pool = None
        self.query_stats = {}
        
    async def initialize_pool(self, min_connections: int = 5, max_connections: int = 20):
        """Initialize connection pool for optimal performance"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                **self.db_config,
                min_size=min_connections,
                max_size=max_connections,
                command_timeout=30,
                server_settings={
                    'application_name': 'atm_dashboard_api',
                    'timezone': 'UTC'
                }
            )
            logger.info(f"Database pool initialized: {min_connections}-{max_connections} connections")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool with automatic cleanup"""
        if not self.connection_pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.connection_pool.acquire() as connection:
            yield connection
    
    async def execute_optimized_query(self, query: str, params: tuple = (), query_name: str = "unknown") -> List[Dict]:
        """Execute query with performance monitoring"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *params)
                execution_time = time.time() - start_time
                
                # Track query performance
                if query_name not in self.query_stats:
                    self.query_stats[query_name] = {
                        'count': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'max_time': 0,
                        'min_time': float('inf')
                    }
                
                stats = self.query_stats[query_name]
                stats['count'] += 1
                stats['total_time'] += execution_time
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['max_time'] = max(stats['max_time'], execution_time)
                stats['min_time'] = min(stats['min_time'], execution_time)
                
                logger.debug(f"Query '{query_name}' executed in {execution_time:.3f}s")
                return [dict(row) for row in result]
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query '{query_name}' failed after {execution_time:.3f}s: {e}")
            raise
    
    async def get_optimized_daily_cash_usage(self, 
                                           start_date: datetime, 
                                           end_date: datetime,
                                           terminal_ids: Optional[List[str]] = None) -> List[Dict]:
        """Optimized query for daily cash usage with efficient JOINs"""
        
        # Build optimized query with CTEs and proper indexing
        base_query = """
        WITH date_range AS (
            SELECT generate_series(
                date_trunc('day', $1::timestamp),
                date_trunc('day', $2::timestamp),
                interval '1 day'
            )::date as usage_date
        ),
        terminal_filter AS (
            SELECT DISTINCT terminal_id 
            FROM terminal_cash_information 
            WHERE retrieval_timestamp >= $1 
              AND retrieval_timestamp <= $2
              {terminal_filter}
        ),
        daily_cash_stats AS (
            SELECT 
                tci.terminal_id,
                date(tci.retrieval_timestamp AT TIME ZONE 'Asia/Dili') as usage_date,
                MIN(tci.total_cash_amount) as min_cash,
                MAX(tci.total_cash_amount) as max_cash,
                AVG(tci.total_cash_amount) as avg_cash,
                COUNT(*) as reading_count,
                STDDEV(tci.total_cash_amount) as cash_variance
            FROM terminal_cash_information tci
            INNER JOIN terminal_filter tf ON tci.terminal_id = tf.terminal_id
            WHERE tci.retrieval_timestamp >= $1 
              AND tci.retrieval_timestamp <= $2
              AND tci.total_cash_amount IS NOT NULL 
              AND tci.total_cash_amount > 0
            GROUP BY tci.terminal_id, date(tci.retrieval_timestamp AT TIME ZONE 'Asia/Dili')
        ),
        terminal_locations AS (
            SELECT DISTINCT ON (terminal_id)
                terminal_id,
                location,
                region_code,
                bank_code
            FROM terminal_details
            WHERE retrieved_date >= (CURRENT_DATE - INTERVAL '30 days')
            ORDER BY terminal_id, retrieved_date DESC
        )
        SELECT 
            dr.usage_date,
            COALESCE(tl.terminal_id, tf.terminal_id) as terminal_id,
            COALESCE(tl.location, 'Unknown Location') as location,
            COALESCE(tl.region_code, 'Unknown') as region_code,
            COALESCE(tl.bank_code, 'Unknown') as bank_code,
            COALESCE(dcs.min_cash, 0) as min_cash_amount,
            COALESCE(dcs.max_cash, 0) as max_cash_amount,
            COALESCE(dcs.avg_cash, 0) as avg_cash_amount,
            COALESCE(dcs.reading_count, 0) as reading_count,
            COALESCE(dcs.cash_variance, 0) as cash_variance,
            CASE 
                WHEN dcs.max_cash > dcs.min_cash 
                THEN dcs.max_cash - dcs.min_cash 
                ELSE 0 
            END as cash_usage_amount
        FROM date_range dr
        CROSS JOIN terminal_filter tf
        LEFT JOIN daily_cash_stats dcs ON dr.usage_date = dcs.usage_date 
                                       AND tf.terminal_id = dcs.terminal_id
        LEFT JOIN terminal_locations tl ON tf.terminal_id = tl.terminal_id
        ORDER BY dr.usage_date, tf.terminal_id
        """
        
        # Add terminal filter if specified
        terminal_filter = ""
        params = [start_date, end_date]
        
        if terminal_ids:
            terminal_filter = "AND terminal_id = ANY($3)"
            params.append(terminal_ids)
        
        final_query = base_query.format(terminal_filter=terminal_filter)
        
        return await self.execute_optimized_query(
            final_query, 
            tuple(params), 
            "optimized_daily_cash_usage"
        )
    
    async def get_optimized_cash_trends(self, 
                                      days: int = 30, 
                                      aggregation: str = 'daily') -> List[Dict]:
        """Optimized query for cash usage trends with efficient aggregation"""
        
        # Define aggregation intervals
        interval_map = {
            'daily': "date_trunc('day', retrieval_timestamp AT TIME ZONE 'Asia/Dili')",
            'weekly': "date_trunc('week', retrieval_timestamp AT TIME ZONE 'Asia/Dili')",
            'monthly': "date_trunc('month', retrieval_timestamp AT TIME ZONE 'Asia/Dili')"
        }
        
        date_trunc_expr = interval_map.get(aggregation, interval_map['daily'])
        
        query = f"""
        WITH time_series AS (
            SELECT 
                {date_trunc_expr} as period_start,
                terminal_id,
                MIN(total_cash_amount) as period_min_cash,
                MAX(total_cash_amount) as period_max_cash,
                AVG(total_cash_amount) as period_avg_cash,
                COUNT(*) as reading_count
            FROM terminal_cash_information
            WHERE retrieval_timestamp >= NOW() - INTERVAL '{days} days'
              AND total_cash_amount IS NOT NULL
              AND total_cash_amount > 0
            GROUP BY {date_trunc_expr}, terminal_id
        ),
        aggregated_trends AS (
            SELECT 
                period_start,
                COUNT(DISTINCT terminal_id) as active_terminals,
                SUM(period_max_cash - period_min_cash) as total_usage,
                AVG(period_avg_cash) as fleet_avg_cash,
                SUM(reading_count) as total_readings,
                MAX(period_max_cash) as max_terminal_cash,
                MIN(period_min_cash) as min_terminal_cash
            FROM time_series
            GROUP BY period_start
        )
        SELECT 
            period_start,
            active_terminals,
            COALESCE(total_usage, 0) as total_cash_usage,
            COALESCE(fleet_avg_cash, 0) as average_cash_level,
            total_readings,
            max_terminal_cash,
            min_terminal_cash,
            CASE 
                WHEN active_terminals > 0 
                THEN total_usage / active_terminals 
                ELSE 0 
            END as usage_per_terminal
        FROM aggregated_trends
        ORDER BY period_start
        """
        
        return await self.execute_optimized_query(
            query, 
            (), 
            f"optimized_trends_{aggregation}_{days}d"
        )
    
    async def get_optimized_terminal_rankings(self, days: int = 7) -> List[Dict]:
        """Optimized query for terminal cash usage rankings"""
        
        query = """
        WITH terminal_performance AS (
            SELECT 
                tci.terminal_id,
                COUNT(*) as total_readings,
                MIN(tci.total_cash_amount) as min_cash,
                MAX(tci.total_cash_amount) as max_cash,
                AVG(tci.total_cash_amount) as avg_cash,
                SUM(CASE WHEN tci.total_cash_amount > 0 THEN 1 ELSE 0 END) as active_readings,
                MAX(tci.total_cash_amount) - MIN(tci.total_cash_amount) as total_usage
            FROM terminal_cash_information tci
            WHERE tci.retrieval_timestamp >= NOW() - INTERVAL '%s days'
              AND tci.total_cash_amount IS NOT NULL
            GROUP BY tci.terminal_id
            HAVING COUNT(*) >= 5  -- Minimum readings for ranking
        ),
        terminal_details_latest AS (
            SELECT DISTINCT ON (terminal_id)
                terminal_id,
                location,
                region_code,
                bank_code
            FROM terminal_details
            WHERE retrieved_date >= (CURRENT_DATE - INTERVAL '30 days')
            ORDER BY terminal_id, retrieved_date DESC
        )
        SELECT 
            tp.terminal_id,
            COALESCE(tdl.location, 'Unknown Location') as location,
            COALESCE(tdl.region_code, 'Unknown') as region_code,
            COALESCE(tdl.bank_code, 'Unknown') as bank_code,
            tp.total_readings,
            tp.min_cash,
            tp.max_cash,
            tp.avg_cash,
            tp.active_readings,
            tp.total_usage,
            ROUND((tp.active_readings::decimal / tp.total_readings) * 100, 2) as uptime_percentage,
            RANK() OVER (ORDER BY tp.total_usage DESC) as usage_rank,
            RANK() OVER (ORDER BY tp.avg_cash DESC) as cash_level_rank
        FROM terminal_performance tp
        LEFT JOIN terminal_details_latest tdl ON tp.terminal_id = tdl.terminal_id
        ORDER BY tp.total_usage DESC
        """
        
        return await self.execute_optimized_query(
            query % days, 
            (), 
            f"optimized_rankings_{days}d"
        )
    
    async def get_optimized_summary_stats(self, days: int = 7) -> Dict:
        """Optimized query for fleet-wide cash usage summary"""
        
        query = """
        WITH fleet_stats AS (
            SELECT 
                COUNT(DISTINCT terminal_id) as active_terminals,
                COUNT(*) as total_readings,
                SUM(total_cash_amount) as total_fleet_cash,
                AVG(total_cash_amount) as avg_cash_per_reading,
                MIN(total_cash_amount) as min_cash,
                MAX(total_cash_amount) as max_cash,
                STDDEV(total_cash_amount) as cash_stddev
            FROM terminal_cash_information
            WHERE retrieval_timestamp >= NOW() - INTERVAL '%s days'
              AND total_cash_amount IS NOT NULL
              AND total_cash_amount > 0
        ),
        daily_usage AS (
            SELECT 
                terminal_id,
                DATE(retrieval_timestamp AT TIME ZONE 'Asia/Dili') as usage_date,
                MAX(total_cash_amount) - MIN(total_cash_amount) as daily_usage
            FROM terminal_cash_information
            WHERE retrieval_timestamp >= NOW() - INTERVAL '%s days'
              AND total_cash_amount IS NOT NULL
              AND total_cash_amount > 0
            GROUP BY terminal_id, DATE(retrieval_timestamp AT TIME ZONE 'Asia/Dili')
            HAVING MAX(total_cash_amount) > MIN(total_cash_amount)
        )
        SELECT 
            fs.*,
            COALESCE(AVG(du.daily_usage), 0) as avg_daily_usage,
            COALESCE(SUM(du.daily_usage), 0) as total_period_usage,
            COUNT(DISTINCT du.usage_date) as active_days
        FROM fleet_stats fs
        CROSS JOIN daily_usage du
        GROUP BY fs.active_terminals, fs.total_readings, fs.total_fleet_cash, 
                 fs.avg_cash_per_reading, fs.min_cash, fs.max_cash, fs.cash_stddev
        """
        
        result = await self.execute_optimized_query(
            query % (days, days), 
            (), 
            f"optimized_summary_{days}d"
        )
        
        return result[0] if result else {}
    
    async def get_query_performance_stats(self) -> Dict:
        """Get database query performance statistics"""
        return {
            'query_statistics': self.query_stats,
            'connection_pool': {
                'size': self.connection_pool.get_size() if self.connection_pool else 0,
                'available': self.connection_pool.get_idle_size() if self.connection_pool else 0,
                'in_use': self.connection_pool.get_size() - self.connection_pool.get_idle_size() 
                         if self.connection_pool else 0
            }
        }
    
    async def close_pool(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Database connection pool closed")

# Singleton database optimizer instance
db_optimizer = None

async def get_database_optimizer(db_config: dict) -> DatabaseOptimizer:
    """Get or create database optimizer instance"""
    global db_optimizer
    
    if db_optimizer is None:
        db_optimizer = DatabaseOptimizer(db_config)
        await db_optimizer.initialize_pool()
    
    return db_optimizer
