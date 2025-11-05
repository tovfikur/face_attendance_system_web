import {
  alerts as initialAlerts,
  attendanceLogs as initialAttendanceLogs,
  attendanceRecords as initialAttendanceRecords,
  attendanceStatistics,
  auditTrail as initialAuditTrail,
  cameraSummaries,
  cameras as initialCameras,
  defaultFaceRegistrationPayload,
  detectionEventLogs as initialDetectionEventLogs,
  detectionProviderConfig as initialDetectionProviderConfig,
  developerEndpoints,
  faceProfiles as initialFaceProfiles,
  languageOptions,
  liveDetections as initialLiveDetections,
  networkMetrics,
  notifications as initialNotifications,
  odooIntegrationConfig as initialOdooConfig,
  odooSyncLog as initialOdooSyncLog,
  personHistory,
  roles,
  rotatingBannerMessages,
  shiftSchedules,
  systemHealthMetrics,
  systemHealthSummary,
  systemServices,
  systemSummary,
  timezoneOptions,
  userAccounts as initialUserAccounts,
} from '@/data/mockData'
import type {
  Alert,
  AttendanceLog,
  AttendanceRecord,
  AttendanceStatisticPoint,
  AuditLogEntry,
  Camera,
  CameraSummary,
  DetectionEventLog,
  DetectionProviderConfig,
  DeveloperEndpoint,
  FaceProfile,
  FaceRegistrationPayload,
  LanguageOption,
  NetworkMetric,
  NotificationItem,
  OdooIntegrationConfig,
  OdooSyncLog,
  PersonDetection,
  PersonHistoryEntry,
  ResourceUsageMetric,
  Role,
  ShiftSchedule,
  SystemHealthMetric,
  SystemServiceStatus,
  SystemSummary,
  UserAccount,
} from '@/types'

const wait = (ms: number) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms)
  })

const withLatency = async <T>(payload: T, baseLatency = 200): Promise<T> => {
  const jitter = Math.random() * 220
  await wait(baseLatency + jitter)
  return JSON.parse(JSON.stringify(payload)) as T
}

let camerasStore = [...initialCameras]
let alertsStore = [...initialAlerts]
let attendanceRecordsStore = [...initialAttendanceRecords]
let attendanceLogsStore = [...initialAttendanceLogs]
let liveDetectionsStore = [...initialLiveDetections]
let notificationsStore = [...initialNotifications]
let faceProfilesStore = [...initialFaceProfiles]
let auditTrailStore = [...initialAuditTrail]
let userAccountsStore = [...initialUserAccounts]
let odooConfigStore: OdooIntegrationConfig = { ...initialOdooConfig }
let odooSyncLogStore = [...initialOdooSyncLog]
let detectionProviderStore: DetectionProviderConfig = { ...initialDetectionProviderConfig }
let detectionEventLogStore = [...initialDetectionEventLogs]

const pushAudit = (entry: AuditLogEntry) => {
  auditTrailStore = [entry, ...auditTrailStore].slice(0, 60)
}

