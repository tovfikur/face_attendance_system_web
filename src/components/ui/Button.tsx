import { forwardRef } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { clsx } from 'clsx'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: ReactNode
  iconRight?: ReactNode
  fullWidth?: boolean
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent hover:bg-accentMuted text-slate-900 shadow-glow focus-visible:outline-accent',
  secondary:
    'bg-slate-800/80 hover:bg-slate-700/80 text-slate-100 focus-visible:outline-slate-500',
  outline:
    'border border-slate-600/70 hover:border-accent/70 text-slate-100 focus-visible:outline-accent',
  ghost:
    'text-slate-300 hover:bg-slate-700/40 focus-visible:outline-slate-400 aria-[current=true]:bg-slate-700/50',
  danger:
    'bg-danger/90 hover:bg-danger text-white focus-visible:outline-danger shadow-[0_0_20px_rgba(239,68,68,0.35)]',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-2.5 py-1.5 text-xs',
  md: 'px-3.5 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth,
      icon,
      iconRight,
      className,
      children,
      ...props
    },
    ref,
  ) => (
    <button
      ref={ref}
      className={clsx(
        'group inline-flex items-center justify-center gap-2 rounded-md font-medium transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && 'w-full',
        className,
      )}
      {...props}
    >
      {icon ? <span className="text-lg">{icon}</span> : null}
      <span className="flex-1 truncate">{children}</span>
      {iconRight ? <span className="text-lg">{iconRight}</span> : null}
    </button>
  ),
)

Button.displayName = 'Button'
