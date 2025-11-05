# CCTV Face Attendance System - Complete Backend Implementation Plan

## 📋 Table of Contents
1. [Executive Summary](#executive-summary)
2. [Frontend Analysis](#frontend-analysis)
3. [Technology Stack](#technology-stack)
4. [Architecture Overview](#architecture-overview)
5. [Database Design](#database-design)
6. [API Endpoints Specification](#api-endpoints-specification)
7. [Background Jobs & Celery Tasks](#background-jobs--celery-tasks)
8. [WebSocket Channels](#websocket-channels)
9. [File Storage Strategy](#file-storage-strategy)
10. [Security & Authentication](#security--authentication)
11. [Implementation Phases](#implementation-phases)
12. [Development Environment Setup](#development-environment-setup)
13. [Performance Optimization](#performance-optimization)
14. [Testing Strategy](#testing-strategy)

---

## Executive Summary

### Project Goal
Build a production-ready Python FastAPI backend for an existing React TypeScript frontend that manages CCTV-based face recognition attendance tracking with Odoo ERP integration and third-party detection provider support.

### Key Metrics from Frontend Analysis
- **13 Pages**: Dashboard, Live View, Attendance, Cameras, Face Register, Alerts, Settings, Reports, System Health, Audit Log, History, Developer Console, Login
- **48 API Endpoints**: All endpoints mapped and verified
- **Polling Intervals**: 4s (fastest - live detections) to 60s (slowest - roles)
- **Real-time Requirements**: Detection updates every 4s, camera feeds every 6.5s
- **File Upload Support**: Multipart form data for face registration
- **Export Features**: CSV and PDF generation for attendance logs

---

## Frontend Analysis

### 1. **Page-by-Page Breakdown**

#### Dashboard (`/`)
- **Polling Intervals**: Cameras (7s), Camera Summary (12s), Attendance (9s), Alerts (8s), Network Metrics (15s), Shifts (18s)
- **Key Features**: Grid view toggle (2x2 or 3x3), real-time camera status, attendance table, alert feed, network health, shift compliance
- **Backend Requirements**:
  - Fast camera list endpoint with status
  - Aggregated dashboard summary
  - Recent attendance records
  - Alert feed with severity levels

#### Live View (`/live` & `/live/:cameraId`)
- **Polling Intervals**: Cameras (6.5s), Summaries (12s), Live Detections (4s - fastest!), Provider Config (20s), Event Logs (20s)
- **Key Features**: Multi-camera grid, single camera focus, detection provider testing, send frame for detection
- **Backend Requirements**:
  - **Critical**: Live detections endpoint must be fast (<200ms)
  - Camera stream management
  - Detection job queue (Celery)
  - Provider health checks

#### Attendance (`/attendance`)
- **Polling Intervals**: Logs (15s), Odoo Config (20s), Odoo Logs (20s), Cameras (45s), Statistics (30s each)
- **Key Features**: Advanced filtering (search, camera, date range, Odoo status), export (CSV/PDF), Odoo sync, statistics charts
- **Backend Requirements**:
  - Complex filtering logic
  - Pagination support
  - Export generation (Celery)
  - Odoo API integration
  - Statistics aggregation

#### Settings (`/settings`)
- **Polling Intervals**: Cameras (20s), Roles (60s), Users (30s), Odoo/Detection configs (30s each)
- **Key Features**: Camera CRUD, user management, Odoo integration settings, detection provider settings, camera import/export
- **Backend Requirements**:
  - Full CRUD for cameras, users
  - Configuration management
  - JSON import/export
  - Connection testing

#### Face Register (`/face-register`)
- **Polling Intervals**: Face Profiles (12s)
- **Key Features**: Face registration with image upload, profile management, status updates
- **Backend Requirements**:
  - Multipart file upload
  - Image storage (MinIO)
  - Face profile CRUD

#### Alerts (`/alerts`)
- **Polling Intervals**: Alerts (8s - fast!)
- **Key Features**: Acknowledge, mute, clear alerts
- **Backend Requirements**:
  - Alert state management
  - Filtering by level/acknowledged status

#### Other Pages
- **Reports**: Statistics aggregation
- **Cameras**: Camera grid view
- **System Health**: Resource metrics, service status, restart commands
- **History**: Person-specific detection history
- **Audit Log**: System audit trail
- **Developer Console**: API endpoint testing

### 2. **Data Flow Patterns**

```
Frontend Polling (usePolling hook) → REST API → Database
                                   ↓
                                Cache (Redis)
                                   ↓
                            Background Jobs (Celery)
                                   ↓
                          Third-party APIs (Odoo, Detection Provider)
```

### 3. **Critical Performance Requirements**

| Endpoint Type | Target Response Time | Polling Interval | Priority |
|---------------|---------------------|------------------|----------|
| Live Detections | <200ms | 4s | **CRITICAL** |
| Camera List | <300ms | 6.5-20s | HIGH |
| Attendance Logs | <400ms | 15s | HIGH |
| Alerts | <250ms | 8s | HIGH |
| System Metrics | <300ms | 8-15s | MEDIUM |
| Statistics | <500ms | 30s | MEDIUM |
| Roles/Settings | <400ms | 30-60s | LOW |

---

## Technology Stack

### Core Stack
```python
Python 3.11+
FastAPI 0.109+          # REST API + WebSocket + auto OpenAPI
Uvicorn/Gunicorn       # ASGI server
SQLAlchemy 2.0         # ORM
Alembic               # Database migrations
Pydantic v2           # Data validation
```

### Data & Caching
```python
PostgreSQL 15         # Primary database
Redis 7              # Caching + Celery broker
```

### Background Processing
```python
Celery 5.3+          # Distributed task queue
Celery Beat          # Scheduled tasks
Flower (optional)    # Celery monitoring
```

### File Storage
```python
MinIO                # S3-compatible storage
Boto3                # S3 client
```

### Media Processing
```python
FFmpeg               # Video snapshot generation
python-ffmpeg-video-streaming (optional)
```

### Authentication
```python
python-jose[cryptography]  # JWT tokens
passlib[bcrypt]           # Password hashing
python-multipart          # File uploads
```

### HTTP & Integration
```python
httpx                # Async HTTP client (Odoo, Detection Provider)
```

### Development
```python
pytest               # Testing
pytest-asyncio       # Async tests
pytest-cov          # Coverage
black               # Code formatting
ruff                # Linting
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
│          (Polling: 4s-60s intervals + WebSocket)                │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST + WebSocket
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ REST API     │  │  WebSocket   │  │   Auth       │          │
│  │ (48 endpoints)│  │  Channels    │  │   JWT        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────┬────────────────────┬────────────────────────────────────┘
         │                    │
         ↓                    ↓
┌─────────────────┐    ┌──────────────────┐
│   PostgreSQL    │    │      Redis       │
│   (Primary DB)  │    │  Cache + Broker  │
└─────────────────┘    └────────┬─────────┘
                               │
                               ↓
                    ┌────────────────────┐
                    │  Celery Workers    │
                    │  ┌──────────────┐  │
                    │  │ Detection    │  │
                    │  │ Odoo Sync    │  │
                    │  │ Exports      │  │
                    │  │ Monitoring   │  │
                    │  └──────────────┘  │
                    └──┬──────────────┬──┘
                       │              │
          ┌────────────┘              └────────────┐
          ↓                                        ↓
┌──────────────────┐                    ┌──────────────────┐
│  MinIO (S3)      │                    │  External APIs   │
│  - Face Images   │                    │  - Odoo ERP      │
│  - Snapshots     │                    │  - Detection     │
│  - Exports       │                    │    Provider      │
└──────────────────┘                    └──────────────────┘
```

### Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app entry point
│   ├── __init__.py
│   │
│   ├── api/                        # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py             # Authentication endpoints
│   │       ├── users.py            # User management
│   │       ├── cameras.py          # Camera CRUD
│   │       ├── detections.py       # Live detections, provider
│   │       ├── attendance.py       # Attendance logs, stats
│   │       ├── odoo.py             # Odoo integration
│   │       ├── faces.py            # Face registration
│   │       ├── alerts.py           # Alerts & notifications
│   │       ├── system.py           # System health
│   │       ├── audit.py            # Audit trail
│   │       ├── developer.py        # Developer console
│   │       └── settings.py         # Settings & preferences
│   │
│   ├── core/                       # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic settings
│   │   ├── security.py             # JWT, password hashing
│   │   ├── deps.py                 # FastAPI dependencies
│   │   ├── errors.py               # Custom exceptions
│   │   └── logging.py              # Logging config
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── detection.py
│   │   ├── attendance.py
│   │   ├── face.py
│   │   ├── alert.py
│   │   ├── audit.py
│   │   └── system.py
│   │
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── detection.py
│   │   ├── attendance.py
│   │   ├── face.py
│   │   ├── alert.py
│   │   └── common.py               # Shared schemas
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                 # Base repository
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── detection.py
│   │   ├── attendance.py
│   │   └── face.py
│   │
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── camera_service.py
│   │   ├── detection_service.py
│   │   ├── attendance_service.py
│   │   ├── odoo_client.py          # Odoo API client
│   │   ├── detection_provider.py   # Detection API client
│   │   ├── export_service.py       # CSV/PDF generation
│   │   ├── storage_service.py      # MinIO operations
│   │   └── ffmpeg_service.py       # Video processing
│   │
│   ├── ws/                         # WebSocket
│   │   ├── __init__.py
│   │   ├── manager.py              # Connection manager
│   │   └── channels.py             # Channel handlers
│   │
│   └── db/                         # Database
│       ├── __init__.py
│       ├── base.py                 # Base model
│       ├── session.py              # DB session
│       └── init_db.py              # DB initialization
│
├── worker/                         # Celery workers
│   ├── __init__.py
│   ├── celery_app.py               # Celery config
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── detection.py            # Detection tasks
│   │   ├── odoo.py                 # Odoo sync tasks
│   │   ├── export.py               # Export generation
│   │   ├── monitoring.py           # Health checks
│   │   └── cleanup.py              # Data cleanup
│   └── beat_schedule.py            # Periodic tasks
│
├── migrations/                     # Alembic migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/                          # Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/                         # Docker configs
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
├── scripts/                        # Utility scripts
│   ├── init_db.py
│   ├── seed_data.py
│   └── test_connections.py
│
├── .env.example
├── .gitignore
├── pyproject.toml                  # Poetry dependencies
├── pytest.ini
└── README.md
```

---

## Database Design

### Entity Relationship Diagram

```
users ─────┐
  ├─ id (PK)│
  ├─ email  │
  ├─ role_id (FK) ────→ roles
  └─ ...    │              ├─ id (PK)
            │              ├─ name
            │              └─ permissions (JSON)
            │
cameras ───┤
  ├─ id (PK)│
  ├─ name   │
  ├─ stream_type
  └─ ...    │
            │
detections ┼─────→ cameras (FK: camera_id)
  ├─ id (PK)│
  ├─ person_id
  ├─ confidence
  └─ ...    │
            │
attendance_logs ──┼─────→ cameras (FK: camera_id)
  ├─ id (PK)      │
  ├─ employee_id  │
  ├─ odoo_status  │
  └─ ...          │
                  │
face_profiles ────┤
  ├─ id (PK)      │
  ├─ employee_id  │
  └─ ...          │
                  │
face_images ──────┴─────→ face_profiles (FK: profile_id)
  ├─ id (PK)
  ├─ s3_key
  └─ ...

alerts, audit_logs, system_metrics, odoo_configs, etc.
```

### Database Schema (PostgreSQL)

#### 1. **users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role_id VARCHAR(50) NOT NULL,  -- FK to roles
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, suspended
    last_active TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_id ON users(role_id);
```

#### 2. **roles**
```sql
CREATE TABLE roles (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., 'ROLE-ADMIN'
    name VARCHAR(50) NOT NULL,   -- Admin, Operator, Viewer
    permissions JSONB NOT NULL,  -- ["cameras:read", "cameras:write", ...]
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed data
INSERT INTO roles (id, name, permissions, description) VALUES
('ROLE-ADMIN', 'Admin', '["*"]', 'Full system access'),
('ROLE-OPERATOR', 'Operator', '["cameras:read", "cameras:write", "attendance:read", "faces:write"]', 'Operational access'),
('ROLE-VIEWER', 'Viewer', '["cameras:read", "attendance:read", "system:read"]', 'Read-only access');
```

#### 3. **user_sessions** (Refresh tokens)
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(512) UNIQUE NOT NULL,  -- Hashed
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(refresh_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
```

#### 4. **cameras**
```sql
CREATE TABLE cameras (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., 'CAM-01'
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    stream_type VARCHAR(20) NOT NULL,  -- RTSP, USB, HTTP, Socket, Local File
    stream_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'offline',  -- online, offline, maintenance
    fps INTEGER DEFAULT 0,
    latency NUMERIC(10,2) DEFAULT 0,
    bitrate NUMERIC(10,2) DEFAULT 0,
    resolution VARCHAR(20),
    ip_address INET,
    tags JSONB DEFAULT '[]',
    thumbnail VARCHAR(255),
    enabled BOOLEAN DEFAULT true,
    last_seen TIMESTAMP WITH TIME ZONE,
    last_checked TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_cameras_status ON cameras(status);
CREATE INDEX idx_cameras_enabled ON cameras(enabled);
```

#### 5. **camera_summaries**
```sql
CREATE TABLE camera_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    detections_today INTEGER DEFAULT 0,
    unknown_faces INTEGER DEFAULT 0,
    uptime_percent NUMERIC(5,2) DEFAULT 0,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(camera_id, date)
);

CREATE INDEX idx_camera_summaries_camera_id ON camera_summaries(camera_id);
CREATE INDEX idx_camera_summaries_date ON camera_summaries(date);
```

#### 6. **detections**
```sql
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id VARCHAR(50),  -- e.g., 'EMP-00412'
    name VARCHAR(255),
    camera_id VARCHAR(50) NOT NULL REFERENCES cameras(id),
    confidence NUMERIC(5,2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    track_id VARCHAR(100),
    bounding_box JSONB,  -- {top, left, width, height}
    thumbnail VARCHAR(255),
    status VARCHAR(20) NOT NULL,  -- authorized, visitor, unknown
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_detections_camera_id ON detections(camera_id);
CREATE INDEX idx_detections_timestamp ON detections(timestamp DESC);
CREATE INDEX idx_detections_person_id ON detections(person_id);
```

#### 7. **detection_event_logs**
```sql
CREATE TABLE detection_event_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) NOT NULL REFERENCES cameras(id),
    camera_name VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL,  -- received, processing, error
    latency_ms INTEGER,
    payload JSONB,  -- Raw provider response
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_detection_event_logs_camera_id ON detection_event_logs(camera_id);
CREATE INDEX idx_detection_event_logs_timestamp ON detection_event_logs(timestamp DESC);
```

#### 8. **detection_provider_config**
```sql
CREATE TABLE detection_provider_config (
    id INTEGER PRIMARY KEY DEFAULT 1,  -- Singleton
    provider_name VARCHAR(255) NOT NULL,
    endpoint TEXT NOT NULL,
    api_key VARCHAR(512),  -- Encrypted
    enabled BOOLEAN DEFAULT true,
    status VARCHAR(20) DEFAULT 'offline',  -- connected, degraded, offline
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    average_latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    CONSTRAINT chk_singleton CHECK (id = 1)
);

INSERT INTO detection_provider_config (provider_name, endpoint, enabled, status)
VALUES ('Default Provider', 'http://localhost:8001/detect', true, 'offline');
```

#### 9. **attendance_logs**
```sql
CREATE TABLE attendance_logs (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., 'ATT-20251103-001'
    employee_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    date DATE NOT NULL,
    time_in TIME,
    time_out TIME,
    camera_id VARCHAR(50) REFERENCES cameras(id),
    camera_name VARCHAR(255),
    accuracy NUMERIC(5,2),
    status VARCHAR(20) NOT NULL,  -- present, late, missed
    odoo_status VARCHAR(20) DEFAULT 'pending',  -- synced, pending, failed
    odoo_sync_time TIMESTAMP WITH TIME ZONE,
    odoo_error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_attendance_logs_employee_id ON attendance_logs(employee_id);
CREATE INDEX idx_attendance_logs_date ON attendance_logs(date DESC);
CREATE INDEX idx_attendance_logs_odoo_status ON attendance_logs(odoo_status);
```

#### 10. **attendance_records** (Real-time presence)
```sql
CREATE TABLE attendance_records (
    id VARCHAR(50) PRIMARY KEY,
    person_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    department VARCHAR(255),
    status VARCHAR(20) NOT NULL,  -- on-site, off-site, remote
    accuracy NUMERIC(5,2),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    camera_id VARCHAR(50) REFERENCES cameras(id),
    camera_name VARCHAR(255),
    thumbnail VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_attendance_records_person_id ON attendance_records(person_id);
CREATE INDEX idx_attendance_records_timestamp ON attendance_records(timestamp DESC);
```

#### 11. **face_profiles**
```sql
CREATE TABLE face_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',  -- active, pending, archived
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_face_profiles_employee_id ON face_profiles(employee_id);
CREATE INDEX idx_face_profiles_department ON face_profiles(department);
CREATE INDEX idx_face_profiles_status ON face_profiles(status);
```

#### 12. **face_images**
```sql
CREATE TABLE face_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES face_profiles(id) ON DELETE CASCADE,
    s3_key VARCHAR(512) NOT NULL,  -- Path in MinIO/S3
    url TEXT,  -- Signed URL (regenerated on read)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_face_images_profile_id ON face_images(profile_id);
```

#### 13. **odoo_config**
```sql
CREATE TABLE odoo_config (
    id INTEGER PRIMARY KEY DEFAULT 1,  -- Singleton
    base_url TEXT NOT NULL,
    database VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    api_key VARCHAR(512),  -- Encrypted
    auto_sync BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'disconnected',  -- connected, disconnected, error
    last_sync TIMESTAMP WITH TIME ZONE,
    pending_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    CONSTRAINT chk_singleton CHECK (id = 1)
);
```

#### 14. **odoo_sync_logs**
```sql
CREATE TABLE odoo_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    employee_id VARCHAR(50) NOT NULL,
    result VARCHAR(20) NOT NULL,  -- success, failure
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_odoo_sync_logs_timestamp ON odoo_sync_logs(timestamp DESC);
CREATE INDEX idx_odoo_sync_logs_result ON odoo_sync_logs(result);
```

#### 15. **alerts**
```sql
CREATE TABLE alerts (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    level VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    camera_id VARCHAR(50) REFERENCES cameras(id),
    acknowledged BOOLEAN DEFAULT false,
    muted BOOLEAN DEFAULT false,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_level ON alerts(level);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
```

#### 16. **notifications**
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL = broadcast
    title VARCHAR(255) NOT NULL,
    message TEXT,
    level VARCHAR(20) NOT NULL,  -- info, warning, critical
    acknowledged BOOLEAN DEFAULT false,
    link TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_acknowledged ON notifications(acknowledged);
CREATE INDEX idx_notifications_timestamp ON notifications(timestamp DESC);
```

#### 17. **audit_logs**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor VARCHAR(255) NOT NULL,
    actor_role VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    message TEXT NOT NULL,
    context JSONB,
    severity VARCHAR(20) NOT NULL,  -- info, warning, critical
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_actor ON audit_logs(actor);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
```

#### 18. **system_metrics**
```sql
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL,  -- cpu, gpu, memory, disk, network
    label VARCHAR(255) NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    unit VARCHAR(20),
    limit_value NUMERIC(10,2),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_system_metrics_category ON system_metrics(category);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp DESC);
```

#### 19. **system_services**
```sql
CREATE TABLE system_services (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'stopped',  -- running, degraded, stopped
    version VARCHAR(50),
    uptime VARCHAR(100),
    last_restart TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 20. **shift_schedules**
```sql
CREATE TABLE shift_schedules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(255),
    expected_headcount INTEGER NOT NULL,
    compliance NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 21. **user_preferences**
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'dark',
    grid_mode VARCHAR(20) DEFAULT '3x3',
    auto_rotate BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',  -- Additional custom preferences
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 22. **export_jobs**
```sql
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(50) NOT NULL,  -- attendance, audit, history
    format VARCHAR(10) NOT NULL,  -- csv, pdf
    filters JSONB,
    status VARCHAR(20) DEFAULT 'queued',  -- queued, processing, completed, failed
    s3_key VARCHAR(512),
    download_url TEXT,  -- Signed URL
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE  -- For cleanup
);

CREATE INDEX idx_export_jobs_user_id ON export_jobs(user_id);
CREATE INDEX idx_export_jobs_status ON export_jobs(status);
CREATE INDEX idx_export_jobs_created_at ON export_jobs(created_at DESC);
```

---

## API Endpoints Specification

### Base URL: `/api/v1`

### Response Envelope
All responses follow this structure:

**Success:**
```json
{
  "success": true,
  "data": <payload>,
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {"field": "email", "issue": "Invalid format"}
  },
  "requestId": "uuid"
}
```

### 1. **Authentication & Users**

#### `POST /auth/login`
- **Description**: User login
- **Request Body**:
  ```json
  {
    "username": "admin@example.com",
    "password": "password123"
  }
  ```
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "accessToken": "eyJ...",
      "refreshToken": "eyJ...",
      "user": {
        "id": "uuid",
        "name": "Admin User",
        "email": "admin@example.com",
        "roleId": "ROLE-ADMIN",
        "status": "active",
        "lastActive": "2025-11-05T10:30:00Z"
      }
    }
  }
  ```

#### `POST /auth/refresh`
- **Request Body**:
  ```json
  {
    "refreshToken": "eyJ..."
  }
  ```
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "accessToken": "eyJ...",
      "refreshToken": "eyJ..."
    }
  }
  ```

#### `POST /auth/logout`
- **Request Body**:
  ```json
  {
    "refreshToken": "eyJ..."
  }
  ```
- **Response** (204): No content

#### `GET /auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "user": {...},
      "permissions": ["cameras:read", "cameras:write", ...]
    }
  }
  ```

#### `GET /users`
- **Query Params**: `role`, `status`, `search`, `page`, `pageSize`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [...UserAccount],
    "meta": {
      "page": 1,
      "pageSize": 20,
      "total": 50,
      "totalPages": 3
    }
  }
  ```

#### `POST /users`
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "roleId": "ROLE-OPERATOR",
    "password": "optional"
  }
  ```
- **Response** (201): Created user

#### `PUT /users/{id}`, `DELETE /users/{id}`, `PATCH /users/{id}/password`

#### `GET /roles`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "ROLE-ADMIN",
        "name": "Admin",
        "permissions": ["*"],
        "description": "Full system access"
      },
      ...
    ]
  }
  ```

### 2. **Cameras**

#### `GET /cameras`
- **Query Params**: `status`, `streamType`, `enabled`, `search`, `page`, `pageSize`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "CAM-01",
        "name": "Main Entrance",
        "location": "Building A - Lobby",
        "streamType": "RTSP",
        "status": "online",
        "fps": 30,
        "latency": 45.0,
        "bitrate": 6.4,
        "resolution": "1920x1080",
        "lastSeen": "2025-11-05T10:24:00Z",
        "ipAddress": "10.10.1.12",
        "tags": ["primary", "entry"],
        "thumbnail": "https://minio.local/...",
        "streamUrl": "rtsp://10.10.1.12:554/stream",
        "lastChecked": "2025-11-05T10:24:15Z",
        "enabled": true
      },
      ...
    ],
    "meta": {...}
  }
  ```

#### `POST /cameras`
- **Request Body**:
  ```json
  {
    "id": "CAM-07",  // Optional
    "name": "New Camera",
    "location": "Building B",
    "streamType": "RTSP",
    "streamUrl": "rtsp://...",
    "enabled": true
  }
  ```
- **Response** (201): Created camera

#### `GET /cameras/{id}`, `PUT /cameras/{id}`, `DELETE /cameras/{id}`

#### `PATCH /cameras/{id}/state`
- **Request Body**:
  ```json
  {
    "enabled": true
  }
  ```
- **Response** (200): Updated camera

#### `POST /cameras/{id}/test-connection`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "success": true,
      "latencyMs": 42,
      "bitrate": 6.5,
      "message": "Connection OK"
    }
  }
  ```

#### `POST /cameras/{id}/snapshot`
- **Description**: Capture snapshot using FFmpeg
- **Response** (201):
  ```json
  {
    "success": true,
    "data": {
      "assetId": "uuid",
      "url": "https://minio.local/snapshots/cam-01-timestamp.jpg",
      "timestamp": "2025-11-05T10:30:00Z"
    }
  }
  ```

#### `GET /cameras/summary`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "CAM-01",
        "detectionsToday": 124,
        "unknownFaces": 1,
        "uptimePercent": 99.8
      },
      ...
    ]
  }
  ```

#### `POST /cameras/import`, `GET /cameras/export`

### 3. **Live Detections & Provider**

#### `GET /detections/live`
- **Query Params**: `cameraId` (optional), `limit`
- **Performance**: **<200ms** (critical!)
- **Caching**: Redis cache with 3s TTL
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "uuid",
        "personId": "EMP-00412",
        "name": "Sophia Martinez",
        "cameraId": "CAM-01",
        "confidence": 99.2,
        "timestamp": "2025-11-05T10:24:00Z",
        "trackId": "TRACK-123",
        "boundingBox": {
          "top": 100,
          "left": 150,
          "width": 200,
          "height": 250
        },
        "thumbnail": "https://...",
        "status": "authorized"
      },
      ...
    ]
  }
  ```

#### `POST /detections/send-frame`
- **Description**: Queue detection job (Celery)
- **Request Body**:
  ```json
  {
    "cameraId": "CAM-01"
  }
  ```
- **Response** (202):
  ```json
  {
    "success": true,
    "data": {
      "jobId": "uuid",
      "status": "queued"
    }
  }
  ```

#### `POST /detections/test-provider`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "status": "connected",
      "latencyMs": 180,
      "message": "Provider healthy"
    }
  }
  ```

#### `GET /detections/provider/config`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "providerName": "Default Provider",
      "endpoint": "http://localhost:8001/detect",
      "apiKey": "***",
      "enabled": true,
      "status": "connected",
      "lastHeartbeat": "2025-11-05T10:20:00Z",
      "averageLatencyMs": 175
    }
  }
  ```

#### `PUT /detections/provider/config`

#### `GET /detections/events`
- **Query Params**: `status`, `cameraId`, `from`, `to`, `page`, `pageSize`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "uuid",
        "cameraId": "CAM-01",
        "cameraName": "Main Entrance",
        "timestamp": "2025-11-05T10:20:00Z",
        "status": "received",
        "latencyMs": 150,
        "payload": {...}
      },
      ...
    ],
    "meta": {...}
  }
  ```

### 4. **Attendance**

#### `GET /attendance/records`
- **Description**: Current presence status
- **Query Params**: `limit`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "uuid",
        "personId": "EMP-00412",
        "name": "Sophia Martinez",
        "role": "Process Engineer",
        "department": "Manufacturing",
        "status": "on-site",
        "accuracy": 99.2,
        "timestamp": "2025-11-05T10:21:04Z",
        "cameraId": "CAM-03",
        "cameraName": "R&D Corridor",
        "thumbnail": "https://..."
      },
      ...
    ]
  }
  ```

