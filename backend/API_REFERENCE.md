# API Reference - Phase 1 Complete

**Status**: ✅ Phase 1 Complete (15/15 tasks)
**Last Updated**: 2025-11-05
**Version**: 1.0

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Testing](#testing)
5. [Error Handling](#error-handling)
6. [Frontend Integration](#frontend-integration)

---

## Getting Started

### Base URL

```
http://localhost:8000/api/v1
```

### Response Format

All responses follow this envelope format:

**Success Response**:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PASSWORD",
    "message": "Invalid email or password",
    "details": {}
  },
  "requestId": "req_123456"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (Delete Success) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden (Permission Denied) |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

---

## Authentication

All protected endpoints require the `Authorization` header with a Bearer token:

```
Authorization: Bearer <accessToken>
```

### Authentication Flow

1. **Login** → Get access and refresh tokens
2. **Use Access Token** → For API requests (15 min expiration)
3. **Token Expires** → Use refresh token to get new tokens (14 days expiration)
4. **Logout** → Revoke refresh token (optional)

---

## Endpoints

### Health Check Endpoints

#### GET /health/live
Check if API is running.

**Response**:
```json
{
  "status": "alive",
  "timestamp": "2025-11-05T10:30:00.000Z",
  "version": "1.0.0"
}
```

#### GET /health/ready
Check if API is ready to serve requests.

**Response**:
```json
{
  "status": "ready",
  "timestamp": "2025-11-05T10:30:00.000Z",
  "version": "1.0.0"
}
```

---

### Authentication Endpoints

#### POST /auth/login
User login with email and password.

**Request**:
```json
{
  "username": "admin@example.com",
  "password": "admin123"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Admin User",
      "email": "admin@example.com",
      "roleId": "ROLE-ADMIN",
      "status": "active",
      "lastActive": "2025-11-05T10:30:00.000Z",
      "createdAt": "2025-11-05T09:00:00.000Z",
      "updatedAt": "2025-11-05T10:30:00.000Z"
    }
  }
}
```

**Errors**:
- `401`: Invalid email or password
- `422`: Missing or invalid fields

---

#### POST /auth/refresh
Refresh access token using refresh token.

**Request**:
```json
{
  "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Errors**:
- `401`: Invalid or expired refresh token

---

#### GET /auth/me
Get current user information.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Admin User",
      "email": "admin@example.com",
      "roleId": "ROLE-ADMIN",
      "status": "active",
      "lastActive": null,
      "createdAt": "2025-11-05T09:00:00.000Z",
      "updatedAt": "2025-11-05T10:30:00.000Z"
    },
    "permissions": ["*"]
  }
}
```

**Errors**:
- `401`: Missing or invalid token

---

#### PATCH /auth/password
Change password.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Request**:
```json
{
  "currentPassword": "admin123",
  "newPassword": "newpassword123",
  "confirmPassword": "newpassword123"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "message": "Password changed successfully"
  }
}
```

**Errors**:
- `401`: Invalid current password
- `422`: Password too short (min 8 chars)

---

#### POST /auth/logout
Logout and revoke refresh token.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Request**:
```json
{
  "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (204)**:
No content on success

**Errors**:
- `401`: Invalid token

---

### Roles Endpoints

#### GET /roles
Get all available roles.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Query Parameters**:
None

**Response (200)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "ROLE-ADMIN",
      "name": "Admin",
      "permissions": ["*"],
      "description": "Full system access",
      "createdAt": "2025-11-05T09:00:00.000Z",
      "updatedAt": "2025-11-05T09:00:00.000Z"
    },
    {
      "id": "ROLE-OPERATOR",
      "name": "Operator",
      "permissions": [
        "cameras:read",
        "cameras:write",
        "attendance:read",
        "attendance:write",
        "users:read"
      ],
      "description": "Operational access",
      "createdAt": "2025-11-05T09:00:00.000Z",
      "updatedAt": "2025-11-05T09:00:00.000Z"
    }
  ]
}
```

**Errors**:
- `401`: Missing or invalid token
- `403`: Insufficient permissions

---

### User Management Endpoints

#### GET /users
List all users with pagination.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (≥1) |
| page_size | int | 20 | Items per page (1-100) |
| search | string | - | Search by name or email |
| role_id | string | - | Filter by role ID |
| status | string | - | Filter by status (active, suspended) |

**Example**:
```
GET /users?page=1&page_size=10&search=admin&role_id=ROLE-ADMIN
```

**Response (200)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Admin User",
      "email": "admin@example.com",
      "roleId": "ROLE-ADMIN",
      "status": "active",
      "lastActive": null,
      "createdAt": "2025-11-05T09:00:00.000Z",
      "updatedAt": "2025-11-05T10:30:00.000Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 10,
    "total": 1,
    "totalPages": 1
  }
}
```

**Errors**:
- `401`: Missing or invalid token
- `403`: Insufficient permissions (requires `users:read`)

---

#### POST /users
Create a new user.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Request**:
```json
{
  "name": "John Operator",
  "email": "john@example.com",
  "roleId": "ROLE-OPERATOR",
  "password": "securepassword123"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "John Operator",
    "email": "john@example.com",
    "roleId": "ROLE-OPERATOR",
    "status": "active",
    "lastActive": null,
    "createdAt": "2025-11-05T11:00:00.000Z",
    "updatedAt": "2025-11-05T11:00:00.000Z"
  },
  "meta": {
    "createdAt": "2025-11-05T11:00:00.000Z"
  }
}
```

**Errors**:
- `400`: Email already exists
- `401`: Missing or invalid token
- `403`: Insufficient permissions (requires `users:write`)
- `422`: Validation error

---

#### GET /users/{user_id}
Get a specific user by ID.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Admin User",
    "email": "admin@example.com",
    "roleId": "ROLE-ADMIN",
    "status": "active",
    "lastActive": null,
    "createdAt": "2025-11-05T09:00:00.000Z",
    "updatedAt": "2025-11-05T10:30:00.000Z"
  }
}
```

