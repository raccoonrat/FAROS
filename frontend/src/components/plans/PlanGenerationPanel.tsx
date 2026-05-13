import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Zap,
  History,
  ChevronDown,
  ChevronUp,
  Code2,
  ArrowRight,
  FileText,
} from 'lucide-react'
import { PAPER_TYPES_V2, getPaperTypeV2ById } from '@/lib/models/providers'

interface PlanSession {
  id: string
  status: string
  createdAt?: string
  config: {
    providerName: string
    model: string
    ideaSessionId?: string
    ideaCandidateId?: string
    ideaCandidateTitle?: string
    ideaSeedQuery?: string
    paperType: string
    directionId?: string
    directionTitle?: string
    maxCandidates: number
    userNotes?: string
  }
  candidateIds: string[]
  selectedCandidateId?: string
  resultingPlanId?: string
  errorMessage?: string
}

interface TraceStep {
  name: string
  status: string
  durationSeconds: number
  error?: string
}

interface TraceData {
  steps: TraceStep[]
  totalSteps: number
  successfulSteps: number
  failedSteps: number
}

interface ScoreBreakdown {
  novelty: number
  feasibility: number
  impact: number
  clarity: number
  risk: number
  overall: number
  rationale: string
}

interface CandidatePlan {
  id: string
  sessionId: string
  indexNumber: number
  title: string
  planAbstract: string
  novelty: string
  feasibility: string
  risks: string
  gapAnalysis: string
  method: string
  experimentDesign: Record<string, unknown> & {
    research_question?: string
    hypothesis?: string
  }
  evaluationProtocol: Record<string, unknown>
  ablations: string[]
  baselines: string[]
  resourcesEstimate: string
  scoreBreakdown: ScoreBreakdown
  overallScore: number
  createdAt: string
}

