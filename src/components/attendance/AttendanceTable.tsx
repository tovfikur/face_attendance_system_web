import { clsx } from 'clsx'
import type { AttendanceRecord } from '@/types'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { formatAccuracy, formatTimestamp } from '@/utils/formatters'

interface AttendanceTableProps {
  records: AttendanceRecord[]
}

const statusTone: Record<AttendanceRecord['status'], 'success' | 'warning' | 'info'> = {
  'on-site': 'success',
  'off-site': 'warning',
  remote: 'info',
}

export const AttendanceTable = ({ records }: AttendanceTableProps) => (
  <Card padding="sm" className="border-slate-800/70">
    <div className="mb-4 flex items-center justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Live Attendance Feed</p>
        <h2 className="text-xl font-semibold text-white">Authenticated Entries</h2>
      </div>
      <Badge tone="info" soft>
        {records.length} events
      </Badge>
    </div>
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-[0.35em] text-slate-500">
            <th className="pb-3 pr-6 font-medium">Person</th>
            <th className="pb-3 pr-6 font-medium">Role / Department</th>
            <th className="pb-3 pr-6 font-medium">Camera</th>
            <th className="pb-3 pr-6 font-medium">Timestamp</th>
            <th className="pb-3 pr-6 font-medium">Accuracy</th>
            <th className="pb-3 font-medium text-right">Status</th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {records.map((record) => (
            <tr
              key={record.id}
              className="border-t border-slate-800/60 text-slate-200 transition hover:bg-slate-800/40"
            >
              <td className="py-3 pr-6">
                <div className="flex items-center gap-3">
                  <img
                    src={record.thumbnail}
                    alt={record.name}
                    className="h-10 w-10 rounded-full border border-slate-700/60"
                  />
                  <div>
                    <p className="font-medium text-white">{record.name}</p>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                      {record.personId}
                    </p>
                  </div>
                </div>
              </td>
              <td className="py-3 pr-6">
                <div className="flex flex-col gap-1">
                  <span>{record.role}</span>
                  <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {record.department}
                  </span>
                </div>
              </td>
              <td className="py-3 pr-6">
                <div className="flex flex-col gap-1">
                  <span>{record.cameraName}</span>
                  <span className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {record.cameraId}
                  </span>
                </div>
              </td>
              <td className="py-3 pr-6 text-slate-300">
                {formatTimestamp(record.timestamp, { withDate: true })}
              </td>
              <td className="py-3 pr-6">
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 rounded-full bg-slate-800">
                    <div
                      className="h-2 rounded-full bg-emerald-400"
                      style={{ width: `${record.accuracy}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-white">
                    {formatAccuracy(record.accuracy)}
                  </span>
                </div>
              </td>
              <td className="py-3 text-right">
                <Badge tone={statusTone[record.status]} soft className="text-[11px]">
                  {clsx(record.status.replace('-', ' '))}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </Card>
)
