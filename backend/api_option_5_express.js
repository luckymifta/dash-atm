/**
 * Backend API Option 5: Node.js Express API
 * 
 * A lightweight, fast Node.js API using Express.js with PostgreSQL integration.
 * Features: REST endpoints, middleware support, JSON responses, connection pooling.
 * 
 * Strengths:
 * - High performance and scalability with Node.js event-driven architecture
 * - Large ecosystem of npm packages and middleware
 * - Easy to deploy and maintain
 * - Excellent for real-time applications with WebSocket support
 * - JSON-native with built-in parsing
 * 
 * Best for: Teams familiar with JavaScript, microservices architecture,
 *          real-time applications, rapid development cycles
 * 
 * Installation:
 * npm init -y
 * npm install express pg cors helmet morgan compression dotenv
 * npm install --save-dev nodemon
 * 
 * Usage:
 * node api_option_5_express.js
 * or with nodemon for development: npx nodemon api_option_5_express.js
 */

const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

// Database connection pool
const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'atm_database',
    password: process.env.DB_PASSWORD || 'password',
    port: process.env.DB_PORT || 5432,
    max: 20, // Maximum number of clients in the pool
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

// Middleware
app.use(helmet()); // Security headers
app.use(cors()); // Enable CORS
app.use(compression()); // Gzip compression
app.use(morgan('combined')); // Request logging
app.use(express.json()); // Parse JSON bodies

// Helper function to classify health status
function classifyHealthStatus(counts) {
    const total = counts.total || 0;
    if (total === 0) return 'UNKNOWN';
    
    const available = counts.available || 0;
    const availablePercentage = (available / total) * 100;
    
    if (availablePercentage >= 90) return 'HEALTHY';
    if (availablePercentage >= 70) return 'ATTENTION';
    if (availablePercentage >= 50) return 'WARNING';
    return 'CRITICAL';
}

// Helper function to calculate summary statistics
function calculateSummaryStats(data) {
    if (!data || data.length === 0) {
        return {
            total_atms: 0,
            available_atms: 0,
            availability_percentage: 0,
            health_status: 'UNKNOWN'
        };
    }
    
    const totals = data.reduce((acc, row) => {
        const counts = row.regional_data || {};
        return {
            total: acc.total + (counts.total || 0),
            available: acc.available + (counts.available || 0),
            warning: acc.warning + (counts.warning || 0),
            zombie: acc.zombie + (counts.zombie || 0),
            wounded: acc.wounded + (counts.wounded || 0),
            out_of_service: acc.out_of_service + (counts.out_of_service || 0)
        };
    }, { total: 0, available: 0, warning: 0, zombie: 0, wounded: 0, out_of_service: 0 });
    
    const availability_percentage = totals.total > 0 ? (totals.available / totals.total) * 100 : 0;
    
    return {
        total_atms: totals.total,
        available_atms: totals.available,
        warning_atms: totals.warning,
        zombie_atms: totals.zombie,
        wounded_atms: totals.wounded,
        out_of_service_atms: totals.out_of_service,
        availability_percentage: Math.round(availability_percentage * 100) / 100,
        health_status: classifyHealthStatus(totals)
    };
}

// Error handling middleware
function asyncHandler(fn) {
    return (req, res, next) => {
        Promise.resolve(fn(req, res, next)).catch(next);
    };
}

// Routes

// Health check endpoint
app.get('/health', asyncHandler(async (req, res) => {
    try {
        const client = await pool.connect();
        await client.query('SELECT 1');
        client.release();
        
        res.json({
            status: 'healthy',
            timestamp: new Date().toISOString(),
            database: 'connected',
            version: '1.0.0'
        });
    } catch (error) {
        res.status(503).json({
            status: 'unhealthy',
            timestamp: new Date().toISOString(),
            database: 'disconnected',
            error: error.message
        });
    }
}));

