import { useEffect, useRef, useState } from 'react'

interface UsePollingOptions<T> {
  fetcher: () => Promise<T>
  interval?: number
  immediate?: boolean
}

interface UsePollingState<T> {
  data: T | null
  loading: boolean
  error: unknown
  refresh: () => Promise<void>
}

export const usePolling = <T>({
  fetcher,
  interval = 5000,
  immediate = true,
}: UsePollingOptions<T>): UsePollingState<T> => {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState<boolean>(immediate)
  const [error, setError] = useState<unknown>(null)
  const mountedRef = useRef(true)
  const fetcherRef = useRef(fetcher)

  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  const run = async () => {
    try {
      setLoading(true)
      const response = await fetcherRef.current()
      if (mountedRef.current) {
        setData(response)
        setError(null)
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err)
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true
    if (immediate) {
      run()
    }
    const timer = setInterval(() => {
      run()
    }, interval)
    return () => {
      mountedRef.current = false
      clearInterval(timer)
    }
  }, [immediate, interval])

  return {
    data,
    loading,
    error,
    refresh: run,
  }
}
