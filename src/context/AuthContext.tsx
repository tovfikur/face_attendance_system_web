/**
 * Authentication Context
 * Provides authentication state and methods throughout the application
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { apiClient, type LoginRequest } from '@/services/apiClient'

export interface CurrentUser {
  id: string
  username: string
  email: string
  permissions?: string[]
}

interface AuthContextType {
  user: CurrentUser | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

/**
 * Auth Provider Component
 */
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check if user is already logged in on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = apiClient.getToken()
        if (token && !apiClient.isTokenExpired()) {
          // Token exists and is valid
          // In a real app, you'd fetch current user info
          // For now, we'll assume token is valid
          setUser({
            id: 'user-1',
            username: 'user',
            email: 'user@example.com',
            permissions: ['persons:read', 'persons:write', 'attendance:read', 'attendance:write'],
          })
        }
      } catch (err) {
        console.error('Auth initialization error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await apiClient.login(credentials)
      apiClient.setToken(response.access_token)

      // Set user from response or create default
      if (response.user) {
        setUser({
          id: response.user.id,
          username: response.user.username,
          email: response.user.email,
          permissions: ['persons:read', 'persons:write', 'attendance:read', 'attendance:write'],
        })
      } else {
        setUser({
          id: credentials.username,
          username: credentials.username,
          email: credentials.username,
          permissions: ['persons:read', 'persons:write', 'attendance:read', 'attendance:write'],
        })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      setIsLoading(true)
      await apiClient.logout()
      setUser(null)
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    error,
    login,
    logout,
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to use auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

/**
 * Higher-order component for protected routes
 */
export const withAuth = <P extends object>(Component: React.ComponentType<P>) => {
  return (props: P) => {
    const { isAuthenticated, isLoading } = useAuth()

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      )
    }

    if (!isAuthenticated) {
      window.location.href = '/login'
      return null
    }

    return <Component {...props} />
  }
}
