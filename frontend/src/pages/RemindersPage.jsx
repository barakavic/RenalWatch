import { format } from 'date-fns'
import { Link } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { reminders } from '../data/mockData.js'

export default function RemindersPage() {
  const columns = [
    { key: 'patientName', header: 'Patient' },
    { key: 'type', header: 'Reminder Type' },
    { key: 'dueAt', header: 'Due Time', render: (row) => format(new Date(row.dueAt), 'PPp') },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge variant={row.status}>{row.status}</StatusBadge> },
    { key: 'channel', header: 'Channel', render: (row) => <span className="uppercase">{row.channel}</span> },
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
          <h1 className="text-3xl font-semibold text-slate-900">Reminders</h1>
          <p className="text-slate-600">Track medication, blood pressure, and appointment reminder delivery.</p>
        </section>

        <section className="grid gap-4 md:grid-cols-4">
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Due Today</p><p className="mt-3 text-3xl font-semibold">{reminders.length}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Sent</p><p className="mt-3 text-3xl font-semibold">{reminders.filter((item) => item.status === 'sent').length}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Pending</p><p className="mt-3 text-3xl font-semibold">{reminders.filter((item) => item.status === 'pending').length}</p></div>
          <div className="surface-card p-5"><p className="text-sm text-slate-500">Active</p><p className="mt-3 text-3xl font-semibold">{reminders.filter((item) => item.status === 'active').length}</p></div>
        </section>

        <section className="surface-card overflow-hidden">
          <Table columns={columns} rows={reminders} rowKey="id" />
        </section>
      </main>
    </div>
  )
}
