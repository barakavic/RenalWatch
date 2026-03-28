export default function KpiCard({ label, value, icon: Icon, tone = 'default' }) {
  const toneClasses = {
    default: 'bg-brand-50 text-brand-600',
    success: 'bg-emerald-50 text-emerald-600',
    warning: 'bg-amber-50 text-amber-600',
    critical: 'bg-red-50 text-red-600',
  }

  return (
    <article className="surface-card flex items-center justify-between p-5">
      <div>
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <p className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">{value}</p>
      </div>
      <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${toneClasses[tone]}`}>
        <Icon className="h-6 w-6" />
      </div>
    </article>
  )
}
