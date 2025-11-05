import { clsx } from 'clsx'
import type { HTMLAttributes, ReactNode } from 'react'

type CardPadding = 'none' | 'sm' | 'md' | 'lg'
type CardShadow = 'none' | 'default' | 'glow'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: CardPadding
  shadow?: CardShadow
  children: ReactNode
}

const paddingStyles: Record<CardPadding, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}

const shadowStyles: Record<CardShadow, string> = {
  none: '',
  default: 'shadow-inner border border-slate-800/70',
  glow: 'shadow-glow border border-accent/30',
}

export const Card = ({
  padding = 'md',
  shadow = 'default',
  className,
  children,
  ...props
}: CardProps) => (
  <div
    className={clsx(
      'relative rounded-xl bg-surface/90 backdrop-blur-sm ring-1 ring-black/20',
      paddingStyles[padding],
      shadowStyles[shadow],
      className,
    )}
    {...props}
  >
    <div className="pointer-events-none absolute inset-0 rounded-xl border border-white/5" />
    <div className="relative">{children}</div>
  </div>
)