#### `GET /attendance/logs`
- **Query Params**: `search`, `cameraId`, `dateFrom`, `dateTo`, `odooStatus`, `page`, `pageSize`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "ATT-20251105-001",
        "employeeId": "EMP-00412",
        "name": "Sophia Martinez",
        "department": "Manufacturing",
        "date": "2025-11-05",
        "timeIn": "09:00:00",
        "timeOut": "17:30:00",
        "cameraId": "CAM-03",
        "cameraName": "R&D Corridor",
        "accuracy": 99.2,
        "status": "present",
        "odooStatus": "synced",
        "odooSyncTime": "2025-11-05T17:35:00Z"
      },
      ...
    ],
    "meta": {...}
  }
  ```

#### `POST /attendance/manual`
- **Request Body**:
  ```json
  {
    "employeeId": "EMP-00123",
    "cameraId": "CAM-01",
    "timestamp": "2025-11-05T10:00:00Z",
    "status": "present",
    "note": "Manual entry"
  }
  ```
- **Response** (201): Created log

#### `DELETE /attendance/{id}`, `GET /attendance/statistics`, `GET /attendance/overview`, `POST /attendance/export`, `GET /attendance/pending`

### 5. **Odoo Integration**

#### `GET /odoo/config`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "baseUrl": "https://odoo.example.com",
      "database": "production_db",
      "company": "ACME Corp",
      "apiKey": "***",
      "autoSync": false,
      "status": "connected",
      "lastSync": "2025-11-05T10:00:00Z",
      "pendingCount": 5,
      "failureCount": 1
    }
  }
  ```

