import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { CloudDownload, CloudUpload, History, Network, PlugZap, Plus, Radio, RefreshCw, Trash } from 'lucide-react'
import type { Camera, DetectionEventLog, DetectionProviderConfig, OdooIntegrationConfig, OdooSyncLog, Role, StreamType, UserAccount } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { formatTimestamp } from '@/utils/formatters'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface CameraFormState {
  id: string
  name: string
  location: string
  streamType: StreamType
  streamUrl: string
}

const initialForm: CameraFormState = {
  id: '',
  name: '',
  location: '',
  streamType: 'RTSP',
  streamUrl: '',
}

const odooStatusTone: Record<OdooIntegrationConfig['status'], 'success' | 'warning' | 'danger'> = {
  connected: 'success',
  disconnected: 'danger',
  error: 'warning',
}

const detectionStatusTone: Record<DetectionProviderConfig['status'], 'success' | 'warning' | 'danger'> = {
  connected: 'success',
  degraded: 'warning',
  offline: 'danger',
}

export const SettingsPage = () => {
  const [cameraForm, setCameraForm] = useState<CameraFormState>(initialForm)
  const [configPreview, setConfigPreview] = useState('')
  const [statusMessage, setStatusMessage] = useState<string>()
  const [odooForm, setOdooForm] = useState<OdooIntegrationConfig | null>(null)
  const [odooSaving, setOdooSaving] = useState(false)
  const [detectionForm, setDetectionForm] = useState<DetectionProviderConfig | null>(null)
  const [detectionSaving, setDetectionSaving] = useState(false)
  const [testingDetection, setTestingDetection] = useState(false)
  const [testMessage, setTestMessage] = useState<string>()

  const {
    data: cameras,
    refresh: refreshCameras,
    loading: camerasLoading,
  } = usePolling<Camera[]>({
    fetcher: () => mockApi.fetchCameras(),
    interval: 20000,
  })

  const { data: roles } = usePolling<Role[]>({
    fetcher: () => mockApi.fetchRoles(),
    interval: 60000,
  })

  const { data: users, refresh: refreshUsers } = usePolling<UserAccount[]>({
    fetcher: () => mockApi.fetchUserAccounts(),
    interval: 30000,
  })

  const { data: odooConfig, refresh: refreshOdooConfig } = usePolling<OdooIntegrationConfig>({
    fetcher: () => mockApi.fetchOdooIntegrationConfig(),
    interval: 30000,
  })

  const { data: odooSyncLog, refresh: refreshOdooLog } = usePolling<OdooSyncLog[]>({
    fetcher: () => mockApi.fetchOdooSyncLog(10),
    interval: 30000,
  })

  const { data: detectionConfig, refresh: refreshDetectionConfig } = usePolling<DetectionProviderConfig>({
    fetcher: () => mockApi.fetchDetectionProviderConfig(),
    interval: 30000,
  })

  const { data: detectionLogs, refresh: refreshDetectionLogs } = usePolling<DetectionEventLog[]>({
    fetcher: () => mockApi.fetchDetectionEventLogs(12),
    interval: 30000,
  })

  useEffect(() => {
    if (odooConfig) {
      setOdooForm(odooConfig)
    }
  }, [odooConfig])

  useEffect(() => {
    if (detectionConfig) {
      setDetectionForm(detectionConfig)
    }
  }, [detectionConfig])

  const handleCameraSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!cameraForm.id || !cameraForm.name || !cameraForm.streamUrl) {
      setStatusMessage('Camera ID, name, and stream URL are required.')
      return
    }

    const newCamera: Camera = {
      id: cameraForm.id,
      name: cameraForm.name,
      location: cameraForm.location || 'Unassigned',
      streamType: cameraForm.streamType,
      status: 'online',
      fps: 30,
      latency: 40,
      bitrate: 6.2,
      resolution: '1920x1080',
      lastSeen: new Date().toISOString(),
      lastChecked: new Date().toISOString(),
      ipAddress: '0.0.0.0',
      tags: ['new'],
      thumbnail: '/assets/mock-feed-1.svg',
      streamUrl: cameraForm.streamUrl,
      enabled: true,
    }

    await mockApi.createCamera(newCamera)
    setStatusMessage(`Camera ${cameraForm.id} queued for provisioning.`)
    setCameraForm(initialForm)
    refreshCameras()
  }

  const handleToggleCamera = async (camera: Camera) => {
    await mockApi.updateCamera(camera.id, { enabled: !camera.enabled })
    setStatusMessage(
      `Camera ${camera.id} ${camera.enabled ? 'disabled' : 'enabled'} for ingestion pipeline.`,
    )
    refreshCameras()
  }

  const handleTestConnection = async (camera: Camera) => {
    const result = await mockApi.testCameraConnection(camera.id)
    if (result.success) {
      setStatusMessage(
        `Camera ${camera.id} reachable: latency ${result.latency.toFixed(1)} ms.`,
      )
    } else {
      setStatusMessage(`Camera ${camera.id} connection failed.`)
    }
  }

  const handleDeleteCamera = async (cameraId: string) => {
    await mockApi.deleteCamera(cameraId)
    setStatusMessage(`Camera ${cameraId} removed from configuration.`)
    refreshCameras()
  }

  const handleBackup = async () => {
    const current = await mockApi.fetchCameras()
    const payload = JSON.stringify(current, null, 2)
    setConfigPreview(payload)
    setStatusMessage(`Backup generated with ${current.length} cameras.`)
  }

  const handleRestore = async () => {
    if (!configPreview.trim()) {
      setStatusMessage('Paste camera JSON configuration to restore.')
      return
    }
    try {
      const parsed = JSON.parse(configPreview) as Camera[]
      for (const camera of parsed) {
        await mockApi.updateCamera(camera.id, camera)
      }
      setStatusMessage('Configuration restored (mock).')
      refreshCameras()
    } catch (error) {
      console.error(error)
      setStatusMessage('Invalid configuration JSON.')
    }
  }

  const handleOdooConfigSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!odooForm) return
    setOdooSaving(true)
    try {
      await mockApi.updateOdooIntegrationConfig({
        baseUrl: odooForm.baseUrl,
        database: odooForm.database,
        company: odooForm.company,
        apiKey: odooForm.apiKey,
        autoSync: odooForm.autoSync,
      })
      setStatusMessage('Odoo configuration updated.')
      refreshOdooConfig()
      refreshOdooLog()
    } catch (error) {
      console.error(error)
      setStatusMessage('Failed to update Odoo configuration.')
    } finally {
      setOdooSaving(false)
    }
  }

  const handleDetectionConfigSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!detectionForm) return
    setDetectionSaving(true)
    try {
      await mockApi.updateDetectionProviderConfig({
        providerName: detectionForm.providerName,
        endpoint: detectionForm.endpoint,
        apiKey: detectionForm.apiKey,
        enabled: detectionForm.enabled,
      })
      setStatusMessage('Detection provider configuration updated.')
      refreshDetectionConfig()
    } catch (error) {
      console.error(error)
      setStatusMessage('Failed to update detection provider configuration.')
    } finally {
      setDetectionSaving(false)
    }
  }

  const handleTestDetectionProvider = async () => {
    setTestingDetection(true)
    try {
      const result = await mockApi.testDetectionProvider()
      setTestMessage(`Status: ${result.status}, latency ${result.latency} ms`)
      refreshDetectionConfig()
      refreshDetectionLogs()
    } catch (error) {
      console.error(error)
      setTestMessage('Detection provider test failed.')
    } finally {
      setTestingDetection(false)
      setTimeout(() => setTestMessage(undefined), 5000)
    }
  }

  const handleRefreshDetection = () => {
    refreshDetectionConfig()
    refreshDetectionLogs()
  }

  const handleRefreshOdoo = () => {
    refreshOdooConfig()
    refreshOdooLog()
  }

  const handleRoleChange = async (userId: string, roleId: string) => {
    await mockApi.updateUserAccount(userId, { roleId })
    setStatusMessage(`Updated role for ${userId}.`)
    refreshUsers()
  }

  const odooFormState = (odooForm ?? odooConfig) ?? {
    baseUrl: '',
    database: '',
    company: '',
    apiKey: '',
    autoSync: false,
    status: 'disconnected',
    pendingCount: 0,
    failureCount: 0,
  }

  const detectionFormState = (detectionForm ?? detectionConfig) ?? {
    providerName: '',
    endpoint: '',
    apiKey: '',
    enabled: false,
    status: 'offline',
    averageLatencyMs: 0,
    lastHeartbeat: undefined,
  }

