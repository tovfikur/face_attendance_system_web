import { clsx } from 'clsx'
import type { Camera, PersonDetection } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { StatusIndicator } from '@/components/status/StatusIndicator'
import { formatConfidence, formatTimestamp } from '@/utils/formatters'

interface LiveStreamViewportProps {
  camera: Camera
  detections: PersonDetection[]
}

export const LiveStreamViewport = ({ camera, detections }: LiveStreamViewportProps) => (
  <div className="relative overflow-hidden rounded-2xl border border-accent/20 bg-slate-900/60 shadow-glow">
    <div className="flex items-center justify-between border-b border-accent/20 bg-slate-900/70 px-5 py-3">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-accent/80">Live Stream</p>
        <h2 className="text-xl font-semibold text-white">
          {camera.name}{' '}
          <span className="text-sm font-medium text-slate-400">({camera.streamType})</span>
        </h2>
        <p className="text-[11px] uppercase tracking-[0.4em] text-slate-500">
          {camera.location} │ {camera.id}
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="rounded-lg border border-slate-700/70 bg-slate-900/60 px-3 py-2 text-xs uppercase tracking-[0.35em] text-slate-400">
          <span className="text-white">{camera.resolution}</span>
          <span className="ml-3">{camera.fps} FPS</span>
        </div>
        <StatusIndicator status={camera.status} pulse label={camera.status.toUpperCase()} />
      </div>
    </div>

    <div className="relative h-[520px] overflow-hidden">
      <img
        src={camera.thumbnail}
        className={clsx(
          'absolute inset-0 h-full w-full object-cover opacity-60',
          camera.status !== 'online' && 'grayscale',
        )}
        alt={`${camera.name} stream`}
      />
      <div className="absolute inset-0 bg-gradient-to-tr from-slate-950/70 via-transparent to-slate-900/60" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.35),transparent_70%)] opacity-40" />
      <div className="absolute inset-0">
        <div className="h-full w-full bg-[linear-gradient(0deg,rgba(56,189,248,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(56,189,248,0.05)_1px,transparent_1px)] bg-[length:40px_40px]" />
      </div>

      {detections.map((detection) => (
        <div
          key={detection.id}
          className="absolute rounded-lg border border-accent bg-slate-900/60 p-3 text-xs text-white shadow-glow"
          style={{
            top: `${detection.boundingBox.top}%`,
            left: `${detection.boundingBox.left}%`,
            width: `${detection.boundingBox.width}%`,
            height: `${detection.boundingBox.height}%`,
          }}
        >
          <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.35em]">
            <span>{detection.name}</span>
            <Badge tone={detection.status === 'unknown' ? 'danger' : 'success'}>{detection.status}</Badge>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] uppercase tracking-[0.35em] text-slate-300">
            <span>{detection.personId}</span>
            <span>{formatConfidence(detection.confidence)}</span>
          </div>
          <div className="absolute -bottom-16 left-1/2 flex -translate-x-1/2 gap-3 rounded-lg border border-slate-700/70 bg-slate-900/80 px-2 py-1 text-[10px] uppercase tracking-[0.35em]">
            <img
              src={detection.thumbnail}
              alt={detection.name}
              className="h-10 w-10 rounded-lg border border-slate-700/70"
            />
            <div className="flex flex-col justify-center text-left text-slate-200">
              <span>{formatTimestamp(detection.timestamp)}</span>
              <span className="text-[9px] uppercase tracking-[0.45em] text-slate-500">
                Track ID: {detection.trackId}
              </span>
            </div>
          </div>
        </div>
      ))}

      <div className="pointer-events-none absolute inset-x-10 bottom-10 flex justify-between text-[11px] uppercase tracking-[0.35em] text-accent/80">
        <span>Grid overlay stabilized</span>
        <span>People in frame: {detections.length}</span>
      </div>
    </div>
  </div>
)
