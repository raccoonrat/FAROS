import { ReactNode } from 'react'

interface MetaChipProps {
  label: string
  icon?: ReactNode
  variant?: 'default' | 'teal' | 'cyan' | 'indigo' | 'slate'
}

export function MetaChip({ label, icon, variant = 'default' }: MetaChipProps) {
  const variantClasses = {
    default: 'bg-slate-100 text-slate-700 border-slate-200',
    teal: 'bg-teal-50 text-teal-700 border-teal-200',
    cyan: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    slate: 'bg-slate-100 text-slate-600 border-slate-200'
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${variantClasses[variant]}`}>
      {icon}
      {label}
    </span>
  )
}

interface StatChipProps {
  label: string
  value: string | number
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

export function StatChip({ label, value, variant = 'default' }: StatChipProps) {
  const variantClasses = {
    default: 'bg-slate-50 border-slate-200',
    success: 'bg-green-50 border-green-200',
    warning: 'bg-amber-50 border-amber-200',
    danger: 'bg-red-50 border-red-200'
  }

  return (
    <div className={`inline-flex flex-col px-3 py-2 rounded-lg border ${variantClasses[variant]}`}>
      <span className="text-xs text-slate-600 font-medium">{label}</span>
      <span className="text-lg font-semibold text-slate-900">{value}</span>
    </div>
  )
}