export const mockApi = {
  async fetchSystemSummary(): Promise<SystemSummary> {
    return withLatency(systemSummary, 180)
  },

  async fetchRoles(): Promise<Role[]> {
    return withLatency(roles, 160)
  },

  async fetchCameras(): Promise<Camera[]> {
    return withLatency(
      camerasStore.map((camera) => ({
        ...camera,
        fps:
          camera.status === 'online'
            ? Math.max(0, camera.fps + Math.round((Math.random() - 0.5) * 4))
            : camera.fps,
        latency:
          camera.status === 'online'
            ? Number((camera.latency + (Math.random() - 0.5) * 6).toFixed(1))
            : camera.latency,
        bitrate:
          camera.status === 'online'
            ? Number((camera.bitrate + (Math.random() - 0.5) * 0.6).toFixed(2))
            : camera.bitrate,
        lastSeen:
          camera.status === 'online'
            ? new Date().toISOString()
            : camera.lastSeen,
        lastChecked: new Date().toISOString(),
      })),
      220,
    )
  },

  async createCamera(camera: Camera): Promise<Camera> {
    camerasStore = [camera, ...camerasStore]
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Admin',
      actorRole: 'Admin',
      message: `Registered new camera ${camera.name} (${camera.id}).`,
      timestamp: new Date().toISOString(),
      severity: 'info',
    })
    return withLatency(camera, 320)
  },

  async updateCamera(cameraId: string, updates: Partial<Camera>): Promise<Camera | undefined> {
    let updated: Camera | undefined
    camerasStore = camerasStore.map((camera) => {
      if (camera.id === cameraId) {
        updated = { ...camera, ...updates, lastChecked: new Date().toISOString() }
        return updated
      }
      return camera
    })
    if (updated) {
      pushAudit({
        id: `AUD-${Date.now()}`,
        actor: 'Admin',
        actorRole: 'Admin',
        message: `Updated camera ${updated.name} (${updated.id}).`,
        timestamp: new Date().toISOString(),
        severity: 'info',
      })
    }
    return withLatency(updated, 280)
  },

  async deleteCamera(cameraId: string): Promise<boolean> {
    const target = camerasStore.find((camera) => camera.id === cameraId)
    camerasStore = camerasStore.filter((camera) => camera.id !== cameraId)
    if (target) {
      pushAudit({
        id: `AUD-${Date.now()}`,
        actor: 'Admin',
        actorRole: 'Admin',
        message: `Removed camera ${target.name} (${target.id}).`,
        timestamp: new Date().toISOString(),
        severity: 'warning',
      })
    }
    return withLatency(true, 260)
  },

  async testCameraConnection(cameraId: string): Promise<{ success: boolean; latency: number }> {
    const success = Math.random() > 0.15
    const latency = success ? 40 + Math.random() * 30 : 0
    if (!success) {
      pushAudit({
        id: `AUD-${Date.now()}`,
        actor: 'Operator',
        actorRole: 'Operator',
        message: `Camera connectivity test failed for ${cameraId}.`,
        timestamp: new Date().toISOString(),
        severity: 'warning',
      })
    }
    return withLatency({ success, latency: Number(latency.toFixed(1)) }, 420)
  },

  async fetchCameraSummary(): Promise<CameraSummary[]> {
    return withLatency(cameraSummaries, 250)
  },

  async fetchCameraById(id: string): Promise<Camera | undefined> {
    return withLatency(camerasStore.find((camera) => camera.id === id), 260)
  },

  async fetchAttendance(limit = 20): Promise<AttendanceRecord[]> {
    return withLatency(attendanceRecordsStore.slice(0, limit), 300)
  },

  async fetchAttendanceLogs(params?: {
    search?: string
    cameraId?: string
    dateFrom?: string
    dateTo?: string
    odooStatus?: AttendanceLog['odooStatus'] | 'all'
  }): Promise<AttendanceLog[]> {
    const { search, cameraId, dateFrom, dateTo, odooStatus } = params ?? {}
    const filtered = attendanceLogsStore.filter((log) => {
      const matchesSearch =
        !search ||
        log.employeeId.toLowerCase().includes(search.toLowerCase()) ||
        log.name.toLowerCase().includes(search.toLowerCase())
      const matchesCamera = !cameraId || log.cameraId === cameraId
      const logDate = new Date(log.date)
      const matchesFrom = !dateFrom || logDate >= new Date(dateFrom)
      const matchesTo = !dateTo || logDate <= new Date(dateTo)
      const matchesOdoo = !odooStatus || odooStatus === 'all' || log.odooStatus === odooStatus
      return matchesSearch && matchesCamera && matchesFrom && matchesTo && matchesOdoo
    })
    return withLatency(filtered, 320)
  },

  async exportAttendanceLogs(format: 'csv' | 'pdf'): Promise<{ url: string }> {
    const url = `/exports/attendance-${Date.now()}.${format}`
    await wait(420)
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Operator',
      actorRole: 'Operator',
      message: `Exported attendance logs to ${format.toUpperCase()}.`,
      timestamp: new Date().toISOString(),
      severity: 'info',
    })
    return { url }
  },

  async fetchAttendanceStatistics(category: AttendanceStatisticPoint['category']) {
    return withLatency(attendanceStatistics.filter((stat) => stat.category === category), 240)
  },

  async fetchAlerts(limit = 20): Promise<Alert[]> {
    return withLatency(alertsStore.slice(0, limit), 260)
  },

  async acknowledgeAlert(alertId: string): Promise<Alert | undefined> {
    let updated: Alert | undefined
    alertsStore = alertsStore.map((alert) => {
      if (alert.id === alertId) {
        updated = { ...alert, acknowledged: true }
        return updated
      }
      return alert
    })
    if (updated) {
      pushAudit({
        id: `AUD-${Date.now()}`,
        actor: 'Operator',
        actorRole: 'Operator',
        message: `Acknowledged alert ${updated.id}.`,
        timestamp: new Date().toISOString(),
        severity: 'info',
      })
    }
    return withLatency(updated, 200)
  },

  async muteAlert(alertId: string): Promise<Alert | undefined> {
    let updated: Alert | undefined
    alertsStore = alertsStore.map((alert) => {
      if (alert.id === alertId) {
        updated = { ...alert, acknowledged: true, tags: [...alert.tags, 'muted'] }
        return updated
      }
      return alert
    })
    return withLatency(updated, 200)
  },

  async clearAlert(alertId: string): Promise<void> {
    alertsStore = alertsStore.filter((alert) => alert.id !== alertId)
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Operator',
      actorRole: 'Operator',
      message: `Cleared alert ${alertId}.`,
      timestamp: new Date().toISOString(),
      severity: 'warning',
    })
    await wait(160)
  },

  async fetchNotifications(): Promise<NotificationItem[]> {
    return withLatency(notificationsStore, 180)
  },

  async acknowledgeNotification(notificationId: string): Promise<NotificationItem | undefined> {
    let updated: NotificationItem | undefined
    notificationsStore = notificationsStore.map((notification) => {
      if (notification.id === notificationId) {
        updated = { ...notification, acknowledged: true }
        return updated
      }
      return notification
    })
    return withLatency(updated, 160)
  },

  async clearNotifications(): Promise<void> {
    notificationsStore = []
    await wait(120)
  },

  async fetchLiveDetections(cameraId?: string): Promise<PersonDetection[]> {
    const data = cameraId
      ? liveDetectionsStore.filter((item) => item.cameraId === cameraId)
      : liveDetectionsStore
    return withLatency(
      data.map((entry) => ({
        ...entry,
        confidence: Number((entry.confidence + (Math.random() - 0.5) * 1.6).toFixed(1)),
        timestamp: new Date().toISOString(),
      })),
      180,
    )
  },

  async fetchDetectionProviderConfig(): Promise<DetectionProviderConfig> {
    return withLatency(detectionProviderStore, 180)
  },

  async updateDetectionProviderConfig(
    update: Partial<DetectionProviderConfig>,
  ): Promise<DetectionProviderConfig> {
    detectionProviderStore = { ...detectionProviderStore, ...update }
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Admin',
      actorRole: 'Admin',
      message: 'Updated detection provider configuration.',
      timestamp: new Date().toISOString(),
      severity: 'info',
    })
    return withLatency(detectionProviderStore, 220)
  },

  async testDetectionProvider(): Promise<{ status: DetectionProviderConfig['status']; latency: number }> {
    const latency = 150 + Math.random() * 120
    const statusRoll = Math.random()
    const status: DetectionProviderConfig['status'] =
      statusRoll > 0.85 ? 'offline' : statusRoll > 0.55 ? 'degraded' : 'connected'
    detectionProviderStore = {
      ...detectionProviderStore,
      status,
      lastHeartbeat: new Date().toISOString(),
      averageLatencyMs: Math.round((detectionProviderStore.averageLatencyMs + latency) / 2),
    }
    return withLatency({ status, latency: Number(latency.toFixed(0)) }, 280)
  },

  async sendFrameForDetection(cameraId: string): Promise<DetectionEventLog> {
    const camera = camerasStore.find((item) => item.id === cameraId)
    const timestamp = new Date().toISOString()
    const succeeded = Math.random() > 0.15
    const logEntry: DetectionEventLog = succeeded
      ? {
          id: `DET-LOG-${Date.now()}`,
          cameraId,
          cameraName: camera?.name ?? cameraId,
          timestamp,
          status: 'received',
          latencyMs: Math.round(140 + Math.random() * 60),
          payload: {
            detections: [
              {
                personId: `EMP-${String(Math.floor(Math.random() * 500)).padStart(5, '0')}`,
                confidence: Number((90 + Math.random() * 9).toFixed(1)),
                bbox: [Math.random(), Math.random(), Math.random(), Math.random()],
              },
            ],
          },
        }
      : {
          id: `DET-LOG-${Date.now()}`,
          cameraId,
          cameraName: camera?.name ?? cameraId,
          timestamp,
          status: 'error',
          latencyMs: 0,
          payload: { error: 'Detection provider timeout.' },
        }
    detectionEventLogStore = [logEntry, ...detectionEventLogStore].slice(0, 40)
    return withLatency(logEntry, 260)
  },

  async fetchDetectionEventLogs(limit = 30): Promise<DetectionEventLog[]> {
    return withLatency(detectionEventLogStore.slice(0, limit), 220)
  },
  async fetchShiftSchedules(): Promise<ShiftSchedule[]> {
    return withLatency(shiftSchedules, 240)
  },

  async fetchNetworkMetrics(): Promise<NetworkMetric[]> {
    return withLatency(
      networkMetrics.map((metric) => ({
        ...metric,
        value: Number((metric.value + (Math.random() - 0.5) * 4).toFixed(1)),
      })),
      220,
    )
  },

  async fetchSystemHealthMetrics(): Promise<ResourceUsageMetric[]> {
    return withLatency(
      systemHealthMetrics.map((metric) => ({
        ...metric,
        value: Number((metric.value + (Math.random() - 0.5) * 5).toFixed(1)),
      })),
      240,
    )
  },

  async fetchSystemHealthSummary(): Promise<SystemHealthMetric[]> {
    return withLatency(systemHealthSummary, 200)
  },

  async fetchSystemServices(): Promise<SystemServiceStatus[]> {
    return withLatency(systemServices, 200)
  },

  async restartService(serviceId: string): Promise<SystemServiceStatus | undefined> {
    await wait(600)
    let updated: SystemServiceStatus | undefined
    const now = new Date().toISOString()
    for (const service of systemServices) {
      if (service.id === serviceId) {
        updated = { ...service, status: 'running', lastRestart: now, uptime: '0d 00h' }
        break
      }
    }
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Admin',
      actorRole: 'Admin',
      message: `Restarted service ${serviceId}.`,
      timestamp: now,
      severity: 'warning',
    })
    return updated
  },

  async fetchFaceProfiles(): Promise<FaceProfile[]> {
    return withLatency(faceProfilesStore, 260)
  },

  async registerFace(payload: FaceRegistrationPayload): Promise<FaceProfile> {
    const profile: FaceProfile = {
      id: `FACE-${Date.now()}`,
      employeeId: payload.employeeId,
      name: payload.name,
      department: payload.department,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'pending',
      images: payload.images,
    }
    faceProfilesStore = [profile, ...faceProfilesStore]
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Admin',
      actorRole: 'Admin',
      message: `Registered new face for employee ${payload.employeeId}.`,
      timestamp: profile.createdAt,
      severity: 'info',
    })
    return withLatency(profile, 420)
  },

  async updateFaceProfile(faceId: string, updates: Partial<FaceProfile>) {
    let updated: FaceProfile | undefined
    faceProfilesStore = faceProfilesStore.map((profile) => {
      if (profile.id === faceId) {
        updated = { ...profile, ...updates, updatedAt: new Date().toISOString() }
        return updated
      }
      return profile
    })
    if (updated) {
      pushAudit({
        id: `AUD-${Date.now()}`,
        actor: 'Admin',
        actorRole: 'Admin',
        message: `Updated face profile ${updated.employeeId}.`,
        timestamp: new Date().toISOString(),
        severity: 'info',
      })
    }
    return withLatency(updated, 320)
  },

  async deleteFaceProfile(faceId: string): Promise<boolean> {
    const target = faceProfilesStore.find((profile) => profile.id === faceId)
    faceProfilesStore = faceProfilesStore.filter((profile) => profile.id !== faceId)
    if (target) {
      pushAudit({
        id: `AUD-${Date.now()}`,
        actor: 'Admin',
        actorRole: 'Admin',
        message: `Deleted face profile ${target.employeeId}.`,
        timestamp: new Date().toISOString(),
        severity: 'warning',
      })
    }
    return withLatency(true, 260)
  },

  async fetchAuditTrail(): Promise<AuditLogEntry[]> {
    return withLatency(auditTrailStore, 260)
  },

  async fetchUserAccounts(): Promise<UserAccount[]> {
    return withLatency(userAccountsStore, 240)
  },

  async updateUserAccount(userId: string, updates: Partial<UserAccount>) {
    userAccountsStore = userAccountsStore.map((user) =>
      user.id === userId ? { ...user, ...updates } : user,
    )
    return withLatency(
      userAccountsStore.find((user) => user.id === userId),
      220,
    )
  },

  async createUserAccount(user: UserAccount) {
    userAccountsStore = [user, ...userAccountsStore]
    return withLatency(user, 240)
  },

  async fetchPersonHistory(employeeId: string): Promise<PersonHistoryEntry[]> {
    return withLatency(personHistory.filter((entry) => entry.employeeId === employeeId), 280)
  },

  async fetchDeveloperEndpoints(): Promise<DeveloperEndpoint[]> {
    return withLatency(developerEndpoints, 180)
  },

  async invokeDeveloperEndpoint(endpointId: string): Promise<unknown> {
    await wait(360)
    switch (endpointId) {
      case 'DEV-001':
        return camerasStore
      case 'DEV-002':
        return attendanceLogsStore
      case 'DEV-003':
        return { ...defaultFaceRegistrationPayload }
      case 'DEV-004':
        return liveDetectionsStore
      default:
        return { status: 'ok' }
    }
  },

  async fetchLanguageOptions(): Promise<LanguageOption[]> {
    return withLatency(languageOptions, 100)
  },

  async fetchTimezoneOptions(): Promise<string[]> {
    return withLatency(timezoneOptions, 100)
  },

  async fetchOdooIntegrationConfig(): Promise<OdooIntegrationConfig> {
    return withLatency(odooConfigStore, 200)
  },

  async updateOdooIntegrationConfig(
    update: Partial<OdooIntegrationConfig>,
  ): Promise<OdooIntegrationConfig> {
    odooConfigStore = { ...odooConfigStore, ...update }
    pushAudit({
      id: `AUD-${Date.now()}`,
      actor: 'Admin',
      actorRole: 'Admin',
      message: 'Updated Odoo integration configuration.',
      timestamp: new Date().toISOString(),
      severity: 'info',
    })
    return withLatency(odooConfigStore, 220)
  },

  async fetchOdooSyncLog(limit = 20): Promise<OdooSyncLog[]> {
    return withLatency(odooSyncLogStore.slice(0, limit), 200)
  },

  async pushAttendanceToOdoo(recordIds: string[]): Promise<{ success: number; failed: number }> {
    let success = 0
    let failed = 0
    const timestamp = new Date().toISOString()
    attendanceLogsStore = attendanceLogsStore.map((record) => {
      if (!recordIds.includes(record.id)) {
        return record
      }
      const didSucceed = Math.random() > 0.2
      if (didSucceed) {
        success += 1
        odooSyncLogStore = [
          {
            id: `ODOO-PUSH-${Date.now()}-${record.employeeId}`,
            timestamp,
            employeeId: record.employeeId,
            result: 'success',
            message: 'Attendance synchronized with Odoo.',
          },
          ...odooSyncLogStore,
        ]
        return { ...record, odooStatus: 'synced', odooSyncTime: timestamp }
      }
      failed += 1
      odooSyncLogStore = [
        {
          id: `ODOO-PUSH-${Date.now()}-${record.employeeId}`,
          timestamp,
          employeeId: record.employeeId,
          result: 'failure',
          message: 'Mock failure while contacting Odoo API.',
        },
        ...odooSyncLogStore,
      ]
      return { ...record, odooStatus: 'failed' }
    })
    odooConfigStore = {
      ...odooConfigStore,
      pendingCount: Math.max(0, odooConfigStore.pendingCount - success),
      failureCount: odooConfigStore.failureCount + failed,
      lastSync: timestamp,
    }
    return withLatency({ success, failed }, 420)
  },

  subscribeToBannerMessages(callback: (message: string) => void, interval = 6500): () => void {
    let index = 0
    const timer = setInterval(() => {
      callback(rotatingBannerMessages[index % rotatingBannerMessages.length])
      index += 1
    }, interval)

    callback(rotatingBannerMessages[index % rotatingBannerMessages.length])

    return () => clearInterval(timer)
  },
}

