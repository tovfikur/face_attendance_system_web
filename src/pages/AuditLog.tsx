import { ClipboardList, Download } from 'lucide-react'
import type { AuditLogEntry } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatTimestamp } from '@/utils/formatters'

export const AuditLogPage = () => {
  const { data: auditLog, loading } = usePolling<AuditLogEntry[]>({
    fetcher: () => mockApi.fetchAuditTrail(),
    interval: 12000,
  })

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Compliance Ledger
            </p>
            <h1 className="text-xl font-semibold text-white">
              Audit Trail
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({auditLog?.length ?? 0} entries)
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone={loading ? 'warning' : 'info'} soft>
              {loading ? 'Syncing' : 'Live'}
            </Badge>
            <Button variant="outline" size="sm" icon={<Download className="h-4 w-4" />}>
              Export Log
            </Button>
          </div>
        </div>
      </Card>

      <Card padding="sm" className="border-slate-800/70">
        <div className="flex items-center gap-3">
          <ClipboardList className="h-5 w-5 text-accent" />
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Recent Activity
            </p>
            <h2 className="text-lg font-semibold text-white">Operator & System Events</h2>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {auditLog?.map((entry) => (
            <div
              key={entry.id}
              className="flex flex-col gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-white">{entry.message}</p>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {entry.actor} │ {entry.actorRole}
                  </p>
                </div>
                <Badge
                  tone={
                    entry.severity === 'critical'
                      ? 'danger'
                      : entry.severity === 'warning'
                        ? 'warning'
                        : 'info'
                  }
                  soft
                >
                  {entry.severity}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-slate-500">
                <span>{formatTimestamp(entry.timestamp, { withDate: true })}</span>
                {entry.context ? <span>{entry.context}</span> : null}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
