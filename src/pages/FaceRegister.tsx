import { useCallback, useMemo, useState } from 'react'
import type { FaceProfile, FaceRegistrationPayload } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { FaceRegistrationForm } from '@/components/faces/FaceRegistrationForm'
import { FaceGallery } from '@/components/faces/FaceGallery'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

const emptyPayload: FaceRegistrationPayload = {
  name: '',
  employeeId: '',
  department: '',
  images: [],
}

const simulatedCaptures = ['/assets/faces/unknown.svg', '/assets/faces/david-chen.svg']

export const FaceRegisterPage = () => {
  const [payload, setPayload] = useState<FaceRegistrationPayload>(emptyPayload)
  const [previewImages, setPreviewImages] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string>()
  const [validationErrors, setValidationErrors] = useState<
    Partial<Record<keyof FaceRegistrationPayload, string>>
  >({})

  const {
    data: profiles,
    refresh: refreshProfiles,
    loading,
  } = usePolling<FaceProfile[]>({
    fetcher: () => mockApi.fetchFaceProfiles(),
    interval: 12000,
  })

  const validate = useCallback(
    (values: FaceRegistrationPayload) => {
      const errors: Partial<Record<keyof FaceRegistrationPayload, string>> = {}
      if (!values.name.trim()) errors.name = 'Name is required.'
      if (!values.employeeId.trim()) errors.employeeId = 'Employee ID is required.'
      if (!values.department.trim()) errors.department = 'Department is required.'
      if (!values.images.length) errors.images = 'At least one image is required.'
      return errors
    },
    [],
  )

  const handleUpload = async (files: FileList | null) => {
    if (!files?.length) return
    const readers = Array.from(files).map(
      (file) =>
        new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result as string)
          reader.onerror = () => reject(reader.error)
          reader.readAsDataURL(file)
        }),
    )

    try {
      const images = await Promise.all(readers)
      setPreviewImages((prev) => [...prev, ...images])
      setPayload((prev) => ({
        ...prev,
        images: [...prev.images, ...images],
      }))
      setValidationErrors((prev) => ({ ...prev, images: undefined }))
    } catch {
      setStatusMessage('Unable to process one of the images.')
    }
  }

  const handleCapture = () => {
    const image = simulatedCaptures[Math.floor(Math.random() * simulatedCaptures.length)]
    setPreviewImages((prev) => [...prev, image])
    setPayload((prev) => ({
      ...prev,
      images: [...prev.images, image],
    }))
    setValidationErrors((prev) => ({ ...prev, images: undefined }))
  }

  const resetForm = () => {
    setPayload(emptyPayload)
    setPreviewImages([])
    setValidationErrors({})
    setStatusMessage(undefined)
  }

  const handleSubmit = async () => {
    const errors = validate(payload)
    setValidationErrors(errors)
    if (Object.keys(errors).length) {
      setStatusMessage('Please resolve highlighted errors before submitting.')
      return
    }

    try {
      setSubmitting(true)
      setStatusMessage('Submitting registration request...')
      await mockApi.registerFace(payload)
      setStatusMessage('Registration queued successfully for biometric sync.')
      resetForm()
      refreshProfiles()
    } catch {
      setStatusMessage('Registration failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleApprove = async (faceId: string) => {
    await mockApi.updateFaceProfile(faceId, { status: 'active' })
    setStatusMessage(`Face profile ${faceId} approved.`)
    refreshProfiles()
  }

  const handleDelete = async (faceId: string) => {
    await mockApi.deleteFaceProfile(faceId)
    setStatusMessage(`Face profile ${faceId} removed.`)
    refreshProfiles()
  }

  const profileCount = useMemo(() => profiles?.length ?? 0, [profiles])

  return (
    <div className="space-y-6">
      <FaceRegistrationForm
        payload={payload}
        previewImages={previewImages}
        submitting={submitting}
        validationErrors={validationErrors}
        onFieldChange={(field, value) => {
          setPayload((prev) => ({ ...prev, [field]: value }))
          setValidationErrors((prev) => ({ ...prev, [field]: undefined }))
        }}
        onUpload={handleUpload}
        onCapture={handleCapture}
        onSubmit={handleSubmit}
        onReset={resetForm}
      />

      <Card padding="sm" className="border-slate-800/70">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Enrollment Status
            </p>
            <h2 className="text-lg font-semibold text-white">Repository Snapshot</h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="info" soft>
              {profileCount} stored
            </Badge>
            {loading ? (
              <Badge tone="warning" soft>
                Updating...
              </Badge>
            ) : null}
          </div>
        </div>
        {statusMessage ? (
          <div className="mb-4 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-sm text-accent">
            {statusMessage}
          </div>
        ) : null}
        <FaceGallery
          profiles={profiles ?? []}
          onApprove={handleApprove}
          onDelete={handleDelete}
        />
      </Card>
    </div>
  )
}
