import { useMemo } from 'react'
import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  Activity,
  ActivitySquare,
  AlertTriangle,
  Camera,
  ClipboardList,
  Clock,
  Code2,
  ChevronLeft,
  ChevronRight,
  FileBarChart,
  Layers,
  MonitorSmartphone,
  Settings,
  UserPlus,
  Users,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useRoleContext } from '@/context/RoleContext'
import { formatTimestamp } from '@/utils/formatters'
import { systemSummary } from '@/data/mockData'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  lastSynced?: string
}

const navigationItems = [
  { to: '/', icon: Layers, label: 'Dashboard Overview', role: 'Viewer' },
  { to: '/live', icon: MonitorSmartphone, label: 'Live Monitoring', role: 'Operator' },
  { to: '/face-register', icon: UserPlus, label: 'Face Enrollment', role: 'Operator' },
  { to: '/attendance', icon: Users, label: 'Attendance Logs', role: 'Operator' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts & Incidents', role: 'Operator' },
  { to: '/cameras', icon: Camera, label: 'Camera Directory', role: 'Operator' },
  { to: '/reports', icon: FileBarChart, label: 'Reports & Insights', role: 'Operator' },
  { to: '/system-health', icon: ActivitySquare, label: 'System Health', role: 'Operator' },
  { to: '/history', icon: Clock, label: 'Person History', role: 'Operator' },
  { to: '/audit-log', icon: ClipboardList, label: 'Audit Trail', role: 'Admin' },
  { to: '/developer', icon: Code2, label: 'Developer Console', role: 'Admin' },
  { to: '/settings', icon: Settings, label: 'Control Center', role: 'Admin' },
]

export const Sidebar = ({ collapsed, onToggle, lastSynced }: SidebarProps) => {
  const { roles, activeRole } = useRoleContext()

  const allowedNavigation = useMemo(
    () =>
      navigationItems.filter((item) => {
        if (activeRole.name === 'Admin') return true
        if (activeRole.name === 'Operator') {
          return item.role === 'Operator' || item.role === 'Viewer'
        }
        return item.role === 'Viewer'
      }),
    [activeRole],
  )

  return (
    <aside
      className={clsx(
        'relative flex h-full flex-col border-r border-slate-800/60 bg-surface/95 backdrop-blur-xl transition-[width] duration-300',
        collapsed ? 'w-[78px]' : 'w-[264px]',
      )}
    >
      <div className="flex items-center gap-3 border-b border-slate-800/50 px-5 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-accent/30 bg-slate-900/60 text-accent shadow-glow">
          <Activity className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="space-y-0.5">
            <p className="text-sm font-semibold uppercase tracking-wider text-slate-100">
              Sentinel Vision
            </p>
            <p className="text-[11px] font-medium uppercase tracking-widest text-slate-400">
              CCTV | Attendance AI
            </p>
          </div>
        )}
        <Button
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          variant="ghost"
          size="sm"
          className="absolute -right-3 top-5 h-7 w-7 rounded-full border border-slate-700/80 bg-slate-900/90"
          icon={collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          onClick={onToggle}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="space-y-1">
          {allowedNavigation.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-700/40 hover:text-white',
                  isActive && 'bg-accent/15 text-accent shadow-glow',
                  collapsed && 'justify-center px-0',
                )
              }
              end={to === '/'}
            >
              <Icon className="h-[18px] w-[18px]" />
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </div>

        {!collapsed && (
          <div className="mt-8 space-y-3 rounded-lg border border-slate-800/60 bg-slate-900/60 p-4">
            <div className="flex items-center justify-between text-xs uppercase tracking-widest text-slate-500">
              <span>Role Context</span>
              <Badge tone="info">{activeRole.name}</Badge>
            </div>
            <ul className="space-y-1 text-xs text-slate-400">
              {activeRole.permissions.map((permission) => (
                <li key={permission} className="flex items-center gap-2 text-[11px] uppercase tracking-widest">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                  {permission.replace(/-/g, ' ')}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="space-y-4 border-t border-slate-800/50 px-4 py-4">
        {!collapsed && (
          <div className="space-y-2 rounded-lg border border-slate-800/60 bg-slate-900/70 p-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Active Cameras</span>
              <Badge tone="success">{systemSummary.activeCameras}</Badge>
            </div>
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Attendance</span>
              <Badge tone="info" soft>
                {systemSummary.attendanceCompletion}%
              </Badge>
            </div>
            <div className="text-[11px] uppercase tracking-widest text-slate-500">
              Synced {lastSynced ? formatTimestamp(lastSynced, { withDate: false }) : '—'}
            </div>
          </div>
        )}
        <div
          className={clsx(
            'flex items-center justify-between gap-2',
            collapsed && 'flex-col text-[11px]',
          )}
        >
          {!collapsed && (
            <span className="text-[11px] uppercase tracking-[0.35em] text-slate-500">
              {roles.length} roles loaded
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            className={clsx('w-full', collapsed && 'w-full text-[10px]')}
          >
            Control Room Log
          </Button>
        </div>
      </div>
    </aside>
  )
}
