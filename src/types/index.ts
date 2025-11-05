export type StreamType = 'RTSP' | 'USB' | 'HTTP' | 'Socket' | 'Local File'

export type CameraStatus = 'online' | 'offline' | 'maintenance'

export interface Camera {
  id: string
  name: string
  location: string
  streamType: StreamType
  status: CameraStatus
  fps: number
  latency: number
  bitrate: number
  resolution: string
  lastSeen: string
  ipAddress: string
  tags: string[]
  thumbnail: string
  streamUrl?: string
  lastChecked?: string
  enabled?: boolean
}

export interface CameraSummary {
  id: string
  detectionsToday: number
  unknownFaces: number
  uptimePercent: number
}

export interface SystemSummary {
  activeCameras: number
  registeredPeople: number
  peopleDetectedToday: number
  unknownFaceAlerts: number
  manualOverrides: number
  attendanceCompletion: number
  lastSync: string
}

export interface AttendanceRecord {
  id: string
  personId: string
  name: string
  role: string
  department: string
  status: 'on-site' | 'off-site' | 'remote'
  accuracy: number
  timestamp: string
  cameraId: string
  cameraName: string
  thumbnail: string
}

export interface AttendanceLog {
  id: string
  employeeId: string
  name: string
  department: string
  date: string
  timeIn: string
  timeOut: string
  cameraId: string
  cameraName: string
  accuracy: number
  status: 'present' | 'late' | 'missed'
  odooStatus: 'synced' | 'pending' | 'failed'
  odooSyncTime?: string
}

export interface PersonDetection {
  id: string
  personId: string
  name: string
  cameraId: string
  confidence: number
  timestamp: string
  trackId: string
  boundingBox: BoundingBox
  thumbnail: string
  status: 'authorized' | 'visitor' | 'unknown'
}

export interface BoundingBox {
  top: number
  left: number
  width: number
  height: number
}

export interface Alert {
  id: string
  title: string
  description: string
  level: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  cameraId: string
  acknowledged: boolean
  tags: string[]
  muted?: boolean
}

export interface ShiftSchedule {
  id: string
  name: string
  startTime: string
  endTime: string
  location: string
  expectedHeadcount: number
  compliance: number
}

export interface Role {
  id: string
  name: 'Admin' | 'Operator' | 'Viewer'
  permissions: string[]
  description: string
}

export interface SystemHealthMetric {
  id: string
  label: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'steady'
  change: number
}

export interface NetworkMetric {
  id: string
  label: string
  value: number
  unit: string
  status: 'good' | 'warning' | 'critical'
}

export interface FaceProfile {
  id: string
  employeeId: string
  name: string
  department: string
  createdAt: string
  updatedAt: string
  status: 'active' | 'pending' | 'archived'
  images: string[]
  notes?: string
}

export interface FaceRegistrationPayload {
  name: string
  employeeId: string
  department: string
  images: string[]
}

export interface AuditLogEntry {
  id: string
  actor: string
  actorRole: Role['name']
  message: string
  timestamp: string
  context?: string
  severity: 'info' | 'warning' | 'critical'
}

export interface UserAccount {
  id: string
  name: string
  email: string
  roleId: Role['id']
  status: 'active' | 'suspended'
  lastActive: string
}

export interface SystemServiceStatus {
  id: string
  name: string
  status: 'running' | 'degraded' | 'stopped'
  uptime: string
  version: string
  lastRestart: string
}

export interface ResourceUsageMetric {
  id: string
  label: string
  value: number
  unit: string
  limit: number
  category: 'cpu' | 'gpu' | 'memory' | 'disk' | 'network'
}

export interface PersonHistoryEntry {
  id: string
  employeeId: string
  name: string
  cameraId: string
  cameraName: string
  timestamp: string
  accuracy: number
  thumbnail: string
  streamType: StreamType
}

export interface DeveloperEndpoint {
  id: string
  label: string
  description: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string
}

export interface AttendanceStatisticPoint {
  id: string
  label: string
  value: number
  category: 'hour' | 'day' | 'camera'
}

export interface NotificationItem {
  id: string
  title: string
  message: string
  timestamp: string
  level: 'info' | 'warning' | 'critical'
  acknowledged: boolean
  link?: string
}

export interface LanguageOption {
  code: string
  label: string
  isDefault?: boolean
}

export interface OdooIntegrationConfig {
  baseUrl: string
  database: string
  company: string
  apiKey?: string
  autoSync: boolean
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
  pendingCount: number
  failureCount: number
}

export interface OdooSyncLog {
  id: string
  timestamp: string
  employeeId: string
  result: 'success' | 'failure'
  message: string
}

export interface DetectionProviderConfig {
  providerName: string
  endpoint: string
  apiKey?: string
  enabled: boolean
  status: 'connected' | 'degraded' | 'offline'
  lastHeartbeat?: string
  averageLatencyMs: number
}

export interface DetectionEventLog {
  id: string
  cameraId: string
  cameraName: string
  timestamp: string
  status: 'received' | 'processing' | 'error'
  latencyMs: number
  payload: Record<string, unknown>
}
