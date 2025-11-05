import { useState } from 'react'
import type { FormEvent } from 'react'
import { Clock, Compass, Search } from 'lucide-react'
import type { FaceProfile, PersonHistoryEntry } from '@/types'
import { usePolling } from '@/hooks/usePolling'
import { mockApi } from '@/services/mockApi'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

export const HistoryPage = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [results, setResults] = useState<PersonHistoryEntry[]>([])
  const [message, setMessage] = useState<string>()

  const { data: profiles } = usePolling<FaceProfile[]>({
    fetcher: () => mockApi.fetchFaceProfiles(),
    interval: 30000,
  })

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault()
    if (!searchTerm.trim()) {
      setMessage('Enter an employee ID to retrieve history.')
      return
    }
    const history = await mockApi.fetchPersonHistory(searchTerm.trim())
    if (!history.length) {
      setMessage('No appearance records found for that ID.')
    } else {
      setMessage(undefined)
    }
    setResults(history)
  }

  return (
    <div className="space-y-6">
      <Card padding="sm" className="border-slate-800/70 shadow-inner">
        <form onSubmit={handleSearch} className="flex flex-wrap items-center gap-3">
          <label className="flex flex-1 items-center gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2">
            <Search className="h-4 w-4 text-slate-500" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by employee ID"
              className="flex-1 bg-transparent text-sm text-white outline-none"
            />
          </label>
          <button
            type="submit"
            className="rounded-lg border border-accent/40 bg-accent px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-accent/90"
          >
            Fetch History
          </button>
        </form>
        {message ? (
          <div className="mt-3 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-slate-300">
            {message}
          </div>
        ) : null}
      </Card>

      <Card padding="sm" className="border-slate-800/70">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-accent" />
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Appearance Timeline
              </p>
              <h2 className="text-lg font-semibold text-white">Historical Records</h2>
            </div>
          </div>
          <Badge tone="info" soft>
            {results.length} events
          </Badge>
        </div>
        <div className="mt-4 space-y-3">
          {results.map((entry) => (
            <div
              key={entry.id}
              className="flex flex-col gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4"
            >
              <div className="flex items-center gap-3">
                <img
                  src={entry.thumbnail}
                  alt={entry.name}
                  className="h-12 w-12 rounded-lg border border-slate-700/60 object-cover"
                />
                <div>
                  <p className="text-sm font-semibold text-white">
                    {entry.name}{' '}
                    <span className="text-xs text-slate-400">({entry.employeeId})</span>
                  </p>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                    {entry.cameraName} │ {entry.cameraId}
                  </p>
                </div>
                <Badge tone="info" soft className="ml-auto">
                  {entry.streamType}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-slate-400">
                <span>{entry.timestamp}</span>
                <span>Accuracy {entry.accuracy.toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card padding="sm" className="border-slate-800/70">
        <div className="flex items-center gap-3">
          <Compass className="h-5 w-5 text-accent" />
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
              Registered Profiles
            </p>
            <h2 className="text-lg font-semibold text-white">Quick Select</h2>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          {profiles?.map((profile) => (
            <button
              key={profile.id}
              type="button"
              onClick={() => setSearchTerm(profile.employeeId)}
              className="flex items-center gap-3 rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-left text-sm text-slate-200 hover:border-accent/50"
            >
              <img
                src={profile.images[0]}
                alt={profile.name}
                className="h-10 w-10 rounded-lg border border-slate-700/60 object-cover"
              />
              <div>
                <p className="font-semibold text-white">{profile.name}</p>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                  {profile.employeeId}
                </p>
              </div>
            </button>
          ))}
        </div>
      </Card>
    </div>
  )
}
