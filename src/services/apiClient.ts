/**
 * API Client Service
 * Handles all HTTP communication with the backend API
 * Includes token management, error handling, and request/response intercepting
 */

import type {
  AttendanceRecord,
  Camera,
  FaceProfile,
} from '@/types'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_VERSION = 'v1'
const API_ENDPOINT = `${API_BASE_URL}/api/${API_VERSION}`

// Token storage keys
const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const TOKEN_EXPIRY_KEY = 'token_expiry'

// Custom error class for API errors
export class ApiError extends Error {
  statusCode: number
  data?: unknown

  constructor(statusCode: number, message: string, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.statusCode = statusCode
    this.data = data
  }
}

// Request/Response types
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user?: {
    id: string
    username: string
    email: string
  }
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  meta: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

export interface SuccessResponse<T> {
  success: boolean
  data: T
  meta?: Record<string, unknown>
}

// API Client
export const apiClient = {
  /**
   * Set authentication token
   */
  setToken(token: string, expiresIn?: number) {
    localStorage.setItem(TOKEN_KEY, token)
    if (expiresIn) {
      const expiryTime = new Date().getTime() + expiresIn * 1000
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString())
    }
  },

  /**
   * Get stored authentication token
   */
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  /**
   * Clear authentication token
   */
  clearToken() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
  },

  /**
   * Check if token is expired
   */
  isTokenExpired(): boolean {
    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY)
    if (!expiryStr) return false
    const expiry = parseInt(expiryStr, 10)
    return new Date().getTime() > expiry
  },

  /**
   * Make HTTP request with authentication
   */
  async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    endpoint: string,
    options: {
      body?: unknown
      query?: Record<string, string | number | boolean>
      headers?: Record<string, string>
      skipAuth?: boolean
    } = {}
  ): Promise<T> {
    const { body, query, headers = {}, skipAuth = false } = options

    // Build URL with query parameters
    let url = `${API_ENDPOINT}${endpoint}`
    if (query) {
      const params = new URLSearchParams()
      Object.entries(query).forEach(([key, value]) => {
        params.append(key, String(value))
      })
      url += `?${params.toString()}`
    }

    // Build request headers
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    }

    // Add authorization token
    if (!skipAuth) {
      const token = apiClient.getToken()
      if (token) {
        requestHeaders['Authorization'] = `Bearer ${token}`
      }
    }

    // Make request
    try {
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : undefined,
        credentials: 'include',
      })

      // Handle response
      const responseData = await response.json().catch(() => null)

      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401) {
          apiClient.clearToken()
          window.location.href = '/login'
        }

        throw new ApiError(
          response.status,
          responseData?.detail || responseData?.message || 'API Error',
          responseData
        )
      }

      return responseData as T
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }

      // Network error or JSON parsing error
      throw new ApiError(
        0,
        error instanceof Error ? error.message : 'Unknown error'
      )
    }
  },

  // ============================================================================
  // Authentication Endpoints
  // ============================================================================

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.request<LoginResponse>('POST', '/auth/login', {
      body: credentials,
      skipAuth: true,
    })
    return response
  },

  async logout(): Promise<void> {
    try {
      await apiClient.request<void>('POST', '/auth/logout', {})
    } finally {
      apiClient.clearToken()
    }
  },

  // ============================================================================
  // Person Endpoints
  // ============================================================================

  async getPersons(
    page: number = 1,
    pageSize: number = 20,
    filters?: {
      status?: string
      personType?: string
      department?: string
    }
  ): Promise<PaginatedResponse<FaceProfile>> {
    const query: Record<string, string | number> = { page, page_size: pageSize }
    if (filters?.status) query.status = filters.status
    if (filters?.personType) query.person_type = filters.personType
    if (filters?.department) query.department = filters.department

    return apiClient.request<PaginatedResponse<FaceProfile>>('GET', '/persons', {
      query,
    })
  },

  async getPerson(personId: string): Promise<SuccessResponse<FaceProfile>> {
    return apiClient.request<SuccessResponse<FaceProfile>>('GET', `/persons/${personId}`, {})
  },

  async createPerson(data: {
    first_name: string
    last_name: string
    email: string
    phone?: string
    person_type: string
    id_number?: string
    id_type?: string
    department?: string
    organization?: string
    status: string
  }): Promise<SuccessResponse<FaceProfile>> {
    return apiClient.request<SuccessResponse<FaceProfile>>('POST', '/persons', {
      body: data,
    })
  },

  async updatePerson(
    personId: string,
    data: Partial<{
      first_name: string
      last_name: string
      email: string
      phone: string
      person_type: string
      id_number: string
      id_type: string
      department: string
      organization: string
      status: string
    }>
  ): Promise<SuccessResponse<FaceProfile>> {
    return apiClient.request<SuccessResponse<FaceProfile>>(
      'PUT',
      `/persons/${personId}`,
      { body: data }
    )
  },

  async deletePerson(personId: string): Promise<void> {
    return apiClient.request<void>('DELETE', `/persons/${personId}`, {})
  },

  async searchPersons(query: string): Promise<PaginatedResponse<FaceProfile>> {
    return apiClient.request<PaginatedResponse<FaceProfile>>('GET', '/persons/search', {
      query: { q: query },
    })
  },

  async enrollFace(
    personId: string,
    frameData: string, // base64
    isPrimary: boolean = false,
    qualityScore: number = 0
  ): Promise<SuccessResponse<{
    encoding_id: string
    person_id: string
    confidence: number
    total_encodings: number
    is_primary: boolean
    quality_score: number
  }>> {
    return apiClient.request<SuccessResponse<{
      encoding_id: string
      person_id: string
      confidence: number
      total_encodings: number
      is_primary: boolean
      quality_score: number
    }>>('POST', `/persons/${personId}/enroll`, {
      body: {
        frame_data: frameData,
        is_primary: isPrimary,
        quality_score: qualityScore,
      },
    })
  },

  async searchByFace(
    frameData: string,
    confidenceThreshold: number = 0.6
  ): Promise<SuccessResponse<{
    matched: boolean
    best_match?: {
      person_id: string
      first_name: string
      last_name: string
      confidence: number
    }
    all_matches: Array<{
      person_id: string
      first_name: string
      last_name: string
      confidence: number
    }>
  }>> {
    return apiClient.request<SuccessResponse<{
      matched: boolean
      best_match?: {
        person_id: string
        first_name: string
        last_name: string
        confidence: number
      }
      all_matches: Array<{
        person_id: string
        first_name: string
        last_name: string
        confidence: number
      }>
    }>>('POST', '/persons/search/by-face', {
      body: {
        frame_data: frameData,
        confidence_threshold: confidenceThreshold,
      },
    })
  },

  async getPersonSummary(): Promise<SuccessResponse<{
    total_persons: number
    active_persons: number
    persons_with_faces: number
    by_type: Record<string, number>
  }>> {
    return apiClient.request('GET', '/persons/summary', {})
  },

  // ============================================================================
  // Attendance Endpoints
  // ============================================================================

  async checkIn(
    personId: string,
    confidenceThreshold: number = 0.7
  ): Promise<SuccessResponse<{
    success: boolean
    person_id: string
    person_name: string
    check_in_time: string
    confidence: number
    message: string
  }>> {
    return apiClient.request('POST', '/attendance/check-in', {
      body: {
        person_id: personId,
        confidence_threshold: confidenceThreshold,
      },
    })
  },

  async checkOut(personId: string): Promise<SuccessResponse<{
    success: boolean
    person_id: string
    person_name: string
    check_out_time: string
    duration_minutes: number
    message: string
  }>> {
    return apiClient.request('POST', '/attendance/check-out', {
      body: { person_id: personId },
    })
  },

  async getAttendanceRecords(
    page: number = 1,
    pageSize: number = 20,
    filters?: {
      personId?: string
      fromDate?: string
      toDate?: string
      status?: string
    }
  ): Promise<PaginatedResponse<AttendanceRecord>> {
    const query: Record<string, string | number> = { page, page_size: pageSize }
    if (filters?.personId) query.person_id = filters.personId
    if (filters?.fromDate) query.from_date = filters.fromDate
    if (filters?.toDate) query.to_date = filters.toDate
    if (filters?.status) query.status = filters.status

    return apiClient.request<PaginatedResponse<AttendanceRecord>>(
      'GET',
      '/attendance',
      { query }
    )
  },

  async getPersonAttendance(
    personId: string,
    page: number = 1,
    pageSize: number = 30,
    filters?: {
      fromDate?: string
      toDate?: string
    }
  ): Promise<PaginatedResponse<AttendanceRecord>> {
    const query: Record<string, string | number> = { page, page_size: pageSize }
    if (filters?.fromDate) query.from_date = filters.fromDate
    if (filters?.toDate) query.to_date = filters.toDate

    return apiClient.request<PaginatedResponse<AttendanceRecord>>(
      'GET',
      `/attendance/${personId}`,
      { query }
    )
  },

  async getDailyReport(date?: string): Promise<SuccessResponse<{
    total_persons: number
    present: number
    absent: number
    late: number
    presence_percentage: number
  }>> {
    const query = date ? { date: date } : undefined
    return apiClient.request('GET', '/attendance/reports/daily', { query })
  },

  async getPersonStatistics(
    personId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<SuccessResponse<{
    total_working_days: number
    days_present: number
    days_absent: number
    days_late: number
    days_early_leave: number
    presence_percentage: number
  }>> {
    const query: Record<string, string> = {}
    if (fromDate) query.from_date = fromDate
    if (toDate) query.to_date = toDate

    return apiClient.request('GET', `/attendance/${personId}/statistics`, {
      query,
    })
  },

  async getPersonStatus(personId: string): Promise<SuccessResponse<{
    person_id: string
    person_name: string
    checked_in: boolean
    check_in_time?: string
    current_duration_minutes?: number
  }>> {
    return apiClient.request('GET', `/attendance/status/${personId}`, {})
  },

  // ============================================================================
  // Camera Endpoints
  // ============================================================================

  async getCameras(): Promise<SuccessResponse<Camera[]>> {
    return apiClient.request('GET', '/cameras', {})
  },

  async getCamera(cameraId: string): Promise<SuccessResponse<Camera>> {
    return apiClient.request('GET', `/cameras/${cameraId}`, {})
  },

  async createCamera(data: Partial<Camera>): Promise<SuccessResponse<Camera>> {
    return apiClient.request('POST', '/cameras', { body: data })
  },

  async updateCamera(
    cameraId: string,
    data: Partial<Camera>
  ): Promise<SuccessResponse<Camera>> {
    return apiClient.request('PUT', `/cameras/${cameraId}`, { body: data })
  },

  async deleteCamera(cameraId: string): Promise<void> {
    return apiClient.request('DELETE', `/cameras/${cameraId}`, {})
  },

  // ============================================================================
  // Detection Endpoints
  // ============================================================================

  async getDetections(
    page: number = 1,
    pageSize: number = 20,
    filters?: {
      personId?: string
      cameraId?: string
      fromDate?: string
      toDate?: string
    }
  ): Promise<PaginatedResponse<{
    id: string
    person_id?: string
    person_name?: string
    camera_id: string
    confidence: number
    created_at: string
  }>> {
    const query: Record<string, string | number> = { page, page_size: pageSize }
    if (filters?.personId) query.person_id = filters.personId
    if (filters?.cameraId) query.camera_id = filters.cameraId
    if (filters?.fromDate) query.from_date = filters.fromDate
    if (filters?.toDate) query.to_date = filters.toDate

    return apiClient.request('GET', '/detections', { query })
  },

  // ============================================================================
  // Settings Endpoints
  // ============================================================================

  async getSettings(): Promise<SuccessResponse<Record<string, unknown>>> {
    return apiClient.request('GET', '/settings', {})
  },

  async updateSettings(
    data: Record<string, unknown>
  ): Promise<SuccessResponse<Record<string, unknown>>> {
    return apiClient.request('PUT', '/settings', { body: data })
  },
}

export default apiClient
