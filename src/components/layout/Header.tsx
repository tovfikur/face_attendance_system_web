import { useMemo } from 'react'
import {
  ChevronDown,
  Database,
  Globe,
  RefreshCw,
  Search,
  ShieldHalf,
  Siren,
  Wifi,
} from 'lucide-react'
import { clsx } from 'clsx'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { AlertDropdown } from '@/components/alerts/AlertDropdown'
import { useLiveClock } from '@/hooks/useLiveClock'
import { useRoleContext } from '@/context/RoleContext'
import type {
  LanguageOption,
  NotificationItem,
  SystemSummary,
} from '@/types'

interface HeaderProps {
  summary?: SystemSummary | null
  bannerMessage?: string
  notifications: NotificationItem[]
  onNotificationAcknowledge: (notificationId: string) => void
  onNotificationsClear: () => void
  languageOptions: LanguageOption[]
  timezoneOptions: string[]
  activeLanguage: string
  activeTimezone: string
  onLanguageChange: (code: string) => void
  onTimezoneChange: (tz: string) => void
  onRoleChange?: (roleId: string) => void
  onRefresh?: () => void
  isRefreshing?: boolean
}

export const Header = ({
  summary,
  bannerMessage,
  notifications,
  onNotificationAcknowledge,
  onNotificationsClear,
  languageOptions,
  timezoneOptions,
  activeLanguage,
  activeTimezone,
  onLanguageChange,
  onTimezoneChange,
  onRoleChange,
  onRefresh,
  isRefreshing,
}: HeaderProps) => {
  const clock = useLiveClock()
  const { roles, activeRole, setActiveRole } = useRoleContext()

  const handleRoleSwap = () => {
    const index = roles.findIndex((role) => role.id === activeRole.id)
    const nextRole = roles[(index + 1) % roles.length]
    setActiveRole(nextRole.id)
    onRoleChange?.(nextRole.id)
  }

  const summaryMetrics = useMemo(
    () => [
      {
        label: 'Active Cameras',
        value: summary?.activeCameras ?? '—',
        icon: <ShieldHalf className="h-4 w-4 text-emerald-400" />,
      },
      {
        label: 'Detected Today',
        value: summary?.peopleDetectedToday ?? '—',
        icon: <Siren className="h-4 w-4 text-sky-400" />,
      },
      {
        label: 'Unknown Alerts',
        value: summary?.unknownFaceAlerts ?? '—',
        icon: <Wifi className="h-4 w-4 text-amber-400" />,
      },
      {
        label: 'Attendance',
        value: summary ? `${summary.attendanceCompletion}%` : '—',
        icon: <Database className="h-4 w-4 text-slate-300" />,
      },
    ],
    [summary],
  )

  return (
    <header className="relative border-b border-slate-800/50 bg-surface/80 px-6 py-4 backdrop-blur-xl">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-accent/30 bg-slate-900/70 text-accent shadow-glow">
            <ShieldHalf className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              Control Room │ Secure Campus
            </p>
            <h1 className="text-xl font-semibold text-slate-100">
              CCTV Monitoring & Attendance Command
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm">
          <div className="hidden items-center gap-3 rounded-lg border border-slate-800/80 bg-slate-900/60 px-3 py-2 md:flex">
            <Search className="h-4 w-4 text-slate-500" />
            <input
              className="w-48 bg-transparent text-xs text-slate-200 outline-none placeholder:text-slate-500"
              placeholder="Search camera, person, or alert"
            />
          </div>

          <div className="flex items-center gap-2 rounded-lg border border-slate-800/80 bg-slate-900/60 px-3 py-2">
            <span className="text-xs uppercase tracking-[0.35em] text-slate-500">Role</span>
            <button
              onClick={handleRoleSwap}
              className="flex items-center gap-1 text-sm font-medium text-slate-100"
              type="button"
            >
              {activeRole.name}
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </button>
          </div>

          <div className="hidden items-center gap-2 rounded-lg border border-slate-800/80 bg-slate-900/60 px-3 py-2 lg:flex">
            <Globe className="h-4 w-4 text-slate-500" />
            <select
              value={activeLanguage}
              onChange={(event) => onLanguageChange(event.target.value)}
              className="bg-transparent text-xs text-slate-200 outline-none"
            >
              {languageOptions.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-slate-900 text-white">
                  {lang.label}
                </option>
              ))}
            </select>
            <span className="h-1 w-1 rounded-full bg-slate-700" />
            <select
              value={activeTimezone}
              onChange={(event) => onTimezoneChange(event.target.value)}
              className="bg-transparent text-xs text-slate-200 outline-none"
            >
              {timezoneOptions.map((tz) => (
                <option key={tz} value={tz} className="bg-slate-900 text-white">
                  {tz}
                </option>
              ))}
            </select>
          </div>

          <Badge tone="info" className="hidden md:inline-flex">
            {clock}
          </Badge>

          <AlertDropdown
            notifications={notifications}
            onAcknowledge={onNotificationAcknowledge}
            onClearAll={onNotificationsClear}
          />

          <Button
            variant="outline"
            size="sm"
            icon={<RefreshCw className={clsx('h-4 w-4', isRefreshing && 'animate-spin')} />}
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            Refresh
          </Button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-4">
        {summaryMetrics.map(({ label, value, icon }) => (
          <div
            key={label}
            className="flex items-center justify-between rounded-lg border border-slate-800/70 bg-slate-900/60 px-3 py-2"
          >
            <div>
              <p className="text-[11px] uppercase tracking-[0.4em] text-slate-500">{label}</p>
              <p className="text-lg font-semibold text-white">{value}</p>
            </div>
            <div className="rounded-md border border-slate-700/70 bg-slate-800/90 p-2">{icon}</div>
          </div>
        ))}
      </div>

      {bannerMessage ? (
        <div className="mt-4 overflow-hidden rounded-lg border border-accent/40 bg-accent/10">
          <div className="relative flex items-center gap-3 px-4 py-2 text-sm text-accent">
            <div className="flex h-6 w-6 items-center justify-center rounded-full border border-accent/50 bg-slate-900/80">
              <Siren className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1">
              <span className="font-semibold uppercase tracking-[0.35em] text-accent/70">
                Operations Feed
              </span>
              <p className="mt-1 text-accent/90">{bannerMessage}</p>
            </div>
            <div className="hidden items-center gap-1 pr-2 text-[11px] uppercase tracking-widest text-accent/60 sm:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pingSlow" />
              Live
            </div>
          </div>
        </div>
      ) : null}
    </header>
  )
}
