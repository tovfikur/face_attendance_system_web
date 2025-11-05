# Phase 5: Frontend Web Application & API Integration

## Overview

Phase 5 focuses on building the web frontend dashboard that connects to the complete backend API system built in Phases 1-4. The frontend provides:

- **User Authentication**: Login and session management
- **Attendance Dashboard**: Real-time attendance tracking and reporting
- **Person Management**: Manage employee/visitor profiles with facial data
- **Face Registration**: Enroll and manage face encodings
- **Live Camera View**: Real-time stream from CCTV cameras
- **Reports & Analytics**: Generate and view attendance reports
- **System Administration**: Settings, configuration, system health
- **Real-time Updates**: WebSocket integration for live events

**Tech Stack**:
- React 19 with TypeScript
- Vite (build tool)
- React Router (navigation)
- Tailwind CSS (styling)
- Recharts (data visualization)
- Lucide React (icons)

**Status**: 🔄 In Progress (Phase 5)

## Project Structure

```
frontend/
├── src/
│   ├── pages/              # Page components (already scaffolded)
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── LiveView.tsx
│   │   ├── Attendance.tsx
│   │   ├── FaceRegister.tsx
│   │   ├── Reports.tsx
│   │   ├── Cameras.tsx
│   │   ├── Settings.tsx
│   │   ├── Alerts.tsx
│   │   ├── SystemHealth.tsx
│   │   ├── History.tsx
│   │   ├── AuditLog.tsx
│   │   └── Developer.tsx
│   ├── components/         # Reusable components
│   ├── services/           # API client and WebSocket
│   │   ├── apiClient.ts    # HTTP client for backend
│   │   ├── websocket.ts    # WebSocket for real-time
│   │   └── mockApi.ts      # Current mock (to be replaced)
│   ├── context/            # React context (auth, notifications)
│   ├── types/              # TypeScript type definitions
│   ├── hooks/              # Custom hooks
│   ├── utils/              # Utility functions
│   ├── layouts/            # Layout components
│   ├── router/             # Route configuration
│   └── App.tsx
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Phase 5 Tasks

### 1. API Client Service
**File**: `src/services/apiClient.ts`
**Purpose**: Create HTTP client that connects to backend API

**Implementation**:
- Base URL configuration (environment-based)
- Request/response interceptors
- Token management (JWT)
- Error handling
- Typed API methods for all endpoints

**Methods** (organized by domain):
```typescript
// Authentication
POST /auth/login
POST /auth/logout
POST /auth/refresh
GET /auth/me

// Persons
GET /api/v1/persons
POST /api/v1/persons
GET /api/v1/persons/{id}
PUT /api/v1/persons/{id}
DELETE /api/v1/persons/{id}
POST /api/v1/persons/{id}/enroll
POST /api/v1/persons/search/by-face
GET /api/v1/persons/search
GET /api/v1/persons/summary

// Attendance
POST /api/v1/attendance/check-in
POST /api/v1/attendance/check-out
GET /api/v1/attendance
GET /api/v1/attendance/{person_id}
GET /api/v1/attendance/reports/daily
GET /api/v1/attendance/{person_id}/statistics
GET /api/v1/attendance/status/{person_id}

// Cameras
GET /api/v1/cameras
GET /api/v1/cameras/{id}
PUT /api/v1/cameras/{id}
DELETE /api/v1/cameras/{id}

// Detections
GET /api/v1/detections
GET /api/v1/detections/{id}
WS /api/v1/detections/ws/{client_id}

// Settings & Config
GET /api/v1/settings
PUT /api/v1/settings
```

### 2. Authentication Service
**File**: `src/services/authService.ts`
**Purpose**: Manage user authentication and token storage

**Features**:
- Login with credentials
- Token storage (localStorage or sessionStorage)
- Token refresh mechanism
- Logout
- Protected route wrapper
- Current user context

**Context**: `src/context/AuthContext.tsx`
- Current user state
- Login/logout functions
- Token management
- Redirect to login on unauthorized

### 3. WebSocket Service
**File**: `src/services/websocket.ts`
**Purpose**: Real-time updates from backend

**Endpoints**:
- `/api/v1/detections/ws/{client_id}` - Face detection events
- `/api/v1/attendance/ws/{client_id}` - Attendance events

**Message Types**:
```json
{
  "type": "detection_event",
  "person_id": "...",
  "confidence": 0.95,
  "camera_id": "...",
  "timestamp": "..."
}

