# Daily Terminal Cash Usage API Documentation

This document describes the new API endpoints for calculating and tracking daily terminal cash usage, perfect for building line charts and analytics dashboards.

## Overview

The Daily Cash Usage API calculates how much cash each terminal dispensed per day by:
1. Finding the first cash reading of each day (start amount at 00:00:00)
2. Finding the last cash reading of each day (end amount at 23:59:59)
3. Calculating usage as: `start_amount - end_amount`
4. Running continuously for all terminals
5. Providing data suitable for line charts with date on X-axis and usage amount on Y-axis

## New Endpoints

### 1. GET /api/v1/atm/cash-usage/daily

Calculate daily cash usage for terminals within a date range.

**Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format  
- `terminal_ids` (optional): Comma-separated terminal IDs, or 'all' for all terminals
- `include_partial_data` (optional): Include days with incomplete data (default: true)

**Example Request:**
```bash
GET /api/v1/atm/cash-usage/daily?start_date=2025-07-15&end_date=2025-07-25&terminal_ids=all
```

**Example Response:**
```json
{
  "daily_usage_data": [
    {
      "terminal_id": "ATM001",
      "date": "2025-07-20",
      "start_amount": 100000.0,
      "end_amount": 90000.0,
      "daily_usage": 10000.0,
      "usage_percentage": 10.0,
      "transactions_estimated": 200,
      "terminal_location": "Main Street Branch",
      "start_timestamp": "2025-07-20T00:15:00",
      "end_timestamp": "2025-07-20T23:45:00",
      "data_quality": "COMPLETE"
    }
  ],
  "summary_stats": {
    "total_usage": 150000.0,
    "avg_daily_usage": 7500.0,
    "complete_records": 15,
    "partial_records": 3
  },
  "terminal_count": 5,
  "chart_data": {
    "chart_type": "line",
    "x_axis": {"field": "date", "type": "date", "title": "Date"},
    "y_axis": {"field": "daily_usage", "type": "numeric", "title": "Daily Cash Usage (USD)"}
  }
}
```

### 2. GET /api/v1/atm/cash-usage/trends

Get cash usage trends over time for line chart visualization.

**Parameters:**
- `terminal_id` (optional): Specific terminal ID for individual trends, omit for overall trends
- `days` (optional): Number of days to look back (1-365, default: 30)
- `aggregation` (optional): Aggregation level: daily, weekly, monthly (default: daily)

**Example Request:**
```bash
GET /api/v1/atm/cash-usage/trends?days=30&aggregation=daily
```

**Example Response:**
```json
{
  "terminal_id": null,
  "trend_data": [
    {
      "date": "2025-07-20",
      "total_usage": 45000.0,
      "average_usage_per_terminal": 9000.0,
      "terminal_count": 5,
      "max_usage": 15000.0,
      "min_usage": 5000.0
    }
  ],
  "summary_stats": {
    "total_periods": 30,
    "avg_daily_usage": 8500.0,
    "peak_usage_date": "2025-07-20",
    "peak_usage_amount": 45000.0
  },
  "chart_config": {
    "chart_type": "line",
    "x_axis": {"field": "date", "type": "date", "title": "Date"},
    "y_axis": {"field": "total_usage", "type": "numeric", "title": "Cash Usage (USD)"},
    "line_config": {"interpolation": "linear", "show_points": true}
  }
}
```

### 3. GET /api/v1/atm/{terminal_id}/cash-usage/history

Get detailed cash usage history for a specific terminal.

**Parameters:**
- `terminal_id` (path): Terminal ID to get history for
- `days` (optional): Number of days to look back (1-365, default: 30)
- `include_raw_readings` (optional): Include individual cash readings (default: false)

**Example Request:**
```bash
GET /api/v1/atm/ATM001/cash-usage/history?days=30
```

### 4. GET /api/v1/atm/cash-usage/summary

Get summary statistics for cash usage across all terminals.

**Parameters:**
- `days` (optional): Number of days to analyze (1-90, default: 7)

**Example Request:**
```bash
GET /api/v1/atm/cash-usage/summary?days=7
```

**Example Response:**
```json
{
  "summary": {
    "active_terminals": 10,
    "fleet_total_usage": 500000.0,
    "fleet_avg_daily_usage": 7142.86,
    "analysis_period_days": 7
  },
  "top_terminals": [
    {
      "terminal_id": "ATM001",
      "location": "Main Street",
      "total_usage": 75000.0,
      "avg_daily_usage": 10714.29
    }
  ],
  "insights": [
    "Fleet dispensed $500,000.00 over 7 days across 10 terminals",
    "Average terminal dispensed $50,000.00 per period ($7,142.86 per day)"
  ]
}
```

