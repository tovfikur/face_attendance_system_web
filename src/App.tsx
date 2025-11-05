import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { DashboardPage } from '@/pages/Dashboard'
import { LiveViewIntegratedPage } from '@/pages/LiveViewIntegrated'
import { FaceRegistrationIntegratedPage } from '@/pages/FaceRegistrationIntegrated'
import { AttendanceIntegratedPage } from '@/pages/AttendanceIntegrated'
import { PersonManagementIntegratedPage } from '@/pages/PersonManagementIntegrated'
import { ReportsIntegratedPage } from '@/pages/ReportsIntegrated'
import { AlertsPage } from '@/pages/Alerts'
import { SettingsPage } from '@/pages/Settings'
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
        <Route path="/live" element={<LiveViewIntegratedPage />} />
        <Route path="/live/:cameraId" element={<LiveViewIntegratedPage />} />
        <Route path="/face-register" element={<FaceRegistrationIntegratedPage />} />
        <Route path="/attendance" element={<AttendanceIntegratedPage />} />
        <Route path="/persons" element={<PersonManagementIntegratedPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/cameras" element={<CamerasPage />} />
        <Route path="/reports" element={<ReportsIntegratedPage />} />
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
