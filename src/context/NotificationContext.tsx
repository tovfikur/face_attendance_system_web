/**
 * Notification Context
 * Manages toast notifications and alerts throughout the application
 */

import React, { createContext, useContext, useState, type ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message?: string
  duration?: number // milliseconds, 0 = persistent
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (
    type: NotificationType,
    title: string,
    message?: string,
    duration?: number
  ) => string
  removeNotification: (id: string) => void
  clearAll: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(
  undefined
)

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = (
    type: NotificationType,
    title: string,
    message?: string,
    duration: number = 5000
  ): string => {
    const id = `notification_${Date.now()}_${Math.random()}`
    const notification: Notification = {
      id,
      type,
      title,
      message,
      duration,
    }

    setNotifications((prev) => [...prev, notification])

    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }

    return id
  }

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }

  const clearAll = () => {
    setNotifications([])
  }

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        addNotification,
        removeNotification,
        clearAll,
      }}
    >
      {children}
      <NotificationContainer notifications={notifications} onRemove={removeNotification} />
    </NotificationContext.Provider>
  )
}

export const useNotification = () => {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error(
      'useNotification must be used within NotificationProvider'
    )
  }
  return context
}

/**
 * Notification Container Component
 */
const NotificationContainer: React.FC<{
  notifications: Notification[]
  onRemove: (id: string) => void
}> = ({ notifications, onRemove }) => {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={() => onRemove(notification.id)}
        />
      ))}
    </div>
  )
}

/**
 * Individual Notification Item
 */
const NotificationItem: React.FC<{
  notification: Notification
  onClose: () => void
}> = ({ notification, onClose }) => {
  const bgColor = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    info: 'bg-blue-50 border-blue-200',
    warning: 'bg-yellow-50 border-yellow-200',
  }[notification.type]

  const textColor = {
    success: 'text-green-800',
    error: 'text-red-800',
    info: 'text-blue-800',
    warning: 'text-yellow-800',
  }[notification.type]

  const Icon = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle,
  }[notification.type]

  return (
    <div
      className={`${bgColor} border rounded-lg shadow-lg p-4 pointer-events-auto animate-in fade-in slide-in-from-right-2 duration-300`}
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${textColor}`} />
        <div className="flex-1 min-w-0">
          <h3 className={`font-medium ${textColor}`}>{notification.title}</h3>
          {notification.message && (
            <p className={`text-sm mt-1 opacity-90 ${textColor}`}>
              {notification.message}
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className={`ml-2 flex-shrink-0 ${textColor} hover:opacity-75`}
        >
          <span className="sr-only">Close</span>
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  )
}
