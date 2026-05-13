// API Telemetry - Request tracking and diagnostics
// Provides in-memory ring buffer for recent API requests

export interface ApiRequestLog {
  id: string
  timestamp: string
  method: string
  url: string
  status?: number
  duration?: number
  requestId?: string
  error?: string
}

const MAX_LOGS = 100
const requestLogs: ApiRequestLog[] = []

let logIdCounter = 0

export function logApiRequest(log: Omit<ApiRequestLog, 'id' | 'timestamp'>): void {
  const entry: ApiRequestLog = {
    id: `req_${++logIdCounter}`,
    timestamp: new Date().toISOString(),
    ...log,
  }
  
  requestLogs.unshift(entry)
  
  // Keep only last MAX_LOGS entries
  if (requestLogs.length > MAX_LOGS) {
    requestLogs.pop()
  }
}

export function getRequestLogs(limit?: number): ApiRequestLog[] {
  return limit ? requestLogs.slice(0, limit) : [...requestLogs]
}

export function getLastRequest(): ApiRequestLog | undefined {
  return requestLogs[0]
}

export function clearRequestLogs(): void {
  requestLogs.length = 0
  logIdCounter = 0
}

export function getRequestStats(): {
  total: number
  successful: number
  failed: number
  avgDuration: number
} {
  const total = requestLogs.length
  const successful = requestLogs.filter(log => log.status && log.status >= 200 && log.status < 300).length
  const failed = requestLogs.filter(log => log.error || (log.status && log.status >= 400)).length
  
  const durations = requestLogs.filter(log => log.duration !== undefined).map(log => log.duration!)
  const avgDuration = durations.length > 0 
    ? durations.reduce((sum, d) => sum + d, 0) / durations.length 
    : 0
  
  return {
    total,
    successful,
    failed,
    avgDuration,
  }
}
