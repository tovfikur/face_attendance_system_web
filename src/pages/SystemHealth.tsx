import { useState } from 'react'
import { ActivitySquare, Cpu, Gauge, RefreshCw, Server } from 'lucide-react'
import type {
  NetworkMetric,
  ResourceUsageMetric,
  SystemHealthMetric,
  SystemServiceStatus,
} from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { TrendSparkline } from '@/components/analytics/TrendSparkline'

export const SystemHealthPage = () => {
  const [message, setMessage] = useState<string>()

  const { data: resourceUsage } = usePolling<ResourceUsageMetric[]>({
    fetcher: () => mockApi.fetchSystemHealthMetrics(),
    interval: 8000,
  })

  const { data: services, refresh: refreshServices } = usePolling<SystemServiceStatus[]>({
    fetcher: () => mockApi.fetchSystemServices(),
    interval: 15000,
  })

  const { data: summary } = usePolling<SystemHealthMetric[]>({
    fetcher: () => mockApi.fetchSystemHealthSummary(),
    interval: 15000,
  })

  const { data: network } = usePolling<NetworkMetric[]>({
    fetcher: () => mockApi.fetchNetworkMetrics(),
    interval: 10000,
  })

  const handleRestart = async (serviceId: string) => {
    await mockApi.restartService(serviceId)
    setMessage(`Restart signal sent to ${serviceId}.`)
    setTimeout(() => setMessage(undefined), 4000)
    refreshServices()
  }

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Infrastructure Telemetry
            </p>
            <h1 className="text-xl font-semibold text-white">
              System Health Overview
              <span className="ml-2 text-sm font-medium text-slate-400">
                ({resourceUsage?.length ?? 0} metrics)
              </span>
            </h1>
          </div>
          <Badge tone="info" soft>
            Auto refresh 8s
          </Badge>
        </div>
        {message ? (
          <div className="mt-3 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-sm text-accent">
            {message}
          </div>
        ) : null}
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {summary?.map((metric) => (
            <div
              key={metric.id}
              className="rounded-lg border border-slate-800/60 bg-slate-900/60 px-4 py-3"
            >
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">{metric.label}</p>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-2xl font-semibold text-white">{metric.value.toFixed(2)}</span>
                <span className="text-sm text-slate-400">{metric.unit}</span>
              </div>
              <Badge tone={metric.trend === 'down' ? 'warning' : 'success'} soft className="mt-2">
                {metric.trend === 'steady' ? 'steady' : `${metric.trend} ${metric.change.toFixed(2)}`}
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <Card padding="sm" className="border-slate-800/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Resource Utilization
              </p>
              <h2 className="text-xl font-semibold text-white">Compute Footprint</h2>
            </div>
            <Badge tone="info" soft>
              GPU accelerated
            </Badge>
          </div>
          <div className="mt-4 space-y-3">
            {resourceUsage?.map((metric) => (
              <div key={metric.id} className="space-y-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-white">{metric.label}</p>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                      Limit {metric.limit} {metric.unit}
                    </p>
                  </div>
                  <Badge tone={metric.value > metric.limit * 0.85 ? 'warning' : 'success'} soft>
                    {metric.value} {metric.unit}
                  </Badge>
                </div>
                <div className="flex items-center gap-4">
                  <div className="h-2 flex-1 rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{ width: `${Math.min((metric.value / metric.limit) * 100, 100)}%` }}
                    />
                  </div>
                  <TrendSparkline
                    values={[
                      metric.value * 0.78,
                      metric.value * 0.91,
                      metric.value,
                      metric.value * 1.05,
                      metric.value * 0.97,
                    ]}
                    width={120}
                    positive={metric.value < metric.limit * 0.9}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="sm" className="border-slate-800/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Network Diagnostics
              </p>
              <h2 className="text-lg font-semibold text-white">Stream Backbone</h2>
            </div>
            <Badge tone="info" soft>
              {network?.length ?? 0} metrics
            </Badge>
          </div>
          <div className="mt-4 space-y-2">
            {network?.map((metric) => (
              <div
                key={metric.id}
                className="flex items-center justify-between rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2"
              >
                <span className="text-sm text-white">{metric.label}</span>
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
                  {metric.value} {metric.unit}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card padding="sm" className="border-slate-800/70">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Service Cluster
            </p>
            <h2 className="text-xl font-semibold text-white">Operational Nodes</h2>
          </div>
          <Badge tone="info" soft>
            {services?.length ?? 0} services
          </Badge>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {services?.map((service) => (
            <div
              key={service.id}
              className="flex flex-col gap-3 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">{service.name}</p>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {service.id} │ v{service.version}
                  </p>
                </div>
                <Badge
                  tone={
                    service.status === 'running'
                      ? 'success'
                      : service.status === 'degraded'
                        ? 'warning'
                        : 'danger'
                  }
                  soft
                >
                  {service.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-slate-500">
                <span>Uptime {service.uptime}</span>
                <span>Restarted {service.lastRestart.slice(0, 10)}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                icon={<RefreshCw className="h-4 w-4" />}
                onClick={() => handleRestart(service.id)}
              >
                Restart Service
              </Button>
            </div>
          ))}
        </div>
      </Card>

      <Card padding="sm" className="border-slate-800/70">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Maintenance Tasks
            </p>
            <h2 className="text-lg font-semibold text-white">Operations Toolkit</h2>
          </div>
          <Badge tone="info" soft>
            Manual actions
          </Badge>
        </div>
        <div className="mt-4 grid gap-3 lg:grid-cols-4">
          <ToolkitAction
            icon={<Cpu className="h-5 w-5" />}
            title="Restart AI Pipeline"
            description="Restarts the face recognition inference workers."
            onTrigger={() => handleRestart('SRV-ANALYTICS')}
          />
          <ToolkitAction
            icon={<Server className="h-5 w-5" />}
            title="Refresh Streams"
            description="Requests all cameras to resync streaming keys."
            onTrigger={() => handleRestart('SRV-INGEST')}
          />
          <ToolkitAction
            icon={<Gauge className="h-5 w-5" />}
            title="Flush Cache"
            description="Clears recognition cache for newest models."
            onTrigger={() => setMessage('Cache flush initiated (mock).')}
          />
          <ToolkitAction
            icon={<ActivitySquare className="h-5 w-5" />}
            title="Diagnostics Snapshot"
            description="Generate system diagnostic bundle."
            onTrigger={() => setMessage('Diagnostics bundle queued (mock).')}
          />
        </div>
      </Card>
    </div>
  )
}

const ToolkitAction = ({
  icon,
  title,
  description,
  onTrigger,
}: {
  icon: React.ReactNode
  title: string
  description: string
  onTrigger: () => void
}) => (
  <div className="flex flex-col gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4">
    <div className="flex items-center gap-2 text-slate-200">
      {icon}
      <span className="text-sm font-semibold">{title}</span>
    </div>
    <p className="text-xs text-slate-400">{description}</p>
    <Button variant="ghost" size="sm" onClick={onTrigger}>
      Execute
    </Button>
  </div>
)