interface SessionListItem {
  id: string
  status: string
  createdAt: string
  config: {
    ideaCandidateTitle?: string
    ideaSeedQuery?: string
    paperType?: string
    directionTitle?: string
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/** Loaded from GET /api/v1/research/plans/{id} (e.g. after Ideas → Open in Planning) */
interface LinkedResearchPlan {
  id: string
  created_at: string
  research_question: string
  hypothesis: string
  variables: Record<string, unknown>
  methodology: Record<string, unknown>
  expected_outcomes: Record<string, unknown>
  tags: string[]
  notes: string
  source_session_id?: string | null
  source_candidate_id?: string | null
  source_candidate_index?: number | null
  source_title?: string | null
}

export function PlanGenerationPanel() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // Config state
  const [activeProvider, setActiveProvider] = useState('moonshot')
  const [activeModel, setActiveModel] = useState('moonshot-v1-8k')
  const [paperType, setPaperType] = useState('algorithmic_method')
  const [maxCandidates, setMaxCandidates] = useState(3)
  const [seedQuery, setSeedQuery] = useState('')
  const [directionTitle, setDirectionTitle] = useState('')
  const [userNotes, setUserNotes] = useState('')

  // Session state
  const [session, setSession] = useState<PlanSession | null>(null)
  const [trace, setTrace] = useState<TraceData | null>(null)
  const [candidates, setCandidates] = useState<CandidatePlan[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null)

  // Provider test
  const [providerTestResult, setProviderTestResult] = useState<{ ok: boolean; latencyMs?: number; error?: string } | null>(null)
  const [isTestingProvider, setIsTestingProvider] = useState(false)

  // Session history
  const [sessionHistory, setSessionHistory] = useState<SessionListItem[]>([])
  const [showHistory, setShowHistory] = useState(true)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [historyLoadError, setHistoryLoadError] = useState<string | null>(null)

  // Selection result
  const [selectedResult, setSelectedResult] = useState<{ researchPlanId: string; candidateId: string } | null>(null)

  // ResearchPlan opened via ?planId= (from Ideas "Open in Planning")
  const [linkedResearchPlan, setLinkedResearchPlan] = useState<LinkedResearchPlan | null>(null)
  const [linkedPlanLoading, setLinkedPlanLoading] = useState(false)
  const [linkedPlanError, setLinkedPlanError] = useState<string | null>(null)

  const planIdFromUrl = searchParams.get('planId')?.trim() || ''
  const ideaSessionIdFromUrl = searchParams.get('ideaSessionId')?.trim() || ''
  const ideaCandidateIdFromUrl = searchParams.get('ideaCandidateId')?.trim() || ''
  const ideaCandidateTitleFromUrl = searchParams.get('ideaCandidateTitle')?.trim() || ''
  const ideaSeedQueryFromUrl = searchParams.get('ideaSeedQuery')?.trim() || ''
  const hasIdeaLinkInUrl = !!(ideaSessionIdFromUrl && ideaCandidateIdFromUrl)

  /** Pre-fill topic fields when arriving from Ideas (only if inputs still empty). */
  useEffect(() => {
    if (ideaSeedQueryFromUrl) {
      setSeedQuery((s) => (s.trim() ? s : ideaSeedQueryFromUrl))
    }
    if (ideaCandidateTitleFromUrl) {
      setDirectionTitle((d) => (d.trim() ? d : ideaCandidateTitleFromUrl))
    }
  }, [ideaSeedQueryFromUrl, ideaCandidateTitleFromUrl])

  useEffect(() => {
    if (!planIdFromUrl) {
      setLinkedResearchPlan(null)
      setLinkedPlanError(null)
      setLinkedPlanLoading(false)
      return
    }
    let cancelled = false
    setLinkedPlanLoading(true)
    setLinkedPlanError(null)
    setLinkedResearchPlan(null)
    fetch(`${API_BASE}/api/v1/research/plans/${encodeURIComponent(planIdFromUrl)}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : `Failed to load plan (${r.status})`)
        return d as LinkedResearchPlan
      })
      .then((data) => {
        if (!cancelled) {
          setLinkedResearchPlan(data)
          setLinkedPlanLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setLinkedPlanError(err instanceof Error ? err.message : 'Failed to load research plan')
          setLinkedResearchPlan(null)
          setLinkedPlanLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [planIdFromUrl])

  const clearPlanIdFromUrl = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('planId')
    setSearchParams(next, { replace: true })
    setLinkedResearchPlan(null)
    setLinkedPlanError(null)
  }

  const clearIdeaLinkFromUrl = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('ideaSessionId')
    next.delete('ideaCandidateId')
    next.delete('ideaCandidateTitle')
    next.delete('ideaSeedQuery')
    setSearchParams(next, { replace: true })
  }

  useEffect(() => {
    loadSessionHistory()
    loadActiveLlmFromSettings()
  }, [])

  const loadActiveLlmFromSettings = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/v1/providers`)
      if (!r.ok) return
      const data = await r.json()
      const provider = data.activeProvider || 'moonshot'
      const providerInfo = (data.providers || []).find((p: { providerName: string; model: string }) => p.providerName === provider)
      setActiveProvider(provider)
      setActiveModel(providerInfo?.model || 'moonshot-v1-8k')
    } catch (err) {
      console.error('Failed to load active LLM from settings:', err)
    }
  }

  const loadSessionHistory = async () => {
    setIsLoadingHistory(true)
    setHistoryLoadError(null)
    try {
      const resp = await fetch(`${API_BASE}/api/v1/plans/sessions`)
      const data = await resp.json().catch(() => ({}))
      if (resp.ok) {
        setSessionHistory(data.sessions || [])
      } else {
        const detail = typeof data.detail === 'string' ? data.detail : `HTTP ${resp.status}`
        setHistoryLoadError(detail)
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load history'
      setHistoryLoadError(msg)
      console.error('Failed to load plan session history:', err)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const loadSession = async (sessionId: string) => {
    try {
      const sResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${sessionId}`)
      if (!sResp.ok) throw new Error('Session not found')
      const sData = await sResp.json()
      setSession(sData)
      setSeedQuery(sData.config.ideaSeedQuery || '')
      setDirectionTitle(sData.config.directionTitle || '')
      setPaperType(sData.config.paperType || 'algorithmic_method')
      setMaxCandidates(sData.config.maxCandidates)

      const tResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${sessionId}/trace`)
      if (tResp.ok) setTrace(await tResp.json())

      const cResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${sessionId}/candidates`)
      if (cResp.ok) { const d = await cResp.json(); setCandidates(d.candidates || []) }

      setShowHistory(true)
      setError(null)
      setSelectedResult(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session')
    }
  }

  const testProvider = async () => {
    setProviderTestResult(null)
    setIsTestingProvider(true)
    try {
      const resp = await fetch(`${API_BASE}/api/v1/providers/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Say OK', maxTokens: 10 }),
      })
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({}))
        setProviderTestResult({ ok: false, error: d.detail || `Error ${resp.status}` })
        return
      }
      setProviderTestResult(await resp.json())
    } catch (err) {
      setProviderTestResult({ ok: false, error: 'Backend unreachable' })
    } finally {
      setIsTestingProvider(false)
    }
  }

  const generatePlans = async () => {
    if (!seedQuery.trim() && !directionTitle.trim()) {
      setError('Enter a research topic or direction title')
      return
    }
    setIsLoading(true); setError(null); setSession(null); setTrace(null); setCandidates([]); setSelectedResult(null)
    try {
      await loadActiveLlmFromSettings()
      const createBody: Record<string, unknown> = {
        paperType,
        maxCandidates,
        ideaSeedQuery: seedQuery,
        directionTitle: directionTitle || seedQuery,
        userNotes: userNotes || undefined,
      }
      if (ideaSessionIdFromUrl && ideaCandidateIdFromUrl) {
        createBody.ideaSessionId = ideaSessionIdFromUrl
        createBody.ideaCandidateId = ideaCandidateIdFromUrl
        if (ideaCandidateTitleFromUrl) createBody.ideaCandidateTitle = ideaCandidateTitleFromUrl
      }

      const createResp = await fetch(`${API_BASE}/api/v1/plans/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createBody),
      })
      if (!createResp.ok) {
        const d = await createResp.json().catch(() => ({}))
        throw new Error(d.detail || `Failed: ${createResp.status}`)
      }
      const sessionData = await createResp.json()
      setSession(sessionData)

      const startResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${sessionData.id}/generate`, { method: 'POST' })
      if (!startResp.ok) throw new Error(`Failed to start: ${startResp.status}`)
      setSession(await startResp.json())
      setIsPolling(true)
      setShowHistory(true)
      void loadSessionHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  const pollSession = useCallback(async () => {
    if (!session?.id || !isPolling) return
    try {
      const sResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${session.id}`)
      const sData = await sResp.json()
      setSession(sData)

      const tResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${session.id}/trace`)
      if (tResp.ok) setTrace(await tResp.json())

      if (sData.status === 'completed' || sData.status === 'failed') {
        setIsPolling(false)
        if (sData.status === 'completed') {
          const cResp = await fetch(`${API_BASE}/api/v1/plans/sessions/${session.id}/candidates`)
          if (cResp.ok) { const d = await cResp.json(); setCandidates(d.candidates || []) }
        }
        setShowHistory(true)
        void loadSessionHistory()
      }
    } catch (err) { console.error('Polling error:', err) }
  }, [session?.id, isPolling])

  useEffect(() => {
    if (!isPolling) return
    const interval = setInterval(pollSession, 2000)
    return () => clearInterval(interval)
  }, [isPolling, pollSession])

  const selectCandidate = async (candidateId: string) => {
    if (!session?.id) return
    setError(null)
    try {
      const resp = await fetch(`${API_BASE}/api/v1/plans/sessions/${session.id}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidateId }),
      })
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({ detail: resp.statusText }))
        throw new Error(d.detail || `Failed: ${resp.status}`)
      }
      const data = await resp.json()
      if (data.ok && data.researchPlanId) {
        setSelectedResult({ researchPlanId: data.researchPlanId, candidateId })
        loadSessionHistory()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select candidate')
    }
  }

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStepIcon = (s: string) => {
    switch (s) {
      case 'ok': return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const navigateToCode = async (candidateId: string) => {
    if (!session?.id) return
    try {
      const resp = await fetch(`${API_BASE}/api/v1/code/plan-links`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planSessionId: session.id,
          candidateId,
          candidateIndex: candidates.find(c => c.id === candidateId)?.indexNumber,
        }),
      })
      if (!resp.ok) throw new Error('Failed to create plan link')
      const data = await resp.json()
      navigate(`/code?linkId=${data.linkId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to navigate to code')
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-100 text-green-800'
    if (score >= 6) return 'bg-amber-100 text-amber-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-6">
      {/* ResearchPlan from Ideas (?planId=) — same entity as POST /ideas/.../select */}
      {planIdFromUrl && (
        <Card className="border-teal-200 bg-gradient-to-r from-teal-50/80 to-emerald-50/50">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4 text-teal-600" />
                  Linked Research Plan
                </CardTitle>
                <CardDescription className="mt-1">
                  Opened from Ideas (plan ID in URL). This is stored under <span className="font-mono text-xs">/api/v1/research/plans</span>, not Plan Sessions below.
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={clearPlanIdFromUrl}>
                Dismiss
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {linkedPlanLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Loading plan…
              </div>
            )}
            {linkedPlanError && (
              <div className="p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-800 space-y-2">
                <p className="font-medium">Could not load this plan</p>
                <p>{linkedPlanError}</p>
                <p className="text-xs text-red-700">
                  Confirm the backend is running and the plan file exists under backend data (e.g. after a successful Ideas selection).
                </p>
              </div>
            )}
            {linkedResearchPlan && !linkedPlanLoading && (
              <div className="space-y-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="font-mono text-xs">
                    {linkedResearchPlan.id}
                  </Badge>
                  {linkedResearchPlan.source_title && (
                    <Badge variant="secondary" className="text-xs max-w-[280px] truncate" title={linkedResearchPlan.source_title}>
                      From idea: {linkedResearchPlan.source_title}
                    </Badge>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {new Date(linkedResearchPlan.created_at).toLocaleString()}
                  </span>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Research question</p>
                  <p className="mt-1 text-slate-900">{linkedResearchPlan.research_question}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Hypothesis</p>
                  <p className="mt-1 text-slate-900">{linkedResearchPlan.hypothesis}</p>
                </div>
                {(linkedResearchPlan.source_session_id || linkedResearchPlan.source_candidate_id) && (
                  <p className="text-xs text-muted-foreground">
                    Trace: session{' '}
                    <span className="font-mono">{linkedResearchPlan.source_session_id ?? '—'}</span>
                    {' · '}candidate{' '}
                    <span className="font-mono">{linkedResearchPlan.source_candidate_id ?? '—'}</span>
                  </p>
                )}
                {linkedResearchPlan.notes ? (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Notes</p>
                    <p className="mt-1 whitespace-pre-wrap text-slate-800">{linkedResearchPlan.notes}</p>
                  </div>
                ) : null}
                <details className="rounded-md border border-slate-200 bg-white/60 px-3 py-2">
                  <summary className="cursor-pointer text-xs font-medium text-slate-700">Variables, methodology, outcomes (JSON)</summary>
                  <pre className="mt-2 max-h-64 overflow-auto text-xs text-slate-700 whitespace-pre-wrap break-words">
                    {JSON.stringify(
                      {
                        variables: linkedResearchPlan.variables,
                        methodology: linkedResearchPlan.methodology,
                        expected_outcomes: linkedResearchPlan.expected_outcomes,
                        tags: linkedResearchPlan.tags,
                      },
                      null,
                      2
                    )}
                  </pre>
                </details>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {hasIdeaLinkInUrl && (
        <Card className="border-amber-200 bg-gradient-to-r from-amber-50/90 to-orange-50/50">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-600" />
                  Idea context for Plan Generation
                </CardTitle>
                <CardDescription className="mt-1">
                  The next <strong>Plan Generation</strong> run will send this Idea session/candidate to the backend so the LLM prompt includes your selected idea (see{' '}
                  <span className="font-mono text-xs">PlanSessionConfig.idea*</span>).
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={clearIdeaLinkFromUrl}>
                Clear link
              </Button>
            </div>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            {ideaCandidateTitleFromUrl && (
              <p>
                <span className="text-muted-foreground">Idea title:</span>{' '}
                <span className="font-medium text-slate-900">{ideaCandidateTitleFromUrl}</span>
              </p>
            )}
            <p className="text-xs text-muted-foreground font-mono break-all">
              ideaSessionId={ideaSessionIdFromUrl} · ideaCandidateId={ideaCandidateIdFromUrl}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Session History */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <History className="h-4 w-4 text-slate-500" />
              Plan Session History
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setShowHistory(!showHistory)}>
              {showHistory ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              <span className="ml-1">{sessionHistory.length} sessions</span>
            </Button>
          </div>
          <CardDescription className="text-xs text-muted-foreground pt-1">
            Lists only <strong>Plan Generation</strong> runs from this page (backend stores <span className="font-mono">psess_*</span>).
            Research plans created solely via <strong>Ideas</strong> → select candidate are tracked under Idea Session History, not here.
          </CardDescription>
        </CardHeader>
        {showHistory && (
          <CardContent>
            {isLoadingHistory ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><RefreshCw className="h-4 w-4 animate-spin" /> Loading...</div>
            ) : historyLoadError ? (
              <p className="text-sm text-destructive">{historyLoadError}</p>
            ) : sessionHistory.length === 0 ? (
              <p className="text-sm text-muted-foreground">No previous plan sessions — use Generate below at least once, or confirm the backend URL (VITE_API_BASE_URL).</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {sessionHistory.map((s) => (
                  <div key={s.id} className={`p-2 rounded border cursor-pointer hover:bg-slate-50 ${session?.id === s.id ? 'border-teal-400 bg-teal-50' : 'border-slate-200'}`} onClick={() => loadSession(s.id)}>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium truncate flex-1">
                        {s.config.ideaCandidateTitle || s.config.ideaSeedQuery || s.config.directionTitle || s.id}
                      </span>
                      <Badge className={getStatusColor(s.status)} variant="outline">{s.status}</Badge>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <span>{getPaperTypeV2ById(s.config.paperType || '')?.label || s.config.paperType}</span>
                      <span>•</span>
                      <span>{new Date(s.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Button variant="outline" size="sm" onClick={loadSessionHistory} className="mt-2"><RefreshCw className="h-3 w-3 mr-1" /> Refresh</Button>
          </CardContent>
        )}
      </Card>

      {/* Plan Generation Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5 text-teal-500" />Plan Generation</CardTitle>
          <CardDescription>Generate candidate research plans using AI-powered analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Research Topic / Seed Query</label>
            <textarea value={seedQuery} onChange={(e) => setSeedQuery(e.target.value)} placeholder="e.g., improving LLM reasoning with chain-of-thought prompting" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm min-h-[80px] focus:ring-2 focus:ring-teal-500" disabled={isPolling} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Direction Title (optional)</label>
            <input value={directionTitle} onChange={(e) => setDirectionTitle(e.target.value)} placeholder="e.g., Chain-of-Thought Reasoning" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-teal-500" disabled={isPolling} />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">LLM (from Settings)</label>
              <div className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm bg-slate-50">
                {activeProvider} / {activeModel}
              </div>
              <p className="text-xs text-muted-foreground">Uses active provider/model configured in Settings -&gt; LLM Providers</p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Paper Type</label>
              <select value={paperType} onChange={(e) => setPaperType(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" disabled={isPolling}>
                {PAPER_TYPES_V2.map(pt => (<option key={pt.id} value={pt.id}>{pt.label}</option>))}
              </select>
              <p className="text-xs text-muted-foreground">{getPaperTypeV2ById(paperType)?.description}</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Candidates: {maxCandidates}</label>
              <input type="range" min={1} max={5} value={maxCandidates} onChange={(e) => setMaxCandidates(parseInt(e.target.value))} className="w-full" disabled={isPolling} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Additional Notes (optional)</label>
              <input value={userNotes} onChange={(e) => setUserNotes(e.target.value)} placeholder="Any constraints or focus areas..." className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" disabled={isPolling} />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={testProvider} disabled={isPolling || isTestingProvider}>
              {isTestingProvider ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Zap className="h-4 w-4 mr-2" />}Test Provider
            </Button>
            <Button onClick={generatePlans} disabled={isLoading || isPolling || (!seedQuery.trim() && !directionTitle.trim())} className="bg-teal-500 hover:bg-teal-600">
              {isLoading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}Plan Generation
            </Button>
          </div>
          {providerTestResult && (
            <div className={`p-3 rounded-md ${providerTestResult.ok ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex items-center gap-2">
                {providerTestResult.ok ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-red-600" />}
                <span className={`text-sm font-medium ${providerTestResult.ok ? 'text-green-700' : 'text-red-700'}`}>
                  {providerTestResult.ok ? `Provider OK (${providerTestResult.latencyMs}ms)` : `Error: ${providerTestResult.error}`}
                </span>
              </div>
            </div>
          )}
          {error && (<div className="p-3 rounded-md bg-red-50 border border-red-200"><p className="text-sm text-red-700">{error}</p></div>)}
        </CardContent>
      </Card>

      {/* Session Progress */}
      {session && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Session: {session.id}</CardTitle>
              <Badge className={getStatusColor(session.status)}>{session.status}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {trace && trace.steps && trace.steps.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium mb-3">Pipeline Steps</h4>
                <div className="space-y-1">
                  {trace.steps.map((step, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 rounded bg-slate-50">
                      {getStepIcon(step.status)}
                      <span className="text-sm font-medium flex-1">{step.name}</span>
                      <span className="text-xs text-muted-foreground">{step.durationSeconds.toFixed(1)}s</span>
                      {step.error && <span className="text-xs text-red-500">{step.error}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {isPolling && (<div className="flex items-center gap-2 mt-4 text-sm text-muted-foreground"><RefreshCw className="h-4 w-4 animate-spin" /> Generating plans...</div>)}
            {session.errorMessage && (<div className="mt-3 p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">{session.errorMessage}</div>)}
          </CardContent>
        </Card>
      )}

      {/* Candidate Plans */}
      {candidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg"><Sparkles className="h-5 w-5 text-teal-500" />Candidate Plans ({candidates.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {candidates.map((c) => (
                <div key={c.id} className="p-4 rounded-lg border bg-gradient-to-r from-teal-50 to-emerald-50">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-teal-600">#{c.indexNumber}</span>
                      <h4 className="font-semibold">{c.title}</h4>
                    </div>
                    <Badge className={getScoreColor(c.overallScore)}>Score: {c.overallScore.toFixed(1)}</Badge>
                  </div>
                  {c.planAbstract && <p className="text-sm text-muted-foreground mb-2">{c.planAbstract}</p>}
                  <div className="grid grid-cols-5 gap-2 mb-3">
                    {(['novelty', 'feasibility', 'impact', 'clarity', 'risk'] as const).map((key) => (
                      <div key={key} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium capitalize">{key}</span>
                          <span className={getScoreColor(c.scoreBreakdown[key]) + ' px-1 rounded'}>{c.scoreBreakdown[key].toFixed(1)}</span>
                        </div>
                        <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                          <div className="h-full bg-teal-500 rounded-full" style={{ width: `${c.scoreBreakdown[key] * 10}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Expand/Collapse */}
                  <Button variant="ghost" size="sm" onClick={() => setExpandedCandidate(expandedCandidate === c.id ? null : c.id)} className="text-xs mb-2">
                    {expandedCandidate === c.id ? <><ChevronUp className="h-3 w-3 mr-1" /> Hide Details</> : <><ChevronDown className="h-3 w-3 mr-1" /> Show Details</>}
                  </Button>
                  {expandedCandidate === c.id && (
                    <div className="mb-3 p-3 bg-white/60 rounded text-xs space-y-2 border">
                      {c.method && <p><span className="font-medium text-teal-700">Method:</span> {c.method}</p>}
                      {c.novelty && <p><span className="font-medium text-purple-700">Novelty:</span> {c.novelty}</p>}
                      {c.feasibility && <p><span className="font-medium text-blue-700">Feasibility:</span> {c.feasibility}</p>}
                      {c.risks && <p><span className="font-medium text-red-700">Risks:</span> {c.risks}</p>}
                      {c.gapAnalysis && <p><span className="font-medium text-orange-700">Gap Analysis:</span> {c.gapAnalysis}</p>}
                      {c.resourcesEstimate && <p><span className="font-medium text-slate-700">Resources:</span> {c.resourcesEstimate}</p>}
                      {typeof c.experimentDesign?.research_question === 'string' && (
                        <div className="mt-2 p-2 bg-teal-50 rounded">
                          <p className="font-medium text-teal-800 mb-1">Experiment Design</p>
                          <p><span className="font-medium">Research Q:</span> {c.experimentDesign.research_question}</p>
                          {typeof c.experimentDesign.hypothesis === 'string' && (
                            <p><span className="font-medium">Hypothesis:</span> {c.experimentDesign.hypothesis}</p>
                          )}
                        </div>
                      )}
                      {c.scoreBreakdown.rationale && <p><span className="font-medium text-gray-700">Score Rationale:</span> {c.scoreBreakdown.rationale}</p>}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => selectCandidate(c.id)}
                      disabled={!!selectedResult || session?.selectedCandidateId === c.id}
                      className="bg-teal-500 hover:bg-teal-600">
                      <ArrowRight className="h-4 w-4 mr-2" />
                      {session?.selectedCandidateId === c.id ? 'Selected' : 'Select & Generate Plan'}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => {
                      if (session?.resultingPlanId || selectedResult?.researchPlanId) {
                        navigateToCode(c.id)
                      } else {
                        setError('Select a plan first to enable Code Generation')
                      }
                    }} disabled={!selectedResult && !session?.resultingPlanId}>
                      <Code2 className="h-4 w-4 mr-2" />Code Generation
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selection Success */}
      {selectedResult && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-semibold text-green-800">Research Plan Created!</p>
                <p className="text-sm text-green-700">Plan ID: {selectedResult.researchPlanId}</p>
              </div>
              <div className="ml-auto flex gap-2">
                <Button variant="outline" onClick={() => navigate('/runs')}>
                  <Zap className="h-4 w-4 mr-2" /> View Runs
                </Button>
                <Button variant="outline" onClick={() => navigateToCode(selectedResult.candidateId)}>
                  <Code2 className="h-4 w-4 mr-2" /> Code Generation
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Module Navigation Links */}
      <div className="flex justify-center gap-4 pt-2">
        <Button variant="ghost" size="sm" onClick={() => navigate('/ideas')} className="text-muted-foreground">
          <Sparkles className="h-4 w-4 mr-1" /> Ideas Module
        </Button>
        <Button variant="ghost" size="sm" onClick={() => navigate('/runs')} className="text-muted-foreground">
          <Zap className="h-4 w-4 mr-1" /> Runs Module
        </Button>
        <Button variant="ghost" size="sm" onClick={() => navigate('/research/workflows')} className="text-muted-foreground">
          <FileText className="h-4 w-4 mr-1" /> Workflows
        </Button>
      </div>
    </div>
  )
}
