import { useMemo } from 'react'
import { Activity, BarChart3, Users } from 'lucide-react'
import type { AttendanceStatisticPoint, SystemSummary } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { TrendSparkline } from '@/components/analytics/TrendSparkline'

export const ReportsPage = () => {
  const { data: summary } = usePolling<SystemSummary>({
    fetcher: () => mockApi.fetchSystemSummary(),
    interval: 20000,
  })

  const { data: hourlyStats } = usePolling<AttendanceStatisticPoint[]>({
    fetcher: () => mockApi.fetchAttendanceStatistics('hour'),
    interval: 30000,
  })

  const { data: dayStats } = usePolling<AttendanceStatisticPoint[]>({
    fetcher: () => mockApi.fetchAttendanceStatistics('day'),
    interval: 30000,
  })

  const { data: cameraStats } = usePolling<AttendanceStatisticPoint[]>({
    fetcher: () => mockApi.fetchAttendanceStatistics('camera'),
    interval: 30000,
  })

  const topCameras = useMemo(
    () => (cameraStats ?? []).slice().sort((a, b) => b.value - a.value).slice(0, 4),
    [cameraStats],
  )

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-6 w-6 text-accent" />
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Executive Reporting
            </p>
            <h1 className="text-xl font-semibold text-white">Operational Analytics</h1>
          </div>
        </div>
        <p className="mt-3 text-sm text-slate-400">
          High-level analytics blending attendance trends, camera throughput, and AI health to
          support strategic decision making.
        </p>
      </Card>

      <div className="grid gap-4 md:grid-cols-4">
        <SummaryTile
          icon={<Users className="h-5 w-5 text-emerald-400" />}
          label="Registered Personnel"
          value={summary?.registeredPeople ?? 0}
          trendValues={[420, 448, 463, summary?.registeredPeople ?? 0]}
        />
        <SummaryTile
          icon={<Activity className="h-5 w-5 text-sky-400" />}
          label="Detections Today"
          value={summary?.peopleDetectedToday ?? 0}
          trendValues={[288, 306, 298, summary?.peopleDetectedToday ?? 0]}
        />
        <SummaryTile
          icon={<BarChart3 className="h-5 w-5 text-amber-400" />}
          label="Unknown Alerts"
          value={summary?.unknownFaceAlerts ?? 0}
          trendValues={[7, 5, summary?.unknownFaceAlerts ?? 0]}
          positive={false}
        />
        <SummaryTile
          icon={<Users className="h-5 w-5 text-purple-400" />}
          label="Attendance Completion"
          value={`${summary?.attendanceCompletion ?? 0}%`}
          trendValues={[92, 94, 96]}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Card padding="sm" className="border-slate-800/70">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Shift Throughput
              </p>
              <h2 className="text-lg font-semibold text-white">Hourly Flow</h2>
            </div>
            <Badge tone="info" soft>
              {hourlyStats?.length ?? 0} points
            </Badge>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyStats ?? []}>
                <defs>
                  <linearGradient id="reportHour" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(51,65,85,0.4)" strokeDasharray="4 4" />
                <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #38bdf8' }} />
                <Area type="linear" dataKey="value" stroke="#38bdf8" fill="url(#reportHour)" name="Entries" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card padding="sm" className="border-slate-800/70">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Top Cameras</p>
              <h2 className="text-lg font-semibold text-white">Capture Density</h2>
            </div>
            <Badge tone="info" soft>
              {topCameras.length} highlighted
            </Badge>
          </div>
          <div className="space-y-3">
            {topCameras.map((camera) => (
              <div
                key={camera.id}
                className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white">{camera.label}</span>
                  <Badge tone="info" soft>
                    {camera.value}
                  </Badge>
                </div>
                <TrendSparkline
                  values={[camera.value * 0.85, camera.value * 0.92, camera.value]}
                  width={220}
                />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card padding="sm" className="border-slate-800/70">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Daily Trend</p>
            <h2 className="text-lg font-semibold text-white">Attendance Momentum</h2>
          </div>
          <Badge tone="info" soft>
            {dayStats?.length ?? 0} days
          </Badge>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dayStats ?? []}>
              <CartesianGrid stroke="rgba(51,65,85,0.4)" strokeDasharray="4 4" />
              <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #38bdf8' }} />
              <Area type="monotone" dataKey="value" stroke="#0ea5e9" fill="#0ea5e933" name="Entries" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}

const SummaryTile = ({
  icon,
  label,
  value,
  trendValues,
  positive = true,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  trendValues: number[]
  positive?: boolean
}) => (
  <div className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-4 py-3">
    <div className="flex items-center justify-between">
      <span className="text-xs uppercase tracking-[0.35em] text-slate-500">{label}</span>
      <span>{icon}</span>
    </div>
    <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    <TrendSparkline values={trendValues} positive={positive} />
  </div>
)
