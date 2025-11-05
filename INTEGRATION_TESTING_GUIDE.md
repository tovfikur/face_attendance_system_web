# Integration Testing Guide

## Overview

This guide provides comprehensive testing procedures for the Face Attendance System, covering both frontend and backend integration.

## Prerequisites

1. Backend API running (Phases 1-4)
2. PostgreSQL database running
3. Redis instance running
4. MinIO storage running
5. Frontend development server running
6. Network connectivity between all services

## Environment Setup

### Backend Services

```bash
# Terminal 1: Start PostgreSQL
# (Usually started automatically on your system)

# Terminal 2: Start Redis
redis-server

# Terminal 3: Start MinIO
minio server ./data

# Terminal 4: Start FastAPI Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 5: Start Celery Worker
cd backend
celery -A worker.celery_app worker --loglevel=info

# Terminal 6: Start Celery Beat (Scheduler)
cd backend
celery -A worker.celery_app beat --loglevel=info
```

### Frontend Development

```bash
# Terminal 7: Start Frontend Dev Server
cd frontend
npm run dev
# Runs on http://localhost:5173
```

## Test Environment Configuration

### Frontend .env Setup

Create `.env.local` in the frontend root:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_API_VERSION=v1
VITE_ENABLE_WEBSOCKET=true
VITE_DEBUG=true
```

### Backend Health Check

Test backend is running:

```bash
curl http://localhost:8000/api/v1/health
# Should return 200 OK
```

## Test Scenarios

### 1. Authentication Flow

**Objective**: Verify login/logout and token management

#### Steps:
1. Open http://localhost:5173/login
2. Enter test credentials:
   - Username: `testuser`
   - Password: `testpass123`
3. Click "Login"
4. **Expected**: Redirected to dashboard, success notification shown

#### Verification:
- Token stored in localStorage
- User can access protected routes
- Navigation to /login redirects to /

#### Cleanup:
- Click logout in settings
- Verify redirected to login
- Token cleared from localStorage

### 2. Person Management CRUD

**Objective**: Test person profile creation, update, deletion

#### Create Person:
1. Navigate to "Person Management"
2. Click "Add Person"
3. Fill form:
   - First Name: `John`
   - Last Name: `Doe`
   - Email: `john.doe@test.com`
   - Type: `Employee`
   - Department: `Engineering`
4. Click "Save"
5. **Expected**: Success notification, person appears in list

#### Update Person:
1. Find John Doe in list
2. Click "Edit"
3. Change Department to `Sales`
4. Click "Save"
5. **Expected**: Success notification, list updated

#### Delete Person:
1. Find John Doe in list
2. Click "Delete"
3. Confirm deletion
4. **Expected**: Success notification, person removed from list

#### Search:
1. Use search box to find by name: `john`
2. **Expected**: Filter shows matching persons
3. Clear search: **Expected**: Shows all persons

#### Filter:
1. Change "Status" filter to "Active"
2. **Expected**: Shows only active persons
3. Change "Type" filter to "Employee"
4. **Expected**: Further filtered results

### 3. Face Registration

**Objective**: Test face enrollment workflow

#### Webcam Access:
1. Navigate to "Face Registration"
2. Click "Start Camera"
3. **Expected**: Browser permission prompt appears
4. Allow camera access
5. **Expected**: Video feed displays

#### Capture Face:
1. Position face in front of camera
2. Click "Capture Frame"
3. **Expected**: Frame thumbnail appears below
4. Click "Capture Frame" again 3-4 times
5. **Expected**: Multiple thumbnails visible

#### Enroll Face:
1. Select person from left panel
2. Click on a captured frame thumbnail (turns blue)
3. Adjust quality score slider: Set to 0.9
4. Check "Set as primary face"
5. Click "Enroll Face"
6. **Expected**: Success notification, face appears in enrolled list

#### Face Search:
1. Capture a new frame of the same person
2. Click "Search by Face"
3. **Expected**: Person found with confidence score
4. Person auto-selected
5. **Expected**: Can re-enroll same person

#### Multiple Faces:
1. Select same person again
2. Capture different angle
3. Enroll face
4. **Expected**: Person now shows 2 faces
5. Verify primary face has star icon

### 4. Attendance Tracking

**Objective**: Test real-time attendance and manual operations

#### View Dashboard:
1. Navigate to "Attendance"
2. **Expected**: Daily summary cards visible
   - Total Persons
   - Present count
   - Absent count
   - Late count
   - Presence percentage

#### Manual Check-in:
1. Find unchecked-in person in list
2. Click "Check In" button
3. **Expected**: Success notification
4. Button changes to "Check Out"
5. Person appears in current statuses

#### Manual Check-out:
1. Click "Check Out" button
2. **Expected**: Success notification
3. Duration calculated and displayed
4. Button removed

#### Real-time Updates via WebSocket:
1. Open browser DevTools → Console
2. Check for WebSocket connection message
3. **Expected**: "Connected to real-time attendance" notification
4. Trigger check-in from another browser/system
5. **Expected**: Dashboard updates automatically within 1 second

#### Person History:
1. Click on person name in table
2. **Expected**: History panel appears below
3. Shows recent attendance records
4. Click close (×) to hide

#### Filtering:
1. Change Status filter: "Present", "Absent", "Late"
2. **Expected**: Table filters accordingly

### 5. Reports & Analytics

**Objective**: Test reporting and analytics

#### View Daily Report:
1. Navigate to "Reports"
2. Select today's date
3. **Expected**: Daily summary displays
   - Charts show distribution
   - Statistics updated
   - Numbers match attendance page

#### Date Range Analysis:
1. Change "From Date" to 30 days ago
2. **Expected**: Person stats update
3. View "Top Performers" section
4. View "Persons with Issues" section

#### Charts:
1. **Pie Chart**: Shows presence distribution
2. **Bar Chart**: (if implemented) Shows daily trends
3. **Expected**: Interactive on hover
4. Tooltips show values

#### Export:
1. Click "CSV" button
2. **Expected**: Notification "Feature coming soon" (ready for future)
3. Click "PDF" button
4. **Expected**: Same notification

#### Statistics:
1. Verify "Total Working Days" shown
2. Verify "Average Presence" calculated
3. Verify "Total Absences" counted
4. **Expected**: Numbers match source data

### 6. Error Handling

**Objective**: Verify error handling and user feedback

#### Network Errors:
1. Stop backend server
2. Try any API operation
3. **Expected**: Error notification shown
4. Error message user-friendly
5. No console errors (only warnings)

#### Validation Errors:
1. Try to create person with blank email
2. **Expected**: Red border on input
3. Error message: "Email is required"
4. Cannot submit form

#### Authentication Errors:
1. Login with invalid credentials
2. **Expected**: Error notification
3. Not redirected to dashboard
4. Token not stored

#### Permission Errors:
1. Backend: Restrict user permissions
2. Try CRUD operation
3. **Expected**: 403 Forbidden error
4. User-friendly message displayed

### 7. WebSocket Testing

**Objective**: Verify real-time updates

#### Connection:
1. Open DevTools → Network → WS
2. Check WebSocket connection open
3. **Expected**: Connected to /api/v1/attendance/ws/...
4. Status: Connected

#### Message Format:
1. Open DevTools → Console
2. Add logging to websocket.ts
3. Trigger attendance event
4. **Expected**: Message received in console
5. **Expected**: Message format matches spec

#### Reconnection:
1. Close WebSocket in DevTools
2. **Expected**: Auto-reconnect attempts
3. **Expected**: Reconnection successful within 30 seconds

#### Message Handling:
1. Enroll new face for person
2. Check-in with that person
3. **Expected**: Dashboard updates immediately
4. Notification appears
5. No page refresh needed

### 8. Performance Testing

**Objective**: Verify performance is acceptable

#### Load Time:
1. Clear browser cache
2. Open application
3. **Expected**: Initial load < 3 seconds
4. Dashboard interactive < 2 seconds

#### API Response Time:
1. Open DevTools → Network
2. Perform various API calls
3. **Expected**: Most < 500ms
4. Check-in/out < 1s

#### WebSocket Latency:
1. Trigger check-in event
2. Measure time to update UI
3. **Expected**: Update < 100ms after event

#### Memory Usage:
1. Keep app open 5 minutes
2. Check memory in DevTools
3. **Expected**: Stable memory usage
4. No memory leaks

### 9. Responsive Design

**Objective**: Test on different screen sizes

#### Desktop (1920x1080):
1. All content visible
2. Tables show all columns
3. No horizontal scroll
4. Layout intact

#### Tablet (768x1024):
1. Open DevTools → Device Toolbar
2. Test iPad view
3. **Expected**: Responsive layout
4. Touch interactions work

#### Mobile (375x667):
1. Test iPhone view
2. **Expected**: Single column layout
3. Menus collapse
4. Buttons accessible

#### Orientations:
1. Rotate device
2. **Expected**: Layout adapts
3. No broken elements

### 10. Accessibility

**Objective**: Verify accessibility standards

#### Keyboard Navigation:
1. Disable mouse
2. Use Tab to navigate
3. **Expected**: All buttons reachable
4. Focus visible on all inputs
5. Enter submits forms

#### Screen Reader:
1. Enable browser screen reader
2. Navigate page
3. **Expected**: All text readable
4. Images have alt text
5. Form labels associated

#### Color Contrast:
1. Use DevTools accessibility inspector
2. Check color contrast ratios
3. **Expected**: WCAG AA compliant (4.5:1 for text)

## Test Data Setup

### Create Test Persons

Use the Person Management page:

1. John Doe - Employee, Engineering
2. Jane Smith - Employee, Sales
3. Bob Johnson - Visitor
4. Alice Brown - Contractor, Finance

### Enroll Test Faces

Use Face Registration page:

1. Enroll 2 faces for John Doe
2. Enroll 1 face for Jane Smith
3. Enroll 3 faces for Bob Johnson

### Create Test Attendance Records

Use Attendance page or API:

```bash
# Check in John Doe
curl -X POST http://localhost:8000/api/v1/attendance/check-in \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"person_id": "john_doe_id", "confidence_threshold": 0.7}'

