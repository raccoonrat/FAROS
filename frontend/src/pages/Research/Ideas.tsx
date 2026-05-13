import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { IdeaGenerationPanel } from '@/components/ideas/IdeaGenerationPanel'
import { Lightbulb } from 'lucide-react'

export function ResearchIdeas() {
  return (
    <AppPageLayout
      title="Idea Generation"
      subtitle="Generate novel research ideas using AI-powered analysis"
      icon={Lightbulb}
      iconColor="amber"
      accentColor="amber"
      headerViz="metricCapsules"
    >
      <IdeaGenerationPanel />
    </AppPageLayout>
  )
}
