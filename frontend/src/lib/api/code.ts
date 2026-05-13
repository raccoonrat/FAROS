/**
 * Code Module API Client
 * 
 * Typed API client for code generation endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// Types

export interface CodeSessionConfig {
  repoPath: string;
  goal: string;
  providerName: string;
  model: string;
  maxCandidates: number;
  maxIterations: number;
  constraints?: string;
  targetFiles?: string[];
}

export interface CodeSession {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  config: CodeSessionConfig;
  createdAt: string;
  startedAt?: string;
  endedAt?: string;
  duration?: number;
  currentStep?: string;
  iterationCount: number;
  candidateIds: string[];
  selectedCandidateId?: string;
  summary?: string;
  errorMessage?: string;
}

export interface CandidateScores {
  correctness: number;
  completeness: number;
  efficiency: number;
  readability: number;
  safety: number;
}

export interface CodeCandidate {
  id: string;
  sessionId: string;
  title: string;
  approach: string;
  patch: string;
  rationale: string;
  scores: CandidateScores;
  overallScore: number;
  rank: number;
  createdAt: string;
}

export interface TraceStep {
  step: string;
  status: string;
  timestamp: string;
  durationMs?: number;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
  error?: string;
}

export interface CreateSessionRequest {
  repoPath: string;
  goal: string;
  providerName?: string;
  model?: string;
  maxCandidates?: number;
  constraints?: string;
}

// API Functions

export async function createSession(request: CreateSessionRequest): Promise<CodeSession> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to create session: ${response.statusText}`);
  }
  
  return response.json();
}

export async function startSession(sessionId: string): Promise<CodeSession> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions/${sessionId}/start`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to start session: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getSession(sessionId: string): Promise<CodeSession> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions/${sessionId}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to get session: ${response.statusText}`);
  }
  
  return response.json();
}

export async function listSessions(): Promise<{ sessions: CodeSession[]; total: number }> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to list sessions: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getCandidates(sessionId: string): Promise<{ candidates: CodeCandidate[]; total: number }> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions/${sessionId}/candidates`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to get candidates: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getTrace(sessionId: string): Promise<{ sessionId: string; steps: TraceStep[] }> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions/${sessionId}/trace`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to get trace: ${response.statusText}`);
  }
  
  return response.json();
}

export async function selectCandidate(sessionId: string, candidateId: string): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions/${sessionId}/select`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ candidateId }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to select candidate: ${response.statusText}`);
  }
  
  return response.json();
}

export async function cancelSession(sessionId: string): Promise<CodeSession> {
  const response = await fetch(`${API_BASE}/api/v1/code/sessions/${sessionId}/cancel`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to cancel session: ${response.statusText}`);
  }
  
  return response.json();
}

export async function testProvider(providerName: string): Promise<{ ok: boolean; latencyMs: number; text: string; error?: string }> {
  const response = await fetch(`${API_BASE}/api/v1/providers/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ providerName }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to test provider: ${response.statusText}`);
  }
  
  return response.json();
}
