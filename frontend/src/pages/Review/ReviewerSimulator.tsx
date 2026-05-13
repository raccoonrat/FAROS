import { useState, useEffect, useCallback } from 'react'
import { LLM_PROVIDERS, getModelsByProvider } from '@/lib/models/providers'
import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  CheckCircle, ThumbsUp, ThumbsDown, HelpCircle, AlertTriangle, Loader2,
  RefreshCw, FileText, Target, Zap, ArrowRight, Check,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

interface Paper { id: string; title: string; paperType: string; status: string }

interface ActionItem {
  description: string
  section: string
  severity: string
  targetModule: string
  suggestedEdit: string
}

interface Review {
  id: string
  paperId: string
  reviewerProfile: string
  providerName: string
  model: string
  status: string
  scoreSuggestion: number | null
  jsonReport: {
    overallAssessment?: string
    strengths?: string[]
    weaknesses?: string[]
    questions?: string[]
    missingExperiments?: string[]
    writingIssues?: string[]
  } | null
  markdownReport: string | null
  actionItems: ActionItem[]
  createdAt: string
  updatedAt: string
}

interface ImprovementRequest {
  id: string
  reviewId: string
  paperId: string
  targetModule: string
  description: string
  severity: string
  sectionPointer: string
  suggestedEdit: string
  status: string
  createdAt: string
}

const severityColors: Record<string, string> = {
  BLOCKER: 'bg-red-100 text-red-800 border-red-300',
  MAJOR: 'bg-orange-100 text-orange-800 border-orange-300',
  MINOR: 'bg-yellow-100 text-yellow-800 border-yellow-300',
}

const moduleColors: Record<string, string> = {
  papers: 'bg-indigo-100 text-indigo-800',
  experiments: 'bg-green-100 text-green-800',
  code: 'bg-purple-100 text-purple-800',
}