# Check out John Doe
curl -X POST http://localhost:8000/api/v1/attendance/check-out \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"person_id": "john_doe_id"}'
```

## Automated Testing (Future)

```bash
# Install testing dependencies
npm install --save-dev vitest @testing-library/react jsdom

# Run tests
npm run test

# Coverage
npm run test:coverage
```

## Test Report Template

```
Test Date: ___________
Tester: ___________
Backend Version: ___________
Frontend Version: ___________

Passed Tests: ___/____
Failed Tests: ___/____
Skipped Tests: ___/____

Issues Found:
1. [Issue Description]
2. [Issue Description]

Recommendations:
1. [Recommendation]
2. [Recommendation]

Overall Status: [ ] PASS [ ] FAIL
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Failed
- **Cause**: Backend not running or wrong URL
- **Solution**:
  1. Check backend is running: `curl http://localhost:8000/api/v1/health`
  2. Check .env VITE_WS_BASE_URL
  3. Restart frontend dev server

#### API 401 Unauthorized
- **Cause**: Token invalid or expired
- **Solution**:
  1. Log out
  2. Clear localStorage
  3. Log in again

#### Camera Permission Denied
- **Cause**: Browser permissions not granted
- **Solution**:
  1. Check browser camera permissions
  2. Clear site data for localhost
  3. Reload page and allow camera

#### Blank Page After Login
- **Cause**: Missing components or import error
- **Solution**:
  1. Check DevTools console for errors
  2. Verify all imports are correct
  3. Check file existence

## Success Criteria

- ✅ All 10 test scenarios pass
- ✅ No unhandled exceptions
- ✅ Error messages user-friendly
- ✅ Response times acceptable
- ✅ WebSocket auto-reconnects
- ✅ Data persists correctly
- ✅ Responsive on all sizes
- ✅ Accessible via keyboard
- ✅ No memory leaks
- ✅ Network requests optimized

## Sign-off

```
Testing Date: ___________
Tested By: ___________
Approved By: ___________

All tests passed: [ ] YES [ ] NO

Issues to fix before production:
[ ] None
[ ] See attached list

Ready for production: [ ] YES [ ] NO
```

---

**Next Steps**: After successful integration testing, proceed with:
1. Security audit
2. Performance optimization
3. Load testing
4. Production deployment