#### `PUT /odoo/config`, `POST /odoo/test`, `POST /odoo/sync`, `GET /odoo/logs`, `GET /odoo/status`

### 6. **Face Registration**

#### `GET /faces`
- **Query Params**: `department`, `search`, `status`, `page`, `pageSize`

#### `POST /faces`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `name`: string
  - `employeeId`: string
  - `department`: string
  - `images[]`: file[] (max 5 images)
- **Response** (201): Created profile

#### `GET /faces/{id}`, `PUT /faces/{id}`, `DELETE /faces/{id}`, `POST /faces/{id}/images`, `DELETE /faces/{id}/images/{imageId}`, `GET /faces/{id}/images`

### 7. **Alerts & Notifications**

#### `GET /alerts`, `POST /alerts/{id}/acknowledge`, `POST /alerts/{id}/mute`, `DELETE /alerts/{id}`, `GET /notifications`, `POST /notifications/{id}/acknowledge`, `DELETE /notifications`

### 8. **System & Health**

#### `GET /system/summary`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "activeCameras": 24,
      "registeredPeople": 486,
      "peopleDetectedToday": 312,
      "unknownFaceAlerts": 4,
      "manualOverrides": 3,
      "attendanceCompletion": 96.0,
      "lastSync": "2025-11-05T10:24:30Z"
    }
  }
  ```

#### `GET /system/health/metrics`, `GET /system/health/services`, `GET /system/network-metrics`, `POST /system/services/{id}/restart`, `GET /system/uptime`, `GET /system/version`, `GET /shifts`, `GET /services/banner-messages`, `POST /services/banner-messages`

### 9. **Audit & History**

#### `GET /audit`, `GET /history/person/{employeeId}`

### 10. **Developer Console**

#### `GET /developer/endpoints`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "DEV-001",
        "label": "Cameras",
        "description": "List all cameras",
        "method": "GET",
        "path": "/api/v1/cameras"
      },
      ...
    ]
  }
  ```

