import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { CheckCircle2, AlertCircle, Activity } from 'lucide-react'
import { useSystemHealth } from '@/lib/hooks/useApi'

const statusVariants = {
  ok: 'success' as const,
  degraded: 'default' as const,
  down: 'destructive' as const,
}

const statusIcons = {
  ok: <CheckCircle2 className="h-4 w-4" />,
  degraded: <AlertCircle className="h-4 w-4" />,
  down: <AlertCircle className="h-4 w-4" />,
}

export function SystemHealth() {
  const { data: health, isLoading } = useSystemHealth()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  const overallStatus = health?.components.every(c => c.status === 'ok') ? 'ok' :
    health?.components.some(c => c.status === 'down') ? 'down' : 'degraded'

  return (
    <AppPageLayout
      title="System Health"
      subtitle="Monitor system status and performance metrics"
      icon={Activity}
      iconColor="cyan"
      accentColor="cyan"
      headerViz="metricCapsules"
    >

      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
          <CardDescription>Overall system health</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div className={overallStatus === 'ok' ? 'text-success' : overallStatus === 'down' ? 'text-destructive' : 'text-orange-500'}>
              {statusIcons[overallStatus]}
            </div>
            <div>
              <Badge variant={statusVariants[overallStatus]} className="capitalize">
                {overallStatus === 'ok' ? 'Healthy' : overallStatus === 'down' ? 'Down' : 'Degraded'}
              </Badge>
              <p className="text-sm text-muted-foreground mt-1">
                {overallStatus === 'ok' ? 'All systems operational' :
                  overallStatus === 'down' ? 'Critical services down' :
                    'Some services degraded'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Components ({health?.components.length || 0})</CardTitle>
          <CardDescription>Individual component status and health checks</CardDescription>
        </CardHeader>
        <CardContent>
          {!health || health.components.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No components to monitor
            </div>
          ) : (
            <div className="rounded-md border">
              <table className="w-full">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium">Service</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Last Check</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {health.components.map((component) => (
                    <tr key={component.name} className="border-b last:border-0">
                      <td className="px-4 py-3">
                        <div className="font-medium text-sm">{component.name}</div>
                        {component.message && (
                          <div className="text-xs text-muted-foreground">{component.message}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className={component.status === 'ok' ? 'text-success' : component.status === 'down' ? 'text-destructive' : 'text-orange-500'}>
                            {statusIcons[component.status]}
                          </div>
                          <Badge variant={statusVariants[component.status]} className="capitalize">
                            {component.status}
                          </Badge>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {new Date(component.lastCheck).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {component.latency ? `${component.latency}ms` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </AppPageLayout>
  )
}
