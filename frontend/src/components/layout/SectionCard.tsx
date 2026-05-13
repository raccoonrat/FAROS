import { ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface SectionCardProps {
  children: ReactNode
  className?: string
  title?: string
  description?: string
  actions?: ReactNode
  variant?: 'default' | 'elevated' | 'inset'
}

export function SectionCard({
  children,
  className,
  title,
  description,
  actions,
  variant = 'default',
}: SectionCardProps) {
  const variantClasses = {
    default: 'bg-card',
    elevated: 'bg-card shadow-md',
    inset: 'bg-muted/30',
  }

  return (
    <Card className={cn(variantClasses[variant], className)}>
      {(title || description || actions) && (
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              {title && <CardTitle>{title}</CardTitle>}
              {description && <CardDescription>{description}</CardDescription>}
            </div>
            {actions && (
              <div className="flex items-center gap-2 flex-shrink-0">
                {actions}
              </div>
            )}
          </div>
        </CardHeader>
      )}
      <CardContent className={cn(!title && !description && !actions && 'pt-6')}>
        {children}
      </CardContent>
    </Card>
  )
}
