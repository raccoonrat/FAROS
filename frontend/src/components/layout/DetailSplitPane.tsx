import { ReactNode } from 'react'

interface DetailSplitPaneProps {
  leftContent: ReactNode
  rightContent: ReactNode
  rightTitle?: string
}

export function DetailSplitPane({ leftContent, rightContent, rightTitle }: DetailSplitPaneProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        {leftContent}
      </div>
      
      <div className="lg:col-span-1">
        <div className="sticky top-6">
          {rightTitle && (
            <h3 className="text-lg font-semibold text-slate-900 mb-4">
              {rightTitle}
            </h3>
          )}
          {rightContent}
        </div>
      </div>
    </div>
  )
}
