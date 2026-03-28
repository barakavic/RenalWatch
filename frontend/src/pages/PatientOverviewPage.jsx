import { AlertTriangle, HeartPulse, Search, TrendingUp, Users } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import KpiCard from '../components/ui/KpiCard.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { patients } from '../data/mockData.js'

function stageVariant(stage) {
  return `stage${stage}`
}

export default function PatientOverviewPage() {
  const kpis = {
    total: patients.length,
    critical: patients.filter((patient) => patient.riskLevel === 'critical').length,
    high: patients.filter((patient) => patient.riskLevel === 'high').length,
    active: patients.filter((patient) => patient.activeToday).length,
  }

  const columns = [
    {
      key: 'name',
      header: 'Patient',
      render: (patient) => (
        <div>
          <p className="font-semibold text-slate-900">{patient.name}</p>
          <p className="mt-1 text-xs text-slate-500">{patient.email}</p>
        </div>
      ),
    },
    { key: 'age', header: 'Age' },
    {
      key: 'ckdStage',
      header: 'CKD Stage',
      render: (patient) => <StatusBadge variant={stageVariant(patient.ckdStage)}>Stage {patient.ckdStage}</StatusBadge>,
    },
    {
      key: 'riskLevel',
      header: 'Risk',
      render: (patient) => <StatusBadge variant={patient.riskLevel}>{patient.riskLevel}</StatusBadge>,
    },
    { key: 'latestBp', header: 'Latest BP' },
    {
      key: 'latestReadingAt',
      header: 'Last Reading',
      render: (patient) => formatDistanceToNow(new Date(patient.latestReadingAt), { addSuffix: true }),
    },
    { key: 'phone', header: 'Phone' },
    {
      key: 'action',
      header: 'Actions',
      render: (patient) => (
        <Link
          to={`/patients/${patient.id}`}
          className="inline-flex items-center rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          View Dashboard
        </Link>
      ),
    },
  ]

  return (
    <div className="app-shell">
      <TopNav />
      <main className="page-container space-y-6">
        <section className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Patient Overview</h1>
          <p className="text-base text-slate-600">Monitor CKD patients with real-time BP tracking and identify high-risk cases early.</p>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard label="Total Patients" value={kpis.total} icon={Users} tone="default" />
          <KpiCard label="Critical Risk" value={kpis.critical} icon={AlertTriangle} tone="critical" />
          <KpiCard label="High Risk" value={kpis.high} icon={TrendingUp} tone="warning" />
          <KpiCard label="Active Today" value={kpis.active} icon={HeartPulse} tone="success" />
        </section>

        <section className="surface-card p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <label className="relative block w-full max-w-xl">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                placeholder="Search by patient name or phone"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm text-slate-700 outline-none transition focus:border-brand-300 focus:bg-white"
              />
            </label>
            <div className="flex flex-wrap gap-3">
              <select className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 outline-none">
                <option>All CKD Stages</option>
              </select>
              <select className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 outline-none">
                <option>All Risk Levels</option>
              </select>
              <select className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 outline-none">
                <option>Last 7 Days</option>
              </select>
            </div>
          </div>
        </section>

        <section className="surface-card overflow-hidden">
          <Table columns={columns} rows={patients} rowKey="id" />
        </section>
      </main>
    </div>
  )
}