#### `POST /developer/endpoints/{id}/invoke`
- **Request Body** (optional):
  ```json
  {
    "payload": {...}
  }
  ```
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "status": 200,
      "headers": {...},
      "body": {...}
    }
  }
  ```

### 11. **Settings**

#### `GET /i18n/languages`, `GET /settings/timezones`, `GET /settings/preferences`, `PUT /settings/preferences`

---

## Background Jobs & Celery Tasks

### Celery Configuration

#### `worker/celery_app.py`
```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "face_attendance_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "worker.tasks.detection",
        "worker.tasks.odoo",
        "worker.tasks.export",
        "worker.tasks.monitoring",
        "worker.tasks.cleanup",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
)
```

### Task Definitions

#### 1. **Detection Tasks** (`worker/tasks/detection.py`)

##### `send_frame_for_detection(camera_id: str)`
- **Trigger**: API call `POST /detections/send-frame`
- **Steps**:
  1. Fetch camera config from DB
  2. Capture frame using FFmpeg
  3. POST frame to detection provider API
  4. Parse response
  5. Store detection in DB
  6. Update live detections cache (Redis)
  7. Broadcast via WebSocket
- **Retry**: 3 attempts with exponential backoff
- **Timeout**: 30s

##### `test_detection_provider()`
- **Trigger**: Scheduled (every 5 minutes)
- **Steps**:
  1. Send health check to provider
  2. Measure latency
  3. Update `detection_provider_config` table
  4. Raise alert if degraded/offline

#### 2. **Odoo Sync Tasks** (`worker/tasks/odoo.py`)

##### `sync_attendance_to_odoo(record_ids: List[str] = None)`
- **Trigger**: API call `POST /odoo/sync` OR scheduled (if auto_sync enabled)
- **Steps**:
  1. Fetch pending attendance logs (or specified records)
  2. Batch records (100 per batch)
  3. For each batch:
     - Call Odoo JSON-RPC API
     - Handle timezone conversion
     - Update `odoo_status` and `odoo_sync_time`
     - Log result in `odoo_sync_logs`
  4. Update `odoo_config` counters
  5. Raise alert if failure_count > threshold
- **Retry**: 5 attempts with exponential backoff
- **Timeout**: 120s

##### `scheduled_odoo_sync()`
- **Trigger**: Cron (every 30 minutes if auto_sync=true)
- **Steps**: Call `sync_attendance_to_odoo()` with no args

#### 3. **Export Tasks** (`worker/tasks/export.py`)

##### `generate_export(job_id: str)`
- **Trigger**: API call `POST /attendance/export`
- **Steps**:
  1. Fetch job from DB
  2. Query data based on filters
  3. Generate CSV or PDF
  4. Upload to MinIO
  5. Generate signed URL (7-day expiry)
  6. Update job status to `completed`
- **Formats**:
  - CSV: Use Python `csv` module
  - PDF: Use `reportlab` or `weasyprint`
- **Timeout**: 300s

#### 4. **Monitoring Tasks** (`worker/tasks/monitoring.py`)

##### `collect_system_metrics()`
- **Trigger**: Scheduled (every 60 seconds)
- **Steps**:
  1. Collect CPU, memory, disk, network stats (using `psutil`)
  2. Store in `system_metrics` table
  3. Update Redis cache for fast dashboard queries

##### `check_camera_health()`
- **Trigger**: Scheduled (every 2 minutes)
- **Steps**:
  1. Check `last_seen` for all enabled cameras
  2. If camera offline > 5 minutes, create alert
  3. Update camera status

#### 5. **Cleanup Tasks** (`worker/tasks/cleanup.py`)

##### `cleanup_old_data()`
- **Trigger**: Scheduled (daily at 2 AM)
- **Steps**:
  1. Delete detections > 90 days
  2. Delete audit logs > 365 days
  3. Delete expired export jobs
  4. Delete old system metrics > 30 days

### Celery Beat Schedule

#### `worker/beat_schedule.py`
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "test-detection-provider": {
        "task": "worker.tasks.detection.test_detection_provider",
        "schedule": 300.0,  # Every 5 minutes
    },
    "sync-attendance-odoo": {
        "task": "worker.tasks.odoo.scheduled_odoo_sync",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    "collect-system-metrics": {
        "task": "worker.tasks.monitoring.collect_system_metrics",
        "schedule": 60.0,  # Every minute
    },
    "check-camera-health": {
        "task": "worker.tasks.monitoring.check_camera_health",
        "schedule": 120.0,  # Every 2 minutes
    },
    "cleanup-old-data": {
        "task": "worker.tasks.cleanup.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

---

## WebSocket Channels

### WebSocket Endpoint: `/ws`

### Authentication
- JWT token passed via query param: `/ws?token=<access_token>`
- Validate token on connection

### Connection Manager (`app/ws/manager.py`)

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id].remove(websocket)

    async def broadcast_to_channel(self, channel: str, message: dict):
        # Broadcast to all users subscribed to channel
        for connections in self.active_connections.values():
            for connection in connections:
                if channel in connection.subscriptions:
                    await connection.send_json(message)
```

