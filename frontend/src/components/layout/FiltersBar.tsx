import { ReactNode } from 'react'

interface FiltersBarProps {
  searchSlot?: ReactNode
  filterSlots?: ReactNode
  actionSlots?: ReactNode
  sticky?: boolean
}

export function FiltersBar({ searchSlot, filterSlots, actionSlots, sticky = false }: FiltersBarProps) {
  return (
    <div 
      className={`bg-white border border-slate-200 rounded-lg shadow-sm p-4 mb-6 ${
        sticky ? 'sticky top-4 z-10' : ''
      }`}
    >
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        {searchSlot && (
          <div className="flex-1 min-w-0">
            {searchSlot}
          </div>
        )}
        
        {filterSlots && (
          <div className="flex items-center gap-3 flex-wrap">
            {filterSlots}
          </div>
        )}
        
        {actionSlots && (
          <div className="flex items-center gap-2">
            {actionSlots}
          </div>
        )}
      </div>
    </div>
  )
}
