import { useState } from 'react'
import { Bell, Check, Trash2 } from 'lucide-react'
import type { NotificationItem } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatTimestamp } from '@/utils/formatters'

interface AlertDropdownProps {
  notifications: NotificationItem[]
  onAcknowledge: (notificationId: string) => void
  onClearAll: () => void
}

export const AlertDropdown = ({
  notifications,
  onAcknowledge,
  onClearAll,
}: AlertDropdownProps) => {
  const [open, setOpen] = useState(false)

  const unread = notifications.filter((notification) => !notification.acknowledged).length

  return (
    <div className="relative">
      <button
        type="button"
        className="relative flex h-10 w-10 items-center justify-center rounded-full border border-slate-700/70 bg-slate-900/60 text-slate-300 transition hover:border-accent/50 hover:text-white"
        onClick={() => setOpen((prev) => !prev)}
      >
        <Bell className="h-5 w-5" />
        {unread ? (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-danger text-[10px] font-semibold text-white">
            {unread}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute right-0 z-20 mt-3 w-80 overflow-hidden rounded-xl border border-slate-800/70 bg-slate-900/80 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-slate-800/60 px-4 py-3">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">
                Notifications
              </p>
              <p className="text-sm text-slate-300">{notifications.length} activity event(s)</p>
            </div>
            <Button variant="ghost" size="sm" onClick={onClearAll} icon={<Trash2 className="h-4 w-4" />}>
              Clear
            </Button>
          </div>
          <div className="max-h-72 space-y-2 overflow-y-auto p-3">
            {notifications.length === 0 ? (
              <p className="rounded-lg border border-slate-800/60 bg-slate-900/60 p-4 text-sm text-slate-400">
                All clear. The control room is quiet.
              </p>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className="flex flex-col gap-2 rounded-lg border border-slate-800/60 bg-slate-900/60 p-3"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-white">{notification.title}</p>
                    <Badge
                      tone={
                        notification.level === 'critical'
                          ? 'danger'
                          : notification.level === 'warning'
                            ? 'warning'
                            : 'info'
                      }
                      soft
                    >
                      {notification.level}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-400">{notification.message}</p>
                  <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.35em] text-slate-500">
                    <span>{formatTimestamp(notification.timestamp, { withDate: true })}</span>
                    {notification.link ? <span>{notification.link}</span> : null}
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={notification.acknowledged}
                    icon={<Check className="h-4 w-4" />}
                    onClick={() => onAcknowledge(notification.id)}
                  >
                    {notification.acknowledged ? 'Acknowledged' : 'Acknowledge'}
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
