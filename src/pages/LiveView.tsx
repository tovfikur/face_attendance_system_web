import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Airplay,
  Clock,
  Maximize,
  Monitor,
  Pause,
  Play,
  PlugZap,
  RefreshCw,
  Rows3,
  Rows4,
  Split,
} from 'lucide-react'
import type { Camera, CameraSummary, DetectionEventLog, DetectionProviderConfig, PersonDetection, StreamType } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { formatTimestamp } from '@/utils/formatters'
import { CameraStreamGrid } from '@/components/camera/CameraStreamGrid'
import { LiveStreamViewport } from '@/components/camera/LiveStreamViewport'
import { DetectionList } from '@/components/camera/DetectionList'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

const detectionStatusTone: Record<DetectionProviderConfig['status'], 'success' | 'warning' | 'danger'> = {
  connected: 'success',
  degraded: 'warning',
  offline: 'danger',
}

type GridMode = '2x2' | '3x3'
type ProtocolFilter = StreamType | 'ALL'

const protocolLabels: Record<ProtocolFilter, string> = {
  ALL: 'All Streams',
  RTSP: 'RTSP',
  USB: 'USB',
  HTTP: 'HTTP',
  Socket: 'Socket',
  'Local File': 'Local File',
}

export const LiveViewPage = () => {
  const { cameraId } = useParams<{ cameraId?: string }>()
  const navigate = useNavigate()
  const [gridMode, setGridMode] = useState<GridMode>('3x3')
  const [protocol, setProtocol] = useState<ProtocolFilter>('ALL')
  const [autoRotate, setAutoRotate] = useState(true)
  const [selectedCameraId, setSelectedCameraId] = useState<string | undefined>(cameraId)
  const [detectionMessage, setDetectionMessage] = useState<string>()
  const [sendingFrame, setSendingFrame] = useState(false)
  const [testingProvider, setTestingProvider] = useState(false)
  const fullscreenRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    setSelectedCameraId(cameraId)
  }, [cameraId])

  const {
    data: cameraList,
    refresh: refreshCameras,
    loading: camerasLoading,
  } = usePolling<Camera[]>({
    fetcher: () => mockApi.fetchCameras(),
    interval: 6500,
  })

  const { data: summaries } = usePolling<CameraSummary[]>({
    fetcher: () => mockApi.fetchCameraSummary(),
    interval: 12000,
  })

  const {
    data: detections,
    refresh: refreshDetections,
  } = usePolling<PersonDetection[]>({
    fetcher: () => mockApi.fetchLiveDetections(selectedCameraId),
    interval: 4000,
    immediate: Boolean(selectedCameraId),
  })

  const { data: detectionConfig, refresh: refreshDetectionConfig } = usePolling<DetectionProviderConfig>({
    fetcher: () => mockApi.fetchDetectionProviderConfig(),
    interval: 20000,
  })

  const { data: detectionLogs, refresh: refreshDetectionLogs } = usePolling<DetectionEventLog[]>({
    fetcher: () => mockApi.fetchDetectionEventLogs(12),
    interval: 20000,
  })

  useEffect(() => {
    if (selectedCameraId) {
      refreshDetections()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCameraId])

  const summaryMap = useMemo(() => {
    if (!summaries) return new Map<string, CameraSummary>()
    return new Map(summaries.map((summary) => [summary.id, summary]))
  }, [summaries])

  const detectionLogsToShow = useMemo(() => (detectionLogs ?? []).slice(0, 6), [detectionLogs])
  const detectionStatus = detectionConfig?.status ?? 'offline'

  const filteredCameras = useMemo(() => {
    if (!cameraList) return []
    if (protocol === 'ALL') return cameraList
    return cameraList.filter((camera) => camera.streamType === protocol)
  }, [cameraList, protocol])

  const selectedCamera = filteredCameras.find((camera) => camera.id === selectedCameraId) ??
    cameraList?.find((camera) => camera.id === selectedCameraId)

  const protocolBreakdown = useMemo(() => {
    if (!cameraList) return []
    const counts = new Map<ProtocolFilter, number>()
    counts.set('ALL', cameraList.length)
    cameraList.forEach((camera) => {
      counts.set(camera.streamType, (counts.get(camera.streamType) ?? 0) + 1)
    })
    return Array.from(counts.entries())
  }, [cameraList])

  useEffect(() => {
    if (!autoRotate || !cameraList || !cameraList.length) return undefined
    const timer = setInterval(() => {
      setSelectedCameraId((prev) => {
        if (!cameraList.length) return prev
        const index = prev ? cameraList.findIndex((camera) => camera.id === prev) : -1
        const nextCamera = cameraList[(index + 1) % cameraList.length]
        navigate(`/live/${nextCamera.id}`, { replace: true })
        return nextCamera.id
      })
    }, 20000)
    return () => clearInterval(timer)
  }, [autoRotate, cameraList, navigate])

  const handleSelectCamera = (id: string) => {
    setSelectedCameraId(id)
    navigate(`/live/${id}`)
  }

  const handleFullscreen = async () => {
    if (!fullscreenRef.current) return
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await fullscreenRef.current.requestFullscreen()
    }
  }

  const handleSendFrameForDetection = async () => {
    if (!selectedCameraId) {
      setDetectionMessage('Select a camera to send a frame for detection.')
      setTimeout(() => setDetectionMessage(undefined), 4000)
      return
    }
    setSendingFrame(true)
    try {
      const result = await mockApi.sendFrameForDetection(selectedCameraId)
      setDetectionMessage(`Frame processed: ${result.status}`)
      refreshDetectionLogs()
    } catch (error) {
      console.error(error)
      setDetectionMessage('Failed to send frame to detection provider.')
    } finally {
      setSendingFrame(false)
      setTimeout(() => setDetectionMessage(undefined), 5000)
    }
  }

  const handleTestDetectionProvider = async () => {
    setTestingProvider(true)
    try {
      const result = await mockApi.testDetectionProvider()
      setDetectionMessage(`Provider ${result.status} (${result.latency} ms)`)
      refreshDetectionConfig()
    } catch (error) {
      console.error(error)
      setDetectionMessage('Detection provider test failed.')
    } finally {
      setTestingProvider(false)
      setTimeout(() => setDetectionMessage(undefined), 5000)
    }
  }

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Multi-protocol Stream Matrix
            </p>
            <h1 className="text-xl font-semibold text-white">
              Live Monitoring Control
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({filteredCameras.length} active of {cameraList?.length ?? 0})
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={autoRotate ? 'primary' : 'ghost'}
              size="sm"
              icon={autoRotate ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              onClick={() => setAutoRotate((prev) => !prev)}
            >
              Auto-rotate
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={<Monitor className="h-4 w-4" />}
              onClick={() => refreshCameras()}
              disabled={camerasLoading}
            >
              Refresh Grid
            </Button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center rounded-lg border border-slate-800/60 bg-slate-900/60">
            <Button
              variant={gridMode === '2x2' ? 'primary' : 'ghost'}
              size="sm"
              className="rounded-r-none border-0 px-3"
              icon={<Rows3 className="h-4 w-4" />}
              onClick={() => setGridMode('2x2')}
            >
              2 x 2
            </Button>
            <Button
              variant={gridMode === '3x3' ? 'primary' : 'ghost'}
              size="sm"
              className="rounded-l-none border-0 px-3"
              icon={<Rows4 className="h-4 w-4" />}
              onClick={() => setGridMode('3x3')}
            >
              3 x 3
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {protocolBreakdown.map(([key, count]) => (
              <button
                key={key}
                type="button"
                onClick={() => setProtocol(key)}
                className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-[0.35em] transition ${
                  protocol === key
                    ? 'border-accent bg-accent/15 text-accent shadow-glow'
                    : 'border-slate-800/60 bg-slate-900/60 text-slate-400 hover:border-slate-700'
                }`}
              >
                <Split className="h-3.5 w-3.5" />
                {protocolLabels[key]}
                <Badge tone="info" soft>
                  {count}
                </Badge>
              </button>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-3 text-[11px] uppercase tracking-[0.35em] text-slate-500">
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4 text-sky-400" />
              Streams auto-sync every 6.5s
            </span>
            <span className="hidden items-center gap-1 md:flex">
              <Airplay className="h-4 w-4 text-emerald-400" />
              Cohort {cameraList ? cameraList.length : 0} feeds
            </span>
          </div>
        </div>
      </Card>

      {selectedCamera ? (
        <div className="grid gap-6 xl:grid-cols-[2.2fr_1fr]" ref={fullscreenRef}>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Focused Stream
                </p>
                <h2 className="text-lg font-semibold text-white">
                  {selectedCamera.name}{' '}
                  <span className="text-sm font-medium text-slate-400">
                    ({selectedCamera.streamType})
                  </span>
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="info" soft>
                  {mockActiveStreamsDescription(selectedCamera)}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Maximize className="h-4 w-4" />}
                  onClick={handleFullscreen}
                >
                  Fullscreen
                </Button>
              </div>
            </div>
            <LiveStreamViewport
              camera={selectedCamera}
              detections={detections ?? []}
            />
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="primary"
                size="sm"
                icon={<PlugZap className="h-4 w-4" />}
                onClick={handleSendFrameForDetection}
                disabled={sendingFrame}
              >
                {sendingFrame ? 'Sending...' : 'Send Frame to Provider'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                icon={<RefreshCw className="h-4 w-4" />}
                onClick={handleTestDetectionProvider}
                disabled={testingProvider}
              >
                {testingProvider ? 'Testing...' : 'Test Provider'}
              </Button>
            </div>
            {detectionMessage ? (
              <Badge tone="info" soft>
                {detectionMessage}
              </Badge>
            ) : null}
          </div>
          <div className="space-y-4">
            <DetectionList detections={detections ?? []} />
            <Card padding="sm" className="border-slate-800/70">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Detection Provider</p>
                  <h3 className="text-lg font-semibold text-white">
                    {detectionConfig?.providerName ?? 'External API'}
                  </h3>
                </div>
                <Badge tone={detectionStatusTone[detectionStatus]} soft>{detectionStatus}</Badge>
              </div>
              <div className="mt-3 grid gap-2 text-xs text-slate-400 md:grid-cols-2">
                <span>Avg latency: {detectionConfig?.averageLatencyMs ?? 0} ms</span>
                <span>Last heartbeat: {detectionConfig?.lastHeartbeat ? formatTimestamp(detectionConfig.lastHeartbeat, { withDate: false }) : '-'}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<RefreshCw className="h-4 w-4" />}
                  onClick={() => {
                    refreshDetectionConfig()
                    refreshDetectionLogs()
                  }}
                >
                  Refresh status
                </Button>
              </div>
              <div className="mt-4 space-y-2">
                {detectionLogsToShow.map((entry) => (
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
                      {entry.cameraName}
                    </p>
                  </div>
                ))}
                {detectionLogsToShow.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/60 px-4 py-4 text-center text-xs text-slate-500">
                    No detection events logged yet.
                  </div>
                ) : null}
              </div>
            </Card>
          </div>
        </div>
      ) : null}

      <Card padding="sm" className="border-slate-800/70">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Live Streams
            </p>
            <h2 className="text-xl font-semibold text-white">Concurrent Camera Grid</h2>
          </div>
          <Badge tone="info" soft>
            {filteredCameras.length} feeds showing
          </Badge>
        </div>

        <CameraStreamGrid
          cameras={filteredCameras}
          summaries={summaryMap}
          mode={gridMode}
          activeCameraId={selectedCameraId}
          onSelect={handleSelectCamera}
        />
      </Card>
    </div>
  )
}

const mockActiveStreamsDescription = (camera: Camera) => {
  switch (camera.streamType) {
    case 'RTSP':
      return 'RTSP stream with H.265 decoding'
    case 'USB':
      return 'USB UVC camera feed'
    case 'HTTP':
      return 'HTTP MJPEG stream'
    case 'Socket':
      return 'Socket ingest (WebRTC)'
    case 'Local File':
      return 'Local archival playback'
    default:
      return 'Live stream'
  }
}
