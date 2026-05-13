import { useNavigate } from 'react-router-dom'
import { useRuns } from '@/lib/hooks/useApi'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Beaker,
  PlayCircle,
  FlaskConical,
  FolderOpen,
  FileText,
  ClipboardCheck,
  Settings,
  Activity,
  ArrowRight,
  Sparkles
} from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'
import { getRunCategoryInfo } from '@/lib/taxonomy/categories'

export function Homepage() {
  const navigate = useNavigate()
  const { data: runs } = useRuns()

  const recentRuns = runs?.slice(0, 5) || []

  const modules = [
    {
      id: 'research',
      title: 'Research Planning',
      description: 'Design experiments with AI-guided workflows',
      icon: Beaker,
      path: '/research/planning',
      accent: 'teal',
    },
    {
      id: 'workflows',
      title: 'Workflow Templates',
      description: 'Browse pre-built research templates',
      icon: FlaskConical,
      path: '/research/workflows',
      accent: 'teal',
    },
    {
      id: 'runs',
      title: 'Execution Runs',
      description: 'Monitor and track research executions',
      icon: PlayCircle,
      path: '/runs',
      accent: 'cyan',
    },
    {
      id: 'experiments',
      title: 'Experiments',
      description: 'Compare results and analyze metrics',
      icon: Activity,
      path: '/experiments',
      accent: 'cyan',
    },
    {
      id: 'artifacts',
      title: 'Artifacts',
      description: 'Browse generated code, papers, and logs',
      icon: FolderOpen,
      path: '/artifacts',
      accent: 'indigo',
    },
    {
      id: 'papers',
      title: 'Papers',
      description: 'Draft and edit research publications',
      icon: FileText,
      path: '/papers',
      accent: 'indigo',
    },
    {
      id: 'review',
      title: 'Review Tools',
      description: 'Quality assurance and consistency checks',
      icon: ClipboardCheck,
      path: '/review/consistency',
      accent: 'slate',
    },
    {
      id: 'system',
      title: 'System Monitor',
      description: 'Platform health and diagnostics',
      icon: Settings,
      path: '/system/health',
      accent: 'slate',
    },
  ]

  const accentColors = {
    teal: 'from-teal-500/20 to-cyan-500/20',
    cyan: 'from-cyan-500/20 to-teal-500/20',
    indigo: 'from-indigo-500/20 to-purple-500/20',
    slate: 'from-slate-500/20 to-gray-500/20',
  }

  const accentBorders = {
    teal: 'border-l-teal-500',
    cyan: 'border-l-cyan-500',
    indigo: 'border-l-indigo-500',
    slate: 'border-l-slate-500',
  }

  return (
    <div className="min-h-screen bg-[#F6F7F9]">
      {/* Hero Section */}
      <section
        className="relative overflow-hidden"
        style={{
          backgroundImage: 'url(/hero/hero-bg.svg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      >
        {/* Overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/40 via-white/60 to-white/80" />

        <div className="relative max-w-6xl mx-auto px-6 py-24 md:py-32 text-center">
          {/* Animated content */}
          <div className="space-y-8 animate-fade-in">
            <h1
              className="font-bold text-slate-900"
              style={{
                fontFamily: '"DM Serif Display", "Playfair Display", ui-serif, Georgia, serif',
                fontSize: 'clamp(44px, 6vw, 72px)',
                lineHeight: '1.05',
                letterSpacing: '-0.02em',
                animation: 'fadeInUp 0.8s ease-out',
              }}
            >
              <span className="bg-gradient-to-r from-teal-600 to-cyan-500 bg-clip-text text-transparent">FAROS</span>
            </h1>

            <p
              className="text-xl md:text-2xl text-slate-500 mx-auto font-light"
              style={{
                maxWidth: '60ch',
                animation: 'fadeInUp 0.8s ease-out 0.2s backwards'
              }}
            >
              A foundation AutoResearch runtime for blueprint-driven LLM research workflows, experiments, papers, and reviews
            </p>

            <div
              className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
              style={{ animation: 'fadeInUp 0.8s ease-out 0.4s backwards' }}
            >
              <Button
                size="lg"
                className="text-lg px-8 py-6 bg-teal-600 hover:bg-teal-700 shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5"
                onClick={() => navigate('/research/planning')}
                aria-label="Start Research - Navigate to research planning"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Start Research
              </Button>

              <Button
                size="lg"
                variant="outline"
                className="text-lg px-8 py-6 border-2 border-slate-300 hover:border-teal-500 hover:bg-teal-50 shadow-md hover:shadow-lg transition-all hover:-translate-y-0.5"
                onClick={() => navigate('/runs')}
                aria-label="Explore Runs - Navigate to runs list"
              >
                <PlayCircle className="mr-2 h-5 w-5" />
                Explore Runs
              </Button>

              <Button
                size="lg"
                variant="ghost"
                className="text-lg px-6 py-6 text-slate-600 hover:text-teal-600 hover:bg-teal-50 transition-all"
                onClick={() => navigate('/artifacts')}
                aria-label="Browse Artifacts - Navigate to artifacts browser"
              >
                Browse Artifacts
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            {/* Trust Row */}
            <div
              className="flex flex-wrap items-center justify-center gap-4 pt-4"
              style={{ animation: 'fadeInUp 0.8s ease-out 0.6s backwards' }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/60 border border-slate-200 text-sm text-slate-700">
                <div className="h-2 w-2 rounded-full bg-teal-500" />
                FAROS-LLM
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/60 border border-slate-200 text-sm text-slate-700">
                <div className="h-2 w-2 rounded-full bg-cyan-500" />
                Blueprint-driven
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/60 border border-slate-200 text-sm text-slate-700">
                <div className="h-2 w-2 rounded-full bg-indigo-500" />
                Artifact-native
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/60 border border-slate-200 text-sm text-slate-700">
                <div className="h-2 w-2 rounded-full bg-teal-600" />
                Provider-pluggable
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Built for AutoResearch Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Built for AutoResearch
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            From idea refinement to experiment execution, paper drafting, and review simulation in one extensible runtime
          </p>
        </div>

        {/* Horizontal Scrolling Container */}
        <div className="relative">
          <div className="overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100">
            <div className="flex gap-6 min-w-max px-2">
              {/* Example Card A: Paper Draft */}
              <div className="bg-white rounded-xl border-l-4 border-l-teal-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-teal-50 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-teal-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Paper Draft</h3>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-slate-700 leading-relaxed">
                    <strong>Abstract:</strong> We present a novel approach to post-training optimization
                    that reduces inference latency by 40% while maintaining 98% accuracy on standard benchmarks.
                  </p>

                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Key Contributions:</p>
                    <ul className="text-sm text-slate-700 space-y-1.5">
                      <li className="flex items-start gap-2">
                        <span className="text-teal-600 mt-1">•</span>
                        <span>Adaptive quantization strategy for transformer models</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-600 mt-1">•</span>
                        <span>Layer-wise pruning with minimal accuracy degradation</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-600 mt-1">•</span>
                        <span>Comprehensive evaluation on 5 downstream tasks</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                    <p className="text-xs font-semibold text-slate-600 mb-2 font-mono">LaTeX Snippet:</p>
                    <pre className="text-xs font-mono text-slate-700 leading-relaxed overflow-x-auto">
                      {`\\begin{equation}
  \\mathcal{L}_{total} = \\mathcal{L}_{task} + 
    \\lambda \\mathcal{L}_{distill}
\\end{equation}

where $\\lambda$ controls the trade-off
between task performance and model
compression. We set $\\lambda=0.1$
for all experiments.`}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Example Card B: Experiment Results */}
              <div className="bg-white rounded-xl border-l-4 border-l-cyan-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-cyan-50 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-cyan-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Experiment Results</h3>
                </div>

                <div className="space-y-4">
                  <p className="text-sm text-slate-700">
                    Comparison of post-training methods on MMLU benchmark
                  </p>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left py-2 px-3 font-semibold text-slate-700">Model</th>
                          <th className="text-right py-2 px-3 font-semibold text-slate-700">Acc (%)</th>
                          <th className="text-right py-2 px-3 font-semibold text-slate-700">Cost</th>
                        </tr>
                      </thead>
                      <tbody className="text-slate-600">
                        <tr className="border-b border-slate-100">
                          <td className="py-2 px-3 font-mono text-xs">baseline</td>
                          <td className="text-right py-2 px-3">72.4</td>
                          <td className="text-right py-2 px-3 font-mono text-xs">$1.00</td>
                        </tr>
                        <tr className="border-b border-slate-100">
                          <td className="py-2 px-3 font-mono text-xs">quantized</td>
                          <td className="text-right py-2 px-3">71.8</td>
                          <td className="text-right py-2 px-3 font-mono text-xs">$0.45</td>
                        </tr>
                        <tr className="border-b border-slate-100">
                          <td className="py-2 px-3 font-mono text-xs">pruned</td>
                          <td className="text-right py-2 px-3">70.2</td>
                          <td className="text-right py-2 px-3 font-mono text-xs">$0.38</td>
                        </tr>
                        <tr className="bg-teal-50/50">
                          <td className="py-2 px-3 font-mono text-xs font-semibold text-teal-900">ours</td>
                          <td className="text-right py-2 px-3 font-semibold text-teal-900">71.9</td>
                          <td className="text-right py-2 px-3 font-mono text-xs font-semibold text-teal-900">$0.42</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Enhanced accuracy trend chart */}
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-slate-600">Accuracy Trend Across Runs</p>
                    <svg width="100%" height="80" viewBox="0 0 280 80" className="overflow-visible">
                      <defs>
                        <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#0EA5A4" stopOpacity="0.3" />
                          <stop offset="100%" stopColor="#0EA5A4" stopOpacity="0.05" />
                        </linearGradient>
                      </defs>

                      {/* Grid lines */}
                      <line x1="30" y1="15" x2="260" y2="15" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="2,2" />
                      <line x1="30" y1="35" x2="260" y2="35" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="2,2" />
                      <line x1="30" y1="55" x2="260" y2="55" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="2,2" />

                      {/* Axes */}
                      <line x1="30" y1="10" x2="30" y2="60" stroke="#94a3b8" strokeWidth="1.5" />
                      <line x1="30" y1="60" x2="260" y2="60" stroke="#94a3b8" strokeWidth="1.5" />

                      {/* Y-axis labels */}
                      <text x="22" y="15" fontSize="8" fill="#64748b" textAnchor="end">72%</text>
                      <text x="22" y="35" fontSize="8" fill="#64748b" textAnchor="end">71%</text>
                      <text x="22" y="55" fontSize="8" fill="#64748b" textAnchor="end">70%</text>

                      {/* X-axis labels */}
                      <text x="70" y="72" fontSize="8" fill="#64748b" textAnchor="middle">Run 1</text>
                      <text x="120" y="72" fontSize="8" fill="#64748b" textAnchor="middle">Run 2</text>
                      <text x="170" y="72" fontSize="8" fill="#64748b" textAnchor="middle">Run 3</text>
                      <text x="220" y="72" fontSize="8" fill="#64748b" textAnchor="middle">Run 4</text>

                      {/* Baseline (dashed) */}
                      <path
                        d="M 70,40 L 120,42 L 170,41 L 220,43"
                        fill="none"
                        stroke="#94a3b8"
                        strokeWidth="1.5"
                        strokeDasharray="4,3"
                      />

                      {/* Our method (solid) */}
                      <path
                        d="M 70,38 L 120,35 L 170,37 L 220,34"
                        fill="none"
                        stroke="#0EA5A4"
                        strokeWidth="2"
                      />
                      <path
                        d="M 70,38 L 120,35 L 170,37 L 220,34 L 220,60 L 70,60 Z"
                        fill="url(#sparkGradient)"
                      />

                      {/* Data points */}
                      {[70, 120, 170, 220].map((x, i) => (
                        <circle
                          key={i}
                          cx={x}
                          cy={[38, 35, 37, 34][i]}
                          r="3"
                          fill="#0EA5A4"
                          stroke="white"
                          strokeWidth="1.5"
                        />
                      ))}
                    </svg>

                    {/* Legend */}
                    <div className="flex items-center gap-4 text-xs pt-1">
                      <div className="flex items-center gap-1.5">
                        <div className="h-0.5 w-4 bg-teal-500" />
                        <span className="text-slate-600">Ours</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="h-0.5 w-4 bg-slate-400" style={{ borderTop: '1.5px dashed #94a3b8' }} />
                        <span className="text-slate-600">Baseline</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example Card C: Figure Preview */}
              <div className="bg-white rounded-xl border-l-4 border-l-indigo-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                    <Beaker className="h-5 w-5 text-indigo-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Figure Preview</h3>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-slate-700">
                    Performance vs. Efficiency Trade-off
                  </p>

                  {/* Enhanced scatter plot with clear comparison */}
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <svg width="100%" height="200" viewBox="0 0 280 200" className="overflow-visible">
                      {/* Axes */}
                      <line x1="40" y1="20" x2="40" y2="160" stroke="#64748b" strokeWidth="2" />
                      <line x1="40" y1="160" x2="260" y2="160" stroke="#64748b" strokeWidth="2" />

                      {/* Axis labels */}
                      <text x="150" y="190" textAnchor="middle" fontSize="11" fontWeight="500" fill="#475569">
                        Inference Cost (relative)
                      </text>
                      <text x="12" y="95" textAnchor="middle" fontSize="11" fontWeight="500" fill="#475569" transform="rotate(-90 12 95)">
                        Accuracy (%)
                      </text>

                      {/* Grid lines */}
                      <line x1="40" y1="120" x2="260" y2="120" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3,3" />
                      <line x1="40" y1="80" x2="260" y2="80" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3,3" />
                      <line x1="40" y1="40" x2="260" y2="40" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3,3" />
                      <line x1="100" y1="20" x2="100" y2="160" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3,3" />
                      <line x1="160" y1="20" x2="160" y2="160" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3,3" />
                      <line x1="220" y1="20" x2="220" y2="160" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3,3" />

                      {/* Tick marks and labels */}
                      <text x="100" y="175" fontSize="9" fill="#64748b" textAnchor="middle">0.5×</text>
                      <text x="160" y="175" fontSize="9" fill="#64748b" textAnchor="middle">1.0×</text>
                      <text x="220" y="175" fontSize="9" fill="#64748b" textAnchor="middle">1.5×</text>
                      <text x="32" y="43" fontSize="9" fill="#64748b" textAnchor="end">72</text>
                      <text x="32" y="83" fontSize="9" fill="#64748b" textAnchor="end">71</text>
                      <text x="32" y="123" fontSize="9" fill="#64748b" textAnchor="end">70</text>

                      {/* Baseline points (gray) */}
                      <circle cx="210" cy="50" r="5" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" />
                      <circle cx="170" cy="70" r="5" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" />
                      <circle cx="130" cy="95" r="5" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" />

                      {/* Our method (teal, larger, highlighted) */}
                      <circle cx="110" cy="65" r="7" fill="#0EA5A4" stroke="#0d9488" strokeWidth="2" />
                      <circle cx="110" cy="65" r="12" fill="none" stroke="#0EA5A4" strokeWidth="1" opacity="0.3" />

                      {/* Labels */}
                      <text x="215" y="48" fontSize="9" fill="#64748b">baseline</text>
                      <text x="175" y="68" fontSize="9" fill="#64748b">quantized</text>
                      <text x="135" y="93" fontSize="9" fill="#64748b">pruned</text>
                      <text x="115" y="60" fontSize="10" fontWeight="600" fill="#0d9488">ours</text>

                      {/* Pareto frontier annotation */}
                      <path
                        d="M 110,65 Q 120,60 130,95 Q 150,80 170,70 Q 190,55 210,50"
                        fill="none"
                        stroke="#0EA5A4"
                        strokeWidth="1.5"
                        strokeDasharray="4,2"
                        opacity="0.5"
                      />

                      {/* Better region indicator */}
                      <text x="70" y="35" fontSize="8" fill="#0d9488" fontWeight="600">← Better</text>
                    </svg>
                  </div>

                  {/* Enhanced legend */}
                  <div className="flex items-center gap-4 text-xs pt-2">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-teal-600 ring-2 ring-teal-600 ring-opacity-30" />
                      <span className="text-slate-700 font-medium">Our Method</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-slate-300 ring-2 ring-slate-400" />
                      <span className="text-slate-600">Baselines</span>
                    </div>
                    <div className="flex items-center gap-2 ml-auto">
                      <div className="h-0.5 w-4 bg-teal-500" style={{ borderTop: '1.5px dashed #0EA5A4' }} />
                      <span className="text-slate-600 text-xs">Pareto Frontier</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example Card D: Run Trace */}
              <div className="bg-white rounded-xl border-l-4 border-l-orange-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-orange-50 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-orange-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Run Trace</h3>
                </div>
                <div className="space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded border-l-2 border-l-green-500">
                      <span className="text-sm font-medium text-slate-700">Step 1: Data Loading</span>
                      <span className="text-xs text-green-700 font-semibold">✓ 2.3s</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded border-l-2 border-l-green-500">
                      <span className="text-sm font-medium text-slate-700">Step 2: Model Init</span>
                      <span className="text-xs text-green-700 font-semibold">✓ 5.1s</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-blue-50 rounded border-l-2 border-l-blue-500">
                      <span className="text-sm font-medium text-slate-700">Step 3: Training</span>
                      <span className="text-xs text-blue-700 font-semibold">⟳ 45.2s</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-100 rounded border-l-2 border-l-slate-300">
                      <span className="text-sm font-medium text-slate-500">Step 4: Evaluation</span>
                      <span className="text-xs text-slate-500">pending</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example Card E: Code Snippet */}
              <div className="bg-white rounded-xl border-l-4 border-l-purple-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-purple-50 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-purple-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Generated Code</h3>
                </div>
                <div className="space-y-3">
                  <p className="text-sm text-slate-700">Optimized inference pipeline</p>
                  <div className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-xs font-mono text-green-400">
                      {`def optimize_model(model, config):
    # Apply quantization
    quantized = quantize_weights(
        model, bits=config.bits
    )
    
    # Layer fusion
    fused = fuse_layers(quantized)
    
    return fused`}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Example Card F: Review Finding */}
              <div className="bg-white rounded-xl border-l-4 border-l-red-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-red-50 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-red-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Consistency Check</h3>
                </div>
                <div className="space-y-3">
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <span className="text-red-600 font-bold">⚠</span>
                      <div>
                        <p className="text-sm font-semibold text-red-900">Citation Mismatch</p>
                        <p className="text-xs text-red-700 mt-1">Reference [12] cited but not in bibliography</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <span className="text-yellow-600 font-bold">!</span>
                      <div>
                        <p className="text-sm font-semibold text-yellow-900">Table Reference</p>
                        <p className="text-xs text-yellow-700 mt-1">Table 3 mentioned but not present</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example Card G: Artifact Preview */}
              <div className="bg-white rounded-xl border-l-4 border-l-teal-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-teal-50 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-teal-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Artifacts</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 border rounded hover:bg-slate-50">
                    <span className="text-sm font-mono text-slate-700">model_v1.pt</span>
                    <span className="text-xs text-slate-500">245 MB</span>
                  </div>
                  <div className="flex items-center justify-between p-2 border rounded hover:bg-slate-50">
                    <span className="text-sm font-mono text-slate-700">results.json</span>
                    <span className="text-xs text-slate-500">12 KB</span>
                  </div>
                  <div className="flex items-center justify-between p-2 border rounded hover:bg-slate-50">
                    <span className="text-sm font-mono text-slate-700">training.log</span>
                    <span className="text-xs text-slate-500">3.2 MB</span>
                  </div>
                </div>
              </div>

              {/* Example Card H: Metrics Dashboard */}
              <div className="bg-white rounded-xl border-l-4 border-l-cyan-500 border border-slate-200 shadow-sm p-6 space-y-4 w-[380px] flex-shrink-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-lg bg-cyan-50 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-cyan-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Live Metrics</h3>
                </div>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-50 rounded-lg border">
                      <p className="text-xs text-slate-600 mb-1">Accuracy</p>
                      <p className="text-2xl font-bold text-teal-600">94.2%</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border">
                      <p className="text-xs text-slate-600 mb-1">Loss</p>
                      <p className="text-2xl font-bold text-slate-900">0.142</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border">
                      <p className="text-xs text-slate-600 mb-1">Latency</p>
                      <p className="text-2xl font-bold text-cyan-600">23ms</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border">
                      <p className="text-xs text-slate-600 mb-1">Cost</p>
                      <p className="text-2xl font-bold text-indigo-600">$0.42</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scroll hint */}
          <div className="text-center mt-6">
            <p className="text-sm text-slate-500">← Scroll to explore more examples →</p>
          </div>
        </div>
      </section>

      {/* Module Entry Grid */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-3">
            Foundation AutoResearch Runtime
          </h2>
          <p className="text-lg text-slate-600">
            Composable surfaces for blueprint execution, artifacts, and research memory
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {modules.map((module, index) => {
            const Icon = module.icon
            return (
              <div
                key={module.id}
                className={`
                  group relative bg-white rounded-lg border-l-4 ${accentBorders[module.accent as keyof typeof accentBorders]}
                  border border-slate-200 shadow-sm hover:shadow-lg
                  transition-all duration-300 hover:-translate-y-1 cursor-pointer
                  overflow-hidden
                `}
                onClick={() => navigate(module.path)}
                style={{ animation: `fadeInUp 0.5s ease-out ${0.1 * index}s backwards` }}
              >
                {/* Accent gradient overlay */}
                <div className={`absolute inset-0 bg-gradient-to-br ${accentColors[module.accent as keyof typeof accentColors]} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />

                <div className="relative p-6 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="p-3 rounded-lg bg-slate-50 group-hover:bg-white transition-colors">
                      <Icon className="h-6 w-6 text-slate-700 group-hover:text-teal-600 transition-colors" />
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>

                  <div>
                    <h3 className="font-semibold text-slate-900 mb-1">
                      {module.title}
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {module.description}
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>


      {/* Recent Activity */}
      <section className="max-w-7xl mx-auto px-6 py-16 pb-24">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold text-slate-900 mb-2">
              Recent Activity
            </h2>
            <p className="text-slate-600">
              Latest research runs and their status
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/runs')}
            className="hover:border-teal-500 hover:text-teal-600"
          >
            View All Runs
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>

        {recentRuns.length > 0 ? (
          <div className="space-y-3">
            {recentRuns.map((run) => {
              const categoryInfo = getRunCategoryInfo(run)
              return (
                <div
                  key={run.id}
                  className="group bg-white rounded-lg border-l-4 border-l-teal-500 border border-slate-200 p-5 hover:shadow-md transition-all cursor-pointer hover:-translate-y-0.5"
                  onClick={() => navigate(`/runs/${run.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-mono text-sm font-medium text-slate-900">
                          {run.id}
                        </span>
                        <Badge
                          variant={run.status === 'completed' ? 'default' : run.status === 'running' ? 'secondary' : 'outline'}
                          className="capitalize"
                        >
                          {run.status}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {categoryInfo.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-600">
                        {run.type} • Started {formatRelativeTime(run.startedAt)}
                      </p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-teal-600 transition-colors flex-shrink-0" />
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
            <PlayCircle className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-600 mb-4">
              No runs yet. Start your first research workflow to see activity here.
            </p>
            <Button onClick={() => navigate('/research/planning')}>
              Create First Run
            </Button>
          </div>
        )}
      </section>

      {/* Inline animations */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @media (prefers-reduced-motion: reduce) {
          * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
      `}</style>
    </div>
  )
}
