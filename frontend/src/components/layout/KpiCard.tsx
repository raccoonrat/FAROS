import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface KpiCardProps {
  title: string
  value: string | number
  description?: string
  icon?: LucideIcon
  trend?: {
    value: number
    label: string
    direction: 'up' | 'down' | 'neutral'
  }
  className?: string
  onClick?: () => void
}

export function KpiCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
  onClick,
}: KpiCardProps) {
  const trendColors = {
    up: 'text-success',
    down: 'text-destructive',
    neutral: 'text-muted-foreground',
  }

  return (
    <Card
      className={cn(
        'transition-all duration-200',
        onClick && 'cursor-pointer hover:shadow-md hover:-translate-y-0.5',
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-muted-foreground mb-1">
              {title}
            </p>
            <p className="text-3xl font-bold font-display tracking-tight">
              {value}
            </p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">
                {description}
              </p>
            )}
            {trend && (
              <div className={cn('text-xs font-medium mt-2', trendColors[trend.direction])}>
                {trend.direction === 'up' && '↑ '}
                {trend.direction === 'down' && '↓ '}
                {trend.value > 0 && '+'}
                {trend.value}% {trend.label}
              </div>
            )}
          </div>
          {Icon && (
            <div className="flex-shrink-0">
              <div className="p-3 rounded-lg bg-primary/10">
                <Icon className="h-6 w-6 text-primary" />
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