export function ReviewerSimulator() {
  const [papers, setPapers] = useState<Paper[]>([])
  const [reviews, setReviews] = useState<Review[]>([])
  const [requests, setRequests] = useState<ImprovementRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPaperId, setSelectedPaperId] = useState('')
  const [selectedReview, setSelectedReview] = useState<Review | null>(null)
  const [reviewTab, setReviewTab] = useState('actions')
  const [generating, setGenerating] = useState(false)
  const [applying, setApplying] = useState(false)
  const [selectedActions, setSelectedActions] = useState<Set<number>>(new Set())
  const [provider, setProvider] = useState('')
  const [model, setModel] = useState('')

  const loadPapers = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/papers`)
      if (resp.ok) {
        const data = await resp.json()
        setPapers(data.papers || [])
      }
    } catch { void 0 }
  }, [])

  const loadReviews = useCallback(async () => {
    const url = selectedPaperId
      ? `${API_BASE}/api/v1/reviews?paperId=${selectedPaperId}`
      : `${API_BASE}/api/v1/reviews`
    try {
      const resp = await fetch(url)
      if (resp.ok) {
        const data = await resp.json()
        setReviews(data.reviews || [])
      }
    } catch { void 0 }
  }, [selectedPaperId])

  const loadRequests = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/reviews/requests`)
      if (resp.ok) {
        const data = await resp.json()
        setRequests(data.requests || [])
      }
    } catch { void 0 }
  }, [])

  useEffect(() => {
    Promise.all([loadPapers(), loadReviews(), loadRequests()]).then(() => setLoading(false))
  }, [loadPapers, loadReviews, loadRequests])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/v1/providers`)
        if (!resp.ok || cancelled) return
        const data = await resp.json()
        const providerName = data.activeProvider || ''
        const providerInfo = (data.providers || []).find((p: { providerName: string; model: string }) => p.providerName === providerName)
        if (!cancelled) {
          setProvider(providerName)
          setModel(providerInfo?.model || getModelsByProvider(providerName)[0]?.id || '')
        }
      } catch {
        if (!cancelled) {
          setProvider('')
          setModel('')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => { loadReviews() }, [loadReviews])

  const createReview = async () => {
    if (!selectedPaperId) return
    setGenerating(true)
    try {
      const resp = await fetch(`${API_BASE}/api/v1/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paperId: selectedPaperId, providerName: provider || undefined, model: model || undefined }),
      })
      if (resp.ok) {
        const rev = await resp.json()
        // Poll until done
        for (let i = 0; i < 40; i++) {
          await new Promise(r => setTimeout(r, 3000))
          const rr = await fetch(`${API_BASE}/api/v1/reviews/${rev.id}`)
          if (rr.ok) {
            const data = await rr.json()
            if (data.status === 'completed' || data.status === 'failed') {
              setSelectedReview(data)
              loadReviews()
              break
            }
          }
        }
      }
    } catch { void 0 }
    setGenerating(false)
  }

  const selectReview = async (rev: Review) => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/reviews/${rev.id}`)
      if (resp.ok) {
        const data = await resp.json()
        setSelectedReview(data)
        setSelectedActions(new Set())
      }
    } catch { setSelectedReview(rev) }
  }

  const toggleAction = (idx: number) => {
    setSelectedActions(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const applyFeedback = async () => {
    if (!selectedReview || selectedActions.size === 0) return
    setApplying(true)
    try {
      const resp = await fetch(`${API_BASE}/api/v1/reviews/${selectedReview.id}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actionItemIndices: [...selectedActions] }),
      })
      if (resp.ok) {
        const data = await resp.json()
        setSelectedActions(new Set())
        loadRequests()
        alert(`Applied ${data.appliedCount} action item(s) as improvement requests.`)
      }
    } catch { void 0 }
    setApplying(false)
  }

  const report = selectedReview?.jsonReport

  if (loading) {
    return (
      <AppPageLayout
        title="Review Agent"
        subtitle="LLM-driven paper review with structured feedback and improvement requests"
        icon={CheckCircle}
        iconColor="indigo"
        accentColor="indigo"
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      </AppPageLayout>
    )
  }

  return (
    <AppPageLayout
      title="Review Agent"
      subtitle="LLM-driven paper review with structured feedback and improvement requests"
      icon={CheckCircle}
      iconColor="indigo"
      accentColor="indigo"
      actions={
        <Button variant="outline" size="sm" onClick={() => { loadReviews(); loadRequests() }}>
          <RefreshCw className="h-4 w-4 mr-1" /> Refresh
        </Button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left: Paper selector + reviews list */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Generate Review</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <select
                className="w-full rounded border px-2 py-1.5 text-sm"
                value={selectedPaperId}
                onChange={e => setSelectedPaperId(e.target.value)}
              >
                <option value="">Select a paper...</option>
                {papers.filter(p => p.status === 'completed').map(p => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
              <div className="grid grid-cols-2 gap-1">
                <select className="border rounded px-2 py-1 text-xs" value={provider} onChange={e => { const providerName = e.target.value; setProvider(providerName); setModel(getModelsByProvider(providerName)[0]?.id || "") }}>
                  <option value="">Select provider</option>
                  {LLM_PROVIDERS.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
                <select className="border rounded px-2 py-1 text-xs" value={model} onChange={e => setModel(e.target.value)}>
                  {getModelsByProvider(provider).map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
              </div>
              <Button size="sm" className="w-full" onClick={createReview} disabled={!selectedPaperId || generating}>
                {generating ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Zap className="h-3 w-3 mr-1" />}
                {generating ? 'Reviewing...' : 'Generate Review'}
              </Button>
            </CardContent>
          </Card>

          <div className="text-xs font-medium text-muted-foreground">{reviews.length} reviews</div>
          <div className="space-y-1.5 max-h-[50vh] overflow-y-auto">
            {reviews.map(r => (
              <div
                key={r.id}
                className={`p-2.5 rounded-lg border cursor-pointer transition-colors ${selectedReview?.id === r.id ? 'border-indigo-400 bg-indigo-50' : 'hover:bg-muted/50'}`}
                onClick={() => selectReview(r)}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium truncate">
                    {papers.find(p => p.id === r.paperId)?.title?.slice(0, 30) || r.paperId.slice(0, 15)}
                  </span>
                  <Badge variant="outline" className="text-[10px]">{r.status}</Badge>
                </div>
                <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                  {r.scoreSuggestion !== null && <span className="font-semibold">{r.scoreSuggestion}/10</span>}
                  <span>{r.actionItems?.length || 0} actions</span>
                  <span>{new Date(r.createdAt).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Review Detail */}
        <div className="lg:col-span-3 space-y-4">
          {!selectedReview ? (
            <Card><CardContent className="py-12 text-center text-muted-foreground">
              <CheckCircle className="h-10 w-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Select a review or generate one to view details</p>
            </CardContent></Card>
          ) : selectedReview.status === 'generating' ? (
            <Card><CardContent className="py-12 text-center">
              <Loader2 className="h-8 w-8 mx-auto mb-3 animate-spin text-indigo-500" />
              <p className="text-sm text-muted-foreground">Generating review... This may take a minute.</p>
            </CardContent></Card>
          ) : selectedReview.status === 'failed' ? (
            <Card><CardContent className="py-12 text-center text-red-600">
              <AlertTriangle className="h-8 w-8 mx-auto mb-3" />
              <p className="text-sm">{selectedReview.markdownReport || 'Review generation failed'}</p>
            </CardContent></Card>
          ) : (
            <>
              {/* Score header */}
              <div className="flex items-center gap-4 bg-white border rounded-lg px-4 py-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-600">{selectedReview.scoreSuggestion ?? '?'}</div>
                  <div className="text-[10px] text-muted-foreground">/10</div>
                </div>
                <div className="flex-1">
                  <p className="text-sm">{report?.overallAssessment || 'No assessment'}</p>
                </div>
                <div className="text-xs text-muted-foreground">
                  <div>{selectedReview.actionItems?.length || 0} action items</div>
                  <div>{new Date(selectedReview.createdAt).toLocaleString()}</div>
                </div>
              </div>

              <Tabs value={reviewTab} onValueChange={setReviewTab}>
                <TabsList>
                  <TabsTrigger value="actions"><Target className="h-3 w-3 mr-1" /> Action Items ({selectedReview.actionItems?.length || 0})</TabsTrigger>
                  <TabsTrigger value="report"><FileText className="h-3 w-3 mr-1" /> Full Report</TabsTrigger>
                  <TabsTrigger value="requests"><ArrowRight className="h-3 w-3 mr-1" /> Requests ({requests.filter(r => r.reviewId === selectedReview.id).length})</TabsTrigger>
                </TabsList>

                <TabsContent value="actions" className="mt-4 space-y-3">
                  {/* Select all + apply */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => {
                        if (selectedActions.size === selectedReview.actionItems.length) setSelectedActions(new Set())
                        else setSelectedActions(new Set(selectedReview.actionItems.map((_, i) => i)))
                      }}>
                        <Check className="h-3 w-3 mr-1" /> {selectedActions.size === selectedReview.actionItems?.length ? 'Deselect All' : 'Select All'}
                      </Button>
                      <span className="text-xs text-muted-foreground">{selectedActions.size} selected</span>
                    </div>
                    <Button size="sm" onClick={applyFeedback} disabled={applying || selectedActions.size === 0} className="h-7 text-xs">
                      {applying ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <ArrowRight className="h-3 w-3 mr-1" />}
                      Apply as Improvement Requests
                    </Button>
                  </div>

                  {(selectedReview.actionItems || []).map((item, i) => (
                    <div
                      key={i}
                      className={`border rounded-lg p-3 cursor-pointer transition-colors ${selectedActions.has(i) ? 'border-indigo-400 bg-indigo-50/50' : 'hover:bg-muted/30'}`}
                      onClick={() => toggleAction(i)}
                    >
                      <div className="flex items-start gap-2">
                        <input type="checkbox" checked={selectedActions.has(i)} readOnly className="mt-1 accent-indigo-500" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${severityColors[item.severity] || 'bg-gray-100'}`}>{item.severity}</span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${moduleColors[item.targetModule] || 'bg-gray-100'}`}>{item.targetModule}</span>
                            <span className="text-xs text-muted-foreground">{item.section}</span>
                          </div>
                          <p className="text-sm">{item.description}</p>
                          {item.suggestedEdit && (
                            <p className="text-xs text-muted-foreground mt-1 italic">Suggested: {item.suggestedEdit}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </TabsContent>

                <TabsContent value="report" className="mt-4 space-y-4">
                  {report && (
                    <>
                      {report.strengths && report.strengths.length > 0 && (
                        <Card>
                          <CardHeader className="pb-1"><CardTitle className="text-sm flex items-center gap-2"><ThumbsUp className="h-4 w-4 text-green-500" /> Strengths</CardTitle></CardHeader>
                          <CardContent><ul className="space-y-1 ml-4">{report.strengths.map((s, i) => <li key={i} className="text-sm list-disc">{s}</li>)}</ul></CardContent>
                        </Card>
                      )}
                      {report.weaknesses && report.weaknesses.length > 0 && (
                        <Card>
                          <CardHeader className="pb-1"><CardTitle className="text-sm flex items-center gap-2"><ThumbsDown className="h-4 w-4 text-red-500" /> Weaknesses</CardTitle></CardHeader>
                          <CardContent><ul className="space-y-1 ml-4">{report.weaknesses.map((w, i) => <li key={i} className="text-sm list-disc">{w}</li>)}</ul></CardContent>
                        </Card>
                      )}
                      {report.questions && report.questions.length > 0 && (
                        <Card>
                          <CardHeader className="pb-1"><CardTitle className="text-sm flex items-center gap-2"><HelpCircle className="h-4 w-4 text-blue-500" /> Questions</CardTitle></CardHeader>
                          <CardContent><ul className="space-y-1 ml-4">{report.questions.map((q, i) => <li key={i} className="text-sm list-disc">{q}</li>)}</ul></CardContent>
                        </Card>
                      )}
                      {report.missingExperiments && report.missingExperiments.length > 0 && (
                        <Card>
                          <CardHeader className="pb-1"><CardTitle className="text-sm flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-500" /> Missing Experiments</CardTitle></CardHeader>
                          <CardContent><ul className="space-y-1 ml-4">{report.missingExperiments.map((m, i) => <li key={i} className="text-sm list-disc">{m}</li>)}</ul></CardContent>
                        </Card>
                      )}
                      {report.writingIssues && report.writingIssues.length > 0 && (
                        <Card>
                          <CardHeader className="pb-1"><CardTitle className="text-sm flex items-center gap-2"><FileText className="h-4 w-4 text-gray-500" /> Writing Issues</CardTitle></CardHeader>
                          <CardContent><ul className="space-y-1 ml-4">{report.writingIssues.map((w, i) => <li key={i} className="text-sm list-disc">{w}</li>)}</ul></CardContent>
                        </Card>
                      )}
                    </>
                  )}
                  {selectedReview.markdownReport && (
                    <Card>
                      <CardHeader className="pb-1"><CardTitle className="text-sm">Raw Markdown</CardTitle></CardHeader>
                      <CardContent><pre className="text-xs font-mono whitespace-pre-wrap max-h-96 overflow-auto bg-muted/30 p-3 rounded">{selectedReview.markdownReport}</pre></CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="requests" className="mt-4 space-y-2">
                  {requests.filter(r => r.reviewId === selectedReview.id).length === 0 ? (
                    <p className="text-sm text-muted-foreground py-4 text-center">No improvement requests yet. Select action items and click "Apply".</p>
                  ) : (
                    requests.filter(r => r.reviewId === selectedReview.id).map(req => (
                      <div key={req.id} className="border rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${severityColors[req.severity] || 'bg-gray-100'}`}>{req.severity}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${moduleColors[req.targetModule] || 'bg-gray-100'}`}>{req.targetModule}</span>
                          <Badge variant="outline" className="text-[10px]">{req.status}</Badge>
                          <span className="text-[10px] text-muted-foreground ml-auto">{req.sectionPointer}</span>
                        </div>
                        <p className="text-sm">{req.description}</p>
                        {req.suggestedEdit && <p className="text-xs text-muted-foreground mt-1 italic">Fix: {req.suggestedEdit}</p>}
                      </div>
                    ))
                  )}
                </TabsContent>
              </Tabs>
            </>
          )}
        </div>
      </div>
    </AppPageLayout>
  )
}
