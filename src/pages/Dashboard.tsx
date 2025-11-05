import { useMemo, useState } from 'react'
import { Video, Rows3, Rows4 } from 'lucide-react'
import { CameraCard } from '@/components/camera/CameraCard'
import { AttendanceTable } from '@/components/attendance/AttendanceTable'
import { AlertList } from '@/components/alerts/AlertList'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { TrendSparkline } from '@/components/analytics/TrendSparkline'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import type { Camera, CameraSummary, NetworkMetric, ShiftSchedule } from '@/types'

type GridMode = 'twoByTwo' | 'threeByThree'

const GRID_COLUMNS: Record<GridMode, string> = {
  twoByTwo: 'sm:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3',
  threeByThree: 'sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4',
}

export const DashboardPage = () => {
  const [gridMode, setGridMode] = useState<GridMode>('threeByThree')

  const { data: cameraList } = usePolling<Camera[]>({
    fetcher: () => mockApi.fetchCameras(),
    interval: 7000,
  })

  const { data: cameraSummary } = usePolling<CameraSummary[]>({
    fetcher: () => mockApi.fetchCameraSummary(),
    interval: 12000,
  })

  const { data: attendanceRecords } = usePolling({
    fetcher: () => mockApi.fetchAttendance(12),
    interval: 9000,
  })

  const { data: alertFeed } = usePolling({
    fetcher: () => mockApi.fetchAlerts(10),
    interval: 8000,
  })

  const { data: network } = usePolling<NetworkMetric[]>({
    fetcher: () => mockApi.fetchNetworkMetrics(),
    interval: 15000,
  })

  const { data: shifts } = usePolling<ShiftSchedule[]>({
    fetcher: () => mockApi.fetchShiftSchedules(),
    interval: 18000,
  })

  const summaryByCameraId = useMemo(() => {
    if (!cameraSummary) return new Map<string, CameraSummary>()
    return new Map(cameraSummary.map((summary) => [summary.id, summary]))
  }, [cameraSummary])

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[2.7fr_1.3fr]">
        <div className="space-y-6">
          <Card padding="sm" className="border-slate-800/70">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Camera Control Grid
                </p>
                <h2 className="text-xl font-semibold text-white">
                  Real-time Streams ({cameraList?.length ?? 0})
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="info" soft className="hidden sm:inline-flex">
                  <Video className="mr-2 h-3.5 w-3.5" />
                  {cameraList?.filter((camera) => camera.status === 'online').length ?? 0} active
                </Badge>
                <div className="flex items-center rounded-lg border border-slate-800/60 bg-slate-900/60">
                  <Button
                    variant={gridMode === 'twoByTwo' ? 'primary' : 'ghost'}
                    size="sm"
                    className="rounded-r-none border-0 px-3"
                    icon={<Rows3 className="h-4 w-4" />}
                    onClick={() => setGridMode('twoByTwo')}
                  >
                    2 × 2
                  </Button>
                  <Button
                    variant={gridMode === 'threeByThree' ? 'primary' : 'ghost'}
                    size="sm"
                    className="rounded-l-none border-0 px-3"
                    icon={<Rows4 className="h-4 w-4" />}
                    onClick={() => setGridMode('threeByThree')}
                  >
                    3 × 3
                  </Button>
                </div>
              </div>
            </div>
            <div
              className={`grid gap-4 ${GRID_COLUMNS[gridMode]} transition-[grid-template-columns] duration-300`}
            >
              {cameraList?.map((camera) => (
                <CameraCard
                  key={camera.id}
                  camera={camera}
                  summary={summaryByCameraId.get(camera.id)}
                />
              )) ?? (
                <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/40 p-6 text-sm text-slate-400">
                  Waiting for camera telemetry feed...
                </div>
              )}
            </div>
          </Card>

          <AttendanceTable records={attendanceRecords ?? []} />
        </div>

        <div className="space-y-6">
          <AlertList alerts={alertFeed ?? []} />

          <Card padding="sm" className="border-slate-800/70">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Network & Decoder Health
                </p>
                <h2 className="text-xl font-semibold text-white">Stream Backbone Monitor</h2>
              </div>
              <Badge tone="info" soft>
                {network?.length ?? 0} metrics
              </Badge>
            </div>
            <div className="space-y-3">
              {network?.map((metric) => (
                <div
                  key={metric.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-white">{metric.label}</p>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                      Stream metric #{metric.id.replace('NET-', '')}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <TrendSparkline
                      values={[
                        metric.value * 0.82,
                        metric.value * 0.93,
                        metric.value,
                        metric.value * 1.06,
                        metric.value * 0.97,
                      ]}
                      positive={metric.status !== 'critical'}
                    />
                    <div className="text-right">
                      <p className="text-lg font-semibold text-white">
                        {metric.value}
                        <span className="ml-1 text-xs text-slate-400">{metric.unit}</span>
                      </p>
                      <Badge
                        tone={
                          metric.status === 'good'
                            ? 'success'
                            : metric.status === 'warning'
                              ? 'warning'
                              : 'danger'
                        }
                        soft
                      >
                        {metric.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              )) ?? (
                <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/50 p-5 text-sm text-slate-400">
                  Network metrics pending initial poll...
                </div>
              )}
            </div>
          </Card>

          <Card padding="sm" className="border-slate-800/70">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  Shift Compliance Radar
                </p>
                <h2 className="text-xl font-semibold text-white">Operational Coverage</h2>
              </div>
              <Badge tone="success" soft>
                {shifts?.reduce((acc, shift) => acc + shift.expectedHeadcount, 0) ?? 0} expected
              </Badge>
            </div>
            <div className="space-y-4">
              {shifts?.map((shift) => (
                <div key={shift.id} className="space-y-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-white">{shift.name}</p>
                      <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                        {shift.startTime} ─ {shift.endTime} │ {shift.location}
                      </p>
                    </div>
                    <Badge tone={shift.compliance >= 95 ? 'success' : 'warning'} soft>
                      {shift.compliance}% coverage
                    </Badge>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{ width: `${Math.min(shift.compliance, 100)}%` }}
                    />
                  </div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    Expected headcount: {shift.expectedHeadcount}
                  </p>
                </div>
              )) ?? (
                <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/50 p-5 text-sm text-slate-400">
                  Loading planned shift coverage...
                </div>
              )}
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
