import { useState, useMemo } from 'react'
import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { FileText } from 'lucide-react'
import { useSystemLogs } from '@/lib/hooks/useApi'

const levelColors = {
  debug: 'text-muted-foreground',
  info: 'text-blue-500',
  warn: 'text-orange-500',
  error: 'text-destructive',
}

const levelBadgeVariants = {
  debug: 'secondary' as const,
  info: 'default' as const,
  warn: 'default' as const,
  error: 'destructive' as const,
}

export function SystemLogs() {
  const { data: logs, isLoading } = useSystemLogs()
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)

  const filteredLogs = useMemo(() => {
    if (!logs) return []

    return logs.filter((log) => {
      if (levelFilter !== 'all' && log.level !== levelFilter) return false
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !log.source?.toLowerCase().includes(searchQuery.toLowerCase())) return false
      return true
    })
  }, [logs, levelFilter, searchQuery])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <AppPageLayout
      title="System Logs"
      subtitle="View and filter system logs and events"
      icon={FileText}
      iconColor="slate"
      accentColor="slate"
      headerViz="miniBars"
    >

      <Card>
        <CardHeader>
          <CardTitle>Log Console ({filteredLogs.length})</CardTitle>
          <CardDescription>Real-time system logs with filtering</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
            >
              <option value="all">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warn">Warning</option>
              <option value="error">Error</option>
            </select>

            <input
              type="search"
              placeholder="Search logs..."
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Auto-scroll</label>
              <button
                type="button"
                role="switch"
                aria-checked={autoScroll}
                onClick={() => setAutoScroll(!autoScroll)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${autoScroll ? 'bg-primary' : 'bg-input'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${autoScroll ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>
          </div>

          <div className="rounded-md border bg-muted/50 p-4 font-mono text-xs h-96 overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No logs match the current filters
              </div>
            ) : (
              <div className="space-y-1">
                {filteredLogs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="text-muted-foreground shrink-0">
                      [{new Date(log.timestamp).toLocaleString()}]
                    </span>
                    <Badge
                      variant={levelBadgeVariants[log.level]}
                      className="shrink-0 uppercase text-xs"
                    >
                      {log.level}
                    </Badge>
                    {log.source && (
                      <span className="text-muted-foreground shrink-0">
                        [{log.source}]
                      </span>
                    )}
                    <span className={levelColors[log.level]}>
                      {log.message}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </AppPageLayout>
  )
}
