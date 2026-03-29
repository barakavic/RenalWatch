import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { getDashboardAlerts } from '../lib/api.js'

export default function AlertsPage() {
  const [data, setData] = useState({ kpis: null, alerts: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadAlerts() {
      try {
        setLoading(true)
        const response = await getDashboardAlerts()
        if (!cancelled) {
          setData(response)
          setError('')
        }
      } catch (loadError) {
        if (!cancelled) {
          setError('Could not load alerts.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadAlerts()
    return () => {
      cancelled = true
    }
  }, [])

  const kpis = data.kpis ?? { critical: 0, high: 0, unresolved: 0, today: 0 }

  const columns = [
    { key: 'patient_name', header: 'Patient' },
    { key: 'alert_type', header: 'Alert Type', render: (row) => <span className="uppercase">{row.alert_type}</span> },
    { key: 'severity', header: 'Severity', render: (row) => <StatusBadge variant={row.severity}>{row.severity}</StatusBadge> },
    { key: 'explanation', header: 'Explanation' },
    { key: 'sent_via', header: 'Sent Via', render: (row) => <span className="uppercase">{row.sent_via}</span> },
    { key: 'triggered_at', header: 'Triggered', render: (row) => formatDistanceToNow(new Date(row.triggered_at), { addSuffix: true }) },
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
          <h1 className="text-3xl font-semibold text-slate-900">Alerts Center</h1>
          <p className="text-slate-600">Review critical and high-risk patient events before escalation.</p>
        </section>

        <section className="grid gap-4 md:grid-cols-4">
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Critical</p><p className="mt-3 text-3xl font-semibold">{kpis.critical}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">High</p><p className="mt-3 text-3xl font-semibold">{kpis.high}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Unresolved</p><p className="mt-3 text-3xl font-semibold">{kpis.unresolved}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Today</p><p className="mt-3 text-3xl font-semibold">{kpis.today}</p></div>
        </section>

        <section className="surface-card overflow-hidden">
          {loading ? (
            <div className="p-6 text-sm text-slate-500">Loading alerts...</div>
          ) : error ? (
            <div className="p-6 text-sm text-red-600">{error}</div>
          ) : (
            <Table columns={columns} rows={data.alerts} rowKey="id" />
          )}
        </section>
      </main>
    </div>
  )
}
