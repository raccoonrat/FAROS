import { ReactNode } from 'react'

interface StackedPreviewLayoutProps {
  listPanel: ReactNode
  previewPanel: ReactNode
}

export function StackedPreviewLayout({ listPanel, previewPanel }: StackedPreviewLayoutProps) {
  return (
    <div className="space-y-6" data-testid="stacked-preview-layout">
      {/* Top: List/Search Panel */}
      <div className="w-full">
        {listPanel}
      </div>
      
      {/* Bottom: Preview Panel */}
      <div className="w-full bg-white border border-slate-200 rounded-lg shadow-sm">
        {previewPanel}
      </div>
    </div>
  )
}
