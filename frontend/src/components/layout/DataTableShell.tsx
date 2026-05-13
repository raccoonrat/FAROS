import { ReactNode } from 'react'

interface DataTableShellProps {
  title?: string
  count?: number
  loading?: boolean
  empty?: boolean
  emptyIcon?: ReactNode
  emptyTitle?: string
  emptyDescription?: string
  emptyAction?: ReactNode
  children: ReactNode
}

export function DataTableShell({
  title,
  count,
  loading,
  empty,
  emptyIcon,
  emptyTitle = 'No data',
  emptyDescription = 'Get started by creating your first item',
  emptyAction,
  children
}: DataTableShellProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
      {(title || count !== undefined) && (
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">
              {title}
            </h3>
            {count !== undefined && (
              <span className="text-sm text-slate-600">
                {count} {count === 1 ? 'item' : 'items'}
              </span>
            )}
          </div>
        </div>
      )}
      
      <div className="overflow-x-auto">
        {loading ? (
          <div className="p-8">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-4 py-3 border-b border-slate-100 last:border-0">
                <div className="h-4 bg-slate-200 rounded animate-pulse w-1/4" />
                <div className="h-4 bg-slate-200 rounded animate-pulse w-1/3" />
                <div className="h-4 bg-slate-200 rounded animate-pulse w-1/5" />
                <div className="h-4 bg-slate-200 rounded animate-pulse w-1/6" />
              </div>
            ))}
          </div>
        ) : empty ? (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            {emptyIcon && (
              <div className="mb-4 text-slate-300">
                {emptyIcon}
              </div>
            )}
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              {emptyTitle}
            </h3>
            <p className="text-sm text-slate-600 mb-6 max-w-md">
              {emptyDescription}
            </p>
            {emptyAction}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  )
}
