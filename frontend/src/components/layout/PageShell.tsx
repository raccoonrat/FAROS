import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageShellProps {
  children: ReactNode
  className?: string
  title?: string
  subtitle?: string
  actions?: ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
}

export function PageShell({
  children,
  className,
  title,
  subtitle,
  actions,
  maxWidth = '2xl',
}: PageShellProps) {
  const maxWidthClasses = {
    sm: 'max-w-screen-sm',
    md: 'max-w-screen-md',
    lg: 'max-w-screen-lg',
    xl: 'max-w-screen-xl',
    '2xl': 'max-w-screen-2xl',
    full: 'max-w-full',
  }

  return (
    <div className={cn('min-h-full', className)}>
      {(title || subtitle || actions) && (
        <div className="border-b border-border bg-surface">
          <div className={cn('mx-auto px-6 py-8', maxWidthClasses[maxWidth])}>
            <div className="flex items-start justify-between gap-6">
              <div className="flex-1 min-w-0">
                {title && (
                  <h1 className="text-3xl font-bold font-display text-foreground tracking-tight">
                    {title}
                  </h1>
                )}
                {subtitle && (
                  <p className="mt-2 text-base text-muted-foreground max-w-3xl">
                    {subtitle}
                  </p>
                )}
              </div>
              {actions && (
                <div className="flex items-center gap-3 flex-shrink-0">
                  {actions}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <div className={cn('mx-auto px-6 py-8', maxWidthClasses[maxWidth])}>
        {children}
      </div>
    </div>
  )
}
