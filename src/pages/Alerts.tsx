import { useMemo, useState } from 'react'
import { Flame, ShieldAlert, Siren, VolumeX } from 'lucide-react'
import type { Alert } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { AlertList } from '@/components/alerts/AlertList'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

export const AlertsPage = () => {
  const [threshold, setThreshold] = useState(85)
  const [message, setMessage] = useState<string>()

  const {
    data: alerts,
    refresh: refreshAlerts,
    loading,
  } = usePolling<Alert[]>({
    fetcher: () => mockApi.fetchAlerts(24),
    interval: 8000,
  })

  const summary = useMemo(() => {
    const data = { critical: 0, high: 0, medium: 0, low: 0, open: 0 }
    for (const alert of alerts ?? []) {
      data[alert.level] += 1
      if (!alert.acknowledged) data.open += 1
    }
    return data
  }, [alerts])

  const handleAction = async (action: () => Promise<unknown>, success: string) => {
    await action()
    setMessage(success)
    setTimeout(() => setMessage(undefined), 4000)
    refreshAlerts()
  }

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Real-time Alerting Engine
            </p>
            <h1 className="text-xl font-semibold text-white">
              Incident Management
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({alerts?.length ?? 0} active)
              </span>
            </h1>
          </div>
          <Badge tone={loading ? 'warning' : 'info'} soft>
            {loading ? 'Syncing feed...' : 'Live feed'}
          </Badge>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <AlertSummary
            icon={<Siren className="h-5 w-5 text-red-400" />}
            label="Critical"
            value={summary.critical}
          />
          <AlertSummary
            icon={<ShieldAlert className="h-5 w-5 text-amber-400" />}
            label="High"
            value={summary.high}
          />
          <AlertSummary
            icon={<Flame className="h-5 w-5 text-orange-400" />}
            label="Medium"
            value={summary.medium}
          />
          <AlertSummary
            icon={<VolumeX className="h-5 w-5 text-slate-300" />}
            label="Unacknowledged"
            value={summary.open}
          />
        </div>
      </Card>

      {message ? (
        <div className="rounded-lg border border-accent/40 bg-accent/10 px-4 py-2 text-sm text-accent">
          {message}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <AlertList
          alerts={alerts ?? []}
          onAcknowledge={(id) =>
            handleAction(() => mockApi.acknowledgeAlert(id), `Alert ${id} acknowledged.`)
          }
          onMute={(id) => handleAction(() => mockApi.muteAlert(id), `Alert ${id} muted.`)}
          onClear={(id) => handleAction(() => mockApi.clearAlert(id), `Alert ${id} cleared.`)}
        />

        <Card padding="sm" className="border-slate-800/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Detection Threshold
              </p>
              <h2 className="text-lg font-semibold text-white">{threshold}% confidence</h2>
            </div>
            <Badge tone="info" soft>
              Adjustable
            </Badge>
          </div>
          <p className="mt-3 text-sm text-slate-400">
            Adjust the minimum required recognition confidence before an alert is escalated to the
            control room.
          </p>
          <input
            type="range"
            min="70"
            max="100"
            value={threshold}
            onChange={(event) => setThreshold(Number(event.target.value))}
            className="mt-4 h-2 w-full cursor-pointer accent-sky-400"
          />
          <div className="mt-2 flex justify-between text-xs uppercase tracking-[0.35em] text-slate-500">
            <span>Permissive</span>
            <span>Strict</span>
          </div>
          <div className="mt-4 grid gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                handleAction(
                  () => mockApi.acknowledgeAlert('ALERT-0001'),
                  'Applied new inference threshold.',
                )
              }
            >
              Apply Threshold
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setThreshold(85)}>
              Reset Default (85%)
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}

const AlertSummary = ({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: number
}) => (
  <div className="flex items-center justify-between rounded-lg border border-slate-800/70 bg-slate-900/60 px-4 py-3">
    <div>
      <p className="text-xs uppercase tracking-[0.35em] text-slate-500">{label}</p>
      <p className="text-2xl font-semibold text-white">{value}</p>
    </div>
    <div className="rounded-full border border-slate-700/60 bg-slate-800/80 p-3">{icon}</div>
  </div>
)
