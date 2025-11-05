import { UserCheck, UserPlus, UserX } from 'lucide-react'
import type { ReactNode } from 'react'
import type { PersonDetection } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { formatConfidence, formatTimestamp } from '@/utils/formatters'

interface DetectionListProps {
  detections: PersonDetection[]
}

const statusConfig: Record<
  PersonDetection['status'],
  { label: string; icon: ReactNode; tone: 'success' | 'info' | 'danger' }
> = {
  authorized: {
    label: 'Authorized',
    icon: <UserCheck className="h-3.5 w-3.5 text-emerald-400" />,
    tone: 'success',
  },
  visitor: {
    label: 'Visitor',
    icon: <UserPlus className="h-3.5 w-3.5 text-sky-400" />,
    tone: 'info',
  },
  unknown: {
    label: 'Unknown',
    icon: <UserX className="h-3.5 w-3.5 text-rose-400" />,
    tone: 'danger',
  },
}

export const DetectionList = ({ detections }: DetectionListProps) => (
  <Card padding="sm" className="border-slate-800/70">
    <div className="mb-4">
      <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Recognition Feed</p>
      <h2 className="text-xl font-semibold text-white">People in Frame</h2>
      <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
        Active detections: {detections.length}
      </p>
    </div>
    <div className="space-y-3">
      {detections.map((detection) => {
        const status = statusConfig[detection.status]
        return (
          <div
            key={detection.id}
            className="flex items-center gap-3 rounded-lg border border-slate-800/60 bg-slate-900/60 p-3"
          >
            <img
              src={detection.thumbnail}
              alt={detection.name}
              className="h-12 w-12 rounded-lg border border-slate-700/60"
            />
            <div className="flex-1">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{detection.name}</p>
                  <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">
                    {detection.personId} │ {formatTimestamp(detection.timestamp)}
                  </p>
                </div>
                <Badge tone={status.tone}>
                  <span className="flex items-center gap-1">
                    {status.icon}
                    {status.label}
                  </span>
                </Badge>
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                <span>Confidence {formatConfidence(detection.confidence)}</span>
                <span className="uppercase tracking-[0.35em] text-slate-500">
                  Track: {detection.trackId}
                </span>
              </div>
            </div>
          </div>
        )
      })}
      {detections.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/50 p-5 text-sm text-slate-400">
          Waiting for detection events from stream...
        </div>
      ) : null}
    </div>
  </Card>
)
