import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

interface SectionCardProps {
  title: string
  icon?: LucideIcon
  accentColor?: string
  children: ReactNode
  actions?: ReactNode
}

export function SectionCard({
  title,
  icon: Icon,
  accentColor = 'teal',
  children,
  actions,
}: SectionCardProps) {
  const colorMap = {
    teal: {
      iconBg: 'bg-teal-50',
      iconText: 'text-teal-600',
      border: 'border-l-teal-500',
    },
    cyan: {
      iconBg: 'bg-cyan-50',
      iconText: 'text-cyan-600',
      border: 'border-l-cyan-500',
    },
    indigo: {
      iconBg: 'bg-indigo-50',
      iconText: 'text-indigo-600',
      border: 'border-l-indigo-500',
    },
    slate: {
      iconBg: 'bg-slate-50',
      iconText: 'text-slate-600',
      border: 'border-l-slate-500',
    },
    orange: {
      iconBg: 'bg-orange-50',
      iconText: 'text-orange-600',
      border: 'border-l-orange-500',
    },
  }

  const colors = colorMap[accentColor as keyof typeof colorMap] || colorMap.teal

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {Icon && (
            <div className={`h-8 w-8 rounded-lg ${colors.iconBg} flex items-center justify-center`}>
              <Icon className={`h-4 w-4 ${colors.iconText}`} />
            </div>
          )}
          <h2 className="text-xl font-semibold text-slate-900 tracking-tight">{title}</h2>
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <Card className={`border-l-4 ${colors.border} shadow-sm hover:shadow-md transition-shadow`}>
        <CardContent className="pt-6">
          {children}
        </CardContent>
      </Card>
    </div>
  )
}
