import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { DashboardPage } from '@/pages/Dashboard'
import { LiveViewPage } from '@/pages/LiveView'
import { FaceRegisterPage } from '@/pages/FaceRegister'
import { AttendancePage } from '@/pages/Attendance'
import { AlertsPage } from '@/pages/Alerts'
import { SettingsPage } from '@/pages/Settings'
import { ReportsPage } from '@/pages/Reports'
import { CamerasPage } from '@/pages/Cameras'
import { SystemHealthPage } from '@/pages/SystemHealth'
import { AuditLogPage } from '@/pages/AuditLog'
import { HistoryPage } from '@/pages/History'
import { DeveloperPage } from '@/pages/Developer'
import { LoginPage } from '@/pages/Login'

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/live" element={<LiveViewPage />} />
        <Route path="/live/:cameraId" element={<LiveViewPage />} />
        <Route path="/face-register" element={<FaceRegisterPage />} />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/cameras" element={<CamerasPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/system-health" element={<SystemHealthPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/audit-log" element={<AuditLogPage />} />
        <Route path="/developer" element={<DeveloperPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
