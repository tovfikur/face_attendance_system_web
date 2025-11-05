import { useMemo } from 'react'
import { NavLink } from 'react-router-dom'
import { Expand, Gauge, Network, Radio, Video } from 'lucide-react'
import { clsx } from 'clsx'
import type { Camera, CameraSummary } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { StatusIndicator } from '@/components/status/StatusIndicator'
import {
  formatBitrate,
  formatFps,
  formatLatency,
  formatTimestamp,
} from '@/utils/formatters'

interface CameraStreamTileProps {
  camera: Camera
  summary?: CameraSummary
  active?: boolean
  onSelect?: (cameraId: string) => void
}

const protocolColors: Record<Camera['streamType'], string> = {
  RTSP: 'text-sky-300',
  USB: 'text-emerald-300',
  HTTP: 'text-amber-300',
  Socket: 'text-cyan-300',
  'Local File': 'text-purple-300',
}

export const CameraStreamTile = ({ camera, summary, active, onSelect }: CameraStreamTileProps) => {
  const protocolIcon = useMemo(() => {
    switch (camera.streamType) {
      case 'RTSP':
      case 'HTTP':
        return <Radio className="h-4 w-4" />
      case 'USB':
        return <Video className="h-4 w-4" />
      case 'Socket':
        return <Network className="h-4 w-4" />
      default:
        return <Gauge className="h-4 w-4" />
    }
  }, [camera.streamType])

  return (
    <div
      className={clsx(
        'group relative flex flex-col overflow-hidden rounded-xl border border-slate-800/60 bg-slate-900/60 p-3 transition-all duration-200 hover:border-accent/40 hover:shadow-glow',
        active && 'border-accent/50 shadow-glow',
        !camera.enabled && 'opacity-60',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.35em] text-slate-400">
            <span>{camera.id}</span>
            <span className="h-1 w-1 rounded-full bg-slate-700" />
            <span>{camera.location}</span>
          </div>
          <h3 className="mt-1 text-lg font-semibold text-white">{camera.name}</h3>
        </div>
        <StatusIndicator status={camera.status} pulse={camera.status === 'online'} />
      </div>

      <div className="relative mt-3 rounded-lg border border-slate-800/60 bg-slate-950/60">
        <img
          src={camera.thumbnail}
          alt={camera.name}
          className={clsx(
            'h-40 w-full rounded-lg object-cover opacity-70 transition duration-500 group-hover:opacity-90',
            camera.status !== 'online' && 'grayscale',
          )}
        />
        <div className="absolute inset-0 rounded-lg bg-gradient-to-tr from-slate-950/50 via-transparent to-slate-900/30" />
        <div className="pointer-events-none absolute inset-x-2 bottom-2 flex items-center justify-between rounded-lg border border-slate-800/60 bg-slate-900/60 px-2 py-1 text-[11px] uppercase tracking-[0.35em] text-slate-300">
          <span>{camera.streamType}</span>
          <span>{camera.resolution}</span>
        </div>

        <div className="absolute -right-5 top-4 hidden rounded-lg border border-accent/30 bg-accent/20 px-3 py-1 text-xs font-medium uppercase tracking-[0.35em] text-accent shadow-glow transition group-hover:block">
          Hover to preview
        </div>

        <div className="pointer-events-none absolute -bottom-10 left-1/2 hidden w-44 -translate-x-1/2 rounded-lg border border-slate-800/60 bg-slate-900/70 p-3 text-xs text-slate-300 shadow-xl transition group-hover:flex group-hover:flex-col">
          <span className="text-[11px] uppercase tracking-[0.4em] text-accent/70">
            Stream URL
          </span>
          <span className="truncate font-mono text-[11px] text-slate-200">{camera.streamUrl}</span>
          <span className="mt-2 text-[10px] uppercase tracking-[0.4em] text-slate-500">
            Last check {camera.lastChecked ? formatTimestamp(camera.lastChecked, { withDate: true }) : '—'}
          </span>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-slate-400">
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-2 py-1.5">
          <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">FPS</p>
          <p className="text-sm font-semibold text-white">{formatFps(camera.fps)}</p>
        </div>
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-2 py-1.5">
          <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">Latency</p>
          <p className="text-sm font-semibold text-white">{formatLatency(camera.latency)}</p>
        </div>
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-2 py-1.5">
          <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500">Bitrate</p>
          <p className="text-sm font-semibold text-white">{formatBitrate(camera.bitrate)}</p>
        </div>
      </div>

      {summary ? (
        <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-[11px] uppercase tracking-[0.35em] text-slate-400">
          <div className="text-left">
            <span className="block text-slate-400">Detections</span>
            <span className="text-base font-semibold text-white">{summary.detectionsToday}</span>
          </div>
          <div className="text-left">
            <span className="block text-slate-400">Unknown</span>
            <span className="text-base font-semibold text-amber-400">{summary.unknownFaces}</span>
          </div>
          <div className="text-left">
            <span className="block text-slate-400">Uptime</span>
            <span className="text-base font-semibold text-emerald-400">
              {summary.uptimePercent}%
            </span>
          </div>
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs uppercase tracking-[0.35em] text-slate-500">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-800/60 bg-slate-900/60 px-3 py-1 text-[11px] text-slate-300">
          <span className={clsx('flex items-center gap-1 font-semibold', protocolColors[camera.streamType])}>
            {protocolIcon}
            {camera.streamType}
          </span>
          <span className="h-1 w-1 rounded-full bg-slate-700" />
          <span>{camera.ipAddress}</span>
        </div>
        <span>Last seen {formatTimestamp(camera.lastSeen, { withDate: false })}</span>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <Button
          variant="primary"
          size="sm"
          className="flex-1"
          icon={<Expand className="h-4 w-4" />}
          onClick={() => {
            onSelect?.(camera.id)
          }}
        >
          Focus
        </Button>
        <NavLink to={`/live/${camera.id}`} className="flex-1">
          <Button variant="outline" size="sm" className="w-full" icon={<Video className="h-4 w-4" />}>
            Open
          </Button>
        </NavLink>
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        {camera.tags.map((tag) => (
          <Badge key={tag} tone="neutral" soft className="text-[10px] uppercase tracking-[0.3em]">
            {tag.replace(/-/g, ' ')}
          </Badge>
        ))}
      </div>
    </div>
  )
}
