import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Code2, ArrowLeft, RefreshCw, Play, XCircle, CheckCircle2,
  Loader2, Clock, FileCode, ChevronDown, ChevronUp, Copy, ArrowRight
} from 'lucide-react'
import {
  getSession, getCandidates, getTrace, selectCandidate, startSession,
  CodeSession as CodeSessionType, CodeCandidate, TraceStep
} from '@/lib/api/code'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-800',
}

export function CodeSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const [session, setSession] = useState<CodeSessionType | null>(null)
  const [candidates, setCandidates] = useState<CodeCandidate[]>([])
  const [trace, setTrace] = useState<TraceStep[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null)
  const [isSelecting, setIsSelecting] = useState(false)

  const loadData = useCallback(async () => {
    if (!sessionId) return

    try {
      const [sessionData, candidatesData, traceData] = await Promise.all([
        getSession(sessionId),
        getCandidates(sessionId).catch(() => ({ candidates: [], total: 0 })),
        getTrace(sessionId).catch(() => ({ sessionId, steps: [] })),
      ])

      setSession(sessionData)
      setCandidates(candidatesData.candidates)
      setTrace(traceData.steps)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadData()
    const interval = setInterval(() => {
      if (session?.status === 'running' || session?.status === 'pending') {
        loadData()
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [loadData, session?.status])

  const handleStart = async () => {
    if (!sessionId) return
    try {
      await startSession(sessionId)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session')
    }
  }

  const handleSelect = async (candidateId: string) => {
    if (!sessionId) return
    setIsSelecting(true)
    try {
      await selectCandidate(sessionId, candidateId)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select candidate')
    } finally {
      setIsSelecting(false)
    }
  }

  const copyPatch = (patch: string) => {
    navigator.clipboard.writeText(patch)
  }

  if (isLoading) {
    return (
      <AppPageLayout title="Code Session" icon={Code2} iconColor="violet" accentColor="violet">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
        </div>
      </AppPageLayout>
    )
  }

  if (!session) {
    return (
      <AppPageLayout title="Code Session" icon={Code2} iconColor="violet" accentColor="violet">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Session not found</p>
          <Button variant="outline" onClick={() => navigate('/code')} className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard
          </Button>
        </div>
      </AppPageLayout>
    )
  }

  return (
    <AppPageLayout
      title="Code Session"
      subtitle={session.config.goal}
      icon={Code2}
      iconColor="violet"
      accentColor="violet"
    >
      <div className="flex items-center justify-between mb-6">
        <Button variant="outline" onClick={() => navigate('/code')}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>
        <div className="flex items-center gap-2">
          <Badge className={statusColors[session.status]}>
            {session.status === 'running' && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
            {session.status}
          </Badge>
          {session.status === 'pending' && (
            <Button onClick={handleStart} className="bg-violet-500 hover:bg-violet-600">
              <Play className="h-4 w-4 mr-2" /> Start Pipeline
            </Button>
          )}
          <Button variant="outline" onClick={loadData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Session Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Session Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div><span className="text-muted-foreground">ID:</span> {session.id}</div>
            <div><span className="text-muted-foreground">Repo:</span> {session.config.repoPath}</div>
            <div><span className="text-muted-foreground">Provider:</span> {session.config.providerName}</div>
            <div><span className="text-muted-foreground">Model:</span> {session.config.model}</div>
            <div><span className="text-muted-foreground">Created:</span> {new Date(session.createdAt).toLocaleString()}</div>
            {session.duration && <div><span className="text-muted-foreground">Duration:</span> {session.duration}s</div>}
            {session.currentStep && (
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Current Step:</span>
                <Badge variant="outline">{session.currentStep}</Badge>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pipeline Trace */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Clock className="h-4 w-4" /> Pipeline Trace
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trace.length === 0 ? (
              <p className="text-muted-foreground text-sm">No trace steps yet</p>
            ) : (
              <div className="space-y-2">
                {trace.map((step, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm">
                    <div className="w-24 font-mono text-xs text-muted-foreground">
                      {step.durationMs ? `${step.durationMs}ms` : '-'}
                    </div>
                    <Badge
                      variant="outline"
                      className={step.status === 'completed' ? 'border-green-300 text-green-700' :
                        step.status === 'failed' ? 'border-red-300 text-red-700' :
                          'border-blue-300 text-blue-700'}
                    >
                      {step.status === 'completed' && <CheckCircle2 className="h-3 w-3 mr-1" />}
                      {step.status === 'failed' && <XCircle className="h-3 w-3 mr-1" />}
                      {step.status === 'started' && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
                      {step.step}
                    </Badge>
                    {step.error && <span className="text-red-600 text-xs">{step.error}</span>}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Candidates */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCode className="h-5 w-5" /> Candidates ({candidates.length})
          </CardTitle>
          <CardDescription>Generated code solutions ranked by score</CardDescription>
        </CardHeader>
        <CardContent>
          {candidates.length === 0 ? (
            <p className="text-muted-foreground text-sm py-4 text-center">
              {session.status === 'running' ? 'Generating candidates...' : 'No candidates generated yet'}
            </p>
          ) : (
            <div className="space-y-4">
              {candidates.map((candidate) => (
                <div
                  key={candidate.id}
                  className={`border rounded-lg p-4 ${session.selectedCandidateId === candidate.id
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-200'
                    }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="font-mono">#{candidate.rank}</Badge>
                      <span className="font-medium">{candidate.title}</span>
                      {session.selectedCandidateId === candidate.id && (
                        <Badge className="bg-green-500">Selected</Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        Score: <span className="text-violet-600">{candidate.overallScore.toFixed(2)}</span>
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedCandidate(
                          expandedCandidate === candidate.id ? null : candidate.id
                        )}
                      >
                        {expandedCandidate === candidate.id ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Score breakdown */}
                  <div className="flex gap-4 text-xs text-muted-foreground mb-2">
                    <span>Correctness: {candidate.scores.correctness}</span>
                    <span>Completeness: {candidate.scores.completeness}</span>
                    <span>Efficiency: {candidate.scores.efficiency}</span>
                    <span>Readability: {candidate.scores.readability}</span>
                    <span>Safety: {candidate.scores.safety}</span>
                  </div>

                  {expandedCandidate === candidate.id && (
                    <div className="mt-4 space-y-4">
                      <div>
                        <h4 className="text-sm font-medium mb-1">Approach</h4>
                        <p className="text-sm text-muted-foreground">{candidate.approach}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium mb-1">Rationale</h4>
                        <p className="text-sm text-muted-foreground">{candidate.rationale}</p>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-medium">Patch</h4>
                          <Button variant="ghost" size="sm" onClick={() => copyPatch(candidate.patch)}>
                            <Copy className="h-3 w-3 mr-1" /> Copy
                          </Button>
                        </div>
                        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto max-h-96">
                          {candidate.patch}
                        </pre>
                      </div>
                      {session.status === 'completed' && !session.selectedCandidateId && (
                        <Button
                          onClick={() => handleSelect(candidate.id)}
                          disabled={isSelecting}
                          className="bg-green-500 hover:bg-green-600"
                        >
                          {isSelecting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                          Select This Candidate
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Next Step: Go to Runs when candidate is selected */}
      {session.selectedCandidateId && (
        <Card className="mt-6 border-blue-200 bg-blue-50">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-blue-900">Candidate Selected!</h3>
                <p className="text-sm text-blue-700">Proceed to monitor the execution run</p>
              </div>
              <Button onClick={() => navigate('/runs')} className="bg-blue-500 hover:bg-blue-600">
                Go to Runs <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </AppPageLayout>
  )
}
