const timeFormatter = new Intl.DateTimeFormat('en-US', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
})

export const formatTimestamp = (isoString: string, options?: { withDate?: boolean }) => {
  const date = new Date(isoString)
  return options?.withDate ? dateFormatter.format(date) : timeFormatter.format(date)
}

export const formatLatency = (latency: number) => `${latency.toFixed(0)} ms`

export const formatBitrate = (bitrate: number) => `${bitrate.toFixed(1)} Mbps`

export const formatConfidence = (confidence: number) => `${confidence.toFixed(1)}%`

export const formatAccuracy = (accuracy: number) => `${accuracy.toFixed(1)}%`

export const formatFps = (fps: number) => `${Math.max(fps, 0)} FPS`

export const formatPercentage = (value: number, fractionDigits = 0) =>
  `${value.toFixed(fractionDigits)}%`
