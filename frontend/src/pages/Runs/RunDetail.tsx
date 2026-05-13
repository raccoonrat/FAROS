import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { DetailSplitPane } from '@/components/layout/DetailSplitPane'
import { MetaChip } from '@/components/ui/MetaChips'
import { SummaryStrip } from '@/components/detail/SummaryStrip'
import { SectionCard } from '@/components/detail/SectionCard'
import { InfoGrid } from '@/components/detail/InfoGrid'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowLeft, Copy, CheckCircle, XCircle, Clock, ChevronDown, ChevronRight, ExternalLink, FileText, Zap, Map, Settings } from 'lucide-react'
import { useRun } from '@/lib/hooks/useApi'
import { formatDuration, formatBytes } from '@/lib/utils'
import type { Run, StepResult } from '@/lib/types'
import { getRunCategoryInfo, categoryGroups } from '@/lib/taxonomy/categories'
import { getTemplateById } from '@/lib/taxonomy/templates'

const statusVariants: Record<Run['status'], 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  completed: 'success',
  running: 'default',
  failed: 'destructive',
  pending: 'secondary',
  cancelled: 'warning',
}

const stepStatusIcons = {
  ok: <CheckCircle className="h-4 w-4 text-success" />,
  failed: <XCircle className="h-4 w-4 text-destructive" />,
  skipped: <Clock className="h-4 w-4 text-muted-foreground" />,
}

