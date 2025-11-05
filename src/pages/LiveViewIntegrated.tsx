/**
 * Live Camera View - Integrated with Backend Detection API
 * Real-time camera stream with face detection overlay
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import {
  Play,
  Pause,
  Camera,
  Download,
  RefreshCw,
  Loader2,
  AlertCircle,
  Eye,
  Settings,
} from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { getWebSocketService, type DetectionEvent } from '@/services/websocket'
import { useNotification } from '@/context/NotificationContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface CameraStreamOptions {
  cameraId: string
  autoPlay: boolean
  fps: number
  qualityLevel: 'high' | 'medium' | 'low'
}

interface DetectionRecord {
  id: string
  person_id?: string
  person_name?: string
  confidence: number
  timestamp: string
  location?: {
    x: number
    y: number
    width: number
    height: number
  }
}

export const LiveViewIntegratedPage = () => {
  const { addNotification } = useNotification()

  // State
  const [loading, setLoading] = useState(true)
  const [streaming, setStreaming] = useState(false)
  const [cameras, setCameras] = useState<any[]>([])
  const [selectedCameraId, setSelectedCameraId] = useState<string>('')
  const [detections, setDetections] = useState<DetectionRecord[]>([])
  const [showStats, setShowStats] = useState(true)

  // Stream options
  const [streamOptions, setStreamOptions] = useState<CameraStreamOptions>({
    cameraId: '',
    autoPlay: true,
    fps: 30,
    qualityLevel: 'high',
  })

  // Refs
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const animationFrameRef = useRef<number | null>(null)

  // Fetch cameras
  const fetchCameras = useCallback(async () => {
    try {
      setLoading(true)
      const response = await apiClient.getCameras()
      const cameraList = Array.isArray(response.data) ? response.data : []
      setCameras(cameraList)

      if (cameraList.length > 0 && !selectedCameraId) {
        setSelectedCameraId(cameraList[0].id)
        setStreamOptions((prev) => ({ ...prev, cameraId: cameraList[0].id }))
      }
    } catch (err) {
      console.error('Failed to fetch cameras:', err)
      addNotification('error', 'Failed to load cameras')
    } finally {
      setLoading(false)
    }
  }, [selectedCameraId, addNotification])

  // Fetch recent detections
  const fetchDetections = useCallback(async (cameraId: string) => {
    try {
      const response = await apiClient.getDetections(1, 50, {
        cameraId: cameraId,
      })
      setDetections(response.data)
    } catch (err) {
      console.error('Failed to fetch detections:', err)
    }
  }, [])

  // Handle detection events via WebSocket
  const handleDetectionEvent = useCallback((event: DetectionEvent) => {
    // Add to detection list
    const detection: DetectionRecord = {
      id: `detection_${Date.now()}`,
      person_id: event.person_id,
      person_name: event.person_name,
      confidence: event.confidence,
      timestamp: event.event_timestamp,
      location: event.face_location,
    }

    setDetections((prev) => [detection, ...prev].slice(0, 20))

    // Show notification for new detection
    if (event.person_id && event.person_name) {
      addNotification(
        'info',
        `Detected: ${event.person_name}`,
        `Confidence: ${(event.confidence * 100).toFixed(1)}%`,
        2000
      )
    }
  }, [addNotification])

  // Initialize WebSocket for detections
  useEffect(() => {
    const ws = getWebSocketService()

    const connectWebSocket = async () => {
      try {
        await ws.connect('/api/v1/detections/ws', {
          camera_id: selectedCameraId,
          min_confidence: 0.6,
        })
      } catch (err) {
        console.error('WebSocket connection failed:', err)
      }
    }

    if (selectedCameraId) {
      connectWebSocket()
      const unsubscribe = ws.onDetectionEvent(handleDetectionEvent)
      return () => {
        unsubscribe()
      }
    }
  }, [selectedCameraId, handleDetectionEvent])

  // Initialize cameras on mount
  useEffect(() => {
    fetchCameras()
  }, [fetchCameras])

  // Fetch detections when camera changes
  useEffect(() => {
    if (selectedCameraId) {
      fetchDetections(selectedCameraId)
    }
  }, [selectedCameraId, fetchDetections])

  // Load camera stream
  const loadCameraStream = useCallback(async () => {
    if (!selectedCameraId || !videoRef.current) return

    try {
      setStreaming(true)

      // Construct stream URL (backend should provide proxy)
      const streamUrl = `${import.meta.env.VITE_API_BASE_URL}/api/v1/cameras/${selectedCameraId}/stream`

      // Try to load the video stream
      videoRef.current.src = streamUrl
      videoRef.current.play().catch((err) => {
        console.error('Failed to play stream:', err)
        addNotification(
          'error',
          'Failed to load camera stream',
          'Check camera is online and accessible'
        )
        setStreaming(false)
      })
    } catch (err) {
      console.error('Stream load error:', err)
      addNotification('error', 'Failed to load camera stream')
      setStreaming(false)
    }
  }, [selectedCameraId, addNotification])

  // Draw detection rectangles on canvas
  const drawDetections = useCallback(() => {
    const canvas = canvasRef.current
    const video = videoRef.current

    if (!canvas || !video || video.videoWidth === 0) {
      if (animationFrameRef.current) {
        animationFrameRef.current = requestAnimationFrame(drawDetections)
      }
      return
    }

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw recent detections
    detections.forEach((detection) => {
      if (!detection.location) return

      const { x, y, width, height } = detection.location
      const confidence = detection.confidence

      // Draw bounding box
      ctx.strokeStyle = confidence > 0.8 ? '#10b981' : confidence > 0.7 ? '#f59e0b' : '#ef4444'
      ctx.lineWidth = 3
      ctx.strokeRect(x, y, width, height)

      // Draw label background
      const label = detection.person_name || 'Unknown'
      const confidenceText = `${(confidence * 100).toFixed(0)}%`
      const text = `${label} (${confidenceText})`

      ctx.font = 'bold 14px Arial'
      ctx.fillStyle = ctx.strokeStyle
      const textMetrics = ctx.measureText(text)
      const textHeight = 20

      ctx.fillRect(x, y - textHeight - 5, textMetrics.width + 10, textHeight)

      // Draw text
      ctx.fillStyle = '#ffffff'
      ctx.fillText(text, x + 5, y - 8)
    })

    // Continue animation
    if (streaming) {
      animationFrameRef.current = requestAnimationFrame(drawDetections)
    }
  }, [detections, streaming])

  // Update canvas when detections change
  useEffect(() => {
    if (streaming && animationFrameRef.current === null) {
      animationFrameRef.current = requestAnimationFrame(drawDetections)
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }
    }
  }, [streaming, detections, drawDetections])

  // Start/stop streaming
  const toggleStreaming = () => {
    if (streaming) {
      if (videoRef.current) {
        videoRef.current.pause()
      }
      setStreaming(false)
    } else {
      loadCameraStream()
    }
  }

  // Screenshot
  const captureScreenshot = () => {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) {
      addNotification('error', 'No active stream to capture')
      return
    }

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.drawImage(video, 0, 0)
      const url = canvas.toDataURL('image/jpeg')
      const link = document.createElement('a')
      link.href = url
      link.download = `capture_${Date.now()}.jpg`
      link.click()
      addNotification('success', 'Screenshot saved', '', 2000)
    }
  }

  const selectedCamera = cameras.find((c) => c.id === selectedCameraId)
  const recentDetectionCount = detections.length
  const identifiedPersonCount = detections.filter((d) => d.person_id).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Live Camera View</h1>
          <p className="mt-2 text-slate-400">Real-time detection with face recognition overlay</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setShowStats(!showStats)}
            icon={<Eye className="h-4 w-4" />}
            variant="outline"
          >
            {showStats ? 'Hide' : 'Show'} Stats
          </Button>
          <Button
            onClick={captureScreenshot}
            icon={<Download className="h-4 w-4" />}
            variant="outline"
            disabled={!streaming}
          >
            Screenshot
          </Button>
        </div>
      </div>

      {/* Camera Selection */}
      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      ) : cameras.length === 0 ? (
        <Card className="border-slate-800/70 bg-yellow-500/5 border-yellow-500/30">
          <div className="flex gap-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-yellow-500 mt-0.5" />
            <div>
              <h3 className="font-semibold text-white">No Cameras Found</h3>
              <p className="text-sm text-slate-300 mt-1">
                Please configure cameras in the Camera Management section first.
              </p>
            </div>
          </div>
        </Card>
      ) : (
        <>
          {/* Camera Selection Dropdown */}
          <Card className="border-slate-800/70">
            <div className="flex items-end gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Select Camera
                </label>
                <select
                  value={selectedCameraId}
                  onChange={(e) => setSelectedCameraId(e.target.value)}
                  disabled={streaming}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
                >
                  <option value="">-- Select Camera --</option>
                  {cameras.map((camera) => (
                    <option key={camera.id} value={camera.id}>
                      {camera.name || camera.id} {camera.is_active ? '(Active)' : '(Inactive)'}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                onClick={toggleStreaming}
                disabled={!selectedCameraId}
                icon={
                  streaming ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )
                }
                variant={streaming ? 'outline' : 'primary'}
              >
                {streaming ? 'Stop Stream' : 'Start Stream'}
              </Button>

              <Button
                onClick={() => fetchDetections(selectedCameraId)}
                icon={<RefreshCw className="h-4 w-4" />}
                variant="outline"
              >
                Refresh
              </Button>
            </div>
          </Card>

          {/* Camera Stream Display */}
          <Card className="border-slate-800/70 relative overflow-hidden bg-black">
            <div className="relative w-full pt-[56.25%]">
              {/* Video element */}
              <video
                ref={videoRef}
                className="absolute inset-0 w-full h-full bg-black"
                controls={false}
                onLoadedMetadata={() => {
                  setStreaming(true)
                  drawDetections()
                }}
              />

              {/* Canvas overlay for detections */}
              <canvas
                ref={canvasRef}
                className="absolute inset-0 w-full h-full cursor-crosshair"
              />

              {/* Stream Status Badge */}
              <div className="absolute top-4 left-4 z-10">
                <Badge
                  tone={streaming ? 'success' : 'warning'}
                  soft
                  className="flex items-center gap-2"
                >
                  <span className={`w-2 h-2 rounded-full ${streaming ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                  {streaming ? 'LIVE' : 'OFFLINE'}
                </Badge>
              </div>

              {/* FPS Counter */}
              {streaming && (
                <div className="absolute top-4 right-4 z-10">
                  <Badge tone="info" soft>
                    {streamOptions.fps} FPS
                  </Badge>
                </div>
              )}

              {/* Camera Info Overlay */}
              {selectedCamera && (
                <div className="absolute bottom-4 left-4 z-10 text-sm text-white">
                  <p className="font-medium">{selectedCamera.name || 'Unnamed Camera'}</p>
                  <p className="text-slate-400 text-xs">{selectedCamera.location || 'No location info'}</p>
                </div>
              )}
            </div>
          </Card>

          {/* Stream Controls */}
          <Card className="border-slate-800/70">
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  FPS (Frames Per Second)
                </label>
                <input
                  type="range"
                  min="5"
                  max="60"
                  step="5"
                  value={streamOptions.fps}
                  onChange={(e) =>
                    setStreamOptions((prev) => ({ ...prev, fps: parseInt(e.target.value) }))
                  }
                  disabled={streaming}
                  className="w-full"
                />
                <span className="text-xs text-slate-400 mt-1 block">{streamOptions.fps} FPS</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Quality Level
                </label>
                <select
                  value={streamOptions.qualityLevel}
                  onChange={(e) =>
                    setStreamOptions((prev) => ({
                      ...prev,
                      qualityLevel: e.target.value as any,
                    }))
                  }
                  disabled={streaming}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white text-sm"
                >
                  <option value="low">Low (480p)</option>
                  <option value="medium">Medium (720p)</option>
                  <option value="high">High (1080p)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Detection Sensitivity
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="0.95"
                  step="0.05"
                  defaultValue="0.6"
                  className="w-full"
                  disabled={!streaming}
                />
                <span className="text-xs text-slate-400 mt-1 block">0.60 (Medium)</span>
              </div>
            </div>
          </Card>

          {/* Statistics Panel */}
          {showStats && (
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="border-blue-500/30 bg-blue-500/5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-400">Total Detections</p>
                    <p className="text-2xl font-bold text-white mt-2">{recentDetectionCount}</p>
                  </div>
                  <Camera className="h-8 w-8 text-blue-500" />
                </div>
              </Card>

              <Card className="border-green-500/30 bg-green-500/5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-400">Identified Persons</p>
                    <p className="text-2xl font-bold text-white mt-2">{identifiedPersonCount}</p>
                  </div>
                  <Eye className="h-8 w-8 text-green-500" />
                </div>
              </Card>

              <Card className="border-purple-500/30 bg-purple-500/5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-400">Stream Status</p>
                    <p className="text-lg font-semibold text-white mt-2">
                      {streaming ? (
                        <span className="text-green-400">● Live</span>
                      ) : (
                        <span className="text-yellow-400">● Offline</span>
                      )}
                    </p>
                  </div>
                  <Settings className="h-8 w-8 text-purple-500" />
                </div>
              </Card>
            </div>
          )}

          {/* Recent Detections List */}
          <Card className="border-slate-800/70">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Recent Detections</h2>
              <Badge tone="info" soft>
                {recentDetectionCount} events
              </Badge>
            </div>

            {recentDetectionCount === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 p-6 text-center text-sm text-slate-400">
                No detections yet. Start the stream to begin capturing.
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {detections.map((detection) => (
                  <div
                    key={detection.id}
                    className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">
                        {detection.person_name || 'Unknown Person'}
                      </p>
                      <p className="text-xs text-slate-400">
                        {new Date(detection.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <Badge
                      tone={
                        detection.confidence > 0.8
                          ? 'success'
                          : detection.confidence > 0.7
                            ? 'warning'
                            : 'danger'
                      }
                      soft
                    >
                      {(detection.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}

      {/* Help Card */}
      <Card className="border-slate-800/70 bg-blue-500/5 border-blue-500/30">
        <div className="flex gap-3">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-blue-500 mt-0.5" />
          <div className="text-sm">
            <h3 className="font-semibold text-white">How It Works</h3>
            <ul className="text-slate-300 mt-2 space-y-1">
              <li>• Select a camera from the dropdown list</li>
              <li>• Click "Start Stream" to begin viewing live feed</li>
              <li>• Face detections appear as colored rectangles with confidence scores</li>
              <li>• Green = High confidence (>80%), Yellow = Medium (>70%), Red = Low (<70%)</li>
              <li>• Recent detections are shown in the list below</li>
              <li>• Click "Screenshot" to save current frame as JPEG</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}
