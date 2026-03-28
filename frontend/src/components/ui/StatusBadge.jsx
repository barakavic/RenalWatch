const variants = {
  low: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  medium: 'bg-amber-50 text-amber-700 ring-amber-200',
  high: 'bg-orange-50 text-orange-700 ring-orange-200',
  critical: 'bg-red-50 text-red-700 ring-red-200',
  stage1: 'bg-blue-50 text-blue-700 ring-blue-200',
  stage2: 'bg-slate-100 text-slate-700 ring-slate-200',
  stage3: 'bg-orange-50 text-orange-700 ring-orange-200',
  stage4: 'bg-red-50 text-red-700 ring-red-200',
  stage5: 'bg-rose-100 text-rose-700 ring-rose-200',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  pending: 'bg-amber-50 text-amber-700 ring-amber-200',
  sent: 'bg-blue-50 text-blue-700 ring-blue-200',
}

export default function StatusBadge({ children, variant = 'low' }) {
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ring-1 ${variants[variant] ?? variants.low}`}>
      {children}
    </span>
  )
}
