# Product Requirements Document (PRD) - ATM Dashboard System

**Document Version**: 1.0  
**Last Updated**: January 30, 2025  
**Document Type**: Living Document  
**Next Review**: February 15, 2025  

---

## Document Information

| Field | Value |
|-------|-------|
| Product | ATM Dashboard Monitoring System |
| Feature | Terminal Maintenance Management |
| Priority | High |
| Status | In Development |
| Owner | Development Team |
| Stakeholders | Operations Team, System Administrators |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Feature: Terminal Maintenance Management](#2-feature-terminal-maintenance-management)
3. [Future Features Pipeline](#3-future-features-pipeline)
4. [System Architecture](#4-system-architecture)
5. [Change Log](#5-change-log)

---

## 1. Overview

### 1.1 Product Vision
The ATM Dashboard System provides comprehensive monitoring, maintenance tracking, and predictive analytics for ATM terminal networks. The system enables operators to maintain high availability and operational efficiency through real-time monitoring and structured maintenance management.

### 1.2 Current System Capabilities
- Real-time ATM status monitoring
- Regional status breakdowns
- Historical trend analysis
- Predictive analytics for maintenance
- Notification system for status changes
- RESTful API with FastAPI
- Interactive web dashboard

---

## 2. Feature: Terminal Maintenance Management

### 2.1 Feature Overview

**Feature Name**: Terminal Maintenance Management  
**Version**: 1.0  
**Target Release**: Q1 2025  
**Status**: In Development  

#### 2.1.1 Purpose
Provide a comprehensive CRUD system for tracking ATM maintenance activities, serving as a record-keeping system for maintenance operations performed on ATM terminals.

#### 2.1.2 Success Metrics
- 100% of maintenance activities logged in system
- Reduced maintenance record retrieval time by 80%
- Improved maintenance audit compliance
- Enhanced operational visibility for management

### 2.2 Technical Specifications

#### 2.2.1 Database Schema

**Table**: `terminal_maintenance`

```sql
CREATE TABLE terminal_maintenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    terminal_id VARCHAR(50) NOT NULL,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE,
    problem_description TEXT NOT NULL,
    solution_description TEXT,
    maintenance_type VARCHAR(20) DEFAULT 'CORRECTIVE' 
        CHECK (maintenance_type IN ('PREVENTIVE', 'CORRECTIVE', 'EMERGENCY')),
    priority VARCHAR(10) DEFAULT 'MEDIUM' 
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(20) DEFAULT 'PLANNED' 
        CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    images JSONB DEFAULT '[]',
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_terminal_maintenance_terminal 
        FOREIGN KEY (terminal_id) REFERENCES terminal_details(terminal_id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX idx_terminal_maintenance_terminal_id ON terminal_maintenance(terminal_id);
CREATE INDEX idx_terminal_maintenance_start_datetime ON terminal_maintenance(start_datetime);
CREATE INDEX idx_terminal_maintenance_status ON terminal_maintenance(status);
CREATE INDEX idx_terminal_maintenance_created_by ON terminal_maintenance(created_by);
```

#### 2.2.2 API Endpoints

**Base Path**: `/api/v1/maintenance`

| Method | Endpoint | Description | Auth | Roles |
|--------|----------|-------------|------|-------|
| GET | `/api/v1/maintenance` | List maintenance records | ✅ | All |
| POST | `/api/v1/maintenance` | Create maintenance record | ✅ | operator, admin, superadmin |
| GET | `/api/v1/maintenance/{id}` | Get specific record | ✅ | All |
| PUT | `/api/v1/maintenance/{id}` | Update maintenance record | ✅ | operator, admin, superadmin |
| DELETE | `/api/v1/maintenance/{id}` | Delete maintenance record | ✅ | admin, superadmin |
| GET | `/api/v1/atm/{terminal_id}/maintenance` | ATM maintenance history | ✅ | All |
| POST | `/api/v1/maintenance/{id}/images` | Upload images | ✅ | operator, admin, superadmin |
| DELETE | `/api/v1/maintenance/{id}/images/{image_id}` | Delete image | ✅ | operator, admin, superadmin |

#### 2.2.3 Data Models

```python
class MaintenanceCreate(BaseModel):
    terminal_id: str
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    problem_description: str = Field(..., min_length=10, max_length=2000)
    solution_description: Optional[str] = Field(None, max_length=2000)
    maintenance_type: str = Field("CORRECTIVE", pattern="^(PREVENTIVE|CORRECTIVE|EMERGENCY)$")
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    status: str = Field("PLANNED", pattern="^(PLANNED|IN_PROGRESS|COMPLETED|CANCELLED)$")

class MaintenanceRecord(BaseModel):
    id: str
    terminal_id: str
    terminal_name: Optional[str] = None
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    problem_description: str
    solution_description: Optional[str] = None
    maintenance_type: str
    priority: str
    status: str
    images: List[MaintenanceImage] = []
    duration_hours: Optional[float] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
```

### 2.3 User Experience

#### 2.3.1 Role-Based Access Control

| Role | Create | Read | Update | Delete | Upload Images |
|------|--------|------|--------|--------|---------------|
| viewer | ❌ | ✅ | ❌ | ❌ | ❌ |
| operator | ✅ | ✅ | ✅ | ❌ | ✅ |
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| superadmin | ✅ | ✅ | ✅ | ✅ | ✅ |

#### 2.3.2 Frontend Components

**New Pages**:
- `/maintenance` - Main maintenance management page
- `/maintenance/create` - Create new maintenance record
- `/maintenance/{id}` - View/edit maintenance record
- `/maintenance/{id}/images` - Image management

**Enhanced Pages**:
- ATM detail pages - Add maintenance history tab

**Key Components**:
- `MaintenanceList.tsx` - Filterable table view
- `MaintenanceForm.tsx` - Create/edit form with validation
- `MaintenanceDetail.tsx` - Detailed view with image gallery
- `ImageUpload.tsx` - Drag-and-drop image upload
- `ATMMaintenanceHistory.tsx` - Timeline view for ATM-specific maintenance

#### 2.3.3 File Upload Specifications

```javascript
const UPLOAD_CONFIG = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedExtensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
  maxFilesPerRecord: 5,
  uploadDirectory: 'uploads/maintenance'
};
```

### 2.4 Validation & Security

#### 2.4.1 Business Rules
- `start_datetime` cannot be more than 1 hour in the future
- `end_datetime` must be after `start_datetime` when provided
- `terminal_id` must exist in the system
- Only authorized roles can perform write operations
- Image files must meet security and format requirements

#### 2.4.2 Security Measures
- JWT-based authentication for all endpoints
- Role-based authorization checks
- File upload validation and virus scanning
- SQL injection prevention
- XSS protection for user-generated content
- Secure file storage outside web root

### 2.5 Performance Requirements

#### 2.5.1 Response Times
- List endpoint: < 500ms for 1000 records
- Create/Update operations: < 200ms
- Image upload: < 2s per file (up to 10MB)
- Search/Filter operations: < 300ms

#### 2.5.2 Scalability
- Support up to 10,000 maintenance records
- Handle concurrent users (up to 50)
- Efficient pagination for large datasets
- Optimized database queries with proper indexing

### 2.6 Testing Strategy

#### 2.6.1 Backend Testing
- [ ] Unit tests for all CRUD operations
- [ ] Integration tests for database operations
- [ ] File upload security testing
- [ ] Role-based access control validation
- [ ] Performance testing for large datasets

#### 2.6.2 Frontend Testing
- [ ] Component unit tests
- [ ] Form validation testing
- [ ] File upload flow testing
- [ ] Cross-browser compatibility
- [ ] Mobile responsiveness testing

### 2.7 Deployment Plan

#### 2.7.1 Database Migration
```sql
-- Migration script v1.0
-- File: migrations/001_create_terminal_maintenance.sql
-- Date: 2025-01-30
```

#### 2.7.2 Rollout Strategy
1. **Phase 1**: Backend API deployment (Week 1)
2. **Phase 2**: Frontend integration (Week 2)
3. **Phase 3**: User training and feedback (Week 3)
4. **Phase 4**: Full production rollout (Week 4)

---

## 3. Future Features Pipeline

### 3.1 Planned Features (Q2 2025)

#### 3.1.1 Advanced Maintenance Analytics
**Priority**: Medium  
**Estimated Effort**: 3 weeks  

Features:
- Maintenance cost tracking and reporting
- MTTR (Mean Time To Repair) analytics
- Preventive vs corrective maintenance ratios
- Technician performance metrics
- Maintenance scheduling optimization

#### 3.1.2 Mobile Application for Field Technicians
**Priority**: High  
**Estimated Effort**: 6 weeks  

Features:
- Mobile-first maintenance record creation
- Offline capability with sync
- QR code scanning for terminal identification
- Voice-to-text for problem descriptions
- GPS location verification

#### 3.1.3 Automated Maintenance Scheduling
**Priority**: Medium  
**Estimated Effort**: 4 weeks  

Features:
- Calendar-based maintenance scheduling
- Conflict detection and resolution
- Email/SMS notifications for scheduled maintenance
- Integration with predictive analytics
- Resource allocation optimization

### 3.2 Research & Development (Q3-Q4 2025)

#### 3.2.1 AI-Powered Maintenance Recommendations
**Priority**: Low  
**Estimated Effort**: 8 weeks  

Features:
- Machine learning models for failure prediction
- Optimal maintenance timing recommendations
- Parts inventory optimization
- Maintenance pattern analysis
- Cost-benefit analysis automation

#### 3.2.2 IoT Sensor Integration
**Priority**: Medium  
**Estimated Effort**: 10 weeks  

Features:
- Real-time environmental monitoring
- Vibration and temperature sensors
- Predictive maintenance based on sensor data
- Alert system for abnormal conditions
- Integration with existing monitoring infrastructure

---

## 4. System Architecture

### 4.1 Current Technology Stack

**Backend**:
- FastAPI (Python 3.9+)
- PostgreSQL with asyncpg
- Pydantic for data validation
- JWT for authentication
- Uvicorn ASGI server

**Frontend**:
- React 18+ with TypeScript
- Redux Toolkit for state management
- Material-UI or Tailwind CSS
- Axios for API communication
- React Router for navigation

**Infrastructure**:
- Docker containerization
- Nginx reverse proxy
- Redis for caching (planned)
- File storage system

### 4.2 Integration Points

#### 4.2.1 Existing System Integration
- Terminal details database
- User authentication system
- Notification service
- Predictive analytics engine
- File upload service

#### 4.2.2 External Integrations (Planned)
- Email service (SendGrid/AWS SES)
- SMS service (Twilio)
- Cloud storage (AWS S3)
- Monitoring service (Prometheus/Grafana)

---

## 5. Change Log

### Version 1.0 (January 30, 2025)
**Author**: Development Team  
**Type**: Initial Release  

**Added**:
- Terminal Maintenance Management feature specification
- Complete technical requirements
- Database schema design
- API endpoint definitions
- Frontend component specifications
- Security and validation requirements
- Testing strategy
- Deployment plan

**Changes**: N/A (Initial version)

**Removed**: N/A (Initial version)

---

### Version Template for Future Updates

```markdown
### Version X.X (Date)
**Author**: [Name]  
**Type**: [Feature Addition/Enhancement/Bug Fix/Breaking Change]  

**Added**:
- New feature descriptions
- New requirements
- New components

**Changed**:
- Modified requirements
- Updated specifications
- Enhanced features

**Removed**:
- Deprecated features
- Obsolete requirements

**Migration Notes**:
- Database changes required
- API breaking changes
- Frontend updates needed

**Impact Assessment**:
- User impact level (Low/Medium/High)
- System downtime required
- Training requirements
```

---

## Document Maintenance

### Review Schedule
- **Monthly**: Feature progress review
- **Quarterly**: Complete document review and update
- **Ad-hoc**: As new requirements emerge

### Stakeholder Approval
- [ ] Development Team Lead
- [ ] Operations Manager
- [ ] System Administrator
- [ ] Product Owner

### Distribution List
- Development Team
- Operations Team
- System Administrators
- Management Team
- External Vendors (as needed)

---

**Document Control**  
**Location**: `/Users/luckymifta/Documents/2. AREA/dash-atm/PRD.md`  
**Backup**: Version controlled in Git repository  
**Access**: Internal team members only