// Get ATM summary counts
app.get('/api/atm-summary', asyncHandler(async (req, res) => {
    const useNewTable = req.query.use_new_table === 'true';
    
    let query, queryParams = [];
    
    if (useNewTable) {
        query = `
            SELECT 
                region_name,
                regional_data,
                retrieved_at
            FROM regional_data 
            WHERE retrieved_at >= NOW() - INTERVAL '1 day'
            ORDER BY retrieved_at DESC
        `;
    } else {
        query = `
            SELECT 
                region_name,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                retrieved_at
            FROM regional_atm_counts 
            WHERE retrieved_at >= NOW() - INTERVAL '1 day'
            ORDER BY retrieved_at DESC
        `;
    }
    
    const result = await pool.query(query, queryParams);
    
    let summary;
    if (useNewTable) {
        summary = calculateSummaryStats(result.rows);
    } else {
        const totals = result.rows.reduce((acc, row) => ({
            available: acc.available + (row.count_available || 0),
            warning: acc.warning + (row.count_warning || 0),
            zombie: acc.zombie + (row.count_zombie || 0),
            wounded: acc.wounded + (row.count_wounded || 0),
            out_of_service: acc.out_of_service + (row.count_out_of_service || 0)
        }), { available: 0, warning: 0, zombie: 0, wounded: 0, out_of_service: 0 });
        
        const total = Object.values(totals).reduce((sum, count) => sum + count, 0);
        const availability = total > 0 ? (totals.available / total) * 100 : 0;
        
        summary = {
            total_atms: total,
            available_atms: totals.available,
            warning_atms: totals.warning,
            zombie_atms: totals.zombie,
            wounded_atms: totals.wounded,
            out_of_service_atms: totals.out_of_service,
            availability_percentage: Math.round(availability * 100) / 100,
            health_status: classifyHealthStatus({ total, available: totals.available })
        };
    }
    
    res.json({
        summary,
        last_updated: result.rows[0]?.retrieved_at || null,
        data_source: useNewTable ? 'regional_data' : 'regional_atm_counts',
        total_records: result.rows.length
    });
}));

// Get regional breakdown
app.get('/api/regional-breakdown', asyncHandler(async (req, res) => {
    const useNewTable = req.query.use_new_table === 'true';
    const limit = parseInt(req.query.limit) || 50;
    
    let query, queryParams = [limit];
    
    if (useNewTable) {
        query = `
            SELECT DISTINCT ON (region_name)
                region_name,
                regional_data,
                retrieved_at
            FROM regional_data 
            ORDER BY region_name, retrieved_at DESC
            LIMIT $1
        `;
    } else {
        query = `
            SELECT DISTINCT ON (region_name)
                region_name,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                retrieved_at
            FROM regional_atm_counts 
            ORDER BY region_name, retrieved_at DESC
            LIMIT $1
        `;
    }
    
    const result = await pool.query(query, queryParams);
    
    const regions = result.rows.map(row => {
        if (useNewTable) {
            const data = row.regional_data || {};
            const total = data.total || 0;
            const available = data.available || 0;
            const availability = total > 0 ? (available / total) * 100 : 0;
            
            return {
                region_name: row.region_name,
                total_atms: total,
                available_atms: available,
                warning_atms: data.warning || 0,
                zombie_atms: data.zombie || 0,
                wounded_atms: data.wounded || 0,
                out_of_service_atms: data.out_of_service || 0,
                availability_percentage: Math.round(availability * 100) / 100,
                health_status: classifyHealthStatus({ total, available }),
                last_updated: row.retrieved_at
            };
        } else {
            const counts = {
                available: row.count_available || 0,
                warning: row.count_warning || 0,
                zombie: row.count_zombie || 0,
                wounded: row.count_wounded || 0,
                out_of_service: row.count_out_of_service || 0
            };
            const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
            const availability = total > 0 ? (counts.available / total) * 100 : 0;
            
            return {
                region_name: row.region_name,
                total_atms: total,
                ...counts,
                availability_percentage: Math.round(availability * 100) / 100,
                health_status: classifyHealthStatus({ total, available: counts.available }),
                last_updated: row.retrieved_at
            };
        }
    });
    
    res.json({
        regions,
        total_regions: regions.length,
        data_source: useNewTable ? 'regional_data' : 'regional_atm_counts'
    });
}));