### Message Protocol

#### Client → Server

##### Subscribe
```json
{
  "action": "subscribe",
  "channel": "detections",
  "cameraId": "CAM-01"  // Optional
}
```

##### Unsubscribe
```json
{
  "action": "unsubscribe",
  "channel": "detections",
  "cameraId": "CAM-01"
}
```

##### Ping/Pong
```json
{
  "type": "ping"
}
```

#### Server → Client

##### Detection Event
```json
{
  "type": "detection",
  "channel": "detections",
  "cameraId": "CAM-01",
  "detection": {
    "id": "uuid",
    "personId": "EMP-00412",
    "name": "Sophia Martinez",
    "confidence": 99.2,
    ...
  }
}
```

##### Camera Status
```json
{
  "type": "camera-status",
  "channel": "camera-status",
  "cameraId": "CAM-01",
  "status": "online",
  "lastSeen": "2025-11-05T10:30:00Z"
}
```

##### Alert
```json
{
  "type": "alert",
  "channel": "alerts",
  "alert": {
    "id": "ALERT-001",
    "title": "Camera Offline",
    "level": "high",
    ...
  }
}
```

##### Notification
```json
{
  "type": "notification",
  "channel": "notifications",
  "notification": {
    "id": "uuid",
    "title": "Odoo Sync Complete",
    ...
  }
}
```

