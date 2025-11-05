import { useEffect, useMemo, useState } from 'react'
import {
  CalendarRange,
  DownloadCloud,
  History,
  PlugZap,
  RefreshCw,
  Search,
  SlidersHorizontal,
} from 'lucide-react'
import type { AttendanceLog, Camera, OdooIntegrationConfig, OdooSyncLog } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { formatTimestamp } from '@/utils/formatters'
import { mockApi } from '@/services/mockApi'
import { AttendanceLogTable } from '@/components/attendance/AttendanceLogTable'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface FilterState {
  search: string
  cameraId: string
  dateFrom: string
  dateTo: string
  odooStatus: AttendanceLog['odooStatus'] | 'all'
}

const odooStatusTone: Record<OdooIntegrationConfig["status"], "success" | "warning" | "danger"> = {
  connected: "success",
  disconnected: "danger",
  error: "warning",
}

const initialFilters: FilterState = {
  search: '',
  cameraId: '',
  dateFrom: '',
  dateTo: '',
  odooStatus: 'all',
}

export const AttendancePage = () => {
  const [filters, setFilters] = useState<FilterState>(initialFilters)
  const [exportMessage, setExportMessage] = useState<string>()
  const [syncMessage, setSyncMessage] = useState<string>()
  const [syncing, setSyncing] = useState(false)

  const {
    data: logs,
    refresh: refreshLogs,
    loading,
  } = usePolling<AttendanceLog[]>({
    fetcher: () => mockApi.fetchAttendanceLogs(filters),
    interval: 15000,
  })

  const { data: odooConfig, refresh: refreshOdooConfig } = usePolling<OdooIntegrationConfig>({
    fetcher: () => mockApi.fetchOdooIntegrationConfig(),
    interval: 20000,
  })

  const { data: odooLog, refresh: refreshOdooLog } = usePolling<OdooSyncLog[]>({
    fetcher: () => mockApi.fetchOdooSyncLog(15),
    interval: 20000,
  })

  const { data: cameras } = usePolling<Camera[]>({
    fetcher: () => mockApi.fetchCameras(),
    interval: 45000,
  })

  const { data: hourlyStats } = usePolling({
    fetcher: () => mockApi.fetchAttendanceStatistics('hour'),
    interval: 30000,
  })

  const { data: cameraStats } = usePolling({
    fetcher: () => mockApi.fetchAttendanceStatistics('camera'),
    interval: 30000,
  })

  const { data: dailyStats } = usePolling({
    fetcher: () => mockApi.fetchAttendanceStatistics('day'),
    interval: 30000,
  })

  useEffect(() => {
    refreshLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.search, filters.cameraId, filters.dateFrom, filters.dateTo, filters.odooStatus])

  const handleExport = async (format: 'csv' | 'pdf') => {
    const { url } = await mockApi.exportAttendanceLogs(format)
    setExportMessage(`Export ready: ${url}`)
    setTimeout(() => setExportMessage(undefined), 6000)
  }

  const pendingRecords = useMemo(() => (logs ?? []).filter((log) => log.odooStatus !== 'synced'), [logs])

  const handlePushToOdoo = async () => {
    if (!pendingRecords.length) {
      setSyncMessage('All attendance records are synchronized with Odoo.')
      setTimeout(() => setSyncMessage(undefined), 4000)
      return
    }
    setSyncing(true)
    try {
      const result = await mockApi.pushAttendanceToOdoo(pendingRecords.map((record) => record.id))
      setSyncMessage(`Odoo sync: ${result.success} success, ${result.failed} failed.`)
      refreshLogs()
      refreshOdooConfig()
      refreshOdooLog()
    } catch (error) {
      setSyncMessage('Failed to push attendance to Odoo.')
      console.error(error)
    } finally {
      setSyncing(false)
      setTimeout(() => setSyncMessage(undefined), 6000)
    }
  }

  const handleRefreshOdoo = () => {
    refreshOdooConfig()
    refreshOdooLog()
    refreshLogs()
  }
  const totalPresent = useMemo(
    () => (logs ?? []).filter((log) => log.status === 'present').length,
    [logs],
  )

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Attendance Intelligence
            </p>
            <h1 className="text-xl font-semibold text-white">
              Workforce Compliance
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({logs?.length ?? 0} records)
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<DownloadCloud className="h-4 w-4" />}
              onClick={() => handleExport('csv')}
            >
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={<DownloadCloud className="h-4 w-4" />}
              onClick={() => handleExport('pdf')}
            >
              Export PDF
            </Button>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <Card padding="sm" className="border-slate-800/70">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-accent/30 bg-slate-900/70 text-accent shadow-glow">
                  <PlugZap className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Odoo Integration</p>
                  <h2 className="text-lg font-semibold text-white">
                    {odooConfig?.company ?? 'Odoo Platform'}
                  </h2>
                </div>
              </div>
              <Badge tone={odooStatusTone[odooConfig?.status ?? 'error']} soft>
                {odooConfig?.status ?? 'disconnected'}
              </Badge>
            </div>
            <div className="grid gap-3 text-sm text-slate-300 md:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Endpoint</p>
                <p className="font-mono text-[12px] text-sky-300">{odooConfig?.baseUrl ?? '-'}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Database</p>
                <p>{odooConfig?.database ?? '-'}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Pending</p>
                <p className="font-semibold text-white">{odooConfig?.pendingCount ?? 0}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Failures</p>
                <p className="font-semibold text-amber-300">{odooConfig?.failureCount ?? 0}</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs uppercase tracking-[0.35em] text-slate-500">
              <span>Last sync: {odooConfig?.lastSync ? new Date(odooConfig.lastSync).toLocaleTimeString() : '-'}</span>
              <Badge tone={odooConfig?.autoSync ? 'info' : 'warning'} soft>
                Auto sync {odooConfig?.autoSync ? 'enabled' : 'disabled'}
              </Badge>
            </div>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              icon={<PlugZap className="h-4 w-4" />}
              onClick={handlePushToOdoo}
              disabled={syncing || pendingRecords.length === 0}
            >
              {syncing ? 'Syncing...' : 'Sync Pending'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={<RefreshCw className="h-4 w-4" />}
              onClick={handleRefreshOdoo}
            >
              Refresh
            </Button>
          </div>
          {syncMessage ? (
            <div className="mt-3 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-xs text-slate-300">
              {syncMessage}
            </div>
          ) : null}
        </Card>
          <Card padding="sm" className="border-slate-800/70">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History className="h-5 w-5 text-accent" />
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Sync Timeline</p>
                  <h3 className="text-lg font-semibold text-white">Recent Odoo feedback</h3>
                </div>
              </div>
              <Badge tone="info" soft>
                {odooLog?.length ?? 0}
              </Badge>
            </div>
            <div className="space-y-2">
              {(odooLog ?? []).slice(0, 6).map((entry) => (
                <div
                  key={entry.id}
                  className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-xs text-slate-300"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-slate-400">
                      {formatTimestamp(entry.timestamp, { withDate: false })}
                    </span>
                    <Badge tone={entry.result === 'success' ? 'success' : 'danger'} soft>
                      {entry.result}
                    </Badge>
                  </div>
                  <p className="mt-1 text-slate-200">{entry.employeeId} - {entry.message}</p>
                </div>
              ))}
              {(odooLog ?? []).length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-700/70 bg-slate-900/60 px-3 py-4 text-center text-xs text-slate-500">
                  No sync activity recorded yet.
                </div>
              ) : null}
            </div>
          </Card>
        </div>
        <div className="mt-4 grid gap-4 lg:grid-cols-[2fr_1fr_1fr_1fr_1fr]">
          <FilterSearch
            value={filters.search}
            onChange={(value) => setFilters((prev) => ({ ...prev, search: value }))}
          />
          <FilterCamera
            cameras={cameras ?? []}
            value={filters.cameraId}
            onChange={(value) => setFilters((prev) => ({ ...prev, cameraId: value }))}
          />
          <FilterDate
            label="From"
            value={filters.dateFrom}
            onChange={(value) => setFilters((prev) => ({ ...prev, dateFrom: value }))}
          />
          <FilterDate
            label="To"
            value={filters.dateTo}
            onChange={(value) => setFilters((prev) => ({ ...prev, dateTo: value }))}
          />
          <FilterOdooStatus
            value={filters.odooStatus}
            onChange={(value) => setFilters((prev) => ({ ...prev, odooStatus: value }))}
          />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-[11px] uppercase tracking-[0.35em] text-slate-500">
          <SlidersHorizontal className="h-4 w-4 text-accent" />
          <span>{totalPresent} entries match compliance criteria</span>
          {exportMessage ? (
            <Badge tone="info" soft>
              {exportMessage}
            </Badge>
          ) : null}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <AttendanceLogTable logs={logs ?? []} loading={loading} />
        <Card padding="sm" className="border-slate-800/70">
          <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
            Daily Attendance Totals
          </p>
          <div className="mt-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyStats ?? []}>
                <CartesianGrid stroke="rgba(51,65,85,0.4)" strokeDasharray="4 4" />
                <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #0ea5e9' }} />
                <Legend />
                <Bar dataKey="value" fill="#38bdf8" name="Entries" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card padding="sm" className="border-slate-800/70">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Throughput per Hour
              </p>
              <h2 className="text-lg font-semibold text-white">Shift Flow</h2>
            </div>
            <Badge tone="info" soft>
              {hourlyStats?.length ?? 0} data points
            </Badge>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyStats ?? []}>
                <defs>
                  <linearGradient id="attdHour" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(51,65,85,0.4)" strokeDasharray="4 4" />
                <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #0ea5e9' }} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#38bdf8"
                  fill="url(#attdHour)"
                  name="Entries"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card padding="sm" className="border-slate-800/70">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Camera Contributions
              </p>
              <h2 className="text-lg font-semibold text-white">Capture Density</h2>
            </div>
            <Badge tone="info" soft>
              {cameraStats?.length ?? 0} cameras
            </Badge>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cameraStats ?? []} layout="vertical">
                <CartesianGrid stroke="rgba(51,65,85,0.4)" strokeDasharray="4 4" />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis type="category" dataKey="label" stroke="#94a3b8" fontSize={11} width={120} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #0ea5e9' }} />
                <Bar dataKey="value" fill="#0ea5e9" name="Captures" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  )
}

