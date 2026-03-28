import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { alerts } from '../data/mockData.js'

export default function AlertsPage() {
  const columns = [
    { key: 'patientName', header: 'Patient' },
    { key: 'type', header: 'Alert Type', render: (row) => <span className="uppercase">{row.type}</span> },
    { key: 'bp', header: 'BP' },
    { key: 'severity', header: 'Severity', render: (row) => <StatusBadge variant={row.severity}>{row.severity}</StatusBadge> },
    { key: 'explanation', header: 'Explanation' },
    { key: 'sentVia', header: 'Sent Via', render: (row) => <span className="uppercase">{row.sentVia}</span> },
    { key: 'triggeredAt', header: 'Triggered', render: (row) => formatDistanceToNow(new Date(row.triggeredAt), { addSuffix: true }) },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <Link to={`/patients/${row.patientId}`} className="text-sm font-semibold text-brand-700 hover:text-brand-800">
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
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Critical</p><p className="mt-3 text-3xl font-semibold">{alerts.filter((alert) => alert.severity === 'critical').length}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">High</p><p className="mt-3 text-3xl font-semibold">{alerts.filter((alert) => alert.severity === 'high').length}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Unresolved</p><p className="mt-3 text-3xl font-semibold">{alerts.filter((alert) => alert.status === 'unresolved').length}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Today</p><p className="mt-3 text-3xl font-semibold">{alerts.length}</p></div>
        </section>

        <section className="surface-card overflow-hidden">
          <Table columns={columns} rows={alerts} rowKey="id" />
        </section>
      </main>
    </div>
  )
}