{
  "type": "attendance_event",
  "action": "check_in",
  "person_name": "John Doe",
  "confidence": 0.92,
  "timestamp": "..."
}
```

**Features**:
- Auto-reconnection with exponential backoff
- Message subscription system
- Connection status tracking
- Graceful disconnection handling

### 4. Person Management Integration
**File**: `src/pages/PersonManagement.tsx` (new page)
**Purpose**: CRUD operations for persons

**Features**:
- List persons with pagination
- Search by name/email/ID
- Create new person
- Edit person details
- Delete person
- View person's face encodings
- Enroll new faces
- View attendance history

**Connected Components**:
- PersonTable with API data
- PersonForm for create/edit
- FaceEncodingsList with actual encodings
- PersonSearch with real API search

### 5. Attendance Dashboard
**File**: `src/pages/Attendance.tsx` (update existing)
**Purpose**: Real-time attendance tracking and analytics

**Features**:
- Real-time check-in/check-out display
- Today's attendance summary (via WebSocket)
- Currently checked-in persons
- Daily statistics
- Person-level attendance history
- Manual check-in/check-out capability
- Attendance status filtering

**Real-time Updates**:
- Connect to WebSocket on load
- Update attendance list on new events
- Show check-in/check-out notifications
- Update person status in real-time

### 6. Face Registration
**File**: `src/pages/FaceRegister.tsx` (update existing)
**Purpose**: Facial recognition enrollment

**Features**:
- Select person from list
- Capture face from webcam
- Display face detection visualization
- Show face encoding quality
- Enroll face with API
- View enrolled faces
- Set primary face
- Delete face encodings

**Technologies**:
- Canvas API for webcam access
- Face detection from camera
- Base64 encoding for transmission
- Real-time quality feedback

### 7. Live View Integration
**File**: `src/pages/LiveView.tsx` (update existing)
**Purpose**: Real-time camera streams with detection overlay

**Features**:
- Camera stream display (via backend proxy)
- Detection events overlay
- Real-time face detection visualization
- Person identification on stream
- Confidence score display
- Timestamp logging

**Real-time Updates**:
- Connect to detection WebSocket
- Overlay detections on camera feed
- Display person information
- Log all detections

### 8. Real-time WebSocket Integration
**Purpose**: Update UI with live events

**Implementation**:
- Connect in root App component
- Broadcast events via React Context
- Update relevant pages when events arrive
- Show notifications for important events

**Event Types**:
- Detection events → Update LiveView
- Attendance events → Update Attendance page
- System events → Show notifications

### 9. Reports Dashboard
**File**: `src/pages/Reports.tsx` (update existing)
**Purpose**: Attendance analytics and reporting

**Features**:
- Daily attendance summary
- Date range filtering
- Person-level statistics
- Presence percentage graphs
- Late arrival tracking
- Monthly trends
- Export reports (CSV/PDF)
- Custom report builder

**Charts**:
- Attendance over time (LineChart)
- Presence distribution (PieChart)
- Daily summary (BarChart)
- Late arrivals (BarChart)

### 10. Testing & Refinement
**Purpose**: End-to-end testing and bug fixes

**Testing Scenarios**:
- Login flow
- Person CRUD operations
- Face enrollment and search
- Real-time attendance updates
- WebSocket reconnection
- Error handling
- Permission checks
- Session expiration

## Implementation Priority

### Phase 5a - Foundation (Week 1)
1. ✅ Plan API structure
2. Create API client service
3. Implement authentication
4. Create WebSocket service
5. Update Auth context

### Phase 5b - Core Integration (Week 2)
6. Integrate attendance page
7. Integrate person management
8. Implement face registration
9. Connect live view
10. Update real-time features

### Phase 5c - Polish (Week 3)
11. Create reports dashboard
12. Add error handling
13. Implement notifications
14. Add loading states
15. Test all integrations

## Backend API Compatibility

### Authentication
```
POST /auth/login
{
  "username": "user@example.com",
  "password": "password"
}
→ { "access_token": "...", "token_type": "bearer" }
```

### Person API
```
GET /api/v1/persons?page=1&page_size=20
→ {
  "success": true,
  "data": [...],
  "meta": { "page": 1, "pageSize": 20, "total": 100, "totalPages": 5 }
}
```

### Attendance API
```
POST /api/v1/attendance/check-in
{
  "person_id": "person_uuid",
  "confidence_threshold": 0.7
}
→ { "success": true, "data": { "person_id": "...", "check_in_time": "..." } }
```

### WebSocket Format
```
WS /api/v1/attendance/ws/client_id?person_id=all&min_confidence=0.0

