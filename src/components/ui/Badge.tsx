import { clsx } from 'clsx'
import type { HTMLAttributes } from 'react'

type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone
  soft?: boolean
}

const toneStyles: Record<BadgeTone, string> = {
  neutral: 'text-slate-200 bg-slate-700/70 border border-slate-600/70',
  success: 'text-emerald-200 bg-emerald-600/20 border border-emerald-400/40',
  warning: 'text-amber-200 bg-amber-600/20 border border-amber-500/40',
  danger: 'text-rose-200 bg-rose-600/20 border border-rose-500/40',
  info: 'text-sky-200 bg-sky-600/20 border border-sky-500/40',
}

const toneSoftStyles: Record<BadgeTone, string> = {
  neutral: 'text-slate-400 bg-slate-700/30 border border-slate-700/10',
  success: 'text-emerald-300 bg-emerald-600/15 border border-emerald-500/10',
  warning: 'text-amber-300 bg-amber-600/15 border border-amber-500/10',
  danger: 'text-rose-300 bg-rose-600/15 border border-rose-500/10',
  info: 'text-sky-300 bg-sky-600/15 border border-sky-500/10',
}

export const Badge = ({ tone = 'neutral', soft = false, className, ...props }: BadgeProps) => (
  <span
    className={clsx(
      'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide',
      soft ? toneSoftStyles[tone] : toneStyles[tone],
      className,
    )}
    {...props}
  />
)
