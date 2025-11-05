# Phase 4: Attendance & Person Management Integration Guide

## Overview

Phase 4 completes the CCTV Face Attendance System by integrating the detection system (Phase 3) with automated attendance tracking and person/employee management. This phase provides:

- **Person Management**: Create and manage employee/visitor profiles with facial data
- **Face Recognition**: Extract, store, and match 128-dimensional face encodings
- **Attendance Tracking**: Automatically mark attendance from face detections with confidence scoring
- **Real-time Updates**: WebSocket support for live attendance event streaming
- **Reporting**: Daily and monthly attendance summaries with analytics
- **Background Processing**: Celery tasks for batch operations and scheduled reports

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│  API Endpoints (REST + WebSocket)                       │
│  ├── /api/v1/persons/*              (Person CRUD)       │
│  ├── /api/v1/attendance/*           (Attendance CRUD)    │
│  └── /api/v1/attendance/ws/*        (Real-time events)  │
├─────────────────────────────────────────────────────────┤
│  Service Layer                                          │
│  ├── PersonService                                      │
│  ├── AttendanceService                                  │
│  ├── AutoAttendanceService                              │
│  └── FaceRecognitionService                             │
├─────────────────────────────────────────────────────────┤
│  Repository Layer (Data Access)                         │
│  ├── PersonRepository                                   │
│  ├── PersonFaceEncodingRepository                       │
│  ├── PersonImageRepository                              │
│  └── AttendanceRepository                               │
├─────────────────────────────────────────────────────────┤
│  Database Models                                        │
│  ├── Person                                             │
│  ├── PersonFaceEncoding  (128-D face vectors)          │
│  ├── PersonImage         (Face photos)                  │
│  ├── PersonMetadata      (Extended attributes)          │
│  ├── Attendance          (Check-in/out records)         │
│  ├── AttendanceSession   (Shift definitions)            │
│  ├── AttendanceRule      (Attendance policies)          │
│  └── AttendanceException (Holidays/leaves)              │
└─────────────────────────────────────────────────────────┘
       ↑                                    ↓
   Detection                        Celery Tasks
   (Phase 3)                        (Background Jobs)
   ├── Face Recognition             ├── process_detection
   └── Detection Events             ├── batch_process
                                    ├── generate_reports
                                    └── send_notifications
```

### Data Flow

1. **Detection → Attendance**
   - Camera captures face → Detection service detects face
   - Detection linked to Person → AutoAttendanceService processes
   - If confidence high enough → Auto-mark attendance
   - WebSocket broadcasts event to subscribed clients

2. **Person Enrollment**
   - User submits person record with face photo
   - FaceRecognitionService extracts 128-D encoding
   - PersonImage and PersonFaceEncoding records created
   - Encoding stored in database for future matching

3. **Face Matching**
   - New detection face extracted → 128-D encoding calculated
   - Compare against all enrolled encodings using Euclidean distance
   - Best matches returned with confidence scores
   - Used for person identification and attendance

## Database Models

### Person Models

#### Person
```python
class Person(Base):
    """Employee/visitor profile with facial data."""
    id: str                          # UUID primary key
    first_name: str                  # Employee first name
    last_name: str                   # Employee last name
    email: str (unique)              # Email for communication
    phone: Optional[str]             # Contact phone
    person_type: str                 # "employee" | "visitor" | "contractor"
    id_number: Optional[str]         # Government ID or employee ID
    id_type: Optional[str]           # Type of ID document
    department: Optional[str]        # Department/organization unit
    organization: Optional[str]      # Company/organization name
    status: str                      # "active" | "inactive" | "archived"
    face_encoding_count: int         # Number of enrolled faces
    enrolled_at: Optional[datetime]  # First enrollment timestamp
    last_face_enrolled: Optional[dt] # Last enrollment timestamp

    # Relationships
    face_encodings: List[PersonFaceEncoding]
    images: List[PersonImage]
    metadata: Optional[PersonMetadata]
    attendance_records: List[Attendance]
```

#### PersonFaceEncoding
```python
class PersonFaceEncoding(Base):
    """128-dimensional face vector for recognition."""
    id: str                     # UUID primary key
    person_id: str              # Foreign key to Person
    encoding: bytes             # dlib 128-D face vector (binary format)
    encoding_list: List[float]  # Encoding as list for storage/serialization
    confidence: float           # Quality score (0.0-1.0)
    is_primary: bool            # Primary face for person
    source: str                 # "enrollment" | "detection" | "manual"
    created_at: datetime        # When encoding was created

    # Relationships
    person: Person
```

**Storage Format**: Face encodings stored as binary (128 bytes for float64) for efficiency. Converted to/from numpy arrays for computation using Euclidean distance.

#### PersonImage
```python
class PersonImage(Base):
    """Face photo for person."""
    id: str                     # UUID primary key
    person_id: str              # Foreign key to Person
    image_path: str             # Storage path (MinIO)
    file_size: int              # File size in bytes
    is_primary: bool            # Primary photo for person
    quality_score: float        # Face quality 0.0-1.0
    face_location: Optional[dict]  # Face bounding box
    created_at: datetime

    # Relationships
    person: Person
```

#### PersonMetadata
```python
class PersonMetadata(Base):
    """Extended attributes for person."""
    id: str                     # UUID primary key
    person_id: str              # Foreign key to Person
    address: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    preferences: dict           # JSON - notification prefs, etc
    custom_fields: dict         # JSON - extensible custom data
    created_at: datetime
    updated_at: datetime
```

### Attendance Models

#### Attendance
```python
class Attendance(Base):
    """Check-in/check-out record for person on specific date."""
    id: str                         # UUID primary key
    person_id: str                  # Foreign key to Person
    attendance_date: date           # Date of attendance record

    # Check-in information
    check_in_time: Optional[datetime]
    check_in_confidence: Optional[float]    # Face recognition confidence
    check_in_source: str            # "auto" | "manual" | "detection"
    check_in_detection_id: Optional[str]

    # Check-out information
    check_out_time: Optional[datetime]
    check_out_confidence: Optional[float]
    check_out_source: str           # "auto" | "manual" | "detection"
    check_out_detection_id: Optional[str]

    # Calculated
    duration_minutes: Optional[int] # Total time present (if checked out)
    status: str                     # "present" | "absent" | "late" | "early_leave" | "pending"
    is_manual: bool                 # True if manually entered
    approved_by: Optional[str]      # User ID who approved manual entry
    approval_timestamp: Optional[dt]
    remarks: Optional[str]          # Admin notes

    created_at: datetime
    updated_at: datetime
```

#### AttendanceSession
```python
class AttendanceSession(Base):
    """Shift or session definition."""
    id: str                 # UUID primary key
    name: str               # Shift name "Morning" / "Evening"
    start_time: time        # Session start time HH:MM:SS
    end_time: time          # Session end time HH:MM:SS
    expected_duration_minutes: int
    grace_period_minutes: int  # Allow N minutes late
    is_active: bool
    organization: Optional[str]

    created_at: datetime
    updated_at: datetime
```

#### AttendanceRule
```python
class AttendanceRule(Base):
    """Attendance policy/rules."""
    id: str                      # UUID primary key
    name: str                    # Rule name "Standard Working Hours"
    working_days: List[int]      # [0-6] = Mon-Sun
    start_time: time             # Work start
    end_time: time               # Work end
    min_presence_percentage: float  # Required presence %
    auto_check_in_threshold: float  # Confidence for auto check-in
    manual_review_threshold: float  # Confidence for manual review
    is_active: bool

    created_at: datetime
    updated_at: datetime
```

#### AttendanceException
```python
class AttendanceException(Base):
    """Holiday, leave, or special event."""
    id: str                 # UUID primary key
    person_id: Optional[str]  # NULL = applies to all
    exception_date: date    # Date of exception
    exception_type: str     # "holiday" | "leave" | "special_event"
    reason: str             # Description
    requires_approval: bool
    approved: bool
    created_at: datetime
```

## API Endpoints

### Person Management

#### Create Person
```http
POST /api/v1/persons
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@company.com",
  "phone": "+1234567890",
  "person_type": "employee",
  "id_number": "EMP123456",
  "id_type": "employee_id",
  "department": "Engineering",
  "organization": "ACME Corp",
  "status": "active"
}

Response (201):
{
  "success": true,
  "data": {
    "id": "person_uuid",
    "first_name": "John",
    "last_name": "Doe",
    ...
    "face_encoding_count": 0,
    "enrolled_at": null,
    "createdAt": "2024-01-15T10:30:00",
    "updatedAt": "2024-01-15T10:30:00"
  },
  "meta": {"created": true}
}
```

#### List Persons
```http
GET /api/v1/persons?page=1&page_size=20&status=active&department=Engineering
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": [
    {
      "id": "person_uuid",
      "first_name": "John",
      ...
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

#### Get Person
```http
GET /api/v1/persons/{person_id}
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": {
    "id": "person_uuid",
    "first_name": "John",
    ...
    "face_encoding_count": 3,
    "enrolled_at": "2024-01-10T14:30:00",
    "last_face_enrolled": "2024-01-15T09:45:00"
  }
}
```

#### Update Person
```http
PUT /api/v1/persons/{person_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "department": "Sales",
  "status": "inactive"
}

Response (200):
{
  "success": true,
  "data": { ... updated person ... }
}
```

#### Delete Person
```http
DELETE /api/v1/persons/{person_id}
Authorization: Bearer <token>

Response (204): No Content
```

#### Enroll Face
```http
POST /api/v1/persons/{person_id}/enroll
Authorization: Bearer <token>
Content-Type: application/json

{
  "frame_data": "base64_encoded_image_data",
  "is_primary": false,
  "quality_score": 0.95
}

Response (200):
{
  "success": true,
  "data": {
    "encoding_id": "encoding_uuid",
    "person_id": "person_uuid",
    "confidence": 0.98,
    "total_encodings": 4,
    "is_primary": false,
    "quality_score": 0.95,
    "message": "Face enrolled successfully"
  }
}
```

#### Search by Face
```http
POST /api/v1/persons/search/by-face
Authorization: Bearer <token>
Content-Type: application/json

{
  "frame_data": "base64_encoded_image_data",
  "confidence_threshold": 0.6
}

Response (200):
{
  "success": true,
  "data": {
    "matched": true,
    "best_match": {
      "person_id": "person_uuid",
      "first_name": "John",
      "last_name": "Doe",
      "confidence": 0.92
    },
    "all_matches": [
      {
        "person_id": "person_uuid",
        "first_name": "John",
        "last_name": "Doe",
        "confidence": 0.92
      },
      ...
    ]
  }
}
```

#### Search Persons
```http
GET /api/v1/persons/search?q=john&page=1&page_size=20
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": [ ... persons matching "john" ... ],
  "meta": { ... pagination ... }
}
```

#### Get Person Summary
```http
GET /api/v1/persons/summary
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": {
    "total_persons": 150,
    "active_persons": 145,
    "persons_with_faces": 120,
    "by_type": {
      "employee": 100,
      "visitor": 40,
      "contractor": 10
    }
  }
}
```

### Attendance Management

#### Check-in
```http
POST /api/v1/attendance/check-in
Authorization: Bearer <token>
Content-Type: application/json

{
  "person_id": "person_uuid",
  "confidence_threshold": 0.7
}

Response (200):
{
  "success": true,
  "data": {
    "success": true,
    "person_id": "person_uuid",
    "person_name": "John Doe",
    "check_in_time": "2024-01-15T09:30:45",
    "confidence": 0.95,
    "message": "Check-in successful"
  }
}
```

#### Check-out
```http
POST /api/v1/attendance/check-out
Authorization: Bearer <token>
Content-Type: application/json

{
  "person_id": "person_uuid"
}

Response (200):
{
  "success": true,
  "data": {
    "success": true,
    "person_id": "person_uuid",
    "person_name": "John Doe",
    "check_out_time": "2024-01-15T17:45:30",
    "duration_minutes": 495,
    "message": "Check-out successful"
  }
}
```

#### Get Attendance Records
```http
GET /api/v1/attendance?page=1&person_id=person_uuid&from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": [
    {
      "id": "attendance_uuid",
      "person_id": "person_uuid",
      "attendance_date": "2024-01-15",
      "check_in_time": "2024-01-15T09:30:45",
      "check_in_confidence": 0.95,
      "check_in_source": "auto",
      "check_out_time": "2024-01-15T17:45:30",
      "check_out_confidence": 0.92,
      "check_out_source": "auto",
      "duration_minutes": 495,
      "status": "present",
      "is_manual": false,
      "createdAt": "2024-01-15T09:30:45"
    }
  ],
  "meta": { ... pagination ... }
}
```

#### Get Person Attendance
```http
GET /api/v1/attendance/{person_id}?page=1&from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": [ ... attendance records for person ... ],
  "meta": { ... pagination ... }
}
```

#### Get Daily Report
```http
GET /api/v1/attendance/reports/daily?date=2024-01-15
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": {
    "total_persons": 150,
    "present": 145,
    "absent": 5,
    "late": 8,
    "presence_percentage": 96.7
  }
}
```

#### Get Person Statistics
```http
GET /api/v1/attendance/{person_id}/statistics?from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": {
    "total_working_days": 22,
    "days_present": 20,
    "days_absent": 2,
    "days_late": 3,
    "days_early_leave": 1,
    "presence_percentage": 90.9
  }
}
```

#### Get Current Status
```http
GET /api/v1/attendance/status/{person_id}
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": {
    "person_id": "person_uuid",
    "person_name": "John Doe",
    "checked_in": true,
    "check_in_time": "2024-01-15T09:30:45",
    "current_duration_minutes": 435
  }
}
```

## WebSocket Real-time Updates

### Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/attendance/ws/client123?person_id=person_uuid&min_confidence=0.7');

ws.onopen = () => {
  console.log('Connected to attendance stream');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from attendance stream');
};
```

### Message Types

#### Connection Established
```json
{
  "type": "connection_established",
  "client_id": "client123",
  "timestamp": "2024-01-15T10:30:45.123456",
  "subscribed_to": "person_uuid",
  "min_confidence": 0.7
}
```

#### Initial Status
```json
{
  "type": "initial_status",
  "person_id": "person_uuid",
  "checked_in": true,
  "check_in_time": "2024-01-15T09:30:45",
  "current_duration_minutes": 435
}
```

#### Attendance Event
```json
{
  "type": "attendance_event",
  "event_timestamp": "2024-01-15T10:30:45.123456",
  "person_id": "person_uuid",
  "person_name": "John Doe",
  "action": "check_in",
  "timestamp": "2024-01-15T10:30:45.123456",
  "confidence": 0.95,
  "attendance_id": "attendance_uuid",
  "check_in_time": "2024-01-15T10:30:45.123456",
  "duration_minutes": null
}
```

#### Person Status Update
```json
{
  "type": "person_status_update",
  "event_timestamp": "2024-01-15T17:45:30.123456",
  "person_id": "person_uuid",
  "person_name": "John Doe",
  "checked_in": false,
  "check_in_time": "2024-01-15T09:30:45",
  "current_duration_minutes": 495
}
```

#### Keep-alive Ping
```json
{
  "type": "ping",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Subscribe/Unsubscribe

Subscribe to different person:
```javascript
ws.send(JSON.stringify({
  "type": "subscribe",
  "person_id": "different_person_uuid",
  "min_confidence": 0.6
}));
```

Unsubscribe (disconnect):
```javascript
ws.send(JSON.stringify({
  "type": "unsubscribe"
}));
```

## Face Recognition

### Face Encoding Format

**128-Dimensional Vector**: Face encodings are stored as 128-dimensional floating-point vectors extracted using dlib's deep learning face recognition model.

- **Storage**: Binary format (128 float64 = 1024 bytes per encoding)
- **Matching**: Euclidean distance between vectors
- **Tolerance**: Default 0.6 (distance between 0 and 1)

### Confidence Scoring

```
Confidence = max(0.0, 1.0 - distance)

Distance Ranges:
- Excellent: < 0.4 (confidence > 0.6)
- Good:      < 0.5 (confidence > 0.5)
- Acceptable: < 0.6 (confidence > 0.4)
```

### Thresholds

In `AutoAttendanceService`:

```python
# Auto-mark attendance threshold (70%+ confidence)
MIN_CONFIDENCE_FOR_AUTO_CHECK_IN = 0.7

# Manual review threshold (60-70% confidence)
MIN_CONFIDENCE_FOR_REVIEW = 0.6

# Duplicate prevention window
DUPLICATE_CHECK_WINDOW = 5  # minutes
```

### Auto-Attendance Logic

**Time-based Check-in/Check-out Decision**:

```
Morning (before 12:00)  → Auto-check-in if confidence >= 0.7
Afternoon (12:00-16:00) → Manual review required
Evening (after 16:00)   → Auto-check-out if confidence >= 0.7
```

This heuristic avoids ambiguity about whether mid-day detections are arrivals or departures.

## Celery Tasks

### Available Tasks

#### process_detection_for_attendance
```python
from worker.tasks.attendance import process_detection_for_attendance

# Single detection processing
result = process_detection_for_attendance.delay(detection_id="detection_uuid")
result.get()  # Wait for result
```

**Max Retries**: 2 with exponential backoff (30s * 2^retry)

#### batch_process_recent_detections
```python
# Process last 5 minutes of detections
result = batch_process_recent_detections.delay(minutes=5)
result.get()
```

**Returns**:
```json
{
  "success": true,
  "detections_processed": 10,
  "summary": {
    "total_processed": 10,
    "auto_marked": 8,
    "requires_review": 2,
    "failed": 0
  }
}
```

#### generate_daily_attendance_report
```python
# Generate report for specific date
result = generate_daily_attendance_report.delay(date_str="2024-01-15")
result.get()

# Generate for today
result = generate_daily_attendance_report.delay()
result.get()
```

#### generate_monthly_report
```python
result = generate_monthly_report.delay(year=2024, month=1)
result.get()
```

#### send_attendance_notifications
```python
# Send for specific person
result = send_attendance_notifications.delay(person_id="person_uuid")

# Send for all persons
result = send_attendance_notifications.delay()
```

#### cleanup_old_attendance
```python
# Delete records older than 90 days
result = cleanup_old_attendance.delay(days=90)
```

## Configuration

### Environment Variables

```bash
# Face Recognition
FACE_RECOGNITION_MODEL=hog  # or "cnn" for higher accuracy
FACE_RECOGNITION_ENABLED=true

# Attendance Settings
AUTO_ATTENDANCE_ENABLED=true
AUTO_CHECK_IN_THRESHOLD=0.7
AUTO_CHECKOUT_THRESHOLD=0.7
DUPLICATE_CHECK_WINDOW=5  # minutes

# Celery Task Scheduling (in celery_config.py)
CELERY_BEAT_SCHEDULE = {
    'batch_process_detections': {
        'task': 'worker.tasks.attendance.batch_process_recent_detections',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'generate_daily_report': {
        'task': 'worker.tasks.attendance.generate_daily_attendance_report',
        'schedule': crontab(hour=23, minute=30),  # 11:30 PM daily
    },
    'cleanup_old_records': {
        'task': 'worker.tasks.attendance.cleanup_old_attendance',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

## Integration with Phase 3

### Detection → Attendance Flow

1. **Detection Created** (Phase 3)
   ```python
   # In detection service
   detection = await detection_repo.create(...)

   # Trigger attendance processing
   if detection.person_id:
       process_detection_for_attendance.delay(detection.id)
   ```

2. **Celery Task Processes**
   ```python
   # worker/tasks/attendance.py
   async def _async_process_detection(detection_id):
       detection = await detection_repo.get_by_id(detection_id)
       result = await auto_attendance.process_detection_for_attendance(detection)
       return result
   ```

3. **Auto-Attendance Logic**
   ```python
   # app/services/auto_attendance.py
   if detection.confidence >= 0.7:
       if hour < 12:
           result = await attendance_service.check_in(
               person_id=detection.person_id,
               check_in_time=detection.created_at,
               detection_id=detection.id,
               confidence=detection.confidence
           )
   ```

4. **WebSocket Broadcast**
   ```python
   # When check-in succeeds
   await broadcast_check_in_event(
       person_id=person_id,
       person_name=person_name,
       timestamp=check_in_time,
       confidence=confidence,
       attendance_id=attendance_id
   )
   ```

5. **Real-time Update**
   ```javascript
   // Client receives
   {
     "type": "attendance_event",
     "action": "check_in",
     "person_name": "John Doe",
     "confidence": 0.95
   }
   ```

## Security Considerations

### Permission Model

All endpoints require authentication and permission checks:

```python
if not current_user.has_permission("persons:read"):
    raise HTTPException(status_code=403, detail="Forbidden")
```

**Person Permissions**:
- `persons:read` - View person profiles and search
- `persons:write` - Create, update, delete persons and enroll faces

**Attendance Permissions**:
- `attendance:read` - View attendance records and reports
- `attendance:write` - Record check-in/check-out

### Data Protection

- Face encodings stored as binary (not human-readable)
- Original face images stored securely in MinIO
- Attendance records include audit trail (created_at, updated_at, approved_by)
- Manual entries require approval before finalization

### Duplicate Prevention

Built-in duplicate check prevents:
```python
# Check if already checked in today (within 5-minute window)
existing = await attendance_repo.get_by_person_and_date(
    person_id, attendance_date
)
if existing and existing.check_in_time:
    # Already checked in
    return {"success": False, "error": "Already checked in"}
```

## Performance Optimization

### Indexing

Database indexes on frequently queried fields:

```python
# Person model
Index("idx_person_email", "email")
Index("idx_person_status", "status")
Index("idx_person_type", "person_type")
Index("idx_person_department", "department")

# Attendance model
Index("idx_attendance_person_date", "person_id", "attendance_date")
Index("idx_attendance_date_range", "attendance_date")

# Face encoding model
Index("idx_encoding_person_active", "person_id", "is_primary")
```

### Caching Strategies

```python
# Cache person summaries (30 minute TTL)
cache_key = f"person:summary"
cached = await redis.get(cache_key)

# Cache recent attendance (5 minute TTL)
cache_key = f"person:attendance:{person_id}"
cached = await redis.get(cache_key)
```

### Batch Operations

Process multiple detections efficiently:

```python
# Batch process instead of one-by-one
results = await auto_attendance.process_batch_detections(detections)
# Broadcasts aggregated summary
```

## Troubleshooting

### Face Recognition Not Working

**Issue**: `face_recognition library not available`

**Solution**: Install with `pip install face_recognition dlib`

### Duplicate Attendance Records

**Issue**: Same person checked in multiple times within seconds

**Solution**: Duplicate check window is 5 minutes. Detections within window return error.

### Low Confidence Matches

**Issue**: Person not being recognized (confidence < 0.6)

**Solutions**:
1. Enroll additional face photos for person
2. Check lighting/camera angle matches training photos
3. Lower confidence threshold (not recommended)

### WebSocket Connection Drops

**Issue**: Real-time updates stop

**Solution**: Client-side should handle reconnection with exponential backoff

## Next Steps

1. **Frontend Integration**: Build UI for attendance dashboard and real-time updates
2. **Mobile App**: Create mobile check-in application with face capture
3. **Notifications**: Implement email/SMS notifications for late arrivals
4. **Analytics**: Dashboard with attendance trends and person insights
5. **ODOO Integration**: Sync attendance with ERP system
6. **Biometric Hardware**: Integrate with physical access control systems

## References

- **Face Recognition**: https://github.com/ageitgey/face_recognition
- **dlib Documentation**: http://dlib.net/python/index.html
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Celery**: https://docs.celeryproject.io/