// Get historical trends
app.get('/api/trends', asyncHandler(async (req, res) => {
    const useNewTable = req.query.use_new_table === 'true';
    const days = parseInt(req.query.days) || 7;
    const region = req.query.region;
    
    let query, queryParams = [days];
    let whereClause = `WHERE retrieved_at >= NOW() - INTERVAL '${days} days'`;
    
    if (region) {
        whereClause += ` AND region_name = $${queryParams.length + 1}`;
        queryParams.push(region);
    }
    
    if (useNewTable) {
        query = `
            SELECT 
                region_name,
                regional_data,
                retrieved_at,
                DATE_TRUNC('hour', retrieved_at) as hour_bucket
            FROM regional_data 
            ${whereClause}
            ORDER BY retrieved_at DESC
        `;
    } else {
        query = `
            SELECT 
                region_name,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                retrieved_at,
                DATE_TRUNC('hour', retrieved_at) as hour_bucket
            FROM regional_atm_counts 
            ${whereClause}
            ORDER BY retrieved_at DESC
        `;
    }
    
    const result = await pool.query(query, queryParams);
    
    // Group by hour and calculate averages
    const hourlyData = {};
    result.rows.forEach(row => {
        const hour = row.hour_bucket.toISOString();
        if (!hourlyData[hour]) {
            hourlyData[hour] = {
                timestamp: hour,
                total_available: 0,
                total_atms: 0,
                count: 0
            };
        }
        
        if (useNewTable) {
            const data = row.regional_data || {};
            hourlyData[hour].total_available += data.available || 0;
            hourlyData[hour].total_atms += data.total || 0;
        } else {
            const total = (row.count_available || 0) + (row.count_warning || 0) + 
                         (row.count_zombie || 0) + (row.count_wounded || 0) + 
                         (row.count_out_of_service || 0);
            hourlyData[hour].total_available += row.count_available || 0;
            hourlyData[hour].total_atms += total;
        }
        hourlyData[hour].count += 1;
    });
    
    const trends = Object.values(hourlyData).map(hour => ({
        timestamp: hour.timestamp,
        availability_percentage: hour.total_atms > 0 ? 
            Math.round((hour.total_available / hour.total_atms) * 10000) / 100 : 0,
        total_atms: hour.total_atms,
        available_atms: hour.total_available,
        data_points: hour.count
    })).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    res.json({
        trends,
        period: `${days} days`,
        region: region || 'all_regions',
        data_source: useNewTable ? 'regional_data' : 'regional_atm_counts'
    });
}));

// Get latest data
app.get('/api/latest', asyncHandler(async (req, res) => {
    const useNewTable = req.query.use_new_table === 'true';
    
    let query;
    if (useNewTable) {
        query = `
            SELECT 
                region_name,
                regional_data,
                retrieved_at
            FROM regional_data 
            WHERE retrieved_at = (SELECT MAX(retrieved_at) FROM regional_data)
            ORDER BY region_name
        `;
    } else {
        query = `
            SELECT 
                region_name,
                count_available,
                count_warning,
                count_zombie,
                count_wounded,
                count_out_of_service,
                retrieved_at
            FROM regional_atm_counts 
            WHERE retrieved_at = (SELECT MAX(retrieved_at) FROM regional_atm_counts)
            ORDER BY region_name
        `;
    }
    
    const result = await pool.query(query);
    
    const latestData = result.rows.map(row => {
        if (useNewTable) {
            const data = row.regional_data || {};
            return {
                region_name: row.region_name,
                counts: data,
                retrieved_at: row.retrieved_at
            };
        } else {
            return {
                region_name: row.region_name,
                counts: {
                    available: row.count_available || 0,
                    warning: row.count_warning || 0,
                    zombie: row.count_zombie || 0,
                    wounded: row.count_wounded || 0,
                    out_of_service: row.count_out_of_service || 0
                },
                retrieved_at: row.retrieved_at
            };
        }
    });
    
    res.json({
        latest_data: latestData,
        timestamp: result.rows[0]?.retrieved_at || null,
        total_regions: latestData.length,
        data_source: useNewTable ? 'regional_data' : 'regional_atm_counts'
    });
}));

