const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with status ${response.status}`)
  }

  return response.json()
}

export function getDashboardOverview() {
  return fetchJson('/dashboard/overview')
}

export function getDashboardPatient(patientId) {
  return fetchJson(`/dashboard/patients/${patientId}`)
}

export function getDashboardAlerts() {
  return fetchJson('/dashboard/alerts')
}

export function getDashboardReminders() {
  return fetchJson('/dashboard/reminders')
}
