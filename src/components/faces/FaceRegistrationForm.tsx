import type { ChangeEvent } from 'react'
import { Camera, ImagePlus, Loader2, RotateCcw, Save } from 'lucide-react'
import type { FaceRegistrationPayload } from '@/types'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface FaceRegistrationFormProps {
  payload: FaceRegistrationPayload
  previewImages: string[]
  submitting?: boolean
  validationErrors?: Partial<Record<keyof FaceRegistrationPayload, string>>
  onFieldChange: <K extends keyof FaceRegistrationPayload>(field: K, value: FaceRegistrationPayload[K]) => void
  onUpload: (files: FileList | null) => void
  onCapture: () => void
  onSubmit: () => void
  onReset: () => void
}

export const FaceRegistrationForm = ({
  payload,
  previewImages,
  submitting,
  validationErrors,
  onFieldChange,
  onUpload,
  onCapture,
  onSubmit,
  onReset,
}: FaceRegistrationFormProps) => {
  const handleInputChange =
    (field: keyof FaceRegistrationPayload) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      onFieldChange(field, event.target.value)
    }

  return (
    <div className="space-y-6 rounded-xl border border-slate-800/70 bg-slate-900/70 p-6 shadow-inner">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
          Face Registration Pipeline
        </p>
        <h2 className="text-xl font-semibold text-white">Enroll New Identity</h2>
        <p className="mt-1 text-sm text-slate-400">
          Submit details and biometric captures to sync with the recognition engine.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">
              Full Name
            </label>
            <input
              className="mt-2 w-full rounded-lg border border-slate-800/70 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none ring-0 transition focus:border-accent focus:ring-0"
              placeholder="e.g. Sophia Martinez"
              value={payload.name}
              onChange={handleInputChange('name')}
            />
            {validationErrors?.name ? (
              <p className="mt-1 text-xs text-rose-400">{validationErrors.name}</p>
            ) : null}
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">
              Employee ID
            </label>
            <input
              className="mt-2 w-full rounded-lg border border-slate-800/70 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
              placeholder="EMP-00412"
              value={payload.employeeId}
              onChange={handleInputChange('employeeId')}
            />
            {validationErrors?.employeeId ? (
              <p className="mt-1 text-xs text-rose-400">{validationErrors.employeeId}</p>
            ) : null}
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">
              Department
            </label>
            <input
              className="mt-2 w-full rounded-lg border border-slate-800/70 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none focus:border-accent"
              placeholder="Manufacturing"
              value={payload.department}
              onChange={handleInputChange('department')}
            />
            {validationErrors?.department ? (
              <p className="mt-1 text-xs text-rose-400">{validationErrors.department}</p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-col justify-between gap-4 rounded-xl border border-slate-800/70 bg-slate-950/60 p-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">
              Capture Options
            </label>
            <p className="mt-2 text-xs text-slate-400">
              Upload high-resolution frontal images or simulate a live capture feed from an attached
              camera.
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <label className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-700/80 bg-slate-900/50 px-4 py-6 text-center text-sm text-slate-300 hover:border-accent/60 hover:bg-slate-900/60">
              <ImagePlus className="mb-2 h-5 w-5 text-accent" />
              <span className="font-medium">Upload Reference Images</span>
              <span className="text-xs text-slate-500">Accepted: PNG, JPG, JPEG</span>
              <input
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(event) => onUpload(event.target.files)}
              />
            </label>

            <Button
              variant="secondary"
              icon={<Camera className="h-4 w-4" />}
              onClick={onCapture}
            >
              Simulate Live Capture
            </Button>
            {validationErrors?.images ? (
              <p className="text-xs text-rose-400">{validationErrors.images}</p>
            ) : null}
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.35em] text-slate-500">
            <Badge tone="info" soft>
              {previewImages.length} sample(s) ready
            </Badge>
            <span>Use at least two angles for best accuracy.</span>
          </div>
        </div>
      </div>

      {previewImages.length ? (
        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">
            Capture Preview
          </p>
          <div className="flex flex-wrap gap-3">
            {previewImages.map((image, index) => (
              <div
                key={`${image}-${index.toString()}`}
                className="relative h-28 w-28 overflow-hidden rounded-lg border border-slate-800/70 bg-slate-950/70"
              >
                <img src={image} alt="preview" className="h-full w-full object-cover" />
                <Badge tone="info" soft className="absolute left-1 top-1 text-[10px]">
                  Frame {index + 1}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
          Submission triggers biometric sync with the recognition cluster.
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            icon={<RotateCcw className="h-4 w-4" />}
            onClick={onReset}
            disabled={submitting}
          >
            Reset
          </Button>
          <Button
            icon={submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            onClick={onSubmit}
            disabled={submitting}
          >
            Submit Profile
          </Button>
        </div>
      </div>
    </div>
  )
}