// Get terminal details
app.get('/api/terminals', asyncHandler(async (req, res) => {
    const region = req.query.region;
    const status = req.query.status;
    const limit = parseInt(req.query.limit) || 100;
    
    let query = `
        SELECT 
            terminal_id,
            region_name,
            terminal_details,
            retrieved_at
        FROM terminal_details 
        WHERE retrieved_at >= NOW() - INTERVAL '1 day'
    `;
    
    const queryParams = [];
    
    if (region) {
        query += ` AND region_name = $${queryParams.length + 1}`;
        queryParams.push(region);
    }
    
    if (status) {
        query += ` AND terminal_details->>'status' = $${queryParams.length + 1}`;
        queryParams.push(status);
    }
    
    query += ` ORDER BY retrieved_at DESC LIMIT $${queryParams.length + 1}`;
    queryParams.push(limit);
    
    const result = await pool.query(query, queryParams);
    
    res.json({
        terminals: result.rows,
        total_terminals: result.rows.length,
        filters: { region, status, limit }
    });
}));

// API documentation endpoint
app.get('/api/docs', (req, res) => {
    const baseUrl = `${req.protocol}://${req.get('host')}`;
    
    res.json({
        title: 'ATM Monitoring API',
        description: 'Node.js Express API for ATM status monitoring and analytics',
        version: '1.0.0',
        base_url: baseUrl,
        endpoints: {
            'GET /health': 'Health check and system status',
            'GET /api/atm-summary': 'Overall ATM status summary',
            'GET /api/regional-breakdown': 'ATM status by region',
            'GET /api/trends': 'Historical availability trends',
            'GET /api/latest': 'Latest ATM status data',
            'GET /api/terminals': 'Individual terminal details',
            'GET /api/docs': 'This documentation'
        },
        query_parameters: {
            use_new_table: 'Use regional_data table instead of regional_atm_counts (boolean)',
            limit: 'Limit number of results (integer)',
            days: 'Number of days for trends (integer, default: 7)',
            region: 'Filter by specific region (string)',
            status: 'Filter terminals by status (string)'
        },
        examples: {
            summary: `${baseUrl}/api/atm-summary`,
            regional: `${baseUrl}/api/regional-breakdown?limit=10`,
            trends: `${baseUrl}/api/trends?days=7&region=JAKARTA`,
            latest: `${baseUrl}/api/latest?use_new_table=true`,
            terminals: `${baseUrl}/api/terminals?region=JAKARTA&status=AVAILABLE`
        }
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Error:', error);
    
    res.status(error.status || 500).json({
        error: {
            message: error.message || 'Internal Server Error',
            status: error.status || 500,
            timestamp: new Date().toISOString()
        }
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: {
            message: 'Endpoint not found',
            status: 404,
            timestamp: new Date().toISOString(),
            available_endpoints: [
                '/health',
                '/api/atm-summary',
                '/api/regional-breakdown',
                '/api/trends',
                '/api/latest',
                '/api/terminals',
                '/api/docs'
            ]
        }
    });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully');
    await pool.end();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully');
    await pool.end();
    process.exit(0);
});

// Start server
app.listen(port, () => {
    console.log(`[START] ATM Monitoring API server running on port ${port}`);
    console.log(`[INFO] API documentation available at http://localhost:${port}/api/docs`);
    console.log(`[INFO] Health check available at http://localhost:${port}/health`);
});

module.exports = app;
