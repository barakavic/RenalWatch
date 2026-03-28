import { Activity, Bell, CalendarClock, UserRound } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Patients', to: '/' },
  { label: 'Alerts', to: '/alerts' },
  { label: 'Reminders', to: '/reminders' },
]

function navClassName({ isActive }) {
  return [
    'rounded-full px-4 py-2 text-sm font-medium transition',
    isActive ? 'bg-brand-50 text-brand-700 shadow-sm' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900',
  ].join(' ')
}

export default function TopNav() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="page-container flex flex-col gap-4 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 shadow-panel">
            <Activity className="h-6 w-6 text-white" />
          </div>
          <div>
            <p className="text-xl font-semibold text-slate-900">RenalWatch</p>
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Doctor Portal</p>
          </div>
        </div>

        <nav className="flex items-center gap-2 rounded-full bg-slate-100 p-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={navClassName}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-3 self-end md:self-auto">
          <div className="text-right">
            <p className="text-sm font-semibold text-slate-900">Dr. Mwangi</p>
            <p className="text-xs text-slate-500">Nephrologist</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-500">
            <UserRound className="h-5 w-5" />
          </div>
          <div className="hidden h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-500 lg:flex">
            <CalendarClock className="h-5 w-5" />
          </div>
          <div className="hidden h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-500 lg:flex">
            <Bell className="h-5 w-5" />
          </div>
        </div>
      </div>
    </header>
  )
}
