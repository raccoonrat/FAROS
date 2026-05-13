/**
 * Code Jobs API Client
 * 
 * Provides typed API calls for job execution, log streaming, and artifacts.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// Types

export interface CreateJobRequest {
  sessionId: string;
  candidateId?: string;
  mode: 'quick' | 'debug';
  command: string;
  envVars?: Record<string, string>;
  cwdRel?: string;
  timeoutSec?: number;
}

export interface Job {
  id: string;
  sessionId: string;
  candidateId?: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  mode: string;
  command: string;
  envVars?: Record<string, string>;
  cwdRel?: string;
  timeoutSec: number;
  workspacePath?: string;
  pid?: number;
  exitCode?: number;
  stdoutPath?: string;
  stderrPath?: string;
  createdAt: string;
  startedAt?: string;
  endedAt?: string;
  durationSec?: number;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export interface LogResponse {
  jobId: string;
  logType: string;
  lines: string[];
  totalLines: number;
}

export interface Artifact {
  id: string;
  kind: string;
  path: string;
  filename: string;
  sizeBytes: number;
  createdAt: string;
}

export interface ArtifactListResponse {
  artifacts: Artifact[];
  total: number;
}

export interface EvalResponse {
  id: string;
  jobId: string;
  syntaxValid: boolean;
  lintScore: number;
  riskCount: number;
  testPassed?: boolean;
  overallScore: number;
  grade: string;
  scores?: Record<string, number>;
}

// API Functions

export async function createJob(request: CreateJobRequest): Promise<Job> {
  const response = await fetch(`${API_BASE}/api/v1/code/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to create job: ${response.status}`);
  }
  
  return response.json();
}

export async function startJob(jobId: string): Promise<Job> {
  const response = await fetch(`${API_BASE}/api/v1/code/jobs/${jobId}/start`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to start job: ${response.status}`);
  }
  
  return response.json();
}

export async function stopJob(jobId: string): Promise<Job> {
  const response = await fetch(`${API_BASE}/api/v1/code/jobs/${jobId}/stop`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to stop job: ${response.status}`);
  }
  
  return response.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const response = await fetch(`${API_BASE}/api/v1/code/jobs/${jobId}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to get job: ${response.status}`);
  }
  
  return response.json();
}

export async function listJobs(params?: {
  sessionId?: string;
  candidateId?: string;
  status?: string;
  limit?: number;
}): Promise<JobListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.sessionId) searchParams.set('sessionId', params.sessionId);
  if (params?.candidateId) searchParams.set('candidateId', params.candidateId);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  
  const url = `${API_BASE}/api/v1/code/jobs?${searchParams}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to list jobs: ${response.status}`);
  }
  
  return response.json();
}

export async function getJobLogs(
  jobId: string,
  logType: 'stdout' | 'stderr' = 'stdout',
  lines: number = 100
): Promise<LogResponse> {
  const url = `${API_BASE}/api/v1/code/jobs/${jobId}/logs?logType=${logType}&lines=${lines}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to get logs: ${response.status}`);
  }
  
  return response.json();
}

export function getLogDownloadUrl(jobId: string, logType: 'stdout' | 'stderr' = 'stdout'): string {
  return `${API_BASE}/api/v1/code/jobs/${jobId}/logs/download?logType=${logType}`;
}

export async function getJobArtifacts(jobId: string): Promise<ArtifactListResponse> {
  const response = await fetch(`${API_BASE}/api/v1/code/jobs/${jobId}/artifacts`);
  
  if (!response.ok) {
    throw new Error(`Failed to get artifacts: ${response.status}`);
  }
  
  return response.json();
}

export async function getJobEvaluation(jobId: string): Promise<EvalResponse | null> {
  const response = await fetch(`${API_BASE}/api/v1/code/jobs/${jobId}/evaluation`);
  
  if (response.status === 404) {
    return null;
  }
  
  if (!response.ok) {
    throw new Error(`Failed to get evaluation: ${response.status}`);
  }
  
  return response.json();
}

// Utility: Poll for job completion
export async function pollJobUntilComplete(
  jobId: string,
  onUpdate?: (job: Job) => void,
  intervalMs: number = 1000,
  maxAttempts: number = 600
): Promise<Job> {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    const job = await getJob(jobId);
    
    if (onUpdate) {
      onUpdate(job);
    }
    
    if (['succeeded', 'failed', 'cancelled'].includes(job.status)) {
      return job;
    }
    
    await new Promise(resolve => setTimeout(resolve, intervalMs));
    attempts++;
  }
  
  throw new Error('Job polling timeout');
}