### Channels

1. **`detections`**: Live detection updates (pushed when new detection occurs)
2. **`camera-status`**: Camera online/offline status changes
3. **`alerts`**: New alerts
4. **`notifications`**: New notifications

### Broadcasting from Backend

When a Celery task completes detection:

```python
from app.ws.manager import manager

async def broadcast_detection(detection: Detection):
    await manager.broadcast_to_channel(
        channel="detections",
        message={
            "type": "detection",
            "cameraId": detection.camera_id,
            "detection": detection.dict()
        }
    )
```

---

## File Storage Strategy

### MinIO Setup

#### Docker Compose Config
```yaml
minio:
  image: minio/minio:latest
  ports:
    - "9000:9000"
    - "9001:9001"
  environment:
    MINIO_ROOT_USER: admin
    MINIO_ROOT_PASSWORD: password123
  command: server /data --console-address ":9001"
  volumes:
    - minio_data:/data
```

### Bucket Structure

```
face-attendance-bucket/
├── faces/                          # Face images
│   ├── {profile_id}/
│   │   ├── {image_id}.jpg
│   │   └── ...
├── snapshots/                      # Camera snapshots
│   ├── {camera_id}/
│   │   ├── {timestamp}.jpg
│   │   └── ...
├── exports/                        # Generated exports
│   ├── attendance/
│   │   ├── {job_id}.csv
│   │   └── {job_id}.pdf
│   └── audit/
└── thumbnails/                     # Detection thumbnails
    └── {detection_id}.jpg
```

### Storage Service (`app/services/storage_service.py`)

```python
import boto3
from datetime import timedelta
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        )
        self.bucket = settings.MINIO_BUCKET

    async def upload_file(self, file_path: str, s3_key: str) -> str:
        self.client.upload_file(file_path, self.bucket, s3_key)
        return s3_key

    async def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expiration
        )
        return url

    async def delete_file(self, s3_key: str):
        self.client.delete_object(Bucket=self.bucket, Key=s3_key)
```

### Usage Examples

#### Face Image Upload
```python
from app.services.storage_service import storage_service

async def upload_face_image(profile_id: str, image_file: UploadFile):
    image_id = str(uuid.uuid4())
    s3_key = f"faces/{profile_id}/{image_id}.jpg"

    # Save temp file
    temp_path = f"/tmp/{image_id}.jpg"
    with open(temp_path, "wb") as f:
        f.write(await image_file.read())

    # Upload to MinIO
    await storage_service.upload_file(temp_path, s3_key)

    # Generate signed URL
    url = await storage_service.generate_presigned_url(s3_key, expiration=86400)

    return {"s3_key": s3_key, "url": url}
```

#### Camera Snapshot (FFmpeg → MinIO)
```python
from app.services.ffmpeg_service import capture_snapshot

async def create_camera_snapshot(camera_id: str):
    # Capture frame using FFmpeg
    temp_path = await capture_snapshot(camera_id)

    # Upload to MinIO
    timestamp = datetime.now().isoformat()
    s3_key = f"snapshots/{camera_id}/{timestamp}.jpg"
    await storage_service.upload_file(temp_path, s3_key)

    # Generate URL
    url = await storage_service.generate_presigned_url(s3_key)

    return {"assetId": s3_key, "url": url, "timestamp": timestamp}
```

---

## Security & Authentication

### JWT Token Strategy

#### Access Token
- **Lifetime**: 15 minutes
- **Payload**:
  ```json
  {
    "sub": "user_id",
    "email": "user@example.com",
    "role": "ROLE-ADMIN",
    "permissions": ["*"],
    "exp": 1699200000
  }
  ```

#### Refresh Token
- **Lifetime**: 14 days
- **Storage**: `user_sessions` table (hashed)
- **Rotation**: New refresh token issued on every refresh

### Password Hashing
- **Algorithm**: bcrypt
- **Rounds**: 12

### RBAC Implementation

#### Decorator (`app/core/security.py`)
```python
from functools import wraps
from fastapi import HTTPException, status

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401)

            if "*" not in current_user.permissions and permission not in current_user.permissions:
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

#### Usage
```python
@router.delete("/cameras/{id}")
@require_permission("cameras:delete")
async def delete_camera(id: str, current_user: User = Depends(get_current_user)):
    # Only users with "cameras:delete" permission can access
    ...
```

### Audit Logging

All mutating operations (POST, PUT, PATCH, DELETE) are automatically logged to `audit_logs` table:

```python
async def log_audit(
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str,
    message: str,
    severity: str = "info",
    ip_address: str = None,
    user_agent: str = None
):
    audit_entry = AuditLog(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        message=message,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)
    await db.commit()
```

### Rate Limiting (Redis)

```python
from fastapi import Request
from app.core.redis import redis_client

async def rate_limit(request: Request, max_requests: int = 100, window: int = 60):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window)

    if current > max_requests:
        raise HTTPException(status_code=429, detail="Too many requests")
