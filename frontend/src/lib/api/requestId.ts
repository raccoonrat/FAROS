// Request ID Generation
// Provides deterministic IDs in mock mode, random IDs in real mode

let requestCounter = 0

export function generateRequestId(mode: 'mock' | 'real' = 'mock'): string {
  if (mode === 'mock') {
    // Deterministic for testing and debugging
    requestCounter++
    return `req_mock_${String(requestCounter).padStart(6, '0')}`
  }

  // Random for real API calls
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 10)
  return `req_${timestamp}_${random}`
}

export function resetRequestCounter(): void {
  requestCounter = 0
}
