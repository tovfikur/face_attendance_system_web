/**
 * Attendance Dashboard - Integrated with Backend API
 * Real-time attendance tracking with WebSocket updates
 */

import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Clock,
  Users,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Loader2,
  RefreshCw,
  LogOut,
  LogIn,
} from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { getWebSocketService, type AttendanceEvent } from '@/services/websocket'
import { useNotification } from '@/context/NotificationContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import type { AttendanceRecord } from '@/types'

interface PersonStatus {
  person_id: string
  person_name: string
  checked_in: boolean
  check_in_time?: string
  current_duration_minutes?: number
}

interface DailySummary {
  total_persons: number
  present: number
  absent: number
  late: number
  presence_percentage: number
}

export const AttendanceIntegratedPage = () => {
  const navigate = useNavigate()
  const { addNotification } = useNotification()

  // State management
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null)
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([])
  const [currentStatuses, setCurrentStatuses] = useState<Map<string, PersonStatus>>(new Map())
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null)
  const [personAttendanceHistory, setPersonAttendanceHistory] = useState<AttendanceRecord[]>([])
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    status: 'all' as string,
  })

  // Fetch daily summary
  const fetchDailySummary = useCallback(async () => {
    try {
      const response = await apiClient.getDailyReport()
      setDailySummary(response.data)
    } catch (err) {
      console.error('Failed to fetch daily summary:', err)
      addNotification('error', 'Failed to load daily summary')
    }
  }, [addNotification])

  // Fetch attendance records
  const fetchAttendanceRecords = useCallback(async () => {
    try {
      setLoading(true)
      const response = await apiClient.getAttendanceRecords(filters.page, filters.pageSize, {
        status: filters.status === 'all' ? undefined : filters.status,
      })
      setAttendanceRecords(response.data)
    } catch (err) {
      console.error('Failed to fetch attendance records:', err)
      addNotification('error', 'Failed to load attendance records')
    } finally {
      setLoading(false)
    }
  }, [filters.page, filters.pageSize, filters.status, addNotification])

  // Fetch person's attendance history
  const fetchPersonHistory = useCallback(async (personId: string) => {
    try {
      const response = await apiClient.getPersonAttendance(personId, 1, 50)
      setPersonAttendanceHistory(response.data)
      setSelectedPersonId(personId)
    } catch (err) {
      console.error('Failed to fetch person history:', err)
      addNotification('error', 'Failed to load person history')
    }
  }, [addNotification])

  // Get person status
  const fetchPersonStatus = useCallback(
    async (personId: string) => {
      try {
        const response = await apiClient.getPersonStatus(personId)
        setCurrentStatuses((prev) => {
          const newMap = new Map(prev)
          newMap.set(personId, response.data)
          return newMap
        })
      } catch (err) {
        console.error(`Failed to fetch status for ${personId}:`, err)
      }
    },
    []
  )

  // Handle real-time attendance events via WebSocket
  const handleAttendanceEvent = useCallback(
    (event: AttendanceEvent) => {
      // Update current statuses
      const status: PersonStatus = {
        person_id: event.person_id,
        person_name: event.person_name,
        checked_in: event.action === 'check_in',
        check_in_time: event.action === 'check_in' ? event.check_in_time : undefined,
        current_duration_minutes:
          event.action === 'check_in' ? 0 : event.duration_minutes,
      }

      setCurrentStatuses((prev) => {
        const newMap = new Map(prev)
        newMap.set(event.person_id, status)
        return newMap
      })

      // Show notification
      const actionText = event.action === 'check_in' ? 'checked in' : 'checked out'
      addNotification(
        'success',
        `${event.person_name} ${actionText}`,
        `Confidence: ${(event.confidence * 100).toFixed(1)}%`,
        3000
      )

      // Refresh daily summary
      fetchDailySummary()

      // If this is the selected person, refresh their history
      if (event.person_id === selectedPersonId) {
        fetchPersonHistory(selectedPersonId)
      }
    },
    [selectedPersonId, fetchDailySummary, fetchPersonHistory, addNotification]
  )

  // Initialize WebSocket connection
  useEffect(() => {
    const ws = getWebSocketService()

    const connectWebSocket = async () => {
      try {
        await ws.connect('/api/v1/attendance/ws', {
          person_id: 'all',
          min_confidence: 0.0,
        })
        addNotification('success', 'Connected to real-time attendance', '', 3000)
      } catch (err) {
        console.error('WebSocket connection failed:', err)
        addNotification('warning', 'Real-time updates unavailable', 'Using polling instead', 5000)
      }
    }

    connectWebSocket()

    // Subscribe to attendance events
    const unsubscribe = ws.onAttendanceEvent(handleAttendanceEvent)

    return () => {
      unsubscribe()
    }
  }, [handleAttendanceEvent, addNotification])

  // Initial data fetch
  useEffect(() => {
    fetchDailySummary()
    fetchAttendanceRecords()
  }, [fetchDailySummary, fetchAttendanceRecords])

  // Manual refresh
  const handleRefresh = async () => {
    setSyncing(true)
    try {
      await Promise.all([fetchDailySummary(), fetchAttendanceRecords()])
      addNotification('success', 'Data refreshed', '', 2000)
    } catch (err) {
      addNotification('error', 'Refresh failed')
    } finally {
      setSyncing(false)
    }
  }

  // Check in person
  const handleCheckIn = async (personId: string) => {
    try {
      setSyncing(true)
      await apiClient.checkIn(personId, 0.7)
      addNotification('success', 'Check-in recorded')
      await Promise.all([fetchDailySummary(), fetchPersonStatus(personId)])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Check-in failed'
      addNotification('error', 'Check-in failed', message)
    } finally {
      setSyncing(false)
    }
  }

  // Check out person
  const handleCheckOut = async (personId: string) => {
    try {
      setSyncing(true)
      await apiClient.checkOut(personId)
      addNotification('success', 'Check-out recorded')
      await Promise.all([fetchDailySummary(), fetchPersonStatus(personId)])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Check-out failed'
      addNotification('error', 'Check-out failed', message)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Attendance Tracking</h1>
          <p className="mt-2 text-slate-400">Real-time employee attendance management</p>
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

      {/* Daily Summary Cards */}
      {dailySummary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <SummaryCard
            icon={<Users className="h-6 w-6" />}
            label="Total Persons"
            value={dailySummary.total_persons}
            color="blue"
          />
          <SummaryCard
            icon={<CheckCircle className="h-6 w-6" />}
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
      )}

      {/* Attendance Records Table */}
      <Card className="border-slate-800/70">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Today's Attendance Records</h2>
          <div className="flex gap-2">
            <select
              value={filters.status}
              onChange={(e) => {
                setFilters((prev) => ({ ...prev, status: e.target.value, page: 1 }))
              }}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white"
            >
              <option value="all">All Status</option>
              <option value="present">Present</option>
              <option value="absent">Absent</option>
              <option value="late">Late</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Person</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Check-in</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Check-out</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Duration</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {attendanceRecords.map((record) => (
                  <tr
                    key={record.id}
                    className="border-b border-slate-800/50 hover:bg-slate-900/50"
                  >
                    <td className="px-4 py-3 text-white">
                      <button
                        onClick={() => fetchPersonHistory(record.person_id)}
                        className="hover:text-blue-400 hover:underline"
                      >
                        {record.person_id}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {record.check_in_time
                        ? new Date(record.check_in_time).toLocaleTimeString()
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {record.check_out_time
                        ? new Date(record.check_out_time).toLocaleTimeString()
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {record.duration_minutes ? `${record.duration_minutes} min` : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        tone={
                          record.status === 'present'
                            ? 'success'
                            : record.status === 'late'
                              ? 'warning'
                              : 'danger'
                        }
                        soft
                      >
                        {record.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 space-x-2">
                      {!record.check_in_time && (
                        <Button
                          size="sm"
                          variant="outline"
                          icon={<LogIn className="h-3 w-3" />}
                          onClick={() => handleCheckIn(record.person_id)}
                          disabled={syncing}
                        >
                          Check In
                        </Button>
                      )}
                      {record.check_in_time && !record.check_out_time && (
                        <Button
                          size="sm"
                          variant="outline"
                          icon={<LogOut className="h-3 w-3" />}
                          onClick={() => handleCheckOut(record.person_id)}
                          disabled={syncing}
                        >
                          Check Out
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Person History Modal/Drawer */}
      {selectedPersonId && personAttendanceHistory.length > 0 && (
        <Card className="border-slate-800/70">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">
              Attendance History - {selectedPersonId}
            </h2>
            <button
              onClick={() => setSelectedPersonId(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2">
            {personAttendanceHistory.slice(0, 10).map((record) => (
              <div
                key={record.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3"
              >
                <div>
                  <p className="text-sm text-white">
                    {record.check_in_time &&
                      new Date(record.check_in_time).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-slate-400">
                    {record.check_in_time &&
                      new Date(record.check_in_time).toLocaleTimeString()}{' '}
                    -{' '}
                    {record.check_out_time &&
                      new Date(record.check_out_time).toLocaleTimeString()}
                  </p>
                </div>
                <Badge tone={record.status === 'present' ? 'success' : 'danger'} soft>
                  {record.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}
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