const cameraCount = useMemo(() => cameras?.length ?? 0, [cameras])

  return (
    <div className="space-y-6">
      {statusMessage ? (
        <div className="rounded-lg border border-accent/40 bg-accent/10 px-4 py-2 text-sm text-accent">
          {statusMessage}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Card padding="sm" className="border-slate-800/70">
          <form className="space-y-4" onSubmit={handleOdooConfigSubmit}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-accent/30 bg-slate-900/70 text-accent shadow-glow">
                  <PlugZap className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    Odoo Integration
                  </p>
                  <h2 className="text-lg font-semibold text-white">
                    {odooConfig?.company ?? 'Odoo Platform'}
                  </h2>
                </div>
              </div>
              <Badge tone={odooStatusTone[odooConfig?.status ?? 'error']} soft>
                {odooConfig?.status ?? 'disconnected'}
              </Badge>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Base URL
                </span>
                <input
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={odooFormState.baseUrl}
                  onChange={(event) =>
                    setOdooForm((prev) => ({
                      ...(prev ?? odooFormState),
                      baseUrl: event.target.value,
                    }))
                  }
                  placeholder="https://odoo.example.com"
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Database
                </span>
                <input
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={odooFormState.database}
                  onChange={(event) =>
                    setOdooForm((prev) => ({
                      ...(prev ?? odooFormState),
                      database: event.target.value,
                    }))
                  }
                  placeholder="odoo_db"
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Company
                </span>
                <input
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={odooFormState.company}
                  onChange={(event) =>
                    setOdooForm((prev) => ({
                      ...(prev ?? odooFormState),
                      company: event.target.value,
                    }))
                  }
                  placeholder="Sentinel Vision"
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  API Key
                </span>
                <input
                  type="password"
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={odooFormState.apiKey ?? ''}
                  onChange={(event) =>
                    setOdooForm((prev) => ({
                      ...(prev ?? odooFormState),
                      apiKey: event.target.value,
                    }))
                  }
                  placeholder="********"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 text-xs uppercase tracking-[0.35em] text-slate-500">
              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={odooFormState.autoSync}
                  onChange={(event) =>
                    setOdooForm((prev) => ({
                      ...(prev ?? odooFormState),
                      autoSync: event.target.checked,
                    }))
                  }
                  className="h-4 w-4 rounded border border-slate-700 bg-slate-900 text-accent focus:ring-accent"
                />
                Auto sync attendance
              </label>
              <span>Pending: {odooConfig?.pendingCount ?? 0}</span>
              <span className="text-amber-300">Failures: {odooConfig?.failureCount ?? 0}</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                icon={<PlugZap className="h-4 w-4" />}
                disabled={odooSaving}
              >
                {odooSaving ? 'Saving...' : 'Save Changes'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                icon={<RefreshCw className="h-4 w-4" />}
                onClick={handleRefreshOdoo}
              >
                Refresh
              </Button>
            </div>
          </form>

          <div className="mt-6 space-y-3">
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Recent sync feedback
            </p>
            <div className="space-y-2">
              {(odooSyncLog ?? []).slice(0, 5).map((entry) => (
                <div
                  key={entry.id}
                  className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-xs text-slate-300"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-slate-500">
                      {formatTimestamp(entry.timestamp, { withDate: false })}
                    </span>
                    <Badge tone={entry.result === 'success' ? 'success' : 'danger'} soft>
                      {entry.result}
                    </Badge>
                  </div>
                  <p className="mt-1 text-slate-200">
                    {entry.employeeId} - {entry.message}
                  </p>
                </div>
              ))}
              {(odooSyncLog ?? []).length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/60 px-4 py-6 text-center text-xs text-slate-500">
                  No sync activity recorded yet.
                </div>
              ) : null}
            </div>
          </div>
        </Card>

        <Card padding="sm" className="border-slate-800/70">
          <form className="space-y-4" onSubmit={handleDetectionConfigSubmit}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-700/80 bg-slate-900/70 text-sky-300">
                  <Radio className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    Detection Provider
                  </p>
                  <h2 className="text-lg font-semibold text-white">
                    {detectionConfig?.providerName ?? 'External API'}
                  </h2>
                </div>
              </div>
              <Badge tone={detectionStatusTone[detectionConfig?.status ?? 'offline']} soft>
                {detectionConfig?.status ?? 'offline'}
              </Badge>
            </div>

            <div className="grid gap-3">
              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Provider name
                </span>
                <input
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={detectionFormState.providerName}
                  onChange={(event) =>
                    setDetectionForm((prev) => ({
                      ...(prev ?? detectionFormState),
                      providerName: event.target.value,
                    }))
                  }
                  placeholder="VisionGrid AI"
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Endpoint
                </span>
                <input
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={detectionFormState.endpoint}
                  onChange={(event) =>
                    setDetectionForm((prev) => ({
                      ...(prev ?? detectionFormState),
                      endpoint: event.target.value,
                    }))
                  }
                  placeholder="https://api.provider.com/v1/detect"
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  API Key
                </span>
                <input
                  type="password"
                  className="w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
                  value={detectionFormState.apiKey ?? ''}
                  onChange={(event) =>
                    setDetectionForm((prev) => ({
                      ...(prev ?? detectionFormState),
                      apiKey: event.target.value,
                    }))
                  }
                  placeholder="********"
                />
              </label>

              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={detectionFormState.enabled}
                  onChange={(event) =>
                    setDetectionForm((prev) => ({
                      ...(prev ?? detectionFormState),
                      enabled: event.target.checked,
                    }))
                  }
                  className="h-4 w-4 rounded border border-slate-700 bg-slate-900 text-accent focus:ring-accent"
                />
                Provider enabled
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                icon={<Radio className="h-4 w-4" />}
                disabled={detectionSaving}
              >
                {detectionSaving ? 'Saving...' : 'Save Changes'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                icon={<RefreshCw className="h-4 w-4" />}
                onClick={handleRefreshDetection}
              >
                Refresh
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                icon={<History className="h-4 w-4" />}
                onClick={handleTestDetectionProvider}
                disabled={testingDetection}
              >
                {testingDetection ? 'Testing...' : 'Test Connection'}
              </Button>
            </div>
          </form>

          <div className="mt-4 space-y-3 text-xs text-slate-400">
            <div className="flex items-center justify-between">
              <span>
                Last heartbeat:{' '}
                {detectionConfig?.lastHeartbeat
                  ? formatTimestamp(detectionConfig.lastHeartbeat, { withDate: false })
                  : '-'}
              </span>
              <span>Avg latency: {detectionConfig?.averageLatencyMs ?? 0} ms</span>
            </div>
            {testMessage ? (
              <div className="rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-accent">
                {testMessage}
              </div>
            ) : null}
            <div className="space-y-2">
              {(detectionLogs ?? []).slice(0, 5).map((entry) => (
                <div
                  key={entry.id}
                  className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-xs text-slate-300"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-slate-500">
                      {formatTimestamp(entry.timestamp, { withDate: false })}
                    </span>
                    <Badge tone={entry.status === 'error' ? 'danger' : 'info'} soft>
                      {entry.status}
                    </Badge>
                  </div>
                  <p className="mt-1 text-slate-200">
                    {entry.cameraName} - {entry.status === 'error' ? ((entry.payload as { error?: string })?.error ?? 'Detection provider error') : 'Detection payload received'}
                  </p>
                </div>
              ))}
              {(detectionLogs ?? []).length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/60 px-4 py-6 text-center text-xs text-slate-500">
                  No detection events captured yet.
                </div>
              ) : null}
            </div>
          </div>
        </Card>
      </div>

      <Card padding="sm" className="border-slate-800/70">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Camera Provisioning
            </p>
            <h1 className="text-xl font-semibold text-white">
              Stream Configuration
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({cameraCount} registered)
              </span>
            </h1>
          </div>
          <Badge tone={camerasLoading ? 'warning' : 'info'} soft>
            {camerasLoading ? 'Syncing cameras' : 'Up to date'}
          </Badge>
        </div>

        <form
          onSubmit={handleCameraSubmit}
          className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1.4fr_1fr_1fr_0.7fr]"
        >
          <input
            placeholder="Camera ID"
            value={cameraForm.id}
            onChange={(event) => setCameraForm((prev) => ({ ...prev, id: event.target.value }))}
            className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
          <input
            placeholder="Name"
            value={cameraForm.name}
            onChange={(event) => setCameraForm((prev) => ({ ...prev, name: event.target.value }))}
            className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
          <input
            placeholder="Location"
            value={cameraForm.location}
            onChange={(event) =>
              setCameraForm((prev) => ({ ...prev, location: event.target.value }))
            }
            className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
          <select
            value={cameraForm.streamType}
            onChange={(event) =>
              setCameraForm((prev) => ({
                ...prev,
                streamType: event.target.value as StreamType,
              }))
            }
            className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
          >
            <option value="RTSP">RTSP</option>
            <option value="USB">USB</option>
            <option value="HTTP">HTTP</option>
            <option value="Socket">Socket</option>
            <option value="Local File">Local File</option>
          </select>
          <Button type="submit" icon={<Plus className="h-4 w-4" />}>
            Add Camera
          </Button>
        </form>
        <input
          placeholder="Stream URL / path"
          value={cameraForm.streamUrl}
          onChange={(event) =>
            setCameraForm((prev) => ({ ...prev, streamUrl: event.target.value }))
          }
          className="mt-3 w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
        />
      </Card>

      <Card padding="sm" className="border-slate-800/70">
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Camera Directory</p>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {cameras?.map((camera) => (
            <div
              key={camera.id}
              className="flex flex-col gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">{camera.name}</h3>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {camera.id} | {camera.location}
                  </p>
                </div>
                <Badge tone={camera.enabled ? 'success' : 'warning'} soft>
                  {camera.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span>{camera.streamType}</span>
                <span className="font-mono text-[11px] text-slate-300">{camera.streamUrl}</span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleToggleCamera(camera)}
                >
                  {camera.enabled ? 'Disable' : 'Enable'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Network className="h-4 w-4" />}
                  onClick={() => handleTestConnection(camera)}
                >
                  Test
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-auto text-rose-400 hover:text-rose-200"
                  icon={<Trash className="h-4 w-4" />}
                  onClick={() => handleDeleteCamera(camera.id)}
                >
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <Card padding="sm" className="border-slate-800/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">User Directory</p>
              <h2 className="text-xl font-semibold text-white">Role Assignments</h2>
            </div>
            <Badge tone="info" soft>
              {users?.length ?? 0} users
            </Badge>
          </div>
          <div className="mt-4 space-y-3">
            {users?.map((user) => (
              <div
                key={user.id}
                className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-3"
              >
                <div className="flex-1">
                  <p className="text-sm font-semibold text-white">{user.name}</p>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {user.email}
                  </p>
                </div>
                <select
                  value={user.roleId}
                  onChange={(event) => handleRoleChange(user.id, event.target.value)}
                  className="rounded-lg border border-slate-700/60 bg-slate-900/60 px-2 py-1 text-sm text-white outline-none focus:border-accent"
                >
                  {roles?.map((role) => (
                    <option key={role.id} value={role.id} className="bg-slate-900 text-white">
                      {role.name}
                    </option>
                  ))}
                </select>
                <Badge tone={user.status === 'active' ? 'success' : 'warning'} soft>
                  {user.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="sm" className="border-slate-800/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Backup & Restore
              </p>
              <h2 className="text-lg font-semibold text-white">Configuration Payload</h2>
            </div>
            <Badge tone="info" soft>
              JSON snapshot
            </Badge>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" icon={<CloudDownload className="h-4 w-4" />} onClick={handleBackup}>
              Backup
            </Button>
            <Button variant="outline" size="sm" icon={<CloudUpload className="h-4 w-4" />} onClick={handleRestore}>
              Restore
            </Button>
          </div>
          <textarea
            value={configPreview}
            onChange={(event) => setConfigPreview(event.target.value)}
            className="mt-3 h-40 w-full rounded-lg border border-slate-800/60 bg-slate-950/60 p-3 font-mono text-sm text-slate-200 outline-none focus:border-accent"
            placeholder="Camera JSON configuration will appear here after backup."
          />
        </Card>
      </div>

      <Card padding="sm" className="border-slate-800/70">
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Role Matrix</p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {roles?.map((role) => (
            <div key={role.id} className="rounded-lg border border-slate-800/60 bg-slate-900/60 p-3">
              <h3 className="text-lg font-semibold text-white">{role.name}</h3>
              <p className="mt-2 text-sm text-slate-400">{role.description}</p>
              <ul className="mt-3 space-y-1 text-xs uppercase tracking-[0.35em] text-slate-500">
                {role.permissions.map((permission) => (
                  <li key={permission} className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                    {permission.replace(/-/g, ' ')}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}




