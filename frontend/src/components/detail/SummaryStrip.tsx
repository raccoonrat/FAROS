import { ReactNode } from 'react'

interface SummaryStripProps {
  children: ReactNode
}

export function SummaryStrip({ children }: SummaryStripProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4 mb-6 hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3 flex-wrap">
        {children}
      </div>
    </div>
  )
}
