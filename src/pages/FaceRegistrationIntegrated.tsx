/**
 * Face Registration - Integrated with Backend API
 * Enroll face encodings for persons with webcam capture
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import {
  Camera,
  Plus,
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  Trash2,
  Star,
  X,
} from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { useNotification } from '@/context/NotificationContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import type { FaceProfile } from '@/types'

interface CapturedFrame {
  dataUrl: string
  timestamp: Date
}

interface EnrolledFace {
  encoding_id: string
  confidence: number
  is_primary: boolean
  quality_score: number
  created_at: string
}

export const FaceRegistrationIntegratedPage = () => {
  const { addNotification } = useNotification()

  // State
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [persons, setPersons] = useState<FaceProfile[]>([])
  const [selectedPerson, setSelectedPerson] = useState<FaceProfile | null>(null)
  const [enrolledFaces, setEnrolledFaces] = useState<EnrolledFace[]>([])

  // Webcam state
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [cameraActive, setCameraActive] = useState(false)
  const [capturedFrames, setCapturedFrames] = useState<CapturedFrame[]>([])
  const [selectedFrameIndex, setSelectedFrameIndex] = useState<number | null>(null)

  // Form state
  const [showEnrollForm, setShowEnrollForm] = useState(false)
  const [enrollData, setEnrollData] = useState({
    isPrimary: false,
    qualityScore: 0.9,
  })

  // Fetch persons
  const fetchPersons = useCallback(async () => {
    try {
      setLoading(true)
      const response = await apiClient.getPersons(1, 100)
      setPersons(response.data)
    } catch (err) {
      console.error('Failed to fetch persons:', err)
      addNotification('error', 'Failed to load persons')
    } finally {
      setLoading(false)
    }
  }, [addNotification])

  // Initialize camera
  const initializeCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setCameraActive(true)
      }
    } catch (err) {
      console.error('Camera access error:', err)
      addNotification('error', 'Camera access denied', 'Please enable camera permissions')
    }
  }, [addNotification])

  // Stop camera
  const stopCamera = useCallback(() => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach((track) => track.stop())
      setCameraActive(false)
    }
  }, [])

  // Capture frame from video
  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return

    const context = canvasRef.current.getContext('2d')
    if (!context) return

    canvasRef.current.width = videoRef.current.videoWidth
    canvasRef.current.height = videoRef.current.videoHeight

    context.drawImage(videoRef.current, 0, 0)
    const dataUrl = canvasRef.current.toDataURL('image/jpeg', 0.9)

    setCapturedFrames((prev) => [
      ...prev,
      {
        dataUrl,
        timestamp: new Date(),
      },
    ])

    addNotification('success', 'Frame captured', '', 2000)
  }, [addNotification])

  // Remove captured frame
  const removeFrame = (index: number) => {
    setCapturedFrames((prev) => prev.filter((_, i) => i !== index))
    if (selectedFrameIndex === index) {
      setSelectedFrameIndex(null)
    }
  }

  // Enroll face
  const handleEnrollFace = async () => {
    if (!selectedPerson || selectedFrameIndex === null) {
      addNotification('error', 'Please select person and capture a frame')
      return
    }

    const frame = capturedFrames[selectedFrameIndex]
    if (!frame) return

    try {
      setSyncing(true)

      // Remove data URL prefix to get base64
      const base64Data = frame.dataUrl.split(',')[1]

      const response = await apiClient.enrollFace(
        selectedPerson.id,
        base64Data,
        enrollData.isPrimary,
        enrollData.qualityScore
      )

      addNotification(
        'success',
        'Face enrolled successfully',
        `Confidence: ${(response.data.confidence * 100).toFixed(1)}%`
      )

      // Refresh enrolled faces
      setEnrolledFaces((prev) => [
        ...prev,
        {
          encoding_id: response.data.encoding_id,
          confidence: response.data.confidence,
          is_primary: response.data.is_primary,
          quality_score: response.data.quality_score,
          created_at: new Date().toISOString(),
        },
      ])

      // Update person's face count
      setPersons((prev) =>
        prev.map((p) =>
          p.id === selectedPerson.id
            ? { ...p, face_encoding_count: (p.face_encoding_count || 0) + 1 }
            : p
        )
      )

      // Reset form
      removeFrame(selectedFrameIndex)
      setEnrollData({ isPrimary: false, qualityScore: 0.9 })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Enrollment failed'
      addNotification('error', 'Enrollment failed', message)
    } finally {
      setSyncing(false)
    }
  }

  // Search person by face
  const handleSearchByFace = async () => {
    if (selectedFrameIndex === null) {
      addNotification('error', 'Please capture a frame first')
      return
    }

    const frame = capturedFrames[selectedFrameIndex]
    if (!frame) return

    try {
      setSyncing(true)
      const base64Data = frame.dataUrl.split(',')[1]

      const response = await apiClient.searchByFace(base64Data, 0.6)

      if (response.data.matched && response.data.best_match) {
        const person = persons.find((p) => p.id === response.data.best_match?.person_id)
        if (person) {
          setSelectedPerson(person)
          addNotification(
            'success',
            `Found: ${response.data.best_match.first_name} ${response.data.best_match.last_name}`,
            `Confidence: ${(response.data.best_match.confidence * 100).toFixed(1)}%`
          )
        }
      } else {
        addNotification('warning', 'No matching person found', 'Check confidence threshold')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed'
      addNotification('error', 'Face search failed', message)
    } finally {
      setSyncing(false)
    }
  }

  // Select person
  const selectPerson = (person: FaceProfile) => {
    setSelectedPerson(person)
    setEnrolledFaces([]) // Reset enrolled faces list
  }

  // Initial fetch
  useEffect(() => {
    fetchPersons()
  }, [fetchPersons])

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      if (cameraActive) {
        stopCamera()
      }
    }
  }, [cameraActive, stopCamera])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Face Registration</h1>
        <p className="mt-2 text-slate-400">Enroll and manage face encodings for persons</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Person Selection */}
        <div className="lg:col-span-1">
          <Card className="border-slate-800/70">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">Select Person</h2>
              <p className="text-sm text-slate-400">Choose person to enroll faces</p>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                </div>
              ) : persons.length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 p-4 text-center text-sm text-slate-400">
                  No persons available
                </div>
              ) : (
                persons.map((person) => (
                  <button
                    key={person.id}
                    onClick={() => selectPerson(person)}
                    className={`w-full rounded-lg border-2 p-3 text-left transition ${
                      selectedPerson?.id === person.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-slate-700 bg-slate-900/50 hover:border-slate-600'
                    }`}
                  >
                    <p className="font-medium text-white">
                      {person.first_name} {person.last_name}
                    </p>
                    <p className="text-xs text-slate-400">{person.email}</p>
                    <div className="mt-2 flex items-center justify-between">
                      <Badge tone="info" soft>
                        {person.person_type}
                      </Badge>
                      <span className="text-xs text-slate-400">
                        {person.face_encoding_count || 0} faces
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Webcam Capture */}
        <div className="lg:col-span-2">
          <Card className="border-slate-800/70">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">Capture Face</h2>
                <p className="text-sm text-slate-400">Use webcam to capture face</p>
              </div>
              {cameraActive ? (
                <Button
                  onClick={stopCamera}
                  variant="outline"
                  icon={<X className="h-4 w-4" />}
                >
                  Stop Camera
                </Button>
              ) : (
                <Button
                  onClick={initializeCamera}
                  icon={<Camera className="h-4 w-4" />}
                >
                  Start Camera
                </Button>
              )}
            </div>

            {/* Video Feed */}
            {cameraActive && (
              <div className="mb-4 rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full aspect-video object-cover"
                />
              </div>
            )}

            {/* Hidden Canvas */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Capture Button */}
            {cameraActive && (
              <div className="mb-4 flex gap-2">
                <Button
                  onClick={captureFrame}
                  icon={<Camera className="h-4 w-4" />}
                  variant="primary"
                  className="flex-1"
                >
                  Capture Frame
                </Button>
                <Button
                  onClick={handleSearchByFace}
                  disabled={selectedFrameIndex === null || syncing}
                  variant="outline"
                  className="flex-1"
                >
                  Search by Face
                </Button>
              </div>
            )}

            {/* Captured Frames */}
            {capturedFrames.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-white">Captured Frames ({capturedFrames.length})</h3>
                <div className="grid grid-cols-4 gap-2">
                  {capturedFrames.map((frame, index) => (
                    <div
                      key={index}
                      onClick={() => setSelectedFrameIndex(index)}
                      className={`relative rounded-lg border-2 overflow-hidden cursor-pointer transition ${
                        selectedFrameIndex === index
                          ? 'border-blue-500'
                          : 'border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <img
                        src={frame.dataUrl}
                        alt={`Frame ${index + 1}`}
                        className="w-full aspect-square object-cover"
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          removeFrame(index)
                        }}
                        className="absolute top-1 right-1 rounded-full bg-red-500/80 hover:bg-red-600 p-1"
                      >
                        <X className="h-3 w-3 text-white" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Enrollment Form */}
      {selectedPerson && selectedFrameIndex !== null && (
        <Card className="border-slate-800/70">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Left: Selected Frame */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Selected Frame</h3>
              <img
                src={capturedFrames[selectedFrameIndex].dataUrl}
                alt="Selected frame"
                className="w-full rounded-lg border border-slate-700"
              />
              <p className="mt-2 text-xs text-slate-400">
                {capturedFrames[selectedFrameIndex].timestamp.toLocaleTimeString()}
              </p>
            </div>

            {/* Right: Enrollment Details */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Enrollment Details</h3>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Selected Person
                  </label>
                  <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
                    <p className="font-medium text-white">
                      {selectedPerson.first_name} {selectedPerson.last_name}
                    </p>
                    <p className="text-sm text-slate-400">{selectedPerson.email}</p>
                  </div>
                </div>

                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enrollData.isPrimary}
                      onChange={(e) =>
                        setEnrollData((prev) => ({ ...prev, isPrimary: e.target.checked }))
                      }
                      className="rounded border-slate-600"
                    />
                    <span className="text-sm font-medium text-slate-300">
                      Set as primary face
                    </span>
                  </label>
                  <p className="mt-1 text-xs text-slate-500">
                    Primary face is used for matching and search
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Quality Score: {(enrollData.qualityScore * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={enrollData.qualityScore}
                    onChange={(e) =>
                      setEnrollData((prev) => ({
                        ...prev,
                        qualityScore: parseFloat(e.target.value),
                      }))
                    }
                    className="w-full"
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Adjust quality score based on face clarity
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleEnrollFace}
                  disabled={syncing || !selectedPerson}
                  icon={syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  variant="primary"
                  className="flex-1"
                >
                  {syncing ? 'Enrolling...' : 'Enroll Face'}
                </Button>
              </div>
            </div>
          </div>

          {/* Enrolled Faces */}
          {enrolledFaces.length > 0 && (
            <div className="mt-6 pt-6 border-t border-slate-800">
              <h3 className="text-lg font-semibold text-white mb-4">Enrolled Faces</h3>
              <div className="space-y-2">
                {enrolledFaces.map((face, index) => (
                  <div
                    key={face.encoding_id}
                    className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <div>
                        <p className="text-sm font-medium text-white">Face #{index + 1}</p>
                        <p className="text-xs text-slate-400">
                          Confidence: {(face.confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    {face.is_primary && <Star className="h-5 w-5 text-yellow-500" />}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Instructions */}
      <Card className="border-slate-800/70 bg-blue-500/5 border-blue-500/30">
        <div className="flex gap-3">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-blue-500 mt-0.5" />
          <div>
            <h3 className="font-semibold text-white">Tips for Best Results</h3>
            <ul className="mt-2 text-sm text-slate-300 space-y-1">
              <li>• Ensure good lighting on the face</li>
              <li>• Face should be clear and directly facing camera</li>
              <li>• Avoid shadows or tilting head too much</li>
              <li>• Enroll multiple faces for better recognition accuracy</li>
              <li>• Quality score should be 0.8 or higher for best results</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}