```

---

## Implementation Phases

### **Phase 1: Foundation** (Week 1)

#### Goals
- Project scaffolding
- Database setup
- Authentication system
- Basic API structure

#### Tasks
1. Create project structure (as per Architecture section)
2. Set up `pyproject.toml` with Poetry
3. Configure PostgreSQL + Redis + MinIO in Docker Compose
4. Implement `app/core/config.py` (Pydantic Settings)
5. Set up SQLAlchemy base models and session management
6. Create Alembic migrations for core tables (users, roles, sessions)
7. Implement JWT authentication:
   - `POST /auth/login`
   - `POST /auth/refresh`
   - `POST /auth/logout`
   - `GET /auth/me`
8. Create RBAC decorator
9. Set up logging (Python `logging` module)
10. Implement health endpoints (`/health/live`, `/health/ready`)
11. Write unit tests for auth module

#### Deliverables
- ✅ FastAPI app running with auth
- ✅ Database migrations
- ✅ Docker Compose environment
- ✅ Authentication flow working
- ✅ Health checks passing

---

### **Phase 2: Camera Management** (Week 2)

#### Goals
- Camera CRUD operations
- FFmpeg integration for snapshots
- MinIO file storage

#### Tasks
1. Create camera models, schemas, repositories
2. Implement camera endpoints:
   - `GET /cameras` (with filtering, pagination)
   - `POST /cameras`
   - `PUT /cameras/{id}`
   - `DELETE /cameras/{id}`
   - `PATCH /cameras/{id}/state`
   - `GET /cameras/{id}`
3. Implement camera connection test (FFmpeg probe)
4. Set up MinIO storage service
5. Implement snapshot capture:
   - `POST /cameras/{id}/snapshot`
   - FFmpeg frame extraction
   - Upload to MinIO
   - Generate signed URL
6. Implement camera import/export (JSON)
7. Set up Celery workers (basic config)
8. Create camera health monitoring task (Celery)
9. Audit logging for camera operations
10. Write tests

#### Deliverables
- ✅ Full camera CRUD
- ✅ Snapshot generation working
- ✅ MinIO integration
- ✅ Celery workers running

---

### **Phase 3: Detection Provider Integration** (Week 3)

#### Goals
- Live detections endpoint (CRITICAL PERFORMANCE)
- Detection provider API integration
- WebSocket for real-time updates

#### Tasks
1. Create detection models (detections, detection_event_logs, detection_provider_config)
2. Implement detection provider HTTP client
3. Create detection endpoints:
   - `GET /detections/live` (**optimize for <200ms**)
   - `POST /detections/send-frame` (queue Celery task)
   - `POST /detections/test-provider`
   - `GET /detections/provider/config`
   - `PUT /detections/provider/config`
   - `GET /detections/events`
4. Implement Celery task: `send_frame_for_detection`
5. Set up Redis caching for live detections (3s TTL)
6. Implement WebSocket endpoint `/ws`
7. Create connection manager
8. Implement detection broadcasting
9. Create scheduled task: `test_detection_provider` (every 5 minutes)
10. Write tests (including load tests for `/detections/live`)

#### Deliverables
- ✅ Detection provider integration
- ✅ Live detections < 200ms response time
- ✅ WebSocket real-time updates
- ✅ Celery detection pipeline

---

### **Phase 4: Attendance & Analytics** (Week 4)

#### Goals
- Attendance logs with filtering
- Statistics aggregation
- Export generation (CSV/PDF)

#### Tasks
1. Create attendance models (attendance_logs, attendance_records)
2. Implement attendance endpoints:
   - `GET /attendance/records`
   - `GET /attendance/logs` (complex filtering)
   - `POST /attendance/manual`
   - `DELETE /attendance/{id}`
   - `GET /attendance/statistics`
   - `GET /attendance/overview`
   - `POST /attendance/export`
   - `GET /attendance/pending`
3. Implement export service:
   - CSV generation
   - PDF generation (using `reportlab`)
   - Upload to MinIO
   - Signed URL generation
4. Create Celery task: `generate_export`
5. Implement statistics aggregation (by hour, day, camera)
6. Dashboard summary endpoint: `GET /system/summary`
7. Write tests

#### Deliverables
- ✅ Attendance logging system
- ✅ Filtering and pagination
- ✅ Export generation (CSV/PDF)
- ✅ Statistics charts data

---

### **Phase 5: Odoo Integration** (Week 5)

#### Goals
- Odoo API client
- Attendance sync workflow
- Background sync jobs

#### Tasks
1. Create Odoo models (odoo_config, odoo_sync_logs)
2. Implement Odoo JSON-RPC client
3. Implement Odoo endpoints:
   - `GET /odoo/config`
   - `PUT /odoo/config`
   - `POST /odoo/test`
   - `POST /odoo/sync`
   - `GET /odoo/logs`
   - `GET /odoo/status`
4. Create Celery task: `sync_attendance_to_odoo`
   - Batch processing
   - Timezone handling
   - Error handling & retry
   - Status updates
5. Create scheduled task: `scheduled_odoo_sync` (every 30 minutes if auto_sync)
6. Implement alert generation for sync failures
7. Encrypt API keys at rest
8. Write tests (including mock Odoo responses)

#### Deliverables
- ✅ Odoo integration working
- ✅ Attendance sync functional
- ✅ Background sync with auto mode
- ✅ Error handling and alerts

---

### **Phase 6: Face Registration & System Features** (Week 6)

#### Goals
- Face profile management
- Multipart file upload
- System health monitoring
- Alerts & notifications

#### Tasks
1. Create face models (face_profiles, face_images)
2. Implement face endpoints:
   - `GET /faces`
   - `POST /faces` (multipart upload)
   - `PUT /faces/{id}`
   - `DELETE /faces/{id}`
   - `POST /faces/{id}/images`
   - `DELETE /faces/{id}/images/{imageId}`
   - `GET /faces/{id}/images`
3. Person history: `GET /history/person/{employeeId}`
4. Create alert/notification models
5. Implement alert endpoints:
   - `GET /alerts`
   - `POST /alerts/{id}/acknowledge`
   - `POST /alerts/{id}/mute`
   - `DELETE /alerts/{id}`
6. Implement notification endpoints:
   - `GET /notifications`
   - `POST /notifications/{id}/acknowledge`
   - `DELETE /notifications`
7. WebSocket channels for alerts/notifications
8. Create system models (system_metrics, system_services, shift_schedules)
9. Implement system endpoints:
   - `GET /system/health/metrics`
   - `GET /system/health/services`
   - `GET /system/network-metrics`
   - `POST /system/services/{id}/restart`
   - `GET /system/uptime`
   - `GET /system/version`
   - `GET /shifts`
10. Celery task: `collect_system_metrics`
11. Write tests

#### Deliverables
- ✅ Face registration with images
- ✅ System health monitoring
- ✅ Alerts & notifications
- ✅ Person history tracking

---

### **Phase 7: Final Features & Polish** (Week 7)

#### Goals
- Settings & preferences
- Developer console
- Audit log
- Banner messages

#### Tasks
1. Implement settings endpoints:
   - `GET /i18n/languages`
   - `GET /settings/timezones`
   - `GET /settings/preferences`
   - `PUT /settings/preferences`
2. Create user preferences model
3. Implement developer console:
   - `GET /developer/endpoints`
   - `POST /developer/endpoints/{id}/invoke`
4. Audit trail: `GET /audit`
5. Banner messages: `GET/POST /services/banner-messages`
6. User management:
   - `GET /users`
   - `POST /users`
   - `PUT /users/{id}`
   - `DELETE /users/{id}`
   - `PATCH /users/{id}/password`
7. Roles: `GET /roles`
8. Create Celery task: `cleanup_old_data`
9. Implement rate limiting middleware
10. Add request ID to all responses
11. Write tests

#### Deliverables
- ✅ All endpoints implemented
- ✅ Settings & preferences working
- ✅ Developer console functional
- ✅ Rate limiting enabled

---

### **Phase 8: Testing, Documentation & Deployment** (Week 8)

#### Goals
- Comprehensive testing
- Performance optimization
- Documentation
- Production deployment

#### Tasks
1. Write integration tests for all endpoints
2. Write E2E tests for critical flows:
   - Login → fetch cameras → send frame → detection appears
   - Attendance log → export → Odoo sync
3. Load testing:
   - `/detections/live` (target: <200ms at 100 req/s)
   - Camera list endpoints
4. Optimize slow queries (add indexes, query optimization)
5. Set up Redis caching strategy
6. Complete OpenAPI documentation
7. Create Postman collection
8. Write deployment guide:
   - Docker Compose production setup
   - Environment variables
   - Database migration steps
   - Backup/restore procedures
9. Set up monitoring (basic metrics)
10. Create seed data script
11. Performance profiling and optimization
12. Security audit (dependency scanning, OWASP checks)
13. Final code review

#### Deliverables
- ✅ Test coverage > 80%
- ✅ Performance targets met
- ✅ Complete documentation
- ✅ Production-ready deployment

---

## Development Environment Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Poetry (Python dependency manager)
- PostgreSQL client (optional, for manual DB access)

### Setup Steps

#### 1. Clone Repository
```bash
git clone <repo-url>
cd backend
```

#### 2. Install Dependencies
```bash
poetry install
poetry shell
```

#### 3. Create `.env` File
```bash
cp .env.example .env
```

`.env` content:
```env
# App
APP_NAME=Face Attendance System
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/face_attendance
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=14

