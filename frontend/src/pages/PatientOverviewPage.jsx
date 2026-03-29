import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, HeartPulse, Search, TrendingUp, Users } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import KpiCard from '../components/ui/KpiCard.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { getDashboardOverview } from '../lib/api.js'

function stageVariant(stage) {
  return `stage${stage}`
}

export default function PatientOverviewPage() {
  const [overview, setOverview] = useState({ kpis: null, patients: [] })
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadOverview() {
      try {
        setLoading(true)
        const data = await getDashboardOverview()
        if (!cancelled) {
          setOverview(data)
          setError('')
        }
      } catch (loadError) {
        if (!cancelled) {
          setError('Could not load dashboard overview.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadOverview()
    return () => {
      cancelled = true
    }
  }, [])

  const filteredPatients = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) {
      return overview.patients
    }

    return overview.patients.filter((patient) => {
      return (
        patient.name.toLowerCase().includes(needle) ||
        (patient.phone ?? '').toLowerCase().includes(needle) ||
        (patient.email ?? '').toLowerCase().includes(needle)
      )
    })
  }, [overview.patients, query])

  const kpis = overview.kpis ?? {
    total_patients: 0,
    critical_risk: 0,
    high_risk: 0,
    active_today: 0,
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
      key: 'ckd_stage',
      header: 'CKD Stage',
      render: (patient) => <StatusBadge variant={stageVariant(patient.ckd_stage)}>Stage {patient.ckd_stage}</StatusBadge>,
    },
    {
      key: 'risk_level',
      header: 'Risk',
      render: (patient) => <StatusBadge variant={patient.risk_level}>{patient.risk_level}</StatusBadge>,
    },
    { key: 'latest_bp', header: 'Latest BP' },
    {
      key: 'latest_reading_at',
      header: 'Last Reading',
      render: (patient) =>
        patient.latest_reading_at ? formatDistanceToNow(new Date(patient.latest_reading_at), { addSuffix: true }) : 'No reading yet',
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
          <KpiCard label="Total Patients" value={kpis.total_patients} icon={Users} tone="default" />
          <KpiCard label="Critical Risk" value={kpis.critical_risk} icon={AlertTriangle} tone="critical" />
          <KpiCard label="High Risk" value={kpis.high_risk} icon={TrendingUp} tone="warning" />
          <KpiCard label="Active Today" value={kpis.active_today} icon={HeartPulse} tone="success" />
        </section>

        <section className="surface-card p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <label className="relative block w-full max-w-xl">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                placeholder="Search by patient name or phone"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
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
          {loading ? (
            <div className="p-6 text-sm text-slate-500">Loading patients...</div>
          ) : error ? (
            <div className="p-6 text-sm text-red-600">{error}</div>
          ) : (
            <Table columns={columns} rows={filteredPatients} rowKey="id" />
          )}
        </section>
      </main>
    </div>
  )
}
