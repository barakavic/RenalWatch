import { useEffect, useMemo, useState } from 'react'
import { format, formatDistanceToNow } from 'date-fns'
import { ArrowLeft, BellRing, Phone, Send } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import TopNav from '../components/layout/TopNav.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import Table from '../components/ui/Table.jsx'
import { getDashboardPatient } from '../lib/api.js'

function parseBp(bp) {
  const [systolic, diastolic] = bp.split('/').map(Number)
  return { systolic, diastolic }
}

function buildLinePath(points, chartHeight, minValue, range) {
  return points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 100
      const y = ((chartHeight - ((point - minValue) / range) * chartHeight) / chartHeight) * 100
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')
}

function MiniTrendChart({ readings }) {
  if (readings.length === 0) {
    return <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">No reading trend yet.</div>
  }

  const values = readings.map((reading) => parseBp(reading.bp))
  const allValues = values.flatMap((reading) => [reading.systolic, reading.diastolic])
  const minValue = Math.min(...allValues) - 10
  const maxValue = Math.max(...allValues) + 10
  const range = Math.max(maxValue - minValue, 1)
  const chartHeight = 220
  const systolicPath = buildLinePath(values.map((reading) => reading.systolic), chartHeight, minValue, range)
  const diastolicPath = buildLinePath(values.map((reading) => reading.diastolic), chartHeight, minValue, range)

  return (
    <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-4 flex flex-wrap items-center gap-4 text-sm text-slate-500">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-brand-600" />
          Systolic
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-emerald-500" />
          Diastolic
        </div>
      </div>
      <div className="grid grid-cols-[auto_1fr] gap-3">
        <div className="flex h-[220px] flex-col justify-between pr-2 text-xs font-medium text-slate-400">
          {[maxValue, Math.round((maxValue + minValue) / 2), minValue].map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <div className="relative h-[220px]">
          <div className="absolute inset-0 flex flex-col justify-between">
            {[0, 1, 2, 3].map((line) => (
              <div key={line} className="border-t border-dashed border-slate-200" />
            ))}
          </div>
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="relative z-10 h-full w-full overflow-visible">
            <path d={systolicPath} fill="none" stroke="#2563eb" strokeWidth="2.5" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
            <path d={diastolicPath} fill="none" stroke="#10b981" strokeWidth="2.5" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
            {values.map((reading, index) => {
              const x = (index / Math.max(values.length - 1, 1)) * 100
              const systolicY = ((chartHeight - ((reading.systolic - minValue) / range) * chartHeight) / chartHeight) * 100
              const diastolicY = ((chartHeight - ((reading.diastolic - minValue) / range) * chartHeight) / chartHeight) * 100
              return (
                <g key={readings[index].id}>
                  <circle cx={x} cy={systolicY} r="2.2" fill="#2563eb" />
                  <circle cx={x} cy={diastolicY} r="2.2" fill="#10b981" />
                </g>
              )
            })}
          </svg>
          <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-500">
            {readings.map((reading) => (
              <span key={reading.id} className="truncate">
                {format(new Date(reading.time), 'MMM d')}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function PatientDetailPage() {
  const { patientId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadPatient() {
      try {
        setLoading(true)
        const response = await getDashboardPatient(patientId)
        if (!cancelled) {
          setData(response)
          setError('')
        }
      } catch (loadError) {
        if (!cancelled) {
          setError('Could not load patient dashboard.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadPatient()
    return () => {
      cancelled = true
    }
  }, [patientId])

  const patient = data?.patient
  const readingRows = useMemo(() => {
    return (data?.readings ?? []).map((reading) => ({
      id: reading.id,
      bp: `${Math.round(reading.systolic)}/${Math.round(reading.diastolic)}`,
      source: reading.source,
      time: reading.timestamp,
      anomaly: Boolean(reading.is_anomaly),
      severity: (reading.fuzzy_severity ?? 'low').toLowerCase(),
    }))
  }, [data])
  const patientAlerts = data?.alerts ?? []
  const patientReminderRows = data?.reminders ?? []
  const symptomLog = data?.symptom_log ?? null

  const columns = [
    { key: 'time', header: 'Timestamp', render: (row) => format(new Date(row.time), 'PPp') },
    { key: 'bp', header: 'BP' },
    { key: 'source', header: 'Source', render: (row) => <span className="capitalize">{row.source}</span> },
    { key: 'anomaly', header: 'Anomaly', render: (row) => <StatusBadge variant={row.anomaly ? 'critical' : 'low'}>{row.anomaly ? 'Yes' : 'No'}</StatusBadge> },
    { key: 'severity', header: 'Severity', render: (row) => <StatusBadge variant={row.severity}>{row.severity}</StatusBadge> },
  ]

  if (loading) {
    return (
      <div className="app-shell">
        <TopNav />
        <main className="page-container p-6 text-sm text-slate-500">Loading patient dashboard...</main>
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="app-shell">
        <TopNav />
        <main className="page-container p-6 text-sm text-red-600">{error || 'Patient not found.'}</main>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <TopNav />
      <main className="page-container space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-2">
            <Link to="/" className="inline-flex items-center gap-2 text-sm font-medium text-brand-700 hover:text-brand-800">
              <ArrowLeft className="h-4 w-4" />
              Back to patients
            </Link>
            <h1 className="text-3xl font-semibold text-slate-900">{patient.name}</h1>
            <p className="text-sm text-slate-500">Patient detail dashboard with blood pressure trends, alerts, reminders, and symptom context.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700">
              <Phone className="h-4 w-4" />
              Call Patient
            </button>
            <Link to="/reminders" className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700">
              <Send className="h-4 w-4" />
              Send Reminder
            </Link>
            <Link to="/alerts" className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white">
              <BellRing className="h-4 w-4" />
              View Alert History
            </Link>
          </div>
        </div>

        <section className="surface-card grid gap-6 p-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6">
            <div>
              <p className="section-title">Blood Pressure Trend</p>
              <p className="section-copy">Recent blood pressure activity for wearable and manual entries.</p>
              <MiniTrendChart readings={readingRows} />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <article className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-500">Latest BP</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">{patient.latest_bp ?? 'N/A'}</p>
                <p className="mt-2 text-sm text-slate-500">
                  {patient.latest_reading_at ? formatDistanceToNow(new Date(patient.latest_reading_at), { addSuffix: true }) : 'No recent reading'}
                </p>
              </article>
              <article className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-500">CKD Stage</p>
                <div className="mt-3">
                  <StatusBadge variant={`stage${patient.ckd_stage}`}>Stage {patient.ckd_stage}</StatusBadge>
                </div>
              </article>
              <article className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-500">Risk Level</p>
                <div className="mt-3">
                  <StatusBadge variant={patient.risk_level}>{patient.risk_level}</StatusBadge>
                </div>
              </article>
            </div>
            <div className="surface-card overflow-hidden border border-slate-200">
              <div className="border-b border-slate-200 px-5 py-4">
                <p className="section-title">Reading History</p>
              </div>
              <Table columns={columns} rows={readingRows} rowKey="id" />
            </div>
          </div>

          <div className="space-y-4">
            <article className="surface-card p-5">
              <p className="section-title">Clinical Insight</p>
              <p className="mt-1 text-sm text-slate-500">Latest ML-assisted interpretation for the patient record.</p>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Anomaly status</span>
                  <StatusBadge variant={patient.risk_level}>{patient.anomaly_status}</StatusBadge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Anomaly score</span>
                  <span className="text-sm font-semibold text-slate-900">
                    {patient.anomaly_score != null ? patient.anomaly_score.toFixed(4) : 'N/A'}
                  </span>
                </div>
                <p className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-700">
                  {patient.clinical_explanation ?? patient.summary ?? 'No interpretation yet.'}
                </p>
              </div>
            </article>

            <article className="surface-card p-5">
              <p className="section-title">Active Alerts</p>
              <div className="mt-4 space-y-3">
                {patientAlerts.length > 0 ? (
                  patientAlerts.map((alert) => (
                    <div key={alert.id} className="rounded-2xl bg-slate-50 p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-semibold text-slate-900">{alert.type.toUpperCase()} alert</p>
                          <p className="mt-1 text-sm text-slate-500">{alert.explanation}</p>
                        </div>
                        <StatusBadge variant={alert.severity}>{alert.severity}</StatusBadge>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No active alerts.</p>
                )}
              </div>
            </article>

            <article className="surface-card p-5">
              <p className="section-title">Symptom Log</p>
              {symptomLog ? (
                <div className="mt-4 space-y-3 text-sm text-slate-700">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl bg-slate-50 p-3">Fatigue: <strong>{symptomLog.fatigue}/10</strong></div>
                    <div className="rounded-xl bg-slate-50 p-3">Pain: <strong>{symptomLog.pain_level}/10</strong></div>
                    <div className="rounded-xl bg-slate-50 p-3">Swelling: <strong>{symptomLog.swelling}/10</strong></div>
                    <div className="rounded-xl bg-slate-50 p-3">Nausea: <strong>{symptomLog.nausea}/10</strong></div>
                  </div>
                  <p className="rounded-2xl bg-slate-50 p-4">{symptomLog.notes}</p>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">No recent symptom log found.</p>
              )}
            </article>

            <article className="surface-card p-5">
              <p className="section-title">Reminder Status</p>
              <div className="mt-4 space-y-3">
                {patientReminderRows.length > 0 ? (
                  patientReminderRows.map((reminder) => (
                    <div key={reminder.id} className="flex items-center justify-between rounded-2xl bg-slate-50 p-4">
                      <div>
                        <p className="font-semibold text-slate-900">{reminder.type}</p>
                        <p className="text-sm text-slate-500">{format(new Date(reminder.scheduled_at), 'PPp')}</p>
                      </div>
                      <StatusBadge variant={reminder.status}>{reminder.status}</StatusBadge>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No reminders for this patient.</p>
                )}
              </div>
            </article>
          </div>
        </section>
      </main>
    </div>
  )
}
