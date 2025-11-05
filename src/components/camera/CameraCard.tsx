import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import { Camera, Settings2, Video } from 'lucide-react'
import type { Camera as CameraType, CameraSummary } from '@/types'
import { StatusIndicator } from '@/components/status/StatusIndicator'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import {
  formatBitrate,
  formatFps,
  formatLatency,
  formatTimestamp,
} from '@/utils/formatters'

interface CameraCardProps {
  camera: CameraType
  summary?: CameraSummary
}

const statusLabels: Record<CameraType['status'], string> = {
  online: 'Online',
  offline: 'Offline',
  maintenance: 'Maintenance',
}

export const CameraCard = ({ camera, summary }: CameraCardProps) => {
  const isOnline = camera.status === 'online'

  return (
    <Card padding="sm" className="group overflow-hidden border-slate-800/70 bg-slate-900/70">
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Badge tone="info" soft>
                {camera.streamType}
              </Badge>
              <Badge tone={isOnline ? 'success' : camera.status === 'maintenance' ? 'warning' : 'danger'}>
                {statusLabels[camera.status]}
              </Badge>
            </div>
            <h3 className="mt-2 text-lg font-semibold text-white">{camera.name}</h3>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">{camera.location}</p>
          </div>
          <StatusIndicator status={camera.status} pulse={isOnline} />
        </div>

        <div className="relative overflow-hidden rounded-lg border border-slate-800/60 bg-slate-950/70">
          <div
            aria-hidden
            className={clsx(
              'relative h-40 overflow-hidden rounded-lg border border-slate-900/40 bg-slate-900/60',
              !isOnline && 'grayscale',
            )}
          >
            <img
              src={camera.thumbnail}
              alt={`${camera.name} thumbnail`}
              className="h-full w-full object-cover opacity-80 transition duration-500 group-hover:opacity-100"
            />
            <div className="absolute inset-0 bg-gradient-to-tr from-slate-950/40 via-transparent to-slate-900/40" />
            <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-3">
              <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.35em] text-slate-300">
                <span>{camera.id}</span>
                <span>{camera.resolution}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-xs text-slate-400">
          <div className="rounded-lg border border-slate-800/50 bg-slate-900/60 px-2 py-2">
            <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">FPS</p>
            <p className="text-sm font-semibold text-white">{formatFps(camera.fps)}</p>
          </div>
          <div className="rounded-lg border border-slate-800/50 bg-slate-900/60 px-2 py-2">
            <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">Latency</p>
            <p className="text-sm font-semibold text-white">{formatLatency(camera.latency)}</p>
          </div>
          <div className="rounded-lg border border-slate-800/50 bg-slate-900/60 px-2 py-2">
            <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">Bitrate</p>
            <p className="text-sm font-semibold text-white">{formatBitrate(camera.bitrate)}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {camera.tags.map((tag) => (
            <Badge key={tag} tone="neutral" soft className="text-[10px] uppercase tracking-[0.3em]">
              {tag.replace(/-/g, ' ')}
            </Badge>
          ))}
        </div>

        <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.35em] text-slate-500">
          <span>{camera.ipAddress}</span>
          <span>Last seen {formatTimestamp(camera.lastSeen)}</span>
        </div>

        {summary ? (
          <div className="grid grid-cols-3 gap-2 border border-slate-800/60 bg-slate-900/50 px-3 py-2 text-center text-[11px] uppercase tracking-[0.35em] text-slate-400">
            <div className="flex flex-col">
              <span>Detections</span>
              <span className="text-base font-semibold text-white">{summary.detectionsToday}</span>
            </div>
            <div className="flex flex-col">
              <span>Unknown</span>
              <span className="text-base font-semibold text-amber-400">{summary.unknownFaces}</span>
            </div>
            <div className="flex flex-col">
              <span>Uptime</span>
              <span className="text-base font-semibold text-emerald-400">
                {summary.uptimePercent}%
              </span>
            </div>
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-2">
          <NavLink to={`/live/${camera.id}`} className="flex-1">
            <Button
              variant="primary"
              size="sm"
              className="w-full"
              icon={<Video className="h-4 w-4" />}
            >
              View Live
            </Button>
          </NavLink>
          <Button
            variant="ghost"
            size="sm"
            icon={<Camera className="h-4 w-4" />}
            className="flex-1 border border-slate-700/60 bg-slate-900/80 hover:border-accent"
          >
            Snap
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<Settings2 className="h-4 w-4" />}
            className="flex-1 border border-slate-700/60 bg-slate-900/80 hover:border-accent"
          >
            Config
          </Button>
        </div>
      </div>
    </Card>
  )
}
