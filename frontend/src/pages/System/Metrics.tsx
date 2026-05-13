import { AppPageLayout } from '@/components/layout/AppPageLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp } from 'lucide-react'
import { useSystemMetrics } from '@/lib/hooks/useApi'

export function SystemMetrics() {
  const { data: metrics, isLoading } = useSystemMetrics()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  // Mock time-series data for charts
  const chartData = [
    { time: '14:00', requests: 45, latency: 23, errors: 0 },
    { time: '14:15', requests: 52, latency: 28, errors: 1 },
    { time: '14:30', requests: 48, latency: 25, errors: 0 },
    { time: '14:45', requests: 61, latency: 31, errors: 2 },
    { time: '15:00', requests: 55, latency: 27, errors: 0 },
    { time: '15:15', requests: 58, latency: 29, errors: 1 },
    { time: '15:30', requests: 63, latency: 32, errors: 0 },
    { time: '15:45', requests: 57, latency: 26, errors: 0 },
  ]

  const latencyData = [
    { time: '14:00', p50: 18, p95: 45, p99: 78 },
    { time: '14:15', p50: 21, p95: 52, p99: 85 },
    { time: '14:30', p50: 19, p95: 48, p99: 80 },
    { time: '14:45', p50: 24, p95: 58, p99: 92 },
    { time: '15:00', p50: 20, p95: 50, p99: 82 },
    { time: '15:15', p50: 22, p95: 54, p99: 88 },
    { time: '15:30', p50: 25, p95: 60, p99: 95 },
    { time: '15:45', p50: 19, p95: 47, p99: 79 },
  ]

  return (
    <AppPageLayout
      title="System Metrics"
      subtitle="Monitor system performance and resource usage"
      icon={TrendingUp}
      iconColor="indigo"
      accentColor="indigo"
      headerViz="sparkline"
    >
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">CPU Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.cpu.current}%</div>
            <p className="text-xs text-muted-foreground">
              Avg: {metrics?.cpu.average}% | Peak: {metrics?.cpu.peak}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Memory Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.memory.usedPercent}%</div>
            <p className="text-xs text-muted-foreground">
              {(metrics?.memory.used || 0 / 1024).toFixed(1)} GB / {(metrics?.memory.total || 0 / 1024).toFixed(1)} GB
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Disk Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.disk.usedPercent}%</div>
            <p className="text-xs text-muted-foreground">
              {(metrics?.disk.used || 0 / 1024).toFixed(1)} GB / {(metrics?.disk.total || 0 / 1024).toFixed(1)} GB
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Requests & Errors</CardTitle>
          <CardDescription>Request rate and error count over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="time" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px'
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="requests" stroke="hsl(var(--primary))" name="Requests/min" strokeWidth={2} />
              <Line type="monotone" dataKey="errors" stroke="hsl(var(--destructive))" name="Errors" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Latency Percentiles</CardTitle>
          <CardDescription>Response time distribution (p50, p95, p99)</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="time" className="text-xs" />
              <YAxis className="text-xs" label={{ value: 'ms', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px'
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="p50" stroke="#10b981" name="p50" strokeWidth={2} />
              <Line type="monotone" dataKey="p95" stroke="#f59e0b" name="p95" strokeWidth={2} />
              <Line type="monotone" dataKey="p99" stroke="#ef4444" name="p99" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </AppPageLayout>
  )
}