**Errors**:
- `401`: Missing or invalid token
- `403`: Insufficient permissions (requires `users:read`)
- `404`: User not found

---

#### PUT /users/{user_id}
Update a user.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Request**:
```json
{
  "name": "Updated Name",
  "email": "newemail@example.com",
  "roleId": "ROLE-OPERATOR",
  "status": "active"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Updated Name",
    "email": "newemail@example.com",
    "roleId": "ROLE-OPERATOR",
    "status": "active",
    "lastActive": null,
    "createdAt": "2025-11-05T09:00:00.000Z",
    "updatedAt": "2025-11-05T11:30:00.000Z"
  }
}
```

**Errors**:
- `400`: Email already taken by another user
- `401`: Missing or invalid token
- `403`: Insufficient permissions (requires `users:write`)
- `404`: User not found
- `422`: Validation error

---

#### DELETE /users/{user_id}
Delete a user.

**Headers**:
```
Authorization: Bearer <accessToken>
```

**Response (204)**:
No content on success

**Errors**:
- `400`: Cannot delete your own account
- `401`: Missing or invalid token
- `403`: Insufficient permissions (requires `users:write`)
- `404`: User not found

---

## Testing

### Using curl

**1. Login**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"admin123"}'
```

**2. Get Current User** (copy accessToken from login response):
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <accessToken>"
```

**3. List Users**:
```bash
curl -X GET "http://localhost:8000/api/v1/users?page=1&page_size=10" \
  -H "Authorization: Bearer <accessToken>"
```

**4. Create User**:
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New User",
    "email": "newuser@example.com",
    "roleId": "ROLE-OPERATOR",
    "password": "securepassword123"
  }'
```

### Using Postman

1. Import OpenAPI spec: `http://localhost:8000/openapi.json`
2. Use the `/docs` UI to test endpoints directly
3. Create an environment variable for `accessToken`:
   - Get token from login endpoint
   - Use `{{accessToken}}` in Authorization header

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin@example.com", "password": "admin123"}
)
tokens = response.json()["data"]
access_token = tokens["accessToken"]

# Make authenticated request
headers = {"Authorization": f"Bearer {access_token}"}
users = requests.get(f"{BASE_URL}/users", headers=headers).json()
print(users)
```

---

## Error Handling

### Common Error Codes

| Code | Message | Cause |
|------|---------|-------|
| INVALID_PASSWORD | Invalid email or password | Login with wrong credentials |
| INVALID_TOKEN | Invalid or expired token | Token is malformed or expired |
| PERMISSION_DENIED | You don't have permission | Missing required permission |
| NOT_FOUND | Resource not found | Resource doesn't exist |
| EMAIL_EXISTS | User with this email already exists | Email taken |
| VALIDATION_ERROR | Field validation failed | Invalid input |

### Retry Logic

- **401 Unauthorized**: Use refresh token to get new access token
- **500 Server Error**: Retry after 1 second (exponential backoff)
- **Rate Limiting**: Wait and retry (limit: 1000 requests/hour)

---

## Frontend Integration

### React Example

```typescript
// services/api.ts
const API_URL = 'http://localhost:8000/api/v1';

export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: email, password })
  });

  if (!response.ok) throw new Error('Login failed');

  const data = await response.json();
  return data.data;
}

export async function getUsers(page = 1, pageSize = 20) {
  const token = localStorage.getItem('accessToken');
  const response = await fetch(
    `${API_URL}/users?page=${page}&page_size=${pageSize}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );

  if (!response.ok) throw new Error('Failed to fetch users');
  return await response.json();
}

export async function createUser(name: string, email: string, roleId: string, password: string) {
  const token = localStorage.getItem('accessToken');
  const response = await fetch(`${API_URL}/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ name, email, roleId, password })
  });

  if (!response.ok) throw new Error('Failed to create user');
  return await response.json();
}
```

### Vue Example

```typescript
// composables/useApi.ts
import { ref } from 'vue';

export function useApi() {
  const API_URL = 'http://localhost:8000/api/v1';

  async function login(email: string, password: string) {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: email, password })
    });

    const data = await response.json();
    if (data.success) {
      localStorage.setItem('accessToken', data.data.accessToken);
      localStorage.setItem('refreshToken', data.data.refreshToken);
    }
    return data;
  }

  async function getUsers(page = 1) {
    const token = localStorage.getItem('accessToken');
    return fetch(`${API_URL}/users?page=${page}`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(r => r.json());
  }

  return { login, getUsers };
}
```

---

## Phase 1 Completion Checklist

- [x] Project structure
- [x] Dependencies configured
- [x] Docker Compose setup
- [x] Environment configuration
- [x] Core modules (config, security, logging)
- [x] Database models and session
- [x] Authentication endpoints
- [x] FastAPI app
- [x] Database seeding script
- [x] Unit tests for auth
- [x] Integration tests for endpoints
- [x] User management CRUD endpoints
- [x] API router integration
- [x] Documentation
- [x] Frontend integration guide

**Status**: ✅ Phase 1 Complete (15/15 tasks)

---

## Next Steps

### Phase 2: Camera Management
- Implement camera CRUD endpoints
- Add camera connection testing
- Implement snapshot capture
- Add camera state management

### Phase 3: Detection Integration
- Integrate detection provider
- Implement live detection streaming
- Add face detection processing

---

**API Documentation Version**: 1.0
**Last Updated**: 2025-11-05
**Maintained By**: Development Team
