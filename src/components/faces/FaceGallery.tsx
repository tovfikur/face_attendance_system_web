import { CheckCircle2, Pencil, Trash2 } from 'lucide-react'
import type { FaceProfile } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { formatTimestamp } from '@/utils/formatters'

interface FaceGalleryProps {
  profiles: FaceProfile[]
  onApprove: (faceId: string) => void
  onDelete: (faceId: string) => void
}

const statusTone: Record<FaceProfile['status'], 'success' | 'info' | 'warning'> = {
  active: 'success',
  pending: 'info',
  archived: 'warning',
}

export const FaceGallery = ({ profiles, onApprove, onDelete }: FaceGalleryProps) => (
  <Card padding="sm" className="border-slate-800/70">
    <div className="mb-4 flex items-center justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Registered Faces</p>
        <h2 className="text-xl font-semibold text-white">Enrollment Repository</h2>
      </div>
      <Badge tone="info" soft>
        {profiles.length} profile(s)
      </Badge>
    </div>

    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {profiles.map((profile) => (
        <div
          key={profile.id}
          className="flex flex-col gap-3 rounded-xl border border-slate-800/70 bg-slate-900/60 p-4"
        >
          <div className="flex items-center gap-3">
            <img
              src={profile.images[0]}
              alt={profile.name}
              className="h-16 w-16 rounded-lg border border-slate-700/60 object-cover"
            />
            <div>
              <h3 className="text-base font-semibold text-white">{profile.name}</h3>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                {profile.employeeId} │ {profile.department}
              </p>
              <Badge tone={statusTone[profile.status]} soft className="mt-2">
                {profile.status}
              </Badge>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {profile.images.slice(1).map((image, index) => (
              <img
                key={`${profile.id}-${index.toString()}`}
                src={image}
                alt={`${profile.name} reference ${index + 2}`}
                className="h-10 w-10 rounded-md border border-slate-700/60 object-cover"
              />
            ))}
          </div>

          {profile.notes ? (
            <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200">
              {profile.notes}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-3 text-[11px] uppercase tracking-[0.35em] text-slate-500">
            <span>Created {formatTimestamp(profile.createdAt, { withDate: true })}</span>
            <span>Updated {formatTimestamp(profile.updatedAt, { withDate: true })}</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<CheckCircle2 className="h-4 w-4" />}
              onClick={() => onApprove(profile.id)}
              disabled={profile.status === 'active'}
            >
              Approve
            </Button>
            <Button
              variant="ghost"
              size="sm"
              icon={<Pencil className="h-4 w-4" />}
              disabled
            >
              Update
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto text-rose-400 hover:text-rose-200"
              icon={<Trash2 className="h-4 w-4" />}
              onClick={() => onDelete(profile.id)}
            >
              Delete
            </Button>
          </div>
        </div>
      ))}
    </div>

    {profiles.length === 0 ? (
      <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/50 p-6 text-sm text-slate-400">
        No face profiles have been registered yet.
      </div>
    ) : null}
  </Card>
)
