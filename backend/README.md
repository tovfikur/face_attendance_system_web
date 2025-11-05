# CCTV Face Attendance System - Backend API

**FastAPI Backend for Face Recognition Attendance Tracking**

## 🏗️ Project Structure

```
backend/
├── app/                        # Main application
│   ├── api/                    # API routes
│   │   └── v1/                 # API version 1
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── cameras.py      # Camera management
│   │       ├── detections.py   # Detection & provider
│   │       ├── attendance.py   # Attendance logs
│   │       ├── odoo.py         # Odoo integration
│   │       ├── faces.py        # Face registration
│   │       ├── alerts.py       # Alerts & notifications
│   │       ├── system.py       # System health
│   │       ├── audit.py        # Audit trail
│   │       ├── users.py        # User management
│   │       ├── settings.py     # Settings & preferences
│   │       ├── developer.py    # Developer console
│   │       └── history.py      # Person history
│   │
│   ├── core/                   # Core functionality
│   │   ├── config.py           # Configuration
│   │   ├── security.py         # JWT & security
│   │   ├── deps.py             # FastAPI dependencies
│   │   ├── errors.py           # Custom exceptions
│   │   ├── logging.py          # Logging setup
│   │   └── redis.py            # Redis client
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py             # User models
│   │   ├── camera.py           # Camera models
│   │   ├── detection.py        # Detection models
│   │   ├── attendance.py       # Attendance models
│   │   ├── face.py             # Face profile models
│   │   ├── alert.py            # Alert models
│   │   ├── odoo.py             # Odoo models
│   │   ├── audit.py            # Audit models
│   │   ├── system.py           # System models
│   │   └── export.py           # Export job models
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── common.py           # Shared schemas
│   │   ├── user.py             # User schemas
│   │   ├── camera.py           # Camera schemas
│   │   ├── detection.py        # Detection schemas
│   │   ├── attendance.py       # Attendance schemas
│   │   ├── face.py             # Face schemas
│   │   ├── alert.py            # Alert schemas
│   │   ├── odoo.py             # Odoo schemas
│   │   ├── audit.py            # Audit schemas
│   │   ├── system.py           # System schemas
│   │   └── settings.py         # Settings schemas
│   │
│   ├── repositories/           # Data access layer
│   │   ├── base.py             # Base repository
│   │   ├── user.py             # User repository
│   │   ├── camera.py           # Camera repository
│   │   ├── detection.py        # Detection repository
│   │   ├── attendance.py       # Attendance repository
│   │   ├── face.py             # Face repository
│   │   └── odoo.py             # Odoo repository
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py     # Authentication
│   │   ├── camera_service.py   # Camera management
│   │   ├── detection_service.py # Detection logic
│   │   ├── detection_provider.py # Provider client
│   │   ├── attendance_service.py # Attendance logic
│   │   ├── odoo_client.py      # Odoo API client
│   │   ├── face_service.py     # Face registration
│   │   ├── alert_service.py    # Alert management
│   │   ├── export_service.py   # Export generation
│   │   ├── storage_service.py  # MinIO operations
│   │   ├── ffmpeg_service.py   # FFmpeg operations
│   │   └── system_service.py   # System monitoring
│   │
│   ├── ws/                     # WebSocket
│   │   ├── manager.py          # Connection manager
│   │   └── channels.py         # Channel handlers
│   │
│   ├── db/                     # Database
│   │   ├── base.py             # Base model class
│   │   ├── session.py          # DB session
│   │   └── init_db.py          # DB initialization
│   │
│   └── main.py                 # FastAPI app entry
│
├── worker/                     # Celery workers
│   ├── celery_app.py           # Celery configuration
│   ├── beat_schedule.py        # Scheduled tasks
│   └── tasks/                  # Celery tasks
│       ├── detection.py        # Detection tasks
│       ├── odoo.py             # Odoo sync tasks
│       ├── export.py           # Export tasks
│       ├── monitoring.py       # System monitoring
│       └── cleanup.py          # Data cleanup
│
├── migrations/                 # Alembic migrations
│   └── versions/               # Migration scripts
│
├── tests/                      # Tests
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
│
├── docker/                     # Docker files
│   ├── Dockerfile.api          # API container
│   └── Dockerfile.worker       # Worker container
│
├── scripts/                    # Utility scripts
│   ├── init_db.py              # Initialize database
│   ├── seed_data.py            # Seed initial data
│   └── test_connections.py    # Test infrastructure
│
├── .env.example                # Environment template
├── .gitignore                  # Git ignore
├── pyproject.toml              # Poetry dependencies
├── pytest.ini                  # Pytest config
├── docker-compose.yml          # Docker Compose
├── README.md                   # This file
├── TODO.md                     # Task list
└── PROGRESS.md                 # Progress tracking
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Poetry

### 1. Install Dependencies
```bash
cd backend
poetry install
poetry shell
```

### 2. Start Infrastructure
```bash
docker-compose up -d
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run Migrations
```bash
alembic upgrade head
```

### 5. Start API Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start Celery Worker
```bash
# In a new terminal
celery -A worker.celery_app worker --loglevel=info
```

### 7. Start Celery Beat
```bash
# In another terminal
celery -A worker.celery_app beat --loglevel=info
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health/live

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run integration tests only
pytest tests/integration/
```

## 📦 Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Background Jobs**: Celery 5.3+
- **File Storage**: MinIO (S3-compatible)
- **Auth**: JWT (python-jose)
- **Password**: bcrypt (passlib)

## 🔑 Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `MINIO_ENDPOINT`: MinIO endpoint URL
- `ALLOWED_ORIGINS`: CORS origins

## 📖 Development

### Project Status
See `PROGRESS.md` for current implementation status.

### Task List
See `TODO.md` for detailed task breakdown.

### Implementation Plan
See `BACKEND_IMPLEMENTATION_PLAN.md` for complete specifications.

## 🏗️ Current Status

**Phase**: Foundation (Week 1)
**Progress**: 1/15 tasks completed
**Status**: 🟡 In Progress

✅ Project structure created
⏳ Dependencies configuration
⏳ Docker setup
⏳ Database models
⏳ Authentication system

## 🔗 Frontend Integration

The backend is designed to integrate with the React TypeScript frontend at:
`../src`

API base URL: `http://localhost:8000/api/v1`

## 📝 Contributing

1. Follow the implementation phases in TODO.md
2. Update PROGRESS.md after completing tasks
3. Write tests for all new features
4. Update documentation

## 📄 License

[Add your license here]

## 👥 Team

[Add team members here]

---

**Last Updated**: 2025-11-05
**Version**: 0.1.0 (Phase 1 in progress)