const FilterSearch = ({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}) => (
  <label className="flex items-center gap-3 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2">
    <Search className="h-4 w-4 text-slate-500" />
    <input
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder="Search name or employee ID"
      className="flex-1 bg-transparent text-sm text-white outline-none"
    />
  </label>
)

const FilterCamera = ({
  cameras,
  value,
  onChange,
}: {
  cameras: Camera[]
  value: string
  onChange: (value: string) => void
}) => (
  <label className="flex items-center gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-slate-200">
    <span className="text-[11px] uppercase tracking-[0.35em] text-slate-500">Camera</span>
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="flex-1 bg-transparent text-sm text-white outline-none"
    >
      <option value="">All cameras</option>
      {cameras.map((camera) => (
        <option key={camera.id} value={camera.id} className="bg-slate-900 text-white">
          {camera.name} ({camera.id})
        </option>
      ))}
    </select>
  </label>
)

const FilterDate = ({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) => (
  <label className="flex items-center gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-slate-200">
    <CalendarRange className="h-4 w-4 text-slate-500" />
    <div className="flex flex-col">
      <span className="text-[11px] uppercase tracking-[0.35em] text-slate-500">{label}</span>
      <input
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="bg-transparent text-sm text-white outline-none"
      />
    </div>
  </label>
)









const FilterOdooStatus = ({
  value,
  onChange,
}: {
  value: AttendanceLog['odooStatus'] | 'all'
  onChange: (value: AttendanceLog['odooStatus'] | 'all') => void
}) => (
  <label className="flex items-center gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-slate-200">
    <span className="text-[11px] uppercase tracking-[0.35em] text-slate-500">Odoo</span>
    <select
      value={value}
      onChange={(event) => onChange(event.target.value as AttendanceLog['odooStatus'] | 'all')}
      className="flex-1 bg-transparent text-sm text-white outline-none"
    >
      <option value="all">All statuses</option>
      <option value="synced">Synced</option>
      <option value="pending">Pending</option>
      <option value="failed">Failed</option>
    </select>
  </label>
)
