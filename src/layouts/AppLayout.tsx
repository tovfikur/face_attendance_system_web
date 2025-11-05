import { Outlet } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { mockApi } from '@/services/mockApi'
import { usePolling } from '@/hooks/usePolling'
import type { LanguageOption, NotificationItem } from '@/types'

export const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [banner, setBanner] = useState<string>()
  const [language, setLanguage] = useState('en')
  const [timezone, setTimezone] = useState('UTC')

  const {
    data: summary,
    loading: summaryLoading,
    refresh: refreshSummary,
  } = usePolling({
    fetcher: () => mockApi.fetchSystemSummary(),
    interval: 12000,
  })

  const {
    data: notifications,
    refresh: refreshNotifications,
  } = usePolling<NotificationItem[]>({
    fetcher: () => mockApi.fetchNotifications(),
    interval: 10000,
  })

  const { data: languages } = usePolling<LanguageOption[]>({
    fetcher: () => mockApi.fetchLanguageOptions(),
    interval: 60000,
  })

  const { data: timezones } = usePolling<string[]>({
    fetcher: () => mockApi.fetchTimezoneOptions(),
    interval: 60000,
  })

  useEffect(() => {
    const unsubscribe = mockApi.subscribeToBannerMessages(setBanner, 9000)
    return unsubscribe
  }, [])

  useEffect(() => {
    if (languages && languages.length) {
      const defaultLanguage =
        languages.find((lang) => lang.isDefault)?.code ?? languages[0].code
      setLanguage(defaultLanguage)
    }
  }, [languages])

  useEffect(() => {
    if (timezones && timezones.length) {
      setTimezone(timezones[0])
    }
  }, [timezones])

  const notificationList = useMemo(
    () => notifications ?? [],
    [notifications],
  )

  const handleNotificationAcknowledge = async (notificationId: string) => {
    await mockApi.acknowledgeNotification(notificationId)
    refreshNotifications()
  }

  const handleNotificationsClear = async () => {
    await mockApi.clearNotifications()
    refreshNotifications()
  }

  return (
    <div className="relative flex min-h-screen bg-background text-slate-100">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-grid-overlay bg-[length:220px_220px]" />
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((prev) => !prev)}
        lastSynced={summary?.lastSync}
      />
      <div className="flex flex-1 flex-col">
        <Header
          summary={summary ?? null}
          bannerMessage={banner}
          notifications={notificationList}
          onNotificationAcknowledge={handleNotificationAcknowledge}
          onNotificationsClear={handleNotificationsClear}
          languageOptions={languages ?? []}
          timezoneOptions={timezones ?? []}
          activeLanguage={language}
          activeTimezone={timezone}
          onLanguageChange={setLanguage}
          onTimezoneChange={setTimezone}
          onRefresh={refreshSummary}
          isRefreshing={summaryLoading}
        />
        <main className="relative flex-1 overflow-y-auto px-6 pb-10 pt-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
