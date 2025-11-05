import { clsx } from 'clsx'
import type { HTMLAttributes } from 'react'

interface StatusIndicatorProps extends HTMLAttributes<HTMLDivElement> {
  status: 'online' | 'offline' | 'maintenance' | 'warning'
  pulse?: boolean
  label?: string
}

const statusStyles: Record<StatusIndicatorProps['status'], string> = {
  online: 'bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.6)]',
  offline: 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.5)]',
  maintenance: 'bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.55)]',
  warning: 'bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.55)]',
}

export const StatusIndicator = ({
  status,
  pulse = false,
  label,
  className,
  ...props
}: StatusIndicatorProps) => {
  return (
    <div className={clsx('flex items-center gap-2 text-xs uppercase tracking-[0.35em]', className)} {...props}>
      <span className="relative inline-flex h-3 w-3">
        <span
          className={clsx(
            'absolute inline-flex h-full w-full rounded-full opacity-60',
            statusStyles[status],
            pulse && 'animate-ping',
          )}
        />
        <span
          className={clsx('relative inline-flex h-3 w-3 rounded-full', statusStyles[status])}
        />
      </span>
      {label ? <span className="text-slate-400">{label}</span> : null}
    </div>
  )
}
