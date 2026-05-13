/**
 * Code Project Browser — GitHub-like file tree + file viewer + search + export.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Code2, ArrowLeft, FolderOpen, FileCode, File, Download,
  Search, ExternalLink, Copy, Loader2, AlertTriangle,
  ChevronRight, FolderClosed, Archive
} from 'lucide-react'
import {
  getProject, getTree, getFileContent, searchProject,
  exportProject, getVSCodeLink, getFileDownloadUrl, getExportDownloadUrl,
  CodeProjectV2, TreeEntry, SearchResult,
} from '@/lib/api/codeProjects'

// Language to simple syntax highlight class
const LANG_COLORS: Record<string, string> = {
  python: 'text-blue-600',
  javascript: 'text-yellow-600',
  typescript: 'text-blue-500',
  json: 'text-green-600',
  markdown: 'text-gray-700',
  yaml: 'text-purple-600',
  html: 'text-orange-600',
  css: 'text-pink-600',
  bash: 'text-green-700',
  dockerfile: 'text-cyan-600',
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function CodeProjectBrowser() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  // Project data
  const [project, setProject] = useState<CodeProjectV2 | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Tree state
  const [currentPath, setCurrentPath] = useState('')
  const [treeEntries, setTreeEntries] = useState<TreeEntry[]>([])
  const [treeLoading, setTreeLoading] = useState(false)

  // File viewer state
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string | null>(null)
  const [fileLanguage, setFileLanguage] = useState<string | null>(null)
  const [fileLoading, setFileLoading] = useState(false)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'path' | 'content'>('path')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [searching, setSearching] = useState(false)

  // Export state
  const [exporting, setExporting] = useState(false)

  // Load project
  useEffect(() => {
    if (!projectId) return
    const load = async () => {
      try {
        setLoading(true)
        const p = await getProject(projectId)
        setProject(p)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load project')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [projectId])

  // Load tree when path changes
  useEffect(() => {
    if (!projectId) return
    const loadTree = async () => {
      try {
        setTreeLoading(true)
        const resp = await getTree(projectId, currentPath)
        setTreeEntries(resp.entries)
      } catch (err) {
        console.error('Tree load error:', err)
      } finally {
        setTreeLoading(false)
      }
    }
    loadTree()
  }, [projectId, currentPath])

  // Navigate into directory
  const handleTreeClick = async (entry: TreeEntry) => {
    if (entry.isDir) {
      setCurrentPath(entry.path)
      setSelectedFile(null)
      setFileContent(null)
      setSearchResults(null)
    } else {
      // Load file content
      if (!projectId) return
      try {
        setFileLoading(true)
        setSelectedFile(entry.path)
        const resp = await getFileContent(projectId, entry.path)
        setFileContent(resp.content)
        setFileLanguage(resp.language || null)
        setSearchResults(null)
      } catch (err) {
        setFileContent(`Error loading file: ${err instanceof Error ? err.message : 'unknown'}`)
      } finally {
        setFileLoading(false)
      }
    }
  }

  // Navigate up
  const handleNavigateUp = () => {
    if (!currentPath) return
    const parts = currentPath.split('/')
    parts.pop()
    setCurrentPath(parts.join('/'))
    setSelectedFile(null)
    setFileContent(null)
  }

  // Breadcrumb
  const breadcrumbs = currentPath ? currentPath.split('/') : []

  // Search
  const handleSearch = async () => {
    if (!projectId || !searchQuery.trim()) return
    try {
      setSearching(true)
      const resp = await searchProject(projectId, searchQuery, searchMode)
      setSearchResults(resp.results)
      setSelectedFile(null)
      setFileContent(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  // Export
  const handleExport = async () => {
    if (!projectId) return
    try {
      setExporting(true)
      const resp = await exportProject(projectId)
      window.open(getExportDownloadUrl(resp.id), '_blank')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExporting(false)
    }
  }

  // VSCode
  const handleVSCode = async () => {
    if (!projectId) return
    try {
      const resp = await getVSCodeLink(projectId)
      window.open(resp.uri, '_blank')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'VSCode link failed')
    }
  }

  // Copy path
  const copyPath = () => {
    if (selectedFile) navigator.clipboard.writeText(selectedFile)
  }

  if (loading) {
    return (
      <AppPageLayout title="Loading..." icon={Code2} iconColor="violet" accentColor="violet">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
        </div>
      </AppPageLayout>
    )
  }

  if (!project) {
    return (
      <AppPageLayout title="Not Found" icon={Code2} iconColor="violet" accentColor="violet">
        <Card><CardContent className="py-8 text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">Project not found: {projectId}</p>
          <Button onClick={() => navigate('/code/projects')}><ArrowLeft className="h-4 w-4 mr-2" /> Back</Button>
        </CardContent></Card>
      </AppPageLayout>
    )
  }

  return (
    <AppPageLayout
      title={project.title}
      subtitle={project.description || undefined}
      icon={Code2}
      iconColor="violet"
      accentColor="violet"
    >
      {/* Header actions */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate('/code/projects')}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Projects
          </Button>
          {project.language && <Badge variant="secondary">{project.language}</Badge>}
          {project.framework && <Badge variant="outline">{project.framework}</Badge>}
          <span className="text-sm text-muted-foreground">{project.fileCount} files · {formatBytes(project.totalSizeBytes)}</span>
          {project.sourceIdeaSessionId && <Badge variant="outline" className="text-xs">From Idea #{project.sourceIdeaSessionId.slice(-6)}</Badge>}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleVSCode}>
            <ExternalLink className="h-4 w-4 mr-1" /> Open in VSCode
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport} disabled={exporting}>
            {exporting ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Archive className="h-4 w-4 mr-1" />}
            Download ZIP
          </Button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <span className="text-sm text-red-900">{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)} className="ml-auto">Dismiss</Button>
        </div>
      )}

      {/* Search bar */}
      <div className="flex items-center gap-2 mb-4">
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search files..."
          className="max-w-md"
        />
        <select
          className="border rounded-md px-2 py-2 text-sm"
          value={searchMode}
          onChange={(e) => setSearchMode(e.target.value as 'path' | 'content')}
        >
          <option value="path">File name</option>
          <option value="content">Content</option>
        </select>
        <Button variant="outline" size="sm" onClick={handleSearch} disabled={searching}>
          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
        </Button>
        {searchResults !== null && (
          <Button variant="ghost" size="sm" onClick={() => setSearchResults(null)}>
            Clear results
          </Button>
        )}
      </div>

      {/* Main layout: tree + viewer */}
      <div className="grid grid-cols-12 gap-4" style={{ minHeight: '500px' }}>
        {/* Left: Tree / Search Results */}
        <div className="col-span-4 lg:col-span-3">
          <Card className="h-full">
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium text-muted-foreground">
                {searchResults !== null ? `Search: ${searchResults.length} results` : 'Files'}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {searchResults !== null ? (
                /* Search results */
                <div className="max-h-[500px] overflow-auto">
                  {searchResults.length === 0 ? (
                    <p className="text-sm text-muted-foreground p-4 text-center">No results</p>
                  ) : (
                    searchResults.map((r, i) => (
                      <button
                        key={i}
                        className="w-full text-left px-3 py-1.5 hover:bg-accent text-sm flex items-center gap-2 border-b border-b-muted/30"
                        onClick={() => {
                          if (!r.isDir && projectId) {
                            setFileLoading(true)
                            setSelectedFile(r.path)
                            getFileContent(projectId, r.path).then(resp => {
                              setFileContent(resp.content)
                              setFileLanguage(resp.language || null)
                            }).catch(() => setFileContent('Error loading file')).finally(() => setFileLoading(false))
                          }
                        }}
                      >
                        {r.isDir ? <FolderClosed className="h-3 w-3 text-blue-500 flex-shrink-0" /> : <File className="h-3 w-3 text-gray-400 flex-shrink-0" />}
                        <div className="truncate">
                          <div className="font-mono text-xs truncate">{r.path}</div>
                          {r.line && <div className="text-xs text-muted-foreground">Line {r.line}: {r.content}</div>}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              ) : (
                /* Tree view */
                <div className="max-h-[500px] overflow-auto">
                  {/* Breadcrumb */}
                  {currentPath && (
                    <div className="flex items-center gap-1 px-3 py-2 border-b bg-muted/30 text-xs flex-wrap">
                      <button className="hover:underline text-blue-600" onClick={() => { setCurrentPath(''); setSelectedFile(null); setFileContent(null) }}>root</button>
                      {breadcrumbs.map((part, i) => (
                        <span key={i} className="flex items-center gap-1">
                          <ChevronRight className="h-3 w-3 text-muted-foreground" />
                          <button
                            className="hover:underline text-blue-600"
                            onClick={() => {
                              setCurrentPath(breadcrumbs.slice(0, i + 1).join('/'))
                              setSelectedFile(null)
                              setFileContent(null)
                            }}
                          >
                            {part}
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Up button */}
                  {currentPath && (
                    <button
                      className="w-full text-left px-3 py-1.5 hover:bg-accent text-sm flex items-center gap-2 border-b"
                      onClick={handleNavigateUp}
                    >
                      <ArrowLeft className="h-3 w-3" />
                      <span className="text-muted-foreground">..</span>
                    </button>
                  )}

                  {treeLoading ? (
                    <div className="p-4 text-center"><Loader2 className="h-5 w-5 animate-spin mx-auto text-violet-500" /></div>
                  ) : treeEntries.length === 0 ? (
                    <p className="text-sm text-muted-foreground p-4 text-center">Empty directory</p>
                  ) : (
                    treeEntries.map((entry) => (
                      <button
                        key={entry.path}
                        className={`w-full text-left px-3 py-1.5 hover:bg-accent text-sm flex items-center gap-2 border-b border-b-muted/30 ${
                          selectedFile === entry.path ? 'bg-accent' : ''
                        }`}
                        onClick={() => handleTreeClick(entry)}
                      >
                        {entry.isDir ? (
                          <FolderClosed className="h-4 w-4 text-blue-500 flex-shrink-0" />
                        ) : (
                          <FileCode className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        )}
                        <span className="truncate font-mono text-xs">{entry.name}</span>
                        {!entry.isDir && (
                          <span className="ml-auto text-xs text-muted-foreground flex-shrink-0">{formatBytes(entry.size)}</span>
                        )}
                      </button>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: File viewer */}
        <div className="col-span-8 lg:col-span-9">
          <Card className="h-full flex flex-col">
            {selectedFile ? (
              <>
                <CardHeader className="py-2 px-4 border-b flex-row items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCode className="h-4 w-4 text-violet-500" />
                    <span className="font-mono text-sm">{selectedFile}</span>
                    {fileLanguage && <Badge variant="secondary" className="text-xs">{fileLanguage}</Badge>}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="sm" onClick={copyPath} title="Copy path">
                      <Copy className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost" size="sm"
                      onClick={() => projectId && window.open(getFileDownloadUrl(projectId, selectedFile), '_blank')}
                      title="Download file"
                    >
                      <Download className="h-3 w-3" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 p-0 overflow-auto">
                  {fileLoading ? (
                    <div className="flex items-center justify-center h-48">
                      <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
                    </div>
                  ) : (
                    <pre className={`p-4 text-xs font-mono whitespace-pre-wrap break-all ${LANG_COLORS[fileLanguage || ''] || 'text-gray-800'}`}
                         style={{ minHeight: '400px', background: '#fafafa' }}>
                      {fileContent}
                    </pre>
                  )}
                </CardContent>
              </>
            ) : (
              <CardContent className="flex-1 flex items-center justify-center text-center py-16">
                <div>
                  <FolderOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                  <p className="text-muted-foreground">Select a file from the tree to view its contents</p>
                </div>
              </CardContent>
            )}
          </Card>
        </div>
      </div>
    </AppPageLayout>
  )
}
