import { clsx } from 'clsx'
import { AlertTriangle, BellPlus, CheckCircle2 } from 'lucide-react'
import type { Alert } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { formatTimestamp } from '@/utils/formatters'

interface AlertListProps {
  alerts: Alert[]
  title?: string
  limit?: number
  onAcknowledge?: (alertId: string) => void
  onMute?: (alertId: string) => void
  onClear?: (alertId: string) => void
}

const levelStyles: Record<Alert['level'], string> = {
  low: 'border-slate-700/60 bg-slate-900/60',
  medium: 'border-amber-500/40 bg-amber-500/10',
  high: 'border-rose-500/40 bg-rose-500/10',
  critical: 'border-red-600/60 bg-red-600/15',
}

const levelBadge: Record<Alert['level'], { label: string; tone: 'info' | 'warning' | 'danger' }> = {
  low: { label: 'Low', tone: 'info' },
  medium: { label: 'Medium', tone: 'warning' },
  high: { label: 'High', tone: 'danger' },
  critical: { label: 'Critical', tone: 'danger' },
}

export const AlertList = ({
  alerts,
  title = 'Incident Timeline',
  limit = 6,
  onAcknowledge,
  onMute,
  onClear,
}: AlertListProps) => {
  const items = alerts.slice(0, limit)

  return (
    <Card padding="sm" className="border-slate-800/70">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Alert Center</p>
          <h2 className="text-xl font-semibold text-white">{title}</h2>
        </div>
        <Badge tone="danger" soft>
          {alerts.filter((alert) => !alert.acknowledged).length} open
        </Badge>
      </div>
      <div className="space-y-3">
        {items.map((alert) => (
          <div
            key={alert.id}
            className={clsx(
              'flex flex-col gap-3 rounded-lg border px-3 py-3 text-sm text-slate-200',
              levelStyles[alert.level],
            )}
          >
            <div className="flex items-start gap-3">
              <div className="mt-1">
                {alert.acknowledged ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-white">{alert.title}</h3>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-400">
                      {alert.cameraId} │ {formatTimestamp(alert.timestamp, { withDate: true })}
                    </p>
                  </div>
                  <Badge tone={levelBadge[alert.level].tone} soft>
                    {levelBadge[alert.level].label}
                  </Badge>
                </div>
                <p className="mt-2 text-sm text-slate-300">{alert.description}</p>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.35em] text-slate-400">
                  {alert.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-slate-600/60 bg-slate-800/40 px-2 py-1"
                    >
                      #{tag.replace(/-/g, ' ')}
                    </span>
                  ))}
                  <span className="ml-auto flex items-center gap-1 text-[10px] uppercase tracking-[0.4em]">
                    {alert.acknowledged ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        Acknowledged
                      </>
                    ) : (
                      <>
                        <BellPlus className="h-3.5 w-3.5 text-amber-400" />
                        Pending
                      </>
                    )}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={alert.acknowledged}
                onClick={() => onAcknowledge?.(alert.id)}
              >
                Acknowledge
              </Button>
              <Button variant="ghost" size="sm" onClick={() => onMute?.(alert.id)}>
                Mute
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-rose-400 hover:text-rose-200"
                onClick={() => onClear?.(alert.id)}
              >
                Clear
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
