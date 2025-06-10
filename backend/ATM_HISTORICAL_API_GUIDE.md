# ATM Historical Data API - Implementation Guide

## 🎯 Overview

The enhanced ATM monitoring API now includes **individual ATM historical tracking** capabilities, perfect for creating line charts showing ATM availability history over time.

## 🚀 New Features Added

### 1. Individual ATM Historical Data
**Endpoint:** `GET /api/v1/atm/{terminal_id}/history`

This endpoint provides time-series data for a specific ATM, showing:
- ✅ **Status transitions over time** (AVAILABLE → WARNING → WOUNDED, etc.)
- ✅ **Timestamps for each status change**
- ✅ **Fault descriptions when issues occur**
- ✅ **Chart configuration for frontend display**

### 2. ATM List for Selection
**Endpoint:** `GET /api/v1/atm/list`

Returns available ATMs with filters for:
- ✅ **Region-based filtering**
- ✅ **Status-based filtering**
- ✅ **Current status and metadata**

## 📊 Perfect for Line Charts

### X-Axis: Date/Time Timestamps
```
2025-01-30 08:00:00
2025-01-30 12:00:00
2025-01-30 16:00:00
2025-01-30 20:00:00
```

### Y-Axis: ATM Status Categories
```
AVAILABLE      (Green)
WARNING        (Yellow)
WOUNDED        (Orange)  
ZOMBIE         (Purple)
OUT_OF_SERVICE (Red)
```

## 🔧 API Usage Examples

### Get ATM History for Line Chart
```bash
GET /api/v1/atm/80/history?hours=168&include_fault_details=true
```

**Response:**
```json
{
  "atm_data": {
    "terminal_id": "80",
    "location": "BRI SUB-BRANCH FATUHADA",
    "serial_number": "YB762080",
    "historical_points": [
      {
        "timestamp": "2025-01-23T08:00:00",
        "status": "AVAILABLE",
        "location": "BRI SUB-BRANCH FATUHADA",
        "fault_description": null,
        "serial_number": "YB762080"
      },
      {
        "timestamp": "2025-01-24T14:30:00",
        "status": "WARNING", 
        "location": "BRI SUB-BRANCH FATUHADA",
        "fault_description": "CASH LOW",
        "serial_number": "YB762080"
      },
      {
        "timestamp": "2025-01-25T09:15:00",
        "status": "WOUNDED",
        "location": "BRI SUB-BRANCH FATUHADA", 
        "fault_description": "MEDIA JAMMED",
        "serial_number": "YB762080"
      }
    ],
    "time_period": "168 hours",
    "summary_stats": {
      "data_points": 25,
      "uptime_percentage": 76.0,
      "status_distribution": {
        "AVAILABLE": 19,
        "WARNING": 3,
        "WOUNDED": 3
      }
    }
  },
  "chart_config": {
    "chart_type": "line_chart",
    "x_axis": {
      "field": "timestamp",
      "label": "Date & Time",
      "format": "datetime"
    },
    "y_axis": {
      "field": "status", 
      "label": "ATM Status",
      "categories": ["AVAILABLE", "WARNING", "WOUNDED", "ZOMBIE", "OUT_OF_SERVICE"],
      "colors": {
        "AVAILABLE": "#28a745",
        "WARNING": "#ffc107", 
        "WOUNDED": "#fd7e14",
        "ZOMBIE": "#6f42c1",
        "OUT_OF_SERVICE": "#dc3545"
      }
    }
  }
}
```

### Get List of ATMs
```bash
GET /api/v1/atm/list?limit=50
```

**Response:**
```json
{
  "atms": [
    {
      "terminal_id": "80",
      "location": "BRI SUB-BRANCH FATUHADA", 
      "current_status": "AVAILABLE",
      "serial_number": "YB762080",
      "last_updated": "2025-01-30T10:30:00"
    },
    {
      "terminal_id": "81",
      "location": "NOVO TURISMO, BIDAU LECIDERE",
      "current_status": "WOUNDED", 
      "serial_number": "YB762081",
      "last_updated": "2025-01-30T10:25:00"
    }
  ],
  "total_count": 25
}
```

## 🎨 Frontend Integration

### Chart.js Example
```javascript
// Fetch ATM history
const response = await fetch('/api/v1/atm/80/history?hours=168');
const data = await response.json();

// Prepare chart data
const chartData = {
  labels: data.atm_data.historical_points.map(point => point.timestamp),
  datasets: [{
    label: 'ATM Status',
    data: data.atm_data.historical_points.map(point => point.status),
    backgroundColor: data.chart_config.y_axis.colors,
    borderColor: '#333',
    tension: 0.1
  }]
};

// Create chart
new Chart(ctx, {
  type: 'line',
  data: chartData,
  options: {
    responsive: true,
    scales: {
      x: { 
        title: { display: true, text: 'Date & Time' },
        type: 'time'
      },
      y: { 
        title: { display: true, text: 'ATM Status' },
        type: 'category',
        labels: ['AVAILABLE', 'WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE']
      }
    }
  }
});
```

## 📈 Key Features for Historical Analysis

### 1. **Flexible Time Ranges**
- 1 hour to 90 days (2160 hours)
- Automatic fallback for sparse data
- Default: 7 days (168 hours)

### 2. **Smart Status Mapping**
- `HARD` → `WOUNDED`
- `CASH` → `OUT_OF_SERVICE` 
- `UNAVAILABLE` → `OUT_OF_SERVICE`

### 3. **Rich Metadata**
- Uptime percentage calculation
- Status distribution statistics
- Fault descriptions with timestamps
- Data point count and time coverage

### 4. **Production-Ready Features**
- Database connection pooling
- Error handling with fallbacks
- Timezone conversion (Dili time)
- Comprehensive logging

## 🔄 Deployment

The enhanced API is ready to deploy:

1. **File:** `api_option_2_fastapi_fixed.py`
2. **New Models:** `ATMStatusPoint`, `ATMHistoricalData`, `ATMHistoricalResponse`
3. **New Endpoints:** `/atm/{terminal_id}/history`, `/atm/list`
4. **Database:** Uses existing `terminal_details` table

## 🎯 Use Cases

### Perfect for:
- ✅ **Individual ATM availability dashboards**
- ✅ **Maintenance scheduling based on failure patterns**
- ✅ **SLA monitoring and reporting**
- ✅ **Predictive maintenance insights**
- ✅ **Customer-facing ATM status history**

### Example Questions Answered:
- "How often was ATM #80 available last week?"
- "When did ATM #81 last have a fault?"
- "What's the failure pattern for ATMs in Dili region?"
- "Which ATMs have the most status changes?"

## 🚀 Ready to Use!

Your ATM monitoring system now has full **individual ATM historical tracking** capabilities! 🎉

The API provides everything needed for creating beautiful, informative line charts showing ATM availability history over time.
