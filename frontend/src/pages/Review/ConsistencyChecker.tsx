import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, AlertTriangle, Info, CheckCircle, ExternalLink, Shield } from 'lucide-react'
import { usePapers, useReviewFindings } from '@/lib/hooks/useApi'

const severityIcons = {
  blocker: <AlertCircle className="h-4 w-4 text-destructive" />,
  major: <AlertTriangle className="h-4 w-4 text-orange-500" />,
  minor: <Info className="h-4 w-4 text-blue-500" />,
  info: <CheckCircle className="h-4 w-4 text-muted-foreground" />,
}

const severityVariants = {
  blocker: 'destructive' as const,
  major: 'default' as const,
  minor: 'secondary' as const,
  info: 'outline' as const,
}

export function ConsistencyChecker() {
  const { data: papers, isLoading: papersLoading } = usePapers()
  const [selectedPaperId, setSelectedPaperId] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: findings, isLoading: findingsLoading } = useReviewFindings(selectedPaperId)

  const filteredFindings = useMemo(() => {
    if (!findings) return []

    return findings.filter((finding) => {
      if (severityFilter !== 'all' && finding.severity !== severityFilter) return false
      if (searchQuery && !finding.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !finding.description.toLowerCase().includes(searchQuery.toLowerCase())) return false
      return true
    })
  }, [findings, severityFilter, searchQuery])

  const groupedFindings = useMemo(() => {
    const groups: Record<string, typeof filteredFindings> = {
      blocker: [],
      major: [],
      minor: [],
      info: [],
    }

    filteredFindings.forEach((finding) => {
      groups[finding.severity].push(finding)
    })

    return groups
  }, [filteredFindings])

  const severityCounts = useMemo(() => {
    if (!findings) return { blocker: 0, major: 0, minor: 0, info: 0 }
    return findings.reduce((acc, f) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1
      return acc
    }, {} as Record<string, number>)
  }, [findings])

  return (
    <AppPageLayout
      title="Consistency Checker"
      subtitle="Validate research outputs for consistency and quality"
      icon={Shield}
      iconColor="orange"
      accentColor="orange"
      headerViz="metricCapsules"
    >
      {/* Summary Dashboard */}
      {selectedPaperId && findings && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="border-l-4 border-l-red-500 bg-gradient-to-br from-red-50/50 to-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Blockers</p>
                  <p className="text-3xl font-bold text-red-600">{severityCounts.blocker || 0}</p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-orange-500 bg-gradient-to-br from-orange-50/50 to-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Major Issues</p>
                  <p className="text-3xl font-bold text-orange-600">{severityCounts.major || 0}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-blue-500 bg-gradient-to-br from-blue-50/50 to-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Minor Issues</p>
                  <p className="text-3xl font-bold text-blue-600">{severityCounts.minor || 0}</p>
                </div>
                <Info className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-teal-500 bg-gradient-to-br from-teal-50/50 to-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Info</p>
                  <p className="text-3xl font-bold text-teal-600">{severityCounts.info || 0}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-teal-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="shadow-md">
        <CardHeader className="bg-gradient-to-r from-slate-50 to-white border-b">
          <CardTitle className="text-xl">Run Consistency Check</CardTitle>
          <CardDescription>Check citations, references, and formatting</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Select Paper</label>
            {papersLoading ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <select
                className="w-full rounded-md border-2 border-slate-200 bg-white px-4 py-2.5 text-sm font-medium hover:border-teal-500 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 transition-colors"
                value={selectedPaperId}
                onChange={(e) => setSelectedPaperId(e.target.value)}
              >
                <option value="">Select a paper...</option>
                {papers?.map((paper) => (
                  <option key={paper.id} value={paper.id}>
                    {paper.title}
                  </option>
                ))}
              </select>
            )}
          </div>
          <Button
            disabled={!selectedPaperId}
            className="bg-teal-600 hover:bg-teal-700"
            size="lg"
          >
            Run Consistency Check
          </Button>
        </CardContent>
      </Card>

      {selectedPaperId && (
        <Card className="shadow-md">
          <CardHeader className="bg-gradient-to-r from-slate-50 to-white border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl">Audit Results ({filteredFindings.length})</CardTitle>
                <CardDescription>Consistency check results grouped by severity</CardDescription>
              </div>
              <Badge variant="outline" className="text-sm px-3 py-1">
                {filteredFindings.length} findings
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            <div className="flex gap-3">
              <select
                className="rounded-md border-2 border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:border-teal-500 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 transition-colors"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="all">All Severities</option>
                <option value="blocker">🔴 Blocker</option>
                <option value="major">🟠 Major</option>
                <option value="minor">🔵 Minor</option>
                <option value="info">✓ Info</option>
              </select>
              <input
                type="search"
                placeholder="Search findings..."
                className="flex-1 rounded-md border-2 border-slate-200 bg-white px-4 py-2 text-sm hover:border-teal-500 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 transition-colors"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {findingsLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : filteredFindings.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No findings. Paper looks good!
              </div>
            ) : (
              <div className="space-y-8">
                {Object.entries(groupedFindings).map(([severity, items]) =>
                  items.length > 0 && (
                    <div key={severity} className="space-y-3">
                      <div className="flex items-center gap-3 pb-2 border-b-2" style={{
                        borderColor: severity === 'blocker' ? '#ef4444' :
                          severity === 'major' ? '#f97316' :
                            severity === 'minor' ? '#3b82f6' : '#14b8a6'
                      }}>
                        {severityIcons[severity as keyof typeof severityIcons]}
                        <h3 className="text-lg font-bold capitalize text-slate-900">{severity}</h3>
                        <Badge variant="outline" className="ml-auto">{items.length} issues</Badge>
                      </div>
                      <div className="space-y-3">
                        {items.map((finding) => (
                          <Card key={finding.id} className="border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{
                            borderLeftColor: severity === 'blocker' ? '#ef4444' :
                              severity === 'major' ? '#f97316' :
                                severity === 'minor' ? '#3b82f6' : '#14b8a6'
                          }}>
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-2">
                                    <CardTitle className="text-base font-semibold text-slate-900">{finding.title}</CardTitle>
                                    <Badge variant={severityVariants[severity as keyof typeof severityVariants]} className="capitalize text-xs">
                                      {severity}
                                    </Badge>
                                  </div>
                                  <CardDescription className="text-sm leading-relaxed">
                                    {finding.description}
                                  </CardDescription>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              {finding.evidence && (
                                <div className="bg-slate-50 border-l-2 border-slate-300 rounded-r-md">
                                  <div className="px-4 py-2 bg-slate-100 border-b border-slate-200">
                                    <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Evidence</span>
                                  </div>
                                  <div className="p-4">
                                    <pre className="text-xs font-mono text-slate-700 whitespace-pre-wrap leading-relaxed">
                                      {finding.evidence}
                                    </pre>
                                  </div>
                                </div>
                              )}

                              {finding.suggestedFix && (
                                <div className="bg-teal-50 border-l-2 border-teal-400 rounded-r-md">
                                  <div className="px-4 py-2 bg-teal-100 border-b border-teal-200">
                                    <span className="text-xs font-semibold text-teal-800 uppercase tracking-wide">Suggested Fix</span>
                                  </div>
                                  <div className="p-4">
                                    <p className="text-sm text-teal-900 leading-relaxed">{finding.suggestedFix}</p>
                                  </div>
                                </div>
                              )}

                              <div className="flex items-center gap-2 pt-3 border-t">
                                {finding.relatedRunId && (
                                  <Link to={`/runs/${finding.relatedRunId}`}>
                                    <Button variant="outline" size="sm" className="hover:bg-teal-50 hover:border-teal-500">
                                      <ExternalLink className="h-3 w-3 mr-2" />
                                      View Run
                                    </Button>
                                  </Link>
                                )}
                                {finding.relatedArtifactId && (
                                  <Link to="/artifacts">
                                    <Button variant="outline" size="sm" className="hover:bg-teal-50 hover:border-teal-500">
                                      <ExternalLink className="h-3 w-3 mr-2" />
                                      View Artifact
                                    </Button>
                                  </Link>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </AppPageLayout>
  )
}
