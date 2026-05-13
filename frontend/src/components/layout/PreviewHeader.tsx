import { ReactNode } from 'react'

interface PreviewHeaderProps {
  icon?: ReactNode
  title: string
  metadata?: string
  actions?: ReactNode
}

export function PreviewHeader({ icon, title, metadata, actions }: PreviewHeaderProps) {
  return (
    <div className="space-y-3 pb-4 border-b border-slate-200" data-testid="preview-header">
      {/* Row 1: Title area with icon and metadata */}
      <div className="flex items-center gap-2 min-w-0" data-testid="preview-title">
        {icon && <div className="shrink-0">{icon}</div>}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 truncate">{title}</h3>
          {metadata && (
            <p className="text-xs text-slate-600 mt-0.5">{metadata}</p>
          )}
        </div>
      </div>
      
      {/* Row 2: Actions row with flex-wrap to prevent overlap */}
      {actions && (
        <div className="flex items-center gap-2 flex-wrap" data-testid="preview-actions">
          {actions}
        </div>
      )}
    </div>
  )
}
