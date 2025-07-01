# ATM Masters CRUD API Documentation

## Overview

The ATM Masters CRUD API provides comprehensive Create, Read, Update, Delete functionality for managing ATM master data in the Timor-Leste ATM monitoring system. This API allows you to manage all aspects of ATM information including hardware specifications, location details, operational status, and maintenance schedules.

## Base URL
```
http://localhost:8000/api/v1/atm-masters
```

## Authentication
Currently, the API uses database connection validation. Ensure your database configuration is properly set in the `.env` file.

## Data Models

### ATM Master Record Structure
```json
{
  "id": 1,
  "terminal_id": "TEST001",
  "terminal_name": "Test ATM Central",
  "external_id": "EXT001",
  "network_id": null,
  "business_id": null,
  "technical_code": null,
  "brand": "NCR",
  "model": "SelfServ 24e",
  "serial_number": "NCR123456789",
  "location": "Test Building, Central Dili",
  "location_type": "Financial Institution Office",
  "address_line_1": "123 Test Street",
  "address_line_2": null,
  "city": "Dili",
  "region": "TL-DL",
  "postal_code": null,
  "country": "Timor-Leste",
  "latitude": -8.5594,
  "longitude": 125.5647,
  "geo_location": null,
  "is_active": true,
  "installation_date": null,
  "last_maintenance_date": "2025-06-01",
  "next_maintenance_date": "2025-12-01",
  "service_period": null,
  "maintenance_period": null,
  "created_at": "2025-07-01T09:30:00",
  "updated_at": "2025-07-01T09:30:00",
  "created_by": "test_user",
  "updated_by": "test_user_2"
}
```

## CRUD Endpoints

### 1. CREATE - Add New ATM

**Endpoint:** `POST /api/v1/atm-masters`

**Description:** Creates a new ATM master record in the database.

**Request Body:**
```json
{
  "terminal_id": "ATM001",
  "terminal_name": "Central Bank ATM",
  "brand": "NCR",
  "model": "SelfServ 22e", 
  "location": "Central Bank Building, Dili",
  "region": "TL-DL",
  "is_active": true,
  "created_by": "admin_user"
}
```

**Required Fields:**
- `terminal_id` (string, max 50 chars, unique)
- `brand` (string, max 100 chars)
- `model` (string, max 100 chars)
- `location` (string, max 500 chars)

**Response:** `201 Created`
```json
{
  "id": 15,
  "terminal_id": "ATM001",
  "terminal_name": "Central Bank ATM",
  "brand": "NCR",
  "model": "SelfServ 22e",
  "location": "Central Bank Building, Dili",
  "region": "TL-DL",
  "is_active": true,
  "created_at": "2025-07-01T09:30:00",
  "updated_at": "2025-07-01T09:30:00",
  "created_by": "admin_user",
  "updated_by": null
}
```

### 2. READ - Get Specific ATM

**Endpoint:** `GET /api/v1/atm-masters/{terminal_id}`

**Description:** Retrieves a specific ATM master record by terminal ID.

**Path Parameters:**
- `terminal_id` (string): The terminal ID to retrieve

**Response:** `200 OK`
```json
{
  "id": 15,
  "terminal_id": "ATM001",
  "terminal_name": "Central Bank ATM",
  // ... full ATM record
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "ATM with terminal_id 'ATM001' not found"
}
```

### 3. READ - List ATMs (Paginated)

**Endpoint:** `GET /api/v1/atm-masters`

**Description:** Retrieves a paginated list of ATM master records with optional filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `per_page` (int, default: 20, max: 100): Items per page  
- `region` (string, optional): Filter by region
- `brand` (string, optional): Filter by brand (case-insensitive)
- `is_active` (boolean, optional): Filter by active status
- `location_search` (string, optional): Search in location and terminal name

**Example:** `GET /api/v1/atm-masters?page=1&per_page=10&region=TL-DL&is_active=true`

**Response:** `200 OK`
```json
{
  "atms": [
    {
      "id": 1,
      "terminal_id": "83",
      "terminal_name": "Nautilus Hyosun Dili Center",
      // ... full ATM records
    }
  ],
  "total_count": 14,
  "page": 1,
  "per_page": 10,
  "total_pages": 2,
  "has_next": true,
  "has_previous": false
}
```

### 4. UPDATE - Modify ATM

**Endpoint:** `PUT /api/v1/atm-masters/{terminal_id}`

**Description:** Updates an existing ATM master record. Only provided fields will be updated (partial updates supported).

**Path Parameters:**
- `terminal_id` (string): The terminal ID to update

**Request Body (all fields optional):**
```json
{
  "terminal_name": "Updated ATM Name",
  "location_type": "Bank Branch",
  "last_maintenance_date": "2025-06-01",
  "next_maintenance_date": "2025-12-01",
  "is_active": false,
  "updated_by": "maintenance_user"
}
```

**Response:** `200 OK`
```json
{
  "id": 15,
  "terminal_id": "ATM001",
  "terminal_name": "Updated ATM Name",
  "updated_at": "2025-07-01T10:15:00",
  "updated_by": "maintenance_user"
  // ... full updated record
}
```

### 5. DELETE - Remove ATM

**Endpoint:** `DELETE /api/v1/atm-masters/{terminal_id}`

**Description:** Permanently deletes an ATM master record. This action cannot be undone.

