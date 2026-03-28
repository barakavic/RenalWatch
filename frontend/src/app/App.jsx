import { Routes, Route, Navigate } from 'react-router-dom'

import PatientOverviewPage from '../pages/PatientOverviewPage.jsx'
import PatientDetailPage from '../pages/PatientDetailPage.jsx'
import AlertsPage from '../pages/AlertsPage.jsx'
import RemindersPage from '../pages/RemindersPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PatientOverviewPage />} />
      <Route path="/patients/:patientId" element={<PatientDetailPage />} />
      <Route path="/alerts" element={<AlertsPage />} />
      <Route path="/reminders" element={<RemindersPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