## Data Quality Indicators

The API provides data quality indicators for each calculation:

- **COMPLETE**: Both start and end amounts available, normal calculation
- **PARTIAL**: Only start OR end amount available, limited analysis possible
- **ESTIMATED**: Calculation required estimation (e.g., due to cash replenishment)
- **MISSING**: No data available for the period

## Frontend Integration Guide

### For Line Charts

Use the `/atm/cash-usage/trends` endpoint:

```javascript
// Fetch trend data
const response = await fetch('/api/v1/atm/cash-usage/trends?days=30');
const data = await response.json();

// The chart_config provides all necessary configuration
const chartConfig = data.chart_config;
const chartData = data.trend_data;

// Example with Chart.js
const chart = new Chart(ctx, {
  type: chartConfig.chart_type,
  data: {
    labels: chartData.map(point => point.date),
    datasets: [{
      label: 'Daily Cash Usage',
      data: chartData.map(point => point.total_usage),
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  },
  options: {
    scales: {
      x: { title: { display: true, text: chartConfig.x_axis.title } },
      y: { title: { display: true, text: chartConfig.y_axis.title } }
    }
  }
});
```

### For Individual Terminal Charts

Use the `/atm/{terminal_id}/cash-usage/history` endpoint:

```javascript
// Fetch individual terminal data
const terminalId = 'ATM001';
const response = await fetch(`/api/v1/atm/${terminalId}/cash-usage/history?days=30`);
const data = await response.json();

// Create line chart for individual terminal
const chartData = data.trend_data.map(point => ({
  x: point.date,
  y: point.total_usage
}));
```

### For Dashboard Widgets

Use the `/atm/cash-usage/summary` endpoint:

```javascript
// Fetch summary for dashboard widgets
const response = await fetch('/api/v1/atm/cash-usage/summary?days=7');
const data = await response.json();

// Display key metrics
document.getElementById('total-usage').textContent = `$${data.summary.fleet_total_usage.toLocaleString()}`;
document.getElementById('avg-usage').textContent = `$${data.summary.fleet_avg_daily_usage.toLocaleString()}`;
document.getElementById('active-terminals').textContent = data.summary.active_terminals;
```

## Example Use Cases

### 1. Daily Cash Usage Tracking
```bash
# Get last 7 days of cash usage for all terminals
GET /api/v1/atm/cash-usage/daily?start_date=2025-07-18&end_date=2025-07-25&terminal_ids=all
```

### 2. Monthly Trend Analysis
```bash
# Get monthly trends for the last year
GET /api/v1/atm/cash-usage/trends?days=365&aggregation=monthly
```

### 3. Individual Terminal Monitoring
```bash
# Monitor specific terminal for last 30 days
GET /api/v1/atm/ATM001/cash-usage/history?days=30
```

### 4. Fleet Performance Dashboard
```bash
# Get weekly summary for dashboard
GET /api/v1/atm/cash-usage/summary?days=7
```

## Testing

Run the test script to verify all endpoints:

```bash
python test_cash_usage_api.py
```

The test script will:
1. Verify API connectivity
2. Test all cash usage endpoints
3. Display sample data and statistics
4. Provide integration guidance

## Database Requirements

The API uses the existing `terminal_cash_information` table with these key fields:
- `terminal_id`: Terminal identifier
- `total_cash_amount`: Cash amount in the terminal
- `retrieval_timestamp`: When the data was collected
- `event_date`: Event timestamp

No database schema changes are required!

## Error Handling

The API includes comprehensive error handling:
- Invalid date formats return HTTP 400
- Database connection issues return HTTP 503
- Missing data returns HTTP 404 with helpful messages
- All errors include descriptive error messages

## Performance Considerations

- Date ranges are limited to 90 days for daily calculations
- Trends endpoint supports up to 365 days
- Database queries are optimized with window functions
- Results include pagination for large datasets
- Connection pooling is used for database efficiency

## Next Steps

1. **Frontend Integration**: Use the chart configurations provided in API responses
2. **Dashboard Creation**: Implement widgets using the summary endpoint
3. **Monitoring**: Set up alerts based on usage patterns
4. **Analytics**: Extend with additional aggregations and insights
