import { useState } from 'react'
import { Code2, Play } from 'lucide-react'
import type { DeveloperEndpoint } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

export const DeveloperPage = () => {
  const { data: endpoints } = usePolling<DeveloperEndpoint[]>({
    fetcher: () => mockApi.fetchDeveloperEndpoints(),
    interval: 60000,
  })
  const [selectedEndpoint, setSelectedEndpoint] = useState<DeveloperEndpoint>()
  const [response, setResponse] = useState<string>('Invoke an endpoint to see the payload.')
  const [loading, setLoading] = useState(false)

  const invoke = async (endpoint: DeveloperEndpoint) => {
    setSelectedEndpoint(endpoint)
    setLoading(true)
    try {
      const result = await mockApi.invokeDeveloperEndpoint(endpoint.id)
      setResponse(JSON.stringify(result, null, 2))
    } catch (error) {
      setResponse(`Error: ${(error as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <div className="flex items-center gap-3">
          <Code2 className="h-6 w-6 text-accent" />
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Developer Console
            </p>
            <h1 className="text-xl font-semibold text-white">Mock API Explorer</h1>
          </div>
        </div>
        <p className="mt-3 text-sm text-slate-400">
          Inspect available REST endpoints and view their mock responses. Useful for backend
          integration planning and contract validation.
        </p>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
        <Card padding="sm" className="border-slate-800/70">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Endpoints</h2>
            <Badge tone="info" soft>
              {endpoints?.length ?? 0} available
            </Badge>
          </div>
          <div className="space-y-3">
            {endpoints?.map((endpoint) => (
              <div
                key={endpoint.id}
                className="flex flex-col gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-white">{endpoint.label}</p>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                      {endpoint.method} {endpoint.path}
                    </p>
                  </div>
                  <Badge tone="info" soft>
                    {endpoint.method}
                  </Badge>
                </div>
                <p className="text-sm text-slate-300">{endpoint.description}</p>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Play className="h-4 w-4" />}
                  onClick={() => invoke(endpoint)}
                >
                  Invoke
                </Button>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="sm" className="border-slate-800/70">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Response Preview
              </p>
              <h2 className="text-lg font-semibold text-white">
                {selectedEndpoint ? selectedEndpoint.label : 'Awaiting selection'}
              </h2>
            </div>
            <Badge tone={loading ? 'warning' : 'info'} soft>
              {loading ? 'Fetching...' : 'Ready'}
            </Badge>
          </div>
          <pre className="mt-4 h-80 overflow-auto rounded-lg border border-slate-800/60 bg-slate-950/60 p-4 text-xs text-sky-300">
            {response}
          </pre>
        </Card>
      </div>
    </div>
  )
}