function StepAccordion({ step }: { step: StepResult }) {
  const [isOpen, setIsOpen] = useState(false)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="border rounded-md">
      <button
        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          {stepStatusIcons[step.status]}
          <div className="text-left">
            <div className="font-medium">{step.name}</div>
            <div className="text-xs text-muted-foreground">
              {formatDuration(step.durationSeconds)}
            </div>
          </div>
        </div>
        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>

      {isOpen && (
        <div className="border-t p-4 space-y-4 bg-muted/20">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium">Inputs</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(JSON.stringify(step.inputs, null, 2))}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
            <pre className="text-xs bg-background p-3 rounded border overflow-x-auto">
              {JSON.stringify(step.inputs, null, 2)}
            </pre>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium">Outputs</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(JSON.stringify(step.outputs, null, 2))}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
            <pre className="text-xs bg-background p-3 rounded border overflow-x-auto">
              {JSON.stringify(step.outputs, null, 2)}
            </pre>
          </div>

          {step.artifacts.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Artifacts ({step.artifacts.length})</h4>
              <ul className="text-xs space-y-1">
                {step.artifacts.map((artifact, i) => (
                  <li key={i} className="font-mono text-muted-foreground">{artifact}</li>
                ))}
              </ul>
            </div>
          )}

          {step.error && (
            <div>
              <h4 className="text-sm font-medium mb-2 text-destructive">Error</h4>
              <p className="text-xs text-destructive bg-destructive/10 p-3 rounded border border-destructive/20">
                {step.error}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function RunDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch run with polling enabled for running runs
  const { data: run, isLoading, error } = useRun(id!)

  // Enable polling when run is running
  useRun(id!, run?.status === 'running' ? 2000 : undefined)

  if (isLoading) {
    return (
      <AppPageLayout title="Loading..." subtitle="Fetching run details">
        <Skeleton className="h-96 w-full" />
      </AppPageLayout>
    )
  }

  if (error || !run) {
    return (
      <AppPageLayout title="Run Not Found" subtitle="Unable to load run details">
        <div className="bg-white border border-slate-200 rounded-lg p-8">
          <p className="text-center text-red-600">
            {error?.message || 'Run not found'}
          </p>
        </div>
      </AppPageLayout>
    )
  }

  const categoryInfo = getRunCategoryInfo(run)
  const template = run.config.templateId ? getTemplateById(run.config.templateId) : null
  const artifactsCount = run.trace?.steps.reduce((acc, s) => acc + s.artifacts.length, 0) || 0
  const lastError = run.trace?.steps.find(s => s.error)?.error

  return (
    <AppPageLayout
      title={`Run ${run.id.slice(0, 8)}`}
      subtitle={categoryInfo.label}
      headerViz="donut"
      headerVizData={[run.status === 'completed' ? 100 : run.status === 'running' ? 65 : run.status === 'failed' ? 30 : 0]}
      breadcrumb={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/runs')}
          className="hover:bg-slate-100"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Runs
        </Button>
      }
      actions={
        <Badge variant={statusVariants[run.status]} className="capitalize">
          {run.status}
        </Badge>
      }
    >
      {/* Run Summary Strip */}
      <SummaryStrip>
        <Badge variant={statusVariants[run.status]} className="capitalize">
          {run.status}
        </Badge>
        <MetaChip label={categoryInfo.label} variant="teal" />
        {categoryInfo.direction && (
          <MetaChip label={categoryInfo.direction.title} variant="cyan" />
        )}
        {template && (
          <MetaChip label={template.name} icon={<FileText className="h-3 w-3" />} variant="indigo" />
        )}
        <MetaChip label={new Date(run.startedAt).toLocaleDateString()} variant="slate" />
      </SummaryStrip>

      <DetailSplitPane
        leftContent={
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="steps">Steps</TabsTrigger>
              <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
              <TabsTrigger value="logs">Logs</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="space-y-6">
                {/* Top Status Strip */}
                <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
                  <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-600">Status:</span>
                      <Badge variant={statusVariants[run.status]} className="capitalize text-sm px-3 py-1">{run.status}</Badge>
                    </div>
                    <div className="h-6 w-px bg-slate-200" />
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-600">Type:</span>
                      <Badge variant="outline" className="capitalize text-sm px-3 py-1">{run.type}</Badge>
                    </div>
                    <div className="h-6 w-px bg-slate-200" />
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-600">Started:</span>
                      <span className="text-sm text-slate-900">{new Date(run.startedAt).toLocaleString()}</span>
                    </div>
                    {run.duration && (
                      <>
                        <div className="h-6 w-px bg-slate-200" />
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-slate-600">Duration:</span>
                          <span className="text-sm font-semibold text-teal-600">{formatDuration(run.duration)}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Execution Summary Dashboard */}
                <SectionCard title="Execution Summary" icon={Zap} accentColor="teal">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Lifecycle Group */}
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200" data-testid="lifecycle-group">
                      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-300">
                        <Clock className="h-4 w-4 text-slate-600" />
                        <h4 className="text-sm font-semibold text-slate-900">Lifecycle</h4>
                      </div>
                      <InfoGrid
                        columns={1}
                        items={[
                          {
                            label: 'Started',
                            value: new Date(run.startedAt).toLocaleString()
                          },
                          {
                            label: 'Ended',
                            value: run.endedAt ? new Date(run.endedAt).toLocaleString() : '—'
                          },
                          {
                            label: 'Duration',
                            value: run.duration ? formatDuration(run.duration) : '—'
                          },
                        ]}
                      />
                    </div>

                    {/* Compute & Policy Group */}
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200" data-testid="compute-group">
                      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-300">
                        <Settings className="h-4 w-4 text-slate-600" />
                        <h4 className="text-sm font-semibold text-slate-900">Compute & Policy</h4>
                      </div>
                      <InfoGrid
                        columns={1}
                        items={[
                          {
                            label: 'Model',
                            value: <span className="font-mono">{run.config.model}</span>
                          },
                          {
                            label: 'Paper Type',
                            value: run.config.paperType || '—'
                          },
                          {
                            label: 'Task Level (legacy)',
                            value: run.config.taskLevel
                          },
                          {
                            label: 'Max Iterations',
                            value: run.config.maxIterTimes
                          },
                          {
                            label: 'Steps',
                            value: run.trace ? `${run.trace.successfulSteps}/${run.trace.totalSteps}` : '—'
                          },
                        ]}
                      />
                    </div>
                  </div>
                </SectionCard>

                {/* Research Context Section */}
                <SectionCard title="Research Context" icon={Map} accentColor="cyan">
                  {(() => {
                    const categoryInfo = getRunCategoryInfo(run)
                    const template = run.config.templateId ? getTemplateById(run.config.templateId) : null

                    return (
                      <>
                        <div className="grid gap-6 md:grid-cols-2">
                          <div>
                            <h3 className="text-sm font-semibold text-slate-900 mb-3">Research Direction</h3>
                            {categoryInfo.direction ? (
                              <div className="space-y-3">
                                <p className="text-xs text-slate-500">
                                  {categoryGroups[categoryInfo.group!].label} › {categoryGroups[categoryInfo.group!].subgroupLabel}
                                </p>
                                <p className="font-semibold text-base text-slate-900">{categoryInfo.direction.title}</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {categoryInfo.direction.tags.map(tag => (
                                    <Badge key={tag} variant="secondary" className="text-xs">
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <p className="text-sm text-slate-600">{categoryInfo.label}</p>
                            )}
                          </div>

                          {template && (
                            <div>
                              <h3 className="text-sm font-semibold text-slate-900 mb-3">Template</h3>
                              <div className="space-y-2">
                                <p className="text-base font-semibold text-slate-900">{template.name}</p>
                                <p className="text-sm text-slate-600">{template.description}</p>
                                <div className="flex gap-2 mt-3">
                                  <Badge variant="outline">{template.config.model.split('-')[0]}</Badge>
                                  <Badge variant="outline">${template.config.budget || 'N/A'}</Badge>
                                  {template.estimatedDuration && (
                                    <Badge variant="outline">{template.estimatedDuration}</Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                        {categoryInfo.direction && (
                          <div className="mt-6 pt-6 border-t">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                const params = new URLSearchParams()
                                params.set('direction', categoryInfo.direction!.id)
                                if (run.config.templateId) {
                                  params.set('template', run.config.templateId)
                                }
                                navigate(`/research/planning?${params.toString()}`)
                              }}
                            >
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open in Planning
                            </Button>
                          </div>
                        )}
                      </>
                    )
                  })()}
                </SectionCard>
              </div>
            </TabsContent>

            <TabsContent value="timeline">
              <Card>
                <CardHeader>
                  <CardTitle>Execution Timeline</CardTitle>
                  <CardDescription>Step-by-step execution timeline</CardDescription>
                </CardHeader>
                <CardContent>
                  {run.trace ? (
                    <div className="relative pl-8 space-y-4">
                      <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border" />
                      {run.trace.steps.map((step, index) => (
                        <div key={index} className="relative">
                          <div className="absolute -left-[1.875rem] top-2 w-6 h-6 rounded-full border-2 bg-background flex items-center justify-center">
                            {step.status === 'ok' ? (
                              <CheckCircle className="h-3 w-3 text-success" />
                            ) : step.status === 'failed' ? (
                              <XCircle className="h-3 w-3 text-destructive" />
                            ) : (
                              <Clock className="h-3 w-3 text-muted-foreground" />
                            )}
                          </div>
                          <div className="bg-muted/50 rounded-md p-4">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">{step.name}</span>
                              <span className="text-xs text-muted-foreground">
                                {formatDuration(step.durationSeconds)}
                              </span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {new Date(step.startedAt).toLocaleTimeString()} → {new Date(step.endedAt).toLocaleTimeString()}
                            </div>
                            {step.error && (
                              <div className="mt-2 text-xs text-destructive">{step.error}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No trace data available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="steps">
              <Card>
                <CardHeader>
                  <CardTitle>Workflow Steps</CardTitle>
                  <CardDescription>Detailed step inputs, outputs, and artifacts</CardDescription>
                </CardHeader>
                <CardContent>
                  {run.trace ? (
                    <div className="space-y-2">
                      {run.trace.steps.map((step, index) => (
                        <StepAccordion key={index} step={step} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No step data available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="artifacts">
              <Card>
                <CardHeader>
                  <CardTitle>Artifacts ({run.artifacts.length})</CardTitle>
                  <CardDescription>Files and outputs generated by this run</CardDescription>
                </CardHeader>
                <CardContent>
                  {run.artifacts.length > 0 ? (
                    <div className="space-y-2">
                      {run.artifacts.map((artifact) => (
                        <div
                          key={artifact.id}
                          className="flex items-center justify-between p-3 border rounded-md hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex-1">
                            <div className="font-medium text-sm">{artifact.filename}</div>
                            <div className="text-xs text-muted-foreground">
                              {artifact.type} • {formatBytes(artifact.size)} • {new Date(artifact.createdAt).toLocaleString()}
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">
                            View
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No artifacts generated yet</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="logs">
              <Card>
                <CardHeader>
                  <CardTitle>Execution Logs</CardTitle>
                  <CardDescription>Runtime logs and debug information</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted/50 rounded-md p-4 font-mono text-xs space-y-1 max-h-96 overflow-y-auto">
                    {run.trace ? (
                      run.trace.steps.map((step, index) => (
                        <div key={index}>
                          <div className="text-muted-foreground">
                            [{new Date(step.startedAt).toISOString()}] INFO Starting step: {step.name}
                          </div>
                          {step.error ? (
                            <div className="text-destructive">
                              [{new Date(step.endedAt).toISOString()}] ERROR {step.error}
                            </div>
                          ) : (
                            <div className="text-success">
                              [{new Date(step.endedAt).toISOString()}] INFO Step completed: {step.name} ({formatDuration(step.durationSeconds)})
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-muted-foreground">No logs available</div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        }
        rightContent={
          < div className="space-y-4" >
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Metadata</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Type:</span>
                  <span className="font-medium">{run.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Model:</span>
                  <span className="font-mono text-xs">{run.config.model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Duration:</span>
                  <span>{run.duration ? formatDuration(run.duration) : '—'}</span>
                </div>
                {run.trace && (
                  <div className="flex justify-between">
                    <span className="text-slate-600">Steps:</span>
                    <span>{run.trace.successfulSteps}/{run.trace.totalSteps}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Artifacts</h3>
              <div className="text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Total artifacts:</span>
                  <Badge variant="outline">{artifactsCount}</Badge>
                </div>
              </div>
            </div>

            {
              lastError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-red-900 mb-2">Last Error</h3>
                  <p className="text-xs text-red-700">{lastError}</p>
                </div>
              )
            }
          </div >
        }
        rightTitle="Inspector"
      />
    </AppPageLayout >
  )
}