Message:
{
  "type": "attendance_event",
  "action": "check_in",
  "person_name": "John Doe",
  "confidence": 0.95,
  "timestamp": "2024-01-15T10:30:45"
}
```

## Environment Configuration

**`.env` file**:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_API_VERSION=v1
```

**Usage in code**:
```typescript
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL
```

## Error Handling

### API Errors
- 401 Unauthorized → Redirect to login
- 403 Forbidden → Show permission error
- 404 Not Found → Show not found message
- 500 Server Error → Show error notification
- Network error → Show retry button

### WebSocket Errors
- Connection refused → Show offline notification
- Connection lost → Auto-reconnect
- Message error → Log and continue

## Performance Optimization

### Code Splitting
- Lazy load pages with React.lazy()
- Dynamic imports for large components
- Chunk vendors separately

### Caching
- Cache API responses with React Query or SWR
- Implement token refresh before expiry
- Cache file uploads

### WebSocket Optimization
- Single WebSocket connection for all events
- Event throttling for high-frequency updates
- Memory leak prevention on unmount

## Security Considerations

### Token Management
- Store JWT in secure storage
- Refresh token before expiry
- Clear token on logout
- Handle token refresh errors

### CORS
- Configure backend CORS properly
- Use credentials in requests if needed

### Input Validation
- Validate all user inputs
- Sanitize outputs
- Use TypeScript for type safety

### API Security
- Always use HTTPS in production
- Validate response data
- Handle sensitive data carefully

## Testing Strategy

### Unit Tests
- API client methods
- Utility functions
- Custom hooks

### Integration Tests
- Page integration with API
- WebSocket integration
- Authentication flow

### E2E Tests
- Login to logout flow
- Create person → Enroll face → Check attendance
- Real-time attendance updates

## Deployment

### Build
```bash
npm run build
# Creates dist/ folder with optimized build
```

### Docker
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm install
COPY src .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment Variables
```
VITE_API_BASE_URL=https://api.example.com
VITE_WS_BASE_URL=wss://api.example.com
```

## Documentation

### User Guide
- How to use attendance dashboard
- Face registration process
- Report generation
- Settings configuration

### Developer Guide
- API client usage
- WebSocket integration
- Adding new pages
- Testing procedures

## Success Criteria

- ✅ All pages connected to real API
- ✅ Real-time WebSocket working
- ✅ Authentication functional
- ✅ All CRUD operations working
- ✅ No console errors
- ✅ Responsive on mobile/tablet
- ✅ WebSocket auto-reconnects on failure
- ✅ Proper error handling throughout
- ✅ Loading states for all async operations
- ✅ 90%+ lighthouse score

## Next Steps (Phase 6)

After Phase 5 completion:
1. Mobile app (React Native)
2. Advanced analytics
3. Hardware integration
4. ODOO ERP sync
5. Performance optimization
