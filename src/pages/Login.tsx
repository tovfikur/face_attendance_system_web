import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/context/AuthContext'
import { useNotification } from '@/context/NotificationContext'

export const LoginPage = () => {
  const navigate = useNavigate()
  const { login, isLoading } = useAuth()
  const { addNotification } = useNotification()

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    try {
      await login({
        username: formData.username,
        password: formData.password,
      })
      addNotification('success', 'Login successful', 'Redirecting to dashboard...')
      navigate('/')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      addNotification('error', 'Login failed', message)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <Card padding="lg" className="max-w-md border-slate-800/70">
        <div className="flex flex-col items-center gap-3">
          <Shield className="h-10 w-10 text-blue-500" />
          <h1 className="text-2xl font-semibold text-white">Face Attendance System</h1>
          <p className="text-center text-sm text-slate-400">
            Sign in with your credentials to access the system
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-[0.35em] text-slate-400">
              Username or Email
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="user@example.com"
              disabled={isLoading}
              className="mt-2 w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none placeholder-slate-600 focus:border-blue-500 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-[0.35em] text-slate-400">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="••••••••"
              disabled={isLoading}
              className="mt-2 w-full rounded-lg border border-slate-800/60 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none placeholder-slate-600 focus:border-blue-500 disabled:opacity-50"
            />
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {isLoading ? 'Logging in...' : 'Login'}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-slate-500">
          Connected to backend API at {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
        </p>
      </Card>
    </div>
  )
}
