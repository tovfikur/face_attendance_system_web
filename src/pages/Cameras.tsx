import { useMemo, useState } from 'react'
import { Filter, Radar } from 'lucide-react'
import type { Camera, CameraSummary, StreamType } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { CameraStreamGrid } from '@/components/camera/CameraStreamGrid'

type StatusFilter = 'all' | 'online' | 'offline' | 'maintenance'

export const CamerasPage = () => {
  const [status, setStatus] = useState<StatusFilter>('all')
  const [protocol, setProtocol] = useState<StreamType | 'ALL'>('ALL')

  const { data: cameras } = usePolling<Camera[]>({
    fetcher: () => mockApi.fetchCameras(),
    interval: 12000,
  })

  const { data: summaries } = usePolling<CameraSummary[]>({
    fetcher: () => mockApi.fetchCameraSummary(),
    interval: 18000,
  })

  const summaryMap = useMemo(() => {
    if (!summaries) return new Map<string, CameraSummary>()
    return new Map(summaries.map((summary) => [summary.id, summary]))
  }, [summaries])

  const filtered = useMemo(() => {
    if (!cameras) return []
    return cameras.filter((camera) => {
      const matchesStatus = status === 'all' || camera.status === status
      const matchesProtocol = protocol === 'ALL' || camera.streamType === protocol
      return matchesStatus && matchesProtocol
    })
  }, [cameras, status, protocol])

  const statusCounts = useMemo(() => {
    const counts: Record<StatusFilter, number> = { all: cameras?.length ?? 0, online: 0, offline: 0, maintenance: 0 }
    cameras?.forEach((camera) => {
      counts[camera.status] += 1
    })
    return counts
  }, [cameras])

  const protocolCounts = useMemo(() => {
    const map = new Map<string, number>()
    cameras?.forEach((camera) => {
      map.set(camera.streamType, (map.get(camera.streamType) ?? 0) + 1)
    })
    return map
  }, [cameras])

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex items-center gap-3">
          <Radar className="h-6 w-6 text-accent" />
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Camera Inventory
            </p>
            <h1 className="text-xl font-semibold text-white">
              Fleet Overview
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({cameras?.length ?? 0} streams)
              </span>
            </h1>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <FilterBadge
            active={status === 'all'}
            onClick={() => setStatus('all')}
            label="All"
            value={statusCounts.all}
          />
          <FilterBadge
            active={status === 'online'}
            onClick={() => setStatus('online')}
            label="Online"
            value={statusCounts.online}
          />
          <FilterBadge
            active={status === 'offline'}
            onClick={() => setStatus('offline')}
            label="Offline"
            value={statusCounts.offline}
          />
          <FilterBadge
            active={status === 'maintenance'}
            onClick={() => setStatus('maintenance')}
            label="Maintenance"
            value={statusCounts.maintenance}
          />
          <div className="flex items-center gap-2 rounded-full border border-slate-800/60 bg-slate-900/60 px-3 py-1 text-xs uppercase tracking-[0.35em] text-slate-500">
            <Filter className="h-4 w-4 text-accent" />
            <span className="text-slate-300">Protocol</span>
            <select
              value={protocol}
              onChange={(event) => setProtocol(event.target.value as StreamType | 'ALL')}
              className="bg-transparent text-white outline-none"
            >
              <option value="ALL">All</option>
              {Array.from(protocolCounts.entries()).map(([key, value]) => (
                <option key={key} value={key} className="bg-slate-900 text-white">
                  {key} ({value})
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      <CameraStreamGrid
        cameras={filtered}
        summaries={summaryMap}
        mode="3x3"
      />
    </div>
  )
}

const FilterBadge = ({
  active,
  label,
  value,
  onClick,
}: {
  active: boolean
  label: string
  value: number
  onClick: () => void
}) => (
  <button
    type="button"
    onClick={onClick}
    className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-[0.35em] transition ${
      active
        ? 'border-accent bg-accent/15 text-accent shadow-glow'
        : 'border-slate-800/60 bg-slate-900/60 text-slate-400 hover:border-accent/30'
    }`}
  >
    {label}
    <Badge tone="info" soft>
      {value}
    </Badge>
  </button>
)
