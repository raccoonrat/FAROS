import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { FileText } from 'lucide-react'
import { PlanGenerationPanel } from '@/components/plans/PlanGenerationPanel'

export function ResearchPlanning() {
  return (
    <AppPageLayout
      title="Plan"
      subtitle="Generate candidate research plans using AI-powered analysis"
      icon={FileText}
      iconColor="teal"
      accentColor="teal"
      headerViz="metricCapsules"
    >
      <PlanGenerationPanel />
    </AppPageLayout>
  )
}
