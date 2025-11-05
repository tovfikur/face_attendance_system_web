/**
 * Reports Dashboard - Integrated with Backend API
 * Attendance analytics and reporting with real data
 */

import { useEffect, useState, useCallback } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Calendar,
  TrendingUp,
  Users,
  Clock,
  AlertCircle,
  Download,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { useNotification } from '@/context/NotificationContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface PersonStats {
  person_id: string
  person_name: string
  total_working_days: number
  days_present: number
  days_absent: number
  days_late: number
  days_early_leave: number
  presence_percentage: number
}

interface DailySummary {
  date: string
  total_persons: number
  present: number
  absent: number
  late: number
  presence_percentage: number
}

export const ReportsIntegratedPage = () => {
  const { addNotification } = useNotification()

  // State
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null)
  const [personStats, setPersonStats] = useState<PersonStats[]>([])

  // Filter state
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  )
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0],
  })

  // Fetch daily summary
  const fetchDailySummary = useCallback(async (date: string) => {
    try {
      const response = await apiClient.getDailyReport(date)
      setDailySummary({
        date,
        ...response.data,
      })
    } catch (err) {
      console.error('Failed to fetch daily summary:', err)
      addNotification('error', 'Failed to load daily summary')
    }
  }, [addNotification])

  // Fetch person statistics
  const fetchPersonStats = useCallback(async () => {
    try {
      // Get all persons first
      const personsResponse = await apiClient.getPersons(1, 100)

      // Fetch stats for each person
      const statsPromises = personsResponse.data.map((person) =>
        apiClient
          .getPersonStatistics(person.id, dateRange.from, dateRange.to)
          .then((response) => ({
            person_id: person.id,
            person_name: `${person.first_name} ${person.last_name}`,
            ...response.data,
          }))
          .catch(() => null)
      )

      const results = await Promise.all(statsPromises)
      setPersonStats(results.filter((r) => r !== null) as PersonStats[])
    } catch (err) {
      console.error('Failed to fetch person stats:', err)
      addNotification('error', 'Failed to load person statistics')
    }
  }, [dateRange.from, dateRange.to, addNotification])

  // Initial fetch
  useEffect(() => {
    setLoading(true)
    Promise.all([fetchDailySummary(selectedDate), fetchPersonStats()]).finally(() => {
      setLoading(false)
    })
  }, [selectedDate, fetchDailySummary, fetchPersonStats])

  // Refresh
  const handleRefresh = async () => {
    setSyncing(true)
    try {
      await Promise.all([fetchDailySummary(selectedDate), fetchPersonStats()])
      addNotification('success', 'Data refreshed', '', 2000)
    } catch (err) {
      addNotification('error', 'Refresh failed')
    } finally {
      setSyncing(false)
    }
  }

  // Prepare chart data
  const presenceData = dailySummary
    ? [
        { name: 'Present', value: dailySummary.present, color: '#10b981' },
        { name: 'Absent', value: dailySummary.absent, color: '#ef4444' },
        { name: 'Late', value: dailySummary.late, color: '#f59e0b' },
      ]
    : []

  const topPerformers = personStats
    .sort((a, b) => b.presence_percentage - a.presence_percentage)
    .slice(0, 10)

  const attendanceIssues = personStats
    .filter((s) => s.presence_percentage < 70)
    .sort((a, b) => a.presence_percentage - b.presence_percentage)
    .slice(0, 10)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Attendance Reports</h1>
          <p className="mt-2 text-slate-400">Analyze attendance patterns and performance</p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={syncing}
          icon={syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          variant="outline"
        >
          {syncing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {/* Filter Controls */}
      <Card className="border-slate-800/70">
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Select Date</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">From Date</label>
            <input
              type="date"
              value={dateRange.from}
              onChange={(e) => setDateRange((prev) => ({ ...prev, from: e.target.value }))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">To Date</label>
            <input
              type="date"
              value={dateRange.to}
              onChange={(e) => setDateRange((prev) => ({ ...prev, to: e.target.value }))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
            />
          </div>
        </div>
      </Card>

      {/* Daily Summary Cards */}
      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      ) : dailySummary ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <SummaryCard
            icon={<Users className="h-6 w-6" />}
            label="Total Persons"
            value={dailySummary.total_persons}
            color="blue"
          />
          <SummaryCard
            icon={<TrendingUp className="h-6 w-6" />}
            label="Present"
            value={dailySummary.present}
            subtext={`${dailySummary.presence_percentage.toFixed(1)}%`}
            color="green"
          />
          <SummaryCard
            icon={<AlertCircle className="h-6 w-6" />}
            label="Absent"
            value={dailySummary.absent}
            color="red"
          />
          <SummaryCard
            icon={<Clock className="h-6 w-6" />}
            label="Late"
            value={dailySummary.late}
            color="yellow"
          />
          <SummaryCard
            icon={<TrendingUp className="h-6 w-6" />}
            label="Presence Rate"
            value={`${dailySummary.presence_percentage.toFixed(1)}%`}
            color="purple"
          />
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Presence Distribution */}
        {dailySummary && (
          <Card className="border-slate-800/70">
            <h2 className="text-lg font-semibold text-white mb-4">Presence Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={presenceData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {presenceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Top Performers */}
        <Card className="border-slate-800/70">
          <h2 className="text-lg font-semibold text-white mb-4">Top Performers</h2>
          <div className="space-y-2">
            {topPerformers.map((person, index) => (
              <div
                key={person.person_id}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-slate-400 w-6 text-center">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {person.person_name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {person.days_present}/{person.total_working_days} days
                    </p>
                  </div>
                </div>
                <Badge tone="success" soft>
                  {person.presence_percentage.toFixed(1)}%
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Attendance Issues */}
        <Card className="border-slate-800/70">
          <h2 className="text-lg font-semibold text-white mb-4">Persons with Issues</h2>
          {attendanceIssues.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 p-6 text-center text-sm text-slate-400">
              No attendance issues detected
            </div>
          ) : (
            <div className="space-y-2">
              {attendanceIssues.map((person) => (
                <div
                  key={person.person_id}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {person.person_name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {person.days_absent} absent, {person.days_late} late
                    </p>
                  </div>
                  <Badge
                    tone={
                      person.presence_percentage < 50
                        ? 'danger'
                        : person.presence_percentage < 70
                          ? 'warning'
                          : 'info'
                    }
                    soft
                  >
                    {person.presence_percentage.toFixed(1)}%
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Statistics Table */}
        <Card className="border-slate-800/70">
          <h2 className="text-lg font-semibold text-white mb-4">Attendance Summary</h2>
          <div className="space-y-3">
            <StatRow label="Total Working Days" value={personStats[0]?.total_working_days || 0} />
            <StatRow
              label="Average Presence"
              value={`${(
                personStats.reduce((sum, p) => sum + p.presence_percentage, 0) / personStats.length ||
                0
              ).toFixed(1)}%`}
            />
            <StatRow
              label="Total Absences"
              value={personStats.reduce((sum, p) => sum + p.days_absent, 0)}
            />
            <StatRow
              label="Total Late Arrivals"
              value={personStats.reduce((sum, p) => sum + p.days_late, 0)}
            />
            <StatRow
              label="At Risk (< 70%)"
              value={personStats.filter((p) => p.presence_percentage < 70).length}
            />
          </div>
        </Card>
      </div>

      {/* Export Button */}
      <Card className="border-slate-800/70 bg-blue-500/5 border-blue-500/30">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white">Export Reports</h3>
            <p className="text-sm text-slate-400">Download attendance data for external use</p>
          </div>
          <div className="flex gap-2">
            <Button
              icon={<Download className="h-4 w-4" />}
              variant="outline"
              onClick={() => addNotification('info', 'CSV export', 'Feature coming soon')}
            >
              CSV
            </Button>
            <Button
              icon={<Download className="h-4 w-4" />}
              variant="outline"
              onClick={() => addNotification('info', 'PDF export', 'Feature coming soon')}
            >
              PDF
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

/**
 * Summary Card Component
 */
const SummaryCard: React.FC<{
  icon: React.ReactNode
  label: string
  value: string | number
  subtext?: string
  color: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
}> = ({ icon, label, value, subtext, color }) => {
  const colorClasses = {
    blue: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    green: 'text-green-500 bg-green-500/10 border-green-500/20',
    red: 'text-red-500 bg-red-500/10 border-red-500/20',
    yellow: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
    purple: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
  }

  return (
    <Card className={`border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-400">{label}</p>
          <p className="mt-2 text-2xl font-bold text-white">{value}</p>
          {subtext && <p className="mt-1 text-xs text-slate-400">{subtext}</p>}
        </div>
        <div className={`rounded-lg p-3 ${colorClasses[color]}`}>{icon}</div>
      </div>
    </Card>
  )
}

/**
 * Stat Row Component
 */
const StatRow: React.FC<{ label: string; value: string | number }> = ({
  label,
  value,
}) => (
  <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3">
    <span className="text-sm text-slate-400">{label}</span>
    <span className="text-lg font-semibold text-white">{value}</span>
  </div>
)
