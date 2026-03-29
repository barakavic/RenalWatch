import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { Link } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { getDashboardReminders } from '../lib/api.js'

export default function RemindersPage() {
  const [data, setData] = useState({ kpis: null, reminders: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadReminders() {
      try {
        setLoading(true)
        const response = await getDashboardReminders()
        if (!cancelled) {
          setData(response)
          setError('')
        }
      } catch (loadError) {
        if (!cancelled) {
          setError('Could not load reminders.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadReminders()
    return () => {
      cancelled = true
    }
  }, [])

  const kpis = data.kpis ?? { due_today: 0, sent: 0, pending: 0, active: 0 }

  const columns = [
    { key: 'patient_name', header: 'Patient' },
    { key: 'reminder_type', header: 'Reminder Type' },
    { key: 'scheduled_at', header: 'Due Time', render: (row) => format(new Date(row.scheduled_at), 'PPp') },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge variant={row.status}>{row.status}</StatusBadge> },
    { key: 'message', header: 'Message' },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <Link to={`/patients/${row.patient_id}`} className="text-sm font-semibold text-brand-700 hover:text-brand-800">
          Open Patient
        </Link>
      ),
    },
  ]

  return (
    <div className="app-shell">
      <TopNav />
      <main className="page-container space-y-6">
        <section className="space-y-2">
          <h1 className="text-3xl font-semibold text-slate-900">Reminders</h1>
          <p className="text-slate-600">Track medication, blood pressure, and appointment reminder delivery.</p>
        </section>

        <section className="grid gap-4 md:grid-cols-4">
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Due Today</p><p className="mt-3 text-3xl font-semibold">{kpis.due_today}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Sent</p><p className="mt-3 text-3xl font-semibold">{kpis.sent}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Pending</p><p className="mt-3 text-3xl font-semibold">{kpis.pending}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Active</p><p className="mt-3 text-3xl font-semibold">{kpis.active}</p></div>
        </section>

        <section className="surface-card overflow-hidden">
          {loading ? (
            <div className="p-6 text-sm text-slate-500">Loading reminders...</div>
          ) : error ? (
            <div className="p-6 text-sm text-red-600">{error}</div>
          ) : (
            <Table columns={columns} rows={data.reminders} rowKey="id" />
          )}
        </section>
      </main>
    </div>
  )
}
