# ATM Dashboard

A comprehensive ATM monitoring dashboard for Timor-Leste, providing real-time availability tracking and historical data analysis.

## Features

- 🏧 **Real-time ATM Monitoring** - Live status updates for ATMs across different regions
- 📊 **Interactive Dashboard** - Visual representation of ATM availability and trends
- 📈 **Historical Analysis** - Time-based availability trends with intelligent fallback
- 📋 **CSV Export** - Download availability data for further analysis
- 🌍 **Regional Filtering** - View data by specific regions (TL-DL, TL-MT, etc.)
- ⏰ **Multiple Time Periods** - 24 hours, 7 days, and 30 days views
- 🔄 **Auto-refresh** - Real-time data updates every 5 minutes

## Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Data visualization library
- **Lucide React** - Icon library

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3.8+** - Backend runtime
- **JSON Data Storage** - Lightweight data persistence
- **CORS Support** - Cross-origin resource sharing

## Project Structure

```
dash-atm/
├── frontend/          # Next.js frontend application
│   ├── src/
│   │   ├── app/       # App router pages
│   │   ├── components/# React components
│   │   └── services/  # API services
│   ├── package.json
│   └── ...
├── backend/           # FastAPI backend application
│   ├── api_option_2_fastapi_fixed.py  # Main API server
│   ├── atm_crawler_complete.py        # Data collection
│   └── *.json        # Historical data files
└── README.md
```

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+ and pip

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install fastapi uvicorn python-multipart
```

3. Start the FastAPI server:
```bash
python api_option_2_fastapi_fixed.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Features

### Enhanced Fallback Logic
The API includes intelligent fallback mechanisms that automatically try shorter time periods when requested data isn't available:

- **Progressive Fallback**: 720h → 168h → 72h → 24h → 12h → 6h → 1h
- **Metadata Response**: Includes original request info and fallback details
- **Consistent Behavior**: All time periods return meaningful data

### Key Endpoints

- `GET /regions/{region_id}/trends` - Get availability trends for a region
- `GET /health` - API health check
- `GET /docs` - Interactive API documentation

### Response Format
```json
{
  "trends": [...],
  "summary_stats": {
    "data_points": 57,
    "time_range_hours": 168,
    "avg_availability": 73.06
  },
  "time_period": "7 days (168 hours)",
  "requested_hours": 720,
  "fallback_message": "Data limited to 7 days due to availability"
}
```

## CSV Export Feature

The dashboard includes a comprehensive CSV export functionality:

- **Metadata Headers** - Export timestamp, time period, and data summary
- **Formatted Data** - Timestamps, formatted times, and availability percentages
- **Smart Filename** - Auto-generated names with period and date
- **Instant Download** - Browser-based file download

Example CSV structure:
```csv
# ATM Availability History Export
# Generated: 2025-06-01T14:30:00.000Z
# Time Period: 7D
# Data Period: 7 days (57 data points)
# Total Data Points: 57
# Region: TL-DL

Timestamp,Formatted Time,Availability Percentage
"2025-05-25T14:30:00Z","May 25, 14:30",71.4
...
```

## Development

### Running Both Services
```bash
# Terminal 1 - Backend
cd backend && python api_option_2_fastapi_fixed.py

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### Key Components

- **ATMAvailabilityChart.tsx** - Main chart component with time filters and export
- **atmApi.ts** - API service layer with TypeScript interfaces
- **api_option_2_fastapi_fixed.py** - Enhanced FastAPI server with fallback logic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
