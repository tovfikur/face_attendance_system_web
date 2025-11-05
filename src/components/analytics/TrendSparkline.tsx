interface TrendSparklineProps {
  values: number[]
  width?: number
  height?: number
  positive?: boolean
}

export const TrendSparkline = ({
  values,
  width = 120,
  height = 40,
  positive = true,
}: TrendSparklineProps) => {
  if (values.length <= 1) {
    return null
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const step = width / (values.length - 1)

  const points = values
    .map((value, index) => {
      const x = index * step
      const y = height - ((value - min) / range) * height
      return `${x},${y}`
    })
    .join(' ')

  const gradientId = positive ? 'sparklinePositive' : 'sparklineNegative'

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="presentation">
      <defs>
        <linearGradient id="sparklinePositive" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(56, 189, 248, 0.55)" />
          <stop offset="100%" stopColor="rgba(56, 189, 248, 0.05)" />
        </linearGradient>
        <linearGradient id="sparklineNegative" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(248, 113, 113, 0.55)" />
          <stop offset="100%" stopColor="rgba(248, 113, 113, 0.05)" />
        </linearGradient>
      </defs>
      <polyline
        fill={`url(#${gradientId})`}
        stroke="none"
        points={`${points} ${width},${height} 0,${height}`}
        opacity={0.35}
      />
      <polyline
        fill="none"
        stroke={positive ? '#38bdf8' : '#f87171'}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  )
}