# MinIO (S3)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
MINIO_BUCKET=face-attendance-bucket
MINIO_SECURE=false

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# FFmpeg
FFMPEG_PATH=/usr/bin/ffmpeg

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=120
```

#### 4. Start Infrastructure (Docker Compose)
```bash
docker-compose up -d
```

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: face_attendance
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

#### 5. Run Database Migrations
```bash
alembic upgrade head
```

#### 6. Seed Initial Data
```bash
python scripts/seed_data.py
```

#### 7. Start FastAPI Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 8. Start Celery Worker (separate terminal)
```bash
celery -A worker.celery_app worker --loglevel=info
```

#### 9. Start Celery Beat (separate terminal)
```bash
celery -A worker.celery_app beat --loglevel=info
```

#### 10. Verify Setup
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001 (admin/password123)
- Health check: http://localhost:8000/health/live

---

## Performance Optimization

### 1. **Database Indexing**

All critical queries have indexes (see Database Schema section).

### 2. **Redis Caching**

#### Live Detections Cache
```python
from app.core.redis import redis_client
import json

CACHE_KEY = "detections:live:{camera_id}"
CACHE_TTL = 3  # 3 seconds

async def get_live_detections(camera_id: str = None):
    cache_key = CACHE_KEY.format(camera_id=camera_id or "all")

    # Try cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from DB
    detections = await fetch_from_db(camera_id)

    # Cache result
    await redis_client.setex(
        cache_key,
        CACHE_TTL,
        json.dumps([d.dict() for d in detections])
    )

    return detections
```

#### Camera List Cache
- TTL: 10 seconds
- Invalidate on camera update

#### System Summary Cache
- TTL: 15 seconds
- Aggregated dashboard data

### 3. **Database Connection Pooling**

SQLAlchemy config:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### 4. **Query Optimization**

#### Pagination
```python
query = query.offset((page - 1) * page_size).limit(page_size)
```

#### Eager Loading (avoid N+1)
```python
query = query.options(
    selectinload(Camera.summaries),
    joinedload(AttendanceLog.camera)
)
```

### 5. **Async Operations**

Use `asyncio.gather()` for parallel operations:
```python
cameras, summaries, alerts = await asyncio.gather(
    fetch_cameras(),
    fetch_summaries(),
    fetch_alerts()
)
```

### 6. **Response Compression**

Enable gzip compression in FastAPI:
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## Testing Strategy

### 1. **Unit Tests** (`tests/unit/`)

Test individual functions, services, utilities.

Example:
```python
# tests/unit/test_auth_service.py
import pytest
from app.services.auth_service import hash_password, verify_password

def test_password_hashing():
    password = "test123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False
```

### 2. **Integration Tests** (`tests/integration/`)

Test API endpoints with test database.

Example:
```python
# tests/integration/test_cameras.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_camera(client: AsyncClient, auth_token: str):
    response = await client.post(
        "/api/v1/cameras",
        json={
            "id": "CAM-TEST",
            "name": "Test Camera",
            "location": "Test Location",
            "streamType": "RTSP",
            "streamUrl": "rtsp://test",
            "enabled": true
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Camera"
```

### 3. **E2E Tests** (`tests/e2e/`)

Test complete workflows.

Example:
```python
@pytest.mark.asyncio
async def test_detection_workflow(client: AsyncClient):
    # 1. Login
    login_response = await client.post("/api/v1/auth/login", json={...})
    token = login_response.json()["data"]["accessToken"]

    # 2. Send frame for detection
    detect_response = await client.post(
        "/api/v1/detections/send-frame",
        json={"cameraId": "CAM-01"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert detect_response.status_code == 202

    # 3. Wait for job to complete (poll or wait)
    await asyncio.sleep(2)

    # 4. Check live detections
    detections_response = await client.get(
        "/api/v1/detections/live",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert detections_response.status_code == 200
    assert len(detections_response.json()["data"]) > 0
```

### 4. **Load Tests**

Use `locust` for load testing critical endpoints:

```python
# locustfile.py
from locust import HttpUser, task, between

class FaceAttendanceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test@example.com",
            "password": "test123"
        })
        self.token = response.json()["data"]["accessToken"]

    @task(3)
    def get_live_detections(self):
        self.client.get(
            "/api/v1/detections/live",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def get_cameras(self):
        self.client.get(
            "/api/v1/cameras",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

Run:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Target: `/detections/live` at 100 req/s < 200ms p95

---

## Summary

This comprehensive plan covers:

✅ **Complete frontend analysis** (13 pages, 48 endpoints)
✅ **Optimized tech stack** (FastAPI + PostgreSQL + Redis + Celery + MinIO + FFmpeg + WebSocket)
✅ **Detailed database schema** (22 tables with indexes)
✅ **All 48 API endpoints** with request/response examples
✅ **Background jobs** (detection, Odoo sync, exports, monitoring, cleanup)
✅ **WebSocket real-time updates** (4 channels)
✅ **File storage strategy** (MinIO with signed URLs)
✅ **Security & authentication** (JWT, RBAC, audit logging, rate limiting)
✅ **8-week implementation roadmap** (broken into phases)
✅ **Development environment setup** (Docker Compose)
✅ **Performance optimization** (caching, indexing, query optimization)
✅ **Testing strategy** (unit, integration, E2E, load tests)

### Next Steps

1. **Review this plan** with your team
2. **Set up development environment** (Phase 1, Week 1)
3. **Start implementation** following the phased approach
4. **Iterate and refine** based on real-world testing

This plan ensures your backend will perfectly match your frontend requirements and handle the polling intervals efficiently!
