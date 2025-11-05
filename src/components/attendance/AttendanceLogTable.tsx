import type { AttendanceLog } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

interface AttendanceLogTableProps {
  logs: AttendanceLog[]
  loading?: boolean
}

const statusTone: Record<AttendanceLog['status'], 'success' | 'warning' | 'danger'> = {
  present: 'success',
  late: 'warning',
  missed: 'danger',
}

export const AttendanceLogTable = ({ logs, loading }: AttendanceLogTableProps) => (
  <Card padding="sm" className="border-slate-800/70">
    <div className="mb-4 flex items-center justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
          Attendance Audit Trail
        </p>
        <h2 className="text-xl font-semibold text-white">Historical Log</h2>
      </div>
      <Badge tone={loading ? 'warning' : 'info'} soft>
        {loading ? 'Refreshing' : `${logs.length} records`}
      </Badge>
    </div>
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-[0.35em] text-slate-500">
            <th className="pb-3 pr-6 font-medium">Employee ID</th>
            <th className="pb-3 pr-6 font-medium">Name</th>
            <th className="pb-3 pr-6 font-medium">Department</th>
            <th className="pb-3 pr-6 font-medium">Date</th>
            <th className="pb-3 pr-6 font-medium">Time In</th>
            <th className="pb-3 pr-6 font-medium">Time Out</th>
            <th className="pb-3 pr-6 font-medium">Camera</th>
            <th className="pb-3 pr-6 font-medium">Accuracy %</th>
            <th className="pb-3 pr-6 font-medium">Odoo Sync</th>
            <th className="pb-3 font-medium text-right">Status</th>
          </tr>
        </thead>
        <tbody className="text-sm text-slate-200">
          {logs.map((log) => (
            <tr
              key={log.id}
              className="border-t border-slate-800/60 transition hover:bg-slate-800/40"
            >
              <td className="py-3 pr-6 font-medium text-white">{log.employeeId}</td>
              <td className="py-3 pr-6">{log.name}</td>
              <td className="py-3 pr-6 text-slate-400">{log.department}</td>
              <td className="py-3 pr-6 text-slate-300">{log.date}</td>
              <td className="py-3 pr-6 text-slate-300">{log.timeIn}</td>
              <td className="py-3 pr-6 text-slate-300">{log.timeOut}</td>
              <td className="py-3 pr-6">
                <div className="flex flex-col">
                  <span>{log.cameraName}</span>
                  <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {log.cameraId}
                  </span>
                </div>
              </td>
              <td className="py-3 pr-6 font-mono text-sm text-emerald-300">
                {log.accuracy.toFixed(1)}
              </td>
              <td className="py-3 pr-6">
                <div className="flex flex-col items-end gap-1 text-right">
                  <Badge
                    tone={
                      log.odooStatus === 'synced'
                        ? 'success'
                        : log.odooStatus === 'pending'
                          ? 'warning'
                          : 'danger'
                    }
                    soft
                  >
                    {log.odooStatus}
                  </Badge>
                  {log.odooSyncTime ? (
                    <span className="text-[10px] uppercase tracking-[0.35em] text-slate-500">
                      {new Date(log.odooSyncTime).toLocaleTimeString()}
                    </span>
                  ) : null}
                </div>
              </td>
              <td className="py-3 text-right">
                <Badge tone={statusTone[log.status]} soft>
                  {log.status}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    {logs.length === 0 ? (
      <div className="mt-4 rounded-lg border border-dashed border-slate-700/70 bg-slate-900/50 p-6 text-sm text-slate-400">
        No records match the current filters.
      </div>
    ) : null}
  </Card>
)