**Path Parameters:**
- `terminal_id` (string): The terminal ID to delete

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "ATM master record for terminal 'ATM001' deleted successfully",
  "terminal_id": "ATM001",
  "timestamp": "2025-07-01T10:30:00"
}
```

## Specialized Query Endpoints

### 6. Query by Region

**Endpoint:** `GET /api/v1/atm-masters/by-region/{region_code}`

**Description:** Gets all ATMs in a specific region.

**Path Parameters:**
- `region_code` (string): Region code (e.g., "TL-DL")

**Query Parameters:**
- `include_inactive` (boolean, default: false): Include inactive ATMs

**Example:** `GET /api/v1/atm-masters/by-region/TL-DL?include_inactive=true`

### 7. Query by Brand

**Endpoint:** `GET /api/v1/atm-masters/by-brand/{brand}`

**Description:** Gets all ATMs of a specific brand.

**Path Parameters:**
- `brand` (string): Brand name (case-insensitive, partial matching)

**Query Parameters:**
- `include_inactive` (boolean, default: false): Include inactive ATMs

**Example:** `GET /api/v1/atm-masters/by-brand/NCR`

### 8. ATM Statistics

**Endpoint:** `GET /api/v1/atm-masters/statistics`

**Description:** Gets comprehensive statistics about the ATM fleet.

**Response:** `200 OK`
```json
{
  "fleet_overview": {
    "total_atms": 14,
    "active_atms": 13,
    "inactive_atms": 1,
    "active_percentage": 92.86
  },
  "brand_distribution": [
    {
      "brand": "Nautilus Hyosun",
      "total_count": 5,
      "active_count": 5,
      "percentage": 35.71
    },
    {
      "brand": "NCR",
      "total_count": 4,
      "active_count": 4,
      "percentage": 28.57
    }
  ],
  "regional_distribution": [
    {
      "region": "TL-DL",
      "total_count": 14,
      "active_count": 13,
      "percentage": 100.0
    }
  ],
  "maintenance_overview": {
    "atms_with_maintenance_history": 8,
    "atms_with_scheduled_maintenance": 6,
    "overdue_maintenance": 0,
    "maintenance_due_soon_30_days": 2
  },
  "geographic_coverage": {
    "atms_with_coordinates": 14,
    "unique_cities": 1,
    "unique_regions": 1,
    "coordinate_coverage_percentage": 100.0
  },
  "generated_at": "2025-07-01T10:45:00"
}
```

## Error Handling

### Common HTTP Status Codes

- **200 OK**: Successful GET, PUT, DELETE operations
- **201 Created**: Successful POST operations
- **400 Bad Request**: Invalid request data or validation errors
- **404 Not Found**: Resource not found
- **409 Conflict**: Duplicate terminal_id on creation
- **500 Internal Server Error**: Database or server errors
- **503 Service Unavailable**: Database connection issues

### Error Response Format
```json
{
  "detail": "Error description message"
}
```

## Validation Rules

### Terminal ID
- Required, unique, max 50 characters
- Cannot be changed after creation

### Coordinates
- If provided, both latitude and longitude must be specified
- Latitude: -90 to 90 degrees
- longitude: -180 to 180 degrees

### Dates
- Installation date cannot be in the future
- Dates should be in ISO format: "YYYY-MM-DD"

### Required Fields
- `terminal_id`: Unique identifier
- `brand`: ATM manufacturer
- `model`: ATM model
- `location`: Physical location description

## Usage Examples

### Creating an ATM with Python
```python
import requests

url = "http://localhost:8000/api/v1/atm-masters"
data = {
    "terminal_id": "NEW001",
    "terminal_name": "New Branch ATM",
    "brand": "Diebold",
    "model": "Opteva 720",
    "location": "New Branch Office, Dili",
    "region": "TL-DL",
    "latitude": -8.5500,
    "longitude": 125.5800,
    "is_active": True,
    "created_by": "admin"
}

response = requests.post(url, json=data)
print(response.json())
```

### Updating Maintenance Information
```python
import requests

terminal_id = "NEW001"
url = f"http://localhost:8000/api/v1/atm-masters/{terminal_id}"
data = {
    "last_maintenance_date": "2025-07-01",
    "next_maintenance_date": "2026-01-01",
    "updated_by": "maintenance_team"
}

response = requests.put(url, json=data)
print(response.json())
```

### Querying Statistics with JavaScript
```javascript
fetch('http://localhost:8000/api/v1/atm-masters/statistics')
  .then(response => response.json())
  .then(data => {
    console.log('Fleet Overview:', data.fleet_overview);
    console.log('Brand Distribution:', data.brand_distribution);
  })
  .catch(error => console.error('Error:', error));
```

## Integration with Existing System

The ATM Masters CRUD API integrates seamlessly with your existing ATM monitoring system:

1. **Consistent Timezone**: Uses Dili local time (+0900) for all timestamps
2. **Database Integration**: Uses the same `development_db` database
3. **Compatible Schema**: Works with existing `atm_masters` table structure
4. **API Consistency**: Follows same patterns as existing monitoring endpoints

## Testing

Use the provided test script to verify functionality:

```bash
python3 test_atm_masters_crud.py
```

This will test all CRUD operations and provide comprehensive output.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Support

For issues or questions about the ATM Masters CRUD API:
1. Check the interactive documentation at `/docs`
2. Review the test script for usage examples
3. Verify database connectivity and table structure
4. Check server logs for detailed error information

---

**Created**: July 1, 2025  
**Version**: 1.0  
**Compatibility**: PostgreSQL 12+, Python 3.8+, FastAPI 0.68+
